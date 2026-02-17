<script setup lang="ts">
const props = defineProps<{
  page: number
  pages: number
  total: number
}>()

const emit = defineEmits<{
  'update:page': [value: number]
}>()
</script>

<template>
  <div class="flex items-center justify-between mt-4" v-if="pages > 1">
    <span class="text-sm text-gray-500">Всего: {{ total }}</span>
    <div class="flex gap-1">
      <button
        @click="emit('update:page', page - 1)"
        :disabled="page <= 1"
        class="px-3 py-1 text-sm rounded border border-gray-300 disabled:opacity-40 hover:bg-gray-50 cursor-pointer disabled:cursor-default"
      >
        &larr;
      </button>
      <span class="px-3 py-1 text-sm">{{ page }} / {{ pages }}</span>
      <button
        @click="emit('update:page', page + 1)"
        :disabled="page >= pages"
        class="px-3 py-1 text-sm rounded border border-gray-300 disabled:opacity-40 hover:bg-gray-50 cursor-pointer disabled:cursor-default"
      >
        &rarr;
      </button>
    </div>
  </div>
</template>
