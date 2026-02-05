<script setup lang="ts">
import { ref } from 'vue'
import TabNavigation from '@/components/dashboard/TabNavigation.vue'

const activeTab = ref<'profile' | 'tags' | 'rules'>('profile')

const tabs = [
  { id: 'profile', label: 'Profile' },
  { id: 'tags', label: 'Tags' },
  { id: 'rules', label: 'Rules' },
]
</script>

<template>
  <div class="settings-view">
    <!-- Section Header -->
    <div class="section-header">
      <div class="header-left">
        <h1 class="section-title">Settings</h1>
        <p class="section-subtitle">Manage your profile, tags, and automation rules</p>
      </div>
    </div>

    <!-- Tab Navigation -->
    <TabNavigation :tabs="tabs" :activeTab="activeTab" @update:activeTab="activeTab = $event as 'profile' | 'tags' | 'rules'" />

    <!-- Profile Tab -->
    <div v-if="activeTab === 'profile'" class="placeholder-section">
      <div class="placeholder-content">
        <i class="pi pi-user placeholder-icon"></i>
        <h3>Profile</h3>
        <p>Manage your account information and preferences</p>
      </div>
    </div>

    <!-- Tags Tab -->
    <div v-else-if="activeTab === 'tags'" class="placeholder-section">
      <div class="placeholder-content">
        <i class="pi pi-tag placeholder-icon"></i>
        <h3>Tags</h3>
        <p>Create and manage tags for categorizing your transactions</p>
      </div>
    </div>

    <!-- Rules Tab -->
    <div v-else-if="activeTab === 'rules'" class="placeholder-section">
      <div class="placeholder-content">
        <i class="pi pi-list-check placeholder-icon"></i>
        <h3>Rules</h3>
        <p>Configure automation rules for automatic transaction tagging</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.settings-view {
  padding: 32px;
  max-width: 1400px;
  margin: 0 auto;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
}

.header-left {
  flex: 1;
}

.section-title {
  font-size: 28px;
  font-weight: 700;
  color: #111827;
  margin: 0 0 8px 0;
}

.section-subtitle {
  font-size: 15px;
  color: #6b7280;
  margin: 0;
}

.placeholder-section {
  padding: 80px 20px;
}

.placeholder-content {
  text-align: center;
  max-width: 400px;
  margin: 0 auto;
}

.placeholder-icon {
  font-size: 48px;
  display: block;
  margin-bottom: 24px;
  color: #d1d5db;
}

.placeholder-content h3 {
  font-size: 24px;
  font-weight: 700;
  color: #111827;
  margin: 0 0 12px 0;
}

.placeholder-content p {
  font-size: 15px;
  color: #6b7280;
  margin: 0;
}

/* Responsive */
@media (max-width: 1024px) {
  .settings-view {
    padding: 24px;
  }
}

@media (max-width: 768px) {
  .section-title {
    font-size: 24px;
  }
}
</style>
