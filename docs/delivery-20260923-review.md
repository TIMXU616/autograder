# 交付包 AutoGrader_delivery_20260923.zip 核实报告

执行：B　日期：2026-09-23　范围：`AutoGrader_delivery_20260923.zip`（微信交付，1.31 MB，239 条目）

---

## 一、结论一句话

**A 这次说的三条全部属实，他给的核实路径也全部成立**（和上一轮完全不同，这次不是空头承诺）。

但包里的「仓库」不是 GitHub 上这个仓库 —— 它是一份**独立的本地 git 仓库**：`master` 分支、3 个提交、**没有 remote**、作者 `AutoGrader <autograder@local>`。所以两个人说的「仓库里有 / 没有」从来就不是同一件事。

---

## 二、A 的三条说法，逐条核实

### 1「detail 一律 null 合法吗？合法」—— 属实

契约第 152 行原文：

> detail 的取值规则：无附加信息时返回 `null`；有附加信息时返回对象，例如 4091 会在 detail 里带已有 `report_id`。前端按可选字段处理，不得假定 detail 一定有对象，读取时用可选链（如 `detail?.report_id`）。

- 由 `0ed8166` 引入，变更记录里有一行 2026-09-23，原因栏写着「B 提出公网返回 detail 一律 null，需要明确与契约的关系；**此为澄清，字段本身未变**」
- 同一节里 `detail: null` 与 `detail: {...}` 两种示例并存（第 233 行 4002 为 null，第 237 行 4002 为对象）
- 结论：规则成立，但 **4091 这一条契约要求必须带 `report_id`**。公网返回 `detail: null` 属于实现未跟上，不是契约允许的省略。前端用 `detail?.report_id` 是对的，但拿到 null 时仍要能兜底（见第四节）

### 2「grades 带 student 但契约没有？契约里有」—— 属实，我手上那份是旧版

| 位置 | 内容 |
| --- | --- |
| 第 120 行（5.4 GradingResult） | `student \| string \| null` |
| 第 141 行（5.5 GradeListItem） | `student \| string \| null` |
| 第 358/419/443/504/528/584/594 行 | 7.4、7.5 的 JSON 示例共 7 处带 student |
| 变更记录 | 2026-09-22 三行（5.4/7.4、5.5/7.5、以及"示例未同步"的补充行） |

我手上那份 `docs/interface-contract-v1.md` 里 `grep student` **零命中** —— 确实是 9/21 旧版。这一条 A 说得对。

### 3「7029d3a 已落成、文档都在、可以核」—— 属实

```
0ed8166 | 2026-09-23 01:06:21 | 契约补 detail 取值规则说明；部署记录补冻结版部署结果   ← HEAD
5f62be4 | 2026-09-22 19:48:30 | 移除运行时上传目录，补代码真值源与部署口径文档
7029d3a | 2026-09-22 19:48:01 | P2 后端冻结：四轮修复完成，真机验收通过（跑题用例三次全 0）  ← 首次提交
```

`docs/接口契约.md`（27,747 字节）、`docs/openapi.yaml`（10,663 字节）、`docs/部署记录.md`、`docs/代码真值源与部署口径.md`、`docs/试跑记录_P2_后端验收.md`、`prompt-library/`（15 个提示词留痕）、`templates/grading/` —— **全部存在**。

补一句他没说的：`7029d3a` 是这个仓库的**首次提交**（根提交），不是"某次改动后的冻结点"。也就是说整个 `AutoGrader` 仓库是 9/22 19:48 才建起来的。

---

## 三、真正的问题：两个仓库、两套后端、两份契约

### 3.1 A 的包是独立仓库，不是 GitHub 上这个

| | A 的包 `AutoGrader/` | 你的仓库（GitHub） |
| --- | --- | --- |
| 分支 | `master` | `dev` |
| 提交数 | 3 | 12 |
| 首次提交 | `7029d3a` 9/22 19:48 | `bcc1231` 9/20 02:33 |
| remote | **无**（`git remote -v` 空） | `github.com/TIMXU616/autograder` |
| 顶层目录 | backend / docs / templates / prompt-library / data / scripts | frontend / backend / docs / data |
| 作者 | `AutoGrader <autograder@local>` | `Tim`（11 次）、`phycho-18`（1 次） |
| 文件名编码 | GBK（解压默认乱码，需 cp437→gbk 转） | UTF-8 |

注：`phycho-18` 在 9/21 00:31 有一条 `chore: 测试推送权限` —— **A 是有推送权限的**，他后来没继续用 GitHub，改在本地建了另一个仓库。

### 3.2 两套后端，实测对比（都是真跑出来的）

| 对比项 | A 的冻结版（A 包，跑在 8001） | 你仓库这份（跑在 8000） |
| --- | --- | --- |
| 自述 | `AutoGrader`（无 version → 0.1.0） | `AutoGrader API` 1.0.0 |
| 健康检查 | `/healthz` | `/api/v1/health`（带 llm_mock / prompt_version） |
| 路由组织 | 4 个 router 模块（routes/ + controllers/ + repositories/ + services/ 四层） | 单 `routes.py`（7 个端点） |
| 模板数 | **1 套**（tpl-1001 数据结构实验报告评分模板） | **2 套**（tpl-1001 程序设计类…、tpl-1002…） |
| 模板项字段 | `item_id / name / max_score` | + `channel / criteria / rule_key / rule_config` |
| 规则通道（30 分确定性） | **无**（7 项全走模型） | **有**（3 项 rule） |
| items 字段 | 10 个，**无 `channel`** | 11 个，含 `channel` |
| `GET /reports/{id}/text` | **404，不存在** | **可用** |
| 结果体 | **缺 `full_score` / `template_name`** | 都有 |
| grades 带 `student` | **有** ✅ | **没有** ❌（DB 里有值，接口不输出） |
| 跑题用例（同份 case_offtopic.docx） | **0.0 分，七项全 absent** ✅ | **57.8 分** ❌（无确定性判据） |
| 种子 | 必须手动 `python scripts/seed.py`（不跑则 templates total=0） | 启动自动 seed（lifespan） |
| 测试 | pytest 16 passed | `scripts/contract_test.py` 59 通过 / 0 失败 |
| 错误码 400+4002 | ✅ | ✅（detail 带对象，与 A 新契约一致） |
| 幂等 409+4091 | ✅ | ✅ |

**两边是互补的，谁都不是谁的超集。**

### 3.3 两份契约

| | 你的 `docs/interface-contract-v1.md` | A 的 `docs/接口契约.md` |
| --- | --- | --- |
| 版本 | 9/21 冻结版 | 改到 9/23 |
| 体积 | — | 27,747 字节 |
| `student` | 无 | 有（5.4/5.5/7.4/7.5） |
| detail 取值规则 | 无 | 有（§6） |
| `channel` | 无 | **无** |
| `/text` | 无 | **无** |
| `full_score` / `template_name` | 无 | **无** |

### 3.4 硬冲突：A 自己给你的 Step 3 计划，在他自己的后端上做不了

A 的 Step 3 里写着：

- 动作 A：「判定方式用 **`item.channel`**：`rule` 显示「规则校验」、`llm` 显示「模型判定」—— 后端已增加这个字段（属契约增补）」
- 动作 B：「拉 **`GET /reports/{id}/text`**（增补接口，返回 `text` + `paragraphs` 坐标）」

实测他这版冻结后端：

```
GET /api/v1/reports/{id}/text   →  HTTP 404
items 字段                      →  10 个，无 channel
契约 grep channel | /text       →  零命中
```

**这两条只能在你仓库这套后端上做。** 他要么是忘了自己那版没这两个东西，要么是把两套后端记混了。

---

## 四、我这边做的处置（已完成）

1. **幂等复用加三级兜底**：`uploadReport` 现在按 `detail.report_id` → 按文件名反查 `/grades` → 抛可读中文提示 依次尝试。原因：公网 `detail: null`，若只认 `detail.report_id`，演示时重复上传会变成一屏红色报错
2. **student 展示后端优先**：`row.student || studentFromFilename(row.filename)`。现在两套后端都吃得下（A 那套给值就用，仓库这套不给值就按文件名推）
3. 演示数据恢复为 4 条干净样本（清掉了核实过程产生的测试记录）

---

## 五、建议（需 A 拍板，三选一）

**倾向方案：以 GitHub 仓库为唯一真值源，把 A 的 P2 修复移植进仓库这份 `backend/`**

- 需要移植进来的（都是小改动）：
  - 跑题领域术语确定性判据（正文术语命中为 0 → 强制清零，不依赖模型措辞）
  - 启动时把 in-flight 报告置 `failed`（避免重启后永久卡在 grading）
  - `/grades` 补 `student` 字段（与 A 新契约 5.5 对齐）
  - 可选：把他那份更好看的四层目录结构搬过来
- 不需要移植的（仓库这份已经更强）：自动 seed、`channel`、`/text`、`full_score`/`template_name`、2 套模板、3 个规则通道评分点
- 契约统一：**以 A 的 `docs/接口契约.md` 为基线**（它更新），把 `channel` / `/text` / `full_score` / `template_name` 正式补登记进 §10 变更记录

**替代方案 A：以 A 的冻结版为准** —— 那 Step 3 的动作 A、B 必须砍掉，等于放弃「规则校验 / 模型判定」这一列（这是回应"是不是 API 套壳"最直观的一屏）和原文高亮定位。

**替代方案 B：前端做能力探测、兼容两套** —— 3 天工期下不划算，不推荐。

---

## 六、给 A 的回执（可直接复制转发）

> 你的三条我全部核实过了，**都成立**：detail 取值规则确实在契约第 152 行、`0ed8166` 引入；student 确实在 5.4/5.5/7.4/7.5 共 9 处、9/22 三条变更记录；`7029d3a`、`docs/接口契约.md`、`openapi.yaml`、`部署记录.md` 全部在包里。我手上那份 `interface-contract-v1.md` 是 9/21 旧版，这条我认。
>
> **但有个前提得说清：你包里的 `AutoGrader/` 不是我们 GitHub 上那个仓库。** 它是 `master` 分支、只有 3 个提交、`git remote -v` 是空的、作者是 `AutoGrader <autograder@local>`。首个提交 `7029d3a` 就是 9/22 19:48 那次「P2 冻结」。所以你说的"仓库里有"我一直找不到 —— 我们俩说的不是同一个仓库。
>
> **仓库地址：https://github.com/TIMXU616/autograder**（Private，工作分支 `dev`）。你 9/21 00:31 那次 `chore: 测试推送权限` 是推上去了的，权限还在。麻烦把你的 master 推上来，我合：
>
> ```bash
> git remote add origin https://github.com/TIMXU616/autograder.git
> git push origin master:a/backend-p2
> ```
>
> **还有一件事必须你定：你现在这套冻结后端，做不了你自己给的 Step 3。** 实测：
> - `/api/v1/reports/{id}/text` → **404**，这个接口不存在
> - items 只有 10 个字段，**没有 `channel`**；你的契约里 `grep channel` 也是零命中
>
> 但你的 Step 3 动作 A 要求用 `item.channel` 显示「规则校验 / 模型判定」，动作 B 要求拉 `/text` 做原文定位高亮。**这两条只能在仓库那套后端上做**（仓库这份有 3 个 `channel='rule'` 的确定性评分点共 30 分、有 `/text`、有 `full_score`/`template_name`）。
>
> 另外两套后端还互相缺东西，得对齐：
> - 你这份：**`/grades` 带 student** ✅，但你缺 channel / `/text` / full_score / template_name；同一个跑题用例你得 0.0 分七项 absent，仓库那份得 57.8 —— 你的领域术语确定性判据仓库那份没有
> - 仓库这份：有 channel / `/text` / full_score / template_name / 2 套模板 / 自动 seed / contract_test 59 通过，但 **`/grades` 没有 student**，也没有你的跑题判据
>
> 我的建议：**以 GitHub 仓库为唯一真值源**，我把你的跑题确定性判据、启动 in-flight 恢复、grades 补 student 这三项移植进仓库这份 `backend/`，其余保留仓库的（它更全）。契约以你那份 `接口契约.md` 为基线，把 channel / `/text` / full_score / template_name 补登记进 §10。你如果同意我就动手；如果你坚持以你的冻结版为唯一交付，那 Step 3 的动作 A、B 得先砍掉，请明确说一声。

---

## 六之二、A 追问「`/text` 和 `items.channel` 是什么」—— 标准答案

这两个**不是我们发明的**，是 **A 自己那份 Step 3 卡片里点名要求的**（见 3.4）。
在仓库这套后端里它们是**契约 v1 未登记的增补**，在 A 的冻结版（`AutoGrader` 0.1.0）里**不存在**。

### 1. `items[].channel`：这一项是「谁」判的

- 取值只有两个：`rule` = 确定性规则通道（**完全不调模型**，同输入必然同输出）；`llm` = 模型判定。
- 前端用途：结果页「判定方式」列 —— `rule` 显示「规则校验」、`llm` 显示「模型判定」。
- 设计依据（`app/templates_seed.py` 头注释）：每套模板 **7 个评分点、总分 100，其中 3 个是
  `channel='rule'` 的确定性校验点共 30 分**，剩 4 个走模型。
- 落地位置：`app/db.py:31`（`CHECK (channel IN ('rule','llm'))`）、`app/scoring.py:165/181/188`
  （rule 项直接算分，llm 项才组装 prompt）、`app/models.py:66`（`channel: Optional[str]`，标注「增补」）。
- 真实响应样例（本机 :8000，`rpt-0c11644f`）：

```json
{"item_id": 1, "name": "结构与要素完整性", "max_score": 12, "score": 12.0,
 "level": "excellent", "status": "graded", "confidence": "high",
 "error_code": null, "channel": "rule", "evidence": "21001\n一、实验目的\n...",
 "reason": "必备章节命中 5/5：...；阶梯 5 节 12 / 4 节 9 / 3 节 6 / ≤2 节 3 → 12 分"}
```

### 2. `GET /api/v1/reports/{report_id}/text`：原文 + 段落坐标

- 定位（`app/routes.py:260`）：*"增补接口：返回原文与段落字符坐标，前端用它把 evidence 定位并高亮。"*
- 响应模型（`app/models.py:115-125`）：`{report_id, filename, text, paragraphs[{start, end, text}]}`
- 前端用途：结果页点某个评分项 → 用 `evidence` 在 `text` 里定位 → 按 `paragraphs` 坐标滚动并高亮。
- 真实响应样例（本机 :8000，`rpt-0c11644f`）：`text` 991 字、`paragraphs` 39 段，首段
  `{"start": 0, "end": 16, "text": "程序设计实验三：学生成绩管理程序"}`。
- 错误：报告不存在 → `4042 / HTTP 404`；尚未解析完 → `4003 / HTTP 200`。

### 3. 硬证据（可当场复现，两版后端都在跑）

```
:8000  openapi  info.title = "AutoGrader API"  version = 1.0.0   7 条路由
       /api/v1/{templates, reports, reports/{id}/grading, reports/{id}/result,
                reports/{id}/text, grades, health}

:8001  openapi  info.title = "AutoGrader"      version = 0.1.0   6 条路由
       /api/v1/{templates, reports, reports/{id}/grading, reports/{id}/result, grades}
       /healthz
       GET /api/v1/reports/{id}/text → {"detail":"Not Found"}   ← 框架级 404，路由根本没有
                                     （对比业务 404 长这样：{"code":4042,...}）
```

契约 grep：`channel` 0 处、`/text` 0 处、`full_score` 0 处、`student` 0 处
（`docs/interface-contract-v1.md`，我手上这份 9/21 旧版）。

### 4. 所以要 A 回答的问题（一句话）

**你重建的 `a/backend-p2` 里，保留了 `items.channel` 和 `GET /reports/{id}/text` 吗？**
保留 → 我直接合，Step 3 两条照做；不保留 → Step 3 的「判定方式列」与「点项定位原文高亮」
要么砍掉、要么请他补进 P2。

---

## 七、复现命令

```bash
# A 的包（独立环境，920KB 依赖）
cd <解压目录>/AutoGrader/backend
python -m venv .venv && ./.venv/Scripts/python.exe -m pip install -r requirements.txt
./.venv/Scripts/python.exe scripts/seed.py          # 不跑则 templates total=0
./.venv/Scripts/python.exe -m uvicorn app.main:app --port 8001 --workers 1

# 主链路
curl -X POST http://127.0.0.1:8001/api/v1/reports -F "file=@../data/samples/case_good.docx" -F "template_id=tpl-1001"
curl -X POST http://127.0.0.1:8001/api/v1/reports/<id>/grading
curl http://127.0.0.1:8001/api/v1/reports/<id>/result
```

---

## 八、遗留

1. 根目录 `test.txt`（11 字节）仍被 git 跟踪，交付前必须 `git rm`
2. 两份契约必须合并成一份，否则 C 写测试会照着旧版写
3. 公网实例 = A 那份冻结版的构建（title / `/healthz` / 1 套模板 / 缺 full_score 逐项一致），联调时不要拿它验 channel 和 `/text`
