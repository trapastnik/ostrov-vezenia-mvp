<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { fetchBatches, createBatch } from '../api/batches'
import { fetchOrders } from '../api/orders'
import OrderStatusBadge from '../components/OrderStatusBadge.vue'
import Pagination from '../components/Pagination.vue'
import type { Batch, Order } from '../types'
import { BATCH_STATUS_LABELS, BATCH_STATUS_COLORS } from '../types'

const router = useRouter()

// Batches list
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

// === Create batch modal ===
const showCreateModal = ref(false)
const availableOrders = ref<Order[]>([])
const ordersLoading = ref(false)
const ordersPage = ref(1)
const ordersPages = ref(1)
const ordersTotal = ref(0)
const selectedOrderIds = ref<Set<string>>(new Set())
const creating = ref(false)
const createError = ref('')
const ordersStatusFilter = ref('received_warehouse')

const selectedCount = computed(() => selectedOrderIds.value.size)

async function openCreateModal() {
  showCreateModal.value = true
  selectedOrderIds.value = new Set()
  createError.value = ''
  ordersPage.value = 1
  ordersStatusFilter.value = 'received_warehouse'
  await loadAvailableOrders()
}

async function loadAvailableOrders() {
  ordersLoading.value = true
  try {
    const data = await fetchOrders({
      page: ordersPage.value,
      per_page: 20,
      status: ordersStatusFilter.value || undefined,
    })
    availableOrders.value = data.items
    ordersPages.value = data.pages
    ordersTotal.value = data.total
  } catch (e) {
    console.error(e)
  } finally {
    ordersLoading.value = false
  }
}

function toggleOrder(id: string) {
  const s = new Set(selectedOrderIds.value)
  if (s.has(id)) s.delete(id)
  else s.add(id)
  selectedOrderIds.value = s
}

function toggleAllOnPage() {
  const allSelected = availableOrders.value.every(o => selectedOrderIds.value.has(o.id))
  const s = new Set(selectedOrderIds.value)
  if (allSelected) {
    availableOrders.value.forEach(o => s.delete(o.id))
  } else {
    availableOrders.value.forEach(o => s.add(o.id))
  }
  selectedOrderIds.value = s
}

async function handleCreate() {
  if (selectedCount.value === 0) return
  creating.value = true
  createError.value = ''
  try {
    const batch = await createBatch(Array.from(selectedOrderIds.value))
    showCreateModal.value = false
    router.push(`/batches/${batch.id}`)
  } catch (e: any) {
    createError.value = e.response?.data?.detail || 'Ошибка создания партии'
  } finally {
    creating.value = false
  }
}

function formatDate(d: string | null): string {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

function formatRub(kopecks: number): string {
  return (kopecks / 100).toLocaleString('ru-RU', { minimumFractionDigits: 0, maximumFractionDigits: 2 }) + ' \u20BD'
}

onMounted(load)
</script>

<template>
  <div>
    <h2 class="text-2xl font-bold text-gray-800 mb-6">Партии</h2>

    <!-- Create button -->
    <div class="flex items-center gap-3 mb-4">
      <button
        @click="openCreateModal"
        class="ml-auto px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 cursor-pointer"
      >
        Создать партию
      </button>
    </div>

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
          <tr
            v-for="batch in batches"
            :key="batch.id"
            @click="router.push(`/batches/${batch.id}`)"
            class="border-b border-gray-50 hover:bg-gray-50 cursor-pointer"
          >
            <td class="px-5 py-3 text-sm font-medium text-gray-800">{{ batch.number }}</td>
            <td class="px-5 py-3 text-sm text-gray-700">{{ batch.orders_count }}</td>
            <td class="px-5 py-3 text-sm text-gray-700">{{ (batch.total_weight_grams / 1000).toFixed(1) }} кг</td>
            <td class="px-5 py-3">
              <span
                :class="BATCH_STATUS_COLORS[batch.status] || 'bg-gray-100 text-gray-600'"
                class="px-2 py-0.5 rounded-full text-xs font-medium"
              >
                {{ BATCH_STATUS_LABELS[batch.status] || batch.status }}
              </span>
            </td>
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

    <!-- Create batch modal -->
    <div v-if="showCreateModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40" @click.self="showCreateModal = false">
      <div class="bg-white rounded-xl shadow-xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
        <!-- Header -->
        <div class="px-6 py-4 border-b border-gray-200 flex items-center gap-3">
          <h3 class="text-lg font-semibold text-gray-800">Создать партию</h3>
          <span class="text-sm text-gray-500">Выберите заказы для включения в партию</span>
          <button @click="showCreateModal = false" class="ml-auto text-gray-400 hover:text-gray-600 cursor-pointer text-xl">&times;</button>
        </div>

        <!-- Body -->
        <div class="flex-1 overflow-auto p-6">
          <!-- Error -->
          <div v-if="createError" class="mb-4 px-4 py-2 bg-red-50 text-red-700 rounded-lg text-sm">{{ createError }}</div>

          <!-- Status filter for orders -->
          <div class="flex items-center gap-3 mb-4">
            <select
              v-model="ordersStatusFilter"
              @change="ordersPage = 1; loadAvailableOrders()"
              class="text-sm border border-gray-300 rounded-lg px-3 py-2"
            >
              <option value="received_warehouse">На складе</option>
              <option value="accepted">Принят</option>
              <option value="">Все статусы</option>
            </select>
            <span class="text-sm text-gray-500">{{ ordersTotal }} заказов</span>
            <span v-if="selectedCount > 0" class="text-sm font-medium text-blue-600">Выбрано: {{ selectedCount }}</span>
          </div>

          <!-- Orders table -->
          <div class="bg-white rounded-lg border border-gray-200">
            <div v-if="ordersLoading" class="p-8 text-center text-gray-400">Загрузка...</div>
            <table v-else class="w-full">
              <thead>
                <tr class="text-left text-xs text-gray-500 uppercase border-b border-gray-100">
                  <th class="px-4 py-3 w-10">
                    <input
                      type="checkbox"
                      :checked="availableOrders.length > 0 && availableOrders.every(o => selectedOrderIds.has(o.id))"
                      @change="toggleAllOnPage"
                      class="cursor-pointer"
                    />
                  </th>
                  <th class="px-4 py-3">Заказ</th>
                  <th class="px-4 py-3">Получатель</th>
                  <th class="px-4 py-3 text-center">Товаров</th>
                  <th class="px-4 py-3 text-right">Сумма</th>
                  <th class="px-4 py-3 text-right">Вес</th>
                  <th class="px-4 py-3">Декларация</th>
                  <th class="px-4 py-3">Партия</th>
                  <th class="px-4 py-3">Статус</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="order in availableOrders"
                  :key="order.id"
                  @click="toggleOrder(order.id)"
                  class="border-b border-gray-50 hover:bg-blue-50 cursor-pointer"
                  :class="selectedOrderIds.has(order.id) ? 'bg-blue-50' : ''"
                >
                  <td class="px-4 py-3">
                    <input
                      type="checkbox"
                      :checked="selectedOrderIds.has(order.id)"
                      @click.stop="toggleOrder(order.id)"
                      class="cursor-pointer"
                    />
                  </td>
                  <td class="px-4 py-3 text-sm font-medium text-gray-800">{{ order.external_order_id }}</td>
                  <td class="px-4 py-3 text-sm text-gray-700">{{ order.recipient_name }}</td>
                  <td class="px-4 py-3 text-sm text-gray-500 text-center">{{ order.items.length }}</td>
                  <td class="px-4 py-3 text-sm text-gray-700 text-right">{{ formatRub(order.total_amount_kopecks) }}</td>
                  <td class="px-4 py-3 text-sm text-gray-700 text-right">{{ (order.total_weight_grams / 1000).toFixed(1) }} кг</td>
                  <td class="px-4 py-3">
                    <span v-if="order.customs_declaration_number" class="text-xs text-orange-600 font-medium">
                      {{ order.customs_declaration_number }}
                    </span>
                    <span v-else class="text-xs text-gray-300">—</span>
                  </td>
                  <td class="px-4 py-3">
                    <span v-if="order.batch_id" class="text-xs text-purple-600 font-medium">Да</span>
                    <span v-else class="text-xs text-gray-300">—</span>
                  </td>
                  <td class="px-4 py-3"><OrderStatusBadge :status="order.status" /></td>
                </tr>
                <tr v-if="availableOrders.length === 0">
                  <td colspan="9" class="px-4 py-8 text-center text-sm text-gray-400">Нет заказов с этим статусом</td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- Orders pagination -->
          <div v-if="ordersPages > 1" class="flex items-center justify-center gap-2 mt-3">
            <button
              v-for="p in ordersPages"
              :key="p"
              @click="ordersPage = p; loadAvailableOrders()"
              :class="ordersPage === p ? 'bg-blue-600 text-white' : 'text-gray-600 hover:bg-gray-100'"
              class="w-8 h-8 rounded-lg text-sm cursor-pointer"
            >{{ p }}</button>
          </div>
        </div>

        <!-- Footer -->
        <div class="px-6 py-4 border-t border-gray-200 flex items-center gap-3">
          <button
            @click="handleCreate"
            :disabled="creating || selectedCount === 0"
            class="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 disabled:opacity-50 cursor-pointer"
          >
            {{ creating ? 'Создание...' : `Создать партию (${selectedCount} заказов)` }}
          </button>
          <button @click="showCreateModal = false" class="px-4 py-2 text-sm text-gray-600 hover:text-gray-800 cursor-pointer">
            Отмена
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
