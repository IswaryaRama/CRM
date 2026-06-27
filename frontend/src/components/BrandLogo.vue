<template>
  <div v-if="brand?.logo" class="h-full w-full flex items-center" :class="isCollapsed ? 'justify-center' : 'justify-start'">
    <img
      v-if="isCollapsed && brand.favicon"
      :src="brand.favicon"
      class="size-8 shrink-0 rounded object-contain object-center"
    />
    <img
      v-else
      :src="brand.logo"
      class="h-full w-full object-contain"
      :class="isCollapsed ? 'object-center max-h-8 max-w-8' : 'object-left'"
    />
  </div>
  <CRMLogo v-else :isCollapsed="isCollapsed" class="h-full w-auto object-contain shrink-0" :class="isCollapsed ? 'object-center' : 'object-left'" />
</template>

<script setup>
import CRMLogo from '@/components/Icons/CRMLogo.vue'

defineProps({
  isCollapsed: { type: Boolean, default: false },
})

const brand = defineModel({ type: Object, default: () => ({}) })
</script>
