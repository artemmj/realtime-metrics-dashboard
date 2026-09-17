<template>
    <div class="metric-card" :class="[`status-${status}`, { 'is-pulsing': pulsing }]">
        <div class="metric-top">
            <span class="metric-name">{{ definition.display_name }}</span>
            <span class="status-badge" :class="`status-${status}`">
                <span class="status-dot" />
                {{ statusLabel }}
            </span>
        </div>

        <div class="metric-main">
            <span class="metric-value">{{ formattedValue }}</span>
            <span v-if="unitSuffix" class="metric-unit">{{ unitSuffix }}</span>
        </div>

        <div class="metric-bottom">
            <span class="metric-delta" :class="deltaTone">
                {{ deltaArrow }} {{ formattedDelta }}
            </span>
            <span class="metric-updated">{{ updatedAgo }}</span>
        </div>

        <div class="metric-sparkline">
            <Sparkline :values="values" :color="statusColor" :height="36" />
        </div>
    </div>
</template>

<script setup>
import { computed, onUnmounted, ref, watch } from 'vue'
import Sparkline from './Sparkline.vue'

const props = defineProps({
    definition: { type: Object, required: true }, // { name, display_name, unit, precision, ... }
    latest: { type: Object, default: null }, // { id, value, delta, status, text, timestamp }
    values: { type: Array, default: () => [] }, // числа для спарклайна
})

const STATUS_COLORS = {
    normal: '#10b981',
    warning: '#f59e0b',
    critical: '#ef4444',
}
const STATUS_LABELS = {
    normal: 'Normal',
    warning: 'Warning',
    critical: 'Critical',
}

const status = computed(() => props.latest?.status || 'normal')
const statusColor = computed(() => STATUS_COLORS[status.value] || '#3b82f6')
const statusLabel = computed(() => STATUS_LABELS[status.value] || status.value)

const unitSuffix = computed(() =>
    props.definition.unit === 'users' ? '' : props.definition.unit
)

// ============ Плавная анимация значения (tween) ============
const displayValue = ref(props.latest?.value ?? 0)
let rafId = null

watch(
    () => props.latest?.value,
    (target) => {
        if (target == null) return
        const from = displayValue.value
        const to = target
        if (from === to) return

        const start = performance.now()
        const duration = 500

        cancelAnimationFrame(rafId)
        const step = (now) => {
            const progress = Math.min((now - start) / duration, 1)
            const eased = 1 - Math.pow(1 - progress, 3) // easeOutCubic
            displayValue.value = from + (to - from) * eased
            if (progress < 1) {
                rafId = requestAnimationFrame(step)
            }
        }
        rafId = requestAnimationFrame(step)
    },
    { immediate: true }
)

onUnmounted(() => cancelAnimationFrame(rafId))

// ============ Форматирование ============
const numberFormat = computed(
    () =>
        new Intl.NumberFormat('en-US', {
            minimumFractionDigits: props.definition.precision ?? 0,
            maximumFractionDigits: props.definition.precision ?? 0,
        })
)

const formattedValue = computed(() => numberFormat.value.format(displayValue.value))

const formattedDelta = computed(() => {
    const delta = props.latest?.delta ?? 0
    const sign = delta > 0 ? '+' : delta < 0 ? '−' : '±'
    return `${sign}${numberFormat.value.format(Math.abs(delta))}`
})

const deltaArrow = computed(() => {
    const delta = props.latest?.delta ?? 0
    if (delta > 0) return '↑'
    if (delta < 0) return '↓'
    return ''
})

// «Плохая» дельта — красная, «хорошая» — зелёная (с учётом смысла метрики)
const deltaTone = computed(() => {
    const delta = props.latest?.delta ?? 0
    if (delta === 0) return 'flat'
    const isBad = delta > 0 ? props.definition.higher_is_bad : !props.definition.higher_is_bad
    return isBad ? 'bad' : 'good'
})

// ============ «Обновлено N сек назад» ============
const nowTick = ref(Date.now())
const agoTimer = setInterval(() => (nowTick.value = Date.now()), 1000)
onUnmounted(() => clearInterval(agoTimer))

const updatedAgo = computed(() => {
    if (!props.latest?.timestamp) return 'waiting…'
    const seconds = Math.max(
        0,
        Math.round((nowTick.value - new Date(props.latest.timestamp).getTime()) / 1000)
    )
    if (seconds < 3) return 'just now'
    if (seconds < 60) return `${seconds}s ago`
    return `${Math.floor(seconds / 60)}m ago`
})

// ============ Пульс карточки при обновлении ============
const pulsing = ref(false)
let pulseTimer = null
watch(
    () => props.latest?.id,
    () => {
        pulsing.value = true
        clearTimeout(pulseTimer)
        pulseTimer = setTimeout(() => (pulsing.value = false), 700)
    }
)
onUnmounted(() => clearTimeout(pulseTimer))
</script>

<style scoped>
.metric-card {
    position: relative;
    background: white;
    padding: 16px 18px;
    border-radius: 10px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
    border-left: 4px solid transparent;
    overflow: hidden;
    transition: transform 0.2s ease;
    --status-color: #3b82f6;
}

.metric-card:hover {
    transform: translateY(-2px);
}

.metric-card.status-normal {
    --status-color: #10b981;
    --status-glow: rgba(16, 185, 129, 0.45);
    border-left-color: var(--status-color);
}

.metric-card.status-warning {
    --status-color: #f59e0b;
    --status-glow: rgba(245, 158, 11, 0.45);
    border-left-color: var(--status-color);
}

.metric-card.status-critical {
    --status-color: #ef4444;
    --status-glow: rgba(239, 68, 68, 0.45);
    border-left-color: var(--status-color);
}

.metric-card.is-pulsing {
    animation: card-pulse 0.7s ease-out;
}

@keyframes card-pulse {
    0% {
        box-shadow: 0 0 0 0 var(--status-glow);
    }
    100% {
        box-shadow: 0 0 0 14px transparent;
    }
}

.metric-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
}

.metric-name {
    font-size: 0.78em;
    font-weight: 600;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.03em;
}

.status-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: 0.72em;
    font-weight: 600;
    padding: 3px 9px;
    border-radius: 999px;
}

.status-badge.status-normal {
    background: #dcfce7;
    color: #166534;
}

.status-badge.status-warning {
    background: #fef9c3;
    color: #854d0e;
}

.status-badge.status-critical {
    background: #fee2e2;
    color: #991b1b;
}

.status-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: currentColor;
}

.status-badge.status-critical .status-dot {
    animation: blink 1s infinite;
}

@keyframes blink {
    50% {
        opacity: 0.2;
    }
}

.metric-main {
    display: flex;
    align-items: baseline;
    gap: 5px;
}

.metric-value {
    font-size: 2em;
    font-weight: 700;
    color: #0f172a;
    font-variant-numeric: tabular-nums;
    line-height: 1.1;
}

.metric-unit {
    font-size: 0.9em;
    color: #64748b;
}

.metric-bottom {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 6px;
}

.metric-delta {
    font-size: 0.85em;
    font-weight: 600;
    font-variant-numeric: tabular-nums;
}

.metric-delta.good {
    color: #10b981;
}

.metric-delta.bad {
    color: #ef4444;
}

.metric-delta.flat {
    color: #94a3b8;
}

.metric-updated {
    font-size: 0.75em;
    color: #94a3b8;
}

.metric-sparkline {
    height: 36px;
    margin-top: 12px;
}
</style>