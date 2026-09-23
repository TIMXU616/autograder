# AutoGrader 后端（FastAPI + SQLite）· 契约 v1 实现

> 本目录是 `docs/interface-contract-v1.md` 的后端实现，已用 `scripts/contract_test.py`
> 跑通 **59 项契约断言（0 失败）**。前端（Vue3 + Element Plus）不改，只需把
> `frontend/src/api/index.js` 第 24 行的 `USE_MOCK` 改成 `false`。
>
> 放入仓库：把本目录内容整体放到 `backend/`（覆盖现有 README.md 里那份目录规划）。

---

## 0. 取舍说明

| 决策 | 理由 |
|---|---|
| 不引 ORM / Alembic，原生 sqlite3 + WAL | 单机单进程够用；改字段只需换库重启，4 天工期内少一层调试成本 |
| 评分管线跑在进程内后台线程，`--workers 1` | 契约规定并发评分上限 1（串行），单进程最稳，不需要 Celery/Redis |
| 模型调用整份报告**一次**打包，只对证据定位失败的单项补调一次 | 额度有限（初赛 2500 credits/队），按项调用会把成本乘以评分点数 |
| 上传：先校验再落盘（读进内存 ≤20MB） | 失败路径不产生垃圾文件；20MB 上限下内存开销可忽略 |
| 总分由后端累加各项得分，模型不输出总分 | 从根上消除「总分与各项之和对不上」这类演示事故 |
| 30 分走规则通道，完全不经过模型 | 可复现、零幻觉，是回应「API 套壳」质疑的实物证据 |

---

## 1. 目录结构

```
backend/
├── requirements.txt
├── .env.example                 # 复制为 .env，key 不写进代码
├── app/
│   ├── config.py                # 环境变量 + 契约参数基线（超时/重试/20MB/队列 120s）
│   ├── db.py                    # 4 张表：templates / template_items / reports / grade_items
│   ├── templates_seed.py        # 2 套模板（各 7 点 / 100 分，规则项 30 分）
│   ├── rules.py                 # 规则通道：5 个确定性校验器
│   ├── parser.py                # docx/pdf 解析（含 4003/4005 错误码）
│   ├── llm.py                   # OpenAI 兼容适配层（GLM 基线 + 过载/超时重试）
│   ├── prompts.py               # 评分提示词（JSON 契约 + 证据补调）
│   ├── scoring.py               # 状态机 + 双通道评分 + 证据闸门 + 总分累加
│   ├── models.py                # 响应模型（契约字段 + 增补字段）
│   ├── routes.py                # 契约 7.1–7.5 五个接口 + 2 个增补接口
│   └── main.py                  # 入口 + 统一错误体 {code,message,detail}
└── scripts/
    └── contract_test.py         # 契约一致性测试（可当 C 的断言基线）
```

---

## 2. 跑起来

```bash
cd backend
python -m venv .venv && . .venv/Scripts/activate      # Windows
pip install -r requirements.txt
cp .env.example .env                                   # 联调阶段保持 LLM_MOCK=1
uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1
```

* 接口文档：http://127.0.0.1:8000/docs
* 自检：`python scripts/contract_test.py` → 期望「契约一致性：59 通过 / 0 失败」
* `LLM_MOCK=1` 用确定性假数据跑通全链路，**不消耗额度**；拿掉该开关即可切真实模型，
  不需要改任何代码（假数据的 evidence 也是从报告原文真实截取，所以闸门、字段、
  前端展示与真实链路完全一致）。

> 放进仓库后请把 `.env` 里的 `DATA_DIR` 改成 `./data`（在 backend 内）或 `../data`（在仓库根），
> 避免和 `data/`（报告素材）混淆；`*.db`、`data/uploads/`、`.env` 已在仓库 `.gitignore` 中。
> `WEB_DIR` 默认指向 `../frontend/dist`，dist 不存在时不挂载静态文件（由 nginx 托管）。

---

## 3. 接口（契约 v1）

| # | 方法 | 路径 | 契约 | 说明 |
|---|---|---|---|---|
| ① | GET | `/api/v1/templates` | 7.1 | 模板列表（page / page_size / course，返回 total/page/page_size/items） |
| ② | POST | `/api/v1/reports` | 7.2 | 上传，multipart：`file` + `template_id`；**201**，只落库返回 `status=uploaded` |
| ③ | POST | `/api/v1/reports/{report_id}/grading` | 7.3 | 触发评阅；**202**；进行中重复触发幂等，已完成再触发 409/4091 |
| ④ | GET | `/api/v1/reports/{report_id}/result` | 7.4 | 结果 + 轮询口（终态：success / partial_success / failed） |
| ⑤ | GET | `/api/v1/grades` | 7.5 | 成绩列表（page / page_size / template_id / order，只列终态） |
| ⑥ | GET | `/api/v1/reports/{report_id}/text` | 增补 | 原文 + 段落坐标，供「证据高亮」面板使用 |
| ⑦ | GET | `/api/v1/health` | 增补 | 部署自检（Mock 开关、模型名、提示词版本） |

状态机、错误码、字段定义全部按契约实现：

* 状态：`uploaded → parsing → parsed → grading → success / partial_success / failed`
* 错误码：4001(415) / 4002(413·400) / 4003 / 4004(400) / 4005 / 4041 / 4042 / 4091 / 5001–5005
  统一错误体 `{code, message, detail}`
* 幂等：`file_sha256 + template_id` 重复上传 → 409/4091，`detail.report_id` 返回已有报告
* 时间：ISO 8601 带 `+08:00`；分数：1 位小数；`level`：按得分率五档（0.90/0.70/0.50/0）

### 契约增补（需在契约「变更记录」追加一行后生效）

| 字段 / 参数 | 位置 | 依据 |
|---|---|---|
| `student`、`template_name`、`full_score`、`comment`、`highlights`、`suggestions` | GradingResult | B1（结果页四大板块，缺两块会明显减分） |
| `keyword` | GET /grades | B2（否则搜索框只能前端过滤，破坏分页语义） |
| `channel`（`rule` / `llm`） | GradingItem | 本方案需要：展示「规则校验 / 模型判定」，是抗「套壳」质疑最直观的一屏 |

> 三个 `rule` 评分点（每套模板 30 分）完全由规则代码判定，不经过模型 ——
> 这是「AI 能力应用的深度与独特性」可以直接讲的东西。

---

## 4. 评分口径（需要 A/C 确认的两条）

1. **证据闸门**：模型给出的 `evidence` 必须能在原文中定位（去空白与标点后包含匹配，短于 6 字不算）。
   定位失败 → 只对该项补调一次模型；仍失败 → 该项 `status = low_confidence`、`score = null`、
   `evidence = null`，并写入 `warnings`；模型没给引用 → 同样不出分。
2. **`low_confidence` 不出分**：严格按契约 5.3「status 非 graded 时 score 为 null」实现，
   即该项不计入 `total_score`，报告整体判为 `partial_success`。
   如果教研口径更希望「降权出分」（比如按 60% 给出一个暂定分），需要改契约
   （允许 `low_confidence` 时 `score` 非 null），当前实现不这么做。

---

## 5. 前端联调（B 的三个动作）

1. `frontend/src/api/index.js` 第 24 行：`const USE_MOCK = true` → `false`
2. `frontend/vite.config.js` 已配好 `/api → http://localhost:8000` **无需改动**
3. 上传页轮询判断改为 `success / partial_success / failed` 三个终态（契约 3 节），
   `progress` 用状态阶段换算；结果页 `level` / `status` / `confidence` 直接用后端返回值，
   不要自己算分档（避免口径漂移）

建议顺序：先切**上传 + 结果页**（主链路），验收后再切成绩页与模板页。

---

## 6. 联调验收清单

| # | 验什么 | 期望 |
|---|---|---|
| 1 | 上传 → 触发 → 轮询 → 结果 | 一份真实 docx ≤90 秒出结果；页面零 Mock |
| 2 | 总分自校验 | 前端自己 reduce 各项得分 == `total_score`（1 位小数） |
| 3 | 证据闸门 | 用 `/text` 对 `channel='llm'` 且 `status='graded'` 的项做 `text.includes(evidence)`，全部命中 |
| 4 | 规则通道可复现 | 规则项的分数与规则细节每次完全一致（模型项允许小幅波动） |
| 5 | 失败路径 | `.doc`、超大文件、扫描版 PDF、报告不存在 → 都有可读文案 + 错误码，不白屏 |
| 6 | 幂等 | 同一文件同模板重复上传 → 前端提示「该报告已存在」并复用 `report_id` |
| 7 | 部分失败展示 | `partial_success` + `warnings` 警示条；未出分项显示「未出分」并附 `error_code` |
| 8 | 上线 | 手机 4G 打开链接完成一次完整评阅；刷新结果页不 404 |

> 演示提醒：契约的幂等键是 `SHA-256 + template_id`，因此**同一份文件无法重复触发评阅**。
> 若要演示「同一报告两次评阅的分数一致性」，请准备两份**字节不同**的副本
> （例如另存为不同文件名并在文末加一行空行）。

---

## 7. 部署

```bash
npm run build            # frontend → dist/，放到 /var/www/autograder/dist
# 后端：/opt/autograder/backend + 可写的 data/ 目录
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

注意：`workers` 只能是 1；`.env` 权限 600；`data/` 必须可写。

---

## 8. 待办

1. **C（阻塞项）**：真实实验报告素材（好/中/差各 1 份先到，全量 ≥10 份），
   用于校准规则阈值与提示词锚点。
2. **A**：确认第 4 节的证据闸门口径与 `low_confidence` 是否「不出分」；
   在契约「变更记录」追加上面三个增补字段。
3. **A**：`docs/openapi.yaml` 与 `docs/试跑记录_GLM_API诊断.md` 被契约正文引用但仓库里不存在，
   补上或从正文去掉引用；根目录 `test.txt` 疑似误提交。
4. **A/B 口径统一**：`backend/README.md` 现在写的是「LearnBuddy 平台大模型能力」，
   契约第 2 节写的是智谱 GLM —— 两者要统一说法，否则 PPT 与实现互相矛盾。
