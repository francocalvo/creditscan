<script setup lang="ts">
import { RouterView, useRoute } from 'vue-router'
import Button from 'primevue/button'
import { computed } from 'vue'
import { useTheme } from '@/composables/useTheme'

const { toggleTheme, icon } = useTheme()

const route = useRoute()
const isAuthPage = computed(() => {
  return route.path.startsWith('/auth')
})
</script>

<template>
  <div class="app-container" :class="{ 'auth-page': isAuthPage }">
    <div v-if="isAuthPage" class="theme-toggle">
      <Button :icon="icon" @click="toggleTheme()" class="p-button-rounded p-button-text" aria-label="Toggle Dark Mode" />
    </div>
      <RouterView />
  </div>
</template>

<style scoped>
.app-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  position: relative;
}

.theme-toggle {
  position: fixed;
  top: 1rem;
  right: 1rem;
  z-index: 1000;
}
</style>
