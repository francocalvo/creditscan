<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useNotifications } from '@/composables/useNotifications'
import { useToast } from 'primevue/usetoast'
import Button from 'primevue/button'
import InputSwitch from 'primevue/inputswitch'
import InputText from 'primevue/inputtext'
import Message from 'primevue/message'

const toast = useToast()
const { isEnabled, ntfyTopicUrl, isLoading, error, fetchSettings, toggleNotifications, testNotification } =
  useNotifications()

const isTesting = ref(false)

onMounted(() => {
  fetchSettings()
})

const handleToggle = async (value: boolean) => {
  await toggleNotifications(value)
  toast.add({
    severity: value ? 'success' : 'info',
    summary: value ? 'Notifications enabled' : 'Notifications disabled',
    life: 3000,
  })
}

const handleCopy = async () => {
  try {
    await navigator.clipboard.writeText(ntfyTopicUrl.value)
    toast.add({
      severity: 'success',
      summary: 'Copied to clipboard',
      life: 2000,
    })
  } catch {
    toast.add({
      severity: 'error',
      summary: 'Failed to copy',
      life: 3000,
    })
  }
}

const handleTest = async () => {
  isTesting.value = true
  try {
    const result = await testNotification()
    if (result) {
      toast.add({
        severity: result.notification_sent ? 'success' : 'info',
        summary: result.notification_sent
          ? 'Test notification sent'
          : `No statements due tomorrow (${result.statements_found} found)`,
        life: 4000,
      })
    } else {
      toast.add({
        severity: 'error',
        summary: 'Failed to trigger notification',
        life: 3000,
      })
    }
  } finally {
    isTesting.value = false
  }
}
</script>

<template>
  <div class="notifications-tab">
    <div class="notifications-card">
      <Message v-if="error" severity="error" :closable="true" @close="error = null">
        {{ error.message }}
      </Message>

      <h3 class="card-title">Push Notifications</h3>

      <div class="form-group toggle-group">
        <label class="form-label">Enable notifications</label>
        <InputSwitch
          :modelValue="isEnabled"
          @update:modelValue="handleToggle"
          :disabled="isLoading"
        />
      </div>

      <template v-if="isEnabled">
        <div class="form-group">
          <label class="form-label">Your Ntfy Topic URL</label>
          <div class="topic-url-row">
            <InputText :modelValue="ntfyTopicUrl" readonly class="topic-input" />
            <Button icon="pi pi-copy" severity="secondary" outlined @click="handleCopy" />
          </div>
        </div>

        <div class="form-group">
          <label class="form-label">Setup Instructions</label>
          <ol class="instructions">
            <li>Install the <strong>ntfy</strong> app on your phone</li>
            <li>Add server using the base URL from above (without the topic path)</li>
            <li>Subscribe to the topic shown above</li>
          </ol>
        </div>

        <div class="form-actions">
          <Button
            label="Test Notification"
            icon="pi pi-bell"
            @click="handleTest"
            :loading="isTesting"
            severity="secondary"
          />
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.notifications-tab {
  padding: 24px 0;
}

.notifications-card {
  background: var(--surface-card);
  border: 1px solid var(--surface-border);
  border-radius: 12px;
  padding: 24px;
  max-width: 600px;
}

.card-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-color);
  margin: 0 0 24px 0;
}

.form-group {
  margin-bottom: 20px;
}

.form-label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-color);
  margin-bottom: 6px;
}

.toggle-group {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.topic-url-row {
  display: flex;
  gap: 8px;
  align-items: center;
}

.topic-input {
  flex: 1;
}

.instructions {
  font-size: 14px;
  color: var(--text-color-secondary);
  padding-left: 20px;
  margin: 8px 0 0 0;
  line-height: 1.8;
}

.form-actions {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid var(--surface-border);
}
</style>
