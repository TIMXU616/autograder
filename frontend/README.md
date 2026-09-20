# frontend · 前端工程（B 负责）

技术栈：Vue 3 + Vite + Element Plus + Vue Router + Axios
（不引入 Pinia / TypeScript，8 天周期以"跑通 + 好看"为第一目标）

## 页面清单

| 路由 | 页面 | 关键交互 | 状态 |
|---|---|---|---|
| `/upload` | 上传报告 | 拖拽上传、格式与大小校验、选择评分模板、轮询评阅状态 | 骨架已完成 |
| `/result/:id` | 评阅结果 | 总分仪表盘、评分点逐项核查表格、评语、亮点与建议 | 骨架已完成 |
| `/reports` | 成绩管理 | 列表、关键词/模板筛选、分页、跳转结果页 | 骨架已完成 |
| `/templates` | 评分模板 | 模板卡片网格、评分点明细 | 骨架已完成 |

## 目录结构

```
frontend/
├── index.html
├── vite.config.js          # @ 别名、/api 代理到 localhost:8000
├── package.json
└── src/
    ├── main.js             # 挂载 Element Plus（中文语言包）
    ├── App.vue             # 左侧导航 + 内容区布局
    ├── router/index.js     # 四条路由 + 兜底重定向
    ├── api/index.js        # 接口层，USE_MOCK 开关
    ├── mock/data.js        # Mock 数据：3 套模板 / 6 条成绩 / 1 份完整评阅结果
    ├── styles/tokens.css   # 设计 Token：色值、字号、间距、圆角
    ├── styles/global.css   # 基础样式与通用类（ag-page / ag-card 等）
    └── views/              # 四个页面
```

## 开发约定

- **禁止硬编码色值 / 字号 / 间距**，一律引用 `var(--ag-*)`，Token 统一定义在 `styles/tokens.css`
- 图标统一用 `@element-plus/icons-vue`（SVG 组件），**不使用 emoji 作图标**
- 接口调用只写在 `src/api/index.js`，页面不直接引 axios
- 单个 `.vue` 文件控制在 300 行以内
- 页面需处理三态：加载中（`el-skeleton` / `v-loading`）、空数据（`el-empty` / `empty-text`）、错误（`ElMessage.error`）

## 启动

```bash
npm install          # 国内网络慢时加：--registry=https://registry.npmmirror.com
npm run dev          # 打开 http://localhost:5173
```

## 联调（接 A 的后端）

1. 把 `src/api/index.js` 里的 `const USE_MOCK = true` 改成 `false`
2. 启动后端：`uvicorn app.main:app --reload --port 8000`（`/api` 代理已配好）
3. 页面代码无需任何改动
