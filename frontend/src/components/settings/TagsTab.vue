<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useTags, type Tag } from '@/composables/useTags'
import Button from 'primevue/button'

const { tags, isLoading, fetchTags } = useTags()

const showCreateModal = ref(false)
const editingTag = ref<Tag | null>(null)
const deletingTag = ref<Tag | null>(null)

onMounted(() => {
  fetchTags()
})

const handleCreate = () => {
  showCreateModal.value = true
}

const handleEdit = (tag: Tag) => {
  editingTag.value = tag
}

const handleDelete = (tag: Tag) => {
  deletingTag.value = tag
}
</script>

<template>
  <div class="tags-tab">
    <!-- Header -->
    <div class="tab-header">
      <h3 class="tab-title">Tags</h3>
      <Button
        label="Create Tag"
        icon="pi pi-plus"
        size="small"
        @click="handleCreate"
      />
    </div>

    <!-- Loading State -->
    <div v-if="isLoading" class="loading-state">
      <i class="pi pi-spin pi-spinner loading-icon"></i>
      <p>Loading tags...</p>
    </div>

    <!-- Empty State -->
    <div v-else-if="tags.length === 0" class="empty-state">
      <i class="pi pi-tag empty-icon"></i>
      <h4>No tags yet</h4>
      <p>Tags help you categorize and organize your transactions.</p>
      <Button
        label="Create your first tag"
        icon="pi pi-plus"
        @click="handleCreate"
      />
    </div>

    <!-- Tags Table -->
    <div v-else class="tags-table-container">
      <table class="tags-table">
        <thead>
          <tr>
            <th class="col-color">Color</th>
            <th class="col-label">Label</th>
            <th class="col-actions">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="tag in tags" :key="tag.tag_id">
            <td class="col-color">
              <span
                class="color-dot"
                :style="{ backgroundColor: tag.color || '#6B7280' }"
              ></span>
            </td>
            <td class="col-label">{{ tag.label }}</td>
            <td class="col-actions">
              <Button
                icon="pi pi-pencil"
                severity="secondary"
                text
                rounded
                size="small"
                @click="handleEdit(tag)"
                aria-label="Edit tag"
              />
              <Button
                icon="pi pi-trash"
                severity="danger"
                text
                rounded
                size="small"
                @click="handleDelete(tag)"
                aria-label="Delete tag"
              />
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.tags-tab {
  padding: 24px 0;
}

.tab-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.tab-title {
  font-size: 18px;
  font-weight: 600;
  color: #111827;
  margin: 0;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: #6b7280;
}

.loading-icon {
  font-size: 32px;
  margin-bottom: 16px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
}

.empty-icon {
  font-size: 48px;
  color: #d1d5db;
  margin-bottom: 16px;
}

.empty-state h4 {
  font-size: 18px;
  font-weight: 600;
  color: #111827;
  margin: 0 0 8px 0;
}

.empty-state p {
  font-size: 14px;
  color: #6b7280;
  margin: 0 0 24px 0;
  max-width: 300px;
}

.tags-table-container {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  overflow: hidden;
}

.tags-table {
  width: 100%;
  border-collapse: collapse;
}

.tags-table th {
  text-align: left;
  padding: 12px 16px;
  font-size: 12px;
  font-weight: 600;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  background: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
}

.tags-table td {
  padding: 12px 16px;
  font-size: 14px;
  color: #111827;
  border-bottom: 1px solid #e5e7eb;
}

.tags-table tr:last-child td {
  border-bottom: none;
}

.tags-table tr:hover td {
  background: #f9fafb;
}

.col-color {
  width: 60px;
}

.col-label {
  width: auto;
}

.col-actions {
  width: 100px;
  text-align: right;
}

.color-dot {
  display: inline-block;
  width: 12px;
  height: 12px;
  border-radius: 50%;
}
</style>
