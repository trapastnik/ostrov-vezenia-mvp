<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import {
  fetchGroups, updateGroupStatus, forceDispatchGroup,
  fetchGroupingSettings, updateGroupingSettings,
} from '../api/groups'
import type { ShipmentGroup, GroupingSettings } from '../api/groups'

// --- Tabs ---
const activeTab = ref<'groups' | 'settings'>('groups')

// --- Groups list ---
const groups = ref<ShipmentGroup[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 20
const filterStatus = ref('')
const filterHub = ref('')
const loading = ref(false)
const error = ref('')

const GROUP_STATUSES = [
  { value: '', label: 'Все статусы' },
  { value: 'forming', label: 'Формируется' },
  { value: 'ready', label: 'Готова' },
  { value: 'dispatched', label: 'Отправлена' },
  { value: 'at_hub', label: 'В хабе' },
  { value: 'completed', label: 'Завершена' },
  { value: 'cancelled', label: 'Отменена' },
]

const STATUS_COLORS: Record<string, string> = {
  forming: 'bg-yellow-100 text-yellow-800',
  ready: 'bg-blue-100 text-blue-800',
  dispatched: 'bg-purple-100 text-purple-800',
  at_hub: 'bg-indigo-100 text-indigo-800',
  completed: 'bg-green-100 text-green-800',
  cancelled: 'bg-gray-100 text-gray-600',
}

const STATUS_LABELS: Record<string, string> = {
  forming: 'Формируется',
  ready: 'Готова',
  dispatched: 'Отправлена',
  at_hub: 'В хабе',
  completed: 'Завершена',
  cancelled: 'Отменена',
}

const TRANSPORT_LABELS: Record<string, string> = {
  air: '✈ Авиа',
  truck: '🚛 Авто',
  rail: '🚂 ЖД',
}

async function loadGroups() {
  loading.value = true
  error.value = ''
  try {
    const res = await fetchGroups({
      page: page.value,
      page_size: pageSize,
      status: filterStatus.value || undefined,
      hub: filterHub.value || undefined,
    })
    groups.value = res.items
    total.value = res.total
  } catch (e: any) {
    error.value = e.response?.data?.detail || 'Ошибка загрузки'
  } finally {
    loading.value = false
  }
}

watch([filterStatus, filterHub], () => { page.value = 1; loadGroups() })

// --- Force dispatch ---
const dispatchNote = ref('')
const dispatchingId = ref<string | null>(null)

async function handleForceDispatch(group: ShipmentGroup) {
  if (!confirm(`Принудительно отправить группу ${group.number}?`)) return
  dispatchingId.value = group.id
  try {
    await forceDispatchGroup(group.id, dispatchNote.value || undefined)
    await loadGroups()
  } catch (e: any) {
    alert(e.response?.data?.detail || 'Ошибка')
  } finally {
    dispatchingId.value = null
  }
}

async function handleStatusUpdate(group: ShipmentGroup, newStatus: string) {
  try {
    await updateGroupStatus(group.id, newStatus)
    await loadGroups()
  } catch (e: any) {
    alert(e.response?.data?.detail || 'Ошибка')
  }
}

// --- Settings ---
const settings = ref<GroupingSettings | null>(null)
const settingsLoading = ref(false)
const settingsSaved = ref(false)
const settingsError = ref('')

async function loadSettings() {
  settingsLoading.value = true
  try {
    settings.value = await fetchGroupingSettings()
  } catch (e: any) {
    settingsError.value = e.response?.data?.detail || 'Ошибка загрузки'
  } finally {
    settingsLoading.value = false
  }
}

async function saveSettings() {
  if (!settings.value) return
  settingsLoading.value = true
  settingsSaved.value = false
  settingsError.value = ''
  try {
    settings.value = await updateGroupingSettings({
      enabled: settings.value.enabled,
      max_wait_hours: settings.value.max_wait_hours,
      min_group_size: settings.value.min_group_size,
      min_savings_rub: settings.value.min_savings_rub,
      penalty_per_hour_rub: settings.value.penalty_per_hour_rub,
      worker_interval_minutes: settings.value.worker_interval_minutes,
      description: settings.value.description,
    })
    settingsSaved.value = true
    setTimeout(() => { settingsSaved.value = false }, 3000)
  } catch (e: any) {
    settingsError.value = e.response?.data?.detail || 'Ошибка сохранения'
  } finally {
    settingsLoading.value = false
  }
}

// --- Helpers ---
function formatPrice(kopecks: number): string {
  return (kopecks / 100).toLocaleString('ru-RU', { style: 'currency', currency: 'RUB', maximumFractionDigits: 0 })
}

function formatWeight(grams: number): string {
  return grams >= 1000 ? (grams / 1000).toFixed(1) + ' кг' : grams + ' г'
}

function formatDate(d: string | null): string {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

const totalPages = () => Math.ceil(total.value / pageSize)

onMounted(() => {
  loadGroups()
  loadSettings()
})
</script>

<template>
  <div>
    <h2 class="text-2xl font-bold text-gray-800 mb-6">Группы отправок</h2>

    <!-- Tabs -->
    <div class="flex gap-1 mb-6 border-b border-gray-200">
      <button
        v-for="tab in [{ key: 'groups', label: 'Группы' }, { key: 'settings', label: 'Настройки оптимизатора' }]"
        :key="tab.key"
        @click="activeTab = tab.key as typeof activeTab"
        class="px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors cursor-pointer"
        :class="activeTab === tab.key ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'"
      >
        {{ tab.label }}
      </button>
    </div>

    <!-- Tab: Groups -->
    <div v-if="activeTab === 'groups'">
      <!-- Filters -->
      <div class="flex gap-3 mb-5">
        <select v-model="filterStatus" class="border border-gray-300 rounded-lg px-3 py-2 text-sm">
          <option v-for="s in GROUP_STATUSES" :key="s.value" :value="s.value">{{ s.label }}</option>
        </select>
        <input
          v-model="filterHub"
          placeholder="Фильтр по хабу (msk, spb...)"
          class="border border-gray-300 rounded-lg px-3 py-2 text-sm w-52"
        />
        <button @click="loadGroups" class="px-4 py-2 bg-gray-100 text-gray-700 text-sm rounded-lg hover:bg-gray-200 cursor-pointer">
          Обновить
        </button>
      </div>

      <div v-if="error" class="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">{{ error }}</div>
      <div v-if="loading" class="text-gray-400 text-sm">Загрузка...</div>

      <!-- Table -->
      <div v-else class="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <table class="w-full text-sm">
          <thead>
            <tr class="text-left text-xs text-gray-500 uppercase bg-gray-50 border-b border-gray-200">
              <th class="px-4 py-3 font-medium">Группа</th>
              <th class="px-4 py-3 font-medium">Направление</th>
              <th class="px-4 py-3 font-medium text-center">Заказов</th>
              <th class="px-4 py-3 font-medium text-right">Вес</th>
              <th class="px-4 py-3 font-medium text-right">Публичный</th>
              <th class="px-4 py-3 font-medium text-right">Наш тариф</th>
              <th class="px-4 py-3 font-medium text-right">Экономия</th>
              <th class="px-4 py-3 font-medium">Статус</th>
              <th class="px-4 py-3 font-medium">Дата</th>
              <th class="px-4 py-3 font-medium"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="groups.length === 0">
              <td colspan="10" class="px-4 py-8 text-center text-gray-400">Групп не найдено</td>
            </tr>
            <tr v-for="group in groups" :key="group.id" class="border-b border-gray-100 hover:bg-gray-50">
              <td class="px-4 py-3">
                <div class="font-mono text-xs font-semibold text-gray-800">{{ group.number }}</div>
                <div class="text-xs text-gray-400 mt-0.5">{{ TRANSPORT_LABELS[group.transport_type] || group.transport_type }}</div>
              </td>
              <td class="px-4 py-3">
                <div class="font-medium text-gray-800">{{ group.hub_name }}</div>
                <div class="text-xs text-gray-400">{{ group.hub }}</div>
              </td>
              <td class="px-4 py-3 text-center font-semibold text-gray-700">{{ group.orders_count }}</td>
              <td class="px-4 py-3 text-right text-gray-600">{{ formatWeight(group.total_weight_grams) }}</td>
              <td class="px-4 py-3 text-right text-gray-500 line-through">
                {{ group.public_cost_kopecks > 0 ? formatPrice(group.public_cost_kopecks) : '—' }}
              </td>
              <td class="px-4 py-3 text-right font-medium text-gray-800">
                {{ group.contract_cost_kopecks > 0 ? formatPrice(group.contract_cost_kopecks) : '—' }}
              </td>
              <td class="px-4 py-3 text-right">
                <span v-if="group.savings_kopecks > 0" class="text-emerald-600 font-semibold">
                  {{ formatPrice(group.savings_kopecks) }}
                  <span class="text-xs font-normal">({{ group.savings_percent }}%)</span>
                </span>
                <span v-else class="text-gray-300">—</span>
              </td>
              <td class="px-4 py-3">
                <span class="inline-block px-2 py-0.5 rounded text-xs font-medium"
                  :class="STATUS_COLORS[group.status] || 'bg-gray-100 text-gray-600'">
                  {{ STATUS_LABELS[group.status] || group.status }}
                </span>
              </td>
              <td class="px-4 py-3 text-xs text-gray-400">{{ formatDate(group.created_at) }}</td>
              <td class="px-4 py-3">
                <div class="flex gap-2">
                  <button
                    v-if="group.status === 'forming' || group.status === 'ready'"
                    @click="handleForceDispatch(group)"
                    :disabled="dispatchingId === group.id"
                    class="text-xs px-2 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 cursor-pointer"
                  >
                    {{ dispatchingId === group.id ? '...' : 'Отправить' }}
                  </button>
                  <button
                    v-if="group.status === 'dispatched'"
                    @click="handleStatusUpdate(group, 'at_hub')"
                    class="text-xs px-2 py-1 bg-indigo-600 text-white rounded hover:bg-indigo-700 cursor-pointer"
                  >
                    В хаб
                  </button>
                  <button
                    v-if="group.status === 'at_hub'"
                    @click="handleStatusUpdate(group, 'completed')"
                    class="text-xs px-2 py-1 bg-green-600 text-white rounded hover:bg-green-700 cursor-pointer"
                  >
                    Завершить
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination -->
      <div v-if="totalPages() > 1" class="flex justify-center gap-2 mt-4">
        <button
          v-for="p in totalPages()" :key="p"
          @click="page = p; loadGroups()"
          class="w-8 h-8 text-sm rounded"
          :class="page === p ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'"
        >{{ p }}</button>
      </div>

      <!-- Summary bar -->
      <div v-if="groups.length > 0" class="mt-4 flex gap-6 text-sm text-gray-500">
        <span>Всего групп: <strong class="text-gray-800">{{ total }}</strong></span>
        <span>Суммарная экономия:
          <strong class="text-emerald-600">
            {{ formatPrice(groups.reduce((s, g) => s + g.savings_kopecks, 0)) }}
          </strong>
        </span>
      </div>
    </div>

    <!-- Tab: Settings -->
    <div v-if="activeTab === 'settings'" class="max-w-xl">
      <div v-if="settingsLoading && !settings" class="text-gray-400 text-sm">Загрузка...</div>
      <div v-else-if="settings" class="bg-white rounded-xl border border-gray-200 p-6 space-y-5">
        <h3 class="font-semibold text-gray-800">Параметры оптимизатора группировки</h3>

        <!-- Enabled toggle -->
        <div class="flex items-center justify-between py-3 border-b border-gray-100">
          <div>
            <div class="text-sm font-medium text-gray-700">Автогруппировка</div>
            <div class="text-xs text-gray-400 mt-0.5">Воркер автоматически формирует группы по расписанию</div>
          </div>
          <button
            @click="settings.enabled = !settings.enabled"
            class="relative inline-flex h-6 w-11 items-center rounded-full transition-colors cursor-pointer"
            :class="settings.enabled ? 'bg-blue-600' : 'bg-gray-300'"
          >
            <span
              class="inline-block h-4 w-4 transform rounded-full bg-white transition-transform"
              :class="settings.enabled ? 'translate-x-6' : 'translate-x-1'"
            />
          </button>
        </div>

        <!-- Params -->
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">
              Максимальное ожидание заказа (часов)
            </label>
            <div class="text-xs text-gray-400 mb-2">Дедлайн = время создания заказа + это значение. По истечении — принудительная отправка.</div>
            <input v-model.number="settings.max_wait_hours" type="number" min="1" max="168"
              class="w-32 border border-gray-300 rounded-lg px-3 py-2 text-sm" />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">
              Минимальный размер группы (заказов)
            </label>
            <div class="text-xs text-gray-400 mb-2">Группа не отправляется, пока не набралось это количество заказов (если не истёк дедлайн).</div>
            <input v-model.number="settings.min_group_size" type="number" min="1" max="100"
              class="w-32 border border-gray-300 rounded-lg px-3 py-2 text-sm" />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">
              Минимальная экономия для группировки (руб.)
            </label>
            <div class="text-xs text-gray-400 mb-2">Группировать выгодно только если экономия на магистрали превышает это значение.</div>
            <input v-model.number="settings.min_savings_rub" type="number" min="0"
              class="w-32 border border-gray-300 rounded-lg px-3 py-2 text-sm" />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">
              Штраф за просрочку дедлайна (руб./час)
            </label>
            <div class="text-xs text-gray-400 mb-2">
              Используется в функции оптимизации: score = экономия − (штраф × часы_просрочки).
              Чем выше штраф, тем агрессивнее система спешит отправить.
            </div>
            <input v-model.number="settings.penalty_per_hour_rub" type="number" min="0" step="10"
              class="w-32 border border-gray-300 rounded-lg px-3 py-2 text-sm" />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">
              Интервал запуска воркера (минут)
            </label>
            <div class="text-xs text-gray-400 mb-2">Как часто воркер проверяет заказы и принимает решение о группировке.</div>
            <input v-model.number="settings.worker_interval_minutes" type="number" min="5" max="1440"
              class="w-32 border border-gray-300 rounded-lg px-3 py-2 text-sm" />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Описание / заметки</label>
            <textarea v-model="settings.description" rows="2"
              class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
              placeholder="Комментарий для команды..." />
          </div>
        </div>

        <!-- Formula hint -->
        <div class="bg-blue-50 border border-blue-100 rounded-lg p-4 text-xs text-blue-700 space-y-1">
          <div class="font-semibold mb-1">Функция оптимизации:</div>
          <div class="font-mono">score = (публичный_тариф × N) − контрактный_тариф_группы</div>
          <div class="font-mono">      − Σ(max(0, просрочка_i × {{ settings.penalty_per_hour_rub }} руб/час)</div>
          <div class="mt-1">Отправляем если: score > 0 ИЛИ любой заказ просрочен</div>
        </div>

        <div v-if="settingsError" class="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
          {{ settingsError }}
        </div>
        <div v-if="settingsSaved" class="p-3 bg-green-50 border border-green-200 rounded-lg text-sm text-green-700">
          Настройки сохранены
        </div>

        <button
          @click="saveSettings"
          :disabled="settingsLoading"
          class="px-5 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 cursor-pointer"
        >
          {{ settingsLoading ? 'Сохранение...' : 'Сохранить настройки' }}
        </button>
      </div>
    </div>
  </div>
</template>
