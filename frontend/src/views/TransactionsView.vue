<script setup lang="ts">
import TransactionList from '@/components/transactions/TransactionList.vue'
</script>

<template>
  <div class="transactions-view">
    <h1 class="text-3xl font-bold mb-6 text-gray-800">Transactions</h1>
    <TransactionList />
  </div>
</template>

<style scoped>
.transactions-view {
  padding: 32px; /* Adjusted padding */
  max-width: 1400px;
  margin: 0 auto;
}
</style>

