import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../api/client'
import type { Operator } from '../types'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const operator = ref<Operator | null>(
    JSON.parse(localStorage.getItem('operator') || 'null')
  )

  const isAuthenticated = computed(() => !!token.value)
  const isAdmin = computed(() => operator.value?.role === 'admin')

  async function login(email: string, password: string) {
    const { data } = await api.post('/auth/login', { email, password })
    token.value = data.access_token
    operator.value = data.operator
    localStorage.setItem('token', data.access_token)
    localStorage.setItem('operator', JSON.stringify(data.operator))
  }

  function logout() {
    token.value = ''
    operator.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('operator')
  }

  return { token, operator, isAuthenticated, isAdmin, login, logout }
})
