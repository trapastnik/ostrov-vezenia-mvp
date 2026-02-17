<script setup lang="ts">
import { STATUS_LABELS, STATUS_COLORS } from '../types'

const props = defineProps<{ status: string }>()
</script>

<template>
  <span
    class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
    :class="STATUS_COLORS[props.status] || 'bg-gray-100 text-gray-800'"
  >
    {{ STATUS_LABELS[props.status] || props.status }}
  </span>
</template>
