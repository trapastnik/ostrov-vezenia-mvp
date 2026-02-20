<script setup lang="ts">
import { ref, watch } from 'vue'

export interface ApiDebug {
  method: string
  url: string
  requestBody: unknown
  responseStatus: number | null
  responseBody: unknown
  durationMs: number
  isError: boolean
}

const props = defineProps<{
  debug: ApiDebug | null
}>()

const open = ref(false)
const copied = ref(false)

// Закрываем при новом запросе, открываем после получения ответа
watch(() => props.debug, (val) => {
  open.value = !!val
})

function statusClass(status: number | null): string {
  if (!status) return 'text-gray-400'
  if (status >= 200 && status < 300) return 'text-green-600'
  return 'text-red-600'
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

function curlCommand(): string {
  if (!props.debug) return ''
  const { method, url, requestBody } = props.debug
  const baseUrl = window.location.origin
  const fullUrl = `${baseUrl}${url}`
  let cmd = `curl -s -X ${method} '${fullUrl}' \\\n  -H 'Content-Type: application/json' \\\n  -H 'Authorization: Bearer <TOKEN>'`
  if (requestBody) {
    cmd += ` \\\n  -d '${JSON.stringify(requestBody)}'`
  }
  return cmd
}

async function copyToClipboard() {
  const text = `${curlCommand()}\n\n# Response (${statusText(props.debug?.responseStatus ?? null)}):\n${fmt(props.debug?.responseBody)}`
  await navigator.clipboard.writeText(text)
  copied.value = true
  setTimeout(() => { copied.value = false }, 2000)
}
</script>

<template>
  <div v-if="debug" class="mt-4 border border-gray-200 rounded-lg overflow-hidden text-xs font-mono">
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
          {{ copied ? '✓ Скопировано' : 'Копировать curl' }}
        </button>
      </div>
    </div>

    <!-- Body -->
    <div v-if="open" class="bg-gray-950 text-gray-300">
      <!-- REQUEST -->
      <div class="px-4 py-3 border-b border-gray-800">
        <div class="text-gray-500 text-xs uppercase tracking-widest mb-2">Request</div>
        <div class="text-blue-400 mb-1">{{ debug.method }} <span class="text-gray-300">{{ debug.url }}</span></div>
        <div class="text-gray-500 mb-2">Content-Type: application/json</div>
        <pre v-if="debug.requestBody" class="text-green-300 whitespace-pre-wrap break-all leading-relaxed">{{ fmt(debug.requestBody) }}</pre>
        <span v-else class="text-gray-600 italic">— нет тела запроса —</span>
      </div>

      <!-- RESPONSE -->
      <div class="px-4 py-3">
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
    </div>
  </div>
</template>
