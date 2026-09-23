# 联调验证报告 · 后端接入与主链路打通

- 日期：2026-09-22
- 执行：B（前端 + 联调）
- 对象：A 交付的 `autograder-backend/`（契约 v1 实现）
- 结论：**主链路已打通，契约 59 项断言全过；发现并修正 3 处交付说明与实际不符的问题**

---

## 1. 三门一致性核对（契约 / 后端 / 前端）

| 接口 | 契约 §7 | 后端 `app/routes.py` | 前端 `src/api/index.js` | 一致 |
|---|---|---|---|---|
| 模板列表 | `GET /api/v1/templates` | ✅ | ✅ | ✅ |
| 上传 | `POST /api/v1/reports`（201） | ✅ | ✅ | ✅ |
| 触发评阅 | `POST /api/v1/reports/{id}/grading`（202） | ✅ | ✅ | ✅ |
| 查询结果 | `GET /api/v1/reports/{id}/result` | ✅ | ✅ | ✅ |
| 成绩列表 | `GET /api/v1/grades` | ✅ | ✅ | ✅ |

- 后端 `APIRouter(prefix="/api/v1")`，前端 `PREFIX = '/api/v1'`，**前缀口径一致**。
- vite 代理 `/api` → `http://localhost:8000`，**无需 rewrite 也无需改动**（契约前缀本身含 `/api`）。
- 分档口径一致：后端 `scoring.level_of()` 阈值 `0.90 / 0.70 / 0.50` → `excellent / good / fair / weak / absent`；
  前端 `LEVEL_TEXT` / `barColor` 同口径。

---

## 2. 实测结果

### 2.1 契约自检

```
python scripts/contract_test.py
→ 契约一致性：59 通过 / 0 失败
```

### 2.2 主链路端到端（**经 vite 代理 5173**，即前端真实调用路径）

| 步骤 | 请求 | 结果 |
|---|---|---|
| ① 上传 | `POST /api/v1/reports` | **201**，`report_id=rpt-xxxx`，`status=uploaded` |
| ② 触发 | `POST /api/v1/reports/{id}/grading` | **202**，`status=parsing`，`attempt_no=1` |
| ③ 轮询 | `GET /api/v1/reports/{id}/result` | `parsing → parsed → success`，约 4 秒出终态 |
| ④ 结果 | 同上 | 字段齐全（见下） |

结果体核对（7 个评分点 = 3 个 `rule` + 4 个 `llm`）：

```
status=success        total_score=79.8 / full_score=100
student=张三           template_name=程序设计类实验报告评分模板
comment（非空）        highlights=2 条   suggestions=2 条   warnings=[]
model=glm-4.7         attempt_no=1

评分点（item_id / 得分 / level / status / confidence / channel）
1 结构与要素完整性  12.0  excellent  graded  high    rule
2 代码规范性         9.0  excellent  graded  high    rule
3 数据与结果呈现     8.0  excellent  graded  high    rule
4 实验目的与原理阐述 12.8  good      graded  high    llm
5 实验过程与关键实现 14.0  good      graded  medium  llm
6 结果分析与数据解释 12.0  fair      graded  low     llm
7 总结与反思        12.0  good      graded  high    llm
```

> `student` 由后端从**报告正文**提取（`张三`），比前端按文件名末段推导更准；
> 因此前端 `r.student ?? studentFromFilename(...)` 实际走后端值。

### 2.3 前端

- `vite build` 通过（7.89s，退出码 0），`USE_MOCK=false` 下无编译错误。
- 结果页读取的 24 个 `result.*` 字段、11 个 `row.*` 字段全部由适配器产出，**无缺失字段**。

---

## 3. 修正的 3 处问题

### 3.1 `.gitignore` 漏网（**真问题，必须修**）

后端 README 第 65 行称「`*.db`、`data/uploads/`、`.env` 已在仓库 `.gitignore` 中」。
实测**不成立**：

```
git check-ignore -v backend/data/uploads/xxx.docx
→ 会入库（未被忽略）
```

原因：含 `/` 的 gitignore 规则是**相对该 .gitignore 所在层级**的，
`data/uploads/` 只匹配仓库根的 `data/uploads/`，**不覆盖 `backend/data/uploads/`**。

后果：`backend/data/uploads/` 下的**学员上传实验报告会被提交进仓库**（体积 + 数据外泄风险）。

已修正为：

```gitignore
**/data/uploads/
**/data/_trash/
**/data/reports/
```

（`*.db` 无斜杠、任意层级生效，所以数据库文件本来就已被忽略。）

### 3.2 `cp .env.example .env` 是多余动作

交付包内 **`.env` 已存在且已是 `LLM_MOCK=1`**。再执行 `cp` 只会把 `LLM_API_KEY`
覆盖成占位符文案（`请替换为你的key`），没有任何收益。→ **保留交付包里的 `.env` 即可，该步骤跳过。**

### 3.3 `??` 应改为「空即回落」（前端适配器）

`frontend/src/api/index.js` 的 `adaptResult` 原为：

```js
comment: r.comment ?? derived.comment,        // 后端默认值是 ""（不是 null）
highlights: r.highlights ?? derived.highlights,  // 后端默认值是 []
```

后端的 `comment` 默认 `""`、`highlights/suggestions` 默认 `[]`，`??` 只在 `null/undefined` 时回落
→ 会渲染出「**总评空白，页面却仍标注『由评分结果自动汇总』**」的自相矛盾。
已改为 `||` / 长度判断，与 `summary_source` 的判定保持一致。

---

## 4. 环境事实（会影响别人复现）

| 事项 | 说明 |
|---|---|
| **必须先 `cd backend`** | `.env` 的 `DATA_DIR=./data` 是相对 CWD 的；在仓库根启动会写到根目录的 `data/` |
| `WEB_DIR` 路径不符 | `.env` 写的是 `../autograder-repo/frontend/dist`，本仓库应为 `../frontend/dist`。因路径不存在，`main.py` 会跳过静态挂载 → **dev 阶段无害，上线前要改** |
| 只能有一个后端进程 | 8000 端口原有另一实例（LearnBuddy 目录那份），已停止。两个进程同时跑会破坏「并发评分上限 1」的串行保证 |
| 虚拟环境 | `backend/.venv`（Python 3.13.14），依赖 fastapi 0.141.1 / pydantic 2.13.5 |
| 演示数据已复原 | 联调测试产生的垃圾报告已清理，`backend/data/` 恢复为 1 条干净样本（`单链表实验报告_张三.docx`，79.8 分） |

---

## 5. 尚未解决（需 A / C 处理）

1. **契约「变更记录」缺登记**：后端已实现 B1/B2 三处增补
   （`student` / `template_name` / `full_score` / `comment` / `highlights` / `suggestions`、
   `keyword`、`channel`），但 `docs/interface-contract-v1.md` §10 的表格里**没有对应行**。
   按契约第 10 节「任何字段改动需三人一致同意并在下表追加一行」，需补登。
2. **根目录 `test.txt` 被 git 跟踪**（`git ls-files` 可见），交付前必须 `git rm`。
3. **契约 §4 两条口径待确认**（A / C）：
   - 证据闸门：`evidence` 必须能在原文定位，短于 6 字不算有效证据；
   - `low_confidence` **不出分** → 该项不计入 `total_score`，报告整体判 `partial_success`。
     若教研口径希望「降权出分」，需改契约。
4. 成绩页 / 模板页按 A 的建议放在主链路验收之后再切。

---

## 6. A 的公网后端实测对比（2026-09-22 18:45）

地址：`https://autograder-api.app.workbuddy.host`（`/docs` 可打开）

该服务自述 `OpenAPI title=AutoGrader, version=0.1.0`；
而交付包 `backend/` 是 `title=AutoGrader API, version=1.0.0`。
→ **两者不是同一份实现**，这一点需要 A 明确以哪份为交付基准。

### 6.1 一致的部分

契约 5 个路径全部存在且可用，状态机、分档口径一致：

| 路径 | 公网实测 |
|---|---|
| `GET /api/v1/templates` | 200 |
| `POST /api/v1/reports` | 201，`status=uploaded` |
| `POST /api/v1/reports/{id}/grading` | 202，`status=parsing` |
| `GET /api/v1/reports/{id}/result` | 200，直接 `success` |
| `GET /api/v1/grades` | 存在 |

mock 行为与 A 的描述一致：每项恒为满分的 80%，总分 80；`highlights` / `suggestions` 为 `[]`。

### 6.2 不一致清单（需 A 澄清）

| 项 | 公网 | 交付包 `backend/` |
|---|---|---|
| 健康检查 | **无 `/api/v1/health`（404）**，只有 `/healthz` | `/api/v1/health` ✅ |
| 模板数量 | **1 套** | 2 套 |
| `tpl-1001` 内容 | 数据结构实验报告评分模板 / 数据结构 | 程序设计类实验报告评分模板 / 程序设计（C/C++/Java） |
| 模板 item 字段 | 仅 `item_id` / `name` / `max_score`，**无 `channel`、`criteria`** | 含 `channel`、`criteria` |
| 结果体 | **无 `full_score`、`template_name`** | 两者都有 ✅ |
| item 字段 | **无 `channel`** | 含 `channel`（rule / llm） |
| `report_id` 形状 | 32 位 hex（如 `76b00d3d…`） | `rpt-xxxxxxxx` |
| 时间戳 | 带微秒 `…18:42:11.625308+08:00` | 秒级 `…18:42:11+08:00` |
| 总评文案 | 「本报告为骨架阶段占位评分（未配置 GLM_API_KEY）」 | 模型/mock 正常产出 |
| 证据 | 7 项共用同一句（占位） | 各自命中原文，且过闸门校验 |
| 未匹配路径 404 | FastAPI 原生 `{"detail":"Not Found"}` | 统一错误体 |

**好消息：`full_score` 缺失被前端适配器兜住了。** `adaptResult` 不读 `r.full_score`，
而是按 `Σ item.max_score` 计算 → 结果页仍能正确显示 `80 / 100`。
`template_name` 缺失同样由模板缓存（⑤ 接口）兜住。
→ 这两条正是当初坚持「字段在接口层适配、页面不直接吃契约」的收益。

### 6.3 关键风险：公网服务**没有开启 CORS**

```
GET  /api/v1/templates  (Origin: http://localhost:5173)  → 无 Access-Control-Allow-Origin
OPTIONS /api/v1/reports (预检)                            → 405 Method Not Allowed
```

→ **浏览器跨域直连会被拦截**。因此 **不能把 `baseURL` 写成 `https://autograder-api.app.workbuddy.host`**
（multipart 上传还会先发预检，必然被 405 拦掉）。

正确做法（已实测）：

- `baseURL` 保持相对的 `/api/v1` **不变**；
- 把 **vite 代理目标**指向公网地址：
  ```bash
  cd frontend
  VITE_API_TARGET=https://autograder-api.app.workbuddy.host npm run dev
  ```
  （`vite.config.js` 已改为 `process.env.VITE_API_TARGET || 'http://localhost:8000'`）

浏览器因此只与自己的源通信，不触发 CORS。生产环境同理：由 nginx 把 `/api/` 反代到后端。

**实测通过率：经代理打公网后端 8/8 成功；直连公网 8/8 成功**（首次请求有 1 次冷启动 502，随后稳定）。
响应字节与直连完全一致（613 字节，合法 UTF-8）。

### 6.4 环境提醒

- 本机存在 `HTTP_PROXY` / `HTTPS_PROXY`（指向 WorkBuddy 沙箱代理），A 提醒的「代理改写 multipart 导致 404」
  成立；用 `curl --noproxy '*'` 或在代码里显式禁用代理即可。
- `node`/`vite` 的代理默认**不读** `HTTP_PROXY`，所以走 vite 代理不受影响。

