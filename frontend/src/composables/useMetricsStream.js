import { reactive } from 'vue'

// Цвета метрик — общие для карточек и графика
export const METRIC_COLORS = {
  cpu_usage: '#3b82f6',
  memory_usage: '#8b5cf6',
  active_users: '#10b981',
  requests_per_sec: '#f59e0b',
}

const MAX_POINTS = 60 // точек на метрику для графиков
const MAX_EVENTS = 50 // событий в живой ленте

// Модульный синглтон: один WS-поток на всё приложение
const state = reactive({
  connected: false,
  definitions: {}, // name -> определение с бэкенда (юнит, диапазоны, пороги)
  latest: {}, // name -> последнее значение { id, value, delta, status, text, timestamp }
  series: {}, // name -> [{ t, v }] — буфер точек для графиков
  events: [], // [{ id, name, text, status, timestamp }] — живая лента
})

let ws = null
let reconnectTimeout = null
let reconnectAttempts = 0

function ensureSeries(name) {
  if (!state.series[name]) state.series[name] = []
}

function makeLatest(item) {
  return {
    id: item.id,
    value: item.value,
    delta: item.delta,
    status: item.status,
    text: item.text,
    timestamp: item.timestamp,
  }
}

function applyUpdate(data) {
  if (!data || !data.name) return
  ensureSeries(data.name)

  state.series[data.name].push({ t: data.timestamp, v: data.value })
  if (state.series[data.name].length > MAX_POINTS) {
    state.series[data.name].shift()
  }

  state.latest[data.name] = makeLatest(data)

  state.events.unshift({
    id: data.id,
    name: data.name,
    text: data.text,
    status: data.status,
    timestamp: data.timestamp,
  })
  if (state.events.length > MAX_EVENTS) state.events.pop()
}

function applyHistory(items) {
  for (const item of items || []) {
    ensureSeries(item.name)
    state.series[item.name].push({ t: item.timestamp, v: item.value })
    state.latest[item.name] = makeLatest(item)
  }

  // Обрезаем серии до MAX_POINTS
  for (const name of Object.keys(state.series)) {
    if (state.series[name].length > MAX_POINTS) {
      state.series[name] = state.series[name].slice(-MAX_POINTS)
    }
  }
}

function applyDefinitions(defs) {
  for (const def of defs || []) {
    state.definitions[def.name] = def
  }
}

function handleMessage(event) {
  let message
  try {
    message = JSON.parse(event.data)
  } catch {
    console.warn('Failed to parse WebSocket message:', event.data)
    return
  }

  switch (message.type) {
    case 'ping':
      return
    case 'hello':
      return applyDefinitions(message.definitions)
    case 'history':
      return applyHistory(message.data)
    case 'metric_update':
      return applyUpdate(message.data)
    default:
      console.warn('Unknown WebSocket message type:', message.type)
  }
}

function connect() {
  if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) {
    return
  }

  const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
  ws = new WebSocket(`${protocol}://${window.location.host}/api/v1/metrics/ws`)

  ws.onopen = () => {
    state.connected = true
    reconnectAttempts = 0
  }

  ws.onmessage = handleMessage

  ws.onclose = () => {
    state.connected = false
    // Переподключение с нарастающей задержкой
    const delay = Math.min(3000 + reconnectAttempts * 2000, 15000)
    reconnectAttempts += 1
    reconnectTimeout = setTimeout(connect, delay)
  }

  ws.onerror = (error) => {
    console.error('WebSocket error:', error)
  }
}

function disconnect() {
  if (reconnectTimeout) {
    clearTimeout(reconnectTimeout)
    reconnectTimeout = null
  }
  reconnectAttempts = 0
  if (ws) {
    ws.close()
    ws = null
  }
}

export function useMetricsStream() {
  return { state, connect, disconnect }
}