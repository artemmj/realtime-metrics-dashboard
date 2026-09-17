<template>
    <div class="dashboard">
        <header class="dashboard-header">
            <h1>Realtime Metrics Dashboard</h1>
            <div class="user-info" v-if="authStore.user">
                <span>Welcome, {{ authStore.user.email }}</span>
                <button @click="handleLogout" class="btn-logout">Logout</button>
            </div>
        </header>

        <!-- Статус WebSocket -->
        <div class="ws-status" :class="{ connected: stream.state.connected }">
            <span class="ws-dot"></span>
            {{ stream.state.connected ? 'Live' : 'Disconnected' }}
        </div>

        <!-- Realtime: график + живая лента событий -->
        <section class="live-grid">
            <div class="panel chart-panel">
                <div class="panel-title-row">
                    <h2>Realtime</h2>
                    <span class="panel-hint">last 60 points</span>
                </div>
                <div class="chart-container">
                    <LiveChart :definitions="stream.state.definitions" :series="stream.state.series" />
                </div>
            </div>

            <div class="panel feed-panel">
                <div class="panel-title-row">
                    <h2>Live events</h2>
                </div>
                <EventFeed :events="stream.state.events" />
            </div>
        </section>

        <!-- Сводка по последним значениям метрик -->
        <section class="metrics-summary">
            <h2>Current Metrics</h2>
            <div class="metrics-grid">
                <MetricCard
                    v-for="def in definitionList"
                    :key="def.name"
                    :definition="def"
                    :latest="stream.state.latest[def.name]"
                    :values="seriesValues(def.name)"
                />
                <div v-if="definitionList.length === 0" class="no-data">
                    No metrics data yet. Waiting for data...
                </div>
            </div>
        </section>

        <!-- Таблица с историей метрик -->
        <section class="metrics-history">
            <div class="history-header">
                <h2>Metrics History</h2>
                <button @click="loadMetrics" :disabled="loading" class="btn-refresh">
                    {{ loading ? 'Loading...' : 'Refresh' }}
                </button>
            </div>

            <!-- Фильтр по имени метрики -->
            <div class="filters">
                <label>
                    Filter by name:
                    <select v-model="selectedMetricFilter">
                        <option value="">All metrics</option>
                        <option v-for="name in metricNames" :key="name" :value="name">
                        {{ displayName(name) }}
                        </option>
                    </select>
                </label>
            </div>

            <!-- Таблица -->
            <div class="table-wrapper" v-if="filteredMetrics.length > 0">
                <table>
                    <thead>
                        <tr>
                        <th>ID</th>
                        <th>Name</th>
                        <th>Value</th>
                        <th>Status</th>
                        <th>Timestamp</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="metric in filteredMetrics" :key="metric.id"
                            :class="rowClass(metric)">
                            <td>{{ metric.id }}</td>
                            <td>{{ displayName(metric.name) }}</td>
                            <td :style="{ color: statusColor(metric) }">
                                {{ formatValue(metric) }}
                            </td>
                            <td>
                                <span class="status-indicator" :class="metricStatus(metric)">
                                    {{ statusLabel(metric) }}
                                </span>
                            </td>
                            <td>{{ formatTime(metric.created_at) }}</td>
                        </tr>
                    </tbody>
                </table>
            </div>
            <div v-else-if="!loading" class="no-data">
                No metrics in history
            </div>
        </section>
    </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useMetricsStream } from '../composables/useMetricsStream'
import MetricCard from '../components/metrics/MetricCard.vue'
import LiveChart from '../components/metrics/LiveChart.vue'
import EventFeed from '../components/metrics/EventFeed.vue'
import api from '../api'

const authStore = useAuthStore()
const router = useRouter()

// ============ REST метрики ============
const metrics = ref([])          // полный список с REST API
const loading = ref(false)       // индикатор загрузки
const error = ref('')            // ошибки
const selectedMetricFilter = ref('') // фильтр по имени

// ============ Диапазоны метрик больше не нужны — они приходят с бэкенда в WS hello ============

// Уникальные имена метрик из полного списка
const metricNames = computed(() => {
    const names = new Set(metrics.value.map(m => m.name))
    return [...names].sort()
})

// Отфильтрованные метрики
const filteredMetrics = computed(() => {
    if (!selectedMetricFilter.value) {
        return metrics.value
    }
    return metrics.value.filter(m => m.name === selectedMetricFilter.value)
})

// Загрузка метрик с REST API
async function loadMetrics() {
    loading.value = true
    error.value = ''
    try {
        const response = await api.get('/metrics/?limit=100&offset=0')
        metrics.value = response.data
    } catch (e) {
        error.value = 'Failed to load metrics: ' + (e.response?.data?.detail || e.message)
        console.error(error.value)
    } finally {
        loading.value = false
    }
}

// ============ WebSocket-поток (composable-синглтон) ============
const stream = useMetricsStream()

// ============ Определения метрик (прилетают по WS в hello) ============
const definitionList = computed(() => Object.values(stream.state.definitions))

function seriesValues(name) {
    return (stream.state.series[name] || []).map((p) => p.v)
}

// ============ Статусы для таблицы (по определениям из WS hello) ============
const STATUS_COLORS = { normal: '#10b981', warning: '#f59e0b', critical: '#ef4444' }
const STATUS_LABELS = { normal: 'Normal', warning: 'Warning', critical: 'Critical' }
const ROW_CLASSES = { normal: 'row-green', warning: 'row-yellow', critical: 'row-red' }

function metricStatus(metric) {
    const def = stream.state.definitions[metric.name]
    if (!def) return 'normal'

    if (def.higher_is_bad) {
        if (def.critical != null && metric.value >= def.critical) return 'critical'
        if (def.warning != null && metric.value >= def.warning) return 'warning'
    } else {
        if (def.critical != null && metric.value <= def.critical) return 'critical'
        if (def.warning != null && metric.value <= def.warning) return 'warning'
    }
    return 'normal'
}

function statusColor(metric) {
    return STATUS_COLORS[metricStatus(metric)]
}

function statusLabel(metric) {
    return STATUS_LABELS[metricStatus(metric)]
}

function rowClass(metric) {
    return ROW_CLASSES[metricStatus(metric)]
}

// ============ Вспомогательные функции ============
function formatMetricName(name) {
    return name
        .split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ')
}

// Имя из определений WS (fallback — форматирование из snake_case)
function displayName(name) {
    return stream.state.definitions[name]?.display_name || formatMetricName(name)
}

// Форматирование значения с точностью из определения метрики
function formatValue(metric) {
    const precision = stream.state.definitions[metric.name]?.precision ?? 0
    return metric.value.toLocaleString('en-US', {
        minimumFractionDigits: precision,
        maximumFractionDigits: precision
    })
}

function formatTime(isoString) {
    if (!isoString) return ''
    const date = new Date(isoString)
    return date.toLocaleTimeString()
}

// ============ Логаут ============
async function handleLogout() {
    await authStore.logout()
    router.push('/login')
}

// ============ Жизненный цикл ============
onMounted(() => {
    loadMetrics()
    stream.connect()
})

onUnmounted(() => {
    stream.disconnect()
})
</script>

<style scoped>
.dashboard {
    max-width: 1200px;
    margin: 0 auto;
}

.dashboard-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    padding: 15px 0;
    border-bottom: 3px solid #e2e8f0;
}

.user-info {
    display: flex;
    align-items: center;
    gap: 15px;
}

.btn-logout {
    padding: 8px 16px;
    background: #ef4444;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
}

.btn-logout:hover {
    background: #dc2626;
}

/* WebSocket статус */
.ws-status {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 6px 14px;
    border-radius: 999px;
    background: #fee2e2;
    color: #991b1b;
    margin-bottom: 20px;
    font-size: 0.9em;
    font-weight: 600;
}

.ws-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #ef4444;
}

.ws-status.connected {
    background: #dcfce7;
    color: #166534;
}

.ws-status.connected .ws-dot {
    background: #10b981;
    animation: pulse-dot 2s infinite;
}

@keyframes pulse-dot {
    0% {
        box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.5);
    }
    70% {
        box-shadow: 0 0 0 6px rgba(16, 185, 129, 0);
    }
    100% {
        box-shadow: 0 0 0 0 rgba(16, 185, 129, 0);
    }
}

/* Realtime-секция: график + лента событий */
.live-grid {
    display: grid;
    grid-template-columns: 2fr 1fr;
    gap: 15px;
    margin-bottom: 30px;
    align-items: start; /* панели не растягиваются до высоты контента друг друга */
}

@media (max-width: 900px) {
    .live-grid {
        grid-template-columns: 1fr;
    }
}

.panel {
    background: white;
    border-radius: 10px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
    padding: 16px 18px;
}

.panel-title-row {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    margin-bottom: 12px;
}

.panel h2 {
    margin: 0;
    font-size: 1.05em;
}

.panel-hint {
    font-size: 0.75em;
    color: #94a3b8;
}

.chart-panel {
    background: #0f172a;
    border: 1px solid #1e293b;
}

.chart-panel h2 {
    color: #e2e8f0;
}

.chart-panel .panel-hint {
    color: #64748b;
}

.chart-container {
    height: 300px;
}

.feed-panel {
    display: flex;
    flex-direction: column;
    max-height: 360px; /* ограничиваем рост, скролим внутри */
    overflow: hidden;
}

.feed-panel h2 {
    color: #0f172a;
}

.feed-panel :deep(.event-feed) {
    flex: 1 1 auto;
    min-height: 0;
    max-height: 100%;
    overflow-y: auto;
}

/* Сводка метрик */
.metrics-summary {
    margin-bottom: 30px;
    border-top: 3px solid #e2e8f0;
}

.metrics-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
    gap: 15px;
}

/* История */
.history-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 15px;
}

.btn-refresh {
    padding: 8px 16px;
    background: #3b82f6;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
}

.btn-refresh:hover:not(:disabled) {
    background: #2563eb;
}

.btn-refresh:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

/* Фильтр */
.filters {
    margin-bottom: 15px;
}

.filters select {
    padding: 6px 10px;
    border: 1px solid #cbd5e1;
    border-radius: 4px;
    margin-left: 8px;
}

/* Таблица */
.table-wrapper {
    background: white;
    border-radius: 8px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    overflow-x: auto;
}

table {
    width: 100%;
    border-collapse: collapse;
}

th {
    text-align: left;
    padding: 12px 15px;
    background: #f8fafc;
    color: #475569;
    font-weight: 600;
    font-size: 0.85em;
    text-transform: uppercase;
    border-bottom: 2px solid #e2e8f0;
}

td {
    padding: 10px 15px;
    border-bottom: 1px solid #f1f5f9;
}

/* Подсветка строк в таблице */
tr.row-green td {
    background: #f0fdf4;
}

tr.row-yellow td {
    background: #fefce8;
}

tr.row-red td {
    background: #fef2f2;
}

tr:hover td {
    filter: brightness(0.95);
}

/* Индикаторы статуса */
.status-indicator {
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 0.85em;
    font-weight: 500;
}

.status-indicator.status-normal {
    background: #dcfce7;
    color: #166534;
}

.status-indicator.status-warning {
    background: #fef9c3;
    color: #854d0e;
}

.status-indicator.status-critical {
    background: #fee2e2;
    color: #991b1b;
}

/* Нет данных */
.no-data {
    text-align: center;
    padding: 30px;
    color: #94a3b8;
}
</style>
