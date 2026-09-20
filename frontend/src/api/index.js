import axios from 'axios'
import { templates, reportList, pickResult } from '@/mock/data'

/* 联调开关：接 A 的真实后端时改成 false，页面代码一行都不用动 */
const USE_MOCK = true

const http = axios.create({
  baseURL: '/api',
  timeout: 120000
})

http.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const message = error?.response?.data?.detail || error.message || '请求失败，请稍后重试'
    return Promise.reject(new Error(message))
  }
)

function mockDelay(data, ms = 400) {
  return new Promise((resolve) => setTimeout(() => resolve(data), ms))
}

/* Mock 轮询计数：同一份报告前 2 次查询返回 grading，第 3 次起返回 done */
const pollCounter = new Map()

export function fetchTemplates() {
  return USE_MOCK ? mockDelay({ list: templates }) : http.get('/templates')
}

export function uploadReport({ file, templateId }) {
  if (USE_MOCK) {
    const reportId = Math.floor(Math.random() * 900) + 100
    pollCounter.set(reportId, 0)
    return mockDelay(
      { report_id: reportId, task_id: `t_${reportId}`, status: 'grading' },
      600
    )
  }
  const form = new FormData()
  form.append('file', file)
  form.append('template_id', templateId)
  return http.post('/reports', form, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export function fetchReportStatus(reportId) {
  if (USE_MOCK) {
    const count = (pollCounter.get(Number(reportId)) || 0) + 1
    pollCounter.set(Number(reportId), count)
    const done = count >= 3
    return mockDelay(
      {
        report_id: Number(reportId),
        status: done ? 'done' : 'grading',
        progress: done ? 100 : Math.min(count * 30, 90)
      },
      300
    )
  }
  return http.get(`/reports/${reportId}/status`)
}

export function fetchReportResult(reportId) {
  return USE_MOCK
    ? mockDelay(pickResult(Number(reportId)), 500)
    : http.get(`/reports/${reportId}/result`)
}

export function fetchReports({ page = 1, size = 10, keyword = '', templateName = '' } = {}) {
  if (USE_MOCK) {
    const filtered = reportList.filter((item) => {
      const matchKeyword =
        !keyword ||
        item.student.includes(keyword) ||
        item.file_name.includes(keyword)
      const matchTemplate = !templateName || item.template_name === templateName
      return matchKeyword && matchTemplate
    })
    const start = (page - 1) * size
    return mockDelay({
      total: filtered.length,
      list: filtered.slice(start, start + size)
    })
  }
  return http.get('/reports', { params: { page, size, keyword, template_name: templateName } })
}
