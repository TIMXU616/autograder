# 公网部署对齐核实报告

> 核实人：B（前端 + 联调）  
> 核实时间：2026-09-22 23:30  
> 起因：A 转达「公网后端已对齐冻结版 7029d3a」，并要求 B「按 docs/接口契约.md 实现」

---

## 0. 结论一句话

**方向认同，证据对不上。** 「一套代码、仓库是唯一真值源、公网可能滞后」这个说法与实测症状吻合，A 说的三条行为（order 报 400+4002、跑题 0 分七项全 absent、成绩列表带 student）我逐条实测**都成立**。但：

1. A 给的**三个核实路径在仓库里全部不存在**（commit 7029d3a、`docs/接口契约.md`、`docs/openapi.yaml`、`docs/部署记录.md`）；
2. 公网实例与仓库后端之间**有 4 处差异**，其中「错误体 detail 一律为 null」是**方向相反**的——公网在 student 上比仓库新、在 detail / full_score 上比仓库旧，不是单纯的「构建落后」能解释；
3. 其中一条差异会让前端**幂等复用功能直接失效**（已修，见第 4 节）。

---

## 1. 逐条核对 A 的声明

| A 的声明 | 实测结果 | 判定 |
| --- | --- | --- |
| 409 的 report_id 在 `detail.report_id` 里，不在顶层 | 契约 §7.1 / §7.3 明文就是 `detail: {report_id}`；**仓库后端实测** `{"code":4091,...,"detail":{"report_id":"rpt-78ea7284"}}` | 对**仓库**成立 |
| （同上）| **公网实测** `{"code":4091,"message":"该报告已完成评阅，不可重复触发","detail":null}` | 对**公网**不成立 |
| order 参数错误现在返 400 + 4002 | 公网：`HTTP 400` + `{"code":4002,"message":"order 取值非法…"}` | ✅ 成立 |
| 跑题报告返回 0 分、七项全 absent | 公网 `canteen_survey.docx`：total_score 0.0，7 项全 `score=0.0` `level=absent` `status=graded` | ✅ 成立 |
| 成绩列表带 student | 公网：`items[].student` 有值 | ✅ 对公网成立 |
| （同上）| **仓库后端：`items` 里没有 student 字段**（数据库 `reports.student` 有值 '张三' 等，接口未输出） | 对仓库不成立 |
| 公网 = 仓库某次构建，代码逻辑完全相同 | 见第 3 节差异表：title/version/路由/错误体/结果体字段/grades 字段/模板字段**共 7 项不同** | 部分成立 |
| 冻结版 commit 7029d3a | `git cat-file -t 7029d3a` → `fatal: Not a valid object name`；`git log --all` 全部可达 commit 中最新的仍是 `6199fbe`（2026-09-22 16:50） | ❌ 查不到 |

**另外两条我顺手验的（A 没提，但值得记录）：**

- **幂等键 = 文件 SHA-256 + template_id**，行为完全正确：同一文件同一模板重传 → `409 + 4091`；换模板重传 → `201`。
- **契约 v1 全文没有出现过 `student` 这个词**（`grep -n "student" docs/interface-contract-v1.md` 零命中）。所以「成绩列表带 student」是一条**契约增补，尚未登记到 §10 变更记录**。

---

## 2. A 指向的核实路径，逐一落地情况

| A 说的东西 | 仓库里的实际情况 |
| --- | --- |
| commit `7029d3a` | **不存在**（本地所有引用都查不到） |
| `docs/接口契约.md` | **不存在**。仓库里的是 `docs/interface-contract-v1.md`（内容确实是契约：含错误码表 §7、变更记录 §10）。A 说的应该是它，只是文件名对不上 |
| `docs/openapi.yaml` | **不存在**。契约正文里 4 次引用过它（如 §10 写到「openapi.yaml 中该类错误已定义为 HTTP 400」），但文件从未入库 |
| `docs/部署记录.md` | **不存在**，无法核 deployment ↔ commit 的对应关系 |

> 影响：「仓库 AutoGrader/backend/ 是唯一真值源」这句话要成立，得先把这几样真的推上来。目前 B 手上这份 backend/ 是 LearnBuddy 交付的 1.0.0 版本，既不是冻结版 7029d3a，公网那份也不是它。**请 A 把 7029d3a 真正推上 dev 分支**，否则「以仓库为准」无法执行。

---

## 3. 公网实例 vs 仓库后端：差异表

| 观测点 | 公网 `autograder-api.app.workbuddy.host` | 仓库后端（本机 8000） |
| --- | --- | --- |
| OpenAPI title / version | `AutoGrader` / **0.1.0** | `AutoGrader API` / **1.0.0** |
| 健康检查 | 只有 `/healthz`（`/api/v1/health` 404） | `/api/v1/health` ✅ |
| 路由数 | 6 | 7（多 `/reports/{id}/text`） |
| 错误体 `detail` | **一律 `null`** | 按契约返回对象 ✅ |
| 结果体 `full_score` | **缺失** | 有 |
| 结果体 `template_name` | **缺失** | 有 |
| grades item `student` | **有** | 无 |
| 模板评分项字段 | `item_id` / `name` / `max_score` | 另有 `channel` / `criteria` |
| 模板套数 | 1（数据结构实验报告评分模板） | 2 |

**判定：方向相反的两组差异，说明公网既不是「仓库单纯落后」，也不是「仓库本身」。**  
公网在 `student` 上比仓库**新**，在 `detail` / `full_score` / `template_name` 上比仓库**旧**。因此只有两种可能：存在第三个构建（即 A 说的 7029d3a，但仓库里没有）；或 A 描述的「冻结版」实际未落地。**请 A 明确以哪一份为联调基准。**

---

## 4. 对 B 的实际影响（逐条给结论）

| 项 | 结论 |
| --- | --- |
| `level = 'absent'` 前端认不认？ | **认，不用改。** `api/index.js` 的 `LEVEL_TEXT.absent = '缺失'`、`LEVEL_TAG.absent = 'info'`，且结果页「需改进项」列表本就包含 `absent` |
| `full_score` / `template_name` 公网缺失 | **不受影响。** `adaptResult` 从不读 `r.full_score`，而是按 `Σ items[].max_score` 算；公网 items 实测带 `max_score`（Σ = 100），所以结果页照常显示 `0 / 100` |
| 错误体 `detail = null` | ⚠️ **真 bug，已修。** `uploadReport` 原逻辑只认 `error.detail?.report_id`；公网返回 `detail:null` → 幂等复用退化成红色报错。见下 |
| grades 的 `student` | **已修。** `adaptGradeRow` 原先硬用文件名推导，会丢掉后端给的值（公网存成哈希名时推出来是「—」）。已改成后端优先、文件名兜底 |

### 4.1 已做的改动（3 个文件）

**`frontend/src/api/index.js`**

1. `uploadReport` 的 4091 分支重写为三级兜底：
   - `error.detail?.report_id` 存在 → 复用（对仓库后端生效）；
   - 不存在 → 按文件名到成绩列表反查（新增 `findExistingReportId()`，对保留原始文件名的后端生效）；
   - 都拿不到 → 抛**可读**错误「该文件此前已提交过，请到「成绩页」查看已有结果」，而不是一个无头绪的通用报错。
2. `adaptGradeRow` 的 `student` 改为 `row.student || studentFromFilename(row.filename)`，与 `adaptResult` 的口径统一。

**`frontend/src/views/UploadView.vue`**

新增 `uploaded.reused` 的提示（info 提示 + 阶段文案「该文件此前已提交，正在复用已有记录…」），让复用对用户可见。

### 4.2 验证结果

- `npm run build` → ✅ 通过
- 4091 三分支逻辑验证（用**实测抓到的真实响应体**驱动）：

  | 场景 | 结果 |
  | --- | --- |
  | 仓库后端 detail 带 report_id | PASS → `reuse:rpt-a5e6b72c` |
  | 公网 detail:null + 文件名命中 | PASS → `reuse:rpt-77` |
  | 公网 detail:null + 存成哈希名 | PASS → 可读错误（不再是无头绪报错） |

- 仓库后端幂等实测：同文件同模板 → `409 + 4091 + detail.report_id`；换模板 → `201`
- 回归：仓库后端 `/health` 正常，`/grades` 恢复 5 条干净样本（我测试造的两条已清理）

---

## 5. 待 A / C 拍板

1. **联调基准用哪一套？** B 的建议：**用仓库后端**（59/59 契约断言通过、有 rule/llm 双通道、字段齐全），公网只当 A 的临时部署。
2. **`student` 是否正式增补进契约？** 若前端要显示它，需在 §7.4 / §7.5 补字段并在 §10 追加变更记录（三人一致同意）。
3. **公网的 `detail: null` 要不要修？** 这是与契约 §7 的明文冲突，且会让幂等复用降级。
4. **`docs/openapi.yaml` 要不要入库？** 契约正文 4 次引用它，但文件不存在。
5. **`7029d3a` 请推到 dev 分支**，否则「仓库为唯一真值源」无法执行。

---

## 6. 可直接转发

### 6.1 给 A 的回执

> 收到，方向我认同，也已经按 `docs/interface-contract-v1.md`（仓库里实际存在的契约文件）实现。但有四件事要你确认：
>
> 1. **`7029d3a` 在我的仓库里不存在**——`git cat-file -t 7029d3a` 报 not a valid object name，`git log --all` 最新还是 `6199fbe`。麻烦真的推上来，否则「仓库为唯一真值源」落不了地。
> 2. **你指的 `docs/接口契约.md`、`docs/openapi.yaml`、`docs/部署记录.md` 三个文件仓库里都没有。** 我按 `docs/interface-contract-v1.md` 实现，文件名对不上，确认一下是不是同一份。
> 3. **公网和仓库不一致的地方不止「构建落后」：** 公网 rank 了 `student`（仓库没有，且契约 v1 里根本没这个字段），但公网的**错误体 `detail` 一律是 null**（契约 §7 要求带对象），结果体还缺 `full_score` / `template_name`，自述版本是 `AutoGrader 0.1.0`（仓库是 `AutoGrader API 1.0.0`，路由也多一条 `/text`）。一旧一新的差异方向相反，所以到底以哪份为联调基准？
> 4. **`detail: null` 会让我这边幂等复用失效**（409 时拿不到 report_id）。我已经加了按文件名反查的兜底，但建议公网按契约补齐 detail。
>
> 其余你提到的三条我都实测过了，全部成立：order → 400 + 4002 ✅、跑题 → 0 分七项全 absent ✅、成绩列表带 student ✅。

### 6.2 修正版通知（若要发群里，建议用这版）

> 公网后端已更新，我实测确认：order 参数错误返 `400 + 4002`；跑题报告返回 0 分、七项全 `absent`；成绩列表带 `student`。
> 实现依据：`docs/interface-contract-v1.md`（**不是** `docs/接口契约.md`，该文件不存在）。
> 注意公网错误体的 `detail` 目前一律为 `null`，与契约 §7 不符，联调时不要依赖 `detail` 里的字段。

---

## 附：本次实测的原始命令与响应

```
# 公网 409（已完成报告再触发）
POST https://autograder-api.app.workbuddy.host/api/v1/reports/857afb…/grading
→ HTTP 409  {"code":4091,"message":"该报告已完成评阅，不可重复触发","detail":null}

# 仓库后端 409（同一请求）
POST http://127.0.0.1:8000/api/v1/reports/rpt-a5e6b72c/grading
→ HTTP 409  {"code":4091,"message":"该报告已完成评阅，不可重复触发","detail":{"report_id":"rpt-a5e6b72c"}}

# 公网 4042 / 4002
GET  …/api/v1/reports/not-exist-xyz/result   → 404 {"code":4042,…, "detail":null}
GET  …/api/v1/grades?page_size=500           → 400 {"code":4002,…,"detail":null}

# 仓库后端 同requests
GET  http://127.0.0.1:8000/api/v1/reports/not-exist-xyz/result → 404 …"detail":{"report_id":"not-exist-xyz"}
GET  http://127.0.0.1:8000/api/v1/grades?page_size=500        → 400 …"detail":{"page_size":500}

# 仓库后端幂等键
POST /api/v1/reports  (同文件 + tpl-1001) → 409 4091 detail.report_id
POST /api/v1/reports  (同文件 + tpl-1002) → 201

# 公网跑题报告
GET  …/api/v1/reports/deb8d2a89d684ca9acca151c5c109bba/result
→ total_score 0.0 / status success / 7 items 全 level=absent status=graded，Σ max_score = 100
```
