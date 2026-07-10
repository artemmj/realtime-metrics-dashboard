import axios from 'axios'
import { useAuthStore } from '../stores/auth'

const api = axios.create({
    baseURL: 'http://localhost/api/v1',
    headers: {
        'Content-Type': 'application/json'
    }
})

// Интерсептор для добавления токена к каждому запросу
api.interceptors.request.use(
    (config) => {
        const authStore = useAuthStore()
        if (authStore.token) {
            config.headers.Authorization = authStore.token
        }
        return config
    },
    (error) => Promise.reject(error)
)

// Можно добавить интерсептор ответа для обработки 401
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            const authStore = useAuthStore()
            authStore.logout()
            window.location.href = '/login'
        }
        return Promise.reject(error)
    }
)

export default api
