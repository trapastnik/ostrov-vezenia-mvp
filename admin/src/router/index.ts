import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('../pages/LoginPage.vue'),
    },
    {
      path: '/',
      component: () => import('../layouts/DefaultLayout.vue'),
      meta: { requiresAuth: true },
      children: [
        { path: '', name: 'dashboard', component: () => import('../pages/DashboardPage.vue') },
        { path: 'orders', name: 'orders', component: () => import('../pages/OrdersListPage.vue') },
        { path: 'orders/:id', name: 'order-detail', component: () => import('../pages/OrderDetailPage.vue') },
        { path: 'batches', name: 'batches', component: () => import('../pages/BatchesListPage.vue') },
        { path: 'shops', name: 'shops', component: () => import('../pages/ShopsListPage.vue') },
        { path: 'shops/:id', name: 'shop-detail', component: () => import('../pages/ShopDetailPage.vue') },
        { path: 'pochta', name: 'pochta', component: () => import('../pages/PochtaTestPage.vue') },
      ],
    },
  ],
})

router.beforeEach((to) => {
  const token = localStorage.getItem('token')
  if (to.meta.requiresAuth && !token) {
    return { name: 'login' }
  }
  if (to.name === 'login' && token) {
    return { name: 'dashboard' }
  }
})

export default router
