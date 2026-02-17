<script setup lang="ts">
import { ref } from 'vue'
import { ALLOWED_TRANSITIONS, STATUS_LABELS } from '../types'

const props = defineProps<{ currentStatus: string }>()
const emit = defineEmits<{
  confirm: [status: string, comment: string]
  cancel: []
}>()

const nextStatuses = ALLOWED_TRANSITIONS[props.currentStatus] || []
const selectedStatus = ref(nextStatuses[0] || '')
const comment = ref('')

function confirm() {
  if (selectedStatus.value) {
    emit('confirm', selectedStatus.value, comment.value)
  }
}
</script>

<template>
  <div class="fixed inset-0 bg-black/40 flex items-center justify-center z-50" @click.self="emit('cancel')">
    <div class="bg-white rounded-xl shadow-xl w-full max-w-md p-6">
      <h3 class="text-lg font-semibold mb-4">Смена статуса</h3>

      <div class="mb-4">
        <label class="block text-sm font-medium text-gray-700 mb-1">Новый статус</label>
        <select v-model="selectedStatus" class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm">
          <option v-for="s in nextStatuses" :key="s" :value="s">
            {{ STATUS_LABELS[s] || s }}
          </option>
        </select>
      </div>

      <div class="mb-4">
        <label class="block text-sm font-medium text-gray-700 mb-1">Комментарий</label>
        <textarea v-model="comment" rows="3" class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" placeholder="Необязательно" />
      </div>

      <div class="flex justify-end gap-3">
        <button @click="emit('cancel')" class="px-4 py-2 text-sm text-gray-600 hover:text-gray-800 cursor-pointer">Отмена</button>
        <button @click="confirm" class="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 cursor-pointer">Применить</button>
      </div>
    </div>
  </div>
</template>
