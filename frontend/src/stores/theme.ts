import { ref, watch } from 'vue'
import { defineStore } from 'pinia'

export const useThemeStore = defineStore('theme', () => {
    const isDark = ref(false)

    // Initialize theme from localStorage or system preference
    function initTheme() {
        const savedTheme = localStorage.getItem('theme')

        if (savedTheme) {
            isDark.value = savedTheme === 'dark'
        } else {
            isDark.value = window.matchMedia('(prefers-color-scheme: dark)').matches
        }

        applyTheme()
    }

    // Toggle between light and dark
    function toggleTheme() {
        isDark.value = !isDark.value
        applyTheme()
    }

    // Apply theme to DOM and save persistence
    function applyTheme() {
        const root = document.documentElement
        if (isDark.value) {
            root.classList.add('dark')
            localStorage.setItem('theme', 'dark')
        } else {
            root.classList.remove('dark')
            localStorage.setItem('theme', 'light')
        }
    }

    return {
        isDark,
        initTheme,
        toggleTheme
    }
})
