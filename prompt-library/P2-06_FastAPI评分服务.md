# FastAPI 评分服务（解析 / 评分 / 入库三层）

目标：在本地让一份真实实验报告从文件走到出分并落库。本次只搭服务骨架，业务 HTTP 接口（上传、触发评阅、查结果、成绩列表、模板列表）留到下一步做，不要提前实现。

## 必读输入

- `docs/接口契约.md`：第 2 节调用参数、第 3 节状态机、第 5 节数据对象、第 6 节错误码。字段名与取值一律以它为准，不得自造。
- `docs/平台能力清单.md`：后端模型参数基线与降级链。
- `templates/grading/数据结构实验报告.json`：评分点模板，作为种子数据与提示词来源。
- `backend/app/prompts/scoring_v1.md`：评分提示词（可能还没产出，见第二节的处理方式）。

## 技术与目录（锁定）

- FastAPI + SQLite，前后端分离，无登录。
- 目录分层：`backend/app/routes/`、`backend/app/controllers/`、`backend/app/services/`、`backend/app/repositories/`，依赖只向下，禁止反向 import。
- 单文件不超过 300 行；入口 `main.py` 只做装配，零业务逻辑。
- 配置从 `backend/.env` 读取 `GLM_API_KEY`、`GLM_BASE_URL`、`GLM_MODEL`。禁止把密钥写进代码或日志，`.env` 不进仓库。
- 本次只实现一个 `GET /healthz`，返回 `{"status": "ok", "model": "<从配置读到的模型名>"}`。其余接口留到下一步。

## 模型调用参数（照抄，不得改动）

- base_url：`https://open.bigmodel.cn/api/paas/v4`，OpenAI 兼容。
- model：`glm-4.7`，请求体必须带 `"thinking": {"type": "disabled"}`。
- 单次超时 60 秒。
- 过载重试：遇 HTTP 429 或响应体错误码 1305，最多重试 3 次，间隔 3 秒、8 秒。
- 超时与 5xx 重试：1 次，与过载重试分开计数，互不占用次数。
- 并发上限 1：评分任务串行执行，用队列或信号量保证同一时刻只有一个模型请求在飞。
- 错误码映射：智谱 1302（并发超限）、1305（平台过载）重试耗尽后，对外表现为 5001。

## 一、解析层

- docx 走 python-docx，pdf 走 pdfplumber，只支持文本型文件。
- 统一输出结构：`{"text": str, "char_count": int, "source_type": "docx"|"pdf", "warnings": []}`。
- 异常映射，解析层任何情况都不许裸抛 500：
  - 文件 0 字节 → 4004
  - 扩展名不是 docx / pdf → 4001
  - pdf 抽出正文少于 50 字（判定为无文本层扫描件）→ 4003
  - pdf 打开时报加密异常 → 4005
- 单测三个用例：一份最小 docx、一份最小文本型 pdf、一份无文本层 pdf，覆盖上面三条异常路径中的两条。

## 二、评分层

提示词从 `backend/app/prompts/scoring_v1.md` 读取，靠三个机器可读标记定位，规则如下：

- `<!-- PARAMS -->` 之后的一个 json 代码块，含 `model`、`temperature`、`max_tokens`、`timeout_seconds`。
- `<!-- SYSTEM -->` 与 `<!-- USER -->` 之间是 system 提示词原文。
- `<!-- USER -->` 之后是 user 模板，含 `{template_json}` 与 `{report_text}` 两个占位符。
- 启动时校验三个标记齐全且各出现一次。缺失就抛出明确错误，错误信息里指明缺哪个标记；禁止用空提示词或内置兜底提示词静默降级。
- 若 `scoring_v1.md` 还没产出，把「读取与校验提示词」写成一个独立函数，允许用一个自造的 mini 样例（自己造一份只含三个标记和假提示词的文件）跑通单测，但代码路径必须与真实文件完全一致。

评分执行：

- 把模板 JSON 与该报告全文填进 user 模板，调模型。
- 模型应返回顶层六个键 `items` / `total_score` / `comment` / `highlights` / `suggestions` / `warnings`；出现其他键时忽略并在日志记录。缺 `comment` 或把 `highlights`、`suggestions` 写成字符串时，在 warnings 里记一条并按空值处理，不要让整体失败。
- 解析失败（非法 JSON）→ 重试 1 次；仍失败 → 5003。
- `total_score` 与各项 `score` 之和不等 → 以各项之和为准重算，并在 warnings 追加一条说明。
- 每项 `evidence` 与报告全文做归一化后的原样子串匹配（去掉空白与换行再比对）。失配的项降级为 `status=low_confidence`、`confidence=low`、`error_code=null`，保留得分，warnings 追加定位失败说明。不得判 failed，不得用 5003。
- 模型调用全部封装在 `llm_client.py`：负责超时、两类重试、429 / 1305 识别、错误码映射。评分逻辑不得直接碰 HTTP。
- 单测三条分支：总分自动重算、evidence 失配降级、非法返回触发 5003。用假响应客户端打桩，不打真实 API。

## 三、入库层

SQLite 三张表，字段与契约第 5 节一一对应：

- `reports`：report_id、template_id、filename、student、file_sha256、status、uploaded_at。`file_sha256` 与 `template_id` 建联合唯一索引，作为上传幂等键。student 取上传文件名去扩展名作为初值，取不到写 null。
- `grading_templates`：template_id、name、course、total_score、items（JSON 文本）、created_at。
- `grading_results`：report_id、attempt_no、model、status、total_score、comment、highlights（JSON 文本）、suggestions（JSON 文本）、consistency、warnings（JSON 文本）、error_code、items（JSON 文本）、grading_started_at、finished_at。

约定：

- `items` 用 JSON 文本列存储，理由写进回传：三表结构下最省事，避免为一个嵌套数组再拆两张表。若 C 已给出建表脚本，以 C 的脚本为准，冲突处在回传里说明。
- 时间统一 ISO 8601 带 `+08:00`。用 `datetime.now(timezone(timedelta(hours=8)))` 生成，不要依赖系统时区库，Windows 上 tzdata 常缺失。
- 重复插入幂等键冲突时，repository 层抛出可识别的自定义异常，供上层映射为 4091。本步不接 HTTP，只需保证异常类型可辨。
- 种子脚本 `scripts/seed.py`：把 `templates/grading/数据结构实验报告.json` 导入 `grading_templates`，重复执行不产生重复数据。

## 四、端到端脚本

`scripts/run_one_report.py <报告文件路径>`：解析 → 评分 → 入库 → 从库里读回并打印完整结果（每条评分项的 item_id、score、level、evidence 前 30 字、status）。

跑通一次，把完整输出存成 `docs/试跑记录_P2-06_端到端.md`。

## 验收（逐条给证据，不要只说做到了）

1. pytest 全绿，把输出贴进回传。
2. 端到端脚本对一份真实 docx 跑通，库里能查到完整的 grading_results 记录。
3. 无文本层 pdf 走到 4003，全程不出现 500。
4. 同一文件加同一模板连续入库两次，第二次命中唯一索引并抛出可识别异常。
5. 随机取一条 items 里的 evidence，在报告原文里能检索到。
6. 日志与代码里搜不到任何 API key。

## 自检

- 目录无反向依赖，`repositories` 不 import `services`。
- 没有文件超过 300 行。
- 没有硬编码密钥、提示词、错误码数字（错误码走常量或枚举）。
- 没有实现任何业务 HTTP 接口。
- 所有状态与错误码取值都来自契约，没有自造新值。
- 不用 emoji。

交稿时把目录树、pytest 输出、端到端脚本输出、以及你做的取舍说明一起回传。
