<template>
    <div class="live-chart">
        <Line :data="chartData" :options="options" />
    </div>
</template>

<script setup>
import { computed } from 'vue'
import {
    CategoryScale,
    Chart as ChartJS,
    Legend,
    LineElement,
    LinearScale,
    PointElement,
    Tooltip,
} from 'chart.js'
import { Line } from 'vue-chartjs'
import { METRIC_COLORS } from '../../composables/useMetricsStream'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend)

const props = defineProps({
    definitions: { type: Object, required: true }, // name -> definition
    series: { type: Object, required: true }, // name -> [{ t, v }]
})

const FALLBACK_COLORS = ['#3b82f6', '#8b5cf6', '#10b981', '#f59e0b']

const orderedNames = computed(() => Object.keys(props.definitions))

function formatAxisTime(iso) {
    if (!iso) return ''
    return new Date(iso).toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
    })
}

// Подписи оси X — таймстемпы самой длинной серии (серии обновляются синхронно)
const labels = computed(() => {
    let longest = []
    for (const name of orderedNames.value) {
        const points = props.series[name] || []
        if (points.length > longest.length) longest = points
    }
    return longest.map((p) => formatAxisTime(p.t))
})

const chartData = computed(() => {
    const total = labels.value.length

    const datasets = orderedNames.value
        .filter((name) => (props.series[name] || []).length > 0)
        .map((name, index) => {
            const def = props.definitions[name]
            const points = props.series[name] || []
            const color = METRIC_COLORS[name] || FALLBACK_COLORS[index % FALLBACK_COLORS.length]

            // Короткие серии дополняем null'ами в начале — ось X выровнена
            const pad = Math.max(total - points.length, 0)
            const data = [...Array(pad).fill(null), ...points.map((p) => p.v)]

            return {
                label: def?.display_name || name,
                data,
                unit: def?.unit || '',
                borderColor: color,
                backgroundColor: color,
                yAxisID:
                    def?.unit === '%'
                        ? 'yPercent'
                        : def?.unit === 'users'
                            ? 'yUsers'
                            : 'yRps',
                tension: 0.35,
                pointRadius: 0,
                pointHitRadius: 8,
                borderWidth: 2,
                spanGaps: true,
            }
        })

    return { labels: labels.value, datasets }
})

const options = {
    responsive: true,
    maintainAspectRatio: false,
    animation: { duration: 350 },
    interaction: { mode: 'index', intersect: false },
    plugins: {
        legend: {
            labels: {
                color: '#cbd5e1',
                usePointStyle: true,
                pointStyle: 'circle',
                boxWidth: 8,
                padding: 16,
            },
        },
        tooltip: {
            callbacks: {
                label: (ctx) => `${ctx.dataset.label}: ${ctx.parsed.y} ${ctx.dataset.unit}`,
            },
        },
    },
    scales: {
        x: {
            ticks: { color: '#64748b', maxTicksLimit: 8, maxRotation: 0 },
            grid: { color: 'rgba(148, 163, 184, 0.08)' },
        },
        yPercent: {
            display: true,
            position: 'left',
            min: 0,
            max: 100,
            ticks: { color: '#64748b', callback: (v) => `${v}%` },
            grid: { color: 'rgba(148, 163, 184, 0.08)' },
        },
        yUsers: { display: false, min: 0, suggestedMax: 2000 },
        yRps: { display: false, min: 0, suggestedMax: 5000 },
    },
}
</script>

<style scoped>
.live-chart {
    height: 100%;
}
</style>