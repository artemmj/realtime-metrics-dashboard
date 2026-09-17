<template>
    <svg class="sparkline" :viewBox="`0 0 ${width} ${height}`" preserveAspectRatio="none" aria-hidden="true">
        <defs>
            <linearGradient :id="gradientId" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" :stop-color="color" stop-opacity="0.35" />
                <stop offset="100%" :stop-color="color" stop-opacity="0" />
            </linearGradient>
        </defs>

        <template v-if="coords.length > 1">
            <polygon :fill="`url(#${gradientId})`" :points="areaPoints" />
            <polyline :points="linePoints" fill="none" :stroke="color" stroke-width="2"
                stroke-linecap="round" stroke-linejoin="round" />
        </template>
        <circle v-if="lastPoint" :cx="lastPoint.x" :cy="lastPoint.y" r="2.5" :fill="color" />
    </svg>
</template>

<script setup>
import { computed, useId } from 'vue'

const props = defineProps({
    values: { type: Array, default: () => [] }, // числа (последние точки метрики)
    color: { type: String, default: '#3b82f6' },
    width: { type: Number, default: 120 },
    height: { type: Number, default: 32 },
    padding: { type: Number, default: 3 },
})

const gradientId = useId()

const coords = computed(() => {
    const values = props.values.filter((v) => Number.isFinite(v))
    if (values.length === 0) return []

    const min = Math.min(...values)
    const max = Math.max(...values)
    const span = max - min || 1 // защита от плоской линии

    const innerW = props.width - props.padding * 2
    const innerH = props.height - props.padding * 2

    return values.map((value, index) => {
        const x = props.padding + (innerW * index) / Math.max(values.length - 1, 1)
        const y = props.padding + innerH * (1 - (value - min) / span)
        return { x, y }
    })
})

const linePoints = computed(() =>
    coords.value.map((p) => `${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' ')
)

const areaPoints = computed(() => {
    if (coords.value.length < 2) return ''
    const first = coords.value[0]
    const last = coords.value[coords.value.length - 1]
    const base = props.height - props.padding
    return [
        `${first.x.toFixed(1)},${base}`,
        ...coords.value.map((p) => `${p.x.toFixed(1)},${p.y.toFixed(1)}`),
        `${last.x.toFixed(1)},${base}`,
    ].join(' ')
})

const lastPoint = computed(() => coords.value[coords.value.length - 1] || null)
</script>

<style scoped>
.sparkline {
    display: block;
    width: 100%;
    height: 100%;
}
</style>