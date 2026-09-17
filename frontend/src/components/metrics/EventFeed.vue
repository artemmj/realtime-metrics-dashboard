<template>
    <div class="event-feed">
        <TransitionGroup v-if="events.length > 0" name="feed" tag="ul" class="feed-list">
            <li v-for="event in events" :key="event.id" class="feed-item" :class="`status-${event.status}`">
                <span class="feed-time">{{ formatTime(event.timestamp) }}</span>
                <span class="feed-text">{{ event.text }}</span>
            </li>
        </TransitionGroup>
        <div v-else class="feed-empty">Waiting for events…</div>
    </div>
</template>

<script setup>
defineProps({
    events: { type: Array, default: () => [] }, // { id, name, text, status, timestamp }
})

function formatTime(iso) {
    if (!iso) return ''
    return new Date(iso).toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
    })
}
</script>

<style scoped>
.event-feed {
    overflow-y: auto;
    padding-right: 6px;
}

.feed-list {
    list-style: none;
    margin: 0;
    padding: 0;
    position: relative;
}

.feed-item {
    display: flex;
    align-items: baseline;
    gap: 10px;
    padding: 8px 4px;
    border-bottom: 1px dashed #eef2f7;
    font-size: 0.85em;
}

.feed-item:last-child {
    border-bottom: none;
}

.feed-time {
    font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
    color: #94a3b8;
    font-size: 0.9em;
    white-space: nowrap;
}

.feed-text {
    color: #334155;
}

.feed-item.status-warning .feed-text {
    color: #b45309;
}

.feed-item.status-critical .feed-text {
    color: #b91c1c;
    font-weight: 600;
}

.feed-empty {
    color: #94a3b8;
    text-align: center;
    padding: 24px 0;
    font-size: 0.9em;
}

/* Плавное появление новых событий */
.feed-enter-active {
    transition: all 0.4s ease;
}

.feed-enter-from {
    opacity: 0;
    transform: translateY(-8px);
}

.feed-move {
    transition: transform 0.4s ease;
}

.feed-leave-active {
    position: absolute;
    opacity: 0;
}
</style>