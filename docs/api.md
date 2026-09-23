# 接口文档（v1 · 待 A 在 9/20 晚冻结）

> ## ⚠️ 本文档已废弃（2026-09-23）
>
> **接口定义现以 [`docs/接口契约.md`](./接口契约.md) 为唯一依据，本文档不要用于实现。**
>
> 已知本文档与实现不符之处：接口前缀应为 **`/api/v1`**（本文写 `/api`）；
> 异步流程用的是 **`report_id`**（本文写 `task_id`）；状态机、错误码表、终态定义
> 均以 `docs/接口契约.md` 为准。保留本文档仅作需求演进过程的痕迹。

- Base URL：`/api`
- 请求/响应统一 `application/json`，文件上传为 `multipart/form-data`
- 评阅为异步流程：上传后返回 `task_id`，前端轮询状态接口

---

## 1. 上传报告并提交评阅

`POST /api/reports`

请求（multipart/form-data）：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| file | File | 是 | docx / pdf，≤ 20MB |
| template_id | int | 是 | 评分点模板 ID |

响应：

```json
{ "report_id": 12, "task_id": "t_20260920_001", "status": "grading" }
```

---

## 2. 查询评阅状态

`GET /api/reports/{report_id}/status`

```json
{ "report_id": 12, "status": "grading", "progress": 60 }
```

`status` 取值：`pending` / `grading` / `done` / `failed`

---

## 3. 查询评阅结果

`GET /api/reports/{report_id}/result`

```json
{
  "report_id": 12,
  "file_name": "数据结构实验三_张三.docx",
  "template_name": "数据结构实验报告评分模板",
  "total_score": 82,
  "full_score": 100,
  "comment": "整体完成度较好，但时间复杂度的推导过程缺少必要说明……",
  "highlights": ["代码结构清晰", "测试用例覆盖了边界情况"],
  "suggestions": ["补充算法复杂度分析", "实验结论需要与理论值对比"],
  "items": [
    { "name": "实验目的与原理", "score": 18, "full_score": 20, "reason": "原理阐述完整", "evidence": "第 1-2 节" },
    { "name": "算法设计与实现", "score": 30, "full_score": 35, "reason": "实现正确，但缺少复杂度推导", "evidence": "代码块 L20-L80" }
  ]
}
```

---

## 4. 成绩列表

`GET /api/reports?page=1&size=10&keyword=张三&template_id=1`

```json
{
  "total": 26,
  "list": [
    { "report_id": 12, "file_name": "数据结构实验三_张三.docx", "student": "张三",
      "total_score": 82, "template_name": "数据结构实验报告评分模板",
      "created_at": "2026-09-23 14:20:11" }
  ]
}
```

---

## 5. 评分点模板列表

`GET /api/templates`

```json
{
  "list": [
    { "template_id": 1, "name": "数据结构实验报告评分模板", "item_count": 6,
      "items": [ { "name": "实验目的与原理", "full_score": 20 } ] }
  ]
}
```

---

## 6. 导出成绩（加分项，P3 后决定是否实现）

`GET /api/reports/export?template_id=1` → 返回 xlsx 文件流
