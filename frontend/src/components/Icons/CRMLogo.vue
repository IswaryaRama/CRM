<script setup>
const logoImg = '/assets/crm/frontend/logo.png?v=2'
const faviconImg = '/assets/crm/frontend/favicon.png?v=2'

defineProps({
  isCollapsed: { type: Boolean, default: false }
})
</script>

<template>
  <img :src="isCollapsed ? faviconImg : logoImg" alt="Logo" />
</template>
