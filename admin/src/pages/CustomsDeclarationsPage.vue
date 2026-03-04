<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { fetchDeclarations, createDeclaration } from '../api/customs'
import { fetchOrders } from '../api/orders'
import { fetchCompanySettings, updateCompanySettings } from '../api/company'
import Pagination from '../components/Pagination.vue'
import OrderStatusBadge from '../components/OrderStatusBadge.vue'
import type { CustomsDeclaration, CompanySettings, Order } from '../types'
import { DECLARATION_STATUS_LABELS, DECLARATION_STATUS_COLORS } from '../types'

const router = useRouter()

// Tab
const activeTab = ref<'declarations' | 'settings'>('declarations')

// Declarations list
const declarations = ref<CustomsDeclaration[]>([])
const loading = ref(true)
const page = ref(1)
const pages = ref(1)
const total = ref(0)
const statusFilter = ref('')

async function loadDeclarations() {
  loading.value = true
  try {
    const data = await fetchDeclarations(page.value, statusFilter.value || undefined)
    declarations.value = data.items
    pages.value = data.pages
    total.value = data.total
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

// === Create declaration modal ===
const showCreateModal = ref(false)
const availableOrders = ref<Order[]>([])
const ordersLoading = ref(false)
const ordersPage = ref(1)
const ordersPages = ref(1)
const ordersTotal = ref(0)
const selectedOrderIds = ref<Set<string>>(new Set())
const creating = ref(false)
const createError = ref('')
const goodsLocation = ref('')
const operatorNote = ref('')
const ordersStatusFilter = ref('received_warehouse')

const selectedCount = computed(() => selectedOrderIds.value.size)

async function openCreateModal() {
  showCreateModal.value = true
  selectedOrderIds.value = new Set()
  createError.value = ''
  goodsLocation.value = ''
  operatorNote.value = ''
  ordersPage.value = 1
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
    const decl = await createDeclaration(
      Array.from(selectedOrderIds.value),
      goodsLocation.value || undefined,
      operatorNote.value || undefined,
    )
    showCreateModal.value = false
    router.push(`/customs/${decl.id}`)
  } catch (e: any) {
    createError.value = e.response?.data?.detail || 'Ошибка создания декларации'
  } finally {
    creating.value = false
  }
}

function kopecksToRubles(k: number): string {
  return (k / 100).toFixed(2)
}

// Company settings
const settings = ref<CompanySettings | null>(null)
const settingsLoading = ref(false)
const settingsSaving = ref(false)
const settingsMsg = ref('')

async function loadSettings() {
  settingsLoading.value = true
  try {
    settings.value = await fetchCompanySettings()
  } catch (e) {
    console.error(e)
  } finally {
    settingsLoading.value = false
  }
}

async function saveSettings() {
  if (!settings.value) return
  settingsSaving.value = true
  settingsMsg.value = ''
  try {
    const { id, ...rest } = settings.value
    settings.value = await updateCompanySettings(rest)
    settingsMsg.value = 'Сохранено'
    setTimeout(() => settingsMsg.value = '', 3000)
  } catch (e) {
    settingsMsg.value = 'Ошибка сохранения'
  } finally {
    settingsSaving.value = false
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

onMounted(() => {
  loadDeclarations()
  loadSettings()
})
</script>

<template>
  <div>
    <h2 class="text-2xl font-bold text-gray-800 mb-6">Таможня (ПТД-ЭГ)</h2>

    <!-- Tabs -->
    <div class="flex gap-1 mb-6">
      <button
        @click="activeTab = 'declarations'"
        :class="activeTab === 'declarations' ? 'bg-blue-100 text-blue-800' : 'text-gray-600 hover:bg-gray-100'"
        class="px-4 py-2 rounded-lg text-sm font-medium transition-colors cursor-pointer"
      >Декларации</button>
      <button
        @click="activeTab = 'settings'"
        :class="activeTab === 'settings' ? 'bg-blue-100 text-blue-800' : 'text-gray-600 hover:bg-gray-100'"
        class="px-4 py-2 rounded-lg text-sm font-medium transition-colors cursor-pointer"
      >Настройки компании</button>
    </div>

    <!-- Declarations tab -->
    <div v-if="activeTab === 'declarations'">
      <!-- Filters + Create button -->
      <div class="flex items-center gap-3 mb-4">
        <select
          v-model="statusFilter"
          @change="page = 1; loadDeclarations()"
          class="text-sm border border-gray-300 rounded-lg px-3 py-2"
        >
          <option value="">Все статусы</option>
          <option value="draft">Черновик</option>
          <option value="ready">Готова</option>
          <option value="submitted">Подана</option>
          <option value="accepted">Принята</option>
          <option value="rejected">Отклонена</option>
        </select>
        <button
          @click="openCreateModal"
          class="ml-auto px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 cursor-pointer"
        >
          Создать декларацию
        </button>
      </div>

      <div class="bg-white rounded-xl border border-gray-200">
        <div v-if="loading" class="p-8 text-center text-gray-400">Загрузка...</div>
        <table v-else class="w-full">
          <thead>
            <tr class="text-left text-xs text-gray-500 uppercase border-b border-gray-100">
              <th class="px-5 py-3">Номер</th>
              <th class="px-5 py-3">Статус</th>
              <th class="px-5 py-3">Заказов</th>
              <th class="px-5 py-3">Товаров</th>
              <th class="px-5 py-3">Вес</th>
              <th class="px-5 py-3">Стоимость</th>
              <th class="px-5 py-3">USD</th>
              <th class="px-5 py-3">Создана</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="d in declarations"
              :key="d.id"
              @click="router.push(`/customs/${d.id}`)"
              class="border-b border-gray-50 hover:bg-gray-50 cursor-pointer"
            >
              <td class="px-5 py-3 text-sm font-medium text-gray-800">{{ d.number }}</td>
              <td class="px-5 py-3">
                <span :class="DECLARATION_STATUS_COLORS[d.status] || 'bg-gray-100 text-gray-600'" class="px-2 py-0.5 rounded-full text-xs font-medium">
                  {{ DECLARATION_STATUS_LABELS[d.status] || d.status }}
                </span>
              </td>
              <td class="px-5 py-3 text-sm text-gray-700">{{ d.orders_count }}</td>
              <td class="px-5 py-3 text-sm text-gray-700">{{ d.items_count }}</td>
              <td class="px-5 py-3 text-sm text-gray-700">{{ (d.total_weight_grams / 1000).toFixed(1) }} кг</td>
              <td class="px-5 py-3 text-sm text-gray-700">{{ formatRub(d.total_value_kopecks) }} &#8381;</td>
              <td class="px-5 py-3 text-sm text-gray-700">{{ formatUsd(d.total_value_usd_cents) }}</td>
              <td class="px-5 py-3 text-sm text-gray-500">{{ formatDate(d.created_at) }}</td>
            </tr>
            <tr v-if="declarations.length === 0">
              <td colspan="8" class="px-5 py-8 text-center text-sm text-gray-400">Нет деклараций</td>
            </tr>
          </tbody>
        </table>
      </div>

      <Pagination :page="page" :pages="pages" :total="total" @update:page="p => { page = p; loadDeclarations() }" />
    </div>

    <!-- Settings tab -->
    <div v-if="activeTab === 'settings'" class="max-w-2xl">
      <div v-if="settingsLoading" class="p-8 text-center text-gray-400">Загрузка...</div>
      <div v-else-if="settings" class="bg-white rounded-xl border border-gray-200 p-6 space-y-4">
        <h3 class="text-lg font-semibold text-gray-800 mb-4">Данные отправителя</h3>

        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-xs text-gray-500 mb-1">Наименование компании</label>
            <input v-model="settings.company_name" class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
          </div>
          <div>
            <label class="block text-xs text-gray-500 mb-1">ИНН</label>
            <input v-model="settings.company_inn" class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" maxlength="12" />
          </div>
          <div>
            <label class="block text-xs text-gray-500 mb-1">КПП</label>
            <input v-model="settings.company_kpp" class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" maxlength="9" />
          </div>
          <div>
            <label class="block text-xs text-gray-500 mb-1">Почтовый индекс</label>
            <input v-model="settings.company_postal_code" class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" maxlength="6" />
          </div>
          <div class="col-span-2">
            <label class="block text-xs text-gray-500 mb-1">Адрес</label>
            <input v-model="settings.company_address" class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
          </div>
          <div>
            <label class="block text-xs text-gray-500 mb-1">Телефон</label>
            <input v-model="settings.company_phone" class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
          </div>
        </div>

        <h3 class="text-lg font-semibold text-gray-800 mt-6 mb-4">Таможенный представитель</h3>

        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-xs text-gray-500 mb-1">Наименование</label>
            <input v-model="settings.customs_rep_name" class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
          </div>
          <div>
            <label class="block text-xs text-gray-500 mb-1">Номер свидетельства</label>
            <input v-model="settings.customs_rep_certificate" class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
          </div>
          <div>
            <label class="block text-xs text-gray-500 mb-1">ИНН</label>
            <input v-model="settings.customs_rep_inn" class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" maxlength="12" />
          </div>
        </div>

        <h3 class="text-lg font-semibold text-gray-800 mt-6 mb-4">Параметры деклараций</h3>

        <div class="grid grid-cols-2 gap-4">
          <div class="col-span-2">
            <label class="block text-xs text-gray-500 mb-1">Место нахождения товаров (по умолчанию)</label>
            <input v-model="settings.goods_location" class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
          </div>
          <div>
            <label class="block text-xs text-gray-500 mb-1">Курс USD (копеек за 1$)</label>
            <input v-model.number="settings.usd_rate_kopecks" type="number" class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
          </div>
        </div>

        <div class="flex items-center gap-3 pt-4">
          <button
            @click="saveSettings"
            :disabled="settingsSaving"
            class="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 disabled:opacity-50 cursor-pointer"
          >
            {{ settingsSaving ? 'Сохранение...' : 'Сохранить' }}
          </button>
          <span v-if="settingsMsg" class="text-sm text-green-600">{{ settingsMsg }}</span>
        </div>
      </div>
    </div>

    <!-- Create declaration modal -->
    <div v-if="showCreateModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40" @click.self="showCreateModal = false">
      <div class="bg-white rounded-xl shadow-xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
        <!-- Header -->
        <div class="px-6 py-4 border-b border-gray-200 flex items-center gap-3">
          <h3 class="text-lg font-semibold text-gray-800">Создать декларацию</h3>
          <span class="text-sm text-gray-500">Выберите заказы для включения в ПТД-ЭГ</span>
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
              <option value="batch_forming">Формирование партии</option>
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
                  <td class="px-4 py-3 text-sm text-gray-700 text-right">{{ kopecksToRubles(order.total_amount_kopecks) }} &#8381;</td>
                  <td class="px-4 py-3 text-sm text-gray-700 text-right">{{ (order.total_weight_grams / 1000).toFixed(1) }} кг</td>
                  <td class="px-4 py-3"><OrderStatusBadge :status="order.status" /></td>
                </tr>
                <tr v-if="availableOrders.length === 0">
                  <td colspan="7" class="px-4 py-8 text-center text-sm text-gray-400">Нет заказов с этим статусом</td>
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

          <!-- Optional fields -->
          <div class="grid grid-cols-2 gap-4 mt-4">
            <div>
              <label class="block text-xs text-gray-500 mb-1">Место нахождения товаров (необязательно)</label>
              <input v-model="goodsLocation" class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" placeholder="Берётся из настроек компании" />
            </div>
            <div>
              <label class="block text-xs text-gray-500 mb-1">Примечание оператора (необязательно)</label>
              <input v-model="operatorNote" class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" placeholder="" />
            </div>
          </div>
        </div>

        <!-- Footer -->
        <div class="px-6 py-4 border-t border-gray-200 flex items-center gap-3">
          <button
            @click="handleCreate"
            :disabled="creating || selectedCount === 0"
            class="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 disabled:opacity-50 cursor-pointer"
          >
            {{ creating ? 'Создание...' : `Создать декларацию (${selectedCount} заказов)` }}
          </button>
          <button @click="showCreateModal = false" class="px-4 py-2 text-sm text-gray-600 hover:text-gray-800 cursor-pointer">
            Отмена
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
