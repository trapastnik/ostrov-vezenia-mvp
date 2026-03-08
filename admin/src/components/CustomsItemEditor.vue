<script setup lang="ts">
import { ref } from 'vue'
import type { CustomsDeclarationOrder, TnVedSearchResult } from '../types'
import { searchTnVed } from '../api/tnved'
import TnVedBrowser from './TnVedBrowser.vue'

const props = defineProps<{
  order: CustomsDeclarationOrder
}>()

const emit = defineEmits<{
  save: [orderId: string, updates: { item_index: number; tn_ved_code: string; country_of_origin: string; brand?: string }[]]
  close: []
}>()

const saving = ref(false)

// Create editable copies of items
const editItems = ref(
  props.order.items.map((item, i) => ({
    index: i,
    name: item.name,
    tn_ved_code: item.tn_ved_code || '',
    country_of_origin: item.country_of_origin || '',
    brand: item.brand || '',
  }))
)

// TN VED autocomplete state (per item)
const tnVedQuery = ref<Record<number, string>>({})
const tnVedResults = ref<Record<number, TnVedSearchResult[]>>({})
const tnVedLoading = ref<Record<number, boolean>>({})
const showDropdown = ref<Record<number, boolean>>({})
let debounceTimers: Record<number, ReturnType<typeof setTimeout>> = {}

function onTnVedInput(itemIndex: number, value: string) {
  const item = editItems.value[itemIndex]
  if (!item) return
  item.tn_ved_code = value
  tnVedQuery.value[itemIndex] = value

  if (debounceTimers[itemIndex]) clearTimeout(debounceTimers[itemIndex])

  if (value.length < 2) {
    tnVedResults.value[itemIndex] = []
    showDropdown.value[itemIndex] = false
    return
  }

  debounceTimers[itemIndex] = setTimeout(async () => {
    tnVedLoading.value[itemIndex] = true
    try {
      const resp = await searchTnVed(value, 10)
      tnVedResults.value[itemIndex] = resp.items
      showDropdown.value[itemIndex] = resp.items.length > 0
    } catch {
      tnVedResults.value[itemIndex] = []
      showDropdown.value[itemIndex] = false
    } finally {
      tnVedLoading.value[itemIndex] = false
    }
  }, 300)
}

function selectTnVed(itemIndex: number, result: TnVedSearchResult) {
  const item = editItems.value[itemIndex]
  if (!item) return
  // Используем первые 6 знаков (подпозиция) или полный код
  const code = result.code.replace(/0+$/, '') // убираем хвостовые нули
  const finalCode = code.length < 6 ? result.code.substring(0, 6) : code
  item.tn_ved_code = finalCode
  showDropdown.value[itemIndex] = false
}

function hideDropdown(itemIndex: number) {
  // Delay to allow click on dropdown item
  setTimeout(() => {
    showDropdown.value[itemIndex] = false
  }, 200)
}

function handleSave() {
  saving.value = true
  const updates = editItems.value.map(item => ({
    item_index: item.index,
    tn_ved_code: item.tn_ved_code.trim(),
    country_of_origin: item.country_of_origin.trim().toUpperCase(),
    brand: item.brand.trim() || undefined,
  }))
  emit('save', props.order.id, updates)
}

// TN VED browser modal
const showBrowser = ref(false)
const browserItemIndex = ref<number | null>(null)

function openBrowser(itemIndex: number) {
  browserItemIndex.value = itemIndex
  showBrowser.value = true
}

function onBrowserSelect(code: string, _name: string, _unit: string | null) {
  if (browserItemIndex.value !== null) {
    const item = editItems.value[browserItemIndex.value]
    if (item) {
      item.tn_ved_code = code
    }
  }
  showBrowser.value = false
  browserItemIndex.value = null
}

// Common country codes for quick select
const commonCountries = [
  { code: 'CN', label: 'Китай' },
  { code: 'RU', label: 'Россия' },
  { code: 'TR', label: 'Турция' },
  { code: 'DE', label: 'Германия' },
  { code: 'IT', label: 'Италия' },
  { code: 'FR', label: 'Франция' },
  { code: 'US', label: 'США' },
  { code: 'KR', label: 'Ю.Корея' },
  { code: 'JP', label: 'Япония' },
  { code: 'BY', label: 'Беларусь' },
]

function applyToAll(field: 'tn_ved_code' | 'country_of_origin' | 'brand', value: string) {
  editItems.value.forEach(item => {
    item[field] = value
  })
}
</script>

<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40" @click.self="emit('close')">
    <div class="bg-white rounded-xl shadow-xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
      <!-- Header -->
      <div class="px-6 py-4 border-b border-gray-200 flex items-center gap-3">
        <h3 class="text-lg font-semibold text-gray-800">Таможенные данные товаров</h3>
        <span class="text-sm text-gray-500">Заказ {{ order.external_order_id }}</span>
        <button @click="emit('close')" class="ml-auto text-gray-400 hover:text-gray-600 cursor-pointer text-xl">&times;</button>
      </div>

      <!-- Body -->
      <div class="flex-1 overflow-auto p-6">
        <!-- Quick actions -->
        <div class="mb-4 flex items-center gap-2 text-xs text-gray-500">
          <span>Применить страну ко всем:</span>
          <button
            v-for="c in commonCountries"
            :key="c.code"
            @click="applyToAll('country_of_origin', c.code)"
            class="px-2 py-0.5 border border-gray-200 rounded hover:bg-gray-50 cursor-pointer"
          >
            {{ c.code }} ({{ c.label }})
          </button>
        </div>

        <!-- Items -->
        <div class="space-y-3">
          <div
            v-for="item in editItems"
            :key="item.index"
            class="border border-gray-200 rounded-lg p-4"
          >
            <div class="text-sm font-medium text-gray-800 mb-3">{{ item.name }}</div>
            <div class="grid grid-cols-3 gap-3">
              <!-- TN VED code with autocomplete -->
              <div class="relative">
                <label class="block text-xs text-gray-500 mb-1">Код ТН ВЭД (мин. 6 цифр)</label>
                <div class="flex gap-1">
                  <input
                    :value="item.tn_ved_code"
                    @input="onTnVedInput(item.index, ($event.target as HTMLInputElement).value)"
                    @focus="item.tn_ved_code.length >= 2 && onTnVedInput(item.index, item.tn_ved_code)"
                    @blur="hideDropdown(item.index)"
                    class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm font-mono"
                    placeholder="640399"
                    maxlength="10"
                  />
                  <button
                    @click="openBrowser(item.index)"
                    class="px-2 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 cursor-pointer text-gray-500 hover:text-blue-600 transition-colors flex-shrink-0"
                    title="Каталог ТН ВЭД"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                    </svg>
                  </button>
                </div>
                <!-- Loading indicator -->
                <div v-if="tnVedLoading[item.index]" class="absolute right-3 top-8">
                  <div class="w-4 h-4 border-2 border-blue-400 border-t-transparent rounded-full animate-spin"></div>
                </div>
                <!-- Dropdown -->
                <div
                  v-if="showDropdown[item.index] && tnVedResults[item.index]?.length"
                  class="absolute z-10 top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-48 overflow-auto"
                >
                  <div
                    v-for="result in tnVedResults[item.index]"
                    :key="result.code"
                    @mousedown.prevent="selectTnVed(item.index, result)"
                    class="px-3 py-2 hover:bg-blue-50 cursor-pointer border-b border-gray-100 last:border-0"
                  >
                    <div class="flex items-center gap-2">
                      <span class="font-mono text-xs text-blue-600 whitespace-nowrap">{{ result.code.replace(/0+$/, '') || result.code }}</span>
                      <span class="text-xs text-gray-600 truncate">{{ result.name }}</span>
                    </div>
                    <div v-if="result.unit" class="text-[10px] text-gray-400 mt-0.5">{{ result.unit }}</div>
                  </div>
                </div>
              </div>
              <div>
                <label class="block text-xs text-gray-500 mb-1">Страна происхождения (ISO)</label>
                <div class="flex gap-1">
                  <input
                    v-model="item.country_of_origin"
                    class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm font-mono uppercase"
                    placeholder="CN"
                    maxlength="2"
                  />
                </div>
              </div>
              <div>
                <label class="block text-xs text-gray-500 mb-1">Бренд (если есть)</label>
                <input
                  v-model="item.brand"
                  class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
                  placeholder="Nike"
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div class="px-6 py-4 border-t border-gray-200 flex items-center gap-3">
        <button
          @click="handleSave"
          :disabled="saving"
          class="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 disabled:opacity-50 cursor-pointer"
        >
          {{ saving ? 'Сохранение...' : 'Сохранить' }}
        </button>
        <button @click="emit('close')" class="px-4 py-2 text-sm text-gray-600 hover:text-gray-800 cursor-pointer">
          Отмена
        </button>
      </div>
    </div>
  </div>

  <!-- TN VED Browser Modal -->
  <TnVedBrowser
    v-if="showBrowser"
    @select="onBrowserSelect"
    @close="showBrowser = false"
  />
</template>
