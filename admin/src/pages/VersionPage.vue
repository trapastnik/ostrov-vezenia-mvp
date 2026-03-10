<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { fetchVersionInfo } from '../api/version'
import type { VersionInfo, ChangelogEntry } from '../api/version'

const info = ref<VersionInfo | null>(null)
const loading = ref(true)
const error = ref('')

const SECTION_ICONS: Record<string, string> = {
  'Добавлено': '+',
  'Изменено': '~',
  'Исправлено': '!',
  'Безопасность': '#',
  'Удалено': '-',
}

const SECTION_COLORS: Record<string, string> = {
  'Добавлено': 'text-green-700 bg-green-50 border-green-200',
  'Изменено': 'text-blue-700 bg-blue-50 border-blue-200',
  'Исправлено': 'text-orange-700 bg-orange-50 border-orange-200',
  'Безопасность': 'text-purple-700 bg-purple-50 border-purple-200',
  'Удалено': 'text-red-700 bg-red-50 border-red-200',
}

const BADGE_COLORS: Record<string, string> = {
  'Добавлено': 'bg-green-100 text-green-700',
  'Изменено': 'bg-blue-100 text-blue-700',
  'Исправлено': 'bg-orange-100 text-orange-700',
  'Безопасность': 'bg-purple-100 text-purple-700',
  'Удалено': 'bg-red-100 text-red-700',
}

function totalChanges(entry: ChangelogEntry): number {
  return entry.sections.reduce((sum, s) => sum + s.items.length, 0)
}

onMounted(async () => {
  try {
    info.value = await fetchVersionInfo()
  } catch (e: any) {
    error.value = e.response?.data?.detail || 'Ошибка загрузки'
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div>
    <div class="flex items-center gap-4 mb-6">
      <h2 class="text-2xl font-bold text-gray-800">История версий</h2>
      <span
        v-if="info"
        class="px-3 py-1 rounded-full text-sm font-mono font-semibold bg-blue-100 text-blue-700"
      >
        v{{ info.current_version }}
      </span>
    </div>

    <div v-if="loading" class="text-gray-500">Загрузка...</div>
    <div v-else-if="error" class="text-red-600">{{ error }}</div>

    <div v-else-if="info" class="space-y-8">
      <div
        v-for="(entry, idx) in info.changelog"
        :key="entry.version"
        class="bg-white rounded-xl border border-gray-200 overflow-hidden"
      >
        <!-- Version header -->
        <div
          class="px-6 py-4 border-b border-gray-100 flex items-center gap-4"
          :class="idx === 0 ? 'bg-blue-50/50' : 'bg-gray-50/50'"
        >
          <div class="flex items-center gap-3">
            <span class="text-lg font-bold font-mono text-gray-800">v{{ entry.version }}</span>
            <span
              v-if="idx === 0"
              class="px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-700"
            >
              Текущая
            </span>
          </div>
          <span class="text-sm text-gray-500">{{ entry.date }}</span>
          <span class="text-xs text-gray-400 ml-auto">{{ totalChanges(entry) }} изменений</span>
        </div>

        <!-- Sections -->
        <div class="px-6 py-4 space-y-5">
          <div v-for="section in entry.sections" :key="section.title">
            <div class="flex items-center gap-2 mb-2">
              <span
                class="w-5 h-5 rounded text-center text-xs font-bold leading-5"
                :class="BADGE_COLORS[section.title] || 'bg-gray-100 text-gray-600'"
              >
                {{ SECTION_ICONS[section.title] || '?' }}
              </span>
              <h4
                class="text-sm font-semibold"
                :class="(SECTION_COLORS[section.title] || 'text-gray-700').split(' ')[0]"
              >
                {{ section.title }}
              </h4>
              <span class="text-xs text-gray-400">({{ section.items.length }})</span>
            </div>
            <ul class="space-y-1.5 ml-7">
              <li
                v-for="(item, i) in section.items"
                :key="i"
                class="text-sm text-gray-700 leading-relaxed"
              >
                <span class="text-gray-300 mr-1.5">—</span>
                {{ item }}
              </li>
            </ul>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div class="text-center text-xs text-gray-400 py-4">
        Остров Везения &copy; 2026
      </div>
    </div>
  </div>
</template>
