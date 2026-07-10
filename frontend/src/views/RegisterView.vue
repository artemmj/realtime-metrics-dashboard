<template>
    <div class="auth-form">
        <h2>Register</h2>
        <form @submit.prevent="handleRegister">
            <div>
                <label>Email:</label>
                <input v-model="email" type="email" required />
            </div>
            <div>
                <label>Password:</label>
                <input v-model="password" type="password" required />
            </div>
            <button type="submit" :disabled="loading">Register</button>
        </form>
        <p v-if="error" class="error">{{ error }}</p>
        <p v-if="success" class="success">Registration successful! You can now <router-link to="/login">login</router-link>.</p>
        <p>
            Already have an account? <router-link to="/login">Login</router-link>
        </p>
    </div>
</template>

<script setup>
import { ref } from 'vue'
import { useAuthStore } from '../stores/auth'

const email = ref('')
const password = ref('')
const error = ref('')
const success = ref(false)
const loading = ref(false)

const authStore = useAuthStore()

async function handleRegister() {
    error.value = ''
    success.value = false
    loading.value = true
    try {
        await authStore.register(email.value, password.value)
        success.value = true
        email.value = ''
        password.value = ''
    } catch (e) {
        error.value = e.response?.data?.detail || 'Registration failed'
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
.success {
    color: green;
}
</style>
