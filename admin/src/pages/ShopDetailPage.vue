<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { fetchShop, updateShop } from '../api/shops'
import type { Shop } from '../types'

const route = useRoute()
const shop = ref<Shop | null>(null)
const loading = ref(true)
const saving = ref(false)
const error = ref('')
const success = ref('')
const copied = ref(false)

const form = ref({
  name: '',
  webhook_url: '',
  customs_fee_kopecks: 0,
  is_active: true,
})

async function load() {
  loading.value = true
  try {
    shop.value = await fetchShop(route.params.id as string)
    form.value = {
      name: shop.value.name,
      webhook_url: shop.value.webhook_url || '',
      customs_fee_kopecks: shop.value.customs_fee_kopecks,
      is_active: shop.value.is_active,
    }
  } catch (e: any) {
    error.value = e.response?.data?.detail || 'Ошибка'
  } finally {
    loading.value = false
  }
}

async function save() {
  saving.value = true
  error.value = ''
  success.value = ''
  try {
    await updateShop(route.params.id as string, {
      name: form.value.name,
      webhook_url: form.value.webhook_url || null,
      customs_fee_kopecks: form.value.customs_fee_kopecks,
      is_active: form.value.is_active,
    })
    success.value = 'Сохранено'
    await load()
  } catch (e: any) {
    error.value = e.response?.data?.detail || 'Ошибка сохранения'
  } finally {
    saving.value = false
  }
}

function copyApiKey() {
  if (shop.value) {
    navigator.clipboard.writeText(shop.value.api_key)
    copied.value = true
    setTimeout(() => copied.value = false, 2000)
  }
}

onMounted(load)
</script>

<template>
  <div>
    <router-link to="/shops" class="text-sm text-blue-600 hover:underline mb-4 inline-block">&larr; К списку магазинов</router-link>

    <div v-if="loading" class="text-gray-500">Загрузка...</div>
    <div v-else-if="error && !shop" class="text-red-600">{{ error }}</div>

    <template v-else-if="shop">
      <h2 class="text-2xl font-bold text-gray-800 mb-6">{{ shop.name }}</h2>

      <div class="grid grid-cols-2 gap-6">
        <div class="bg-white rounded-xl border border-gray-200 p-5">
          <h3 class="font-semibold text-gray-800 mb-4">Настройки</h3>
          <form @submit.prevent="save" class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Название</label>
              <input v-model="form.name" class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Webhook URL</label>
              <input v-model="form.webhook_url" class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" placeholder="https://..." />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Ставка за оформление (коп.)</label>
              <input v-model.number="form.customs_fee_kopecks" type="number" class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
            </div>
            <div class="flex items-center gap-2">
              <input v-model="form.is_active" type="checkbox" id="active" class="rounded" />
              <label for="active" class="text-sm text-gray-700">Активен</label>
            </div>

            <div v-if="error" class="text-sm text-red-600">{{ error }}</div>
            <div v-if="success" class="text-sm text-green-600">{{ success }}</div>

            <button type="submit" :disabled="saving" class="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 disabled:opacity-50 cursor-pointer">
              {{ saving ? 'Сохранение...' : 'Сохранить' }}
            </button>
          </form>
        </div>

        <div class="bg-white rounded-xl border border-gray-200 p-5">
          <h3 class="font-semibold text-gray-800 mb-4">Информация</h3>
          <dl class="space-y-3 text-sm">
            <div>
              <dt class="text-gray-500 mb-1">Домен</dt>
              <dd class="text-gray-800 font-medium">{{ shop.domain }}</dd>
            </div>
            <div>
              <dt class="text-gray-500 mb-1">API ключ</dt>
              <dd class="flex items-center gap-2">
                <code class="text-xs bg-gray-100 px-2 py-1 rounded font-mono break-all">{{ shop.api_key }}</code>
                <button @click="copyApiKey" class="text-xs text-blue-600 hover:underline cursor-pointer">
                  {{ copied ? 'Скопировано' : 'Копировать' }}
                </button>
              </dd>
            </div>
            <div>
              <dt class="text-gray-500 mb-1">Индекс отправки</dt>
              <dd class="text-gray-800">{{ shop.sender_postal_code }}</dd>
            </div>
            <div>
              <dt class="text-gray-500 mb-1">Создан</dt>
              <dd class="text-gray-800">{{ new Date(shop.created_at).toLocaleDateString('ru-RU') }}</dd>
            </div>
          </dl>
        </div>
      </div>
    </template>
  </div>
</template>
