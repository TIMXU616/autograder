import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', redirect: '/upload' },
  {
    path: '/upload',
    name: 'upload',
    component: () => import('@/views/UploadView.vue'),
    meta: { title: '上传报告' }
  },
  {
    path: '/result/:id',
    name: 'result',
    component: () => import('@/views/ResultView.vue'),
    meta: { title: '评阅结果' }
  },
  {
    path: '/reports',
    name: 'reports',
    component: () => import('@/views/ReportsView.vue'),
    meta: { title: '成绩管理' }
  },
  {
    path: '/templates',
    name: 'templates',
    component: () => import('@/views/TemplatesView.vue'),
    meta: { title: '评分模板' }
  },
  { path: '/:pathMatch(.*)*', redirect: '/upload' }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.afterEach((to) => {
  document.title = to.meta.title ? `${to.meta.title} · AutoGrader` : 'AutoGrader'
})

export default router
