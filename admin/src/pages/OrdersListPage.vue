<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { fetchOrders } from '../api/orders'
import OrderStatusBadge from '../components/OrderStatusBadge.vue'
import Pagination from '../components/Pagination.vue'
import { STATUS_LABELS } from '../types'
import type { Order } from '../types'

const router = useRouter()
const orders = ref<Order[]>([])
const loading = ref(true)
const page = ref(1)
const pages = ref(1)
const total = ref(0)
const statusFilter = ref('')
const search = ref('')

async function load() {
  loading.value = true
  try {
    const data = await fetchOrders({
      page: page.value,
      per_page: 20,
      status: statusFilter.value || undefined,
      search: search.value || undefined,
    })
    orders.value = data.items
    pages.value = data.pages
    total.value = data.total
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

onMounted(load)
watch([page, statusFilter], load)

function doSearch() {
  page.value = 1
  load()
}

function kopecksToRubles(k: number): string {
  return (k / 100).toFixed(2)
}

function formatDate(d: string): string {
  return new Date(d).toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}
</script>

<template>
  <div>
    <h2 class="text-2xl font-bold text-gray-800 mb-6">Заказы</h2>

    <div class="flex gap-3 mb-4">
      <select v-model="statusFilter" class="border border-gray-300 rounded-lg px-3 py-2 text-sm">
        <option value="">Все статусы</option>
        <option v-for="(label, key) in STATUS_LABELS" :key="key" :value="key">{{ label }}</option>
      </select>
      <input
        v-model="search"
        @keyup.enter="doSearch"
        placeholder="Поиск по имени, номеру заказа, треку..."
        class="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm"
      />
      <button @click="doSearch" class="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 cursor-pointer">Найти</button>
    </div>

    <div class="bg-white rounded-xl border border-gray-200">
      <div v-if="loading" class="p-8 text-center text-gray-400">Загрузка...</div>
      <table v-else class="w-full">
        <thead>
          <tr class="text-left text-xs text-gray-500 uppercase border-b border-gray-100">
            <th class="px-5 py-3">Заказ</th>
            <th class="px-5 py-3">Магазин</th>
            <th class="px-5 py-3">Получатель</th>
            <th class="px-5 py-3 text-center">SKU</th>
            <th class="px-5 py-3">Сумма</th>
            <th class="px-5 py-3">Статус</th>
            <th class="px-5 py-3">Дата</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="order in orders"
            :key="order.id"
            @click="router.push(`/orders/${order.id}`)"
            class="border-b border-gray-50 hover:bg-blue-50 cursor-pointer"
          >
            <td class="px-5 py-3 text-sm font-medium text-blue-600">{{ order.external_order_id }}</td>
            <td class="px-5 py-3 text-sm text-gray-600">{{ order.shop_name || '—' }}</td>
            <td class="px-5 py-3 text-sm text-gray-700">{{ order.recipient_name }}</td>
            <td class="px-5 py-3 text-sm text-gray-500 text-center">{{ order.items.length }}</td>
            <td class="px-5 py-3 text-sm text-gray-700">{{ kopecksToRubles(order.total_amount_kopecks) }} &#8381;</td>
            <td class="px-5 py-3"><OrderStatusBadge :status="order.status" /></td>
            <td class="px-5 py-3 text-sm text-gray-500">{{ formatDate(order.created_at) }}</td>
          </tr>
          <tr v-if="orders.length === 0">
            <td colspan="7" class="px-5 py-8 text-center text-sm text-gray-400">Нет заказов</td>
          </tr>
        </tbody>
      </table>
    </div>

    <Pagination :page="page" :pages="pages" :total="total" @update:page="p => page = p" />
  </div>
</template>
