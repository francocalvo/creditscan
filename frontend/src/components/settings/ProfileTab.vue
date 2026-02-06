<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'

const authStore = useAuthStore()

const isEditing = ref(false)
const isSaving = ref(false)
const formData = ref({
  full_name: '',
})

onMounted(() => {
  if (authStore.user) {
    formData.value.full_name = authStore.user.full_name || ''
  }
})

const handleEdit = () => {
  isEditing.value = true
}

const handleCancel = () => {
  if (authStore.user) {
    formData.value.full_name = authStore.user.full_name || ''
  }
  isEditing.value = false
}

const handleSave = async () => {
  isSaving.value = true
  try {
    await authStore.updateProfile({
      full_name: formData.value.full_name || null,
    })
    isEditing.value = false
  } catch (e) {
    console.error('Error updating profile:', e)
  } finally {
    isSaving.value = false
  }
}
</script>

<template>
  <div class="profile-tab">
    <div class="profile-card">
      <h3 class="card-title">Account Information</h3>

      <div class="form-group">
        <label class="form-label">Email</label>
        <div class="field-value">{{ authStore.user?.email }}</div>
        <span class="field-hint">Email cannot be changed</span>
      </div>

      <div class="form-group">
        <label class="form-label">Full Name</label>
        <template v-if="isEditing">
          <InputText
            v-model="formData.full_name"
            class="form-input"
            placeholder="Enter your full name"
          />
        </template>
        <template v-else>
          <div class="field-value">{{ authStore.user?.full_name || 'Not set' }}</div>
        </template>
      </div>

      <div class="form-actions">
        <template v-if="isEditing">
          <Button
            label="Cancel"
            severity="secondary"
            outlined
            @click="handleCancel"
            :disabled="isSaving"
          />
          <Button
            label="Save"
            @click="handleSave"
            :loading="isSaving"
          />
        </template>
        <template v-else>
          <Button
            label="Edit"
            icon="pi pi-pencil"
            @click="handleEdit"
          />
        </template>
      </div>
    </div>
  </div>
</template>

<style scoped>
.profile-tab {
  padding: 24px 0;
}

.profile-card {
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

.field-value {
  font-size: 15px;
  color: var(--text-color);
  padding: 8px 0;
}

.field-hint {
  display: block;
  font-size: 12px;
  color: var(--text-color-secondary);
  margin-top: 4px;
}

.form-input {
  width: 100%;
}

.form-actions {
  display: flex;
  gap: 12px;
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid var(--surface-border);
}
</style>
