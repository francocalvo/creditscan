<script setup lang="ts">
import { ref, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import InputText from 'primevue/inputtext'
import Password from 'primevue/password'
import Button from 'primevue/button'
import { useToast } from 'primevue/usetoast'

const authStore = useAuthStore()
const toast = useToast()

const userForm = ref({
  full_name: authStore.user?.full_name || '',
  email: authStore.user?.email || ''
})

const passwordForm = ref({
  current_password: '',
  new_password: '',
  confirm_password: ''
})

const isUpdatingProfile = ref(false)
const isUpdatingPassword = ref(false)

const canUpdateProfile = computed(() => {
  return userForm.value.full_name !== authStore.user?.full_name
  // Email usually harder to update without verification, but allowing request
})

const canUpdatePassword = computed(() => {
  return passwordForm.value.current_password && 
         passwordForm.value.new_password && 
         passwordForm.value.new_password === passwordForm.value.confirm_password
})

const handleUpdateProfile = async () => {
  if (!canUpdateProfile.value) return
  isUpdatingProfile.value = true
  try {
    await authStore.updateProfile({ 
        full_name: userForm.value.full_name
    })
    toast.add({ severity: 'success', summary: 'Success', detail: 'Profile updated successfully', life: 3000 })
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to update profile', life: 3000 })
  } finally {
    isUpdatingProfile.value = false
  }
}

const handleUpdatePassword = async () => {
  if (!canUpdatePassword.value) return
  isUpdatingPassword.value = true
  try {
    await authStore.changePassword(passwordForm.value.current_password, passwordForm.value.new_password)
    toast.add({ severity: 'success', summary: 'Success', detail: 'Password changed successfully', life: 3000 })
    passwordForm.value = { current_password: '', new_password: '', confirm_password: '' } // Reset
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to change password. Check current password.', life: 3000 })
  } finally {
    isUpdatingPassword.value = false
  }
}
</script>

<template>
  <div class="profile-manager max-w-2xl">
    <div class="mb-8 p-6 bg-white rounded-xl border border-gray-200 shadow-sm">
      <h3 class="text-xl font-semibold mb-6 text-gray-800">Personal Information</h3>
      
      <div class="space-y-4">
        <div class="flex flex-col gap-2">
          <label for="fullName" class="text-sm font-medium text-gray-700">Full Name</label>
          <InputText id="fullName" v-model="userForm.full_name" />
        </div>

        <div class="flex flex-col gap-2">
          <label for="email" class="text-sm font-medium text-gray-700">Email Address</label>
          <InputText id="email" v-model="userForm.email" disabled class="bg-gray-50" />
          <small class="text-gray-500">Email cannot be changed directly.</small>
        </div>

        <div class="pt-4">
          <Button 
            label="Save Changes" 
            :loading="isUpdatingProfile" 
            :disabled="!canUpdateProfile"
            @click="handleUpdateProfile"
          />
        </div>
      </div>
    </div>

    <div class="p-6 bg-white rounded-xl border border-gray-200 shadow-sm">
      <h3 class="text-xl font-semibold mb-6 text-gray-800">Security</h3>
      
      <div class="space-y-4">
        <div class="flex flex-col gap-2">
          <label for="currentPass" class="text-sm font-medium text-gray-700">Current Password</label>
          <Password id="currentPass" v-model="passwordForm.current_password" :feedback="false" toggleMask />
        </div>

        <div class="flex flex-col gap-2">
          <label for="newPass" class="text-sm font-medium text-gray-700">New Password</label>
          <Password id="newPass" v-model="passwordForm.new_password" toggleMask />
        </div>

        <div class="flex flex-col gap-2">
          <label for="confirmPass" class="text-sm font-medium text-gray-700">Confirm New Password</label>
          <Password id="confirmPass" v-model="passwordForm.confirm_password" :feedback="false" toggleMask />
        </div>

        <div class="pt-4">
          <Button 
            label="Change Password" 
            severity="warn"
            :loading="isUpdatingPassword" 
            :disabled="!canUpdatePassword"
            @click="handleUpdatePassword"
          />
        </div>
      </div>
    </div>
  </div>
</template>
