<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import Dialog from 'primevue/dialog'
import Button from 'primevue/button'
import StatusBadge from '@/components/dashboard/StatusBadge.vue'
import { type StatementWithCard } from '@/composables/useStatements'
import { getCardWithLast4 } from '@/composables/useCreditCards'
import { useStatementTransactions } from '@/composables/useStatementTransactions'
import { useTags, type Tag } from '@/composables/useTags'
import { useTransactionTags } from '@/composables/useTransactionTags'

interface Props {
  visible: boolean
  statement: StatementWithCard | null
}

interface Emits {
  (e: 'update:visible', value: boolean): void
  (e: 'pay', statement: StatementWithCard): void
}

type SortField = 'txn_date' | 'amount' | 'payee'
type SortOrder = 'asc' | 'desc'

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// Transactions composable
const { transactions, totalCount, isLoading, error, fetchTransactions, reset } = useStatementTransactions()

// Tags composables
const { fetchTags, getTagById } = useTags()
const { fetchTagsForTransactions, getTagIdsForTransaction, reset: resetTransactionTags } = useTransactionTags()

// Pagination
const PAGE_SIZE = 15
const currentPage = ref(1)

// Sorting
const sortField = ref<SortField>('txn_date')
const sortOrder = ref<SortOrder>('desc')
const DEFAULT_SORT_ORDERS: Record<SortField, SortOrder> = {
  txn_date: 'desc',
  amount: 'asc',
  payee: 'asc'
}

const totalPages = computed(() => {
  if (totalCount.value === 0) return 1
  return Math.ceil(totalCount.value / PAGE_SIZE)
})

// Smart pagination with ellipsis
const visiblePages = computed<(number | null)[]>(() => {
  const total = totalPages.value
  const current = currentPage.value

  // Show all pages if there are 7 or fewer
  if (total <= 7) {
    return Array.from({ length: total }, (_, i) => i + 1)
  }

  // Otherwise, show pages with ellipsis
  const pages: (number | null)[] = []

  // Always include first page
  pages.push(1)

  // Show ellipsis after first page if current is far from start
  if (current > 3) {
    pages.push(null)
  }

  // Show pages around current page
  const startPage = Math.max(2, current - 1)
  const endPage = Math.min(total - 1, current + 1)

  for (let i = startPage; i <= endPage; i++) {
    pages.push(i)
  }

  // Show ellipsis before last page if current is far from end
  if (current < total - 2) {
    pages.push(null)
  }

  // Always include last page
  pages.push(total)

  // Remove consecutive duplicates
  const filteredPages: (number | null)[] = []
  for (let i = 0; i < pages.length; i++) {
    if (pages[i] !== pages[i - 1]) {
      filteredPages.push(pages[i])
    }
  }

  return filteredPages
})

const paginationInfo = computed(() => {
  const startItem = (currentPage.value - 1) * PAGE_SIZE + 1
  const endItem = Math.min(currentPage.value * PAGE_SIZE, totalCount.value)
  return `${startItem}-${endItem} of ${totalCount.value}`
})

const sortedTransactions = computed(() => {
  const txns = [...transactions.value]

  if (sortField.value === 'txn_date') {
    txns.sort((a, b) => {
      const aTime = new Date(a.txn_date).getTime()
      const bTime = new Date(b.txn_date).getTime()
      return sortOrder.value === 'asc' ? aTime - bTime : bTime - aTime
    })
  } else if (sortField.value === 'amount') {
    txns.sort((a, b) => {
      return sortOrder.value === 'asc' ? a.amount - b.amount : b.amount - a.amount
    })
  } else if (sortField.value === 'payee') {
    txns.sort((a, b) => {
      const comparison = a.payee.toLowerCase().localeCompare(b.payee.toLowerCase())
      return sortOrder.value === 'asc' ? comparison : -comparison
    })
  }

  return txns
})

// Watch for modal open/close to fetch/reset transactions
watch(
  () => props.visible,
  async (newVisible) => {
    if (newVisible && props.statement) {
      currentPage.value = 1
      sortField.value = 'txn_date'
      sortOrder.value = 'desc'

      // Fetch tags (uses cache if already fetched)
      await fetchTags()

      // Fetch transactions
      await fetchTransactions(props.statement.id, { skip: 0, limit: PAGE_SIZE })

      // Fetch tag mappings for the transactions
      const transactionIds = transactions.value.map((t) => t.id)
      await fetchTagsForTransactions(transactionIds)
    } else if (!newVisible) {
      currentPage.value = 1
      reset()
      resetTransactionTags()
    }
  }
)

// Internal visible state that syncs with prop
const internalVisible = computed({
  get: () => props.visible,
  set: (value: boolean) => {
    emit('update:visible', value)
  }
})

// Computed properties
const cardDisplay = computed(() => {
  if (!props.statement?.card) return 'Unknown Card'
  return getCardWithLast4(props.statement.card)
})

const formattedPeriod = computed(() => {
  if (!props.statement?.period_start || !props.statement?.period_end) return 'N/A'
  const start = new Date(props.statement.period_start)
  const end = new Date(props.statement.period_end)

  if (start.getMonth() === end.getMonth() && start.getFullYear() === end.getFullYear()) {
    return end.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })
  }

  return `${start.toLocaleDateString('en-US', { month: 'short' })} - ${end.toLocaleDateString('en-US', { month: 'short', year: 'numeric' })}`
})

// Helper functions
const formatCurrency = (amount: number | null): string => {
  if (amount === null) return '$0.00'
  return `$${amount.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

const formatDate = (dateStr: string | null): string => {
  if (!dateStr) return 'N/A'
  const date = new Date(dateStr)
  return date.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })
}

const formatTransactionDate = (dateStr: string): string => {
  const date = new Date(dateStr)
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

const formatInstallments = (cur: number | null, tot: number | null): string => {
  if (cur !== null && tot !== null) {
    return `${cur}/${tot}`
  }
  return '-'
}

const getTagsForTransaction = (transactionId: string): Tag[] => {
  const tagIds = getTagIdsForTransaction(transactionId)
  return tagIds
    .map((tagId) => getTagById(tagId))
    .filter((tag): tag is Tag => tag !== undefined)
}

const goToPage = async (page: number) => {
  if (page < 1 || page > totalPages.value) return
  currentPage.value = page
  await fetchTransactions(props.statement!.id, { skip: (page - 1) * PAGE_SIZE, limit: PAGE_SIZE })

  // Fetch tag mappings for new page's transactions
  const transactionIds = transactions.value.map((t) => t.id)
  await fetchTagsForTransactions(transactionIds)
}

const handleSort = (field: SortField) => {
  if (field === sortField.value) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortField.value = field
    sortOrder.value = DEFAULT_SORT_ORDERS[field]
  }
}

const getAriaSort = (field: SortField): 'ascending' | 'descending' | 'none' => {
  if (field !== sortField.value) return 'none'
  return sortOrder.value === 'asc' ? 'ascending' : 'descending'
}

const getSortLabel = (field: SortField, columnName: string): string => {
  if (field !== sortField.value) {
    return `Sort by ${columnName}`
  }
  const direction = sortOrder.value === 'asc' ? 'ascending' : 'descending'
  return `Sort by ${columnName}, currently sorted ${direction}. Click to sort ${sortOrder.value === 'asc' ? 'descending' : 'ascending'}.`
}

const getSortIcon = (field: SortField): string => {
  if (field !== sortField.value) {
    return 'pi pi-sort-alt'
  }
  return sortOrder.value === 'asc' ? 'pi pi-sort-amount-up' : 'pi pi-sort-amount-down'
}

const handleRetry = () => {
  if (props.statement) {
    fetchTransactions(props.statement.id, { skip: (currentPage.value - 1) * PAGE_SIZE, limit: PAGE_SIZE })
  }
}

// Event handlers
const handleClose = () => {
  internalVisible.value = false
}

const handlePay = () => {
  if (props.statement) {
    emit('pay', props.statement)
  }
}
</script>

<template>
  <Dialog
    v-model:visible="internalVisible"
    modal
    :style="{ width: '850px' }"
    :closable="true"
    :draggable="false"
  >
    <template #header>
      <div v-if="statement" class="modal-header">
        <div class="header-left">
          <p class="card-info">{{ cardDisplay }}</p>
          <p class="period">{{ formattedPeriod }}</p>
        </div>
        <StatusBadge :status="statement.status" />
      </div>
    </template>

    <div v-if="statement" class="modal-content">
      <!-- Summary Section -->
      <section class="summary-section">
        <h3 class="section-title">Statement Summary</h3>
        <div class="summary-grid">
          <div class="summary-item">
            <p class="summary-label">Previous Balance</p>
            <p class="summary-value">{{ formatCurrency(statement.previous_balance) }}</p>
          </div>

          <div class="summary-item summary-item--highlight">
            <p class="summary-label">Current Balance</p>
            <p class="summary-value">{{ formatCurrency(statement.current_balance) }}</p>
          </div>

          <div class="summary-item">
            <p class="summary-label">Minimum Payment</p>
            <p class="summary-value">{{ formatCurrency(statement.minimum_payment) }}</p>
          </div>

          <div class="summary-item">
            <p class="summary-label">Due Date</p>
            <p class="summary-value">{{ formatDate(statement.due_date) }}</p>
          </div>

          <div class="summary-item">
            <p class="summary-label">Close Date</p>
            <p class="summary-value">{{ formatDate(statement.close_date) }}</p>
          </div>
        </div>
      </section>

      <!-- Transactions Section -->
      <section class="transactions-section">
        <h3 class="section-title">Transactions</h3>

        <!-- Loading State -->
        <div v-if="isLoading" class="loading-state" role="status" aria-live="polite" aria-label="Loading transactions">
          <div class="spinner"></div>
          <p>Loading transactions...</p>
        </div>

        <!-- Error State -->
        <div v-else-if="error" class="error-state" role="alert">
          <i class="pi pi-exclamation-circle"></i>
          <p>Failed to load transactions</p>
          <Button label="Retry" size="small" severity="secondary" @click="handleRetry" />
        </div>

        <!-- Empty State -->
        <div v-else-if="transactions.length === 0" class="empty-state">
          <i class="pi pi-inbox"></i>
          <p>No transactions for this statement</p>
        </div>

        <!-- Transactions Table -->
         <table v-else class="transactions-table">
            <thead>
              <tr>
                <th
                  class="sortable"
                  :aria-sort="getAriaSort('txn_date')"
                  :aria-label="getSortLabel('txn_date', 'Date')"
                  tabindex="0"
                  @click="handleSort('txn_date')"
                  @keydown.enter.prevent="handleSort('txn_date')"
                  @keydown.space.prevent="handleSort('txn_date')"
                >
                  Date <i :class="getSortIcon('txn_date')"></i>
                </th>
                <th
                  class="sortable"
                  :aria-sort="getAriaSort('payee')"
                  :aria-label="getSortLabel('payee', 'Payee')"
                  tabindex="0"
                  @click="handleSort('payee')"
                  @keydown.enter.prevent="handleSort('payee')"
                  @keydown.space.prevent="handleSort('payee')"
                >
                  Payee <i :class="getSortIcon('payee')"></i>
                </th>
                <th>Description</th>
                <th
                  class="sortable"
                  :aria-sort="getAriaSort('amount')"
                  :aria-label="getSortLabel('amount', 'Amount')"
                  tabindex="0"
                  @click="handleSort('amount')"
                  @keydown.enter.prevent="handleSort('amount')"
                  @keydown.space.prevent="handleSort('amount')"
                >
                  Amount <i :class="getSortIcon('amount')"></i>
                </th>
                <th>Installments</th>
                <th>Tags</th>
              </tr>
            </thead>
           <tbody>
              <tr v-for="txn in sortedTransactions" :key="txn.id">
                <td>{{ formatTransactionDate(txn.txn_date) }}</td>
               <td class="text-truncate payee-cell" :title="txn.payee">{{ txn.payee }}</td>
               <td class="text-truncate description-cell" :title="txn.description">{{ txn.description }}</td>
               <td :class="txn.amount < 0 ? 'amount--negative' : 'amount--positive'">
                 {{ formatCurrency(txn.amount) }}
               </td>
              <td class="installments">{{ formatInstallments(txn.installment_cur, txn.installment_tot) }}</td>
               <td class="tags">
                 <template v-if="getTagsForTransaction(txn.id).length > 0">
                   <span
                     v-for="tag in getTagsForTransaction(txn.id)"
                     :key="tag.tag_id"
                     class="tag-chip"
                   >
                     {{ tag.label }}
                   </span>
                 </template>
                 <template v-else>-</template>
               </td>
            </tr>
          </tbody>
        </table>

         <!-- Pagination -->
         <div v-if="totalPages > 1" class="pagination">
           <span class="pagination-info">{{ paginationInfo }}</span>
           <div class="pagination-nav">
             <Button
               icon="pi pi-chevron-left"
               severity="secondary"
               text
               :disabled="currentPage === 1"
               @click="goToPage(currentPage - 1)"
               aria-label="Previous page"
             />
             <template v-for="(page, index) in visiblePages" :key="page ?? `ellipsis-${index}`">
               <Button
                  v-if="page !== null"
                  :label="page.toString()"
                  severity="secondary"
                  :outlined="page !== currentPage"
                  @click="goToPage(page)"
                  :aria-label="'Go to page ' + page"
                  :aria-current="page === currentPage ? 'page' : undefined"
                />
                <span v-else class="pagination-ellipsis">...</span>
             </template>
             <Button
               icon="pi pi-chevron-right"
               severity="secondary"
               text
               :disabled="currentPage === totalPages"
               @click="goToPage(currentPage + 1)"
               aria-label="Next page"
             />
           </div>
         </div>
      </section>

      <!-- Action Buttons -->
      <div class="modal-actions">
        <Button
          label="Pay"
          icon="pi pi-credit-card"
          :disabled="statement.is_fully_paid"
          @click="handlePay"
          severity="primary"
        />
        <Button
          label="Close"
          icon="pi pi-times"
          @click="handleClose"
          severity="secondary"
          outlined
        />
      </div>
    </div>
  </Dialog>
</template>

<style scoped>
.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.header-left {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.card-info {
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--text-color);
  margin: 0;
}

.period {
  font-size: 0.875rem;
  color: var(--text-color-secondary);
  margin: 0;
  font-weight: 500;
}

.modal-content {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.summary-section {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.section-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-color);
  margin: 0;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1.25rem;
}

.summary-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 1rem;
  background: var(--surface-50);
  border-radius: 8px;
  border: 1px solid var(--surface-border);
}

.summary-label {
  font-size: 0.875rem;
  color: var(--text-color-secondary);
  margin: 0;
  font-weight: 500;
}

.summary-value {
  font-size: 1.125rem;
  color: var(--text-color);
  margin: 0;
  font-weight: 600;
}

.summary-item--highlight {
  background: linear-gradient(135deg, var(--primary-color-alpha-10) 0%, var(--surface-50) 100%);
  border-color: var(--primary-color);
}

.summary-item--highlight .summary-value {
  font-size: 1.5rem;
  color: var(--primary-color);
}

.transactions-section {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

/* Loading State */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem 1.25rem;
  gap: 1rem;
  color: var(--text-color-secondary);
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--surface-border);
  border-top-color: var(--primary-color);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.loading-state p {
  margin: 0;
  font-size: 0.938rem;
}

/* Error State */
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2.5rem;
  gap: 0.75rem;
  text-align: center;
}

.error-state i {
  font-size: 2rem;
  color: var(--red-500);
}

.error-state p {
  margin: 0;
  color: var(--text-color-secondary);
  font-size: 0.938rem;
}

/* Empty State */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2.5rem;
  text-align: center;
}

.empty-state i {
  font-size: 2rem;
  color: var(--text-color-secondary);
  margin-bottom: 0.75rem;
}

.empty-state p {
  margin: 0;
  color: var(--text-color-secondary);
  font-size: 0.938rem;
}

/* Transactions Table */
.transactions-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.938rem;
}

.transactions-table th {
  text-align: left;
  padding: 0.75rem;
  border-bottom: 2px solid var(--surface-border);
  font-weight: 600;
  color: var(--text-color);
}

.transactions-table td {
  padding: 0.75rem;
  border-bottom: 1px solid var(--surface-border);
  color: var(--text-color);
}

.transactions-table tr:last-child td {
  border-bottom: none;
}

.transactions-table .amount--negative {
  color: var(--red-500);
  font-weight: 500;
}

.transactions-table .amount--positive {
  color: var(--green-500);
  font-weight: 500;
}

.transactions-table .installments {
  text-align: center;
}

.transactions-table .tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
}

.tag-chip {
  display: inline-flex;
  align-items: center;
  padding: 0.125rem 0.5rem;
  background: var(--primary-50);
  color: var(--primary-700);
  border-radius: 1rem;
  font-size: 0.75rem;
  font-weight: 500;
  white-space: nowrap;
}

.transactions-table th.sortable {
  cursor: pointer;
  user-select: none;
}

.transactions-table th.sortable:hover {
  background: var(--surface-100);
}

.transactions-table th.sortable i {
  margin-left: 0.25rem;
  font-size: 0.75rem;
  color: var(--text-color-secondary);
}

.transactions-table th.sortable i.pi-sort-amount-up,
.transactions-table th.sortable i.pi-sort-amount-down {
  color: var(--primary-color);
}

/* Pagination */
.pagination {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid var(--surface-border);
}

.pagination-info {
  font-size: 0.875rem;
  color: var(--text-color-secondary);
}

.pagination-nav {
  display: flex;
  gap: 0.25rem;
  align-items: center;
}

.pagination-nav :deep(.p-button) {
  min-width: 2.25rem;
}

.pagination-ellipsis {
  padding: 0 0.5rem;
  color: var(--text-color-secondary);
  font-size: 0.875rem;
  user-select: none;
}

/* Text Truncation */
.text-truncate {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.payee-cell {
  max-width: 180px;
}

.description-cell {
  max-width: 200px;
}

.modal-actions {
  display: flex;
  gap: 0.75rem;
  justify-content: flex-end;
  margin-top: 0.5rem;
}

/* Responsive design */
@media (max-width: 768px) {
  .modal-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }

  .summary-grid {
    grid-template-columns: 1fr;
  }

  .modal-actions {
    flex-direction: column;
  }

  .modal-actions .p-button {
    width: 100%;
  }
}
</style>
