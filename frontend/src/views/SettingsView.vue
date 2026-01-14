<script setup lang="ts">
import { ref } from 'vue'
import TabView from 'primevue/tabview'
import TabPanel from 'primevue/tabpanel'

import ProfileManager from '@/components/settings/ProfileManager.vue'
import CardsManager from '@/components/settings/CardsManager.vue'
import TagsManager from '@/components/settings/TagsManager.vue'
import RulesManager from '@/components/settings/RulesManager.vue'

const activeTab = ref(0)
</script>

<template>
  <div class="settings-view">
    <div class="mb-8">
      <h1 class="text-3xl font-bold text-gray-900 mb-2">Settings</h1>
      <p class="text-gray-500">Manage your profile, preferences, and automation rules.</p>
    </div>

    <div class="card bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm">
      <TabView v-model:activeIndex="activeTab" class="p-4">
        <TabPanel header="Profile & Security" value="0">
          <div class="py-4">
            <ProfileManager />
          </div>
        </TabPanel>
        
        <TabPanel header="Credit Cards" value="1">
          <div class="py-4">
            <div class="mb-6">
               <h3 class="text-lg font-semibold text-gray-800 mb-1">Card Configuration</h3>
               <p class="text-sm text-gray-500">Set credit limits and billing cycle dates for accurate reporting.</p>
            </div>
            <CardsManager />
          </div>
        </TabPanel>
        
        <TabPanel header="Tags" value="2">
           <div class="py-4">
              <div class="mb-6">
                 <h3 class="text-lg font-semibold text-gray-800 mb-1">Custom Tags</h3>
                 <p class="text-sm text-gray-500">Create and manage color-coded tags for categorizing transactions.</p>
              </div>
              <TagsManager />
           </div>
        </TabPanel>
        
        <TabPanel header="Automation Rules" value="3">
           <div class="py-4">
              <div class="mb-6">
                 <h3 class="text-lg font-semibold text-gray-800 mb-1">Transaction Rules</h3>
                 <p class="text-sm text-gray-500">Automatically assign tags to transactions based on criteria.</p>
              </div>
              <RulesManager />
           </div>
        </TabPanel>
      </TabView>
    </div>
  </div>
</template>

<style scoped>
.settings-view {
  padding: 32px;
  max-width: 1200px;
  margin: 0 auto;
}

:deep(.p-tabview-nav) {
  border-bottom: 1px solid #e5e7eb;
}

:deep(.p-tabview-nav li .p-tabview-nav-link) {
  border: none;
  border-bottom: 2px solid transparent;
  color: #6b7280;
  font-weight: 500;
  padding: 1rem 1.5rem;
  transition: all 0.2s;
}

:deep(.p-tabview-nav li.p-highlight .p-tabview-nav-link) {
  border-bottom-color: var(--primary-color, #3b82f6);
  color: var(--primary-color, #3b82f6);
}

:deep(.p-tabview-nav-content) {
  margin-bottom: 0;
}
</style>
