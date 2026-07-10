<template>
    <div>
        <h1>Dashboard</h1>
        <p v-if="authStore.user">Welcome, {{ authStore.user.email }}!</p>
        <p v-else>Loading user data...</p>
        <button @click="handleLogout">Logout</button>
        <p>Here will be your protected data later.</p>
    </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const authStore = useAuthStore()
const router = useRouter()

// Убедимся, что данные пользователя загружены
onMounted(async () => {
    if (authStore.isAuthenticated && !authStore.user) {
        await authStore.fetchUser()
    }
})

async function handleLogout() {
    await authStore.logout()
    router.push('/login')
}
</script>
