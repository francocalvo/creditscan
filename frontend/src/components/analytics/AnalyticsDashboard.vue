<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { AnalyticsService, ExpensesService } from '@/api/sdk.gen'
import MetricCard from '@/components/dashboard/MetricCard.vue'
import Dropdown from 'primevue/dropdown'
import ProgressBar from 'primevue/progressbar'

// Types for local state since API returns unknown
interface Metrics {
  total_income: number
  total_expenses: number
  net_savings: number
  savings_rate: number
}

interface CategorySummary {
  category: string
  total_amount: number
  count: number
  percentage: number
}

// State
const period = ref('month') // month, year, all
const loading = ref(false)
const metrics = ref<Metrics>({
  total_income: 0,
  total_expenses: 0,
  net_savings: 0,
  savings_rate: 0
})
const categoryBreakdown = ref<CategorySummary[]>([])

// Options
const periodOptions = [
  { label: 'Last 30 Days', value: 'month' },
  { label: 'Last 90 Days', value: 'quarter' },
  { label: 'This Year', value: 'year' } // Simplification, would need date calcs
]

// Date Utilities
const getDateRange = (p: string) => {
  const end = new Date()
  const start = new Date()
  
  if (p === 'month') {
    start.setDate(end.getDate() - 30)
  } else if (p === 'quarter') {
    start.setDate(end.getDate() - 90)
  } else if (p === 'year') {
    start.setMonth(0, 1) // Jan 1st
  }
  
  return {
    fromDate: start.toISOString().split('T')[0],
    toDate: end.toISOString().split('T')[0]
  }
}

// Formatters
const formatCurrency = (val: number) => {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(val)
}

const formatPercent = (val: number) => {
  return new Intl.NumberFormat('en-US', { style: 'percent', minimumFractionDigits: 1 }).format(val / 100)
}

// Fetch Data
const fetchData = async () => {
  loading.value = true
  const { fromDate, toDate } = getDateRange(period.value)
  
  try {
    const [metricsRes, expenseRes] = await Promise.all([
      AnalyticsService.getCombinedMetrics({ fromDate, toDate }),
      ExpensesService.getExpenseSummary({ fromDate, toDate, groupBy: 'category' })
    ])

    // Parse Metrics (Assuming structure, adding safeguards)
    const m = metricsRes as any
    metrics.value = {
      total_income: m.total_income || 0,
      total_expenses: m.total_expenses || 0,
      net_savings: (m.total_income || 0) - (m.total_expenses || 0),
      savings_rate: m.savings_rate || 0
    }

    // Parse Expenses
    const e = expenseRes as any
    // Depending on API, might be array or object. Assuming array of objects based on common patterns
    // If it's an object key->value, we adjust. Let's assume list for now or check previous code if available.
    // 'unknown' return type suggests dynamic dict. 
    // Usually summary endpoints return [ { category: 'Food', amount: 100 }, ... ]
    let categories: any[] = []
    if (Array.isArray(e)) {
      categories = e
    } else if (e.data && Array.isArray(e.data)) {
      categories = e.data
    } else if (typeof e === 'object') {
       // Maybe { "Food": 100, "Rent": 500 }
       categories = Object.entries(e).map(([k, v]) => ({ category: k, total_amount: v }))
    }

    const totalExp = metrics.value.total_expenses || 1 // Avoid div by zero
    
    categoryBreakdown.value = categories.map((c: any) => ({
      category: c.category || c.name || 'Uncategorized',
      total_amount: c.total_amount || c.amount || 0,
      count: c.count || 0,
      percentage: ((c.total_amount || c.amount || 0) / totalExp) * 100
    })).sort((a, b) => b.total_amount - a.total_amount)

  } catch (error) {
    console.error('Failed to fetch analytics', error)
  } finally {
    loading.value = false
  }
}

watch(period, () => {
  fetchData()
})

onMounted(() => {
  fetchData()
})
</script>

<template>
  <div class="analytics-dashboard">
    <!-- Header Controls -->
    <div class="header-controls mb-6 flex justify-between items-center">
      <h2 class="text-xl font-bold text-gray-800">Financial Overview</h2>
      <Dropdown 
        v-model="period" 
        :options="periodOptions" 
        optionLabel="label" 
        optionValue="value" 
        class="w-48" 
      />
    </div>

    <!-- Metrics Cards -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
      <MetricCard
        title="Total Income"
        :value="formatCurrency(metrics.total_income)"
        icon="pi pi-arrow-down-left"
        class="bg-green-50 border-green-100"
        :iconClass="'text-green-500'" 
      />
      <MetricCard
        title="Total Expenses"
        :value="formatCurrency(metrics.total_expenses)"
        icon="pi pi-arrow-up-right"
        class="bg-red-50 border-red-100"
        :iconClass="'text-red-500'"
      />
      <MetricCard
        title="Net Savings"
        :value="formatCurrency(metrics.net_savings)"
        :subtitle="`Savings Rate: ${formatPercent(metrics.savings_rate)}`"
        icon="pi pi-wallet"
        class="bg-blue-50 border-blue-100"
        :iconClass="'text-blue-500'"
      />
    </div>

    <!-- Breakdown Section -->
    <div class="breakdown-section grid grid-cols-1 lg:grid-cols-2 gap-8">
      <!-- Expense Breakdown -->
      <div class="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
        <h3 class="text-lg font-semibold mb-4 text-gray-700">Expense Breakdown</h3>
        
        <div v-if="loading" class="flex justify-center p-8">
          <i class="pi pi-spin pi-spinner text-3xl text-gray-400"></i>
        </div>

        <div v-else-if="categoryBreakdown.length > 0" class="space-y-4">
          <div v-for="cat in categoryBreakdown.slice(0, 8)" :key="cat.category">
            <div class="flex justify-between text-sm mb-1">
              <span class="font-medium text-gray-700">{{ cat.category }}</span>
              <span class="text-gray-900 font-bold">{{ formatCurrency(cat.total_amount) }}</span>
            </div>
            <ProgressBar :value="cat.percentage" :showValue="false" style="height: 8px" />
          </div>
        </div>

        <div v-else class="text-center text-gray-500 p-4">
          No expenses recorded for this period.
        </div>
      </div>

      <!-- Placeholder for Income Breakdown or Charts -->
      <div class="bg-white p-6 rounded-xl border border-gray-200 shadow-sm flex flex-col items-center justify-center text-center">
         <i class="pi pi-chart-pie text-5xl text-gray-200 mb-4"></i>
         <h3 class="text-lg font-medium text-gray-900">More Insights Coming Soon</h3>
         <p class="text-gray-500 max-w-xs">Detailed visualizations and income analysis features will be available in future updates.</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Scoped styles if tailwind not fully available or for specifics */
.analytics-dashboard {
  /* container styles */
}
</style>
