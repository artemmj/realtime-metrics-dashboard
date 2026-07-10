import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../api'

export const useAuthStore = defineStore('auth', () => {
    const token = ref(localStorage.getItem('token') || '')
    const user = ref(null)

    const isAuthenticated = computed(() => !!token.value)

    // Загружаем данные пользователя при наличии токена
    async function fetchUser() {
        if (!token.value) return
        try {
            const response = await api.get('/users/me')
            user.value = response.data
        } catch (error) {
            console.error('Failed to fetch user:', error)
            logout()
        }
    }

    async function login(email, password) {
        const response = await api.post('/auth/login', { email, password })
        token.value = response.data.token
        localStorage.setItem('token', token.value)
        // Можно сразу запросить /me, но в нашем ответе login нет данных пользователя
        await fetchUser()
    }

    async function register(email, password) {
        const response = await api.post('/auth/register', { email, password })
        // После регистрации не авторизуем автоматически, просто возвращаем данные
        return response.data
    }

    async function logout() {
        try {
            // Опционально вызываем API логаута
            await api.get('/auth/logout')
        } catch (e) {
            console.warn('Logout API call failed:', e)
        } finally {
            token.value = ''
            user.value = null
            localStorage.removeItem('token')
        }
    }

    return {
        token,
        user,
        isAuthenticated,
        login,
        register,
        logout,
        fetchUser
    }
})
