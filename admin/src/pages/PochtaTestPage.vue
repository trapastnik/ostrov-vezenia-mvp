<script setup lang="ts">
import { ref } from 'vue'
import {
  compareTariffs,
  normalizeAddress,
  normalizeFio,
  normalizePhone,
  getBalance,
} from '../api/pochta'
import type { TariffCompareResult, AddressResult, FioResult, PhoneResult } from '../api/pochta'

// --- Tabs ---
const activeTab = ref<'tariff' | 'address' | 'fio' | 'phone' | 'balance'>('tariff')

// --- Tariff Compare ---
const tariffFrom = ref('238311')
const tariffTo = ref('101000')
const tariffWeight = ref(1000)
const tariffLoading = ref(false)
const tariffResult = ref<TariffCompareResult | null>(null)
const tariffError = ref('')

async function calcTariff() {
  tariffLoading.value = true
  tariffResult.value = null
  tariffError.value = ''
  try {
    tariffResult.value = await compareTariffs({
      index_from: tariffFrom.value,
      index_to: tariffTo.value,
      weight_grams: tariffWeight.value,
    })
  } catch (e: unknown) {
    const err = e as { response?: { data?: { detail?: string } } }
    tariffError.value = err.response?.data?.detail || 'Ошибка запроса'
  } finally {
    tariffLoading.value = false
  }
}

// --- Address ---
const addressInput = ref('Москва, ул. Ленина, д. 1, кв. 5')
const addressLoading = ref(false)
const addressResult = ref<AddressResult | null>(null)
const addressError = ref('')

async function checkAddress() {
  addressLoading.value = true
  addressResult.value = null
  addressError.value = ''
  try {
    addressResult.value = await normalizeAddress(addressInput.value)
  } catch (e: unknown) {
    const err = e as { response?: { data?: { detail?: string } } }
    addressError.value = err.response?.data?.detail || 'Ошибка запроса'
  } finally {
    addressLoading.value = false
  }
}

// --- FIO ---
const fioInput = ref('Иванов Пётр Сергеевич')
const fioLoading = ref(false)
const fioResult = ref<FioResult | null>(null)
const fioError = ref('')

async function checkFio() {
  fioLoading.value = true
  fioResult.value = null
  fioError.value = ''
  try {
    fioResult.value = await normalizeFio(fioInput.value)
  } catch (e: unknown) {
    const err = e as { response?: { data?: { detail?: string } } }
    fioError.value = err.response?.data?.detail || 'Ошибка запроса'
  } finally {
    fioLoading.value = false
  }
}

// --- Phone ---
const phoneInput = ref('+79261234567')
const phoneLoading = ref(false)
const phoneResult = ref<PhoneResult | null>(null)
const phoneError = ref('')

async function checkPhone() {
  phoneLoading.value = true
  phoneResult.value = null
  phoneError.value = ''
  try {
    phoneResult.value = await normalizePhone(phoneInput.value)
  } catch (e: unknown) {
    const err = e as { response?: { data?: { detail?: string } } }
    phoneError.value = err.response?.data?.detail || 'Ошибка запроса'
  } finally {
    phoneLoading.value = false
  }
}

// --- Balance ---
const balanceLoading = ref(false)
const balanceResult = ref<number | null>(null)
const balanceError = ref('')
const balanceUnavailable = ref('')

async function checkBalance() {
  balanceLoading.value = true
  balanceResult.value = null
  balanceError.value = ''
  balanceUnavailable.value = ''
  try {
    const data = await getBalance()
    if (!data.available) {
      balanceUnavailable.value = data.message || 'Баланс недоступен для этого аккаунта'
    } else {
      balanceResult.value = data.balance_kopecks
    }
  } catch (e: unknown) {
    const err = e as { response?: { data?: { detail?: string } } }
    balanceError.value = err.response?.data?.detail || 'Ошибка запроса'
  } finally {
    balanceLoading.value = false
  }
}

function kopecks(v: number): string {
  return (v / 100).toFixed(2) + ' руб.'
}
</script>

<template>
  <div>
    <h2 class="text-2xl font-bold text-gray-800 mb-6">Тест API Почты России</h2>

    <!-- Tabs -->
    <div class="flex gap-1 mb-6 border-b border-gray-200">
      <button
        v-for="tab in [
          { key: 'tariff', label: 'Тариф' },
          { key: 'address', label: 'Адрес' },
          { key: 'fio', label: 'ФИО' },
          { key: 'phone', label: 'Телефон' },
          { key: 'balance', label: 'Баланс' },
        ]"
        :key="tab.key"
        @click="activeTab = tab.key as typeof activeTab"
        class="px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors cursor-pointer"
        :class="activeTab === tab.key
          ? 'border-blue-600 text-blue-600'
          : 'border-transparent text-gray-500 hover:text-gray-700'"
      >
        {{ tab.label }}
      </button>
    </div>

    <!-- Tab: Tariff Compare -->
    <div v-if="activeTab === 'tariff'" class="max-w-3xl">
      <div class="bg-white rounded-lg border border-gray-200 p-6">
        <h3 class="text-lg font-semibold mb-4">Сравнение тарифов</h3>
        <div class="grid grid-cols-3 gap-4 mb-5">
          <div>
            <label class="block text-sm font-medium text-gray-600 mb-1">Индекс отправителя</label>
            <input v-model="tariffFrom" class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-600 mb-1">Индекс получателя</label>
            <input v-model="tariffTo" class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-600 mb-1">Вес (грамм)</label>
            <input v-model.number="tariffWeight" type="number" class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
          </div>
        </div>
        <button
          @click="calcTariff"
          :disabled="tariffLoading"
          class="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 cursor-pointer"
        >
          {{ tariffLoading ? 'Расчёт...' : 'Сравнить тарифы' }}
        </button>

        <div v-if="tariffError" class="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
          {{ tariffError }}
        </div>

        <div v-if="tariffResult" class="mt-5">
          <!-- Сетка сравнения -->
          <div class="grid grid-cols-2 gap-4 mb-4">
            <!-- Публичный тариф -->
            <div class="bg-gray-50 rounded-lg p-4 border border-gray-200">
              <div class="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-3">Публичный тариф</div>
              <div class="space-y-2 text-sm">
                <div class="flex justify-between">
                  <span class="text-gray-500">Стоимость</span>
                  <span class="font-medium">{{ kopecks(tariffResult.public_cost_kopecks) }}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-gray-500">НДС</span>
                  <span class="font-medium">{{ kopecks(tariffResult.public_vat_kopecks) }}</span>
                </div>
                <div class="flex justify-between border-t border-gray-200 pt-2 mt-2">
                  <span class="text-gray-600 font-medium">Итого</span>
                  <span class="font-bold text-gray-800">{{ kopecks(tariffResult.public_total_kopecks) }}</span>
                </div>
              </div>
            </div>

            <!-- Контрактный тариф -->
            <div
              class="rounded-lg p-4 border"
              :class="tariffResult.contract_available
                ? 'bg-green-50 border-green-200'
                : 'bg-red-50 border-red-200'"
            >
              <div class="text-xs font-semibold uppercase tracking-wide mb-3"
                :class="tariffResult.contract_available ? 'text-green-500' : 'text-red-400'">
                Наш (контрактный) тариф
              </div>
              <div v-if="tariffResult.contract_available" class="space-y-2 text-sm">
                <div class="flex justify-between">
                  <span class="text-gray-500">Стоимость</span>
                  <span class="font-medium">{{ kopecks(tariffResult.contract_cost_kopecks) }}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-gray-500">НДС</span>
                  <span class="font-medium">{{ kopecks(tariffResult.contract_vat_kopecks) }}</span>
                </div>
                <div class="flex justify-between border-t border-green-200 pt-2 mt-2">
                  <span class="text-gray-600 font-medium">Итого</span>
                  <span class="font-bold text-green-700">{{ kopecks(tariffResult.contract_total_kopecks) }}</span>
                </div>
              </div>
              <div v-else class="text-sm text-red-600">
                Недоступен: {{ tariffResult.contract_error }}
              </div>
            </div>
          </div>

          <!-- Итог: экономия + срок -->
          <div class="flex gap-4">
            <div v-if="tariffResult.contract_available && tariffResult.savings_kopecks > 0"
              class="flex-1 bg-emerald-50 border border-emerald-200 rounded-lg p-4 text-center">
              <div class="text-xs text-emerald-500 font-semibold uppercase tracking-wide mb-1">Экономия</div>
              <div class="text-2xl font-bold text-emerald-700">{{ kopecks(tariffResult.savings_kopecks) }}</div>
              <div class="text-sm text-emerald-600 mt-1">{{ tariffResult.savings_percent }}% дешевле публичного</div>
            </div>
            <div v-else-if="tariffResult.contract_available"
              class="flex-1 bg-yellow-50 border border-yellow-200 rounded-lg p-4 text-center">
              <div class="text-sm text-yellow-700">Контрактный тариф не даёт экономии на этом направлении</div>
            </div>
            <div class="flex-1 bg-blue-50 border border-blue-100 rounded-lg p-4 text-center">
              <div class="text-xs text-blue-400 font-semibold uppercase tracking-wide mb-1">Срок доставки</div>
              <div class="text-2xl font-bold text-blue-700">{{ tariffResult.min_days }}–{{ tariffResult.max_days }}</div>
              <div class="text-sm text-blue-500 mt-1">дней</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Tab: Address -->
    <div v-if="activeTab === 'address'" class="max-w-2xl">
      <div class="bg-white rounded-lg border border-gray-200 p-6">
        <h3 class="text-lg font-semibold mb-4">Нормализация адреса</h3>
        <div class="mb-4">
          <label class="block text-sm font-medium text-gray-600 mb-1">Адрес</label>
          <input v-model="addressInput" class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" placeholder="Москва, ул. Ленина, д. 1" />
        </div>
        <button
          @click="checkAddress"
          :disabled="addressLoading"
          class="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 cursor-pointer"
        >
          {{ addressLoading ? 'Проверка...' : 'Проверить' }}
        </button>

        <div v-if="addressError" class="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
          {{ addressError }}
        </div>

        <div v-if="addressResult" class="mt-4 bg-gray-50 rounded-lg p-4">
          <div class="mb-3">
            <span
              class="inline-block px-2 py-1 rounded text-xs font-medium"
              :class="addressResult.is_valid ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'"
            >
              {{ addressResult.is_valid ? 'Валидный' : 'Невалидный' }}
            </span>
          </div>
          <div class="grid grid-cols-2 gap-3 text-sm">
            <div><span class="text-gray-500">Индекс:</span> <span class="font-medium">{{ addressResult.index }}</span></div>
            <div><span class="text-gray-500">Регион:</span> <span class="font-medium">{{ addressResult.region }}</span></div>
            <div><span class="text-gray-500">Город:</span> <span class="font-medium">{{ addressResult.place }}</span></div>
            <div><span class="text-gray-500">Улица:</span> <span class="font-medium">{{ addressResult.street }}</span></div>
            <div><span class="text-gray-500">Дом:</span> <span class="font-medium">{{ addressResult.house }}</span></div>
            <div><span class="text-gray-500">Квартира:</span> <span class="font-medium">{{ addressResult.room }}</span></div>
            <div><span class="text-gray-500">Код качества:</span> <span class="font-mono text-xs">{{ addressResult.quality_code }}</span></div>
            <div><span class="text-gray-500">Код валидации:</span> <span class="font-mono text-xs">{{ addressResult.validation_code }}</span></div>
          </div>
        </div>
      </div>
    </div>

    <!-- Tab: FIO -->
    <div v-if="activeTab === 'fio'" class="max-w-2xl">
      <div class="bg-white rounded-lg border border-gray-200 p-6">
        <h3 class="text-lg font-semibold mb-4">Нормализация ФИО</h3>
        <div class="mb-4">
          <label class="block text-sm font-medium text-gray-600 mb-1">ФИО</label>
          <input v-model="fioInput" class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" placeholder="Иванов Пётр Сергеевич" />
        </div>
        <button
          @click="checkFio"
          :disabled="fioLoading"
          class="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 cursor-pointer"
        >
          {{ fioLoading ? 'Проверка...' : 'Проверить' }}
        </button>

        <div v-if="fioError" class="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
          {{ fioError }}
        </div>

        <div v-if="fioResult" class="mt-4 bg-gray-50 rounded-lg p-4">
          <div class="grid grid-cols-2 gap-3 text-sm">
            <div><span class="text-gray-500">Фамилия:</span> <span class="font-medium">{{ fioResult.surname }}</span></div>
            <div><span class="text-gray-500">Имя:</span> <span class="font-medium">{{ fioResult.name }}</span></div>
            <div><span class="text-gray-500">Отчество:</span> <span class="font-medium">{{ fioResult.middle_name }}</span></div>
            <div><span class="text-gray-500">Код качества:</span> <span class="font-mono text-xs">{{ fioResult.quality_code }}</span></div>
          </div>
        </div>
      </div>
    </div>

    <!-- Tab: Phone -->
    <div v-if="activeTab === 'phone'" class="max-w-2xl">
      <div class="bg-white rounded-lg border border-gray-200 p-6">
        <h3 class="text-lg font-semibold mb-4">Нормализация телефона</h3>
        <div class="mb-4">
          <label class="block text-sm font-medium text-gray-600 mb-1">Телефон</label>
          <input v-model="phoneInput" class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" placeholder="+79261234567" />
        </div>
        <button
          @click="checkPhone"
          :disabled="phoneLoading"
          class="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 cursor-pointer"
        >
          {{ phoneLoading ? 'Проверка...' : 'Проверить' }}
        </button>

        <div v-if="phoneError" class="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
          {{ phoneError }}
        </div>

        <div v-if="phoneResult" class="mt-4 bg-gray-50 rounded-lg p-4">
          <div class="grid grid-cols-2 gap-3 text-sm">
            <div><span class="text-gray-500">Код страны:</span> <span class="font-medium">{{ phoneResult.country_code }}</span></div>
            <div><span class="text-gray-500">Код города:</span> <span class="font-medium">{{ phoneResult.city_code }}</span></div>
            <div><span class="text-gray-500">Номер:</span> <span class="font-medium">{{ phoneResult.number }}</span></div>
            <div><span class="text-gray-500">Код качества:</span> <span class="font-mono text-xs">{{ phoneResult.quality_code }}</span></div>
          </div>
        </div>
      </div>
    </div>

    <!-- Tab: Balance -->
    <div v-if="activeTab === 'balance'" class="max-w-2xl">
      <div class="bg-white rounded-lg border border-gray-200 p-6">
        <h3 class="text-lg font-semibold mb-4">Баланс аккаунта Почты России</h3>
        <button
          @click="checkBalance"
          :disabled="balanceLoading"
          class="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 cursor-pointer"
        >
          {{ balanceLoading ? 'Загрузка...' : 'Проверить баланс' }}
        </button>

        <div v-if="balanceError" class="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
          {{ balanceError }}
        </div>

        <div v-if="balanceUnavailable" class="mt-4 p-4 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-800 flex gap-3">
          <span class="text-xl">⚠️</span>
          <div>
            <div class="font-medium mb-1">Баланс недоступен</div>
            <div>{{ balanceUnavailable }}</div>
          </div>
        </div>

        <div v-if="balanceResult !== null" class="mt-4 bg-gray-50 rounded-lg p-6 text-center">
          <div class="text-sm text-gray-500 mb-1">Баланс</div>
          <div class="text-3xl font-bold text-blue-700">{{ kopecks(balanceResult) }}</div>
        </div>
      </div>
    </div>
  </div>
</template>
