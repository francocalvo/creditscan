<script setup lang="ts">
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick, withDefaults } from 'vue'
import Dialog from 'primevue/dialog'
import Button from 'primevue/button'
import Message from 'primevue/message'
import InputNumber from 'primevue/inputnumber'
import InputText from 'primevue/inputtext'
import DatePicker from 'primevue/datepicker'
import Checkbox from 'primevue/checkbox'
import Dropdown from 'primevue/dropdown'
import StatusBadge from '@/components/dashboard/StatusBadge.vue'
import { type StatementWithCard } from '@/composables/useStatements'
import { type CardStatement } from '@/composables/useStatements'
import { getCardWithLast4 } from '@/composables/useCreditCards'
import { useStatementTransactions } from '@/composables/useStatementTransactions'
import { type StatementTransaction, type TransactionUpdate } from '@/composables/useStatementTransactions'
import { useTags, type Tag } from '@/composables/useTags'
import { useTransactionTags } from '@/composables/useTransactionTags'
import { useStatements } from '@/composables/useStatements'
import { parseDateString, toDateOnlyString } from '@/utils/date'

interface Props {
  visible: boolean
  statement: StatementWithCard | null
  startInEditMode?: boolean
}

interface Emits {
  (e: 'update:visible', value: boolean): void
  (e: 'pay', statement: StatementWithCard): void
  (e: 'statement-updated', statement: CardStatement): void
}

type SortField = 'txn_date' | 'amount' | 'payee'
type SortOrder = 'asc' | 'desc'

// New transaction interface (for unsaved transactions)
interface NewTransaction {
  _tempId: string
  txn_date: string
  payee: string
  description: string
  amount: number
  currency: string
  coupon: string | null
  installment_cur: number | null
  installment_tot: number | null
}

const props = withDefaults(defineProps<Props>(), {
  startInEditMode: false
})
const emit = defineEmits<Emits>()

// Currency options for dropdown
const currencyOptions = [
  { label: 'USD', value: 'USD' },
  { label: 'EUR', value: 'EUR' },
  { label: 'GBP', value: 'GBP' },
  { label: 'ARS', value: 'ARS' },
  { label: 'BRL', value: 'BRL' },
]

// Transactions composable
const { transactions, totalCount, isLoading, error, fetchTransactions, reset, updateTransaction, createTransaction, deleteTransaction } = useStatementTransactions()

// Statements composable
const { updateStatement: updateStatementApi } = useStatements()

// Tags composables
const { fetchTags, getTagById } = useTags()
const { fetchTagsForTransactions, getTagIdsForTransaction, reset: resetTransactionTags } = useTransactionTags()

// Edit mode state
const isEditMode = ref(false)
const isSaving = ref(false)
const saveError = ref<Error | null>(null)

// Form state
const editedStatement = ref<Partial<CardStatement> | null>(null)
const editedTransactions = ref<Map<string, TransactionUpdate>>(new Map())
const deletedTransactionIds = ref<Set<string>>(new Set())
const newTransactions = ref<NewTransaction[]>([])

// Validation computed
const validationErrors = computed(() => {
  const errors: Record<string, string> = {}

  if (!editedStatement.value) return errors

  const { due_date, close_date, period_start, period_end, previous_balance, current_balance, minimum_payment } = editedStatement.value

  // Date validations
  if (due_date && close_date) {
    const due = parseDateString(due_date)
    const close = parseDateString(close_date)
    if (due < close) {
      errors.due_date = 'Due date must not be before close date'
    }
  }

  if (period_start && period_end) {
    const start = parseDateString(period_start)
    const end = parseDateString(period_end)
    if (end < start) {
      errors.period_end = 'Period end must not be before period start'
    }
  }

  // Balance validations
  if (previous_balance !== undefined && previous_balance !== null && previous_balance < 0) {
    errors.previous_balance = 'Previous balance must be non-negative'
  }

  if (current_balance !== undefined && current_balance !== null && current_balance < 0) {
    errors.current_balance = 'Current balance must be non-negative'
  }

  if (minimum_payment !== undefined && minimum_payment !== null && minimum_payment < 0) {
    errors.minimum_payment = 'Minimum payment must be non-negative'
  }

  return errors
})

// Transaction validation for new transactions
const transactionValidationErrors = computed(() => {
  const errors: Record<string, Record<string, string>> = {}

  newTransactions.value.forEach((txn) => {
    const txnErrors: Record<string, string> = {}

    // Required field validations
    if (!txn.txn_date || txn.txn_date.trim() === '') {
      txnErrors.txn_date = 'Date is required'
    }

    if (!txn.payee || txn.payee.trim() === '') {
      txnErrors.payee = 'Payee is required'
    }

    if (!txn.description || txn.description.trim() === '') {
      txnErrors.description = 'Description is required'
    }

    if (txn.amount === null || txn.amount === undefined) {
      txnErrors.amount = 'Amount is required'
    }

    if (!txn.currency || txn.currency.trim() === '') {
      txnErrors.currency = 'Currency is required'
    }

    // Only add to errors if there are actual errors
    if (Object.keys(txnErrors).length > 0) {
      errors[txn._tempId] = txnErrors
    }
  })

  return errors
})

// Combined form validation
const isFormValid = computed(() => {
  // Check statement validation errors
  const hasStatementErrors = Object.keys(validationErrors.value).length > 0

  // Check transaction validation errors
  const hasTransactionErrors = Object.keys(transactionValidationErrors.value).length > 0

  return !hasStatementErrors && !hasTransactionErrors
})

// Get validation error for a specific field of a new transaction
const getTransactionFieldError = (tempId: string, field: string): string | undefined => {
  return transactionValidationErrors.value[tempId]?.[field]
}

// Check if a field has a validation error
const hasTransactionFieldError = (tempId: string, field: string): boolean => {
  return !!getTransactionFieldError(tempId, field)
}


// Date conversion helpers for Calendar components
const dueDateModel = computed({
  get: () => editedStatement.value?.due_date ? parseDateString(editedStatement.value.due_date) : null,
  set: (value: Date | null) => {
    if (editedStatement.value) {
      editedStatement.value.due_date = value ? toDateOnlyString(value) : null
    }
  }
})

const closeDateModel = computed({
  get: () => editedStatement.value?.close_date ? parseDateString(editedStatement.value.close_date) : null,
  set: (value: Date | null) => {
    if (editedStatement.value) {
      editedStatement.value.close_date = value ? toDateOnlyString(value) : null
    }
  }
})

const periodStartModel = computed({
  get: () => editedStatement.value?.period_start ? parseDateString(editedStatement.value.period_start) : null,
  set: (value: Date | null) => {
    if (editedStatement.value) {
      editedStatement.value.period_start = value ? toDateOnlyString(value) : null
    }
  }
})

const periodEndModel = computed({
  get: () => editedStatement.value?.period_end ? parseDateString(editedStatement.value.period_end) : null,
  set: (value: Date | null) => {
    if (editedStatement.value) {
      editedStatement.value.period_end = value ? toDateOnlyString(value) : null
    }
  }
})

// Transaction edit helper functions
const getTransactionValue = <T extends string | number | null | undefined>(
  txn: StatementTransaction,
  field: keyof TransactionUpdate
): T => {
  const edited = editedTransactions.value.get(txn.id)
  if (edited !== undefined && edited[field] !== undefined) {
    return edited[field] as T
  }
  return txn[field] as T
}

const setTransactionValue = (txnId: string, field: keyof TransactionUpdate, value: string | number | null) => {
  const current = editedTransactions.value.get(txnId) || {}
  editedTransactions.value.set(txnId, { ...current, [field]: value })
}

const isTransactionDeleted = (txnId: string): boolean => {
  return deletedTransactionIds.value.has(txnId)
}

const toggleTransactionDeleted = (txnId: string) => {
  if (deletedTransactionIds.value.has(txnId)) {
    deletedTransactionIds.value.delete(txnId)
  } else {
    deletedTransactionIds.value.add(txnId)
  }
}

// Get transaction date model for Calendar component
const getTransactionDateModel = (txn: StatementTransaction) => {
  return computed({
    get: () => {
      const dateValue = getTransactionValue<string | null>(txn, 'txn_date')
      return dateValue ? parseDateString(dateValue) : null
    },
    set: (value: Date | null) => {
      setTransactionValue(txn.id, 'txn_date', value ? toDateOnlyString(value) : null)
    }
  })
}

// Helper to handle model-value updates safely
const handleTextUpdate = (txnId: string, field: 'payee' | 'description', value: string | undefined) => {
  if (value !== undefined) {
    setTransactionValue(txnId, field, value)
  }
}

// Helper to handle date updates
const handleDateUpdate = (txnId: string, value: Date | Date[] | (Date | null)[] | null | undefined) => {
  if (value && !Array.isArray(value)) {
    setTransactionValue(txnId, 'txn_date', toDateOnlyString(value))
  } else {
    setTransactionValue(txnId, 'txn_date', null)
  }
}

// New transaction management functions
const addNewTransaction = () => {
  const newTxn: NewTransaction = {
    _tempId: crypto.randomUUID(),
    txn_date: toDateOnlyString(new Date()), // Today's date
    payee: '',
    description: '',
    amount: 0,
    currency: 'USD',
    coupon: null,
    installment_cur: null,
    installment_tot: null,
  }
  newTransactions.value.push(newTxn)
}

const removeNewTransaction = (tempId: string) => {
  const index = newTransactions.value.findIndex((t) => t._tempId === tempId)
  if (index !== -1) {
    newTransactions.value.splice(index, 1)
  }
}

const updateNewTransactionValue = (tempId: string, field: keyof NewTransaction, value: unknown) => {
  const txn = newTransactions.value.find((t) => t._tempId === tempId)
  if (txn && value !== undefined) {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    ;(txn as any)[field] = value
  }
}

const getNewTransactionDateModel = (tempId: string) => {
  return computed({
    get: () => {
      const txn = newTransactions.value.find((t) => t._tempId === tempId)
      return txn?.txn_date ? parseDateString(txn.txn_date) : null
    },
    set: (value: Date | null) => {
      updateNewTransactionValue(tempId, 'txn_date', value ? toDateOnlyString(value) : null)
    },
  })
}

// Helper to check if a transaction is new
const isNewTransaction = (item: StatementTransaction | NewTransaction): item is NewTransaction => {
  return '_tempId' in item
}

// Helper to handle new transaction date updates
const handleNewTransactionDateUpdate = (tempId: string, value: Date | Date[] | (Date | null)[] | null | undefined) => {
  if (value && !Array.isArray(value)) {
    updateNewTransactionValue(tempId, 'txn_date', toDateOnlyString(value))
  } else {
    updateNewTransactionValue(tempId, 'txn_date', null)
  }
}

// Pagination
const currentPage = ref(1)
const pageSize = ref(10)

const getResponsivePageSize = () => {
  const height = window.innerHeight
  const width = window.innerWidth

  // Keep page sizes small enough that the footer (pagination + actions) stays visible.
  let size = 10

  if (height < 720) size = 5
  else if (height < 820) size = 6
  else if (height < 920) size = 8

  if (width < 768) size = Math.min(size, 6)

  return size
}

const syncPageSize = () => {
  const nextSize = getResponsivePageSize()
  if (nextSize !== pageSize.value) {
    pageSize.value = nextSize
  }
}

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
  return Math.ceil(totalCount.value / pageSize.value)
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
    const page = pages[i]
    if (page === undefined) continue

    const previousPage = i > 0 ? pages[i - 1] : undefined
    if (page !== previousPage) {
      filteredPages.push(page)
    }
  }

  return filteredPages
})

const paginationInfo = computed(() => {
  const startItem = (currentPage.value - 1) * pageSize.value + 1
  const endItem = Math.min(currentPage.value * pageSize.value, totalCount.value)
  return `${startItem}-${endItem} of ${totalCount.value}`
})

const sortedTransactions = computed(() => {
  const txns = [...transactions.value]

  if (sortField.value === 'txn_date') {
    txns.sort((a, b) => {
      const aTime = parseDateString(a.txn_date).getTime()
      const bTime = parseDateString(b.txn_date).getTime()
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

// Combined transactions for display (existing + new) in edit mode
const allTransactions = computed(() => {
  if (!isEditMode.value) {
    return sortedTransactions.value
  }

  // In edit mode, show existing + new transactions
  return [...sortedTransactions.value, ...newTransactions.value]
})

const placeholderRowCount = computed(() => {
  const displayCount = isEditMode.value ? allTransactions.value.length : sortedTransactions.value.length
  return Math.max(0, pageSize.value - displayCount)
})

const theadRef = ref<HTMLElement | null>(null)
const tableHeaderHeight = ref(0)

const syncHeaderHeight = () => {
  if (!theadRef.value) return
  tableHeaderHeight.value = Math.round(theadRef.value.getBoundingClientRect().height)
}

// Watch for modal open/close to fetch/reset transactions
watch(
  () => props.visible,
  async (newVisible) => {
    if (newVisible && props.statement) {
      syncPageSize()
      currentPage.value = 1
      sortField.value = 'txn_date'
      sortOrder.value = 'desc'

      if (props.startInEditMode) {
        enterEditMode()
      }

      // Fetch tags (uses cache if already fetched)
      await fetchTags()

      // Fetch first page of transactions
      await fetchCurrentPage()

      await nextTick()
      syncHeaderHeight()
    } else if (!newVisible) {
      currentPage.value = 1
      exitEditMode()
      reset()
      resetTransactionTags()
    }
  },
  { immediate: true }
)

let resizeTimeout: number | undefined
const handleResize = () => {
  window.clearTimeout(resizeTimeout)
  resizeTimeout = window.setTimeout(async () => {
    const previousSize = pageSize.value
    syncPageSize()

    if (props.visible && props.statement && pageSize.value !== previousSize) {
      currentPage.value = 1
      await fetchCurrentPage()
      await nextTick()
      syncHeaderHeight()
    }
  }, 150)
}

let headerResizeObserver: ResizeObserver | null = null

onMounted(() => {
  syncPageSize()
  window.addEventListener('resize', handleResize, { passive: true })

  if (typeof ResizeObserver !== 'undefined') {
    headerResizeObserver = new ResizeObserver(() => syncHeaderHeight())
    if (theadRef.value) headerResizeObserver.observe(theadRef.value)
  }
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  headerResizeObserver?.disconnect()
})

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
  const start = parseDateString(props.statement.period_start)
  const end = parseDateString(props.statement.period_end)

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
  const date = parseDateString(dateStr)
  return date.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })
}

const formatTransactionDate = (dateStr: string): string => {
  const date = parseDateString(dateStr)
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

const fetchCurrentPage = async () => {
  if (!props.statement) return

  await fetchTransactions(props.statement.id, {
    skip: (currentPage.value - 1) * pageSize.value,
    limit: pageSize.value,
  })

  const transactionIds = transactions.value.map((t) => t.id)
  await fetchTagsForTransactions(transactionIds)
}

const goToPage = async (page: number) => {
  if (page < 1 || page > totalPages.value) return
  currentPage.value = page
  await fetchCurrentPage()
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
  fetchCurrentPage()
}

// Edit mode functions
const enterEditMode = () => {
  if (!props.statement) return

  // Initialize edited statement with current values
  editedStatement.value = {
    due_date: props.statement.due_date,
    close_date: props.statement.close_date,
    period_start: props.statement.period_start,
    period_end: props.statement.period_end,
    previous_balance: props.statement.previous_balance,
    current_balance: props.statement.current_balance,
    minimum_payment: props.statement.minimum_payment,
    is_fully_paid: props.statement.is_fully_paid,
  }

  // Initialize empty transaction edits
  editedTransactions.value = new Map()
  deletedTransactionIds.value = new Set()

  isEditMode.value = true
  saveError.value = null
}

const exitEditMode = () => {
  isEditMode.value = false
  editedStatement.value = null
  editedTransactions.value = new Map()
  deletedTransactionIds.value = new Set()
  newTransactions.value = []
  saveError.value = null
}

// Event handlers
const handleClose = () => {
  if (isEditMode.value) {
    // Discard unsaved changes and exit edit mode
    exitEditMode()
  }
  internalVisible.value = false
}

const handlePay = () => {
  if (props.statement) {
    emit('pay', props.statement)
  }
}

const handleSave = async () => {
  if (!props.statement) return

  // Validate form before saving
  if (!isFormValid.value) {
    saveError.value = new Error('Please fix all validation errors before saving')
    return
  }

  isSaving.value = true
  saveError.value = null

  try {
    // Save statement updates if any
    if (editedStatement.value) {
      const updatedStatement = await updateStatementApi(props.statement.id, editedStatement.value)
      emit('statement-updated', updatedStatement)
    }

    // Save transaction updates
    const updatePromises: Promise<unknown>[] = []

    editedTransactions.value.forEach((updateData, transactionId) => {
      updatePromises.push(updateTransaction(transactionId, updateData))
    })

    // Delete marked transactions
    deletedTransactionIds.value.forEach((transactionId) => {
      updatePromises.push(deleteTransaction(transactionId))
    })

    // Create new transactions
    newTransactions.value.forEach((newTxn) => {
      const { _tempId, ...txnData } = newTxn
      void _tempId // Explicitly ignore unused variable
      updatePromises.push(
        createTransaction({
          ...txnData,
          statement_id: props.statement!.id,
        })
      )
    })

    await Promise.all(updatePromises)

    // Refresh data and exit edit mode
    await fetchCurrentPage()
    exitEditMode()
  } catch (e) {
    saveError.value = e instanceof Error ? e : new Error('Failed to save changes')
    console.error('Error saving changes:', e)
  } finally {
    isSaving.value = false
  }
}

const handleCancel = () => {
  exitEditMode()
}
</script>

<template>
  <Dialog
    v-model:visible="internalVisible"
    modal
    :style="{ width: '850px' }"
    :breakpoints="{ '1024px': '90vw', '768px': '95vw' }"
    :closable="false"
    :draggable="false"
    :dismissableMask="true"
    :class="{ 'edit-mode': isEditMode }"
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
      <!-- Save Error Message -->
      <Message v-if="saveError" severity="error" :closable="true" class="save-error" @close="saveError = null">
        {{ saveError.message }}
      </Message>

      <!-- Saving Overlay -->
      <div v-if="isSaving" class="saving-overlay">
        <i class="pi pi-spin pi-spinner" style="font-size: 2rem"></i>
        <span>Saving changes...</span>
      </div>
      <!-- Summary Section -->
      <section class="summary-section">
        <h3 class="section-title">Statement Summary</h3>
        <div class="summary-grid">
          <div class="summary-item">
            <p class="summary-label">Previous Balance</p>
            <p v-if="!isEditMode" class="summary-value">{{ formatCurrency(statement.previous_balance) }}</p>
            <InputNumber
              v-else
              v-model="editedStatement!.previous_balance"
              :min="0"
              mode="currency"
              currency="USD"
              locale="en-US"
              :maxFractionDigits="2"
              :disabled="isSaving"
              class="summary-input"
              :class="{ 'p-invalid': validationErrors.previous_balance }"
            />
            <small v-if="isEditMode && validationErrors.previous_balance" class="p-error">{{ validationErrors.previous_balance }}</small>
          </div>

          <div class="summary-item summary-item--highlight">
            <p class="summary-label">Current Balance</p>
            <p v-if="!isEditMode" class="summary-value">{{ formatCurrency(statement.current_balance) }}</p>
            <InputNumber
              v-else
              v-model="editedStatement!.current_balance"
              :min="0"
              mode="currency"
              currency="USD"
              locale="en-US"
              :maxFractionDigits="2"
              :disabled="isSaving"
              class="summary-input"
              :class="{ 'p-invalid': validationErrors.current_balance }"
            />
            <small v-if="isEditMode && validationErrors.current_balance" class="p-error">{{ validationErrors.current_balance }}</small>
          </div>

          <div class="summary-item">
            <p class="summary-label">Minimum Payment</p>
            <p v-if="!isEditMode" class="summary-value">{{ formatCurrency(statement.minimum_payment) }}</p>
            <InputNumber
              v-else
              v-model="editedStatement!.minimum_payment"
              :min="0"
              mode="currency"
              currency="USD"
              locale="en-US"
              :maxFractionDigits="2"
              :disabled="isSaving"
              class="summary-input"
              :class="{ 'p-invalid': validationErrors.minimum_payment }"
            />
            <small v-if="isEditMode && validationErrors.minimum_payment" class="p-error">{{ validationErrors.minimum_payment }}</small>
          </div>

          <div class="summary-item">
            <p class="summary-label">Due Date</p>
            <p v-if="!isEditMode" class="summary-value">{{ formatDate(statement.due_date) }}</p>
            <DatePicker
              v-else
              v-model="dueDateModel"
              dateFormat="yy-mm-dd"
              showIcon
              placeholder="Select date"
              :disabled="isSaving"
              class="summary-input"
              :class="{ 'p-invalid': validationErrors.due_date }"
            />
            <small v-if="isEditMode && validationErrors.due_date" class="p-error">{{ validationErrors.due_date }}</small>
          </div>

          <div class="summary-item">
            <p class="summary-label">Close Date</p>
            <p v-if="!isEditMode" class="summary-value">{{ formatDate(statement.close_date) }}</p>
            <DatePicker
              v-else
              v-model="closeDateModel"
              dateFormat="yy-mm-dd"
              showIcon
              placeholder="Select date"
              :disabled="isSaving"
              class="summary-input"
            />
          </div>

          <div class="summary-item">
            <p class="summary-label">Period Start</p>
            <p v-if="!isEditMode" class="summary-value">{{ formatDate(statement.period_start) }}</p>
            <DatePicker
              v-else
              v-model="periodStartModel"
              dateFormat="yy-mm-dd"
              showIcon
              placeholder="Select date"
              :disabled="isSaving"
              class="summary-input"
            />
          </div>

          <div class="summary-item">
            <p class="summary-label">Period End</p>
            <p v-if="!isEditMode" class="summary-value">{{ formatDate(statement.period_end) }}</p>
            <DatePicker
              v-else
              v-model="periodEndModel"
              dateFormat="yy-mm-dd"
              showIcon
              placeholder="Select date"
              :disabled="isSaving"
              class="summary-input"
              :class="{ 'p-invalid': validationErrors.period_end }"
            />
            <small v-if="isEditMode && validationErrors.period_end" class="p-error">{{ validationErrors.period_end }}</small>
          </div>

          <div class="summary-item">
            <p class="summary-label">Fully Paid</p>
            <p v-if="!isEditMode" class="summary-value">{{ statement.is_fully_paid ? 'Yes' : 'No' }}</p>
            <div v-else class="summary-checkbox">
              <Checkbox v-model="editedStatement!.is_fully_paid" binary :inputId="'fully-paid-checkbox'" :disabled="isSaving" />
              <label :for="'fully-paid-checkbox'" class="checkbox-label">{{ editedStatement!.is_fully_paid ? 'Yes' : 'No' }}</label>
            </div>
          </div>
        </div>
      </section>

      <!-- Transactions Section -->
      <section class="transactions-section">
        <h3 class="section-title">Transactions</h3>

        <!-- Loading State -->
        <div
          v-if="isLoading && transactions.length === 0 && !error"
          class="loading-state"
          role="status"
          aria-live="polite"
          aria-label="Loading transactions"
        >
          <div class="spinner"></div>
          <p>Loading transactions...</p>
        </div>

        <!-- Error State -->
        <div v-else-if="error && transactions.length === 0" class="error-state" role="alert">
          <i class="pi pi-exclamation-circle"></i>
          <p>Failed to load transactions</p>
          <Button label="Retry" size="small" severity="secondary" @click="handleRetry" />
        </div>

        <!-- Empty State -->
        <div v-else-if="!isLoading && !error && transactions.length === 0" class="empty-state">
          <i class="pi pi-inbox"></i>
          <p>No transactions for this statement</p>
        </div>

        <!-- Transactions Table -->
        <div v-else :aria-busy="isLoading ? 'true' : 'false'">
          <div v-if="error" class="inline-error" role="alert">
            <i class="pi pi-exclamation-circle"></i>
            <span>Failed to refresh transactions</span>
            <Button label="Retry" size="small" severity="secondary" text @click="handleRetry" />
          </div>

          <div class="table-wrapper" :style="{ '--table-header-height': `${tableHeaderHeight}px` }">
            <div v-if="isLoading" class="table-loading-overlay" aria-hidden="true">
              <div class="spinner spinner--sm"></div>
            </div>
          <table class="transactions-table">
             <thead ref="theadRef">
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
                 <th>Currency</th>
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
                 <th v-if="isEditMode">Actions</th>
               </tr>
             </thead>
            <tbody>
               <tr
                 v-for="item in (isEditMode ? allTransactions : sortedTransactions)"
                 :key="isNewTransaction(item) ? item._tempId : item.id"
                 :class="{ 'transaction-deleted': !isNewTransaction(item) && isTransactionDeleted(item.id) }"
               >
                  <!-- Date column -->
                  <td v-if="!isEditMode">{{ formatTransactionDate(item.txn_date) }}</td>
                  <td v-else-if="isNewTransaction(item)">
                    <div class="table-input-wrapper">
                      <DatePicker
                        :model-value="getNewTransactionDateModel(item._tempId).value"
                        @update:model-value="(value: Date | Date[] | (Date | null)[] | null | undefined) => handleNewTransactionDateUpdate(item._tempId, value)"
                        dateFormat="yy-mm-dd"
                        showIcon
                        :disabled="isSaving"
                        class="table-input"
                        :class="{ 'p-invalid': hasTransactionFieldError(item._tempId, 'txn_date') }"
                      />
                      <small v-if="hasTransactionFieldError(item._tempId, 'txn_date')" class="p-error">{{ getTransactionFieldError(item._tempId, 'txn_date') }}</small>
                    </div>
                  </td>
                 <td v-else>
                   <DatePicker
                     :model-value="getTransactionDateModel(item).value"
                     @update:model-value="(value: Date | Date[] | (Date | null)[] | null | undefined) => handleDateUpdate(item.id, value)"
                     dateFormat="yy-mm-dd"
                     showIcon
                     :disabled="isSaving || isTransactionDeleted(item.id)"
                     class="table-input"
                   />
                 </td>

                   <!-- Payee column -->
                   <td v-if="!isEditMode" class="text-truncate payee-cell" :title="item.payee">{{ item.payee }}</td>
                   <td v-else-if="isNewTransaction(item)">
                     <div class="table-input-wrapper">
                       <InputText
                         :model-value="item.payee"
                         @update:model-value="(val: string | undefined) => updateNewTransactionValue(item._tempId, 'payee', val)"
                         :disabled="isSaving"
                         class="table-input"
                         :class="{ 'p-invalid': hasTransactionFieldError(item._tempId, 'payee') }"
                       />
                       <small v-if="hasTransactionFieldError(item._tempId, 'payee')" class="p-error">{{ getTransactionFieldError(item._tempId, 'payee') }}</small>
                     </div>
                   </td>
                 <td v-else>
                   <InputText
                     :model-value="getTransactionValue(item, 'payee')"
                     @update:model-value="(val: string | undefined) => handleTextUpdate(item.id, 'payee', val)"
                     :disabled="isSaving || isTransactionDeleted(item.id)"
                     class="table-input"
                   />
                 </td>

                   <!-- Description column -->
                   <td v-if="!isEditMode" class="text-truncate description-cell" :title="item.description">{{ item.description }}</td>
                   <td v-else-if="isNewTransaction(item)">
                     <div class="table-input-wrapper">
                       <InputText
                         :model-value="item.description"
                         @update:model-value="(val: string | undefined) => updateNewTransactionValue(item._tempId, 'description', val)"
                         :disabled="isSaving"
                         class="table-input"
                         :class="{ 'p-invalid': hasTransactionFieldError(item._tempId, 'description') }"
                       />
                       <small v-if="hasTransactionFieldError(item._tempId, 'description')" class="p-error">{{ getTransactionFieldError(item._tempId, 'description') }}</small>
                     </div>
                   </td>
                 <td v-else>
                   <InputText
                     :model-value="getTransactionValue(item, 'description')"
                     @update:model-value="(val: string | undefined) => handleTextUpdate(item.id, 'description', val)"
                     :disabled="isSaving || isTransactionDeleted(item.id)"
                     class="table-input"
                   />
                 </td>

                  <!-- Currency column -->
                  <td v-if="!isEditMode">{{ item.currency }}</td>
                  <td v-else-if="isNewTransaction(item)">
                    <div class="table-input-wrapper">
                      <Dropdown
                        :model-value="item.currency"
                        @update:model-value="(val: string) => updateNewTransactionValue(item._tempId, 'currency', val)"
                        :options="currencyOptions"
                        option-label="label"
                        option-value="value"
                        :disabled="isSaving"
                        class="table-input"
                        :class="{ 'p-invalid': hasTransactionFieldError(item._tempId, 'currency') }"
                      />
                      <small v-if="hasTransactionFieldError(item._tempId, 'currency')" class="p-error">{{ getTransactionFieldError(item._tempId, 'currency') }}</small>
                    </div>
                  </td>
                 <td v-else>
                   <Dropdown
                     :model-value="getTransactionValue(item, 'currency')"
                     @update:model-value="(val: string) => setTransactionValue(item.id, 'currency', val)"
                     :options="currencyOptions"
                     option-label="label"
                     option-value="value"
                     :disabled="isSaving || isTransactionDeleted(item.id)"
                     class="table-input"
                   />
                 </td>

                  <!-- Amount column -->
                  <td v-if="!isEditMode" :class="item.amount < 0 ? 'amount--negative' : 'amount--positive'">
                    {{ formatCurrency(item.amount) }}
                  </td>
                  <td v-else-if="isNewTransaction(item)">
                    <div class="table-input-wrapper">
                      <InputNumber
                        :model-value="item.amount"
                        @update:model-value="(val: number | null) => updateNewTransactionValue(item._tempId, 'amount', val ?? 0)"
                        :disabled="isSaving"
                        class="table-input"
                        :class="{ 'p-invalid': hasTransactionFieldError(item._tempId, 'amount') }"
                      />
                      <small v-if="hasTransactionFieldError(item._tempId, 'amount')" class="p-error">{{ getTransactionFieldError(item._tempId, 'amount') }}</small>
                    </div>
                  </td>
                 <td v-else>
                   <InputNumber
                     :model-value="getTransactionValue(item, 'amount')"
                     @update:model-value="(val: number | null) => setTransactionValue(item.id, 'amount', val ?? 0)"
                     :disabled="isSaving || isTransactionDeleted(item.id)"
                     class="table-input"
                   />
                 </td>

                 <!-- Installments column (read-only in both modes for now) -->
                 <td class="installments">{{ formatInstallments(item.installment_cur, item.installment_tot) }}</td>

                 <!-- Tags column (read-only, only for existing transactions) -->
                 <td v-if="!isEditMode && !isNewTransaction(item)" class="tags">
                   <template v-if="getTagsForTransaction(item.id).length > 0">
                     <span
                       v-for="tag in getTagsForTransaction(item.id)"
                       :key="tag.tag_id"
                       class="tag-chip"
                     >
                       {{ tag.label }}
                     </span>
                   </template>
                   <template v-else>-</template>
                 </td>
                 <td v-else>-</td>

                 <!-- Actions column (edit mode only) -->
                 <td v-if="isEditMode" class="actions-cell">
                   <!-- New transaction: show Remove button -->
                   <Button
                     v-if="isNewTransaction(item)"
                     icon="pi pi-times"
                     severity="danger"
                     text
                     size="small"
                     :disabled="isSaving"
                     @click="removeNewTransaction(item._tempId)"
                     aria-label="Remove new transaction"
                   />
                   <!-- Existing transaction: show Delete/Restore button -->
                   <Button
                     v-else-if="!isTransactionDeleted(item.id)"
                     icon="pi pi-trash"
                     severity="danger"
                     text
                     size="small"
                     :disabled="isSaving"
                     @click="toggleTransactionDeleted(item.id)"
                     aria-label="Delete transaction"
                   />
                   <Button
                     v-else
                     icon="pi pi-undo"
                     severity="secondary"
                     text
                     size="small"
                     :disabled="isSaving"
                     @click="toggleTransactionDeleted(item.id)"
                     aria-label="Restore transaction"
                   />
                 </td>
               </tr>
              <tr
                v-for="index in placeholderRowCount"
                :key="`placeholder-${index}`"
                class="placeholder-row"
                aria-hidden="true"
              >
                <td v-for="col in (isEditMode ? 8 : 7)" :key="col">&nbsp;</td>
              </tr>
         </tbody>
       </table>
          </div>
        </div>
      </section>
    </div>

    <template #footer>
      <div v-if="statement" class="modal-footer">
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

        <div class="footer-actions">
          <!-- View mode buttons -->
          <template v-if="!isEditMode">
            <Button
              label="Pay"
              icon="pi pi-credit-card"
              :disabled="statement.is_fully_paid"
              @click="handlePay"
              severity="primary"
            />
            <Button
              label="Edit"
              icon="pi pi-pencil"
              @click="enterEditMode"
              severity="primary"
              outlined
            />
            <Button
              label="Close"
              icon="pi pi-times"
              @click="handleClose"
              severity="secondary"
              outlined
            />
          </template>

          <!-- Edit mode buttons -->
          <template v-else>
            <Button
              label="Add Transaction"
              icon="pi pi-plus"
              :disabled="isSaving"
              @click="addNewTransaction"
              severity="secondary"
              outlined
            />
            <Button
              label="Save"
              icon="pi pi-check"
              :loading="isSaving"
              :disabled="!isFormValid || isSaving"
              @click="handleSave"
              severity="primary"
            />
            <Button
              label="Cancel"
              icon="pi pi-times"
              :disabled="isSaving"
              @click="handleCancel"
              severity="secondary"
              outlined
            />
          </template>
        </div>
      </div>
    </template>
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
  position: relative;
}

.save-error {
  margin-bottom: 0;
}

.saving-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.8);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  z-index: 10;
  color: var(--text-color-secondary);
}

.saving-overlay span {
  font-size: 0.938rem;
  font-weight: 500;
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

.summary-input {
  width: 100%;
  margin-top: 0.25rem;
}

.summary-checkbox {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 0.25rem;
}

.checkbox-label {
  font-size: 1rem;
  color: var(--text-color);
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

.summary-item small.p-error {
  display: block;
  margin-top: 0.25rem;
  font-size: 0.75rem;
  color: var(--red-500);
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
.table-wrapper {
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  position: relative;
}

.table-loading-overlay {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  top: var(--table-header-height, 0px);
  background: color-mix(in srgb, var(--surface-0) 65%, transparent);
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: none;
}

.spinner--sm {
  width: 28px;
  height: 28px;
  border-width: 2px;
}

.inline-error {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  border: 1px solid var(--red-200);
  background: var(--red-50);
  color: var(--red-700);
  border-radius: 8px;
  margin-bottom: 0.75rem;
}

.inline-error i {
  color: var(--red-500);
}

.transactions-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.938rem;
  min-width: 700px;
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

.placeholder-row td {
  color: transparent;
  pointer-events: none;
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
  align-items: center;
  gap: 1rem;
  flex: 1;
  min-width: 0;
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

/* Transaction edit styles */
.transaction-deleted {
  opacity: 0.5;
  text-decoration: line-through;
  background: var(--surface-100);
}

.table-input {
  width: 100%;
  min-width: 100px;
}

.table-input-wrapper {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  width: 100%;
}

.table-input-wrapper small.p-error {
  font-size: 0.7rem;
  color: var(--red-500);
  margin: 0;
  line-height: 1.2;
}

.actions-cell {
  text-align: center;
}

.modal-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
}

.footer-actions {
  display: flex;
  gap: 0.75rem;
  justify-content: flex-end;
  flex-shrink: 0;
}

/* Responsive design */
@media (max-width: 1024px) {
  .summary-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .summary-item:last-child {
    grid-column: span 2;
  }
}

@media (max-width: 768px) {
  .modal-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }

  .modal-footer {
    flex-direction: column;
    align-items: stretch;
  }

  .pagination {
    justify-content: center;
  }

  .footer-actions {
    flex-direction: column;
  }

  .footer-actions .p-button {
    width: 100%;
  }
}

@media (max-width: 480px) {
  .summary-grid {
    grid-template-columns: 1fr;
  }

  .summary-item:last-child {
    grid-column: auto;
  }
}
</style>
