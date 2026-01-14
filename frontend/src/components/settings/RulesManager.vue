<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRulesStore } from '@/stores/rules'
import { useTagsStore } from '@/stores/tags'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Dropdown from 'primevue/dropdown'
import InputSwitch from 'primevue/inputswitch'
import Tag from 'primevue/tag'

const rulesStore = useRulesStore()
const tagsStore = useTagsStore()
const showDialog = ref(false)
const isEditing = ref(false)

const form = ref({
  id: '',
  name: '',
  field: 'narration',
  operator: 'contains',
  value: '',
  assignTagId: '',
  isActive: true
})

// Options
const fieldOptions = [
  { label: 'Description/Narration', value: 'narration' },
  { label: 'Merchant/Payee', value: 'payee' },
  { label: 'Amount', value: 'amount' }
]

const operatorOptions = [
  { label: 'Contains', value: 'contains' },
  { label: 'Equals', value: 'equals' },
  { label: 'Starts With', value: 'starts_with' }, // For strings
  { label: 'Greater Than', value: 'greater_than' }, // For numbers
]

const openNew = () => {
  form.value = {
    id: '',
    name: '',
    field: 'narration',
    operator: 'contains',
    value: '',
    assignTagId: tagsStore.tags[0]?.id || '',
    isActive: true
  }
  isEditing.value = false
  showDialog.value = true
}

const editRule = (rule: any) => {
  form.value = { ...rule }
  isEditing.value = true
  showDialog.value = true
}

const saveRule = () => {
  if (isEditing.value) {
    rulesStore.updateRule(form.value.id, { ...form.value } as any)
  } else {
    rulesStore.addRule({ ...form.value } as any)
  }
  showDialog.value = false
}

const confirmDelete = (id: string) => {
  if (confirm('Delete this rule?')) {
    rulesStore.deleteRule(id)
  }
}

const getTagName = (id: string) => {
  return tagsStore.tags.find(t => t.id === id)?.name || 'Unknown'
}

const getTagColor = (id: string) => {
  return tagsStore.tags.find(t => t.id === id)?.color || '#ccc'
}
</script>

<template>
  <div class="rules-manager">
    <div class="mb-4 flex justify-between items-center">
      <h3 class="text-lg font-semibold text-gray-700">Automation Rules</h3>
      <Button label="New Rule" icon="pi pi-plus" size="small" @click="openNew" />
    </div>

    <div class="space-y-4">
      <div v-if="rulesStore.rules.length === 0" class="text-center p-8 text-gray-400 bg-gray-50 rounded-xl border border-dashed border-gray-300">
        No rules defined yet.
      </div>
      
      <div v-for="rule in rulesStore.rules" :key="rule.id" class="p-4 bg-white border border-gray-200 rounded-xl shadow-sm flex justify-between items-center">
        <div class="flex-1">
          <div class="flex items-center gap-3 mb-1">
             <h4 class="font-bold text-gray-800">{{ rule.name }}</h4>
             <Tag :value="rule.isActive ? 'Active' : 'Disabled'" :severity="rule.isActive ? 'success' : 'secondary'" rounded class="text-xs" />
          </div>
          <div class="text-sm text-gray-600 flex items-center flex-wrap gap-1">
            <span>If</span>
            <span class="font-medium bg-blue-50 text-blue-700 px-2 py-0.5 rounded">{{ rule.field }}</span>
            <span>{{ rule.operator }}</span>
            <span class="font-bold">"{{ rule.value }}"</span>
            <i class="pi pi-arrow-right text-xs mx-1"></i>
            <span>Assign</span>
            <Tag :value="getTagName(rule.assignTagId)" :style="{ backgroundColor: getTagColor(rule.assignTagId), color: 'white' }" />
          </div>
        </div>
        
        <div class="flex gap-2">
           <Button icon="pi pi-pencil" text rounded @click="editRule(rule)" />
           <Button icon="pi pi-trash" text rounded severity="danger" @click="confirmDelete(rule.id)" />
        </div>
      </div>
    </div>

    <Dialog v-model:visible="showDialog" :header="isEditing ? 'Edit Rule' : 'New Rule'" modal class="p-fluid w-full max-w-lg">
      <div class="field mb-4">
        <label class="block mb-2 text-sm font-medium">Rule Name</label>
        <InputText v-model="form.name" placeholder="e.g. Coffee Shops" />
      </div>

      <div class="grid grid-cols-2 gap-4 mb-4">
        <div class="field">
          <label class="block mb-2 text-sm font-medium">Field</label>
          <Dropdown v-model="form.field" :options="fieldOptions" optionLabel="label" optionValue="value" />
        </div>
        <div class="field">
           <label class="block mb-2 text-sm font-medium">Operator</label>
           <Dropdown v-model="form.operator" :options="operatorOptions" optionLabel="label" optionValue="value" />
        </div>
      </div>

      <div class="field mb-4">
        <label class="block mb-2 text-sm font-medium">Value to Match</label>
        <InputText v-model="form.value" placeholder="e.g. Starbucks" />
      </div>

      <div class="field mb-6">
        <label class="block mb-2 text-sm font-medium">Assign Tag</label>
        <Dropdown 
          v-model="form.assignTagId" 
          :options="tagsStore.tags" 
          optionLabel="name" 
          optionValue="id" 
          placeholder="Select a tag"
        >
          <template #option="slotProps">
            <div class="flex items-center gap-2">
               <div class="w-3 h-3 rounded-full" :style="{ backgroundColor: slotProps.option.color }"></div>
               {{ slotProps.option.name }}
            </div>
          </template>
        </Dropdown>
      </div>
      
      <div class="field mb-4 flex items-center gap-2">
        <InputSwitch v-model="form.isActive" />
        <label class="text-sm font-medium">Rule Active</label>
      </div>

      <template #footer>
        <Button label="Cancel" icon="pi pi-times" text @click="showDialog = false" />
        <Button label="Save Rule" icon="pi pi-check" @click="saveRule" autofocus />
      </template>
    </Dialog>
  </div>
</template>
