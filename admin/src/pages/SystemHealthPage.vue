<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { fetchHealth, runSystemTests } from '../api/health'
import type { HealthResponse, SystemTestsResponse, ServiceStatus } from '../api/health'

const health = ref<HealthResponse | null>(null)
const testResults = ref<SystemTestsResponse | null>(null)
const loadingHealth = ref(false)
const loadingTests = ref(false)
const healthError = ref('')
const lastRefreshed = ref<Date | null>(null)

function formatUptime(seconds: number): string {
  const d = Math.floor(seconds / 86400)
  const h = Math.floor((seconds % 86400) / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = seconds % 60
  if (d > 0) return `${d}д ${h}ч ${m}м`
  if (h > 0) return `${h}ч ${m}м ${s}с`
  if (m > 0) return `${m}м ${s}с`
  return `${s}с`
}

function serviceStatusColor(status: ServiceStatus['status']): string {
  return {
    ok: 'bg-green-100 text-green-800 border-green-200',
    error: 'bg-red-100 text-red-800 border-red-200',
    unknown: 'bg-gray-100 text-gray-600 border-gray-200',
  }[status]
}

function serviceStatusDot(status: ServiceStatus['status']): string {
  return {
    ok: 'bg-green-500',
    error: 'bg-red-500',
    unknown: 'bg-gray-400',
  }[status]
}

function serviceStatusLabel(status: ServiceStatus['status']): string {
  return {
    ok: 'OK',
    error: 'ОШИБКА',
    unknown: '—',
  }[status]
}

function testStatusColor(status: 'pass' | 'fail' | 'skip'): string {
  return {
    pass: 'text-green-700 bg-green-50',
    fail: 'text-red-700 bg-red-50',
    skip: 'text-gray-500 bg-gray-50',
  }[status]
}

function testStatusIcon(status: 'pass' | 'fail' | 'skip'): string {
  return {
    pass: '✓',
    fail: '✗',
    skip: '—',
  }[status]
}

const overallStatus = computed<'healthy' | 'degraded' | 'down'>(() => {
  if (!health.value) return 'down'
  const statuses = health.value.services.map((s) => s.status)
  if (statuses.every((s) => s === 'ok')) return 'healthy'
  if (statuses.some((s) => s === 'error')) return 'degraded'
  return 'degraded'
})

const overallStatusLabel = computed(() => {
  return {
    healthy: 'Все системы работают',
    degraded: 'Частичный сбой',
    down: 'Недоступно',
  }[overallStatus.value]
})

const overallStatusClass = computed(() => {
  return {
    healthy: 'bg-green-500',
    degraded: 'bg-yellow-500',
    down: 'bg-red-500',
  }[overallStatus.value]
})

async function loadHealth() {
  loadingHealth.value = true
  healthError.value = ''
  try {
    health.value = await fetchHealth()
    lastRefreshed.value = new Date()
  } catch (e: unknown) {
    if (e instanceof Error) {
      healthError.value = e.message
    } else {
      healthError.value = 'Ошибка загрузки'
    }
  } finally {
    loadingHealth.value = false
  }
}

async function runTests() {
  loadingTests.value = true
  try {
    testResults.value = await runSystemTests()
  } catch (e: unknown) {
    // нечего делать — тесты могут вернуть ошибку
  } finally {
    loadingTests.value = false
  }
}

onMounted(() => {
  loadHealth()
})
</script>

<template>
  <div class="p-6 space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Здоровье системы</h1>
        <p v-if="lastRefreshed" class="text-sm text-gray-400 mt-0.5">
          Обновлено: {{ lastRefreshed.toLocaleTimeString('ru-RU') }}
        </p>
      </div>
      <button
        @click="loadHealth"
        :disabled="loadingHealth"
        class="flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 rounded-lg text-sm text-gray-700 hover:bg-gray-50 transition-colors disabled:opacity-50"
      >
        <span :class="loadingHealth ? 'animate-spin' : ''">↻</span>
        Обновить
      </button>
    </div>

    <!-- Error -->
    <div v-if="healthError" class="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700 text-sm">
      Ошибка загрузки: {{ healthError }}
    </div>

    <!-- Overall Status Banner -->
    <div v-if="health" class="rounded-xl border p-5 flex items-center gap-4"
         :class="overallStatus === 'healthy' ? 'bg-green-50 border-green-200' : overallStatus === 'degraded' ? 'bg-yellow-50 border-yellow-200' : 'bg-red-50 border-red-200'">
      <div class="w-4 h-4 rounded-full flex-shrink-0 animate-pulse" :class="overallStatusClass"></div>
      <div class="flex-1">
        <div class="font-semibold text-gray-900 text-lg">{{ overallStatusLabel }}</div>
        <div class="text-sm text-gray-500">v{{ health.version }} · Аптайм: {{ formatUptime(health.uptime_seconds) }}</div>
      </div>
    </div>

    <!-- Skeleton while loading -->
    <div v-else-if="loadingHealth" class="rounded-xl border bg-gray-50 p-5 animate-pulse">
      <div class="h-6 bg-gray-200 rounded w-64 mb-2"></div>
      <div class="h-4 bg-gray-100 rounded w-40"></div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Services -->
      <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div class="px-5 py-4 border-b border-gray-100">
          <h2 class="font-semibold text-gray-800">Сервисы</h2>
        </div>
        <div v-if="health" class="divide-y divide-gray-50">
          <div
            v-for="svc in health.services"
            :key="svc.name"
            class="px-5 py-4 flex items-center gap-3"
          >
            <div class="w-2.5 h-2.5 rounded-full flex-shrink-0" :class="serviceStatusDot(svc.status)"></div>
            <div class="flex-1 min-w-0">
              <div class="font-medium text-gray-800 text-sm">{{ svc.name }}</div>
              <div v-if="svc.detail" class="text-xs text-gray-400 truncate">{{ svc.detail }}</div>
            </div>
            <div class="flex items-center gap-2 flex-shrink-0">
              <span v-if="svc.latency_ms !== undefined" class="text-xs text-gray-400">{{ svc.latency_ms }}мс</span>
              <span
                class="px-2 py-0.5 rounded text-xs font-medium border"
                :class="serviceStatusColor(svc.status)"
              >{{ serviceStatusLabel(svc.status) }}</span>
            </div>
          </div>
        </div>
        <div v-else-if="loadingHealth" class="px-5 py-4 space-y-4 animate-pulse">
          <div v-for="i in 3" :key="i" class="flex items-center gap-3">
            <div class="w-2.5 h-2.5 rounded-full bg-gray-200"></div>
            <div class="flex-1 h-4 bg-gray-100 rounded"></div>
            <div class="w-16 h-5 bg-gray-100 rounded"></div>
          </div>
        </div>
      </div>

      <!-- Stats -->
      <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div class="px-5 py-4 border-b border-gray-100">
          <h2 class="font-semibold text-gray-800">Статистика</h2>
        </div>
        <div v-if="health" class="grid grid-cols-2 divide-x divide-y divide-gray-100">
          <div class="px-5 py-5">
            <div class="text-3xl font-bold text-gray-900">{{ health.stats.orders_total }}</div>
            <div class="text-xs text-gray-500 mt-1">Заказов всего</div>
          </div>
          <div class="px-5 py-5">
            <div class="text-3xl font-bold text-blue-600">{{ health.stats.orders_today }}</div>
            <div class="text-xs text-gray-500 mt-1">Заказов сегодня</div>
          </div>
          <div class="px-5 py-5">
            <div class="text-3xl font-bold text-gray-900">{{ health.stats.shops_total }}</div>
            <div class="text-xs text-gray-500 mt-1">Магазинов</div>
          </div>
          <div class="px-5 py-5">
            <div class="text-3xl font-bold text-gray-900">{{ health.stats.batches_total }}</div>
            <div class="text-xs text-gray-500 mt-1">Партий</div>
          </div>
        </div>
        <div v-else-if="loadingHealth" class="grid grid-cols-2 divide-x divide-y divide-gray-100 animate-pulse">
          <div v-for="i in 4" :key="i" class="px-5 py-5">
            <div class="h-8 bg-gray-200 rounded w-16 mb-2"></div>
            <div class="h-3 bg-gray-100 rounded w-24"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- System Tests -->
    <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div class="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
        <div>
          <h2 class="font-semibold text-gray-800">Системные тесты</h2>
          <p class="text-xs text-gray-400 mt-0.5">Проверяет БД, Redis, API Почты, JWT</p>
        </div>
        <div class="flex items-center gap-3">
          <!-- Summary badges after run -->
          <template v-if="testResults">
            <span class="px-2.5 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
              ✓ {{ testResults.passed }} прошло
            </span>
            <span v-if="testResults.failed > 0" class="px-2.5 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">
              ✗ {{ testResults.failed }} упало
            </span>
          </template>
          <button
            @click="runTests"
            :disabled="loadingTests"
            class="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
          >
            <span v-if="loadingTests" class="animate-spin">↻</span>
            {{ loadingTests ? 'Выполняю...' : 'Запустить тесты' }}
          </button>
        </div>
      </div>

      <!-- Test results -->
      <div v-if="testResults" class="divide-y divide-gray-50">
        <div
          v-for="result in testResults.results"
          :key="result.name"
          class="px-5 py-3.5 flex items-center gap-3"
        >
          <span
            class="w-6 h-6 rounded flex items-center justify-center text-sm font-bold flex-shrink-0"
            :class="testStatusColor(result.status)"
          >{{ testStatusIcon(result.status) }}</span>
          <div class="flex-1 min-w-0">
            <div class="text-sm font-medium text-gray-800">{{ result.name }}</div>
            <div v-if="result.detail" class="text-xs text-gray-400 truncate">{{ result.detail }}</div>
          </div>
          <div v-if="result.duration_ms > 0" class="text-xs text-gray-400 flex-shrink-0">
            {{ result.duration_ms }}мс
          </div>
        </div>
      </div>

      <!-- Empty state -->
      <div v-else class="px-5 py-8 text-center text-gray-400 text-sm">
        Нажмите «Запустить тесты» для проверки всех подсистем
      </div>
    </div>
  </div>
</template>
