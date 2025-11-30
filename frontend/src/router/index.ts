import { createRouter, createWebHistory } from 'vue-router'
import StatementsView from '../views/StatementsView.vue'
import { useAuthStore } from '../stores/auth'

// Import layouts
import DefaultLayout from '@/layouts/DefaultLayout.vue'
import AuthLayout from '@/layouts/AuthLayout.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      component: DefaultLayout, // Parent layout for authenticated routes
      meta: { requiresAuth: true },
      children: [
        {
          path: '', // Default child route for '/'
          name: 'home',
          component: StatementsView,
        },
        {
          path: 'analytics',
          name: 'analytics',
          component: () => import('../views/AnalyticsView.vue'),
        },
        {
          path: 'transactions',
          name: 'transactions',
          component: () => import('../views/TransactionsView.vue'),
        },
        {
          path: 'about',
          name: 'about',
          component: () => import('../views/AboutView.vue'),
        },
        // Add other authenticated routes here as children of DefaultLayout
        {
          path: 'balance-sheet',
          name: 'balance-sheet',
          component: () => import('../views/AboutView.vue'),
        },
        {
          path: 'monthly-overview',
          name: 'monthly-overview',
          component: () => import('../views/AboutView.vue'),
        },
        {
          path: 'reports',
          name: 'reports',
          component: () => import('../views/AboutView.vue'),
        },
        {
          path: 'queries',
          name: 'queries',
          component: () => import('../views/AboutView.vue'),
        },
        {
          path: 'investment-performance',
          name: 'investment-performance',
          component: () => import('../views/AboutView.vue'),
        },
        {
          path: 'fire-simulations',
          name: 'fire-simulations',
          component: () => import('../views/AboutView.vue'),
        },
        {
          path: 'data-sync',
          name: 'data-sync',
          component: () => import('../views/AboutView.vue'),
        },
        {
          path: 'preferences',
          name: 'preferences',
          component: () => import('../views/AboutView.vue'),
        },
      ],
    },
    {
      path: '/auth/login',
      name: 'login',
      component: AuthLayout,
      meta: { guest: true },
    },
    {
      path: '/auth/signup',
      name: 'signup',
      component: AuthLayout,
      meta: { guest: true },
    },
  ],
})

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()

  // Check if the route or any matched parent requires authentication
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth)
  // Check if the route or any matched parent is for guests only
  const guestOnly = to.matched.some(record => record.meta.guest)

  if (requiresAuth && !authStore.isAuthenticated) {
    // Redirect to login page if not authenticated
    next({ name: 'login', query: { redirect: to.fullPath } })
  } 
  else if (guestOnly && authStore.isAuthenticated) {
    // Redirect to home if already authenticated and trying to access a guest route
    next({ name: 'home' })
  } 
  else {
    next()
  }
})

export default router
