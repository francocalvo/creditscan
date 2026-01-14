<script setup lang="ts">
import { ref } from 'vue'
import { useTagsStore } from '@/stores/tags'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import ColorPicker from 'primevue/colorpicker'
import Tag from 'primevue/tag'

const tagsStore = useTagsStore()
const showDialog = ref(false)
const isEditing = ref(false)
const form = ref({ id: '', name: '', color: '3B82F6' }) // Default blue without #

const openNew = () => {
  form.value = { id: '', name: '', color: '3B82F6' }
  isEditing.value = false
  showDialog.value = true
}

const editTag = (tag: any) => {
  form.value = { ...tag, color: tag.color.replace('#', '') }
  isEditing.value = true
  showDialog.value = true
}

const saveTag = () => {
  if (isEditing.value) {
    tagsStore.updateTag(form.value.id, { 
      name: form.value.name, 
      color: '#' + form.value.color 
    })
  } else {
    tagsStore.addTag({ 
      name: form.value.name, 
      color: '#' + form.value.color 
    })
  }
  showDialog.value = false
}

const confirmDelete = (tag: any) => {
  if (confirm(`Are you sure you want to delete tag "${tag.name}"?`)) {
    tagsStore.deleteTag(tag.id)
  }
}
</script>

<template>
  <div class="tags-manager">
    <div class="mb-4 flex justify-between items-center">
      <h3 class="text-lg font-semibold text-gray-700">Managed Tags</h3>
      <Button label="New Tag" icon="pi pi-plus" size="small" @click="openNew" />
    </div>

    <div class="card bg-white border border-gray-200 rounded-xl overflow-hidden">
      <DataTable :value="tagsStore.tags" stripedRows class="text-sm">
        <Column header="Preview" style="width: 20%">
          <template #body="slotProps">
            <Tag :value="slotProps.data.name" :style="{ backgroundColor: slotProps.data.color, color: 'white' }" />
          </template>
        </Column>
        <Column field="name" header="Name" sortable></Column>
        <Column header="Color Code">
           <template #body="slotProps">
             <div class="flex items-center gap-2">
               <div class="w-4 h-4 rounded-full border border-gray-200" :style="{ backgroundColor: slotProps.data.color }"></div>
               <span class="font-mono text-gray-500">{{ slotProps.data.color }}</span>
             </div>
           </template>
        </Column>
        <Column header="Actions" alignFrozen="right" frozen>
          <template #body="slotProps">
            <div class="flex gap-2">
              <Button icon="pi pi-pencil" text rounded size="small" @click="editTag(slotProps.data)" />
              <Button icon="pi pi-trash" text rounded severity="danger" size="small" @click="confirmDelete(slotProps.data)" />
            </div>
          </template>
        </Column>
      </DataTable>
    </div>

    <Dialog v-model:visible="showDialog" :header="isEditing ? 'Edit Tag' : 'New Tag'" modal class="p-fluid w-full max-w-sm">
      <div class="field mb-4">
        <label for="name" class="block mb-2 text-sm font-medium">Tag Name</label>
        <InputText id="name" v-model="form.name" required autofocus />
      </div>
      <div class="field mb-6">
        <label class="block mb-2 text-sm font-medium">Color</label>
        <div class="flex items-center gap-4">
          <ColorPicker v-model="form.color" />
          <span class="text-gray-500 font-mono">#{{ form.color }}</span>
        </div>
      </div>
      <template #footer>
        <Button label="Cancel" icon="pi pi-times" text @click="showDialog = false" />
        <Button label="Save" icon="pi pi-check" @click="saveTag" autofocus />
      </template>
    </Dialog>
  </div>
</template>
