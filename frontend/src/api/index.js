import axios from 'axios'
import {
  mockQueryTemplates,
  mockUpload,
  mockTrigger,
  mockPoll,
  mockQueryGrades
} from '@/mock/data'

/* ============================================================================
   AutoGrader 前端接口层（契约适配器）
   契约依据：docs/interface-contract-v1.md  v1.0（2026-09-21 冻结）

   为什么要「适配」而不是页面直连：
     · 契约层（A 的后端）用 snake_case：max_score / filename / finished_at …
     · 页面层（4 个 .vue）用视图字段：full_score / file_name / created_at …
   中间加一层转换后，契约再微调（A 补字段、改命名）只改本文件，
   4 个页面的模板与逻辑不动 —— 这是联调期不返工的关键。

   USE_MOCK = true 时，Mock 返回的也是「契约形状」，走同一条适配路径，
   因此联调当天只需要把下面这一个开关改成 false。

   2026-09-22 联调：后端 backend/ 已按契约 v1 落地，本开关已置为 false。
   想回到纯前端 Mock（后端没起时看页面）把它改回 true 即可。
   ============================================================================ */

const USE_MOCK = false

/* 契约 7.x 的接口前缀 */
const PREFIX = '/api/v1'

const http = axios.create({ baseURL: PREFIX, timeout: 130000 })

http.interceptors.response.use(
  (response) => response.data,
  (error) => Promise.reject(normalizeError(error))
)

/* ---------- 错误码 → 用户可读文案（契约第 6 节） ---------- */

const ERROR_TEXT = {
  4001: '仅支持 docx / pdf 格式',
  4002: '文件超过 20MB 上限',
  4003: '该 PDF 无文本层（扫描件），无法解析',
  4004: '文件为空，请重新上传',
  4005: 'PDF 已加密，无法解析',
  5001: '评分服务暂不可用，请稍后重试',
  5002: '评分超时，请重试',
  5003: '评分结果异常，请重试',
  5004: '评分额度不足',
  5005: '排队超时，请稍后重试',
  4041: '评分点模板不存在',
  4042: '报告不存在',
  4090: '报告正在解析，请稍候',
  4091: '该报告已存在或已完成评阅'
}

/* 错误归类（卡片1 要求「失败分三类」）：
     file    —— 文件或参数本身的问题，用户换文件 / 改参数即可解决
     network —— 连不上后端，环境问题，提示"后端服务是否已启动"
     server  —— 服务端处理失败（解析 / 模型 / 排队），只能重试，页面给「重新上传」

   注意 4003 / 4005 / 5001–5005 不会出现在上传响应里：契约规定它们是
   HTTP 200 + 任务置 failed，只能在轮询到 status==='failed' 时从 error_code 读到。 */
const ERROR_KIND = {
  3001: 'network',
  3002: 'network',
  4001: 'file',
  4002: 'file',
  4004: 'file',
  4041: 'file',
  4091: 'file',
  4003: 'server',
  4005: 'server',
  4042: 'server',
  4090: 'server',
  5001: 'server',
  5002: 'server',
  5003: 'server',
  5004: 'server',
  5005: 'server'
}

const KIND_TEXT = {
  file: '文件或参数问题',
  network: '网络问题',
  server: '服务端问题'
}

function fail(code, message, detail) {
  const err = new Error(message)
  err.code = code
  err.kind = ERROR_KIND[code] ?? 'server'
  err.kind_text = KIND_TEXT[err.kind]
  err.detail = detail ?? null
  return err
}

function normalizeError(error) {
  if (error?.code === 'ECONNABORTED') return fail(3001, '请求超时，请稍后重试')
  if (!error?.response) return fail(3002, '无法连接后端服务，请确认服务已启动')
  const body = error.response.data
  const code = body?.code
  return fail(code ?? error.response.status, ERROR_TEXT[code] || body?.message || '请求失败，请稍后重试', body?.detail)
}

/* ---------- 状态机文案（契约第 3 节） ---------- */

const IN_FLIGHT = ['uploaded', 'parsing', 'parsed', 'grading']
const TERMINAL = ['success', 'partial_success', 'failed']

const STAGE_TEXT = {
  uploaded: '已上传，待评阅',
  parsing: '正在解析报告正文与代码块…',
  parsed: '解析完成，准备逐项核查…',
  grading: '正在按评分点逐项核查…'
}

const LEVEL_TEXT = {
  excellent: '优秀',
  good: '良好',
  fair: '合格',
  weak: '待改进',
  absent: '缺失'
}

const LEVEL_TAG = {
  excellent: 'success',
  good: 'primary',
  fair: 'warning',
  weak: 'danger',
  absent: 'info'
}

const ITEM_STATUS_TEXT = {
  graded: '已评分',
  failed: '评分失败',
  low_confidence: '低置信',
  skipped: '已跳过'
}

const CONFIDENCE_TEXT = { high: '高', medium: '中', low: '低' }

/* ---------- 模板缓存：结果页/成绩页要用 template_name、full_score， ----------
   契约的 GradingResult 只给 template_id，这里统一从 ⑤ 接口的缓存里解析 */

let templateCache = null

async function ensureTemplates() {
  if (!templateCache) {
    const res = await fetchTemplates()
    templateCache = res.items
  }
  return templateCache
}

/* ---------- 字符串与时间的小工具 ---------- */

function fmtTime(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

/* 契约没有 student 字段，从文件名末段兜底推导（如 xxx_张三.docx → 张三） */
function studentFromFilename(filename) {
  if (!filename) return '—'
  const base = filename.replace(/\.(docx|pdf)$/i, '')
  const parts = base.split(/[_\-\s]/).filter(Boolean)
  const last = parts[parts.length - 1] || ''
  return parts.length > 1 && last.length <= 4 ? last : '—'
}

/* ============================================================================
   契约 → 页面 的适配函数
   ============================================================================ */

function adaptTemplate(t) {
  return {
    template_id: t.template_id,
    name: t.name,
    description: t.course,
    item_count: t.items?.length ?? 0,
    total_score: t.total_score,
    items: (t.items ?? []).map((i) => ({
      item_id: i.item_id,
      name: i.name,
      full_score: i.max_score
    }))
  }
}

function adaptItem(i) {
  const graded = i.score !== null && i.score !== undefined
  const rate = graded ? Math.round((i.score / i.max_score) * 100) : null
  return {
    item_id: i.item_id,
    name: i.name,
    score: i.score,
    full_score: i.max_score,
    rate,
    level: i.level,
    level_text: LEVEL_TEXT[i.level] ?? '',
    level_tag: LEVEL_TAG[i.level] ?? 'info',
    reason: i.reason,
    evidence: i.evidence,
    status: i.status,
    status_text: ITEM_STATUS_TEXT[i.status] ?? i.status,
    confidence: i.confidence,
    confidence_text: CONFIDENCE_TEXT[i.confidence] ?? '',
    error_code: i.error_code,
    error_text: i.error_code ? ERROR_TEXT[i.error_code] ?? '' : ''
  }
}

/* 契约的 GradingResult 不含总评/亮点/建议（已向 A 提 B1 请求补充）。
   在 A 补齐之前，这里由评分结果做**确定性汇总**，并在页面上标注来源，
   不用模型生成任何文案，避免出现"看起来像 AI 写的"假内容。 */
function deriveSummary(items, totalScore, fullScore) {
  const graded = items.filter((i) => i.status === 'graded')
  if (!graded.length || !fullScore) return { comment: '', highlights: [], suggestions: [] }

  const sorted = [...graded].sort((a, b) => b.rate - a.rate)
  const best = sorted[0]
  const worst = sorted[sorted.length - 1]
  const rate = Math.round((totalScore / fullScore) * 100)

  const comment =
    `本次共核查 ${items.length} 个评分点，已出分 ${graded.length} 项，总分 ${totalScore} / ${fullScore}（得分率 ${rate}%）。` +
    `表现最好的是「${best.name}」（得分率 ${best.rate}%）；` +
    (worst === best ? '各项水平接近。' : `最需要改进的是「${worst.name}」（得分率 ${worst.rate}%）。`)

  const highlights = sorted
    .filter((i) => ['excellent', 'good'].includes(i.level))
    .slice(0, 3)
    .map((i) => `${i.name}：${i.reason}`)

  const suggestions = [...sorted]
    .reverse()
    .filter((i) => ['fair', 'weak', 'absent'].includes(i.level))
    .slice(0, 3)
    .map((i) => `${i.name}：${i.reason}`)

  return { comment, highlights, suggestions }
}

function adaptResult(r, templateMap) {
  const items = (r.items ?? []).map(adaptItem)
  const tpl = templateMap?.get(r.template_id)
  const fullScore = items.length
    ? items.reduce((s, i) => s + i.full_score, 0)
    : tpl?.total_score ?? 0
  const totalScore = r.total_score ?? 0
  const derived = deriveSummary(items, totalScore, fullScore)

  /* 总评三件套的取值策略：整组同源。
     联调实测后端可能只给 comment、而 highlights / suggestions 返回空数组。
     若逐字段回落，会出现「评语来自模型、亮点来自前端推导，却统一标注
     summary_source:'model'」的错标。规则：三者任意非空 → 整组用后端值
     （空的板块如实显示「暂无」）；三者全空 → 整组用确定性汇总并标注 derived。 */
  const hasBackendSummary =
    Boolean(r.comment) || Boolean(r.highlights?.length) || Boolean(r.suggestions?.length)
  const useDerivedSummary = !hasBackendSummary

  return {
    report_id: r.report_id,
    file_name: r.filename,
    student: r.student ?? studentFromFilename(r.filename),
    template_id: r.template_id,
    template_name: r.template_name ?? tpl?.name ?? '—',
    status: r.status,
    in_flight: IN_FLIGHT.includes(r.status),
    is_failed: r.status === 'failed',
    is_partial: r.status === 'partial_success',
    stage_text: STAGE_TEXT[r.status] ?? '',
    total_score: totalScore,
    full_score: fullScore,
    score_rate: fullScore ? Math.round((totalScore / fullScore) * 100) : 0,
    comment: useDerivedSummary ? derived.comment : r.comment,
    highlights: useDerivedSummary ? derived.highlights : (r.highlights ?? []),
    suggestions: useDerivedSummary ? derived.suggestions : (r.suggestions ?? []),
    summary_source: useDerivedSummary ? 'derived' : 'model',
    warnings: r.warnings ?? [],
    consistency: r.consistency ?? null,
    error_code: r.error_code ?? null,
    error_text: r.error_code ? ERROR_TEXT[r.error_code] ?? '' : '',
    /* 轮询到 failed 时，页面靠这两个字段决定给「换文件」还是「重新上传」 */
    error_kind: r.error_code ? ERROR_KIND[r.error_code] ?? 'server' : null,
    error_kind_text: r.error_code ? KIND_TEXT[ERROR_KIND[r.error_code] ?? 'server'] : '',
    model: r.model,
    attempt_no: r.attempt_no,
    created_at: fmtTime(r.finished_at || r.grading_started_at),
    items
  }
}

function adaptGradeRow(row, templateMap) {
  const tpl = templateMap?.get(row.template_id)
  const fullScore = tpl?.total_score ?? 100
  return {
    report_id: row.report_id,
    file_name: row.filename,
    /* 后端给了 student 就用后端的（契约 v1 未定义该字段，属增补项，
       部分构建返回 null），没有才按文件名兜底 —— 与 adaptResult 的口径保持一致 */
    student: row.student || studentFromFilename(row.filename),
    template_id: row.template_id,
    template_name: row.template_name,
    status: row.status,
    total_score: row.total_score,
    full_score: fullScore,
    score_rate: fullScore ? Math.round((row.total_score / fullScore) * 100) : 0,
    created_at: fmtTime(row.finished_at)
  }
}

/* ============================================================================
   对外接口：页面只调用下面这些函数
   ============================================================================ */

/* ⑤ 评分点模板列表（契约 7.1） */
export async function fetchTemplates({ page = 1, page_size = 50, course = '' } = {}) {
  const raw = USE_MOCK
    ? mockQueryTemplates({ page, page_size, course })
    : await http.get('/templates', { params: { page, page_size, course } })
  return {
    total: raw.total,
    page: raw.page,
    page_size: raw.page_size,
    items: (raw.items ?? []).map(adaptTemplate)
  }
}

/* 幂等命中时按文件名反查 report_id。
   契约 4091 的标准响应体是 {"code":4091,"detail":{"report_id":"..."}}，
   但实测部分构建（如公网实例）的 detail 为 null；此时退化为在成绩列表里
   按文件名找 —— keyword 是契约增补参数（B2），已实测生效。
   找不到就返回 null，由调用方抛出可读提示，而不是把 4091 原样透给用户。 */
async function findReportIdByName(filename) {
  try {
    const res = await http.get('/grades', {
      params: { page: 1, page_size: 50, keyword: filename }
    })
    return (res.items ?? []).find((row) => row.filename === filename)?.report_id ?? null
  } catch {
    return null
  }
}

/* ① 上传报告：只落库，不触发解析（契约 7.2，成功 201）
   幂等冲突（4091）表示同一文件已上传过：复用已有 report_id 继续走触发流程，
   对用户表现为"该报告已存在，正在打开已有评阅结果"，不当作错误。 */
export async function uploadReport({ file, templateId }) {
  if (USE_MOCK) {
    const res = mockUpload({ filename: file.name, template_id: templateId })
    return { report_id: res.report_id, status: res.status }
  }
  const form = new FormData()
  form.append('file', file)
  form.append('template_id', templateId)
  try {
    return await http.post('/reports', form, { headers: { 'Content-Type': 'multipart/form-data' } })
  } catch (error) {
    if (error.code !== 4091) throw error
    const existing = error.detail?.report_id ?? (await findReportIdByName(file.name))
    if (existing) return { report_id: existing, status: 'uploaded', reused: true }
    throw fail(4091, '该报告已存在，请到「成绩列表」查看已有评阅结果')
  }
}

/* ② 触发评阅：驱动 parsing → grading 全链（契约 7.3，成功 202）
   已完成再触发返回 4091，视为"已评阅"，不当作错误 */
export async function triggerGrading(reportId) {
  if (USE_MOCK) {
    const res = mockTrigger(reportId)
    if (!res) throw fail(4042, ERROR_TEXT[4042])
    if (res.conflict) return { report_id: reportId, status: res.rec.status, attempt_no: res.rec.attempt_no, reused: true }
    return { report_id: reportId, status: res.rec.status, attempt_no: res.rec.attempt_no }
  }
  try {
    return await http.post(`/reports/${reportId}/grading`)
  } catch (error) {
    if (error.code === 4091) return { report_id: reportId, status: 'success', reused: true }
    throw error
  }
}

/* ③ 查询评阅结果：同时也是状态轮询口（契约 7.4） */
export async function fetchReportResult(reportId) {
  const templateMap = new Map((await ensureTemplates()).map((t) => [t.template_id, t]))
  if (USE_MOCK) {
    const raw = mockPoll(reportId)
    if (!raw) throw fail(4042, ERROR_TEXT[4042])
    return adaptResult(raw, templateMap)
  }
  const raw = await http.get(`/reports/${reportId}/result`)
  return adaptResult(raw, templateMap)
}

/* 轮询到终态：上传页用。onStage 回传当前阶段文案，便于页面展示进度 */
export function waitForResult(reportId, { onStage, interval = 2000, timeout = 180000 } = {}) {
  const startedAt = Date.now()
  return new Promise((resolve, reject) => {
    const tick = async () => {
      try {
        const result = await fetchReportResult(reportId)
        onStage?.(result)
        if (!result.in_flight) {
          resolve(result)
          return
        }
        if (Date.now() - startedAt > timeout) {
          reject(fail(5005, ERROR_TEXT[5005]))
          return
        }
        setTimeout(tick, interval)
      } catch (error) {
        reject(error)
      }
    }
    tick()
  })
}

/* ④ 成绩列表（契约 7.5）
   keyword 是已向 A 提出的补充项（contract-diff.md B2）；未实现时后端会忽略该参数，
   接口仍可用，只是搜索不生效 —— 联调时需确认 */
export async function fetchReports({ page = 1, size = 5, keyword = '', templateId = '', order = 'total_score_desc' } = {}) {
  const templateMap = new Map((await ensureTemplates()).map((t) => [t.template_id, t]))
  if (USE_MOCK) {
    const res = mockQueryGrades({ page, page_size: size, template_id: templateId, keyword, order })
    return { total: res.total, list: res.items.map((row) => adaptGradeRow(row, templateMap)) }
  }
  const res = await http.get('/grades', {
    params: { page, page_size: size, template_id: templateId || undefined, order, keyword: keyword || undefined }
  })
  return { total: res.total, list: res.items.map((row) => adaptGradeRow(row, templateMap)) }
}

/* ⑥ 报告原文与段落坐标（契约 7.6，增补接口，A 排期 2026-09-24 上线）

   ★ 三件"还没好"的事必须能区分，不能都当成功去渲染：
     a. 路由未注册     → 框架级 404，响应体 {"detail":"Not Found"}，**没有业务 code**
     b. 报告还在解析   → HTTP 200 + {"code":4090}（axios 判成功，必须自己看 body.code）
     c. 解析失败       → HTTP 200 + {"code":4003 / 4005}
   所以本函数返回统一形状 {ok, ...}，由页面决定降级展示，**自身不抛错**。 */
export async function fetchReportText(reportId) {
  if (USE_MOCK) return { ok: false, code: null, kind: 'server', message: 'Mock 模式下不提供原文定位' }
  try {
    const body = await http.get(`/reports/${reportId}/text`)
    /* 业务码走 HTTP 200 返回：axios 当成功，需自己判 body.code */
    if (body && typeof body.code === 'number') {
      return {
        ok: false,
        code: body.code,
        kind: ERROR_KIND[body.code] ?? 'server',
        message: ERROR_TEXT[body.code] ?? body.message ?? '原文暂不可用'
      }
    }
    return {
      ok: true,
      filename: body.filename,
      text: body.text ?? '',
      paragraphs: body.paragraphs ?? []
    }
  } catch (error) {
    /* code=404 → 框架级 404（路由不存在）；code=4042 → 业务「报告不存在」 */
    return {
      ok: false,
      code: error.code,
      kind: error.kind,
      message: error.code === 404
        ? '原文定位接口尚未上线（计划 9/24 上线）'
        : error.message
    }
  }
}

/* evidence → 原文偏移。容错顺序（实战必用，因为后端证据闸门是「去空白后」比对）：
     1) 原样 indexOf
     2) 失败 → 去掉所有空白后再匹配，再把归一化下标映射回原串下标
     3) 仍失败 → 返回 -1，由页面降级成「只显示引文」，绝不报错、绝不清空 */
const WS_RE = /\s+/g
const NON_WS_RE = /\S/

export function locateEvidence(text, evidence) {
  if (!text || !evidence) return -1
  const direct = text.indexOf(evidence)
  if (direct >= 0) return direct

  const compactText = text.replace(WS_RE, '')
  const compactEv = evidence.replace(WS_RE, '')
  if (!compactEv) return -1
  const at = compactText.indexOf(compactEv)
  if (at < 0) return -1

  let seen = 0
  for (let i = 0; i < text.length; i++) {
    if (NON_WS_RE.test(text[i])) {
      if (seen === at) return i
      seen += 1
    }
  }
  return -1
}

/* 取 evidence 在原文中的上下文片段，供「查看原文」抽屉展示 */
export function evidenceContext(text, evidence, span = 120) {
  const idx = locateEvidence(text, evidence)
  if (idx < 0) return null
  return {
    start: Math.max(0, idx - span),
    end: Math.min(text.length, idx + evidence.length + span),
    hit_start: idx,
    hit_end: idx + evidence.length,
    snippet: text.slice(Math.max(0, idx - span), Math.min(text.length, idx + evidence.length + span))
  }
}
