# 评分提示词 v1 撰写任务

这份提示词是后端运行时真正发给大模型的那段文字，不是给人看的说明。你要产出可直接复制进代码的 system 与 user 模板，并用四个用例实跑验证。

## 输入（自己读取以下几份文件）

- `templates/grading/数据结构实验报告.json`
- `templates/grading/数据结构实验报告_评分点.md`
- `docs/接口契约.md` 第 2 节（调用参数基线）、第 5 节（数据对象）、第 6 节（错误码）

## 产出物

1. `backend/app/prompts/scoring_v1.md`：生产用提示词文档。文件里必须带三个机器可读标记，供后端直接读取，写法见第一节第 7 条。
2. `docs/试跑记录_P1-05_prompt_v1.md`：试跑记录，含每次的原始输入与原始输出。
3. `data/samples/` 下四个用例文件：`case_good.md`、`case_mid.md`、`case_code_only.md`、`case_offtopic.md`。

## 一、提示词文档必须包含的部分

1. 调用参数（写给后端实现看）：model 用 glm-4.7，必须带 `"thinking": {"type": "disabled"}`，单次超时 60 秒，过载重试与超时重试分开计数。这些数字照抄契约第 2 节，不得改动，也不得补充别的数值。
2. system 提示词正文，可直接复制进代码。
3. user 模板正文，含 `{template_json}` 与 `{report_text}` 两个占位符；模板 JSON 里每项的 criteria、levels、question、pitfall 必须原样嵌入，不得改写、不得压缩、不得换词，保证这段提示词自包含。
4. 三版参数：严格版、平衡版、宽松版。每版写清判定松紧的差别、temperature 取值、适用场景，并明确指出哪一版是默认。
5. 超长报告的处理策略，见第五节。
6. 字段对齐表：模型输出字段与契约第 5 节字段逐行对应。
7. 机器可读标记，后端靠它解析这份文件，标记写法不得改变：

- `<!-- PARAMS -->`、`<!-- SYSTEM -->`、`<!-- USER -->` 三个标记各占一行，顺序就是这个顺序，每个只出现一次。
- `<!-- PARAMS -->` 紧随其后的一个 json 代码块里写 `{"model": "glm-4.7", "temperature": 数字, "max_tokens": 数字, "timeout_seconds": 60}`，数字按你选定的默认版填。
- `<!-- SYSTEM -->` 与 `<!-- USER -->` 之间是 system 提示词正文。
- `<!-- USER -->` 之后是 user 模板正文，其中含 `{template_json}` 与 `{report_text}` 两个占位符。
- system 与 user 正文里不得再出现这三个标记的字样。

## 二、输出 JSON 的硬约束（写进 system）

模型只输出一个 JSON 对象，顶层只有三个键：

```json
{"items": [], "total_score": 0.0, "warnings": []}
```

items 每项十个字段，字段名与语义必须与契约第 5.3 节完全一致：

| 字段 | 类型 | 要求 |
| --- | --- | --- |
| item_id | integer | 与模板一致，从 1 连号 |
| name | string | 与模板完全一致，不得改写 |
| max_score | integer | 与模板完全一致，不得改动分值 |
| score | number 或 null | 保留 1 位小数，0 到 max_score 之间；status 非 graded 时为 null |
| level | string 或 null | excellent / good / fair / weak / absent；按得分率判定 |
| evidence | string 或 null | 报告原文的连续子串，一字不改；不得拼接两处文字；找不到填 null |
| reason | string | 中文一句话，说清给分或扣分依据 |
| status | string | graded / failed / low_confidence / skipped |
| confidence | string | high / medium / low |
| error_code | integer 或 null | 仅 status 为 failed 时填 5002，其余为 null |

必须写清的两件事：

- level 是档位（判得怎么样），status 是执行状态（有没有评出来），两者取值集合不重叠，不得混用。
- 禁止输出 report_id、template_id、filename、顶层 status、attempt_no、model、consistency、时间戳这些字段，它们由后端填充。

## 三、文本与格式硬约束（写进 system）

- 只输出 JSON 一个对象。前后不加任何文字，不用 Markdown 代码块包裹，不写「好的」「以下是」。
- 全部中文，字段名与枚举值除外。
- 只依据报告原文判断，报告里没有的内容不许臆造，不许「推测学生应该做过」。
- 确实找不到依据的评分项：score 填 0，level 填 absent，status 填 graded，confidence 填 high，reason 写明报告中未找到相关内容，并在 warnings 里追加一条。
- total_score 必须等于各项 score 之和，status 为 failed 的项按 0 计入；输出前自己核算一遍。
- 数字写成数字，不要写成字符串。

## 四、四个用例与试跑要求

四个用例每个 600 到 1200 字，用真实实验报告的口吻写，不要写成问题清单：

- `case_good`：章节完整、有具体测试数据、有结果分析，并提到异常或边界情况。
- `case_mid`：章节齐全，但测试数据只有一组、分析基本是复述数据、没有异常情况说明。
- `case_code_only`：大段代码，几乎没有正文说明。
- `case_offtopic`：内容与数据结构实验无关（例如写成食堂消费调研）。

试跑：四个用例各跑一次，原始输出完整贴进试跑记录，逐条记录：

1. 是否 json.loads 成功。
2. items 是否七项，每项是否十个字段齐全。
3. 每条 evidence 能否在用例原文中检索到，逐条写命中或未命中。
4. total_score 是否等于各项 score 之和。
5. warnings 是否按预期触发，`case_code_only` 与 `case_offtopic` 必须触发。

另外用 `case_good` 连跑 5 次，验证 json.loads 连续 5 次成功。

## 五、超长报告处理策略

给出具体做法，不许写「视情况」：

- 触发阈值：正文字数超过多少字时启用分段。
- 分段规则：按什么切（章节标题、字数上限），说明如何处理代码块，避免把一段代码从中间切断。
- 合并规则：同一评分项在多个分段都产出判定时怎么取值；evidence 取哪一段的；分数怎么定。
- 自洽说明：合并后 total_score 仍等于各项之和，不会因为分段出现重复计分。

## 六、自检

交稿前逐项过：

1. system 里十个字段名与契约第 5.3 节逐字一致。
2. 顶层只有 items、total_score、warnings 三个键。
3. level 与 status 的取值集合正确，没有互相串用。
4. 三版参数都给了 temperature 与适用场景，默认版标注清楚。
5. 超长策略有具体阈值和可执行步骤。
6. 四个用例都写了、都实跑过，试跑记录里能看到原始输出。
7. `case_good` 连跑 5 次全部 json.loads 成功。
8. 跑题用例不硬评：各项 0 分加 warnings，没有出现任何得分。
9. scoring_v1.md 里三个机器可读标记齐全、顺序正确、各只出现一次，正文里没有重复出现标记字样。

任何一项没过，重做再交。
