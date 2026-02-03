<script setup lang="ts">
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { useStatements } from '@/composables/useStatements'
import { getCardDisplayName } from '@/composables/useCreditCards'
import MetricCard from '@/components/dashboard/MetricCard.vue'
import StatusBadge from '@/components/dashboard/StatusBadge.vue'
import TabNavigation from '@/components/dashboard/TabNavigation.vue'
import PaymentModal from '@/components/PaymentModal.vue'
import StatementDetailModal from '@/components/StatementDetailModal.vue'
import { useTransactions } from '@/composables/useTransactions'
import Toast from 'primevue/toast'
import { useToast } from 'primevue/usetoast'

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
  formatPeriod 
} = useStatements()

const {
  transactions,
  isLoading: isTransactionsLoading,
  fetchTransactions,
  formatCurrency: formatTransactionCurrency,
  formatDate: formatTransactionDate
} = useTransactions()

const enrichedTransactions = computed(() => {
  return transactions.value.map(txn => {
    const statement = statementsWithCard.value.find(s => s.id === txn.statement_id)
    return {
      ...txn,
      card: statement?.card,
      status: statement?.status || 'pending'
    }
  })
})

const toast = useToast()

const activeTab = ref('statements')
const searchQuery = ref('')
const filterStatus = ref('all')

// Payment modal state
const showPaymentModal = ref(false)
const showDetailModal = ref(false)
const detailStartInEditMode = ref(false)
const selectedStatement = ref<typeof statementsWithCard.value[0] | null>(null)
const isProcessingPayment = ref(false)
const isTransitioningModals = ref(false)

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

const tabs = [
  { id: 'statements', label: 'Statements' },
  { id: 'cards', label: 'Cards' },
  { id: 'analytics', label: 'Analytics' },
  { id: 'transactions', label: 'Transactions' }
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

const pendingStatements = computed(() => {
  return statementsWithCard.value.filter(s => s.status === 'pending').length
})

const creditUtilization = computed(() => {
  // Mock calculation - in real app would use credit limits
  return '23%'
})

// Filter statements based on search and status
const filteredStatements = computed(() => {
  let filtered = statementsWithCard.value

  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(s => {
      if (!s.card) return false
      return (
        s.card.last4.includes(query) || 
        s.card.bank.toLowerCase().includes(query) ||
        s.card.brand.toLowerCase().includes(query)
      )
    })
  }

  if (filterStatus.value !== 'all') {
    filtered = filtered.filter(s => s.status === filterStatus.value)
  }

  return filtered
})

onMounted(() => {
  fetchStatements()
  fetchBalance()
  fetchTransactions()
})

const getStatementCardDisplay = (statement: typeof statementsWithCard.value[0]) => {
  if (!statement.card) return 'Unknown Card'
  const brandName = statement.card.brand.charAt(0).toUpperCase() + statement.card.brand.slice(1)
  return `${statement.card.bank} ${brandName} ••${statement.card.last4}`
}

const getCardBrandIcon = (brand?: string): string => {
  const icons: Record<string, string> = {
    visa: 'pi pi-credit-card',
    mastercard: 'pi pi-credit-card',
    amex: 'pi pi-credit-card',
    discover: 'pi pi-credit-card',
    other: 'pi pi-credit-card'
  }
  return icons[brand || 'other'] || 'pi pi-credit-card'
}

// Get statements count per card
const getCardStatementsCount = (cardId: string) => {
  return statementsWithCard.value.filter(s => s.card_id === cardId).length
}

// Get latest balance for a card
const getCardLatestBalance = (cardId: string) => {
  const cardStatements = statementsWithCard.value
    .filter(s => s.card_id === cardId)
    .sort((a, b) => {
      if (!a.period_end || !b.period_end) return 0
      return new Date(b.period_end).getTime() - new Date(a.period_end).getTime()
    })
  
  return cardStatements.length > 0 ? cardStatements[0].current_balance : null
}

// Handle payment button click
const handlePayClick = (statement: typeof statementsWithCard.value[0]) => {
  selectedStatement.value = statement
  showPaymentModal.value = true
}

// Handle View Details button click
const handleViewDetails = (statement: typeof statementsWithCard.value[0]) => {
  selectedStatement.value = statement
  detailStartInEditMode.value = false
  showDetailModal.value = true
}

// Handle Pay button click from detail modal
const handlePayFromDetail = (statement: typeof statementsWithCard.value[0]) => {
  if (isTransitioningModals.value) return
  isTransitioningModals.value = true
  showDetailModal.value = false
  nextTick(() => {
    selectedStatement.value = statement
    showPaymentModal.value = true
    isTransitioningModals.value = false
  })
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
      life: 3000
    })
    showPaymentModal.value = false
    selectedStatement.value = null
  } catch (error) {
    toast.add({
      severity: 'error',
      summary: 'Payment Failed',
      detail: error instanceof Error ? error.message : 'An error occurred while processing the payment.',
      life: 5000
    })
  } finally {
    isProcessingPayment.value = false
  }
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
        :subtitle="`${pendingStatements} statements pending`"
        icon="pi pi-credit-card"
      />
      
      <MetricCard
        title="Credit Utilization"
        :value="creditUtilization"
        subtitle="Excellent utilization rate"
        icon="pi pi-trending-up"
      />
    </div>

    <!-- Tab Navigation -->
    <TabNavigation 
      :tabs="tabs" 
      :activeTab="activeTab"
      @update:activeTab="activeTab = $event"
    />

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
                  <button class="action-button" @click="handleViewDetails(statement)">View Details</button>
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

      <div v-else-if="cards.length === 0" class="empty-state">
        <i class="pi pi-credit-card" style="font-size: 64px; color: #d1d5db; margin-bottom: 16px;"></i>
        <h3 style="margin: 0 0 8px 0;">No cards added yet</h3>
        <p style="margin: 0; color: #6b7280;">Add your first credit card to get started</p>
      </div>

      <div v-else class="cards-grid">
        <div 
          v-for="card in cards" 
          :key="card.id"
          class="card-item-large"
        >
          <div class="card-header-section">
            <div class="card-brand-icon">
              <i :class="getCardBrandIcon(card.brand)"></i>
            </div>
            <div class="card-menu">
              <i class="pi pi-ellipsis-v"></i>
            </div>
          </div>
          
          <div class="card-body">
            <div class="card-number">
              •••• •••• •••• {{ card.last4 }}
            </div>
            <div class="card-details-row">
              <div class="card-detail">
                <div class="detail-label">Bank</div>
                <div class="detail-value">{{ card.bank }}</div>
              </div>
              <div class="card-detail">
                <div class="detail-label">Brand</div>
                <div class="detail-value">{{ card.brand.toUpperCase() }}</div>
              </div>
            </div>
          </div>

          <div class="card-footer-section">
            <div class="card-stat">
              <div class="stat-label">Current Balance</div>
              <div class="stat-value">{{ formatCurrency(getCardLatestBalance(card.id)) }}</div>
            </div>
            <div class="card-stat">
              <div class="stat-label">Statements</div>
              <div class="stat-value">{{ getCardStatementsCount(card.id) }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Analytics Section (Placeholder) -->
    <div v-else-if="activeTab === 'analytics'" class="placeholder-section">
      <div class="placeholder-content">
        <i class="pi pi-chart-line placeholder-icon"></i>
        <h3>Analytics</h3>
        <p>Analytics dashboard coming soon</p>
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
              <td class="balance-cell">{{ formatTransactionCurrency(transaction.amount, transaction.currency) }}</td>
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
      :current-balance="typeof selectedStatement.current_balance === 'string' ? parseFloat(selectedStatement.current_balance) : selectedStatement.current_balance"
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
  to { transform: rotate(360deg); }
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
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 24px;
}

.card-item-large {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16px;
  padding: 24px;
  color: white;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  transition: transform 0.2s, box-shadow 0.2s;
  cursor: pointer;
  min-height: 240px;
  display: flex;
  flex-direction: column;
}

.card-item-large:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2);
}

.card-header-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
}

.card-brand-icon {
  width: 48px;
  height: 48px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}

.card-menu {
  color: rgba(255, 255, 255, 0.8);
  cursor: pointer;
  padding: 8px;
  border-radius: 4px;
  transition: background 0.2s;
}

.card-menu:hover {
  background: rgba(255, 255, 255, 0.1);
}

.card-body {
  flex: 1;
  margin-bottom: 24px;
}

.card-number {
  font-size: 22px;
  font-weight: 600;
  letter-spacing: 2px;
  margin-bottom: 20px;
  font-family: 'Courier New', monospace;
}

.card-details-row {
  display: flex;
  gap: 32px;
}

.card-detail {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.detail-label {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  opacity: 0.7;
  font-weight: 500;
}

.detail-value {
  font-size: 14px;
  font-weight: 600;
}

.card-footer-section {
  display: flex;
  justify-content: space-between;
  padding-top: 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.2);
}

.card-stat {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-label {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  opacity: 0.7;
  font-weight: 500;
}

.stat-value {
  font-size: 16px;
  font-weight: 700;
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
</style>
