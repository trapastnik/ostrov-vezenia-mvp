<script setup lang="ts">
import { ref, onMounted, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { fetchOrders } from '../api/orders'
import OrderStatusBadge from '../components/OrderStatusBadge.vue'
import Pagination from '../components/Pagination.vue'
import { STATUS_LABELS, DECLARATION_STATUS_COLORS } from '../types'
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
    nextTick(applyColumnWidths)
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

// ---------- Resizable columns ----------
const STORAGE_KEY = 'orders-col-widths'
const tableRef = ref<HTMLTableElement | null>(null)

const defaultWidths: Record<string, number> = {
  order: 120,
  shop: 120,
  recipient: 200,
  sku: 60,
  amount: 100,
  status: 100,
  declaration: 140,
  date: 120,
}

const colKeys = Object.keys(defaultWidths)

function getSavedWidths(): Record<string, number> {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) return { ...defaultWidths, ...JSON.parse(raw) }
  } catch { /* ignore */ }
  return { ...defaultWidths }
}

function saveWidths(w: Record<string, number>) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(w))
}

function applyColumnWidths() {
  if (!tableRef.value) return
  const widths = getSavedWidths()
  const ths = tableRef.value.querySelectorAll<HTMLTableCellElement>('thead th')
  ths.forEach((th, i) => {
    const key = colKeys[i]
    if (key && widths[key]) {
      th.style.width = widths[key] + 'px'
    }
  })
}

let resizing = false
let resizeCol = ''
let resizeStartX = 0
let resizeStartW = 0
let resizeTh: HTMLTableCellElement | null = null

function onResizeStart(e: MouseEvent, key: string) {
  e.preventDefault()
  e.stopPropagation()
  resizing = true
  resizeCol = key
  resizeStartX = e.clientX

  const th = (e.target as HTMLElement).parentElement as HTMLTableCellElement
  resizeTh = th
  resizeStartW = th.offsetWidth

  document.addEventListener('mousemove', onResizeMove)
  document.addEventListener('mouseup', onResizeEnd)
  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'
}

function onResizeMove(e: MouseEvent) {
  if (!resizing || !resizeTh) return
  const diff = e.clientX - resizeStartX
  const newWidth = Math.max(50, resizeStartW + diff)
  resizeTh.style.width = newWidth + 'px'
}

function onResizeEnd() {
  if (!resizing || !resizeTh) return
  const widths = getSavedWidths()
  widths[resizeCol] = resizeTh.offsetWidth
  saveWidths(widths)

  resizing = false
  resizeTh = null
  document.removeEventListener('mousemove', onResizeMove)
  document.removeEventListener('mouseup', onResizeEnd)
  document.body.style.cursor = ''
  document.body.style.userSelect = ''
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

    <div class="bg-white rounded-xl border border-gray-200 overflow-x-auto">
      <div v-if="loading" class="p-8 text-center text-gray-400">Загрузка...</div>
      <table v-else ref="tableRef" class="w-full" style="table-layout: fixed;">
        <thead>
          <tr class="text-left text-xs text-gray-500 uppercase border-b border-gray-100">
            <th class="px-5 py-3 relative">Заказ<div class="resize-handle" @mousedown="onResizeStart($event, 'order')"></div></th>
            <th class="px-5 py-3 relative">Магазин<div class="resize-handle" @mousedown="onResizeStart($event, 'shop')"></div></th>
            <th class="px-5 py-3 relative">Получатель<div class="resize-handle" @mousedown="onResizeStart($event, 'recipient')"></div></th>
            <th class="px-5 py-3 text-center relative">SKU<div class="resize-handle" @mousedown="onResizeStart($event, 'sku')"></div></th>
            <th class="px-5 py-3 relative">Сумма<div class="resize-handle" @mousedown="onResizeStart($event, 'amount')"></div></th>
            <th class="px-5 py-3 relative">Статус<div class="resize-handle" @mousedown="onResizeStart($event, 'status')"></div></th>
            <th class="px-5 py-3 relative">Декларация<div class="resize-handle" @mousedown="onResizeStart($event, 'declaration')"></div></th>
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
            <td class="px-5 py-3 text-sm font-medium text-blue-600 truncate">{{ order.external_order_id }}</td>
            <td class="px-5 py-3 text-sm text-gray-600 truncate">{{ order.shop_name || '—' }}</td>
            <td class="px-5 py-3 text-sm text-gray-700 truncate">{{ order.recipient_name }}</td>
            <td class="px-5 py-3 text-sm text-gray-500 text-center">{{ order.items.length }}</td>
            <td class="px-5 py-3 text-sm text-gray-700 truncate">{{ kopecksToRubles(order.total_amount_kopecks) }} &#8381;</td>
            <td class="px-5 py-3"><OrderStatusBadge :status="order.status" /></td>
            <td class="px-5 py-3 truncate">
              <router-link
                v-if="order.customs_declaration_number"
                :to="`/customs/${order.customs_declaration_id}`"
                @click.stop
                class="inline-flex items-center gap-1"
              >
                <span :class="DECLARATION_STATUS_COLORS[order.customs_declaration_status || ''] || 'bg-gray-100 text-gray-600'" class="px-2 py-0.5 rounded-full text-xs font-medium">
                  {{ order.customs_declaration_number }}
                </span>
              </router-link>
              <span v-else class="text-xs text-gray-300">—</span>
            </td>
            <td class="px-5 py-3 text-sm text-gray-500 truncate">{{ formatDate(order.created_at) }}</td>
          </tr>
          <tr v-if="orders.length === 0">
            <td colspan="8" class="px-5 py-8 text-center text-sm text-gray-400">Нет заказов</td>
          </tr>
        </tbody>
      </table>
    </div>

    <Pagination :page="page" :pages="pages" :total="total" @update:page="p => page = p" />
  </div>
</template>

<style scoped>
.resize-handle {
  position: absolute;
  right: 0;
  top: 0;
  bottom: 0;
  width: 6px;
  cursor: col-resize;
  z-index: 1;
}
.resize-handle:hover {
  background-color: rgba(59, 130, 246, 0.3);
}
</style>
