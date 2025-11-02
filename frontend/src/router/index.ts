import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import LoginView from '../views/LoginView.vue'
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
          component: HomeView,
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
          component: HomeView,
        },
        {
          path: 'monthly-overview',
          name: 'monthly-overview',
          component: HomeView,
        },
        {
          path: 'reports',
          name: 'reports',
          component: HomeView,
        },
        {
          path: 'queries',
          name: 'queries',
          component: HomeView,
        },
        {
          path: 'investment-performance',
          name: 'investment-performance',
          component: HomeView,
        },
        {
          path: 'fire-simulations',
          name: 'fire-simulations',
          component: HomeView,
        },
        {
          path: 'data-sync',
          name: 'data-sync',
          component: HomeView,
        },
        {
          path: 'preferences',
          name: 'preferences',
          component: HomeView,
        },
      ],
    },
    {
      path: '/auth',
      component: AuthLayout,
      children: [
        {
          path: 'login',
          name: 'login',
          component: LoginView,
          meta: { guest: true },
        },
        {
          path: 'signup',
          name: 'signup',
          component: () => import('../views/SignUpView.vue'),
          meta: { guest: true },
        },
      ]
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
