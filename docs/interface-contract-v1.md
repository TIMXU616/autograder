# AutoGrader 接口契约 v1.0

> ## ⚠️ 本文档已降级为历史文档（2026-09-23）
>
> **接口定义现以 [`docs/接口契约.md`](./接口契约.md) 为唯一依据。**
> 那份文档字段最全（含 13 个错误码表、EARS 验收标准、变更记录、`student` 字段），
> 是前端（B）与测试（C）当前唯一的实现根据。
>
> 本文档保留仅作前后对照。已知它**缺少**后面追认的字段：`student`（结果体与成绩列表）、
> 以及本版后端明确**不引入**的 `channel`。凡与 `docs/接口契约.md` 冲突处，以后者为准。

> 本文档是前端（B）与测试（C）的唯一实现依据。B 只按本文档与 `docs/openapi.yaml` 写页面，C 只按本文档写断言。冻结后任何字段改动需三人一致同意，并在文末「变更记录」追加一行。

## 1. 背景与架构

- 产品：AutoGrader，实验报告智能评阅教学平台。
- 团队 3 人，9/26 23:59 截止提交。
- 架构：FastAPI + SQLite 后端，Vue3 + Element Plus 前端，前后端分离，无登录、单教师角色、无多租户。
- 主链路：选评分点模板 → 上传报告（docx / pdf，单份 ≤20MB，绑定模板）→ 后端解析全文 → 调大模型按评分点逐项核查 → 结果页展示 + 进成绩列表。
- 分工边界：上传只落库返回 report_id，不启动解析；「触发评阅」接口驱动 parsing → grading 全链；前端靠轮询「查询评阅结果」拿状态。

## 2. 后端 LLM 与参数基线

后端运行时调用智谱 GLM API（OpenAI 兼容，base_url `https://open.bigmodel.cn/api/paas/v4`）。平台官方文档：`https://docs.bigmodel.cn/cn/api/rate-limit`。下表参数已于 2026-09-20 实测确认，依据见 `docs/试跑记录_GLM_API诊断.md`。

| 参数 | 取值 | 依据 |
| --- | --- | --- |
| 模型 | glm-4.7 | 免费档 glm-4.7-flash 实测不可用（推理 token 吃满预算 + 高峰期 429），已禁用 |
| 思考模式 | 必须关闭：`"thinking": {"type": "disabled"}` | 开启时 reasoning_tokens 吃满预算，正文为空 |
| 后端调模型单次超时 | 60 秒 | 实测 2295 字输入 + 953 字输出耗时 8.1 秒 |
| 过载重试 | 遇 429 / 1305 退避重试，最多 3 次，间隔 3 秒、8 秒 | 实测平台过载频发，重试属必需 |
| 超时与 5xx 重试 | 1 次；仍失败该评分项置 failed，错误码 5002 | 与过载重试分开计数 |
| 后端并发评分上限 | 1（串行） | 实测并发 2 时一请求 429、一请求超时 |
| 队列等待超时 | 120 秒，超时任务置 failed，错误码 5005 | 与并发上限配套 |
| 上传接口超时 | 60 秒 | 20MB 本地上行 |
| 分数精度 | score / total_score 保留 1 位小数，模板分值为整数 | 评分点模板口径 |

过载重试（429 / 1305，最多 3 次）与超时及 5xx 重试（1 次）分开计数，互不占用对方次数。

## 3. 状态机

```
uploaded → parsing → parsed → grading → success / partial_success / failed
```

| 状态 | 进入条件 | 触发者 | 前端展示 |
| --- | --- | --- | --- |
| uploaded | 上传落库成功 | 用户上传动作 | 「已上传，待评阅」 |
| parsing | 触发评阅后开始解析 docx / pdf | 系统流转 | 「解析中」 |
| parsed | 解析成功，得到结构化文本 | 系统流转 | 「解析完成，准备评分」 |
| grading | 开始调用大模型逐项评分 | 系统流转 | 「评分中」 |
| success | 全部评分项 status 为 graded | 系统流转 | 展示完整逐项得分、总分、评语 |
| partial_success | 至少一项 graded，且存在 status 为 failed / low_confidence / skipped 的项 | 系统流转 | 展示已出分项 + 未出分项警告 |
| failed | 解析失败、模型整体失败、队列超时、全部评分项失败，四类入口之一 | 系统流转 | 展示失败原因与错误码 |

附加规则：

- partial_success 一律 HTTP 200，靠业务 status 区分，禁止用 5xx 表达部分失败。
- failed 四类入口对应错误码：
  - 解析失败：4002 超限、4003 无文本层、4004 空文件、4005 加密。
  - 模型整体失败：5001 模型不可用、5002 超时、5003 非法 JSON、5004 Credits 不足。
  - 队列超时：5005 排队超时。
  - 全部评分项失败：所有 items 的 status 均为 failed，顶层 error_code 取首个评分项的 error_code。
- 状态只前进不回退；重新评阅属于新 attempt，不覆盖旧状态机。

## 4. 通用条款

- 幂等：上传幂等键 = 文件 SHA-256 + template_id；同键重复上传返回 409 加 4091，body 附已有 report_id。
- 并发与排队：并发评分上限 1（串行），超出任务排队，等待超 120 秒置 failed 加 5005。
- 时间格式：ISO 8601 带 `+08:00` 时区，示例 `2026-09-21T01:15:00+08:00`。
- 字段命名：JSON 字段 snake_case；URL 路径全小写复数资源。
- 分页：page 从 1 起，返回体带 total；page_size 默认 20，上限 100。

## 5. 数据对象定义

### 5.1 TemplateItem（评分项摘要）

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| item_id | integer | 评分项序号，从 1 起 |
| name | string | 评分项名称 |
| max_score | integer | 该评分项满分，整数 |

### 5.2 Template（评分点模板）

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| template_id | string | 模板唯一标识，UUID |
| name | string | 模板名称 |
| course | string | 适用课程 |
| items | array\<TemplateItem\> | 评分项摘要数组 |
| total_score | integer | 模板总分，等于各 item max_score 之和 |
| created_at | string | 创建时间，ISO 8601 |

### 5.3 GradingItem（评分项结果，十个字段齐全）

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| item_id | integer | 评分项序号 |
| name | string | 评分项名称 |
| max_score | integer | 评分项满分 |
| score | number \| null | 得分，1 位小数；status 非 graded 时为 null |
| level | string \| null | 等级，取值与语义见下；status 非 graded 时为 null |
| evidence | string \| null | 原文连续子串，禁止改写；无证据时为 null |
| reason | string | 给分或扣分理由，一句 |
| status | string | graded / failed / low_confidence / skipped |
| confidence | string | high / medium / low |
| error_code | integer \| null | status 为 failed 时指向错误码表，其余为 null |

level 取值与语义（按得分率 = score / max_score）：

| level | 语义 |
| --- | --- |
| excellent | 得分率 ≥ 0.90 |
| good | 0.70 ≤ 得分率 < 0.90 |
| fair | 0.50 ≤ 得分率 < 0.70 |
| weak | 0 < 得分率 < 0.50 |
| absent | 得分 = 0 |

### 5.4 GradingResult（评阅结果）

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| report_id | string | 报告唯一标识 |
| template_id | string | 绑定的模板标识 |
| filename | string | 原始文件名 |
| status | string | 状态机当前状态 |
| attempt_no | integer | 从 1 起，模型层重试不递增 |
| model | string | 后端调用模型，固定 glm-4.7 |
| total_score | number \| null | 总分，1 位小数；未出分时为 null |
| consistency | number \| null | 同一报告两次完整评阅的 total_score 之差绝对值；未重评为 null |
| warnings | array\<string\> | 警告数组，无警告为空数组 |
| error_code | integer \| null | 整体 failed 时的错误码，其余为 null |
| items | array\<GradingItem\> | 评分项结果数组 |
| grading_started_at | string \| null | 开始评分时间 |
| finished_at | string \| null | 结束时间 |

### 5.5 GradeListItem（成绩列表项）

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| report_id | string | 报告唯一标识 |
| filename | string | 原始文件名 |
| template_id | string | 模板标识 |
| template_name | string | 模板名称 |
| status | string | 终态，success / partial_success |
| total_score | number | 总分，1 位小数 |
| finished_at | string | 完成时间，ISO 8601 |

## 6. 错误码表

错误响应体统一结构：`{"code": 业务码, "message": "人类可读信息", "detail": 可选对象}`。

| 业务码 | HTTP 状态码 | 触发场景 | 前端提示文案方向 |
| --- | --- | --- | --- |
| 4001 | 415 | 上传文件类型非 docx / pdf | 「仅支持 docx / pdf 格式」 |
| 4002 | 413 / 400 | 上传文件超过 20MB（413）；分页等参数超出上限或取值非法（400） | 「文件超过 20MB 上限」/「参数取值非法」 |
| 4003 | 200 | 无文本层 PDF（扫描件），解析阶段任务置 failed | 「该 PDF 无文本层，无法解析」 |
| 4004 | 400 | 上传空文件（0 字节） | 「文件为空，请重新上传」 |
| 4005 | 200 | PDF 加密，解析阶段任务置 failed | 「PDF 已加密，无法解析」 |
| 5001 | 200 | 模型不可用，重试耗尽后任务置 failed | 「评分服务暂不可用，请稍后重试」 |
| 5002 | 200 | 模型调用超时，重试耗尽后评分项置 failed | 「评分超时，请重试」 |
| 5003 | 200 | 模型返回非法 JSON，任务置 failed | 「评分结果异常，请重试」 |
| 5004 | 200 | Credits 不足，任务置 failed | 「评分额度不足」 |
| 5005 | 200 | 排队等待超 120 秒，任务置 failed | 「排队超时，请稍后重试」 |
| 4041 | 404 | 上传时 template_id 不存在 | 「评分点模板不存在」 |
| 4042 | 404 | 报告不存在 | 「报告不存在」 |
| 4091 | 409 | 幂等键重复上传；已完成报告再次触发评阅 | 「该报告已存在 / 已完成评阅」 |

补充说明：4042「报告不存在」不在 P1-03 规范列出的 12 个错误码内，是本节为覆盖「触发评阅 / 查询结果时 report_id 无效」这一必然场景所补的必要项。若团队另有约定，在变更记录中调整。

## 7. 接口定义

### 7.1 GET /api/v1/templates

评分点模板列表。

请求字段：

| 字段 | 类型 | 必填 | 约束 | 说明 |
| --- | --- | --- | --- | --- |
| page | integer | 否 | 默认 1，≥1 | 页码 |
| page_size | integer | 否 | 默认 20，1~100 | 每页条数 |
| course | string | 否 | 空串按不过滤 | 按适用课程过滤 |

返回字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| total | integer | 模板总数 |
| page | integer | 当前页码 |
| page_size | integer | 每页条数 |
| items | array\<Template\> | 模板数组 |

成功 JSON：

```json
{
  "total": 2,
  "page": 1,
  "page_size": 20,
  "items": [
    {
      "template_id": "tpl-1001",
      "name": "数据结构实验报告评分模板",
      "course": "数据结构",
      "items": [
        {"item_id": 1, "name": "实验目的与原理阐述", "max_score": 20},
        {"item_id": 2, "name": "算法与实现说明", "max_score": 20},
        {"item_id": 3, "name": "结果与分析", "max_score": 20}
      ],
      "total_score": 60,
      "created_at": "2026-09-19T10:00:00+08:00"
    },
    {
      "template_id": "tpl-1002",
      "name": "操作系统实验报告评分模板",
      "course": "操作系统",
      "items": [
        {"item_id": 1, "name": "实验环境与步骤", "max_score": 25},
        {"item_id": 2, "name": "结果与分析", "max_score": 25}
      ],
      "total_score": 50,
      "created_at": "2026-09-19T10:05:00+08:00"
    }
  ]
}
```

失败 JSON：

```json
{"code": 4002, "message": "page 参数必须为整数", "detail": null}
```

```json
{"code": 4002, "message": "page_size 最大为 100", "detail": {"page_size": 200}}
```

### 7.2 POST /api/v1/reports

上传报告。multipart/form-data，只落库返回 report_id，不启动解析。

请求字段：

| 字段 | 类型 | 必填 | 约束 | 说明 |
| --- | --- | --- | --- | --- |
| file | file | 是 | docx 或 pdf，≤20MB | 报告文件 |
| template_id | string | 是 | 已存在的模板 | 绑定的评分点模板 |

返回字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| report_id | string | 报告唯一标识 |
| template_id | string | 绑定的模板标识 |
| filename | string | 原始文件名 |
| file_sha256 | string | 文件 SHA-256 |
| status | string | 固定 uploaded |
| uploaded_at | string | 上传时间 |

成功 JSON（HTTP 201）：

```json
{
  "report_id": "rpt-2001",
  "template_id": "tpl-1001",
  "filename": "单链表实验报告.docx",
  "file_sha256": "a3f5c9d2e1b8f7a6c5d4e3f2a1b0c9d8e7f6a5b4c3d2e1f0a9b8c7d6e5f4a3",
  "status": "uploaded",
  "uploaded_at": "2026-09-21T01:15:00+08:00"
}
```

失败 JSON：

```json
{"code": 4001, "message": "仅支持 docx / pdf 格式", "detail": {"filename": "报告.txt"}}
```

```json
{"code": 4002, "message": "文件超过 20MB 上限", "detail": {"size_bytes": 31457280}}
```

```json
{"code": 4004, "message": "文件为空，请重新上传", "detail": {"size_bytes": 0}}
```

```json
{"code": 4041, "message": "评分点模板不存在", "detail": {"template_id": "tpl-9999"}}
```

```json
{"code": 4091, "message": "该报告已上传", "detail": {"report_id": "rpt-2001"}}
```

### 7.3 POST /api/v1/reports/{report_id}/grading

触发评阅。驱动 parsing → grading 全链。成功 202。

路径参数：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| report_id | string | 是 | 报告唯一标识 |

返回字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| report_id | string | 报告唯一标识 |
| status | string | 当前状态机状态 |
| attempt_no | integer | 评阅次数 |
| accepted_at | string | 接受时间 |

幂等规则：进行中重复触发返回 202 加当前状态、不重跑；已完成再触发返回 409 加 4091。

成功 JSON（HTTP 202）：

```json
{
  "report_id": "rpt-2001",
  "status": "parsing",
  "attempt_no": 1,
  "accepted_at": "2026-09-21T01:16:00+08:00"
}
```

失败 JSON：

```json
{"code": 4091, "message": "该报告已完成评阅，不可重复触发", "detail": {"report_id": "rpt-2001"}}
```

```json
{"code": 4042, "message": "报告不存在", "detail": {"report_id": "rpt-8888"}}
```

### 7.4 GET /api/v1/reports/{report_id}/result

查询评阅结果。前端轮询用。返回状态机当前状态与（若已出）完整评阅结果。

路径参数：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| report_id | string | 是 | 报告唯一标识 |

返回字段见 5.4 GradingResult。

成功 JSON（HTTP 200，status=success）：

```json
{
  "report_id": "rpt-2001",
  "template_id": "tpl-1001",
  "filename": "单链表实验报告.docx",
  "status": "success",
  "attempt_no": 1,
  "model": "glm-4.7",
  "total_score": 58.0,
  "consistency": null,
  "warnings": [],
  "error_code": null,
  "items": [
    {
      "item_id": 1,
      "name": "实验目的与原理阐述",
      "max_score": 20,
      "score": 20.0,
      "level": "excellent",
      "evidence": "掌握单链表的存储结构与基本操作，理解指针在动态内存分配中的作用",
      "reason": "实验目的明确，原理对节点结构、指针域与复杂度阐述完整",
      "status": "graded",
      "confidence": "high",
      "error_code": null
    },
    {
      "item_id": 2,
      "name": "算法与实现说明",
      "max_score": 20,
      "score": 18.0,
      "level": "good",
      "evidence": "链表逆置采用三指针迭代法，用 pre、cur、next 三个指针逐步翻转指向",
      "reason": "核心算法有文字说明与代码节选，但删除与逆置未附关键代码扣 2 分",
      "status": "graded",
      "confidence": "medium",
      "error_code": null
    },
    {
      "item_id": 3,
      "name": "结果与分析",
      "max_score": 20,
      "score": 20.0,
      "level": "excellent",
      "evidence": "构造含 10 个元素的链表，头插法插入后遍历输出顺序与插入顺序相反，符合预期",
      "reason": "给出测试结果，并对效率、边界与异常分别做了分析",
      "status": "graded",
      "confidence": "high",
      "error_code": null
    }
  ],
  "grading_started_at": "2026-09-21T01:16:02+08:00",
  "finished_at": "2026-09-21T01:16:11+08:00"
}
```

进行中 JSON（HTTP 200，status=grading，未出分）：

```json
{
  "report_id": "rpt-2001",
  "template_id": "tpl-1001",
  "filename": "单链表实验报告.docx",
  "status": "grading",
  "attempt_no": 1,
  "model": "glm-4.7",
  "total_score": null,
  "consistency": null,
  "warnings": [],
  "error_code": null,
  "items": [],
  "grading_started_at": "2026-09-21T01:16:02+08:00",
  "finished_at": null
}
```

失败 JSON（HTTP 200，status=partial_success）：

```json
{
  "report_id": "rpt-2002",
  "template_id": "tpl-1001",
  "filename": "图遍历实验报告.docx",
  "status": "partial_success",
  "attempt_no": 1,
  "model": "glm-4.7",
  "total_score": 32.0,
  "consistency": null,
  "warnings": ["第 2 项评分失败，已跳过"],
  "error_code": null,
  "items": [
    {
      "item_id": 1,
      "name": "实验目的与原理阐述",
      "max_score": 20,
      "score": 20.0,
      "level": "excellent",
      "evidence": "掌握图的邻接表存储结构与深度优先遍历",
      "reason": "目的与原理阐述完整",
      "status": "graded",
      "confidence": "high",
      "error_code": null
    },
    {
      "item_id": 2,
      "name": "算法与实现说明",
      "max_score": 20,
      "score": null,
      "level": null,
      "evidence": null,
      "reason": "模型调用超时，重试仍失败",
      "status": "failed",
      "confidence": "low",
      "error_code": 5002
    },
    {
      "item_id": 3,
      "name": "结果与分析",
      "max_score": 20,
      "score": 12.0,
      "level": "fair",
      "evidence": "测试数据共 5 组",
      "reason": "结果分析不完整，缺少异常情况说明",
      "status": "graded",
      "confidence": "medium",
      "error_code": null
    }
  ],
  "grading_started_at": "2026-09-21T01:20:00+08:00",
  "finished_at": "2026-09-21T01:20:31+08:00"
}
```

失败 JSON（HTTP 200，status=failed，解析失败）：

```json
{
  "report_id": "rpt-2003",
  "template_id": "tpl-1001",
  "filename": "扫描件.pdf",
  "status": "failed",
  "attempt_no": 1,
  "model": "glm-4.7",
  "total_score": null,
  "consistency": null,
  "warnings": [],
  "error_code": 4003,
  "items": [],
  "grading_started_at": null,
  "finished_at": "2026-09-21T01:25:00+08:00"
}
```

失败 JSON（HTTP 200，status=failed，队列超时）：

```json
{
  "report_id": "rpt-2004",
  "template_id": "tpl-1001",
  "filename": "排序算法实验报告.docx",
  "status": "failed",
  "attempt_no": 1,
  "model": "glm-4.7",
  "total_score": null,
  "consistency": null,
  "warnings": [],
  "error_code": 5005,
  "items": [],
  "grading_started_at": null,
  "finished_at": "2026-09-21T01:27:00+08:00"
}
```

失败 JSON（HTTP 404，报告不存在）：

```json
{"code": 4042, "message": "报告不存在", "detail": {"report_id": "rpt-8888"}}
```

### 7.5 GET /api/v1/grades

成绩列表。只列出终态为 success / partial_success 的记录。

请求字段：

| 字段 | 类型 | 必填 | 约束 | 说明 |
| --- | --- | --- | --- | --- |
| page | integer | 否 | 默认 1，≥1 | 页码 |
| page_size | integer | 否 | 默认 20，1~100 | 每页条数 |
| template_id | string | 否 | 已存在的模板 | 按模板过滤 |
| order | string | 否 | total_score_desc / total_score_asc | 按总分排序，默认 total_score_desc |

返回字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| total | integer | 记录总数 |
| page | integer | 当前页码 |
| page_size | integer | 每页条数 |
| items | array\<GradeListItem\> | 成绩数组 |

成功 JSON（HTTP 200）：

```json
{
  "total": 3,
  "page": 1,
  "page_size": 20,
  "items": [
    {
      "report_id": "rpt-2001",
      "filename": "单链表实验报告.docx",
      "template_id": "tpl-1001",
      "template_name": "数据结构实验报告评分模板",
      "status": "success",
      "total_score": 58.0,
      "finished_at": "2026-09-21T01:16:11+08:00"
    },
    {
      "report_id": "rpt-2002",
      "filename": "图遍历实验报告.docx",
      "template_id": "tpl-1001",
      "template_name": "数据结构实验报告评分模板",
      "status": "partial_success",
      "total_score": 32.0,
      "finished_at": "2026-09-21T01:20:31+08:00"
    }
  ]
}
```

失败 JSON：

```json
{"code": 4002, "message": "order 取值非法", "detail": {"order": "foo"}}
```

```json
{"code": 4002, "message": "page_size 最大为 100", "detail": {"page_size": 500}}
```

## 8. 验收标准（EARS）

正常路径：

1. When 教师上传合法 docx 且 template_id 存在，系统必须返回 HTTP 201，body 含 report_id 与 status=uploaded。
2. When 教师上传带文本层 pdf 且 template_id 存在，系统必须返回 HTTP 201，body 含 report_id 与 status=uploaded。
3. When 教师对 uploaded 状态的报告触发评阅，系统必须返回 HTTP 202，body 含 status=parsing 或 grading。
4. When 评分项全部 status 为 graded 且 total_score 等于各 item score 之和，系统必须返回 HTTP 200 且 status=success。
5. When 至少一项 status 为 graded 且存在 failed / low_confidence / skipped 项，系统必须返回 HTTP 200 且 status=partial_success。
6. When 教师按 template_id 过滤成绩列表，系统必须只返回该模板的记录。
7. When 教师请求 page=2 且存在第 2 页数据，系统必须返回 total 总数与第 2 页记录。

异常路径：

8. If 上传文件大于 20MB，系统必须返回 HTTP 413，业务码 4002，message 说明大小上限。
9. If 上传文件类型非 docx 或 pdf，系统必须返回 HTTP 415，业务码 4001。
10. If 上传空文件（0 字节），系统必须返回 HTTP 400，业务码 4004。
11. If 上传时 template_id 不存在，系统必须返回 HTTP 404，业务码 4041。
12. If 同一文件（SHA-256 相同）与相同 template_id 重复上传，系统必须返回 HTTP 409，业务码 4091，body 附已有 report_id。
13. If 已完成评阅的报告再次触发评阅，系统必须返回 HTTP 409，业务码 4091。
14. If 无文本层 PDF 进入解析，系统必须将任务置 failed，error_code 为 4003，HTTP 200。
15. When 模型连续 3 次过载重试仍返回 429 / 1305，系统必须将任务置 failed，error_code 为 5001，HTTP 200。
16. When 模型调用超时且 1 次超时重试仍失败，系统必须将该评分项 status 置 failed，error_code 为 5002。

## 9. curl 端到端验证

按顺序执行，每步标注预期返回码与关键字段。

第 1 步：拉模板列表。

```bash
curl -s "http://localhost:8000/api/v1/templates?page=1&page_size=20"
# 预期 HTTP 200，body 含 items 数组与 total，items[0] 含 template_id
```

第 2 步：上传一份 docx。

```bash
curl -s -X POST "http://localhost:8000/api/v1/reports" \
  -F "file=@./samples/单链表实验报告.docx" \
  -F "template_id=tpl-1001"
# 预期 HTTP 201，body 含 report_id、status=uploaded、file_sha256
```

第 3 步：触发评阅（report_id 用第 2 步返回值）。

```bash
curl -s -X POST "http://localhost:8000/api/v1/reports/rpt-2001/grading"
# 预期 HTTP 202，body 含 status=parsing 或 grading
```

第 4 步：轮询结果（每 2 秒一次，直到终态）。

```bash
curl -s "http://localhost:8000/api/v1/reports/rpt-2001/result" | jq '.status'
# 预期依次输出 parsing / grading 之一，最终输出 success 或 partial_success 或 failed
```

第 5 步：拉成绩列表。

```bash
curl -s "http://localhost:8000/api/v1/grades?page=1&page_size=20&template_id=tpl-1001&order=total_score_desc"
# 预期 HTTP 200，body 含 items，items 中终态记录 status 为 success 或 partial_success
```

## 10. 冻结与变更流程

本契约于 2026-09-21 冻结。此后任何字段改动需三人一致同意，并在下表追加一行。B 的前端实现只以本文档和 docs/openapi.yaml 为准。

| 日期 | 改动 | 原因 | 影响接口 |
| --- | --- | --- | --- |
| 2026-09-21 | 初始冻结 v1.0 | 定稿 | 全部 |
| 2026-09-21 | 补充错误码 4042「报告不存在」 | 覆盖触发评阅 / 查询结果时 report_id 无效的必然场景 | 7.3、7.4 |
| 2026-09-21 | 并发评分上限统一为 1（串行） | 实测并发 2 时一请求 429、一请求超时；P1-03 提示词内文两处不一致，以实测值为准 | 通用条款 |
| 2026-09-21 | 4001 范围收窄为「上传文件类型不支持」，查询参数类错误改用 4002 + HTTP 400 | 4001 映射 HTTP 415，用于查询参数非法会产生语义错误；openapi.yaml 中该类错误已定义为 HTTP 400 | 7.1、7.5 |
