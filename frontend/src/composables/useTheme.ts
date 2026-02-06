import { ref, computed, onMounted, onUnmounted } from 'vue'

const STORAGE_KEY = 'theme'
const DARK_CLASS = 'my-app-dark'

const isDark = ref(document.documentElement.classList.contains(DARK_CLASS))

function toggleTheme() {
  document.documentElement.classList.toggle(DARK_CLASS)
  isDark.value = document.documentElement.classList.contains(DARK_CLASS)
  localStorage.setItem(STORAGE_KEY, isDark.value ? 'dark' : 'light')
}

export function useTheme() {
  let observer: MutationObserver | null = null

  onMounted(() => {
    observer = new MutationObserver(() => {
      isDark.value = document.documentElement.classList.contains(DARK_CLASS)
    })
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['class'],
    })
  })

  onUnmounted(() => {
    observer?.disconnect()
  })

  const icon = computed(() => (isDark.value ? 'pi pi-sun' : 'pi pi-moon'))

  return { isDark, toggleTheme, icon }
}
