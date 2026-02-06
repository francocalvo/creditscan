<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useTags, type Tag } from '@/composables/useTags'
import { useToast } from 'primevue/usetoast'
import Button from 'primevue/button'
import TagFormModal from '@/components/settings/TagFormModal.vue'
import DeleteConfirmDialog from '@/components/settings/DeleteConfirmDialog.vue'

const toast = useToast()
const { tags, isLoading, fetchTags, deleteTag, getTagUsageCount } = useTags()

const showCreateModal = ref(false)
const editingTag = ref<Tag | null>(null)
const deletingTag = ref<Tag | null>(null)

// Delete dialog state
const showDeleteDialog = ref(false)
const deleteWarning = ref<string | undefined>(undefined)
const isDeleting = ref(false)

onMounted(() => {
  fetchTags()
})

/**
 * Computed visibility for the tag form modal (create or edit mode)
 */
const isFormModalVisible = computed({
  get: () => showCreateModal.value || editingTag.value !== null,
  set: (value: boolean) => {
    if (!value) {
      showCreateModal.value = false
      editingTag.value = null
    }
  },
})

/**
 * Handle create tag button
 */
function handleCreate(): void {
  showCreateModal.value = true
}

/**
 * Handle edit tag button
 */
function handleEdit(tag: Tag): void {
  editingTag.value = tag
}

/**
 * Handle delete tag button - shows confirmation dialog with usage info
 */
async function handleDelete(tag: Tag): Promise<void> {
  deletingTag.value = tag

  // Fetch usage count to show warning
  const usage = await getTagUsageCount(tag.tag_id)

  if (usage.rules > 0 || usage.transactions > 0) {
    const parts: string[] = []
    if (usage.rules > 0) {
      parts.push(`${usage.rules} rule${usage.rules > 1 ? 's' : ''}`)
    }
    if (usage.transactions > 0) {
      parts.push(`${usage.transactions} transaction${usage.transactions > 1 ? 's' : ''}`)
    }
    deleteWarning.value = `This tag is used by ${parts.join(' and ')}. Deleting it will remove these associations.`
  } else {
    deleteWarning.value = undefined
  }

  showDeleteDialog.value = true
}

/**
 * Handle delete confirmation
 */
async function confirmDelete(): Promise<void> {
  if (!deletingTag.value) return

  isDeleting.value = true

  try {
    await deleteTag(deletingTag.value.tag_id)

    toast.add({
      severity: 'success',
      summary: 'Tag Deleted',
      detail: `"${deletingTag.value.label}" has been deleted`,
      life: 3000,
    })

    showDeleteDialog.value = false
    deletingTag.value = null
    deleteWarning.value = undefined
  } catch (e) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: e instanceof Error ? e.message : 'Failed to delete tag',
      life: 5000,
    })
  } finally {
    isDeleting.value = false
  }
}

/**
 * Handle form modal saved event
 */
function handleFormSaved(): void {
  const wasEditing = editingTag.value !== null

  toast.add({
    severity: 'success',
    summary: wasEditing ? 'Tag Updated' : 'Tag Created',
    detail: wasEditing ? 'Tag has been updated' : 'Tag has been created',
    life: 3000,
  })
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

    <!-- Tag Form Modal (Create/Edit) -->
    <TagFormModal
      v-model:visible="isFormModalVisible"
      :tag="editingTag"
      @saved="handleFormSaved"
    />

    <!-- Delete Confirmation Dialog -->
    <DeleteConfirmDialog
      v-model:visible="showDeleteDialog"
      title="Delete Tag"
      :message="`Are you sure you want to delete the tag '${deletingTag?.label}'?`"
      :warningMessage="deleteWarning"
      :loading="isDeleting"
      @confirm="confirmDelete"
    />
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
  color: var(--text-color);
  margin: 0;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: var(--text-color-secondary);
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
  color: var(--surface-border);
  margin-bottom: 16px;
}

.empty-state h4 {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-color);
  margin: 0 0 8px 0;
}

.empty-state p {
  font-size: 14px;
  color: var(--text-color-secondary);
  margin: 0 0 24px 0;
  max-width: 300px;
}

.tags-table-container {
  background: var(--surface-card);
  border: 1px solid var(--surface-border);
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
  color: var(--text-color-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  background: var(--surface-ground);
  border-bottom: 1px solid var(--surface-border);
}

.tags-table td {
  padding: 12px 16px;
  font-size: 14px;
  color: var(--text-color);
  border-bottom: 1px solid var(--surface-border);
}

.tags-table tr:last-child td {
  border-bottom: none;
}

.tags-table tr:hover td {
  background: var(--surface-ground);
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
