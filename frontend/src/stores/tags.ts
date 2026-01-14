import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface Tag {
  id: string
  name: string
  color: string
}

export const useTagsStore = defineStore('tags', () => {
  // Initialize with some default tags if empty
  const defaultTags: Tag[] = [
    { id: '1', name: 'Coffee', color: '#8B4513' },
    { id: '2', name: 'Groceries', color: '#228B22' },
    { id: '3', name: 'Utilities', color: '#4682B4' },
    { id: '4', name: 'Dining', color: '#FF6347' },
    { id: '5', name: 'Subscription', color: '#9370DB' }
  ]

  const savedTags = localStorage.getItem('creditscan_tags')
  const tags = ref<Tag[]>(savedTags ? JSON.parse(savedTags) : defaultTags)

  const saveToStorage = () => {
    localStorage.setItem('creditscan_tags', JSON.stringify(tags.value))
  }

  const addTag = (tag: Omit<Tag, 'id'>) => {
    tags.value.push({
      id: crypto.randomUUID(),
      ...tag
    })
    saveToStorage()
  }

  const updateTag = (id: string, updates: Partial<Tag>) => {
    const index = tags.value.findIndex(t => t.id === id)
    if (index !== -1) {
      tags.value[index] = { ...tags.value[index], ...updates }
      saveToStorage()
    }
  }

  const deleteTag = (id: string) => {
    tags.value = tags.value.filter(t => t.id !== id)
    saveToStorage()
  }

  return {
    tags,
    addTag,
    updateTag,
    deleteTag
  }
})
