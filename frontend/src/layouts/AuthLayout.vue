<script setup lang="ts">
// Auth layout for login, signup, etc.
</script>

<template>
  <div class="auth-layout">
    <div class="auth-container">
      <div class="auth-logo">
        <img src="@/assets/logo.svg" alt="FindDash Logo" />
      </div>
      
      <div class="auth-content">
        <router-view></router-view> <!-- Slot for the actual view -->
      </div>
    </div>
  </div>
</template>

<style scoped>
.auth-layout {
  height: 100vh;
  width: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: var(--surface-ground);
}

.auth-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  max-width: 420px;
  width: 100%;
  padding: 1rem;
}

.auth-logo img {
  height: 60px;
  width: auto;
}

.auth-content {
  width: 100%;
  display: flex;
  justify-content: center;
}
</style>
