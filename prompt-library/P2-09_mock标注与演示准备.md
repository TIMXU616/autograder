# mock 模式标注与演示准备

B 反馈：演示如果走 mock，结果页会把「mock 评分（未配置 GLM_API_KEY）」「骨架阶段占位评分」这类字样直接印给评委看。这件事的处理方向由我定了，本次只改后端，不新增接口。

## 一、结论先说

**演示必须走真模型（配 GLM_API_KEY）。** 但 mock 文案不能改成中性——中性化只会让「假分数」更难被发现，是给自己埋雷。所以：

- **mock 模式要显式自曝**：任何拿到结果的人都能一眼看出这不是真评分。
- 前端可以据此做差异化渲染（B 那边自行决定），后端只负责把标识给出来。

## 二、要改的地方

### 1. `app/services/llm_client.py` 的 `_mock_chat`

- 每条 item 的 `reason` 前缀加 `[模拟]`，正文写成中性但明确的话：`[模拟] 未调用模型，分数为占位值`。
- 顶层返回增加 `comment`，内容明说：`当前为模拟评分（未配置模型密钥），结果仅供联调，不代表真实评阅结论。`
- `highlights` 与 `suggestions` 返回空数组。
- `warnings` 数组第一条固定为：`模拟评分：未配置模型密钥，未调用 glm-4.7`。

### 2. `app/services/grader.py`

`_normalize` 里，如果 item 的 `reason` 以 `[模拟]` 开头，就在 warnings 里保证上面那条固定串只出现一次（mock 已经给了就不重复追加）。真模型路径不受任何影响。

### 3. `app/routes/health.py`

`/healthz` 的返回在 mock 模式下变成：

```json
{"status": "ok", "model": "mock", "mock": true}
```

配了 key 时保持现状：`{"status": "ok", "model": "glm-4.7", "mock": false}`。

注意：部署到公网后，平台的探活会拦截 `/healthz` 返回它自己的 JSON，所以**前端不要依赖 `/healthz` 判断 mock**，以结果体里 warnings 的那条固定串为准。

## 三、单测

补一个用例：mock 客户端下跑一次评分，断言

1. 每条 item 的 `reason` 以 `[模拟]` 开头；
2. `warnings` 里含 `模拟评分：未配置模型密钥，未调用 glm-4.7`，且只出现一次；
3. `comment` 非空且含「模拟」字样。

## 四、验收

1. pytest 全绿并附输出。
2. 不配 key 起服务，跑 `scripts/run_one_report.py ../data/samples/case_good.docx`，把完整输出贴回来——要能一眼看到 `[模拟]` 与那条 warning。
3. 配上 key 再跑同一条命令，输出里**不得**出现任何 `[模拟]` 与「模拟评分」字样（这条是防串味的，必须验）。
4. `/healthz` 两种情况各贴一次返回。

## 五、不许动

评分逻辑、跑题兜底、evidence 校验、重试参数、超长策略、现有接口形状，一律不动。
