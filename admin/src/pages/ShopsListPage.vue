<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { fetchShops, createShop } from '../api/shops'
import type { Shop } from '../types'

const router = useRouter()
const shops = ref<Shop[]>([])
const loading = ref(true)
const showForm = ref(false)
const newShop = ref({ name: '', domain: '', webhook_url: '', customs_fee_kopecks: 15000, sender_postal_code: '238311' })
const error = ref('')

async function load() {
  loading.value = true
  try {
    const data = await fetchShops()
    shops.value = data.items
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function handleCreate() {
  error.value = ''
  try {
    await createShop({
      name: newShop.value.name,
      domain: newShop.value.domain,
      webhook_url: newShop.value.webhook_url || undefined,
      customs_fee_kopecks: newShop.value.customs_fee_kopecks,
      sender_postal_code: newShop.value.sender_postal_code,
    })
    showForm.value = false
    newShop.value = { name: '', domain: '', webhook_url: '', customs_fee_kopecks: 15000, sender_postal_code: '238311' }
    await load()
  } catch (e: any) {
    error.value = e.response?.data?.detail || 'Ошибка создания'
  }
}

onMounted(load)
</script>

<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h2 class="text-2xl font-bold text-gray-800">Магазины</h2>
      <button @click="showForm = !showForm" class="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 cursor-pointer">
        {{ showForm ? 'Отмена' : 'Добавить магазин' }}
      </button>
    </div>

    <div v-if="showForm" class="bg-white rounded-xl border border-gray-200 p-5 mb-6">
      <h3 class="font-semibold text-gray-800 mb-4">Новый магазин</h3>
      <form @submit.prevent="handleCreate" class="grid grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Название</label>
          <input v-model="newShop.name" required class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Домен</label>
          <input v-model="newShop.domain" required placeholder="ikea-39.ru" class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Webhook URL</label>
          <input v-model="newShop.webhook_url" placeholder="https://..." class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Ставка за оформление (коп.)</label>
          <input v-model.number="newShop.customs_fee_kopecks" type="number" class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
        </div>
        <div v-if="error" class="col-span-2 text-sm text-red-600">{{ error }}</div>
        <div class="col-span-2">
          <button type="submit" class="px-4 py-2 bg-green-600 text-white text-sm rounded-lg hover:bg-green-700 cursor-pointer">Создать</button>
        </div>
      </form>
    </div>

    <div class="bg-white rounded-xl border border-gray-200">
      <div v-if="loading" class="p-8 text-center text-gray-400">Загрузка...</div>
      <table v-else class="w-full">
        <thead>
          <tr class="text-left text-xs text-gray-500 uppercase border-b border-gray-100">
            <th class="px-5 py-3">Название</th>
            <th class="px-5 py-3">Домен</th>
            <th class="px-5 py-3">API ключ</th>
            <th class="px-5 py-3">Ставка</th>
            <th class="px-5 py-3">Статус</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="shop in shops"
            :key="shop.id"
            @click="router.push(`/shops/${shop.id}`)"
            class="border-b border-gray-50 hover:bg-blue-50 cursor-pointer"
          >
            <td class="px-5 py-3 text-sm font-medium text-gray-800">{{ shop.name }}</td>
            <td class="px-5 py-3 text-sm text-gray-600">{{ shop.domain }}</td>
            <td class="px-5 py-3 text-sm text-gray-400 font-mono">{{ shop.api_key.slice(0, 12) }}...</td>
            <td class="px-5 py-3 text-sm text-gray-700">{{ (shop.customs_fee_kopecks / 100).toFixed(0) }} &#8381;</td>
            <td class="px-5 py-3">
              <span :class="shop.is_active ? 'text-green-600' : 'text-red-600'" class="text-sm">
                {{ shop.is_active ? 'Активен' : 'Неактивен' }}
              </span>
            </td>
          </tr>
          <tr v-if="shops.length === 0">
            <td colspan="5" class="px-5 py-8 text-center text-sm text-gray-400">Нет магазинов</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
