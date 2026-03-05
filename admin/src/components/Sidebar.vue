<script setup lang="ts">
import { useAuthStore } from '../stores/auth'
import { useRouter } from 'vue-router'

const auth = useAuthStore()
const router = useRouter()

const appVersion = __APP_VERSION__

function logout() {
  auth.logout()
  router.push('/login')
}

const navItems = [
  { name: 'Главная', path: '/', icon: '◻' },
  { name: 'Заказы', path: '/orders', icon: '📦' },
  { name: 'Партии', path: '/batches', icon: '📋' },
  { name: 'Магазины', path: '/shops', icon: '🏪', admin: true },
  { name: 'Таможня (ДТЭГ)', path: '/customs', icon: '🛃', admin: true },
  { name: 'Группы отправок', path: '/groups', icon: '📦' },
  { name: 'Почта API', path: '/pochta', icon: '📮', admin: true },
  { name: 'Здоровье системы', path: '/system-health', icon: '🩺', admin: true },
]
</script>

<template>
  <aside class="w-64 bg-white border-r border-gray-200 flex flex-col">
    <div class="p-4 border-b border-gray-200">
      <h1 class="text-lg font-bold text-gray-800">Остров Везения</h1>
      <p class="text-xs text-gray-500 mt-1">Панель управления</p>
    </div>

    <nav class="flex-1 p-3 space-y-1">
      <router-link
        v-for="item in navItems"
        :key="item.path"
        :to="item.path"
        v-show="!item.admin || auth.isAdmin"
        class="flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-gray-700 hover:bg-gray-100 transition-colors"
        active-class="bg-blue-50 text-blue-700 font-medium"
      >
        <span>{{ item.icon }}</span>
        <span>{{ item.name }}</span>
      </router-link>
    </nav>

    <div class="p-4 border-t border-gray-200">
      <div class="text-sm text-gray-700 font-medium">{{ auth.operator?.name }}</div>
      <div class="text-xs text-gray-500">{{ auth.operator?.role === 'admin' ? 'Администратор' : 'Оператор' }}</div>
      <button @click="logout" class="mt-2 text-xs text-red-600 hover:text-red-800 cursor-pointer">
        Выйти
      </button>
      <div class="mt-3 text-xs text-gray-300">v{{ appVersion }}</div>
    </div>
  </aside>
</template>
