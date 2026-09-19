# AutoGrader · 计算机实验报告智能评阅平台

> 深大计软 & 腾讯云 粤港澳大湾区 AI Coding 创新大赛 · 赛题方向一（AI + 教学管理助手）
>
> 支持实验报告自动解析、评分点逐项核查与成绩评语智能生成的智能评阅教学平台。

## 一、项目简介

高校计算机类实验课中，教师批改实验报告存在"重复劳动多、评分标准不统一、反馈滞后"的痛点。
本项目基于 LearnBuddy 平台的大模型能力，实现：

1. **报告自动解析**：支持 docx / pdf 实验报告上传与正文、代码块、截图的抽取
2. **评分点逐项核查**：按可配置的评分点模板逐项判定，给出每项得分与判定依据
3. **评语智能生成**：输出总评、亮点、改进建议
4. **成绩管理**：评阅记录列表、筛选、导出

## 二、技术栈

| 层 | 选型 |
|---|---|
| 前端 | Vue 3 + Vite + Element Plus + Vue Router + Axios |
| 后端 | Python 3.11 + FastAPI + Uvicorn |
| 文档解析 | python-docx / pdfplumber |
| AI 能力 | LearnBuddy 平台大模型能力 |
| 数据库 | SQLite（开发/演示） |
| 部署 | 单机 uvicorn 托管静态资源，浏览器直接访问 |

## 三、目录结构

```
autograder/
├── frontend/           # 前端工程（Vue3 + Vite）
├── backend/            # 后端服务（FastAPI）
├── data/               # 报告素材、种子数据、测试用例
├── docs/               # 需求文档、接口文档、测试报告
└── README.md
```

## 四、本地启动

### 后端

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

前端默认 `http://localhost:5173`，通过 `/api` 代理到后端 `http://localhost:8000`。

## 五、接口文档

见 [docs/api.md](docs/api.md)。

## 六、团队分工

| 角色 | 定位 | 核心职责 |
|---|---|---|
| A 主驾 | 产品 + AI 管线 | 需求文档、LearnBuddy 主对话、提示词迭代、评分后端、功能验收 |
| B 前端 | 集成与交付 | 线框图、页面开发与联调、UI 走查、部署、仓库管理 |
| C 数据测试 | 数据与质量 | 报告素材集、测试用例、质量抽检、README / 演示 / 答辩材料 |

## 七、协作规范

- 分支：`main` 为主干，日常开发走 `dev` 分支；合并 main 前在群里同步
- 提交信息格式见 [docs/commit-convention.md](docs/commit-convention.md)
- 接口文档在 P1 阶段结束后冻结，变更需三人确认

## 八、赛程

| 时间 | 事项 |
|---|---|
| 9/19 – 9/20 | P1 定稿期：需求 / 接口冻结、仓库与骨架、素材与建表 |
| 9/21 – 9/22 | P2 MVP 期：评分链路跑通、核心页面完成 |
| 9/23 – 9/24 | P3 联调部署期：前后端联调、在线链接可用 |
| 9/25 – 9/26 | P4 交付期：走查、材料制作、提交（9/26 23:59 截止） |
