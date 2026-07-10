<template>
    <div class="auth-form">
        <h2>Login</h2>
        <form @submit.prevent="handleLogin">
            <div>
                <label>Email:</label>
                <input v-model="email" type="email" required />
            </div>
            <div>
                <label>Password:</label>
                <input v-model="password" type="password" required />
            </div>
            <button type="submit" :disabled="loading">Log In</button>
        </form>
        <p v-if="error" class="error">{{ error }}</p>
        <p>
            Don't have an account? <router-link to="/register">Register</router-link>
        </p>
    </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const email = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

const router = useRouter()
const authStore = useAuthStore()

async function handleLogin() {
    error.value = ''
    loading.value = true
    try {
        await authStore.login(email.value, password.value)
        router.push('/')
    } catch (e) {
        error.value = e.response?.data?.detail || 'Login failed'
    } finally {
        loading.value = false
    }
}
</script>

<style scoped>
.auth-form {
    max-width: 400px;
    margin: 50px auto;
    padding: 20px;
    background: white;
    border-radius: 5px;
}
.error {
    color: red;
}
</style>
