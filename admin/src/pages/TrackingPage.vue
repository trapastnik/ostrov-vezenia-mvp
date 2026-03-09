<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'

interface TrackingEvent {
  event_type: string
  description: string
  location: string | null
  details: string | null
  created_at: string
}

interface TrackingData {
  order_id: string
  external_order_id: string
  internal_track_number: string | null
  track_number: string | null
  status: string
  recipient_name: string
  recipient_postal_code: string
  shipment_group_number: string | null
  hub_name: string | null
  events: TrackingEvent[]
}

const route = useRoute()

const query = ref('')
const tracking = ref<TrackingData | null>(null)
const loading = ref(false)
const error = ref('')
const searched = ref(false)

const STATUS_LABELS: Record<string, string> = {
  accepted: 'Принят',
  awaiting_pickup: 'Ожидает забора',
  received_warehouse: 'На складе',
  batch_forming: 'Формирование партии',
  customs_presented: 'Таможенное оформление',
  customs_cleared: 'Таможня пройдена',
  awaiting_carrier: 'Подготовка к отправке',
  shipped: 'Отправлен',
  in_transit: 'В пути',
  delivered: 'Доставлен',
  cancelled: 'Отменён',
  problem: 'Проблема',
}

const STATUS_COLORS: Record<string, string> = {
  accepted: 'text-blue-600',
  awaiting_pickup: 'text-yellow-600',
  received_warehouse: 'text-indigo-600',
  batch_forming: 'text-purple-600',
  customs_presented: 'text-orange-600',
  customs_cleared: 'text-teal-600',
  awaiting_carrier: 'text-cyan-600',
  shipped: 'text-sky-600',
  in_transit: 'text-amber-600',
  delivered: 'text-green-600',
  cancelled: 'text-gray-500',
  problem: 'text-red-600',
}

const EVENT_ICONS: Record<string, string> = {
  order_accepted: '📦',
  order_validating: '🔍',
  order_customs_processing: '🛃',
  order_customs_cleared: '✅',
  order_awaiting_group: '📋',
  last_mile_transferred: '🚚',
  last_mile_in_transit: '🚛',
  delivered: '🎉',
  problem: '⚠️',
  cancelled: '❌',
}

async function search() {
  const q = query.value.trim()
  if (!q) return

  loading.value = true
  error.value = ''
  tracking.value = null
  searched.value = true

  try {
    const baseUrl = import.meta.env.VITE_API_BASE_URL || ''
    const resp = await fetch(`${baseUrl}/api/v1/track/search/${encodeURIComponent(q)}`)
    if (!resp.ok) {
      const data = await resp.json().catch(() => ({}))
      throw new Error(data.detail || `Заказ не найден`)
    }
    tracking.value = await resp.json()
  } catch (e: any) {
    error.value = e.message || 'Ошибка поиска'
  } finally {
    loading.value = false
  }
}

function formatDate(iso: string): string {
  const d = new Date(iso)
  return d.toLocaleDateString('ru-RU', {
    day: '2-digit',
    month: 'long',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

onMounted(() => {
  // Если в URL есть параметр ?q=..., сразу ищем
  const q = route.query.q as string
  if (q) {
    query.value = q
    search()
  }
})
</script>

<template>
  <div class="min-h-screen bg-gradient-to-b from-blue-50 to-white">
    <div class="max-w-2xl mx-auto px-4 py-12">
      <!-- Header -->
      <div class="text-center mb-8">
        <h1 class="text-3xl font-bold text-gray-900 mb-2">Отслеживание заказа</h1>
        <p class="text-gray-500">Введите номер заказа или трек-номер</p>
      </div>

      <!-- Search -->
      <form @submit.prevent="search" class="flex gap-3 mb-8">
        <input
          v-model="query"
          type="text"
          placeholder="Номер заказа, трек-номер ПР или OV-номер..."
          class="flex-1 px-4 py-3 border border-gray-300 rounded-xl text-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent shadow-sm"
          autofocus
        />
        <button
          type="submit"
          :disabled="loading || !query.trim()"
          class="px-6 py-3 bg-blue-600 text-white rounded-xl text-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed shadow-sm transition-colors"
        >
          {{ loading ? '...' : 'Найти' }}
        </button>
      </form>

      <!-- Loading -->
      <div v-if="loading" class="flex justify-center py-12">
        <div class="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600"></div>
      </div>

      <!-- Error -->
      <div v-else-if="error" class="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
        <div class="text-red-600 text-lg mb-1">{{ error }}</div>
        <div class="text-red-400 text-sm">Проверьте номер и попробуйте снова</div>
      </div>

      <!-- Not found hint -->
      <div v-else-if="searched && !tracking" class="text-center py-12 text-gray-400">
        Заказ не найден
      </div>

      <!-- Tracking result -->
      <div v-else-if="tracking">
        <!-- Order info card -->
        <div class="bg-white border border-gray-200 rounded-xl p-6 mb-6 shadow-sm">
          <div class="flex items-start justify-between mb-4">
            <div>
              <div class="text-sm text-gray-500">Заказ</div>
              <div class="text-xl font-bold text-gray-900">{{ tracking.external_order_id }}</div>
            </div>
            <div class="text-right">
              <div class="text-sm text-gray-500">Статус</div>
              <div class="text-lg font-semibold" :class="STATUS_COLORS[tracking.status] || 'text-gray-600'">
                {{ STATUS_LABELS[tracking.status] || tracking.status }}
              </div>
            </div>
          </div>
          <div class="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span class="text-gray-400">Получатель:</span>
              <span class="ml-1 text-gray-700">{{ tracking.recipient_name }}</span>
            </div>
            <div>
              <span class="text-gray-400">Индекс:</span>
              <span class="ml-1 text-gray-700">{{ tracking.recipient_postal_code }}</span>
            </div>
            <div v-if="tracking.track_number">
              <span class="text-gray-400">Трек ПР:</span>
              <span class="ml-1 text-gray-700 font-medium">{{ tracking.track_number }}</span>
            </div>
            <div v-if="tracking.internal_track_number">
              <span class="text-gray-400">Внутренний №:</span>
              <span class="ml-1 text-gray-700">{{ tracking.internal_track_number }}</span>
            </div>
          </div>
        </div>

        <!-- Timeline -->
        <div class="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
          <h3 class="text-lg font-semibold text-gray-900 mb-4">История</h3>
          <div v-if="tracking.events.length === 0" class="text-gray-400 text-center py-4">
            Нет событий
          </div>
          <div v-else class="relative">
            <!-- Timeline line -->
            <div class="absolute left-5 top-2 bottom-2 w-0.5 bg-gray-200"></div>

            <div
              v-for="(event, idx) in [...tracking.events].reverse()"
              :key="idx"
              class="relative flex gap-4 pb-6 last:pb-0"
            >
              <!-- Dot -->
              <div
                class="relative z-10 w-10 h-10 rounded-full flex items-center justify-center text-lg shrink-0"
                :class="idx === 0 ? 'bg-blue-100 ring-2 ring-blue-400' : 'bg-gray-100'"
              >
                {{ EVENT_ICONS[event.event_type] || '📌' }}
              </div>

              <!-- Content -->
              <div class="flex-1 pt-1">
                <div class="text-gray-900 font-medium">{{ event.description }}</div>
                <div class="text-sm text-gray-400 mt-0.5">{{ formatDate(event.created_at) }}</div>
                <div v-if="event.location" class="text-sm text-gray-500 mt-1">
                  📍 {{ event.location }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div class="text-center mt-12 text-sm text-gray-400">
        Остров Везения — логистический сервис
      </div>
    </div>
  </div>
</template>
