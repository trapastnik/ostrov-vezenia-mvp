<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { fetchBatches } from '../api/batches'
import OrderStatusBadge from '../components/OrderStatusBadge.vue'
import Pagination from '../components/Pagination.vue'
import type { Batch } from '../types'

const batches = ref<Batch[]>([])
const loading = ref(true)
const page = ref(1)
const pages = ref(1)
const total = ref(0)

async function load() {
  loading.value = true
  try {
    const data = await fetchBatches(page.value)
    batches.value = data.items
    pages.value = data.pages
    total.value = data.total
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

onMounted(load)

function formatDate(d: string | null): string {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}
</script>

<template>
  <div>
    <h2 class="text-2xl font-bold text-gray-800 mb-6">Партии</h2>

    <div class="bg-white rounded-xl border border-gray-200">
      <div v-if="loading" class="p-8 text-center text-gray-400">Загрузка...</div>
      <table v-else class="w-full">
        <thead>
          <tr class="text-left text-xs text-gray-500 uppercase border-b border-gray-100">
            <th class="px-5 py-3">Номер</th>
            <th class="px-5 py-3">Заказов</th>
            <th class="px-5 py-3">Вес</th>
            <th class="px-5 py-3">Статус</th>
            <th class="px-5 py-3">Создана</th>
            <th class="px-5 py-3">Отправлена</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="batch in batches" :key="batch.id" class="border-b border-gray-50 hover:bg-gray-50">
            <td class="px-5 py-3 text-sm font-medium text-gray-800">{{ batch.number }}</td>
            <td class="px-5 py-3 text-sm text-gray-700">{{ batch.orders_count }}</td>
            <td class="px-5 py-3 text-sm text-gray-700">{{ (batch.total_weight_grams / 1000).toFixed(1) }} кг</td>
            <td class="px-5 py-3"><OrderStatusBadge :status="batch.status" /></td>
            <td class="px-5 py-3 text-sm text-gray-500">{{ formatDate(batch.created_at) }}</td>
            <td class="px-5 py-3 text-sm text-gray-500">{{ formatDate(batch.shipped_at) }}</td>
          </tr>
          <tr v-if="batches.length === 0">
            <td colspan="6" class="px-5 py-8 text-center text-sm text-gray-400">Нет партий</td>
          </tr>
        </tbody>
      </table>
    </div>

    <Pagination :page="page" :pages="pages" :total="total" @update:page="p => { page = p; load() }" />
  </div>
</template>
