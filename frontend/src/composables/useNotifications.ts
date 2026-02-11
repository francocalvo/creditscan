import { ref } from 'vue'
import { UsersService, NotificationsService } from '@/api'

function getNtfyBaseUrl(): string {
  return import.meta.env.VITE_NTFY_URL || 'https://ntfy.sh'
}

const ntfyPublicUrl = getNtfyBaseUrl()

export function useNotifications() {
  const isEnabled = ref(false)
  const ntfyTopic = ref<string | null>(null)
  const ntfyTopicUrl = ref('')
  const isLoading = ref(false)
  const error = ref<Error | null>(null)

  async function fetchSettings(): Promise<void> {
    isLoading.value = true
    error.value = null
    try {
      const user = await UsersService.usersGetCurrentUser()
      isEnabled.value = user.notifications_enabled ?? false
      ntfyTopic.value = user.ntfy_topic ?? null
      ntfyTopicUrl.value = ntfyTopic.value ? `${ntfyPublicUrl}/${ntfyTopic.value}` : ''
    } catch (e) {
      error.value = e instanceof Error ? e : new Error('Failed to fetch notification settings')
    } finally {
      isLoading.value = false
    }
  }

  async function toggleNotifications(enabled: boolean): Promise<void> {
    isLoading.value = true
    error.value = null
    try {
      const user = await UsersService.usersUpdateCurrentUser({
        requestBody: { notifications_enabled: enabled },
      })
      isEnabled.value = user.notifications_enabled ?? false
      ntfyTopic.value = user.ntfy_topic ?? null
      ntfyTopicUrl.value = ntfyTopic.value ? `${ntfyPublicUrl}/${ntfyTopic.value}` : ''
    } catch (e) {
      error.value = e instanceof Error ? e : new Error('Failed to update notification settings')
    } finally {
      isLoading.value = false
    }
  }

  async function testNotification(): Promise<{ statements_found: number; notification_sent: boolean } | null> {
    error.value = null
    try {
      return await NotificationsService.notificationsTriggerNotification()
    } catch (e) {
      error.value = e instanceof Error ? e : new Error('Failed to send test notification')
      return null
    }
  }

  return {
    isEnabled,
    ntfyTopic,
    ntfyTopicUrl,
    isLoading,
    error,
    fetchSettings,
    toggleNotifications,
    testNotification,
  }
}
