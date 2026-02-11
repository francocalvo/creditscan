<script setup lang="ts">
import { ref } from 'vue'
import TabNavigation from '@/components/dashboard/TabNavigation.vue'
import ProfileTab from '@/components/settings/ProfileTab.vue'
import TagsTab from '@/components/settings/TagsTab.vue'
import RulesTab from '@/components/settings/RulesTab.vue'
import NotificationsTab from '@/components/settings/NotificationsTab.vue'

const activeTab = ref<'profile' | 'tags' | 'rules' | 'notifications'>('profile')

const tabs = [
  { id: 'profile', label: 'Profile' },
  { id: 'tags', label: 'Tags' },
  { id: 'rules', label: 'Rules' },
  { id: 'notifications', label: 'Notifications' },
]
</script>

<template>
  <div class="settings-view">
    <!-- Section Header -->
    <div class="section-header">
      <div class="header-left">
        <h1 class="section-title">Settings</h1>
        <p class="section-subtitle">Manage your profile, tags, automation rules, and notifications</p>
      </div>
    </div>

    <!-- Tab Navigation -->
    <TabNavigation :tabs="tabs" :activeTab="activeTab" @update:activeTab="activeTab = $event as 'profile' | 'tags' | 'rules' | 'notifications'" />

    <!-- Profile Tab -->
    <ProfileTab v-if="activeTab === 'profile'" />

    <!-- Tags Tab -->
    <TagsTab v-else-if="activeTab === 'tags'" />

    <!-- Rules Tab -->
    <RulesTab v-else-if="activeTab === 'rules'" />

    <!-- Notifications Tab -->
    <NotificationsTab v-else-if="activeTab === 'notifications'" />
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
  color: var(--text-color);
  margin: 0 0 8px 0;
}

.section-subtitle {
  font-size: 15px;
  color: var(--text-color-secondary);
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
