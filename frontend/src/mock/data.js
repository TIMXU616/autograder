/* Mock 数据（契约形状）—— 仅在 src/api/index.js 的 USE_MOCK = true 时生效
   依据：docs/interface-contract-v1.md v1.0（2026-09-21 冻结）

   设计要点：本文件产出的字段名与 A 的后端**完全一致**（snake_case、max_score、
   status、level、confidence…），「契约 → 页面」的转换全部集中在 src/api/index.js。
   所以 USE_MOCK=true 时前端跑的已经是真实的适配路径，联调当天只改一个开关。 */

/* ============ 1. 评分点模板（契约 5.1 / 5.2） ============ */

export const templates = [
  {
    template_id: 'tpl-1001',
    name: '数据结构实验报告评分模板',
    course: '数据结构',
    items: [
      { item_id: 1, name: '实验目的与原理阐述', max_score: 20 },
      { item_id: 2, name: '算法设计与思路说明', max_score: 20 },
      { item_id: 3, name: '代码实现与规范性', max_score: 25 },
      { item_id: 4, name: '测试用例与运行结果', max_score: 20 },
      { item_id: 5, name: '复杂度分析与实验总结', max_score: 15 }
    ],
    total_score: 100,
    created_at: '2026-09-19T10:00:00+08:00'
  },
  {
    template_id: 'tpl-1002',
    name: '计算机网络实验报告评分模板',
    course: '计算机网络',
    items: [
      { item_id: 1, name: '实验环境与拓扑描述', max_score: 15 },
      { item_id: 2, name: '抓包数据与分析过程', max_score: 30 },
      { item_id: 3, name: '协议原理阐述', max_score: 20 },
      { item_id: 4, name: '问题定位与结论', max_score: 25 },
      { item_id: 5, name: '报告规范与可读性', max_score: 10 }
    ],
    total_score: 100,
    created_at: '2026-09-19T10:05:00+08:00'
  },
  {
    template_id: 'tpl-1003',
    name: '通用实验报告评分模板',
    course: '通用',
    items: [
      { item_id: 1, name: '实验过程完整性', max_score: 30 },
      { item_id: 2, name: '数据与结果记录', max_score: 30 },
      { item_id: 3, name: '分析与讨论深度', max_score: 25 },
      { item_id: 4, name: '格式规范', max_score: 15 }
    ],
    total_score: 100,
    created_at: '2026-09-19T10:10:00+08:00'
  }
]

export function mockQueryTemplates({ page = 1, page_size = 20, course = '' } = {}) {
  const all = course ? templates.filter((t) => t.course === course) : templates
  const start = (page - 1) * page_size
  return { total: all.length, page, page_size, items: all.slice(start, start + page_size) }
}

const templateById = (id) => templates.find((t) => t.template_id === id)

/* ============ 2. 评分等级（契约 5.3 的 level 表，按得分率分档） ============ */

export function levelOf(score, maxScore) {
  if (score === null || score === undefined) return null
  if (score <= 0) return 'absent'
  const rate = score / maxScore
  if (rate >= 0.9) return 'excellent'
  if (rate >= 0.7) return 'good'
  if (rate >= 0.5) return 'fair'
  return 'weak'
}

function buildItem(item_id, name, max_score, score, reason, evidence, extra = {}) {
  const graded = score !== null && score !== undefined
  return {
    item_id,
    name,
    max_score,
    score: graded ? score : null,
    level: graded ? levelOf(score, max_score) : null,
    evidence: evidence ?? null,
    reason,
    status: graded ? 'graded' : 'failed',
    confidence: extra.confidence ?? (graded ? 'high' : 'low'),
    error_code: graded ? null : (extra.error_code ?? 5002)
  }
}

/* ============ 3. 已完成评阅的种子结果（成绩列表与详情页演示用） ============ */

const HERO_2001 = {
  report_id: 'rpt-2001',
  template_id: 'tpl-1001',
  filename: '数据结构实验三_二叉搜索树_张三.docx',
  status: 'success',
  attempt_no: 1,
  model: 'glm-4.7',
  total_score: 84.0,
  consistency: null,
  warnings: [],
  error_code: null,
  items: [
    buildItem(
      1, '实验目的与原理阐述', 20, 20.0,
      '实验目的明确，原理部分对节点结构、查找与插入的复杂度都作了说明',
      '掌握二叉搜索树的定义与性质，中序遍历可得到有序序列，平均查找复杂度为 O(log n)',
      { confidence: 'high' }
    ),
    buildItem(
      2, '算法设计与思路说明', 20, 16.0,
      '插入与查找思路正确，但双孩子删除为何选右子树最小节点作后继未作说明',
      '删除节点分三种情况讨论，其中双孩子节点用右子树的最小节点替换',
      { confidence: 'medium' }
    ),
    buildItem(
      3, '代码实现与规范性', 25, 23.0,
      '代码可运行、注释完整、对空指针作了防护，存在少量重复的查找逻辑可抽取',
      '递归实现时先判断 root == nullptr 再进入递归，避免了对空指针取成员',
      { confidence: 'high' }
    ),
    buildItem(
      4, '测试用例与运行结果', 20, 17.0,
      '覆盖空树、单节点与有序插入退化场景，缺少大规模随机数据验证',
      '构造含 10 个节点的树，中序遍历输出与预期有序序列一致',
      { confidence: 'medium' }
    ),
    buildItem(
      5, '复杂度分析与实验总结', 15, 8.0,
      '只给出平均复杂度结论，未分析退化为链表时的最坏情况；总结未记录调试中遇到的问题',
      '平均时间复杂度为 O(log n)',
      { confidence: 'low' }
    )
  ],
  grading_started_at: '2026-09-21T14:19:58+08:00',
  finished_at: '2026-09-21T14:20:11+08:00'
}

/* 部分成功样本：第 2 项模型超时失败，用来演示 warnings 与 failed 项 */
const PARTIAL_2002 = {
  report_id: 'rpt-2002',
  template_id: 'tpl-1001',
  filename: '数据结构实验四_图遍历_李四.docx',
  status: 'partial_success',
  attempt_no: 1,
  model: 'glm-4.7',
  total_score: 60.0,
  consistency: null,
  warnings: ['第 2 项「算法设计与思路说明」评分失败，已跳过（错误码 5002）'],
  error_code: null,
  items: [
    buildItem(1, '实验目的与原理阐述', 20, 20.0, '目的与原理阐述完整，对两种遍历方式均作了对比', '掌握图的邻接表存储结构与深度、广度优先遍历', { confidence: 'high' }),
    buildItem(2, '算法设计与思路说明', 20, null, '模型调用超时，重试 1 次后仍失败', null, { error_code: 5002, confidence: 'low' }),
    buildItem(3, '代码实现与规范性', 25, 12.0, '非递归实现未给出，递归版本缺少栈深控制说明', '使用队列实现广度优先遍历，邻接表以 vector 存储', { confidence: 'medium' }),
    buildItem(4, '测试用例与运行结果', 20, 18.0, '给出 5 组测试数据与输出，缺少孤立节点场景', '测试数据共 5 组，遍历序列均与预期一致', { confidence: 'high' }),
    buildItem(5, '复杂度分析与实验总结', 15, 10.0, '给出了复杂度分析，实验总结偏简略', '邻接表存储下时间复杂度为 O(V+E)', { confidence: 'medium' })
  ],
  grading_started_at: '2026-09-21T14:31:02+08:00',
  finished_at: '2026-09-21T14:31:33+08:00'
}

/* 解析失败样本：无文本层的扫描件 PDF（契约错误码 4003） */
const FAILED_2003 = {
  report_id: 'rpt-2003',
  template_id: 'tpl-1001',
  filename: '数据结构实验三_扫描件_王五.pdf',
  status: 'failed',
  attempt_no: 1,
  model: 'glm-4.7',
  total_score: null,
  consistency: null,
  warnings: [],
  error_code: 4003,
  items: [],
  grading_started_at: null,
  finished_at: '2026-09-21T14:40:00+08:00'
}

/* 其余历史记录：按模板 + 目标总分自动生成，保证列表有分页与四档色带的样本。
   注意：这些是占位数据，理由文案由等级生成，接入真实后端后即被替换。 */
function makeSeed(report_id, filename, template_id, rate, finished_at, extra = {}) {
  const tpl = templateById(template_id)
  const items = tpl.items.map((t, index) => {
    const jitter = [-0.04, 0.03, 0.06, -0.08, 0.01][index % 5]
    const raw = Math.min(0.99, Math.max(0.05, rate + jitter))
    const score = Math.round(t.max_score * raw * 10) / 10
    return buildItem(
      t.item_id, t.name, t.max_score, score,
      `${t.name}按判定标准核查后给分，等级为 ${levelOf(score, t.max_score)}`,
      null,
      { confidence: score / t.max_score >= 0.7 ? 'high' : 'medium' }
    )
  })
  const total = Math.round(items.reduce((s, i) => s + (i.score ?? 0), 0) * 10) / 10
  return {
    report_id,
    template_id,
    filename,
    status: extra.status ?? 'success',
    attempt_no: 1,
    model: 'glm-4.7',
    total_score: total,
    consistency: extra.consistency ?? null,
    warnings: extra.warnings ?? [],
    error_code: null,
    items,
    grading_started_at: finished_at,
    finished_at
  }
}

const SEEDS = [
  HERO_2001,
  PARTIAL_2002,
  FAILED_2003,
  makeSeed('rpt-2004', '计算机网络实验二_抓包分析_孙七.pdf', 'tpl-1002', 0.88, '2026-09-21T15:12:07+08:00'),
  makeSeed('rpt-2005', '操作系统实验一_进程调度_周八.docx', 'tpl-1003', 0.69, '2026-09-21T16:30:45+08:00'),
  makeSeed('rpt-2006', '数据结构实验三_二叉搜索树_赵六.docx', 'tpl-1001', 0.58, '2026-09-21T17:05:19+08:00'),
  makeSeed('rpt-2007', '计算机网络实验二_抓包分析_钱九.pdf', 'tpl-1002', 0.77, '2026-09-21T17:22:40+08:00', { consistency: 2.0 })
]

const seedById = new Map(SEEDS.map((r) => [r.report_id, r]))

/* ============ 4. 运行时状态机（契约 3：uploaded → parsing → parsed → grading → 终态） ============ */

const STAGE_ORDER = ['parsing', 'parsed', 'grading']
const runtime = new Map()
let seq = 2100

function nowIso() {
  return new Date(Date.now() + 8 * 3600 * 1000).toISOString().replace('Z', '+08:00')
}

function hashRate(name) {
  let h = 0
  for (let i = 0; i < name.length; i += 1) h = (h * 31 + name.charCodeAt(i)) % 997
  return 0.62 + (h % 31) / 100
}

export function mockUpload({ filename, template_id }) {
  const report_id = `rpt-${(seq += 1)}`
  runtime.set(report_id, {
    report_id,
    template_id,
    filename,
    status: 'uploaded',
    attempt_no: 0,
    model: 'glm-4.7',
    total_score: null,
    consistency: null,
    warnings: [],
    error_code: null,
    items: [],
    grading_started_at: null,
    finished_at: null,
    _stage: -1
  })
  return {
    report_id,
    template_id,
    filename,
    file_sha256: 'mock-' + report_id,
    status: 'uploaded',
    uploaded_at: nowIso()
  }
}

export function mockTrigger(report_id) {
  const rec = runtime.get(report_id)
  if (!rec) return null
  if (['success', 'partial_success'].includes(rec.status)) return { conflict: true, rec }
  if (rec.status !== 'uploaded') return { conflict: false, rec }
  rec.status = 'parsing'
  rec.attempt_no = 1
  rec._stage = 0
  rec.grading_started_at = nowIso()
  return { conflict: false, rec }
}

/* 每次轮询推进一个阶段；评分完成后按文件名决定终态 */
export function mockPoll(report_id) {
  const rec = runtime.get(report_id) ?? seedById.get(report_id)
  if (!rec) return null
  if (['success', 'partial_success', 'failed'].includes(rec.status)) return rec

  if (rec._stage < STAGE_ORDER.length - 1) {
    rec._stage += 1
    rec.status = STAGE_ORDER[rec._stage]
    return rec
  }
  return finalize(rec)
}

function finalize(rec) {
  rec.finished_at = nowIso()
  if (/扫描|scan/i.test(rec.filename)) {
    rec.status = 'failed'
    rec.error_code = 4003
    rec.items = []
    return rec
  }
  const tpl = templateById(rec.template_id)
  const base = hashRate(rec.filename)
  rec.items = tpl.items.map((t, index) => {
    const jitter = [0.05, -0.06, 0.02, -0.03, -0.12][index % 5]
    const raw = Math.min(1, Math.max(0.1, base + jitter))
    const score = Math.round(t.max_score * raw * 10) / 10
    return buildItem(
      t.item_id, t.name, t.max_score, score,
      `${t.name}按判定标准逐项核查后给分`,
      null,
      { confidence: raw >= 0.7 ? 'high' : 'medium' }
    )
  })
  rec.total_score = Math.round(rec.items.reduce((s, i) => s + i.score, 0) * 10) / 10
  rec.status = 'success'
  return rec
}

/* ============ 5. 成绩列表查询（契约 7.5） ============ */

export function mockQueryGrades({ page = 1, page_size = 20, template_id = '', keyword = '', order = 'total_score_desc' } = {}) {
  const all = [...SEEDS, ...runtime.values()]
    .filter((r) => ['success', 'partial_success'].includes(r.status))
    .map((r) => ({
      report_id: r.report_id,
      filename: r.filename,
      template_id: r.template_id,
      template_name: templateById(r.template_id)?.name ?? '',
      status: r.status,
      total_score: r.total_score,
      finished_at: r.finished_at
    }))
    .filter((r) => !template_id || r.template_id === template_id)
    .filter((r) => !keyword || r.filename.includes(keyword))

  all.sort((a, b) =>
    order === 'total_score_asc' ? a.total_score - b.total_score : b.total_score - a.total_score
  )

  const start = (page - 1) * page_size
  return {
    total: all.length,
    page,
    page_size,
    items: all.slice(start, start + page_size)
  }
}
