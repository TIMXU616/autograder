import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

/* 代理目标可用环境变量切换，前端代码里的 baseURL 保持相对的 '/api/v1' 不动：
     · 默认打本机后端：        npm run dev
     · 切 A 的公网后端：       VITE_API_TARGET=https://autograder-api.app.workbuddy.host npm run dev

   为什么必须走代理、不能把 baseURL 直接写成对方域名：
   该公网服务没有开启 CORS（响应里没有 Access-Control-Allow-Origin，
   OPTIONS 预检直接返回 405），浏览器跨域调用会被拦下来。
   走 vite 代理时浏览器只与自己的源通信，不触发 CORS；生产环境同理，
   由 nginx 把 /api/ 反代到后端即可。 */
const API_TARGET = process.env.VITE_API_TARGET || 'http://localhost:8000'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: API_TARGET,
        changeOrigin: true
      }
    }
  }
})
