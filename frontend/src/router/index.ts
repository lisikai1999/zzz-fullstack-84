import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'projects',
      component: () => import('../views/ProjectList.vue'),
    },
    {
      path: '/project/:id',
      name: 'editor',
      component: () => import('../views/Editor.vue'),
    },
  ],
})

export default router
