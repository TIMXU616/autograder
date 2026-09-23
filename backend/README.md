# AutoGrader 后端（FastAPI + SQLite）· 四层结构

> **接口定义以 [`docs/接口契约.md`](../docs/接口契约.md) 为唯一依据。**
> `docs/api.md` 与 `docs/interface-contract-v1.md` 是历史文档，仅供对照，不作为实现根据。
>
> 本目录当前是分支 `a/backend-p2`（tip `7ef17b8`）经合并提交 `f6c3d28` 合入 `dev` 的
> **四层结构**实现，取代了原先的扁平结构版本（`db.py` / `scoring.py` / `routes.py` 那一套，
> 已整份备份到仓库外的 `/d/projects/_bak_flat_20260923/`）。
> openapi 自述为 `AutoGrader`、`info.version` = `0.1.0`。

---

## 0. 取舍说明

| 决策 | 理由 |
|---|---|
| 不引 ORM / Alembic，原生 sqlite3 + WAL | 单机单进程够用；改字段只需换库重启 |
| 评分管线跑在进程内后台线程，`--workers 1` | 契约规定并发评分上限 1（串行），单进程最稳 |
| 模型调用整份报告**一次**打包 | 额度有限（初赛 2500 credits/队），按项调用会把成本乘以评分点数 |
| 上传：先校验再落盘（读进内存 ≤20MB） | 失败路径不产生垃圾文件 |
| 总分由后端累加各项得分，模型不输出总分 | 从根上消除「总分与各项之和对不上」这类演示事故 |
| 规则通道完全不经过模型 | 可复现、零幻觉，是回应「API 套壳」质疑的实物证据 |
| 启动时把上次 in-flight 报告置 `failed` | 重启后不会永久卡在 `grading`，避免演示时白屏等不到终态 |

---

## 1. 目录结构（四层）

```
backend/
├── requirements.txt
├── .env.example                      # 复制为 .env，密钥不进仓库
├── app/
│   ├── main.py                       # 只做装配 + 统一错误体 + 启动恢复，零业务逻辑
│   ├── config.py                     # 3 个环境变量 + 契约调用参数基线
│   ├── constants.py                  # 错误码常量 + 业务码→HTTP 映射
│   ├── errors.py                     # GradingError
│   ├── routes/                       # ① 路由层：只声明路径、参数、状态码
│   │   ├── reports.py                #   POST /reports · POST /reports/{id}/grading · GET /reports/{id}/result
│   │   ├── templates.py              #   GET /templates
│   │   ├── grades.py                 #   GET /grades
│   │   ├── health.py                 #   GET /healthz
│   │   └── stub_data.py              #   占位数据（未挂载）
│   ├── controllers/
│   │   └── grading_controller.py     # ② 编排层：上传落盘（backend/uploads/）+ 触发评阅
│   ├── services/                     # ③ 业务层
│   │   ├── parser.py                 #   docx / pdf 解析（4003 / 4005）
│   │   ├── grader.py                 #   评分主流程：状态机 + 证据闸门 + 总分累加
│   │   ├── llm_client.py             #   GLM 适配；**未配置 GLM_API_KEY 时走 _mock_chat**
│   │   └── prompt_loader.py          #   按文件路径读提示词（不走 import）
│   ├── repositories/                 # ④ 数据层
│   │   ├── db.py                     #   DB_PATH = backend/autograder.db，原生 sqlite3
│   │   └── grading_repo.py           #   insert_template / mark_inflight_failed / …
│   └── prompts/
│       └── scoring_v1.md             # 提示词（纯数据目录，无 __init__.py）
├── scripts/
│   ├── seed.py                       # ★ 手动播种模板，演示前必跑
│   ├── smoke.py                      # 端到端冒烟（上传 → 触发 → 轮询 → 断言）
│   └── run_one_report.py             # 单份报告试跑
├── tests/                            # pytest：16 passed
└── samples/                          # 回归样本：4 份正常 docx + 失败用例 2 份
```

仓库根的 `templates/grading/` 是评分点模板的数据源（**当前只有 1 套**，见第 6 节）。

---

## 2. 跑起来

```bash
cd backend                                     # ★ 必须在 backend 目录下启动
python -m venv .venv && . .venv/Scripts/activate
pip install -r requirements.txt
cp .env.example .env                           # 填不填 GLM_API_KEY 见下

./.venv/Scripts/python.exe scripts/seed.py     # ★ 播种模板，不跑则模板为空、上传必报 4041
./.venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1
```

* 接口文档：http://127.0.0.1:8000/docs
* 健康检查：`GET /healthz` → `{"status":"ok","model":"glm-4.7"}`
* 自检：`python -m pytest -q`（期望 **16 passed**）、`python scripts/smoke.py`（期望末行 PASS）

### Mock 模式（演示默认走这条）

**`GLM_API_KEY` 留空 = 不调模型**，`llm_client.chat()` 直接返回 `_mock_chat()` 的确定性假数据。

* 不消耗额度、同输入必同输出、断网也能跑通全链路；
* 假数据的 `evidence` 是从报告原文真实截取的，所以证据闸门、字段形状、前端展示与真实链路一致；
* 单项 `reason` 会显示「mock 评分（未配置 GLM_API_KEY）」，`highlights` / `suggestions` 可能为空 —— 这是预期，不是 bug；
* **注意 mock 下模型项分数是固定值**，样本之间的差异只体现在规则项上。想让分数分层必须切真模型。

切真模型：在 `.env` 里填 `GLM_API_KEY`，重启即可，**不需要改代码**（会烧额度）。

---

## 3. 接口（契约 `docs/接口契约.md`）

| # | 方法 | 路径 | 说明 |
|---|---|---|---|
| ① | GET | `/api/v1/templates` | 模板列表（page / page_size / course → total/page/page_size/items） |
| ② | POST | `/api/v1/reports` | 上传，multipart：`file` + `template_id`；**201**，只落库返回 `status=uploaded` |
| ③ | POST | `/api/v1/reports/{report_id}/grading` | 触发评阅；**202**；进行中重复触发幂等，已完成再触发 409/4091 |
| ④ | GET | `/api/v1/reports/{report_id}/result` | 结果，**同时是唯一的轮询口**（终态：success / partial_success / failed） |
| ⑤ | GET | `/api/v1/grades` | 成绩列表（page / page_size / template_id / order，只列终态） |
| ⑥ | GET | `/healthz` | 部署自检 |

> `/grading` 是 **POST-only**（触发用），拿 GET 打它是 405 `Method Not Allowed` —— 前端轮询请打 ④。

状态机、错误码、字段定义全部按契约实现：

* 状态：`uploaded → parsing → parsed → grading → success / partial_success / failed`
* 错误码：`4001`(415) / `4002`(413·400) / `4003` / `4004`(400) / `4005` / `4041` / `4042` / `4091` / `5001–5005`
  统一错误体 `{code, message, detail}`
* 幂等：`file_sha256 + template_id` 重复上传 → 409/4091
* 时间：ISO 8601 带 `+08:00`；分数 1 位小数；`level` 按得分率五档（0.90 / 0.70 / 0.50 / 0）

契约里已登记的增补字段（`student` / `comment` / `highlights` / `suggestions`）均已返回。

### 未登记但已实现的差异（前端必须靠适配层兜底）

| 差异 | 说明 |
|---|---|
| 结果体**没有** `full_score` | 前端由 `items[].max_score` 求和得出 |
| 结果体**没有** `template_name` | 只有 `/grades` 列表项里带；结果页走模板缓存兜底 |
| **没有** `items[].channel` | 契约已明确本版本不引入。Step 3 的「判定方式」列据此**砍掉** |
| **没有** `GET /reports/{id}/text` | 契约 7.6 已登记，实现排期 9/24 上午。前端做容错版：接口不在就隐藏入口 |
| `/grades` 项带 `student` | 取值为「上传文件名去扩展名」，不一定等于真人姓名 |

---

## 4. 评分口径

1. **证据闸门**：模型给出的 `evidence` 必须能在原文中定位（去空白与标点后包含匹配，短于 6 字不算）。
   定位失败 → 只对该项补调一次模型；仍失败 → 该项不出分，并写入 `warnings`。
2. **`low_confidence` 不出分**：按契约「`status` 非 `graded` 时 `score` 为 `null`」实现，
   该项不计入 `total_score`，报告整体判为 `partial_success`。

---

## 5. 数据落盘位置（演示与清库）

| 内容 | 路径 | 是否进仓库 |
|---|---|---|
| SQLite 库 | `backend/autograder.db` | 否（`*.db`） |
| 上传的原始报告 | `backend/uploads/{report_id}.{ext}` | 否（`**/uploads/`） |
| 评分点模板数据源 | `templates/grading/*.json` | **是**（受版本控制，需要它才能播种） |
| 旧扁平版的库备份 | `/d/projects/_bak_flat_20260923/autograder.flat.db` | 否（在仓库外） |

**重置演示数据**：停掉后端 → 删 `backend/autograder.db` 与 `backend/uploads/` → 重启 → 重跑 `scripts/seed.py`。
（模板不在库里持久化之前，删库后必须重新播种。）

---

## 6. 演示前必须知道的 4 件事

1. **只有 1 套模板**：`tpl-1001`「数据结构实验报告评分模板」/ 100 分 / 7 个评分点。
   ⚠️ **这个 ID 的语义和旧扁平版不同**（旧版 `tpl-1001` 是程序设计类、`tpl-1002` 才是数据结构类），
   凡是对照旧预期分值的地方都要重算。`samples/` 里的「成绩管理」两份样本没有配套模板。
2. **`seed.py` 必须手跑**：四层版**没有**自动播种，忘了这步模板为空、上传直接 4041。
3. **幂等键是 `file_sha256 + template_id`**：同一份文件无法重复触发评阅。
   要演示「两次评阅分数一致性」，请准备两份**字节不同**的副本（另存为不同文件名 + 文末加一行空行）。
4. **`samples/失败用例/`**：`扫描版实验报告_无文本层.pdf` → 4003（注意是 **HTTP 200 后轮询到 failed**）；
   `非法格式示例.txt` → 前端预校验拦截。超限用任意 >20MB 文件。

> `scripts/smoke.py` 的默认样本已改指 `samples/单链表实验报告_张三.docx`
> （原指向仓库根 `data/samples/case_good.docx`，该文件不存在，裸跑必崩）。

---

## 7. 部署

```bash
npm run build            # frontend → dist/
# 后端：/opt/autograder/backend + 可写的 uploads/ 目录
```

```nginx
server {
    listen 80;
    server_name your.domain.or.ip;

    client_max_body_size 25m;     # 后端上限 20MB，nginx 留余量；否则前端只会看到 413 的 HTML
    proxy_read_timeout 180s;      # 评阅含排队与重试，默认 60s 会提前掐断
    proxy_send_timeout 180s;

    root /var/www/autograder/dist;
    index index.html;

    location / { try_files $uri $uri/ /index.html; }   # Vue history 路由必须

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```ini
# /etc/systemd/system/autograder.service
[Unit]
Description=AutoGrader API
After=network.target
[Service]
WorkingDirectory=/opt/autograder/backend
EnvironmentFile=/opt/autograder/backend/.env
ExecStart=/opt/autograder/backend/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1
Restart=always
[Install]
WantedBy=multi-user.target
```

注意：`workers` **只能是 1**（契约规定并发评分上限 1）；`.env` 权限 600；`uploads/` 必须可写；
部署包**必须包含仓库根 `templates/grading/`**，否则 `seed.py` 静默失败、模板总数 0、上传必报 4041。

---

## 8. 待办

1. **A**：`GET /reports/{id}/text`（契约 7.6 + 业务码 4090）实现，排期 9/24 上午；
   未完成的降级方案是「先部署不含 `/text` 的版本，/text 作 9/25 增量上线」。
2. **A**：第二套模板（若要覆盖「成绩管理」类样本）。
3. **C**：真实实验报告素材（好 / 中 / 差各 1 份先到，全量 ≥10 份），用于校准规则阈值与提示词锚点。
4. **A/B**：`docs/api.md`、`docs/interface-contract-v1.md` 已在文首标注为历史文档，
   合入后如需彻底移除，等 `/text` 上线一并处理。
