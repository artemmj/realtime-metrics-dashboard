<template>
    <div class="dashboard">
        <header class="dashboard-header">
            <h1>Dashboard</h1>
            <div class="user-info" v-if="authStore.user">
                <span>Welcome, {{ authStore.user.email }}</span>
                <button @click="handleLogout" class="btn-logout">Logout</button>
            </div>
        </header>

        <!-- Статус WebSocket -->
        <div class="ws-status" :class="{ connected: wsConnected }">
            WebSocket: {{ wsConnected ? 'Connected' : 'Disconnected' }}
        </div>

        <!-- Сводка по последним значениям метрик -->
        <section class="metrics-summary">
            <h2>Current Metrics</h2>
            <div class="metrics-grid">
                <div v-for="metric in latestMetrics" :key="metric.name" class="metric-card">
                    <div class="metric-name">{{ formatMetricName(metric.name) }}</div>
                    <div class="metric-value" :style="{ color: metric.value }">
                        {{ metric.value }}
                    </div>
                    <div class="metric-time">{{ formatTime(metric.created_at) }}</div>
                </div>
                <div v-if="latestMetrics.length === 0" class="no-data">
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
                        {{ formatMetricName(name) }}
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
                        <th>Timestamp</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="metric in filteredMetrics" :key="metric.id">
                            <td>{{ metric.id }}</td>
                            <td>{{ formatMetricName(metric.name) }}</td>
                            <td :style="{ color: metric.value }">
                                {{ metric.value }}
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
import api from '../api'

const authStore = useAuthStore()
const router = useRouter()

// ============ REST метрики ============
const metrics = ref([])          // полный список с REST API
const loading = ref(false)       // индикатор загрузки
const error = ref('')            // ошибки
const selectedMetricFilter = ref('') // фильтр по имени

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

// ============ WebSocket ============
const wsConnected = ref(false)
const wsMetrics = ref([]) // метрики, пришедшие по WebSocket
let ws = null
let reconnectTimeout = null

function connectWebSocket() {
    // Формируем URL с токеном (или без, зависит от бэкенда)
    // Предположим, что токен передаётся в query параметре или бэк сам понимает по cookie
    // По ТЗ пока просто ws://localhost/api/v1/metrics/ws
    const wsUrl = 'ws://localhost/api/v1/metrics/ws'

    ws = new WebSocket(wsUrl)

    ws.onopen = () => {
        wsConnected.value = true
        console.log('WebSocket connected')
    }

    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data)

            // Игнорируем ping
            if (data.type === 'ping') {
                return
            }

            // Это метрика — сохраняем в массив
            // У бэкенда timestamp, а в REST — created_at. Унифицируем:
            const metric = {
                id: data.id || Date.now(), // если нет id, генерируем временный
                name: data.name,
                value: data.value,
                created_at: data.timestamp || data.created_at || new Date().toISOString()
            }

            // Добавляем в начало массива ws-метрик
            wsMetrics.value.unshift(metric)

            // Ограничим размер массива, чтобы не копить бесконечно
            if (wsMetrics.value.length > 200) {
                wsMetrics.value = wsMetrics.value.slice(0, 200)
            }
        } catch (e) {
            console.warn('Failed to parse WebSocket message:', event.data, e)
        }
    }

    ws.onclose = () => {
        wsConnected.value = false
        console.log('WebSocket disconnected')
        // Автопереподключение через 3 секунды
        reconnectTimeout = setTimeout(() => {
            connectWebSocket()
        }, 3000)
    }

    ws.onerror = (err) => {
        console.error('WebSocket error:', err)
    }
}

function disconnectWebSocket() {
    if (reconnectTimeout) {
        clearTimeout(reconnectTimeout)
        reconnectTimeout = null
    }
    if (ws) {
        ws.close()
        ws = null
    }
}

// ============ Computed: последние значения каждой метрики ============
// Объединяем REST-метрики и WS-метрики, берём самое свежее по каждому имени
const latestMetrics = computed(() => {
    const combined = [...metrics.value, ...wsMetrics.value]

    // Группируем по имени
    const grouped = {}
    for (const m of combined) {
        if (!grouped[m.name] || new Date(m.created_at) > new Date(grouped[m.name].created_at)) {
            grouped[m.name] = m
        }
    }

    // Преобразуем в массив и сортируем по имени
    return Object.values(grouped).sort((a, b) => a.name.localeCompare(b.name))
})

// ============ Вспомогательные функции ============
function formatMetricName(name) {
    return name
        .split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ')
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
    connectWebSocket()
})

onUnmounted(() => {
    disconnectWebSocket()
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
    border-bottom: 1px solid #e2e8f0;
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
    padding: 6px 12px;
    border-radius: 4px;
    background: #fee2e2;
    color: #991b1b;
    display: inline-block;
    margin-bottom: 20px;
    font-size: 0.9em;
}

.ws-status.connected {
    background: #dcfce7;
    color: #166534;
}

/* Сводка метрик */
.metrics-summary {
    margin-bottom: 30px;
}

.metrics-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
    gap: 15px;
}

.metric-card {
    background: white;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.metric-name {
    font-size: 0.85em;
    color: #64748b;
    text-transform: uppercase;
    margin-bottom: 8px;
}

.metric-value {
    font-size: 2em;
    font-weight: bold;
}

.metric-time {
    font-size: 0.75em;
    color: #94a3b8;
    margin-top: 5px;
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

tr:hover td {
    background: #f8fafc;
}

/* Нет данных */
.no-data {
    text-align: center;
    padding: 30px;
    color: #94a3b8;
}
</style>
