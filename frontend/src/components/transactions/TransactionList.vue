<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import { ExpensesService, IncomeService } from '@/api/sdk.gen'
import type { ExpensePublic, IncomePublic } from '@/api/types.gen'
import StatusBadge from '@/components/dashboard/StatusBadge.vue' // Reusing if applicable, or generic badge
import Tag from 'primevue/tag'
import Button from 'primevue/button'
import Calendar from 'primevue/calendar'
import Dropdown from 'primevue/dropdown'
import InputText from 'primevue/inputtext'

// Types
type TransactionType = 'expense' | 'income' | 'all'
interface Transaction {
  id: string
  date: string
  amount: number
  currency: string
  category?: string // expenses have category
  origin?: string // incomes have origin
  narration: string
  type: 'expense' | 'income'
  details: ExpensePublic | IncomePublic
}

// State
const transactions = ref<Transaction[]>([])
const loading = ref(false)
const transactionType = ref<TransactionType>('all')
const dateRange = ref<Date[]>([])
const searchQuery = ref('')

// Pagination
const page = ref(0)
const limit = ref(20)
const totalRecords = ref(0)
const hasMore = ref(false)

// Options
const typeOptions = [
  { label: 'All Transactions', value: 'all' },
  { label: 'Expenses', value: 'expense' },
  { label: 'Income', value: 'income' }
]

// Formatting
const formatCurrency = (amount: number) => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD', // Defaulting to USD for display consistency, though API returns specific fields
    minimumFractionDigits: 2
  }).format(amount)
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

// Fetching
const fetchTransactions = async () => {
  loading.value = true
  transactions.value = [] // Reset for simple pagination, or append for infinite scroll
  
  try {
    const fromDate = dateRange.value && dateRange.value[0] 
      ? dateRange.value[0].toISOString().split('T')[0] 
      : new Date(new Date().setMonth(new Date().getMonth() - 3)).toISOString().split('T')[0] // Default 3 months
    
    // Using current date if no end date selected
    const toDate = dateRange.value && dateRange.value[1] 
      ? dateRange.value[1].toISOString().split('T')[0] 
      : undefined

    const promises = []

    if (transactionType.value === 'all' || transactionType.value === 'expense') {
      promises.push(ExpensesService.getExpenses({
        fromDate: fromDate,
        toDate: toDate,
        limit: limit.value,
        skip: page.value * limit.value
      }))
    }

    if (transactionType.value === 'all' || transactionType.value === 'income') {
      promises.push(IncomeService.getIncomes({
        fromDate: fromDate,
        toDate: toDate,
        limit: limit.value,
        skip: page.value * limit.value
      }))
    }

    const results = await Promise.all(promises)
    
    let combined: Transaction[] = []

    // Process Expenses
    if (transactionType.value === 'all' || transactionType.value === 'expense') {
      const expensesRes = results[transactionType.value === 'expense' ? 0 : 0]
      // @ts-ignore - API types might be slightly off in finding 'data' vs direct array depending on generation, assuming 'data' based on types.gen.ts
      const expenses = (expensesRes.data || []) as ExpensePublic[]
      
      combined.push(...expenses.map((e: ExpensePublic) => ({
        id: e.id,
        date: e.date,
        amount: e.amount_usd, // Using USD for unified view, could arguably toggle
        currency: 'USD',
        category: e.category,
        narration: e.narration,
        type: 'expense' as const,
        details: e
      })))
    }

    // Process Incomes
    if (transactionType.value === 'all' || transactionType.value === 'income') {
      const incomeIndex = transactionType.value === 'all' ? 1 : 0
      const incomeRes = results[incomeIndex]
      // @ts-ignore
      const incomes = (incomeRes.data || []) as IncomePublic[]
      
      combined.push(...incomes.map((i: IncomePublic) => ({
        id: i.id,
        date: i.date,
        amount: i.amount_usd,
        currency: 'USD',
        origin: i.origin,
        narration: i.narration,
        type: 'income' as const,
        details: i
      })))
    }

    // Sort by date desc
    combined.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())
    
    transactions.value = combined
    
  } catch (error) {
    console.error('Failed to fetch transactions', error)
  } finally {
    loading.value = false
  }
}

// Watchers
watch([transactionType, dateRange], () => {
  page.value = 0
  fetchTransactions()
})

onMounted(() => {
  fetchTransactions()
})

const getAmountClass = (t: Transaction) => {
  return t.type === 'income' ? 'text-green-600' : 'text-red-600'
}

const getCategoryLabel = (t: Transaction) => {
  if (t.type === 'income') return t.origin || 'Income'
  return t.category || 'Expense'
}

// Computed for Search filtering (client-side for now as API search might be limited)
const filteredTransactions = computed(() => {
  if (!searchQuery.value) return transactions.value
  const query = searchQuery.value.toLowerCase()
  return transactions.value.filter(t => 
    t.narration.toLowerCase().includes(query) ||
    (t.category && t.category.toLowerCase().includes(query)) ||
    (t.origin && t.origin.toLowerCase().includes(query))
  )
})

</script>

<template>
  <div class="transaction-list">
    <!-- Filters -->
    <div class="filters-bar">
      <div class="search-wrapper">
        <i class="pi pi-search search-icon"></i>
        <InputText v-model="searchQuery" placeholder="Search transactions..." class="w-full" />
      </div>
      
      <div class="filter-group">
        <Dropdown 
          v-model="transactionType" 
          :options="typeOptions" 
          optionLabel="label" 
          optionValue="value" 
          class="w-48"
        />
        <Calendar 
          v-model="dateRange" 
          selectionMode="range" 
          :manualInput="false" 
          placeholder="Date Range" 
          showIcon
          class="w-64"
        />
        <Button icon="pi pi-refresh" @click="fetchTransactions" text rounded />
      </div>
    </div>

    <!-- Table -->
    <div class="table-container">
      <div v-if="loading" class="loading-state">
        <i class="pi pi-spin pi-spinner text-4xl mb-4"></i>
        <p>Loading transactions...</p>
      </div>

      <table v-else-if="filteredTransactions.length > 0" class="w-full">
        <thead>
          <tr>
            <th class="text-left py-3 px-4 bg-gray-50 font-semibold text-gray-600">Date</th>
            <th class="text-left py-3 px-4 bg-gray-50 font-semibold text-gray-600">Description</th>
            <th class="text-left py-3 px-4 bg-gray-50 font-semibold text-gray-600">Category / Origin</th>
            <th class="text-right py-3 px-4 bg-gray-50 font-semibold text-gray-600">Amount</th>
            <th class="text-center py-3 px-4 bg-gray-50 font-semibold text-gray-600">Type</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="t in filteredTransactions" :key="t.id" class="border-b hover:bg-gray-50 transition-colors">
            <td class="py-3 px-4 text-gray-700">{{ formatDate(t.date) }}</td>
            <td class="py-3 px-4 font-medium text-gray-900">{{ t.narration }}</td>
            <td class="py-3 px-4 text-gray-600">
              <Tag :value="getCategoryLabel(t)" :severity="t.type === 'income' ? 'success' : 'info'" rounded></Tag>
            </td>
            <td class="py-3 px-4 text-right font-bold" :class="getAmountClass(t)">
              {{ t.type === 'expense' ? '-' : '+' }} {{ formatCurrency(t.amount) }}
            </td>
            <td class="py-3 px-4 text-center">
              <i 
                class="pi" 
                :class="t.type === 'income' ? 'pi-arrow-down-left text-green-500' : 'pi-arrow-up-right text-red-500'"
              ></i>
            </td>
          </tr>
        </tbody>
      </table>

      <div v-else class="empty-state">
        <i class="pi pi-list text-6xl text-gray-200 mb-4"></i>
        <p class="text-gray-500 text-lg">No transactions found</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.transaction-list {
  background: var(--bg-primary);
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  overflow: hidden;
}

.filters-bar {
  padding: 16px;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.search-wrapper {
  position: relative;
  flex: 1;
  min-width: 200px;
}

.search-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: #9ca3af;
  z-index: 10;
}

:deep(.p-inputtext) {
  padding-left: 36px;
}

.filter-group {
  display: flex;
  gap: 12px;
  align-items: center;
}

.loading-state, .empty-state {
  padding: 64px;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #6b7280;
}

.text-green-600 { color: #059669; }
.text-red-600 { color: #dc2626; }

/* PrimeVue Overrides */
:deep(.p-dropdown-label) {
  padding-top: 10px;
  padding-bottom: 10px;
}
</style>
