<script setup lang="ts">
import { ref, watch } from 'vue'

export interface PochtaLogEntry {
  method: string
  url: string
  headers: Record<string, string>
  request_body: unknown
  response_status: number
  response_body: unknown
  duration_ms: number
}

export interface ApiDebug {
  method: string
  url: string
  requestBody: unknown
  responseStatus: number | null
  responseBody: unknown
  durationMs: number
  isError: boolean
  pochtaLog?: PochtaLogEntry[]
}

const props = defineProps<{
  debug: ApiDebug | null
}>()

const open = ref(false)
const copied = ref(false)

watch(() => props.debug, (val) => {
  open.value = !!val
})

function statusClass(status: number | null): string {
  if (!status) return 'text-gray-400'
  if (status >= 200 && status < 300) return 'text-green-400'
  return 'text-red-400'
}

function statusText(status: number | null): string {
  if (!status) return '—'
  const texts: Record<number, string> = {
    200: '200 OK', 201: '201 Created', 400: '400 Bad Request',
    401: '401 Unauthorized', 403: '403 Forbidden', 404: '404 Not Found',
    502: '502 Bad Gateway', 500: '500 Internal Server Error',
  }
  return texts[status] ?? `${status}`
}

function fmt(val: unknown): string {
  try {
    return JSON.stringify(val, null, 2)
  } catch {
    return String(val)
  }
}

async function copyToClipboard() {
  if (!props.debug) return
  const { method, url, requestBody, responseBody, responseStatus, pochtaLog } = props.debug
  const baseUrl = window.location.origin
  let text = `# Наш backend\ncurl -s -X ${method} '${baseUrl}${url}' \\\n  -H 'Content-Type: application/json' \\\n  -H 'Authorization: Bearer <TOKEN>'`
  if (requestBody) text += ` \\\n  -d '${JSON.stringify(requestBody)}'`
  text += `\n\n# Response (${statusText(responseStatus)}):\n${fmt(responseBody)}`
  if (pochtaLog?.length) {
    pochtaLog.forEach((entry, i) => {
      text += `\n\n# Запрос к Почте России ${pochtaLog.length > 1 ? i + 1 : ''}\ncurl -s -X ${entry.method} '${entry.url}'`
      if (entry.request_body) text += ` \\\n  -d '${JSON.stringify(entry.request_body)}'`
      text += `\n\n# Ответ Почты (${statusText(entry.response_status)}):\n${fmt(entry.response_body)}`
    })
  }
  await navigator.clipboard.writeText(text)
  copied.value = true
  setTimeout(() => { copied.value = false }, 2000)
}
</script>

<template>
  <div v-if="debug" class="mt-4 border border-gray-700 rounded-lg overflow-hidden text-xs font-mono">

    <!-- Header -->
    <div
      class="flex items-center justify-between px-4 py-2 bg-gray-900 text-gray-300 cursor-pointer select-none"
      @click="open = !open"
    >
      <div class="flex items-center gap-3">
        <span class="text-gray-500">{{ open ? '▼' : '▶' }}</span>
        <span class="font-semibold text-gray-200">Детали запроса</span>
        <span class="px-1.5 py-0.5 rounded text-xs font-bold bg-blue-800 text-blue-200">{{ debug.method }}</span>
        <span class="text-gray-400 truncate max-w-xs">{{ debug.url }}</span>
      </div>
      <div class="flex items-center gap-3 shrink-0">
        <span :class="statusClass(debug.responseStatus)" class="font-bold">
          {{ statusText(debug.responseStatus) }}
        </span>
        <span class="text-gray-500">{{ debug.durationMs }}ms</span>
        <button
          @click.stop="copyToClipboard"
          class="px-2 py-0.5 rounded bg-gray-700 hover:bg-gray-600 text-gray-300 text-xs transition-colors"
        >
          {{ copied ? '✓ Скопировано' : 'Копировать' }}
        </button>
      </div>
    </div>

    <div v-if="open" class="bg-gray-950 text-gray-300">

      <!-- ── СЕКЦИЯ 1: Наш backend ── -->
      <div class="px-4 py-2 bg-gray-800 border-b border-gray-700">
        <span class="text-xs uppercase tracking-widest text-gray-400 font-semibold">Браузер → Наш backend</span>
      </div>

      <!-- Request -->
      <div class="px-4 py-3 border-b border-gray-800">
        <div class="text-gray-500 text-xs uppercase tracking-widest mb-2">Request</div>
        <div class="mb-1">
          <span class="text-blue-400">{{ debug.method }}</span>
          <span class="text-gray-300 ml-2">{{ debug.url }}</span>
        </div>
        <div class="text-gray-500 mb-2">Content-Type: application/json</div>
        <pre v-if="debug.requestBody" class="text-green-300 whitespace-pre-wrap break-all leading-relaxed">{{ fmt(debug.requestBody) }}</pre>
        <span v-else class="text-gray-600 italic">— нет тела —</span>
      </div>

      <!-- Response -->
      <div class="px-4 py-3 border-b border-gray-700">
        <div class="text-gray-500 text-xs uppercase tracking-widest mb-2">
          Response
          <span :class="statusClass(debug.responseStatus)" class="ml-2 font-bold normal-case tracking-normal">
            {{ statusText(debug.responseStatus) }}
          </span>
          <span class="text-gray-600 ml-2">{{ debug.durationMs }}ms</span>
        </div>
        <pre
          class="whitespace-pre-wrap break-all leading-relaxed"
          :class="debug.isError ? 'text-red-400' : 'text-yellow-200'"
        >{{ fmt(debug.responseBody) }}</pre>
      </div>

      <!-- ── СЕКЦИЯ 2: API Почты России ── -->
      <template v-if="debug.pochtaLog && debug.pochtaLog.length">
        <div class="px-4 py-2 bg-gray-800 border-b border-gray-700">
          <span class="text-xs uppercase tracking-widest text-orange-400 font-semibold">Наш backend → API Почты России</span>
        </div>

        <div
          v-for="(entry, i) in debug.pochtaLog"
          :key="i"
          :class="i < debug.pochtaLog.length - 1 ? 'border-b border-gray-800' : ''"
        >
          <!-- Лейбл если несколько запросов -->
          <div v-if="debug.pochtaLog.length > 1" class="px-4 pt-2 text-gray-500 text-xs">
            Запрос {{ i + 1 }} из {{ debug.pochtaLog.length }}
          </div>

          <!-- Request к Почте -->
          <div class="px-4 py-3 border-b border-gray-800">
            <div class="text-gray-500 text-xs uppercase tracking-widest mb-2">Request</div>
            <div class="mb-1">
              <span class="text-orange-400">{{ entry.method }}</span>
              <span class="text-gray-300 ml-2 break-all">{{ entry.url }}</span>
            </div>
            <template v-if="entry.headers && Object.keys(entry.headers).length">
              <div v-for="(val, key) in entry.headers" :key="key" class="text-gray-500">
                {{ key }}: {{ val }}
              </div>
            </template>
            <pre v-if="entry.request_body" class="mt-2 text-green-300 whitespace-pre-wrap break-all leading-relaxed">{{ fmt(entry.request_body) }}</pre>
            <span v-else class="text-gray-600 italic">— нет тела —</span>
          </div>

          <!-- Response от Почты -->
          <div class="px-4 py-3">
            <div class="text-gray-500 text-xs uppercase tracking-widest mb-2">
              Response
              <span :class="statusClass(entry.response_status)" class="ml-2 font-bold normal-case tracking-normal">
                {{ statusText(entry.response_status) }}
              </span>
              <span class="text-gray-600 ml-2">{{ entry.duration_ms }}ms</span>
            </div>
            <pre class="text-yellow-200 whitespace-pre-wrap break-all leading-relaxed">{{ fmt(entry.response_body) }}</pre>
          </div>
        </div>
      </template>

    </div>
  </div>
</template>
