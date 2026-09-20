/* Mock 数据：接口契约见 docs/api.md
   联调时把 src/api/index.js 里的 USE_MOCK 改为 false 即可切换为真实接口 */

export const templates = [
  {
    template_id: 1,
    name: '数据结构实验报告评分模板',
    item_count: 6,
    description: '适用于线性表、树、图等数据结构实验报告',
    items: [
      { name: '实验目的与原理', full_score: 15 },
      { name: '算法设计与思路', full_score: 20 },
      { name: '代码实现与规范性', full_score: 25 },
      { name: '测试用例与运行结果', full_score: 20 },
      { name: '算法复杂度分析', full_score: 10 },
      { name: '实验总结与反思', full_score: 10 }
    ]
  },
  {
    template_id: 2,
    name: '计算机网络实验报告评分模板',
    item_count: 5,
    description: '适用于抓包分析、协议实现类实验',
    items: [
      { name: '实验环境与拓扑描述', full_score: 15 },
      { name: '抓包数据与分析过程', full_score: 30 },
      { name: '协议原理阐述', full_score: 20 },
      { name: '问题定位与结论', full_score: 25 },
      { name: '报告规范与可读性', full_score: 10 }
    ]
  },
  {
    template_id: 3,
    name: '通用实验报告评分模板',
    item_count: 4,
    description: '未指定课程时的兜底模板',
    items: [
      { name: '实验过程完整性', full_score: 30 },
      { name: '数据与结果记录', full_score: 30 },
      { name: '分析与讨论深度', full_score: 25 },
      { name: '格式规范', full_score: 15 }
    ]
  }
]

export const reportResults = {
  1: {
    report_id: 1,
    file_name: '数据结构实验三_二叉搜索树_张三.docx',
    student: '张三',
    template_name: '数据结构实验报告评分模板',
    total_score: 82,
    full_score: 100,
    comment:
      '整体完成度较好，实验步骤完整、代码可运行，测试用例覆盖了主要边界情况。主要不足在于算法复杂度的推导过程较为简略，仅给出结论缺少论证；实验总结部分对失败的尝试缺少分析。建议补充复杂度推导，并对调试过程中遇到的问题做归因记录。',
    highlights: ['代码结构清晰，命名规范', '测试用例覆盖了空树与单节点等边界情况'],
    suggestions: ['补充时间复杂度的推导过程', '实验结论需要与理论预期做对比说明'],
    created_at: '2026-09-23 14:20:11',
    items: [
      {
        name: '实验目的与原理',
        score: 14,
        full_score: 15,
        reason: '实验目的表述清晰，原理部分覆盖了二叉搜索树的定义与性质',
        evidence: '第 1 节「实验目的」'
      },
      {
        name: '算法设计与思路',
        score: 16,
        full_score: 20,
        reason: '插入与删除的递归实现思路正确，但删除节点的双孩子情况讨论不够充分',
        evidence: '第 2 节「算法设计」'
      },
      {
        name: '代码实现与规范性',
        score: 23,
        full_score: 25,
        reason: '代码可运行，异常处理与注释较完整，存在少量重复逻辑',
        evidence: '代码块 L20-L120'
      },
      {
        name: '测试用例与运行结果',
        score: 18,
        full_score: 20,
        reason: '覆盖了空树、单节点与有序插入的退化场景，缺少大规模随机数据测试',
        evidence: '第 4 节「测试与结果」'
      },
      {
        name: '算法复杂度分析',
        score: 5,
        full_score: 10,
        reason: '仅给出平均复杂度结论，未推导最坏情况与退化条件',
        evidence: '第 5 节「复杂度分析」'
      },
      {
        name: '实验总结与反思',
        score: 6,
        full_score: 10,
        reason: '总结了完成情况，但未记录调试过程中遇到的问题与解决方式',
        evidence: '第 6 节「实验总结」'
      }
    ]
  }
}

export const reportList = [
  {
    report_id: 1,
    file_name: '数据结构实验三_二叉搜索树_张三.docx',
    student: '张三',
    total_score: 82,
    template_name: '数据结构实验报告评分模板',
    created_at: '2026-09-23 14:20:11'
  },
  {
    report_id: 2,
    file_name: '数据结构实验三_二叉搜索树_李四.pdf',
    student: '李四',
    total_score: 91,
    template_name: '数据结构实验报告评分模板',
    created_at: '2026-09-23 14:22:38'
  },
  {
    report_id: 3,
    file_name: '计算机网络实验二_抓包分析_王五.docx',
    student: '王五',
    total_score: 76,
    template_name: '计算机网络实验报告评分模板',
    created_at: '2026-09-23 15:01:52'
  },
  {
    report_id: 4,
    file_name: '数据结构实验三_二叉搜索树_赵六.docx',
    student: '赵六',
    total_score: 58,
    template_name: '数据结构实验报告评分模板',
    created_at: '2026-09-23 15:12:07'
  },
  {
    report_id: 5,
    file_name: '计算机网络实验二_抓包分析_孙七.pdf',
    student: '孙七',
    total_score: 88,
    template_name: '计算机网络实验报告评分模板',
    created_at: '2026-09-23 16:30:45'
  },
  {
    report_id: 6,
    file_name: '操作系统实验一_进程调度_周八.docx',
    student: '周八',
    total_score: 69,
    template_name: '通用实验报告评分模板',
    created_at: '2026-09-23 17:05:19'
  }
]

/* 兜底结果：任何未预置的 report_id 都用它，避免点进详情页时白屏 */
export function buildFallbackResult(reportId) {
  const base = reportResults[1]
  return {
    ...base,
    report_id: Number(reportId),
    file_name: `实验报告_${reportId}.docx`,
    student: '演示学生',
    total_score: 78,
    comment: '这是 Mock 兜底数据：该报告未预置评阅结果，用于验证页面在真实数据到来前的展示效果。',
    created_at: '2026-09-23 18:00:00'
  }
}

export function pickResult(reportId) {
  return reportResults[reportId] || buildFallbackResult(reportId)
}
