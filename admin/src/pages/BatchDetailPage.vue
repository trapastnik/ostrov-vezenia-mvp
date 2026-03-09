<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { fetchBatch, changeBatchStatus } from '../api/batches'
import OrderStatusBadge from '../components/OrderStatusBadge.vue'
import type { BatchDetail } from '../types'
import { BATCH_STATUS_LABELS, BATCH_STATUS_COLORS, BATCH_ALLOWED_TRANSITIONS } from '../types'

const route = useRoute()

const batch = ref<BatchDetail | null>(null)
const loading = ref(true)
const error = ref('')
const actionMsg = ref('')
const actionError = ref('')
const changing = ref(false)

const nextStatus = computed(() => {
  if (!batch.value) return null
  return BATCH_ALLOWED_TRANSITIONS[batch.value.status] || null
})

const nextStatusLabel = computed(() => {
  if (!nextStatus.value) return ''
  const labels: Record<string, string> = {
    customs_presented: 'На таможню',
    customs_cleared: 'Таможня пройдена',
    shipped: 'Отправить',
  }
  return labels[nextStatus.value] || BATCH_STATUS_LABELS[nextStatus.value] || nextStatus.value
})

async function load() {
  loading.value = true
  error.value = ''
  try {
    batch.value = await fetchBatch(route.params.id as string)
  } catch (e: any) {
    error.value = e.response?.data?.detail || 'Ошибка загрузки'
  } finally {
    loading.value = false
  }
}

async function handleStatusChange() {
  if (!nextStatus.value || changing.value) return
  changing.value = true
  actionMsg.value = ''
  actionError.value = ''
  try {
    await changeBatchStatus(route.params.id as string, nextStatus.value)
    await load()
    actionMsg.value = `Статус изменён на «${BATCH_STATUS_LABELS[nextStatus.value] || nextStatus.value}»`
    setTimeout(() => (actionMsg.value = ''), 3000)
  } catch (e: any) {
    actionError.value = e.response?.data?.detail || 'Ошибка смены статуса'
  } finally {
    changing.value = false
  }
}

function formatDate(d: string | null): string {
  if (!d) return '—'
  return new Date(d).toLocaleString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

function formatRub(kopecks: number): string {
  return (kopecks / 100).toLocaleString('ru-RU', { minimumFractionDigits: 0, maximumFractionDigits: 2 }) + ' ₽'
}

onMounted(load)
</script>

<template>
  <div class="p-6">
    <!-- Back -->
    <router-link to="/batches" class="text-blue-600 hover:text-blue-800 text-sm mb-4 inline-block">
      ← К списку партий
    </router-link>

    <!-- Loading -->
    <div v-if="loading" class="flex justify-center py-12">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="bg-red-50 border border-red-200 text-red-700 p-4 rounded-lg">
      {{ error }}
    </div>

    <!-- Content -->
    <div v-else-if="batch">
      <!-- Header -->
      <div class="flex items-center justify-between mb-6">
        <div class="flex items-center gap-4">
          <h1 class="text-2xl font-bold text-gray-900">Партия {{ batch.number }}</h1>
          <span
            class="px-3 py-1 rounded-full text-sm font-medium"
            :class="BATCH_STATUS_COLORS[batch.status] || 'bg-gray-100 text-gray-600'"
          >
            {{ BATCH_STATUS_LABELS[batch.status] || batch.status }}
          </span>
        </div>
        <button
          v-if="nextStatus"
          @click="handleStatusChange"
          :disabled="changing"
          class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {{ changing ? 'Обработка...' : nextStatusLabel }}
        </button>
      </div>

      <!-- Messages -->
      <div v-if="actionMsg" class="mb-4 bg-green-50 border border-green-200 text-green-700 p-3 rounded-lg">
        {{ actionMsg }}
      </div>
      <div v-if="actionError" class="mb-4 bg-red-50 border border-red-200 text-red-700 p-3 rounded-lg">
        {{ actionError }}
      </div>

      <!-- Summary cards -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div class="bg-white border border-gray-200 rounded-lg p-4">
          <div class="text-sm text-gray-500">Заказов</div>
          <div class="text-2xl font-bold text-gray-900">{{ batch.orders_count }}</div>
        </div>
        <div class="bg-white border border-gray-200 rounded-lg p-4">
          <div class="text-sm text-gray-500">Вес</div>
          <div class="text-2xl font-bold text-gray-900">{{ (batch.total_weight_grams / 1000).toFixed(1) }} кг</div>
        </div>
        <div class="bg-white border border-gray-200 rounded-lg p-4">
          <div class="text-sm text-gray-500">Создана</div>
          <div class="text-lg font-semibold text-gray-900">{{ formatDate(batch.created_at) }}</div>
        </div>
        <div class="bg-white border border-gray-200 rounded-lg p-4">
          <div class="text-sm text-gray-500">Отправлена</div>
          <div class="text-lg font-semibold text-gray-900">{{ formatDate(batch.shipped_at) }}</div>
        </div>
      </div>

      <!-- Dates timeline -->
      <div v-if="batch.customs_presented_at || batch.customs_cleared_at" class="bg-white border border-gray-200 rounded-lg p-4 mb-6">
        <h3 class="text-sm font-medium text-gray-500 mb-2">Хронология</h3>
        <div class="flex flex-wrap gap-6 text-sm">
          <div v-if="batch.customs_presented_at">
            <span class="text-gray-500">На таможне:</span>
            <span class="ml-1 font-medium">{{ formatDate(batch.customs_presented_at) }}</span>
          </div>
          <div v-if="batch.customs_cleared_at">
            <span class="text-gray-500">Таможня пройдена:</span>
            <span class="ml-1 font-medium">{{ formatDate(batch.customs_cleared_at) }}</span>
          </div>
          <div v-if="batch.shipped_at">
            <span class="text-gray-500">Отправлена:</span>
            <span class="ml-1 font-medium">{{ formatDate(batch.shipped_at) }}</span>
          </div>
        </div>
      </div>

      <!-- Orders table -->
      <div class="bg-white border border-gray-200 rounded-lg overflow-hidden">
        <div class="px-4 py-3 border-b border-gray-200">
          <h3 class="text-lg font-semibold text-gray-900">Заказы в партии</h3>
        </div>
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead class="bg-gray-50 text-gray-600 text-left">
              <tr>
                <th class="px-4 py-3">#</th>
                <th class="px-4 py-3">Номер заказа</th>
                <th class="px-4 py-3">Получатель</th>
                <th class="px-4 py-3">Индекс</th>
                <th class="px-4 py-3 text-right">Товаров</th>
                <th class="px-4 py-3 text-right">Сумма</th>
                <th class="px-4 py-3 text-right">Вес</th>
                <th class="px-4 py-3">Статус</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-100">
              <tr v-for="(order, idx) in batch.orders" :key="order.id" class="hover:bg-gray-50">
                <td class="px-4 py-3 text-gray-400">{{ idx + 1 }}</td>
                <td class="px-4 py-3">
                  <router-link :to="`/orders/${order.id}`" class="text-blue-600 hover:text-blue-800 font-medium">
                    {{ order.external_order_id }}
                  </router-link>
                </td>
                <td class="px-4 py-3">{{ order.recipient_name }}</td>
                <td class="px-4 py-3 text-gray-500">{{ order.recipient_postal_code }}</td>
                <td class="px-4 py-3 text-right">{{ order.items.length }}</td>
                <td class="px-4 py-3 text-right">{{ formatRub(order.total_amount_kopecks) }}</td>
                <td class="px-4 py-3 text-right">{{ (order.total_weight_grams / 1000).toFixed(1) }} кг</td>
                <td class="px-4 py-3">
                  <OrderStatusBadge :status="order.status" />
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-if="batch.orders.length === 0" class="p-8 text-center text-gray-400">
          Нет заказов в партии
        </div>
      </div>
    </div>
  </div>
</template>
