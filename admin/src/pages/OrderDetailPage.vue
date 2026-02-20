<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { fetchOrder, changeOrderStatus } from '../api/orders'
import OrderStatusBadge from '../components/OrderStatusBadge.vue'
import ChangeStatusModal from '../components/ChangeStatusModal.vue'
import { ALLOWED_TRANSITIONS } from '../types'
import type { OrderDetail } from '../types'

const route = useRoute()
const order = ref<OrderDetail | null>(null)
const loading = ref(true)
const showModal = ref(false)
const error = ref('')

async function load() {
  loading.value = true
  try {
    order.value = await fetchOrder(route.params.id as string)
  } catch (e: any) {
    error.value = e.response?.data?.detail || 'Ошибка загрузки'
  } finally {
    loading.value = false
  }
}

async function handleStatusChange(newStatus: string, comment: string) {
  showModal.value = false
  try {
    await changeOrderStatus(route.params.id as string, newStatus, comment)
    await load()
  } catch (e: any) {
    error.value = e.response?.data?.detail || 'Ошибка смены статуса'
  }
}

function formatDate(d: string): string {
  return new Date(d).toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

function formatPrice(kopecks: number): string {
  return (kopecks / 100).toLocaleString('ru-RU', { style: 'currency', currency: 'RUB', maximumFractionDigits: 0 })
}

function formatWeight(grams: number): string {
  return grams >= 1000 ? (grams / 1000).toFixed(1) + ' кг' : grams + ' г'
}

function canChangeStatus(): boolean {
  if (!order.value) return false
  const transitions = ALLOWED_TRANSITIONS[order.value.status]
  return !!transitions && transitions.length > 0
}

onMounted(load)
</script>

<template>
  <div>
    <router-link to="/orders" class="text-sm text-blue-600 hover:underline mb-4 inline-block">&larr; К списку заказов</router-link>

    <div v-if="loading" class="text-gray-500">Загрузка...</div>
    <div v-else-if="error" class="text-red-600">{{ error }}</div>

    <template v-else-if="order">
      <div class="flex items-center gap-4 mb-6">
        <h2 class="text-2xl font-bold text-gray-800">Заказ {{ order.external_order_id }}</h2>
        <OrderStatusBadge :status="order.status" />
        <button
          v-if="canChangeStatus()"
          @click="showModal = true"
          class="ml-auto px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 cursor-pointer"
        >
          Сменить статус
        </button>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">

        <!-- Товары в заказе -->
        <div class="bg-white rounded-xl border border-gray-200 p-5 lg:col-span-2">
          <h3 class="font-semibold text-gray-800 mb-4">Товары в заказе</h3>
          <table class="w-full text-sm">
            <thead>
              <tr class="text-left text-xs text-gray-500 uppercase border-b border-gray-100">
                <th class="pb-2 font-medium">Артикул</th>
                <th class="pb-2 font-medium">Название</th>
                <th class="pb-2 font-medium text-right">Цена</th>
                <th class="pb-2 font-medium text-center">Кол-во</th>
                <th class="pb-2 font-medium text-right">Вес</th>
                <th class="pb-2 font-medium text-right">Сумма</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(item, i) in order.items" :key="i" class="border-b border-gray-50">
                <td class="py-2 text-gray-400 text-xs font-mono">{{ item.sku || '—' }}</td>
                <td class="py-2 text-gray-800 font-medium">{{ item.name }}</td>
                <td class="py-2 text-gray-600 text-right">{{ formatPrice(item.price_kopecks) }}</td>
                <td class="py-2 text-gray-600 text-center">{{ item.quantity }}</td>
                <td class="py-2 text-gray-600 text-right">{{ formatWeight(item.weight_grams) }}</td>
                <td class="py-2 text-gray-800 font-semibold text-right">{{ formatPrice(item.price_kopecks * item.quantity) }}</td>
              </tr>
            </tbody>
            <tfoot>
              <tr class="border-t border-gray-200">
                <td></td>
                <td class="pt-3 font-semibold text-gray-800">Итого</td>
                <td></td>
                <td class="pt-3 text-center text-gray-600">{{ order.items.reduce((s: number, i: any) => s + i.quantity, 0) }} шт</td>
                <td class="pt-3 text-right text-gray-600">{{ formatWeight(order.total_weight_grams) }}</td>
                <td class="pt-3 text-right font-bold text-gray-900">{{ formatPrice(order.total_amount_kopecks) }}</td>
              </tr>
            </tfoot>
          </table>
        </div>

        <!-- Получатель -->
        <div class="bg-white rounded-xl border border-gray-200 p-5">
          <h3 class="font-semibold text-gray-800 mb-4">Получатель</h3>
          <dl class="space-y-3 text-sm">
            <div class="flex"><dt class="w-28 text-gray-500 shrink-0">ФИО</dt><dd class="text-gray-800 font-medium">{{ order.recipient_name }}</dd></div>
            <div class="flex"><dt class="w-28 text-gray-500 shrink-0">Телефон</dt><dd class="text-gray-800">{{ order.recipient_phone }}</dd></div>
            <div v-if="order.recipient_email" class="flex"><dt class="w-28 text-gray-500 shrink-0">Email</dt><dd class="text-gray-800">{{ order.recipient_email }}</dd></div>
            <div class="flex"><dt class="w-28 text-gray-500 shrink-0">Адрес</dt><dd class="text-gray-800">{{ order.recipient_address }}</dd></div>
            <div class="flex"><dt class="w-28 text-gray-500 shrink-0">Индекс</dt><dd class="text-gray-800">{{ order.recipient_postal_code }}</dd></div>
          </dl>
        </div>

        <!-- Стоимость -->
        <div class="bg-white rounded-xl border border-gray-200 p-5">
          <h3 class="font-semibold text-gray-800 mb-4">Стоимость</h3>
          <dl class="space-y-3 text-sm">
            <div class="flex justify-between"><dt class="text-gray-500">Товары</dt><dd class="text-gray-800 font-medium">{{ formatPrice(order.total_amount_kopecks) }}</dd></div>
            <div class="flex justify-between"><dt class="text-gray-500">Доставка (Почта России)</dt><dd class="text-gray-800 font-medium">{{ formatPrice(order.delivery_cost_kopecks) }}</dd></div>
            <div class="flex justify-between"><dt class="text-gray-500">Таможенное оформление</dt><dd class="text-gray-800 font-medium">{{ formatPrice(order.customs_fee_kopecks) }}</dd></div>
            <div class="flex justify-between border-t border-gray-200 pt-3 mt-2">
              <dt class="text-gray-900 font-bold">Итого</dt>
              <dd class="text-blue-700 font-bold text-lg">{{ formatPrice(order.total_amount_kopecks + order.delivery_cost_kopecks + order.customs_fee_kopecks) }}</dd>
            </div>
          </dl>
          <div class="mt-5 pt-4 border-t border-gray-100">
            <dl class="space-y-2 text-sm">
              <div class="flex justify-between"><dt class="text-gray-500">Трек Почты РФ</dt><dd class="text-gray-800 font-mono text-xs">{{ order.track_number || '—' }}</dd></div>
              <div class="flex justify-between"><dt class="text-gray-500">Наш трек-номер</dt>
                <dd>
                  <span v-if="order.internal_track_number" class="font-mono text-xs bg-blue-50 text-blue-700 px-2 py-0.5 rounded">
                    {{ order.internal_track_number }}
                  </span>
                  <span v-else class="text-gray-400">—</span>
                </dd>
              </div>
              <div class="flex justify-between"><dt class="text-gray-500">Создан</dt><dd class="text-gray-800">{{ formatDate(order.created_at) }}</dd></div>
            </dl>
          </div>
        </div>

        <!-- Тарифы: публичный vs наш -->
        <div v-if="order.public_tariff_kopecks" class="bg-white rounded-xl border border-gray-200 p-5">
          <h3 class="font-semibold text-gray-800 mb-4">Тариф доставки</h3>
          <div class="space-y-2 text-sm">
            <div class="flex justify-between">
              <span class="text-gray-500">Публичный тариф</span>
              <span class="font-medium text-gray-700">{{ formatPrice(order.public_tariff_kopecks) }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-500">Наш (контрактный)</span>
              <span class="font-medium text-green-700">{{ formatPrice(order.contract_tariff_kopecks) }}</span>
            </div>
            <div v-if="order.tariff_savings_kopecks && order.tariff_savings_kopecks > 0"
              class="flex justify-between border-t border-gray-100 pt-2 mt-1">
              <span class="text-emerald-600 font-medium">Экономия</span>
              <span class="font-bold text-emerald-600">
                {{ formatPrice(order.tariff_savings_kopecks) }}
                <span class="text-xs font-normal ml-1">({{ order.tariff_savings_percent }}%)</span>
              </span>
            </div>
          </div>
        </div>

        <!-- История статусов -->
        <div class="bg-white rounded-xl border border-gray-200 p-5 lg:col-span-2">
          <h3 class="font-semibold text-gray-800 mb-4">История статусов</h3>
          <div class="space-y-3">
            <div v-for="(entry, i) in order.history" :key="i" class="flex gap-3 text-sm">
              <div class="w-36 text-gray-400 shrink-0">{{ formatDate(entry.created_at) }}</div>
              <div>
                <OrderStatusBadge :status="entry.new_status" />
                <p v-if="entry.comment" class="text-gray-500 mt-1 text-xs">{{ entry.comment }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <ChangeStatusModal
        v-if="showModal"
        :current-status="order.status"
        @confirm="handleStatusChange"
        @cancel="showModal = false"
      />
    </template>
  </div>
</template>
