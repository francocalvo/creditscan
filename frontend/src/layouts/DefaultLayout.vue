<script setup lang="ts">
 import { ref, computed, onMounted, onUnmounted } from 'vue'
 import { useRouter } from 'vue-router'
 import { useAuthStore } from '@/stores/auth'
 import type { MenuItem } from 'primevue/menuitem'
 import Button from 'primevue/button'
 import Avatar from 'primevue/avatar'
 import Menu from 'primevue/menu'
 import Toast from 'primevue/toast'

 import logoLight from '@/assets/logo.svg'
 import logoDark from '@/assets/logo-dark.svg'
 import UploadStatementModal from '@/components/UploadStatementModal.vue'

// Default layout for authenticated users
const router = useRouter()
const authStore = useAuthStore()

// Dark mode detection
const isDarkMode = ref(document.documentElement.classList.contains('my-app-dark'))
const logoSrc = computed(() => (isDarkMode.value ? logoDark : logoLight))

const updateDarkMode = () => {
  isDarkMode.value = document.documentElement.classList.contains('my-app-dark')
}

onMounted(() => {
  // Create a MutationObserver to watch for class changes on the document element
  const observer = new MutationObserver(updateDarkMode)
  observer.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] })

  // Store observer for cleanup
  ;(window as { __darkModeObserver?: MutationObserver }).__darkModeObserver = observer
})

onUnmounted(() => {
  // Clean up observer
  const observer = (window as { __darkModeObserver?: MutationObserver }).__darkModeObserver
  if (observer) {
    observer.disconnect()
    delete (window as { __darkModeObserver?: MutationObserver }).__darkModeObserver
  }
})

// User menu toggle
const userMenu = ref()
const toggleUserMenu = (event: Event) => {
  userMenu.value.toggle(event)
}

// User menu items
const userMenuItems = ref<MenuItem[]>([
  {
    label: 'Settings',
    icon: 'pi pi-cog',
    command: () => {
      router.push('/settings')
    },
  },
  {
    separator: true,
  },
  {
    label: 'Logout',
    icon: 'pi pi-sign-out',
    command: () => {
      authStore.logout()
      router.push('/auth/login')
    },
  },
])

// User initials for avatar
const userInitials = computed(() => {
  if (!authStore.user?.full_name) return 'U'
  const names = authStore.user.full_name.split(' ')
  if (names.length >= 2) {
    return `${names[0][0]}${names[1][0]}`.toUpperCase()
  }
  return authStore.user.full_name[0].toUpperCase()
})

// Upload statement modal state
const showUploadModal = ref(false)

// Upload statement action - open modal instead of navigating
const handleUploadStatement = (event?: MouseEvent) => {
  event?.preventDefault()
  event?.stopPropagation()
  showUploadModal.value = true
}

// Handle successful upload - navigate to statement detail
const handleUploadComplete = (statementId: string) => {
  showUploadModal.value = false
  router.push(`/statements/${statementId}`)
}

// Navigate to statement from toast
const navigateToStatement = (statementId: string) => {
  router.push(`/statements/${statementId}`)
}

// Dark mode toggle
const toggleDarkMode = () => {
  document.documentElement.classList.toggle('my-app-dark')
}
</script>

<template>
  <div class="default-layout">
    <header class="header">
      <div class="header-content">
        <div class="logo">
          <router-link to="/" class="logo-link">
            <img :src="logoSrc" alt="FinDash Logo" class="logo-image" />
            <span class="logo-text">CreditScan</span>
          </router-link>
        </div>

        <div class="header-actions">
          <Button
            label="Upload Statement"
            icon="pi pi-upload"
            type="button"
            @click="handleUploadStatement"
            class="upload-button"
          />

          <Button
            icon="pi pi-moon"
            @click="toggleDarkMode"
            class="p-button-rounded p-button-text"
            aria-label="Toggle Dark Mode"
          />

          <div class="user-menu-container">
            <Avatar
              :label="userInitials"
              shape="circle"
              class="user-avatar"
              @click="toggleUserMenu"
            />
            <Menu ref="userMenu" :model="userMenuItems" popup />
          </div>
        </div>
      </div>
    </header>

    <main class="content">
      <router-view></router-view>
    </main>

    <!-- Custom toast for upload completion -->
    <Toast group="upload-complete" position="top-right">
      <template #message="slotProps">
        <div class="upload-toast">
          <div class="upload-toast__content">
            <i
              :class="
                slotProps.message.severity === 'success'
                  ? 'pi pi-check-circle'
                  : slotProps.message.severity === 'warn'
                    ? 'pi pi-exclamation-triangle'
                    : 'pi pi-times-circle'
              "
            ></i>
            <div>
              <div class="upload-toast__summary">
                {{ slotProps.message.summary }}
              </div>
              <div class="upload-toast__detail">
                {{ slotProps.message.detail }}
              </div>
            </div>
          </div>
          <Button
            v-if="slotProps.message.data?.statementId"
            label="View"
            size="small"
            @click="navigateToStatement(slotProps.message.data.statementId)"
          />
        </div>
      </template>
    </Toast>

    <!-- Upload Statement Modal -->
    <UploadStatementModal
      v-model:visible="showUploadModal"
      @upload-complete="handleUploadComplete"
    />
  </div>
</template>

<style scoped>
.default-layout {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background-color: var(--surface-ground);
}

.header {
  background-color: var(--surface-card);
  border-bottom: 1px solid var(--surface-border);
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 2rem;
  max-width: 100%;
}

.logo {
  display: flex;
  align-items: center;
}

.logo-link {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  text-decoration: none;
  transition: opacity 0.2s;
}

.logo-link:hover {
  opacity: 0.8;
}

.logo-image {
  height: 40px;
  width: auto;
}

.logo-text {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text-color);
  letter-spacing: -0.02em;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.upload-button {
  font-weight: 500;
}

.user-menu-container {
  position: relative;
}

.user-avatar {
  cursor: pointer;
  background-color: var(--primary-color);
  color: white;
  font-weight: 600;
  transition:
    transform 0.2s,
    opacity 0.2s;
}

.user-avatar:hover {
  transform: scale(1.05);
  opacity: 0.9;
}

.content {
  flex-grow: 1;
  padding: 2rem;
  max-width: 100%;
}

.upload-toast {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.upload-toast__content {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.upload-toast__summary {
  font-weight: 600;
}

.upload-toast__detail {
  font-size: 0.875rem;
  color: var(--text-color-secondary);
}

/* Responsive design */
@media (max-width: 768px) {
  .header-content {
    padding: 1rem;
  }

  .logo-text {
    font-size: 1.25rem;
  }

  .upload-button {
    padding: 0.5rem 1rem;
  }

  .upload-button :deep(.p-button-label) {
    display: none;
  }
}

@media (max-width: 480px) {
  .logo-text {
    font-size: 1rem;
  }

  .logo-image {
    height: 32px;
  }

  .header-actions {
    gap: 0.5rem;
  }
}
</style>
