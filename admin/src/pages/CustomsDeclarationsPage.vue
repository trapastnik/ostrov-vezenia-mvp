<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { fetchDeclarations } from '../api/customs'
import { fetchCompanySettings, updateCompanySettings } from '../api/company'
import Pagination from '../components/Pagination.vue'
import type { CustomsDeclaration, CompanySettings } from '../types'
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
      <!-- Filters -->
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
  </div>
</template>
