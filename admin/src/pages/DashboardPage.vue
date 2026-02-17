<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { fetchOrders } from '../api/orders'
import { fetchShops } from '../api/shops'
import { fetchBatches } from '../api/batches'
import OrderStatusBadge from '../components/OrderStatusBadge.vue'
import type { Order } from '../types'

const stats = ref({ orders: 0, shops: 0, batches: 0 })
const recentOrders = ref<Order[]>([])
const loading = ref(true)

onMounted(async () => {
  try {
    const [ordersData, shopsData, batchesData] = await Promise.all([
      fetchOrders({ per_page: 5 }),
      fetchShops(),
      fetchBatches(),
    ])
    stats.value = {
      orders: ordersData.total,
      shops: shopsData.total,
      batches: batchesData.total,
    }
    recentOrders.value = ordersData.items
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
})

function kopecksToRubles(k: number): string {
  return (k / 100).toFixed(2)
}
</script>

<template>
  <div>
    <h2 class="text-2xl font-bold text-gray-800 mb-6">Главная</h2>

    <div v-if="loading" class="text-gray-500">Загрузка...</div>

    <template v-else>
      <div class="grid grid-cols-3 gap-4 mb-8">
        <div class="bg-white rounded-xl border border-gray-200 p-5">
          <div class="text-3xl font-bold text-blue-600">{{ stats.orders }}</div>
          <div class="text-sm text-gray-500 mt-1">Заказов</div>
        </div>
        <div class="bg-white rounded-xl border border-gray-200 p-5">
          <div class="text-3xl font-bold text-green-600">{{ stats.shops }}</div>
          <div class="text-sm text-gray-500 mt-1">Магазинов</div>
        </div>
        <div class="bg-white rounded-xl border border-gray-200 p-5">
          <div class="text-3xl font-bold text-purple-600">{{ stats.batches }}</div>
          <div class="text-sm text-gray-500 mt-1">Партий</div>
        </div>
      </div>

      <div class="bg-white rounded-xl border border-gray-200">
        <div class="px-5 py-4 border-b border-gray-200">
          <h3 class="font-semibold text-gray-800">Последние заказы</h3>
        </div>
        <table class="w-full">
          <thead>
            <tr class="text-left text-xs text-gray-500 uppercase border-b border-gray-100">
              <th class="px-5 py-3">Заказ</th>
              <th class="px-5 py-3">Получатель</th>
              <th class="px-5 py-3">Сумма</th>
              <th class="px-5 py-3">Статус</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="order in recentOrders" :key="order.id" class="border-b border-gray-50 hover:bg-gray-50">
              <td class="px-5 py-3">
                <router-link :to="`/orders/${order.id}`" class="text-sm text-blue-600 hover:underline">
                  {{ order.external_order_id }}
                </router-link>
              </td>
              <td class="px-5 py-3 text-sm text-gray-700">{{ order.recipient_name }}</td>
              <td class="px-5 py-3 text-sm text-gray-700">{{ kopecksToRubles(order.total_amount_kopecks) }} &#8381;</td>
              <td class="px-5 py-3"><OrderStatusBadge :status="order.status" /></td>
            </tr>
            <tr v-if="recentOrders.length === 0">
              <td colspan="4" class="px-5 py-8 text-center text-sm text-gray-400">Нет заказов</td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>
  </div>
</template>
