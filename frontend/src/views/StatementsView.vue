<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useStatements } from '@/composables/useStatements'
import MetricCard from '@/components/dashboard/MetricCard.vue'
import StatusBadge from '@/components/dashboard/StatusBadge.vue'
import TabNavigation from '@/components/dashboard/TabNavigation.vue'
import PaymentModal from '@/components/PaymentModal.vue'
import StatementDetailModal from '@/components/StatementDetailModal.vue'
import AddCardModal from '@/components/AddCardModal.vue'
import CreditCardTile from '@/components/cards/CreditCardTile.vue'
import SetLimitModal from '@/components/cards/SetLimitModal.vue'
import { useTransactions } from '@/composables/useTransactions'
import { useAnalytics } from '@/composables/useAnalytics'
import { parseDateString } from '@/utils/date'
import type { CreditCard } from '@/composables/useCreditCards'
import Toast from 'primevue/toast'
import { useToast } from 'primevue/usetoast'
import Button from 'primevue/button'
import Chart from 'primevue/chart'
import AddCardPlaceholder from '@/components/AddCardPlaceholder.vue'

const {
  statementsWithCard,
  cards,
  balance,
  isLoading,
  isBalanceLoading,
  fetchStatements,
  fetchBalance,
  createPayment,
  formatCurrency,
  formatDate,
  formatPeriod,
  aggregateUtilization,
  updateCardLimit,
} = useStatements()

const {
  transactions,
  isLoading: isTransactionsLoading,
  fetchTransactions,
  formatCurrency: formatTransactionCurrency,
  formatDate: formatTransactionDate,
} = useTransactions()

const {
  isLoading: isAnalyticsLoading,
  error: analyticsError,
  dateFilter,
  setDateFilter,
  fetchAnalytics,
  refresh: refreshAnalytics,
  filteredTransactions,
  summaryMetrics,
  spendingByMonth,
  spendingByTag,
  topMerchants,
  formatCurrency: formatAnalyticsCurrency,
} = useAnalytics()

const enrichedTransactions = computed(() => {
  return transactions.value.map((txn) => {
    const statement = statementsWithCard.value.find((s) => s.id === txn.statement_id)
    return {
      ...txn,
      card: statement?.card,
      status: statement?.status || 'pending',
    }
  })
})

/**
 * Transform spendingByMonth into Chart.js data format.
 * Creates a new object when spendingByMonth changes to ensure proper reactivity.
 */
const monthlyChartData = computed(() => {
  if (!spendingByMonth.value || spendingByMonth.value.length === 0) {
    return {
      labels: [],
      datasets: [],
    }
  }

  return {
    labels: spendingByMonth.value.map((item) => item.month),
    datasets: [
      {
        label: 'Monthly Spending',
        data: spendingByMonth.value.map((item) => item.amount),
        borderColor: '#3b82f6',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        borderWidth: 2,
        fill: true,
        tension: 0.4,
        pointRadius: 4,
        pointHoverRadius: 6,
        pointBackgroundColor: '#3b82f6',
        pointBorderColor: '#ffffff',
        pointBorderWidth: 2,
      },
    ],
  }
})

/**
 * Chart options for monthly spending line chart.
 * Configured for responsive layout with area fill.
 */
const monthlyChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: false,
    },
    tooltip: {
      backgroundColor: '#1f2937',
      titleColor: '#f9fafb',
      bodyColor: '#f9fafb',
      padding: 12,
      cornerRadius: 8,
	      displayColors: false,
	      callbacks: {
	        label: (context: any) => {
	          const rawValue = context?.parsed?.y
	          const value =
	            typeof rawValue === 'number' || typeof rawValue === 'string' ? rawValue : 0
	          return ` ${formatAnalyticsCurrency(value)}`
	        },
	      },
	    },
	  },
  scales: {
    x: {
      grid: {
        display: false,
      },
      ticks: {
        color: '#6b7280',
        font: {
          size: 12,
        },
      },
    },
    y: {
      beginAtZero: true,
      grid: {
        color: '#f3f4f6',
        borderDash: [5, 5],
      },
	      ticks: {
	        color: '#6b7280',
	        font: {
	          size: 12,
	        },
	        callback: (value: unknown) =>
	          formatAnalyticsCurrency(typeof value === 'number' || typeof value === 'string' ? value : 0),
	      },
	    },
	  },
	}

/**
 * Color palette for tag chart segments.
 * Provides 12 distinguishable colors for different tag categories.
 * Cycles through colors if there are more categories than colors.
 */
const tagChartColors = [
  '#3b82f6', // blue
  '#ef4444', // red
  '#10b981', // green
  '#f59e0b', // amber
  '#8b5cf6', // violet
  '#ec4899', // pink
  '#06b6d4', // cyan
  '#f97316', // orange
  '#6366f1', // indigo
  '#14b8a6', // teal
  '#eab308', // yellow
  '#a855f7', // purple
]

/**
 * Transform spendingByTag into Chart.js pie format.
 * Creates a new object when spendingByTag changes to ensure proper reactivity.
 * Applies colors from palette, cycling if more categories than colors available.
 */
const tagChartData = computed(() => {
  if (!spendingByTag.value || spendingByTag.value.length === 0) {
    return {
      labels: [],
      datasets: [],
    }
  }

  return {
    labels: spendingByTag.value.map((item) => item.tag),
    datasets: [
      {
        data: spendingByTag.value.map((item) => item.amount),
        backgroundColor: spendingByTag.value.map(
          (_, index) => tagChartColors[index % tagChartColors.length],
        ),
        borderWidth: 2,
        borderColor: '#ffffff',
      },
    ],
  }
})

/**
 * Chart options for spending by tag pie chart.
 * Configured for responsive layout with legend on the right side.
 * Legend moves to bottom on mobile screens for better space utilization.
 */
const tagChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
	plugins: {
	  legend: {
	      position: 'right' as 'right' | 'bottom',
	      labels: {
	        color: '#374151',
	        font: {
	          size: 12,
        },
        padding: 15,
        usePointStyle: true,
        pointStyle: 'circle',
      },
    },
	    tooltip: {
      backgroundColor: '#1f2937',
      titleColor: '#f9fafb',
      bodyColor: '#f9fafb',
      padding: 12,
      cornerRadius: 8,
      displayColors: true,
	      callbacks: {
	        label: (context: any) => {
	          const dataIndex = typeof context?.dataIndex === 'number' ? context.dataIndex : -1
	          const item = spendingByTag.value[dataIndex]
	          if (!item) return ''
	          const percentage = item.percentage.toFixed(1)
	          return ` ${item.tag}: ${formatAnalyticsCurrency(item.amount)} (${percentage}%)`
	        },
	      },
	    },
	  },
	}

// Computed options that respond to screen size
const isMobile = ref(false)

// Check screen size on mount and resize
onMounted(() => {
  const checkScreenSize = () => {
    isMobile.value = window.innerWidth <= 768
  }
  checkScreenSize()
  window.addEventListener('resize', checkScreenSize)
  onUnmounted(() => {
    window.removeEventListener('resize', checkScreenSize)
  })
})

// Adjust pie chart legend position based on screen size
// Note: We use type assertion here because Chart.js position types don't
// allow dynamic switching between 'right' and 'bottom' at runtime
watch(
  isMobile,
  (mobile) => {
    tagChartOptions.plugins.legend.position = mobile ? 'bottom' : 'right'
  },
  { immediate: true },
)

const toast = useToast()

const activeTab = ref('statements')
const searchQuery = ref('')
const filterStatus = ref('all')

// Payment modal state
const showPaymentModal = ref(false)
const showDetailModal = ref(false)
const detailStartInEditMode = ref(false)
const selectedStatement = ref<(typeof statementsWithCard.value)[0] | null>(null)
const isProcessingPayment = ref(false)
const isTransitioningModals = ref(false)

// Add Card modal state
const showAddCardModal = ref(false)

// Set Limit modal state (for Step06)
const showSetLimitModal = ref(false)
const cardForLimitEdit = ref<CreditCard | null>(null)

// Handler for opening set limit modal
const handleSetLimit = (card: CreditCard) => {
  cardForLimitEdit.value = card
  showSetLimitModal.value = true
}

watch(showDetailModal, (isVisible) => {
  if (!isVisible) detailStartInEditMode.value = false
})

watch(statementsWithCard, (updatedStatements) => {
  if (!selectedStatement.value) return
  const latest = updatedStatements.find((s) => s.id === selectedStatement.value?.id)
  if (latest && latest !== selectedStatement.value) {
    selectedStatement.value = latest
  }
})

// Analytics composable
const analyticsInitialized = ref(false)

// Check if there are no transactions for the current filter
const hasNoTransactions = computed(() => filteredTransactions.value.length === 0)

const handleAnalyticsRefresh = async () => {
  if (isAnalyticsLoading.value) return

  try {
    await refreshAnalytics()
  } finally {
    analyticsInitialized.value = true
  }
}

watch(
  activeTab,
  async (newTab) => {
    if (newTab !== 'analytics') return
    if (analyticsInitialized.value) return
    if (isAnalyticsLoading.value) return

    try {
      await fetchAnalytics()
    } finally {
      analyticsInitialized.value = true
    }
  },
  { immediate: true },
)

// Date filter presets for analytics
const datePresets = [
  { label: 'Last Week', value: 'week' },
  { label: 'Last Month', value: 'month' },
  { label: 'Last 3 Months', value: '3months' },
  { label: 'Last 6 Months', value: '6months' },
  { label: 'Last Year', value: 'year' },
  { label: 'All Time', value: 'all' },
] as const

const tabs = [
  { id: 'statements', label: 'Statements' },
  { id: 'cards', label: 'Cards' },
  { id: 'analytics', label: 'Analytics' },
  { id: 'transactions', label: 'Transactions' },
]

// Calculate metrics from statements and balance endpoint
const totalBalance = computed(() => {
  return formatCurrency(balance.value.total_balance)
})

const monthlyBalance = computed(() => {
  return formatCurrency(balance.value.monthly_balance)
})

const activeCards = computed(() => {
  return cards.value.length
})

// Filter statements based on search and status
const filteredStatements = computed(() => {
  let filtered = statementsWithCard.value

  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter((s) => {
      if (!s.card) return false
      return (
        s.card.last4.includes(query) ||
        s.card.bank.toLowerCase().includes(query) ||
        s.card.brand.toLowerCase().includes(query)
      )
    })
  }

  if (filterStatus.value !== 'all') {
    filtered = filtered.filter((s) => s.status === filterStatus.value)
  }

  return filtered
})

onMounted(() => {
  fetchStatements()
  fetchBalance()
  fetchTransactions()
})

const getStatementCardDisplay = (statement: (typeof statementsWithCard.value)[0]) => {
  if (!statement.card) return 'Unknown Card'
  const brandName = statement.card.brand.charAt(0).toUpperCase() + statement.card.brand.slice(1)
  return `${statement.card.bank} ${brandName} ••${statement.card.last4}`
}

// Get latest balance for a card
const getCardLatestBalance = (cardId: string) => {
  const cardStatements = statementsWithCard.value
    .filter((s) => s.card_id === cardId)
    .sort((a, b) => {
      if (!a.period_end || !b.period_end) return 0
      return parseDateString(b.period_end).getTime() - parseDateString(a.period_end).getTime()
    })

  return cardStatements.length > 0 ? cardStatements[0]?.current_balance : null
}

// Handle payment button click
const handlePayClick = (statement: (typeof statementsWithCard.value)[0]) => {
  selectedStatement.value = statement
  showPaymentModal.value = true
}

// Handle View Details button click
const handleViewDetails = (statement: (typeof statementsWithCard.value)[0]) => {
  selectedStatement.value = statement
  detailStartInEditMode.value = false
  showDetailModal.value = true
}

// Handle Pay button click from detail modal
const handlePayFromDetail = (statement: (typeof statementsWithCard.value)[0]) => {
  if (isTransitioningModals.value) return
  isTransitioningModals.value = true
  showDetailModal.value = false
  nextTick(() => {
    selectedStatement.value = statement
    showPaymentModal.value = true
    isTransitioningModals.value = false
  })
}

const handleStatementUpdated = async () => {
  await Promise.all([fetchStatements(), fetchBalance()])
}

const handleEditStatementFromPayment = () => {
  if (!selectedStatement.value) return
  if (isTransitioningModals.value) return

  isTransitioningModals.value = true
  showPaymentModal.value = false

  nextTick(() => {
    detailStartInEditMode.value = true
    showDetailModal.value = true
    isTransitioningModals.value = false
  })
}

// Handle payment submission
const handlePaymentSubmit = async (paymentData: {
  statement_id: string
  amount: number
  payment_date: string
  currency: string
}) => {
  isProcessingPayment.value = true
  try {
    await createPayment(paymentData)
    toast.add({
      severity: 'success',
      summary: 'Payment Successful',
      detail: `Payment of ${formatCurrency(paymentData.amount)} has been recorded.`,
      life: 3000,
    })
    showPaymentModal.value = false
    selectedStatement.value = null
  } catch (error) {
    toast.add({
      severity: 'error',
      summary: 'Payment Failed',
      detail:
        error instanceof Error ? error.message : 'An error occurred while processing the payment.',
      life: 5000,
    })
  } finally {
    isProcessingPayment.value = false
  }
}

// Handler for opening add card modal
const openAddCardModal = () => {
  showAddCardModal.value = true
}

// Handler for card creation success
const handleCardCreated = (card: { bank: string; last4: string }) => {
  // Show success toast
  toast.add({
    severity: 'success',
    summary: 'Card Added',
    detail: `${card.bank} card ending in ${card.last4} has been added`,
    life: 3000,
  })
  // Refresh statements and cards list
  fetchStatements()
  fetchBalance()
}

// Handler for set limit modal save success
const handleLimitSaved = () => {
  if (!cardForLimitEdit.value) return
  // Show success toast
  toast.add({
    severity: 'success',
    summary: 'Credit Limit Updated',
    detail: `Limit updated for ${cardForLimitEdit.value.bank} ••${cardForLimitEdit.value.last4}`,
    life: 3000,
  })
  // Clear card reference
  cardForLimitEdit.value = null
}
</script>

<template>
  <div class="statements-view">
    <!-- Metrics Grid -->
    <div class="metrics-grid">
      <MetricCard
        title="Total Balance"
        :value="totalBalance"
        subtitle="All unpaid statements"
        icon="pi pi-dollar"
      />

      <MetricCard
        title="Monthly Balance"
        :value="monthlyBalance"
        subtitle="Excluding future installments"
        icon="pi pi-chart-bar"
      />

      <MetricCard
        title="Active Cards"
        :value="activeCards.toString()"
        subtitle="Total cards registered"
        icon="pi pi-credit-card"
      />

      <MetricCard
        title="Credit Utilization"
        :value="
          aggregateUtilization.value === null
            ? 'N/A'
            : aggregateUtilization.value.toFixed(1) + '%'
        "
        :subtitle="
          aggregateUtilization.totalCount === 0
            ? 'No cards'
            : aggregateUtilization.missingCount === aggregateUtilization.totalCount
            ? 'Requires credit limits'
            : aggregateUtilization.missingCount === 0
            ? 'All cards have limits'
            : `${aggregateUtilization.missingCount} of ${aggregateUtilization.totalCount} cards missing limits`
        "
        icon="pi pi-trending-up"
      />
    </div>

    <!-- Tab Navigation -->
    <TabNavigation :tabs="tabs" :activeTab="activeTab" @update:activeTab="activeTab = $event" />

    <!-- Statements Section -->
    <div v-if="activeTab === 'statements'" class="statements-section">
      <div class="section-header">
        <div class="header-left">
          <h2 class="section-title">Credit Card Statements</h2>
          <p class="section-subtitle">Manage and track all your credit card statements</p>
        </div>
      </div>

      <!-- Search and Filters -->
      <div class="controls">
        <div class="search-box">
          <i class="pi pi-search search-icon"></i>
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search statements..."
            class="search-input"
          />
        </div>

        <div class="filter-controls">
          <button class="filter-button">
            <i class="pi pi-cog"></i>
          </button>
          <select v-model="filterStatus" class="filter-select">
            <option value="all">All</option>
            <option value="paid">Paid</option>
            <option value="pending">Pending</option>
            <option value="overdue">Overdue</option>
          </select>
        </div>
      </div>

      <!-- Statements Table -->
      <div class="table-container">
        <div v-if="isLoading || isBalanceLoading" class="loading-state">
          <div class="spinner"></div>
          <p>Loading statements...</p>
        </div>

        <table v-else-if="filteredStatements.length > 0" class="statements-table">
          <thead>
            <tr>
              <th>Card</th>
              <th>Period</th>
              <th>Balance</th>
              <th>Due Date</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="statement in filteredStatements" :key="statement.id">
              <td class="card-cell">{{ getStatementCardDisplay(statement) }}</td>
              <td>{{ formatPeriod(statement.period_start, statement.period_end) }}</td>
              <td class="balance-cell">{{ formatCurrency(statement.current_balance) }}</td>
              <td class="date-cell">
                <i class="pi pi-calendar calendar-icon"></i>
                {{ formatDate(statement.due_date) }}
              </td>
              <td>
                <StatusBadge :status="statement.status" />
              </td>
              <td>
                <div class="action-buttons">
                  <button
                    class="action-button"
                    @click="handlePayClick(statement)"
                    :disabled="statement.is_fully_paid"
                  >
                    Pay
                  </button>
                  <button class="action-button" @click="handleViewDetails(statement)">
                    View Details
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>

        <div v-else class="empty-state">
          <p>No statements found</p>
        </div>
      </div>
    </div>

    <!-- Cards Section -->
    <div v-else-if="activeTab === 'cards'" class="cards-section">
      <div class="section-header">
        <div class="header-left">
          <h2 class="section-title">Your Credit Cards</h2>
          <p class="section-subtitle">Manage and view all your registered credit cards</p>
        </div>
      </div>

      <div v-if="isLoading || isBalanceLoading" class="loading-state">
        <div class="spinner"></div>
        <p>Loading cards...</p>
      </div>

      <div v-else class="cards-grid">
        <!-- Add Card Placeholder (always shown as first item) -->
        <AddCardPlaceholder @click="openAddCardModal" />
        <CreditCardTile
          v-for="card in cards"
          :key="card.id"
          :card="card"
          :current-balance="getCardLatestBalance(card.id)"
          :format-currency="formatCurrency"
          @set-limit="handleSetLimit"
        />
      </div>
    </div>

    <!-- Analytics Section -->
    <div v-else-if="activeTab === 'analytics'" class="analytics-section">
      <div class="section-header">
        <div class="header-left">
          <h2 class="section-title">Analytics</h2>
          <p class="section-subtitle">View insights into your spending patterns</p>
        </div>
        <div class="header-right">
          <Button
            icon="pi pi-refresh"
            @click="handleAnalyticsRefresh"
            :loading="isAnalyticsLoading"
            :disabled="isAnalyticsLoading"
            outlined
            aria-label="Refresh analytics"
          />
        </div>
      </div>

      <!-- Date Filter Toolbar -->
      <div class="analytics-toolbar">
        <div class="date-filters" role="group" aria-label="Date filter options">
          <Button
            v-for="preset in datePresets"
            :key="preset.value"
            :label="preset.label"
            :outlined="dateFilter !== preset.value"
            @click="setDateFilter(preset.value)"
            size="small"
            :aria-pressed="dateFilter === preset.value"
          />
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="isAnalyticsLoading || !analyticsInitialized" class="loading-state">
        <div class="spinner"></div>
        <p>Loading analytics...</p>
      </div>

      <!-- Error State -->
      <div v-else-if="analyticsError" class="empty-state">
        <i class="pi pi-exclamation-circle error-icon"></i>
        <h3>Error Loading Analytics</h3>
        <p>{{ analyticsError }}</p>
        <Button
          label="Retry"
          icon="pi pi-refresh"
          @click="handleAnalyticsRefresh"
          :loading="isAnalyticsLoading"
          :disabled="isAnalyticsLoading"
          outlined
        />
      </div>

      <!-- Empty State (no transactions) -->
      <div v-else-if="hasNoTransactions" class="empty-state">
        <i class="pi pi-inbox empty-icon"></i>
        <h3>No Transactions Found</h3>
        <p>There are no transactions to analyze yet.</p>
      </div>

      <!-- Analytics Content -->
      <div v-else>
        <!-- Metrics Grid (Step 9) -->
        <div class="analytics-metrics-grid">
          <MetricCard
            title="Total Spending"
            :value="formatAnalyticsCurrency(summaryMetrics.totalSpending)"
            icon="pi pi-wallet"
          />

          <MetricCard
            title="Transactions"
            :value="summaryMetrics.transactionCount.toString()"
            icon="pi pi-list"
          />

          <MetricCard
            title="Median Transaction"
            :value="formatAnalyticsCurrency(summaryMetrics.medianTransaction)"
            icon="pi pi-chart-line"
          />

          <MetricCard
            title="Highest Transaction"
            :value="formatAnalyticsCurrency(summaryMetrics.highestTransaction)"
            icon="pi pi-arrow-up"
          />
        </div>

        <!-- Charts Grid (Steps 10-15) -->
        <div class="charts-grid">
          <!-- Monthly Spending Chart (Step 11) -->
          <div class="chart-card chart-card--wide">
            <div v-if="spendingByMonth.length === 0" class="chart-empty-state">
              <i class="pi pi-chart-line"></i>
              <p>No chart data for selected period</p>
            </div>
            <div v-else class="chart-container">
              <h4 class="chart-title">Monthly Spending</h4>
              <div class="chart-wrapper">
                <Chart type="line" :data="monthlyChartData" :options="monthlyChartOptions" />
              </div>
            </div>
          </div>

          <!-- Spending by Tag Chart (Step 13) -->
          <div v-if="spendingByTag.length === 0" class="chart-card">
            <div class="chart-container">
              <div class="chart-empty-state">
                <i class="pi pi-tags" style="font-size: 2rem; color: #9ca3af"></i>
                <p>No tag data for selected period</p>
              </div>
            </div>
          </div>
          <div v-else class="chart-card">
            <div class="chart-container">
              <h4>Spending by Tag</h4>
              <div class="chart-wrapper">
                <Chart type="pie" :data="tagChartData" :options="tagChartOptions" />
              </div>
            </div>
          </div>

          <!-- Top Merchants List (Step 15) -->
          <div class="chart-card">
            <div v-if="topMerchants.length === 0" class="chart-empty-state">
              <i class="pi pi-store" style="font-size: 2rem; color: #9ca3af"></i>
              <p>No merchant data for selected period</p>
            </div>
            <div v-else class="chart-container">
              <h4>Top Merchants</h4>
              <div class="merchants-list">
                <div
                  v-for="(merchant, index) in topMerchants"
                  :key="merchant.payee"
                  class="merchant-item"
                >
                  <div class="merchant-rank">{{ index + 1 }}</div>
                  <div class="merchant-info">
                    <div class="merchant-name">{{ merchant.payee }}</div>
                    <div class="merchant-count">
                      {{ merchant.transactionCount }}
                      {{ merchant.transactionCount === 1 ? 'transaction' : 'transactions' }}
                    </div>
                  </div>
                  <div class="merchant-amount">
                    {{ formatAnalyticsCurrency(merchant.totalAmount) }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Transactions Section -->
    <div v-else-if="activeTab === 'transactions'" class="transactions-section">
      <div class="section-header">
        <div class="header-left">
          <h2 class="section-title">Transactions</h2>
          <p class="section-subtitle">View all your transactions ordered by date</p>
        </div>
      </div>

      <div class="table-container">
        <div v-if="isTransactionsLoading" class="loading-state">
          <div class="spinner"></div>
          <p>Loading transactions...</p>
        </div>

        <table v-else-if="enrichedTransactions.length > 0" class="statements-table">
          <thead>
            <tr>
              <th>Date</th>
              <th>Card</th>
              <th>Description</th>
              <th>Category</th>
              <th>Amount</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="transaction in enrichedTransactions" :key="transaction.id">
              <td class="date-cell">
                <i class="pi pi-calendar calendar-icon"></i>
                {{ formatTransactionDate(transaction.txn_date) }}
              </td>
              <td>
                <div v-if="transaction.card" class="card-info">
                  <span class="bank-name">{{ transaction.card.bank }}</span>
                  <span class="card-brand">{{ transaction.card.brand }}</span>
                </div>
                <span v-else>-</span>
              </td>
              <td>{{ transaction.description }}</td>
              <td>
                <span v-if="transaction.category" class="category-badge">
                  {{ transaction.category }}
                </span>
                <span v-else>-</span>
              </td>
              <td class="balance-cell">
                {{ formatTransactionCurrency(transaction.amount, transaction.currency) }}
              </td>
              <td>
                <StatusBadge :status="transaction.status" />
              </td>
            </tr>
          </tbody>
        </table>

        <div v-else class="empty-state">
          <p>No transactions found</p>
        </div>
      </div>
    </div>

    <!-- Payment Modal -->
    <PaymentModal
      v-if="selectedStatement"
      v-model:visible="showPaymentModal"
      :statement-id="selectedStatement.id"
      :current-balance="
        typeof selectedStatement.current_balance === 'string'
          ? parseFloat(selectedStatement.current_balance)
          : selectedStatement.current_balance
      "
      :statement-card="getStatementCardDisplay(selectedStatement)"
      :is-submitting="isProcessingPayment"
      @submit="handlePaymentSubmit"
      @edit-statement="handleEditStatementFromPayment"
    />

    <!-- Statement Detail Modal -->
    <StatementDetailModal
      v-if="selectedStatement"
      v-model:visible="showDetailModal"
      :statement="selectedStatement"
      :start-in-edit-mode="detailStartInEditMode"
      @pay="handlePayFromDetail"
      @statement-updated="handleStatementUpdated"
    />

    <!-- Add Card Modal -->
    <AddCardModal
      v-model:visible="showAddCardModal"
      :existing-cards="cards"
      @card-created="handleCardCreated"
    />

    <!-- Set Limit Modal -->
    <SetLimitModal
      v-model="showSetLimitModal"
      :card="cardForLimitEdit"
      :on-save="updateCardLimit"
      @saved="handleLimitSaved"
    />

    <!-- Toast notifications -->
    <Toast />
  </div>
</template>

<style scoped>
.statements-view {
  padding: 32px;
  max-width: 1400px;
  margin: 0 auto;
}

/* Metrics Grid */
.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 24px;
  margin-bottom: 48px;
}

/* Section Header */
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
  color: #111827;
  margin: 0 0 8px 0;
}

.section-subtitle {
  font-size: 15px;
  color: #6b7280;
  margin: 0;
}

/* Controls */
.controls {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
}

.search-box {
  flex: 1;
  position: relative;
  display: flex;
  align-items: center;
  gap: 12px;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 0 16px;
}

.search-icon {
  font-size: 14px;
  color: #9ca3af;
}

.search-input {
  flex: 1;
  border: none;
  outline: none;
  padding: 12px 0;
  font-size: 15px;
}

.filter-controls {
  display: flex;
  gap: 12px;
}

.filter-button {
  padding: 12px 16px;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  cursor: pointer;
  font-size: 16px;
  transition: all 0.2s;
}

.filter-button:hover {
  background: #f9fafb;
}

.filter-select {
  padding: 12px 16px;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  outline: none;
  min-width: 140px;
}

/* Table */
.table-container {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  overflow: hidden;
}

.statements-table {
  width: 100%;
  border-collapse: collapse;
}

.statements-table thead {
  background: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
}

.statements-table th {
  padding: 16px 20px;
  text-align: left;
  font-size: 13px;
  font-weight: 600;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.statements-table tbody tr {
  border-bottom: 1px solid #f3f4f6;
  transition: background-color 0.2s;
}

.statements-table tbody tr:last-child {
  border-bottom: none;
}

.statements-table tbody tr:hover {
  background: #f9fafb;
}

.statements-table td {
  padding: 20px;
  font-size: 14px;
  color: #374151;
}

.card-cell {
  font-weight: 600;
  color: #111827;
}

.balance-cell {
  font-weight: 600;
  font-size: 15px;
}

.date-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.calendar-icon {
  font-size: 13px;
  color: #9ca3af;
}

.action-buttons {
  display: flex;
  gap: 8px;
  align-items: center;
}

.action-button {
  padding: 8px 16px;
  background: transparent;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  color: #374151;
  cursor: pointer;
  transition: all 0.2s;
}

.action-button:hover:not(:disabled) {
  background: #f9fafb;
  border-color: #d1d5db;
}

.action-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.action-button:first-child {
  background: var(--primary-color, #3b82f6);
  color: white;
  border-color: var(--primary-color, #3b82f6);
}

.action-button:first-child:hover:not(:disabled) {
  background: var(--primary-color-dark, #2563eb);
  border-color: var(--primary-color-dark, #2563eb);
}

/* Loading State */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  color: #6b7280;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #f3f4f6;
  border-top-color: #111827;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* Empty State */
.empty-state {
  padding: 80px 20px;
  text-align: center;
  color: #6b7280;
}

/* Cards Section */
.cards-section {
  margin-top: 32px;
}

.cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  gap: 24px;
  align-items: stretch;
}

.cards-grid > * {
  min-width: 0;
}

/* Placeholder Section */
.placeholder-section {
  padding: 80px 20px;
}

.placeholder-content {
  text-align: center;
  max-width: 400px;
  margin: 0 auto;
}

.placeholder-icon {
  font-size: 48px;
  display: block;
  margin-bottom: 24px;
  color: #d1d5db;
}

.placeholder-content h3 {
  font-size: 24px;
  font-weight: 700;
  color: #111827;
  margin: 0 0 12px 0;
}

.placeholder-content p {
  font-size: 15px;
  color: #6b7280;
  margin: 0;
}

/* Responsive */
@media (max-width: 1024px) {
  .statements-view {
    padding: 24px;
  }

  .metrics-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .metrics-grid {
    grid-template-columns: 1fr;
  }

  .controls {
    flex-direction: column;
  }

  .filter-controls {
    justify-content: stretch;
  }

  .filter-select {
    flex: 1;
  }

  .table-container {
    overflow-x: auto;
  }

  .statements-table {
    min-width: 800px;
  }

  .cards-grid {
    grid-template-columns: 1fr;
  }
}

.card-info {
  display: flex;
  flex-direction: column;
  font-size: 13px;
}

.bank-name {
  font-weight: 600;
  color: #111827;
}

.card-brand {
  color: #6b7280;
  font-size: 12px;
  text-transform: uppercase;
}

/* Analytics Section */
.analytics-section {
  animation: fadeIn 0.3s ease-in-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.analytics-toolbar {
  margin-bottom: 24px;
}

.date-filters {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.analytics-metrics-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.charts-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 24px;
}

.chart-card {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  overflow: hidden;
}

.chart-card--wide {
  grid-column: 1 / -1;
}

.chart-container {
  padding: 20px;
  display: flex;
  flex-direction: column;
}

.chart-title {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: #111827;
}

.chart-wrapper {
  position: relative;
  height: 300px;
}

.chart-card--wide .chart-wrapper {
  height: 420px;
}

.chart-wrapper .p-chart {
  height: 100%;
}

.chart-wrapper canvas {
  height: 100% !important;
  width: 100% !important;
}

.chart-empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 200px;
  color: #6b7280;
}

.chart-empty-state i {
  font-size: 48px;
  margin-bottom: 12px;
  color: #d1d5db;
}

.chart-placeholder {
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 32px;
  text-align: center;
  min-height: 200px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.chart-placeholder h4 {
  margin: 0 0 8px 0;
  font-size: 16px;
  font-weight: 600;
  color: #111827;
}

.chart-placeholder p {
  margin: 0;
  font-size: 14px;
  color: #6b7280;
}

/* Merchants List Styles */
.merchants-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.merchant-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #f9fafb;
  border-radius: 8px;
  transition: background-color 0.2s ease;
}

.merchant-item:hover {
  background: #f3f4f6;
}

.merchant-rank {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  min-width: 32px;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: white;
  border-radius: 50%;
  font-weight: 600;
  font-size: 14px;
}

.merchant-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.merchant-name {
  font-weight: 500;
  color: #111827;
  font-size: 14px;
}

.merchant-count {
  font-size: 12px;
  color: #6b7280;
}

.merchant-amount {
  font-weight: 600;
  color: #111827;
  font-size: 14px;
  text-align: right;
}

.error-icon {
  font-size: 48px;
  display: block;
  margin-bottom: 16px;
  color: #ef4444;
}

.empty-icon {
  font-size: 48px;
  display: block;
  margin-bottom: 16px;
  color: #d1d5db;
}

/* Responsive adjustments for analytics */
@media (max-width: 1024px) {
  .analytics-metrics-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .analytics-metrics-grid {
    grid-template-columns: 1fr;
  }

  .charts-grid {
    grid-template-columns: 1fr;
  }

  .chart-card--wide {
    grid-column: 1;
  }

  .chart-wrapper {
    height: 250px;
  }

  .chart-card--wide .chart-wrapper {
    height: 320px;
  }

  .date-filters {
    overflow-x: auto;
    white-space: nowrap;
    padding-bottom: 8px;
  }
}
</style>
