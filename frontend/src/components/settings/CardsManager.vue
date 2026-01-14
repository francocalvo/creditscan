<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useCreditCards, getCardDisplayName } from '@/composables/useCreditCards'
import type { CreditCard } from '@/composables/useCreditCards'
import InputNumber from 'primevue/inputnumber'
import Dropdown from 'primevue/dropdown'
import Button from 'primevue/button'
import { useToast } from 'primevue/usetoast'

const { cards, fetchCards, isLoading } = useCreditCards()
const toast = useToast()

// Local storage model for extended card info since API doesn't support it yet
interface ExtendedCardInfo {
  id: string
  credit_limit: number
  closing_day: number
  due_day: number
}

const extendedInfo = ref<Record<string, ExtendedCardInfo>>({})
const editingId = ref<string | null>(null)
const editForm = ref<ExtendedCardInfo>({ id: '', credit_limit: 0, closing_day: 1, due_day: 10 })

// Days 1-31
const days = Array.from({ length: 31 }, (_, i) => ({ label: `${i + 1}`, value: i + 1 }))

onMounted(async () => {
  await fetchCards()
  loadExtendedInfo()
})

const loadExtendedInfo = () => {
  const stored = localStorage.getItem('creditscan_cards_extended')
  if (stored) {
    extendedInfo.value = JSON.parse(stored)
  }
}

const saveExtendedInfo = () => {
  localStorage.setItem('creditscan_cards_extended', JSON.stringify(extendedInfo.value))
}

const getExtended = (id: string) => {
  return extendedInfo.value[id] || { credit_limit: 0, closing_day: 1, due_day: 10 }
}

const startEdit = (card: CreditCard) => {
  const info = getExtended(card.id)
  editForm.value = { ...info, id: card.id }
  editingId.value = card.id
}

const cancelEdit = () => {
  editingId.value = null
}

const saveEdit = () => {
  if (editingId.value) {
    extendedInfo.value[editingId.value] = { ...editForm.value }
    saveExtendedInfo()
    toast.add({ severity: 'success', summary: 'Saved', detail: 'Card settings updated', life: 3000 })
    editingId.value = null
  }
}

const formatCurrency = (val: number) => {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(val)
}
</script>

<template>
  <div class="cards-manager">
    <div v-if="isLoading" class="flex justify-center p-8">
      <i class="pi pi-spin pi-spinner text-3xl text-gray-400"></i>
    </div>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div v-for="card in cards" :key="card.id" class="p-6 bg-white rounded-xl border border-gray-200 shadow-sm transition-all hover:shadow-md">
        <div class="flex justify-between items-start mb-4">
          <div class="flex items-center gap-3">
             <i class="pi pi-credit-card text-2xl text-blue-600"></i>
             <div>
               <h4 class="font-bold text-gray-800">{{ getCardDisplayName(card) }}</h4>
               <p class="text-sm text-gray-500">•••• {{ card.last4 }}</p>
             </div>
          </div>
          <Button 
            v-if="editingId !== card.id" 
            icon="pi pi-pencil" 
            text 
            rounded 
            @click="startEdit(card)"
          />
        </div>

        <div v-if="editingId === card.id" class="space-y-4">
           <div class="field">
             <label class="block text-xs font-semibold text-gray-500 uppercase mb-1">Credit Limit</label>
             <InputNumber v-model="editForm.credit_limit" mode="currency" currency="USD" class="w-full" />
           </div>
           
           <div class="grid grid-cols-2 gap-4">
             <div class="field">
               <label class="block text-xs font-semibold text-gray-500 uppercase mb-1">Closing Day</label>
               <Dropdown v-model="editForm.closing_day" :options="days" optionLabel="label" optionValue="value" class="w-full" />
             </div>
             <div class="field">
               <label class="block text-xs font-semibold text-gray-500 uppercase mb-1">Due Day</label>
               <Dropdown v-model="editForm.due_day" :options="days" optionLabel="label" optionValue="value" class="w-full" />
             </div>
           </div>

           <div class="flex justify-end gap-2 mt-4">
             <Button label="Cancel" severity="secondary" text size="small" @click="cancelEdit" />
             <Button label="Save" size="small" @click="saveEdit" />
           </div>
        </div>

        <div v-else class="grid grid-cols-3 gap-4 text-sm">
          <div>
            <span class="block text-gray-400 text-xs uppercase">Limit</span>
            <span class="font-semibold text-gray-700">{{ formatCurrency(getExtended(card.id).credit_limit) }}</span>
          </div>
          <div>
            <span class="block text-gray-400 text-xs uppercase">Closes</span>
            <span class="font-semibold text-gray-700">Day {{ getExtended(card.id).closing_day }}</span>
          </div>
          <div>
            <span class="block text-gray-400 text-xs uppercase">Due</span>
            <span class="font-semibold text-gray-700">Day {{ getExtended(card.id).due_day }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
