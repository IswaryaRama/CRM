<template>
  <div v-if="brand?.logo" class="h-full w-full flex items-center justify-center">
    <img
      v-if="isCollapsed && brand.favicon"
      :src="brand.favicon"
      class="size-8 shrink-0 rounded object-contain object-center"
    />
    <img
      v-else
      :src="brand.logo"
      class="h-full w-full object-contain object-center"
      :class="isCollapsed ? 'max-h-8 max-w-8' : ''"
    />
  </div>
  <CRMLogo v-else :isCollapsed="isCollapsed" class="h-full w-auto object-contain object-center shrink-0" />
</template>

<script setup>
import CRMLogo from '@/components/Icons/CRMLogo.vue'

defineProps({
  isCollapsed: { type: Boolean, default: false },
})

const brand = defineModel({ type: Object, default: () => ({}) })
</script>
