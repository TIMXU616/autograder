# backend · 后端服务（A 负责）

技术栈：Python 3.11 + FastAPI + Uvicorn + SQLite
文档解析：python-docx（docx）/ pdfplumber（pdf）
AI 能力：LearnBuddy 平台大模型能力（评分点逐项核查 + 评语生成）

## 目录规划

```
backend/
├── app/
│   ├── main.py          # 入口，挂载路由与静态资源
│   ├── api/             # 路由层
│   ├── services/        # 报告解析、评分链路
│   ├── prompts/         # 提示词模板（A 维护）
│   └── models/          # 数据模型
├── requirements.txt
└── README.md
```

## 启动

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

接口清单见 [../docs/api.md](../docs/api.md)。
