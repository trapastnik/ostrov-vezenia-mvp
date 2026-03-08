<script setup lang="ts">
import { ref, onMounted } from 'vue'
import type { TnVedTreeItem } from '../types'
import { fetchTnVedChildren } from '../api/tnved'

const emit = defineEmits<{
  select: [code: string, name: string, unit: string | null]
  close: []
}>()

const items = ref<TnVedTreeItem[]>([])
const loading = ref(false)
const error = ref('')

// Хлебные крошки: массив {code, name} от корня до текущего уровня
const breadcrumbs = ref<{ code: string | null; name: string }[]>([
  { code: null, name: 'ТН ВЭД' },
])

async function loadChildren(parentCode?: string) {
  loading.value = true
  error.value = ''
  try {
    const resp = await fetchTnVedChildren(parentCode)
    items.value = resp.items
  } catch {
    error.value = 'Ошибка загрузки справочника'
    items.value = []
  } finally {
    loading.value = false
  }
}

function navigateTo(item: TnVedTreeItem) {
  if (item.has_children) {
    breadcrumbs.value.push({ code: item.code, name: formatBreadcrumb(item) })
    loadChildren(item.code)
  }
}

function navigateBreadcrumb(index: number) {
  const crumb = breadcrumbs.value[index]
  if (!crumb) return
  // Обрезаем крошки до выбранного уровня
  breadcrumbs.value = breadcrumbs.value.slice(0, index + 1)
  loadChildren(crumb.code ?? undefined)
}

function selectCode(item: TnVedTreeItem) {
  // Убираем хвостовые нули, но минимум 6 цифр
  const code = item.code.replace(/0+$/, '')
  const finalCode = code.length < 6 ? item.code.substring(0, 6) : code
  emit('select', finalCode, item.name, item.unit)
}

function formatCode(code: string): string {
  // Показываем значимую часть кода без хвостовых нулей
  return code.replace(/0+$/, '') || code
}

function formatBreadcrumb(item: TnVedTreeItem): string {
  const code = formatCode(item.code)
  // Для корневых групп показываем 2-значный код
  if (item.level === 2) return `Группа ${code}`
  return code
}

function levelLabel(level: number): string {
  switch (level) {
    case 2: return 'Группа'
    case 4: return 'Позиция'
    case 6: return 'Субпозиция'
    case 8: return 'Подсубпозиция'
    case 10: return 'Код'
    default: return ''
  }
}

function levelColor(level: number): string {
  switch (level) {
    case 2: return 'bg-indigo-100 text-indigo-700'
    case 4: return 'bg-blue-100 text-blue-700'
    case 6: return 'bg-teal-100 text-teal-700'
    case 8: return 'bg-green-100 text-green-700'
    case 10: return 'bg-emerald-100 text-emerald-700'
    default: return 'bg-gray-100 text-gray-700'
  }
}

function isProhibited(item: TnVedTreeItem): boolean {
  return !!item.note && item.note.toUpperCase().includes('ЗАПРЕЩЕНО')
}

onMounted(() => loadChildren())
</script>

<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/40" @click.self="emit('close')">
    <div class="bg-white rounded-xl shadow-xl w-full max-w-2xl max-h-[80vh] overflow-hidden flex flex-col">
      <!-- Header -->
      <div class="px-6 py-4 border-b border-gray-200 flex items-center gap-3">
        <h3 class="text-lg font-semibold text-gray-800">Справочник ТН ВЭД</h3>
        <span class="text-sm text-gray-400">выберите код</span>
        <button @click="emit('close')" class="ml-auto text-gray-400 hover:text-gray-600 cursor-pointer text-xl">&times;</button>
      </div>

      <!-- Breadcrumbs -->
      <div class="px-6 py-2 border-b border-gray-100 flex items-center gap-1 text-sm flex-wrap">
        <template v-for="(crumb, idx) in breadcrumbs" :key="idx">
          <span v-if="idx > 0" class="text-gray-300">/</span>
          <button
            @click="navigateBreadcrumb(idx)"
            class="cursor-pointer hover:text-blue-600 transition-colors"
            :class="idx === breadcrumbs.length - 1 ? 'text-gray-800 font-medium' : 'text-blue-500'"
          >
            {{ crumb.name }}
          </button>
        </template>
      </div>

      <!-- Body -->
      <div class="flex-1 overflow-auto">
        <!-- Loading -->
        <div v-if="loading" class="flex items-center justify-center py-12">
          <div class="w-6 h-6 border-2 border-blue-400 border-t-transparent rounded-full animate-spin"></div>
          <span class="ml-3 text-sm text-gray-500">Загрузка...</span>
        </div>

        <!-- Error -->
        <div v-else-if="error" class="p-6 text-center text-sm text-red-600">
          {{ error }}
        </div>

        <!-- Empty -->
        <div v-else-if="items.length === 0" class="p-6 text-center text-sm text-gray-500">
          Нет данных на этом уровне
        </div>

        <!-- Items list -->
        <div v-else class="divide-y divide-gray-100">
          <div
            v-for="item in items"
            :key="item.code"
            class="px-6 py-3 flex items-center gap-3 hover:bg-gray-50 transition-colors"
            :class="{ 'opacity-50': isProhibited(item) }"
          >
            <!-- Chevron or leaf indicator -->
            <div class="w-5 flex-shrink-0 text-center">
              <span v-if="item.has_children" class="text-gray-400 text-xs">&#9654;</span>
              <span v-else class="text-gray-300 text-xs">&#9679;</span>
            </div>

            <!-- Code & name (clickable area for navigation) -->
            <div
              class="flex-1 min-w-0 cursor-pointer"
              @click="item.has_children ? navigateTo(item) : null"
            >
              <div class="flex items-center gap-2">
                <span class="font-mono text-sm text-blue-600 whitespace-nowrap font-medium">{{ formatCode(item.code) }}</span>
                <span
                  class="text-[10px] px-1.5 py-0.5 rounded-full whitespace-nowrap"
                  :class="levelColor(item.level)"
                >{{ levelLabel(item.level) }}</span>
                <span v-if="isProhibited(item)" class="text-[10px] px-1.5 py-0.5 rounded-full bg-red-100 text-red-700 whitespace-nowrap">
                  ЗАПРЕЩЕНО
                </span>
              </div>
              <div class="text-sm text-gray-600 mt-0.5 truncate">{{ item.name }}</div>
              <div v-if="item.unit" class="text-[10px] text-gray-400 mt-0.5">{{ item.unit }}</div>
            </div>

            <!-- Action buttons -->
            <div class="flex-shrink-0 flex items-center gap-1">
              <button
                v-if="item.has_children"
                @click="navigateTo(item)"
                class="px-3 py-1.5 text-xs text-blue-600 hover:bg-blue-50 rounded-lg cursor-pointer transition-colors"
              >
                Открыть
              </button>
              <button
                v-if="!isProhibited(item)"
                @click="selectCode(item)"
                class="px-3 py-1.5 text-xs bg-blue-600 text-white hover:bg-blue-700 rounded-lg cursor-pointer transition-colors"
              >
                Выбрать
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Footer info -->
      <div class="px-6 py-3 border-t border-gray-200 text-xs text-gray-400">
        {{ items.length }} элементов на этом уровне
      </div>
    </div>
  </div>
</template>
