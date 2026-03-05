<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  fetchDeclaration,
  changeDeclarationStatus,
  validateDeclaration,
  deleteDeclaration,
  updateOrderItemsCustoms,
  downloadDeclarationCsv,
  fetchDeclarationPdfUrl,
} from '../api/customs'
import CustomsItemEditor from '../components/CustomsItemEditor.vue'
import type { CustomsDeclarationDetail, CustomsDeclarationOrder } from '../types'
import { DECLARATION_STATUS_LABELS, DECLARATION_STATUS_COLORS } from '../types'

const route = useRoute()
const router = useRouter()

const declaration = ref<CustomsDeclarationDetail | null>(null)
const loading = ref(true)
const error = ref('')
const actionMsg = ref('')
const actionError = ref('')

// Tabs
const activeTab = ref<'data' | 'pdf'>('data')
const pdfUrl = ref('')
const pdfLoading = ref(false)

// Item editor
const editingOrder = ref<CustomsDeclarationOrder | null>(null)

// Validation
const validationResult = ref<{ valid: boolean; errors: string[] } | null>(null)
const validating = ref(false)

// Status transitions
const ALLOWED_TRANSITIONS: Record<string, string[]> = {
  draft: ['ready'],
  ready: ['submitted', 'draft'],
  submitted: ['accepted', 'rejected'],
  rejected: ['draft'],
}

const availableTransitions = computed(() => {
  if (!declaration.value) return []
  return ALLOWED_TRANSITIONS[declaration.value.status] || []
})

async function load() {
  loading.value = true
  error.value = ''
  try {
    declaration.value = await fetchDeclaration(route.params.id as string)
  } catch (e: any) {
    error.value = e.response?.data?.detail || 'Ошибка загрузки'
  } finally {
    loading.value = false
  }
}

async function handleStatusChange(newStatus: string) {
  actionMsg.value = ''
  actionError.value = ''
  try {
    await changeDeclarationStatus(route.params.id as string, newStatus)
    await load()
    actionMsg.value = `Статус изменён на «${DECLARATION_STATUS_LABELS[newStatus] || newStatus}»`
    setTimeout(() => actionMsg.value = '', 3000)
  } catch (e: any) {
    actionError.value = e.response?.data?.detail || 'Ошибка смены статуса'
  }
}

async function handleValidate() {
  validating.value = true
  validationResult.value = null
  try {
    validationResult.value = await validateDeclaration(route.params.id as string)
  } catch (e: any) {
    actionError.value = e.response?.data?.detail || 'Ошибка валидации'
  } finally {
    validating.value = false
  }
}

async function handleDelete() {
  if (!confirm('Удалить декларацию? Это действие нельзя отменить.')) return
  try {
    await deleteDeclaration(route.params.id as string)
    router.push('/customs')
  } catch (e: any) {
    actionError.value = e.response?.data?.detail || 'Ошибка удаления'
  }
}

async function handleExportCsv() {
  try {
    await downloadDeclarationCsv(route.params.id as string)
  } catch {
    actionError.value = 'Ошибка скачивания CSV'
  }
}

async function switchToPdf() {
  activeTab.value = 'pdf'
  if (pdfUrl.value) return // already loaded
  pdfLoading.value = true
  actionError.value = ''
  try {
    pdfUrl.value = await fetchDeclarationPdfUrl(route.params.id as string)
  } catch {
    actionError.value = 'Ошибка загрузки PDF'
    activeTab.value = 'data'
  } finally {
    pdfLoading.value = false
  }
}

function refreshPdf() {
  if (pdfUrl.value) {
    window.URL.revokeObjectURL(pdfUrl.value)
    pdfUrl.value = ''
  }
  switchToPdf()
}

function openEditor(order: CustomsDeclarationOrder) {
  editingOrder.value = order
}

async function handleSaveItems(orderId: string, updates: { item_index: number; tn_ved_code: string; country_of_origin: string; brand?: string }[]) {
  try {
    await updateOrderItemsCustoms(orderId, updates)
    editingOrder.value = null
    await load()
    // Invalidate PDF cache after data change
    if (pdfUrl.value) {
      window.URL.revokeObjectURL(pdfUrl.value)
      pdfUrl.value = ''
    }
    actionMsg.value = 'Таможенные данные сохранены'
    setTimeout(() => actionMsg.value = '', 3000)
  } catch (e: any) {
    actionError.value = e.response?.data?.detail || 'Ошибка сохранения'
  }
}

function formatDate(d: string | null): string {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('ru-RU', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

function formatRub(kopecks: number): string {
  return (kopecks / 100).toLocaleString('ru-RU', { minimumFractionDigits: 2 })
}

function formatUsd(cents: number): string {
  return (cents / 100).toLocaleString('en-US', { minimumFractionDigits: 2, style: 'currency', currency: 'USD' })
}

function isCustomsReady(order: CustomsDeclarationOrder): boolean {
  return order.items.every(item => item.tn_ved_code && item.country_of_origin)
}

onMounted(load)

onUnmounted(() => {
  if (pdfUrl.value) {
    window.URL.revokeObjectURL(pdfUrl.value)
  }
})
</script>

<template>
  <div>
    <router-link to="/customs" class="text-sm text-blue-600 hover:underline mb-4 inline-block">&larr; К списку деклараций</router-link>

    <div v-if="loading" class="text-gray-500">Загрузка...</div>
    <div v-else-if="error" class="text-red-600">{{ error }}</div>

    <template v-else-if="declaration">
      <!-- Header -->
      <div class="flex items-center gap-4 mb-6">
        <h2 class="text-2xl font-bold text-gray-800">{{ declaration.number }}</h2>
        <span
          :class="DECLARATION_STATUS_COLORS[declaration.status] || 'bg-gray-100 text-gray-600'"
          class="px-3 py-1 rounded-full text-sm font-medium"
        >
          {{ DECLARATION_STATUS_LABELS[declaration.status] || declaration.status }}
        </span>
      </div>

      <!-- Messages -->
      <div v-if="actionMsg" class="mb-4 px-4 py-2 bg-green-50 text-green-700 rounded-lg text-sm">{{ actionMsg }}</div>
      <div v-if="actionError" class="mb-4 px-4 py-2 bg-red-50 text-red-700 rounded-lg text-sm">{{ actionError }}</div>

      <!-- Actions -->
      <div class="flex flex-wrap gap-2 mb-6">
        <button
          v-for="status in availableTransitions"
          :key="status"
          @click="handleStatusChange(status)"
          class="px-3 py-1.5 text-sm rounded-lg border cursor-pointer"
          :class="status === 'draft' || status === 'rejected'
            ? 'border-gray-300 text-gray-700 hover:bg-gray-50'
            : 'border-blue-300 text-blue-700 hover:bg-blue-50'"
        >
          {{ DECLARATION_STATUS_LABELS[status] || status }}
        </button>

        <button
          @click="handleValidate"
          :disabled="validating"
          class="px-3 py-1.5 text-sm rounded-lg border border-purple-300 text-purple-700 hover:bg-purple-50 disabled:opacity-50 cursor-pointer"
        >
          {{ validating ? 'Проверка...' : 'Проверить готовность' }}
        </button>

        <button
          @click="handleExportCsv"
          class="px-3 py-1.5 text-sm rounded-lg border border-green-300 text-green-700 hover:bg-green-50 cursor-pointer"
        >
          CSV
        </button>

        <button
          v-if="declaration.status === 'draft'"
          @click="handleDelete"
          class="ml-auto px-3 py-1.5 text-sm rounded-lg border border-red-300 text-red-600 hover:bg-red-50 cursor-pointer"
        >
          Удалить
        </button>
      </div>

      <!-- Validation result -->
      <div v-if="validationResult" class="mb-6 p-4 rounded-xl border" :class="validationResult.valid ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'">
        <p class="font-medium text-sm" :class="validationResult.valid ? 'text-green-800' : 'text-red-800'">
          {{ validationResult.valid ? 'Декларация готова к подаче' : 'Есть ошибки' }}
        </p>
        <ul v-if="validationResult.errors.length" class="mt-2 space-y-1">
          <li v-for="(err, i) in validationResult.errors" :key="i" class="text-sm text-red-700">- {{ err }}</li>
        </ul>
      </div>

      <!-- Tabs -->
      <div class="flex border-b border-gray-200 mb-6">
        <button
          @click="activeTab = 'data'"
          class="px-4 py-2.5 text-sm font-medium border-b-2 cursor-pointer transition-colors"
          :class="activeTab === 'data' ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'"
        >
          Данные
        </button>
        <button
          @click="switchToPdf()"
          class="px-4 py-2.5 text-sm font-medium border-b-2 cursor-pointer transition-colors"
          :class="activeTab === 'pdf' ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'"
        >
          PDF
        </button>
      </div>

      <!-- Tab: Data -->
      <div v-if="activeTab === 'data'">
        <!-- Summary -->
        <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <div class="bg-white rounded-xl border border-gray-200 p-4">
            <div class="text-xs text-gray-500">Заказов</div>
            <div class="text-xl font-bold text-gray-800">{{ declaration.orders_count }}</div>
          </div>
          <div class="bg-white rounded-xl border border-gray-200 p-4">
            <div class="text-xs text-gray-500">Товаров</div>
            <div class="text-xl font-bold text-gray-800">{{ declaration.items_count }}</div>
          </div>
          <div class="bg-white rounded-xl border border-gray-200 p-4">
            <div class="text-xs text-gray-500">Вес</div>
            <div class="text-xl font-bold text-gray-800">{{ (declaration.total_weight_grams / 1000).toFixed(1) }} <span class="text-sm font-normal text-gray-500">кг</span></div>
          </div>
          <div class="bg-white rounded-xl border border-gray-200 p-4">
            <div class="text-xs text-gray-500">Стоимость</div>
            <div class="text-lg font-bold text-gray-800">{{ formatRub(declaration.total_value_kopecks) }} <span class="text-sm font-normal text-gray-500">&#8381;</span></div>
            <div class="text-sm text-gray-500">{{ formatUsd(declaration.total_value_usd_cents) }}</div>
          </div>
        </div>

        <!-- Sender & customs rep info -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">
          <div class="bg-white rounded-xl border border-gray-200 p-5">
            <h3 class="font-semibold text-gray-800 mb-3">Отправитель</h3>
            <dl class="space-y-2 text-sm">
              <div class="flex"><dt class="w-20 text-gray-500 shrink-0">Название</dt><dd class="text-gray-800">{{ declaration.sender_name || '—' }}</dd></div>
              <div class="flex"><dt class="w-20 text-gray-500 shrink-0">ИНН</dt><dd class="text-gray-800 font-mono">{{ declaration.sender_inn || '—' }}</dd></div>
              <div class="flex"><dt class="w-20 text-gray-500 shrink-0">Адрес</dt><dd class="text-gray-800">{{ declaration.sender_address || '—' }}</dd></div>
            </dl>
          </div>
          <div class="bg-white rounded-xl border border-gray-200 p-5">
            <h3 class="font-semibold text-gray-800 mb-3">Таможенный представитель</h3>
            <dl class="space-y-2 text-sm">
              <div class="flex"><dt class="w-32 text-gray-500 shrink-0">Наименование</dt><dd class="text-gray-800">{{ declaration.customs_rep_name || '—' }}</dd></div>
              <div class="flex"><dt class="w-32 text-gray-500 shrink-0">Свидетельство</dt><dd class="text-gray-800 font-mono">{{ declaration.customs_rep_certificate || '—' }}</dd></div>
            </dl>
            <div v-if="declaration.goods_location" class="mt-3 pt-3 border-t border-gray-100">
              <div class="text-xs text-gray-500 mb-1">Место нахождения товаров</div>
              <div class="text-sm text-gray-800">{{ declaration.goods_location }}</div>
            </div>
            <div v-if="declaration.operator_note" class="mt-3 pt-3 border-t border-gray-100">
              <div class="text-xs text-gray-500 mb-1">Примечание оператора</div>
              <div class="text-sm text-gray-800">{{ declaration.operator_note }}</div>
            </div>
          </div>
        </div>

        <!-- FTS reference -->
        <div v-if="declaration.fts_reference" class="mb-6 bg-white rounded-xl border border-gray-200 p-4">
          <span class="text-xs text-gray-500">Рег. номер ФТС:</span>
          <span class="ml-2 font-mono text-sm text-gray-800">{{ declaration.fts_reference }}</span>
        </div>

        <!-- Orders -->
        <h3 class="text-lg font-semibold text-gray-800 mb-4">Заказы в декларации ({{ declaration.orders.length }})</h3>

        <div class="space-y-4">
          <div
            v-for="(order, orderIdx) in declaration.orders"
            :key="order.id"
            class="bg-white rounded-xl border border-gray-200 p-5"
          >
            <div class="flex items-center gap-3 mb-3">
              <span class="text-sm font-bold text-gray-800">#{{ orderIdx + 1 }}</span>
              <span class="text-sm text-gray-600">{{ order.external_order_id }}</span>
              <span
                class="px-2 py-0.5 rounded-full text-xs font-medium"
                :class="isCustomsReady(order) ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'"
              >
                {{ isCustomsReady(order) ? 'Данные заполнены' : 'Требуется заполнение' }}
              </span>
              <button
                v-if="declaration.status === 'draft'"
                @click="openEditor(order)"
                class="ml-auto text-sm text-blue-600 hover:text-blue-800 cursor-pointer"
              >
                Редактировать
              </button>
            </div>

            <!-- Recipient -->
            <div class="text-sm text-gray-600 mb-3">
              {{ order.recipient_name }} | {{ order.recipient_address }}, {{ order.recipient_postal_code }}
            </div>

            <!-- Items table -->
            <table class="w-full text-sm">
              <thead>
                <tr class="text-left text-xs text-gray-500 uppercase border-b border-gray-100">
                  <th class="pb-2 font-medium">Товар</th>
                  <th class="pb-2 font-medium">Код ТН ВЭД</th>
                  <th class="pb-2 font-medium">Страна</th>
                  <th class="pb-2 font-medium">Бренд</th>
                  <th class="pb-2 font-medium text-center">Кол-во</th>
                  <th class="pb-2 font-medium text-right">Вес</th>
                  <th class="pb-2 font-medium text-right">Стоимость</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(item, i) in order.items" :key="i" class="border-b border-gray-50">
                  <td class="py-2 text-gray-800">{{ item.name }}</td>
                  <td class="py-2 font-mono text-xs" :class="item.tn_ved_code ? 'text-gray-800' : 'text-red-400'">
                    {{ item.tn_ved_code || 'не указан' }}
                  </td>
                  <td class="py-2 font-mono text-xs" :class="item.country_of_origin ? 'text-gray-800' : 'text-red-400'">
                    {{ item.country_of_origin || 'не указана' }}
                  </td>
                  <td class="py-2 text-gray-600 text-xs">{{ item.brand || '—' }}</td>
                  <td class="py-2 text-gray-600 text-center">{{ item.quantity }}</td>
                  <td class="py-2 text-gray-600 text-right">{{ (item.weight_grams * item.quantity / 1000).toFixed(2) }} кг</td>
                  <td class="py-2 text-gray-800 text-right">{{ formatRub(item.price_kopecks * item.quantity) }} &#8381;</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div v-if="declaration.orders.length === 0" class="text-center text-gray-400 py-8">
            Нет заказов в декларации
          </div>
        </div>

        <!-- Dates -->
        <div class="mt-6 text-xs text-gray-400 space-y-1">
          <div>Создана: {{ formatDate(declaration.created_at) }}</div>
          <div v-if="declaration.submitted_at">Подана: {{ formatDate(declaration.submitted_at) }}</div>
          <div v-if="declaration.accepted_at">Принята: {{ formatDate(declaration.accepted_at) }}</div>
          <div>Обновлена: {{ formatDate(declaration.updated_at) }}</div>
        </div>
      </div>

      <!-- Tab: PDF -->
      <div v-if="activeTab === 'pdf'">
        <div v-if="pdfLoading" class="flex items-center justify-center py-20 text-gray-400">
          <svg class="animate-spin h-5 w-5 mr-2" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none" /><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>
          Загрузка PDF...
        </div>
        <div v-else-if="pdfUrl" class="space-y-3">
          <div class="flex items-center gap-2">
            <button
              @click="refreshPdf"
              class="px-3 py-1.5 text-sm rounded-lg border border-gray-300 text-gray-600 hover:bg-gray-50 cursor-pointer"
            >
              Обновить
            </button>
            <a
              :href="pdfUrl"
              :download="`dteg-${declaration.number}.pdf`"
              class="px-3 py-1.5 text-sm rounded-lg border border-gray-300 text-gray-600 hover:bg-gray-50"
            >
              Скачать
            </a>
          </div>
          <iframe
            :src="pdfUrl"
            class="w-full border border-gray-200 rounded-xl"
            style="height: calc(100vh - 300px); min-height: 600px;"
          />
        </div>
      </div>
    </template>

    <!-- Item editor modal -->
    <CustomsItemEditor
      v-if="editingOrder"
      :order="editingOrder"
      @save="handleSaveItems"
      @close="editingOrder = null"
    />
  </div>
</template>
