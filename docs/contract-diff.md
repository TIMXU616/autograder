# 接口契约差异对照表（前端视角）

> **用途**：A 于 2026-09-21 冻结《AutoGrader 接口契约 v1.0》，本表由 B（前端）逐字段比对现有前端实现后整理，
> 列出**所有会导致联调失败或页面错误**的差异，供三人确认后再动前端代码。
> **前端现状依据**：`frontend/src/api/index.js`、`frontend/src/mock/data.js`、四个 `views/*.vue`（提交 `d829b3e`）
> **契约依据**：`接口契约.md` v1.0（A 定稿）
> **整理人**：B  **日期**：2026-09-21

---

## 0. 结论速览

| 级别 | 数量 | 说明 |
|---|---|---|
| 🔴 P0 · 不改就连不上 | **6** | 字段名/结构完全不同，联调必失败 |
| 🟠 P1 · 不改会显示错 | **5** | 页面能跑但内容错或缺字段 |
| 🟡 P2 · 需补新交互 | **3** | 契约新增了状态/字段，前端没有对应 UI |
| ⚪ 已对齐 | 若干 | 无需改动 |

**总量估算**：改 `api/index.js`（重写适配层）+ `mock/data.js`（按新结构重造）+ 4 个页面局部调整，
**约半天工作量**。建议**在 A 的后端可跑之前完成**，避免联调当天边改边查。

---

## 1. 🔴 P0 · 不改就连不上（6 处）

### 1.1 接口路径前缀不一致

| | 前端现状 | 契约 | 处理 |
|---|---|---|---|
| baseURL | `/api` | `/api/v1` | 改 `api/index.js` 的 `baseURL` 为 `/api/v1` |
| 模板列表 | `GET /templates` | `GET /api/v1/templates` | 同上 |
| 上传 | `POST /reports` | `POST /api/v1/reports` | 同上 |
| 结果 | `GET /reports/{id}/result` | `GET /api/v1/reports/{report_id}/result` | 同上 |
| 成绩列表 | `GET /reports` | `GET /api/v1/grades` ⚠️ | **路径名变了**，不是 `/reports` |
| 触发评阅 | 前端无此调用 | `POST /api/v1/reports/{report_id}/grading` ⚠️ | **新接口**，见 1.2 |

> ⚠️ **成绩列表从 `/reports` 变成 `/grades`**——这是最容易忽略的一处。

### 1.2 上传与评阅被拆成两个接口（前端现在是合成一步）

**契约**：`POST /reports` 只落库返回 `report_id`（不解析）→ 另调 `POST /reports/{id}/grading` 才启动评阅。

**前端现状**：`uploadReport()` 一步完成，上传后直接轮询。

**影响**：`UploadView.vue` 的 `handleSubmit()` 与 `pollUntilDone()` 都要改——先上传拿 `report_id`，再调 grading 接口，再轮询。

### 1.3 状态值完全不同（轮询判断会永远不通过）

| | 前端现状 | 契约 |
|---|---|---|
| 状态取值 | `done` / `grading` / `failed` | `uploaded` / `parsing` / `parsed` / `grading` / `success` / `partial_success` / `failed` |

**影响**：`UploadView.vue` 第 170 行 `status.status === 'done'` **永远为 false** → 前端会无限轮询下去。
必须改为判断 `success` / `partial_success` / `failed`。

### 1.4 轮询接口路径与返回值不同

| | 前端现状 | 契约 |
|---|---|---|
| 轮询地址 | `GET /reports/{id}/status` | **无独立 status 接口**，轮询 `GET /reports/{id}/result` |
| 进度字段 | `progress`（0-100） | **无 progress 字段** |
| 状态字段 | `status` | `status` |

**影响**：`UploadView.vue` 的进度条 `status.progress` 会一直是 undefined。契约没有进度百分比，
需要用状态机（`parsing`→`grading`）映射到一个**模拟进度**（如 parsing 30%、grading 70%），或改为状态文案 + 不确定进度条。

### 1.5 成绩列表返回结构不同

| | 前端现状（Mock） | 契约 |
|---|---|---|
| 列表字段 | `list` | **`items`** |
| 分页参数 | `page` / `size` | `page` / **`page_size`**（默认 20，上限 100） |
| 筛选参数 | `keyword` / `template_name` | **仅 `template_id`**，另加 `order` |
| 无 keyword 参数 | — | ⚠️ **契约未定义 keyword**，见 P1 第 2.1 条 |

### 1.6 模板列表返回结构不同

| | 前端现状（Mock） | 契约 |
|---|---|---|
| 列表字段 | `list` | **`items`** |
| 模板标识类型 | `template_id` 是 **int**（1/2/3） | `template_id` 是 **string UUID**（如 `tpl-1001`） |
| 评分点满分字段 | `full_score` | **`max_score`** |
| 评分点缺字段 | 无 | 多了 `item_id` |
| 模板缺字段 | 有 `item_count`、`description` | ⚠️ **契约无 `item_count` 和 `description`**，见 P1 第 2.2 条 |

---

## 2. 🟠 P1 · 不改会显示错（5 处）

### 2.1 契约缺 `student`（学生姓名）和 `keyword` 搜索

**前端在用**：
- 结果页元信息行显示「文件名 · **学生** · 模板名 · 评阅时间」
- 成绩页表格有「学生」列；搜索框提示"搜索**学生姓名**或文件名"

**契约现状**：`GradingResult`（5.4）和 `GradeListItem`（5.5）**都没有 `student` 字段**；
`GET /grades` 的请求参数里**没有 `keyword`**。

**处理**：契约只从文件名推断学生（如"单链表实验报告.docx"里没有姓名）。三个选项：
- **(a)** 契约补 `student` 字段（若后端能从文件名解析或从上传时附带）
- **(b)** 前端去掉「学生」列与搜索提示，改为按文件名搜索
- **(c)** 契约补 `keyword` 参数（后端按 filename 模糊匹配）

> **建议 (c) + 前端把搜索框提示改为"搜索文件名"**，成本最低；若想保留学生名，需 (a)。

### 2.2 契约缺 `description`（模板说明）和 `item_count`

前端模板页每张卡片显示：模板名 + 「N 项」标签 + **一句描述** + 评分点明细。
契约 `Template`（5.2）只有 `template_id` / `name` / `course` / `items` / `total_score` / `created_at`。

**处理建议**：模板卡片把「描述」位置改为显示 **`course`（适用课程）**，
「N 项」标签改为前端由 `items.length` 自行计算（不需要后端给）。**无需改契约。**

### 2.3 结果页缺 `full_score`（总分满分）

**前端现状**：结果页显示"82 / **100**"，`full_score` 来自契约不存在的字段。
**契约现状**：`GradingResult` 有 `total_score`，**无 `full_score`**；
但 `Template` 有 `total_score`（模板总分）。

**处理**：前端改为 `full_score = 该模板的 total_score`（需同时请求模板列表并按 `template_id` 匹配），
或请求 A 在结果接口补 `full_score`。**建议后者——一行的事，且前端已有模板数据可兜底。**

### 2.4 契约缺 `comment` / `highlights` / `suggestions`（总评三件套）

**前端现状**：结果页有「总评与建议」卡片，含总评正文 + 亮点列表 + 改进建议列表。
**契约现状**：`GradingResult`（5.4）**完全没有这三个字段**。

**处理**：这是结果页四大板块之一（`wireframes.md` 2.1 元素 8-11），不能删。
**建议 A 在 `GradingResult` 补上**：`comment`（string）、`highlights`（array）、`suggestions`（array）。
若后端已有 `warnings`（array），可复用为"提示"但语义不同，不可混用。

### 2.5 结果页缺 `template_name` 和 `student` 用于元信息行

**前端现状**：元信息行显示 `文件名 · 学生 · 模板名 · 评阅时间`。
**契约现状**：`GradingResult` 有 `filename`、`finished_at`，但**无 `template_name`、无 `student`**（只有 `template_id`）。

**处理**：与 2.1、2.3 同类。前端可用模板列表按 `template_id` 反查 `template_name`（兜底可行）；
`student` 与 `created_at`（前端现在用 `created_at`，契约叫 `finished_at`）需统一命名。

---

## 3. 🟡 P2 · 契约新增、前端需补 UI（3 处）

### 3.1 `partial_success` 状态需要新 UI

契约规定：至少一项 graded 且存在 `failed` / `low_confidence` / `skipped` 项时 →
HTTP 200 + `status=partial_success`，且 `warnings` 数组会给出提示（如"第 2 项评分失败，已跳过"）。

**前端现状**：只处理 `done` / `failed` 两种，`partial_success` 会被当成未知状态。

**要补**：
- 结果页顶部加**警示条**（`el-alert`）展示 `warnings`
- 逐项核查表中 `status != graded` 的行，得分列显示「未出分」而非空白，并附 `error_code`
- 总分需注明"部分项未计分"

> **这是 25% 创新性的好素材**——它证明系统对失败是**可观测、可解释**的，不是黑盒。

### 3.2 `level` 字段需要新 UI（5 档等级）

契约 `GradingItem.level`：`excellent` / `good` / `fair` / `weak` / `absent`（按得分率分档）。

**前端现状**：得分率色带是 **4 档**（≥85 绿 / 70-84 蓝 / 60-69 橙 / <60 红），与 `level` 的 5 档**阈值不同**。

**要补**：统一口径。建议**以契约的 `level` 为准**，前端直接把 `level` 映射为标签与颜色
（不要再自己算百分比分档），这样前后端口径一定一致，且 `level` 是后端算好的、可复现。

### 3.3 契约新增字段前端暂未使用（可延后）

| 字段 | 所在对象 | 用途建议 |
|---|---|---|
| `attempt_no` | GradingResult / GradeListItem | 第几次评阅；演示时可显示"第 1 次评阅" |
| `model` | GradingResult | 固定 `glm-4.7`；**PPT 里"AI 能力说明"可直接引用** |
| `consistency` | GradingResult | 两次评阅总分差；**这是回答"AI 打分准不准"质疑的关键数据**，值得在 UI 露出 |
| `confidence` | GradingItem | 每项置信度，可与 `status` 一起做视觉提示 |
| `file_sha256` | 上传响应 | 幂等键，前端仅需在 409 时展示已有 report_id |

> `consistency` 与 `confidence` 建议做进结果页——它们是"可解释性"的直接证据，对应 30% 创新性。

---

## 4. ⚪ 已对齐，无需改动

| 项 | 说明 |
|---|---|
| 文件类型限制 | 前端 `.docx,.pdf` ↔ 契约 4001 |
| 文件大小限制 | 前端 20MB ↔ 契约 4002 |
| 得分精度 | 前端未格式化，契约要求 1 位小数（前端需 `toFixed(1)`，属 P1 小改） |
| 分页起始 | 前端 page 从 1 起 ↔ 契约一致 |
| 空文件/加密/扫描件 | 契约错误码 4003/4004/4005，前端需映射为用户文案（P2） |

---

## 5. 需 A / C 确认的问题（阻塞前端改造）

| # | 问题 | 建议 | 影响 |
|---|---|---|---|
| **B1** | 结果接口能否补 `student`、`full_score`、`template_name`、`comment`、`highlights`、`suggestions` 六个字段？ | **建议补**，否则结果页四大板块缺两块 | 结果页是评委停留最久的页面，缺总评和建议会明显减分 |
| **B2** | 成绩列表能否补 `keyword` 参数（按 filename 模糊匹配）？ | 建议补 | 否则前端搜索框要用 `template_id` 之外的字段就只能前端过滤，破坏分页语义 |
| **B3** | 分页参数统一用 `page_size` 还是 `size`？前端现在传 `size` | 以契约为准用 `page_size` | 前端改一处即可 |
| **B4** | `level` 5 档与前端 4 档色带以哪个为准？ | **以契约 `level` 为准**，前端删掉自己的分档逻辑 | 避免前后端口径漂移 |
| **B5** | 前端轮询用 `/reports/{id}/result`（契约无独立 status 接口），那 `progress` 进度条怎么办？ | 建议前端改为：状态文案（解析中/评分中）+ 不确定型进度条，或 A 补一个 `progress` 字段 | 现在是确定性进度条，改动涉及上传页交互 |
| **B6** | 上传与评阅拆成两步后，前端流程变为「上传 → 触发 → 轮询」，确认这个交互顺序？ | 建议确认 | 影响 `UploadView.vue` 主流程重写 |

---

## 6. 前端改造清单（A 确认后执行）

| 文件 | 改动 | 预估 |
|---|---|---|
| `src/api/index.js` | baseURL 加 `/v1`；`/reports`→`/grades`；新增 `triggerGrading()`；`size`→`page_size`；`list`→`items`；错误码映射用户文案 | 1 小时 |
| `src/mock/data.js` | 按契约结构重造：`template_id` 改 string、`full_score`→`max_score`、状态改状态机、补 `level`/`status`/`confidence`/`warnings` | 1.5 小时 |
| `src/views/UploadView.vue` | 拆成上传→触发→轮询三步；轮询改为查 result；状态判断改 `success`/`partial_success`/`failed`；进度条改不确定型 | 1 小时 |
| `src/views/ResultView.vue` | `full_score` 兜底；补 `warnings` 警示条；`level` 映射标签；未出分项显示；`toFixed(1)` | 1.5 小时 |
| `src/views/ReportsView.vue` | `list`→`items`；`template_name` 改绑 `template_id`；补 `order` 排序；`created_at`→`finished_at` | 1 小时 |
| `src/views/TemplatesView.vue` | `description`→`course`；`item_count` 前端算；`full_score`→`max_score` | 半小时 |
| **合计** | | **约 7 小时（1 天）** |

---

## 7. 变更记录

| 版本 | 日期 | 说明 |
|---|---|---|
| v1 | 2026-09-21 | 初版。比对 A 的接口契约 v1.0 与前端 `d829b3e` 实现，列出 6 项 P0 / 5 项 P1 / 3 项 P2 差异与 6 条待确认问题 |
