# Agent 智能文档审核系统

AI 驱动的合同智能审核平台，聚焦 NDA（保密协议）的自动解析、AI 风险识别与人工审批协同。

## 项目简介

传统的合同审核依赖法务人员逐条阅读，耗时长、成本高、容易遗漏风险。本系统利用 AI Agent 自动化合同解析和风险识别流程，同时保留人工审批的关键决策权——即 **Human-in-the-Loop (HITL)** 模式，让 AI 做初筛，人工做终审。

### 核心能力

- **文档上传与5层校验** — 支持 PDF/DOCX，自动检测格式、加密、损坏、OCR 需求
- **AI 多 Agent 并行解析** — 条款提取、风控分析、合规检查、报告生成四个 Agent 协同工作
- **三级风险分级审批** — 高风险逐条审批、中风险批量确认、低风险抽样审计
- **实时 SSE 推送** — Web 端实时展示解析和审核进度
- **审阅报告生成与签署** — 自动聚合审批结果，导出 PDF 报告并支持在线签署

## 技术栈

### 前端

| 技术 | 说明 |
|------|------|
| React 18 + TypeScript | SPA 应用框架 |
| Vite 5 | 构建工具，支持 HMR 热更新 |
| React Router v6 | 客户端路由，7 个页面 |
| SSE (Server-Sent Events) | 实时事件流，解析/审核进度推送 |
| CSS Variables | 主题变量系统，支持深浅色模式 |

### 后端

| 技术 | 说明 |
|------|------|
| FastAPI | 异步 Web 框架，32 个 REST API 端点 |
| SQLAlchemy 2.0 (async) | ORM，14 个数据模型 |
| SQLite / PostgreSQL | 开发/生产数据库 |
| LangGraph | AI 工作流编排，StateGraph + Checkpointer |
| Pydantic v2 | 请求/响应验证和序列化 |
| ReportLab | PDF 报告生成 |

## 快速开始

### 环境要求

- **Python** >= 3.12
- **Node.js** >= 18
- **Git Bash** (Windows) 或终端 (macOS/Linux)

### 1. 克隆项目

```bash
git clone <repo-url>
cd Agent_Teams_Project
```

### 2. 启动后端

```bash
cd backend

# 首次运行：创建虚拟环境并安装依赖
python -m venv .venv
source .venv/Scripts/activate  # Windows Git Bash
# 或 source .venv/bin/activate  # macOS/Linux
pip install -e .
# 如果 pyproject.toml 中缺少依赖，手动安装：
pip install fastapi uvicorn[standard] sqlalchemy[asyncio] aiosqlite pydantic pydantic-settings python-jose[cryptography] python-multipart sse-starlette reportlab

# 启动服务（默认 http://localhost:8000）
cd src
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. 启动前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器（默认 http://localhost:3000）
npm run dev
```

### 4. 打开浏览器

访问 **http://localhost:3000** 即可使用完整应用。

### 5. 生成测试数据（可选）

```bash
cd backend
python scripts/generate_test_docs.py
```

这会生成 5 份包含真实中文条款的 NDA 测试文档（每份 10 条条款），并通过 API 上传到系统。每份文档会自动生成 12 条模拟 AI 风险标记（3 HIGH + 5 MEDIUM + 4 LOW）。

## 用户使用流程

```
上传 NDA 文档 → 5层自动校验 → AI 多 Agent 并行解析 → AI 风险审核
                                                              ↓
签署报告 ← 查看审阅报告 ← 提交审阅 ← 人工审批工作台
                                    ├── 高风险：逐条审批（同意/编辑/驳回）
                                    ├── 中风险：批量确认（支持升级为高风险）
                                    ├── 低风险：抽样审计（支持升级标记）
                                    └── 手动补充标记
```

### 7 个页面路由

| 路由 | 页面 | 说明 |
|------|------|------|
| `/dashboard` | 工作台 (P1) | 统计卡片、最近审阅、文档列表 |
| `/review/new` | 新建审阅 (P2) | 4步上传向导：选择文件→校验→配置→启动 |
| `/review/:id/parsing` | 解析进度 (P3) | 实时 SSE 进度，4 Agent 状态卡片 |
| `/review/:id/reviewing` | AI 审核 (P4) | Agent 并行卡片，支持暂停/恢复 |
| `/review/:id/workspace` | 审批工作台 (P5) | 三栏布局：文档原文+条款定位+审批操作 |
| `/review/:id/report` | 审阅报告 (P6) | 风险聚合统计、高风险清单、签署 |
| `/review/history` | 历史审阅 (P7) | 状态筛选、关键词搜索、分页 |

## API 接口

Base URL: `/api/v1` | 认证: `Authorization: Bearer <token>` | 响应格式: `{code, message, data, request_id}`

### 接口总览 (32个)

| 组 | 接口 | 说明 |
|------|------|------|
| **上传** | `POST /documents/upload` | 上传文档 (multipart/form-data) |
| | `GET /documents` | 文档列表 (分页+筛选) |
| | `GET /documents/{id}` | 文档详情 |
| | `GET /documents/{id}/file` | 下载原始文件 |
| | `POST /documents/{id}/parse` | 启动 AI 解析 |
| | `POST /documents/{id}/parse/retry` | 重试解析 |
| **审核** | `POST /documents/{id}/review` | 启动 AI 审核 |
| | `POST /documents/{id}/review/pause` | 暂停审核 |
| | `POST /documents/{id}/review/resume` | 恢复审核 |
| | `POST /documents/{id}/review/cancel` | 取消审核 |
| | `POST /documents/{id}/review/retry` | 重试审核 |
| | `GET /documents/{id}/clauses` | 获取条款列表 |
| | `GET /documents/{id}/risk-flags` | 获取风险标记列表 |
| | `GET /risk-flags/{id}/playbook-diff` | 获取 Playbook 对比 |
| | `GET /risk-flags/{id}/decisions` | 获取审批历史 |
| | `GET /documents/{id}/review-summary` | 审批进度摘要 |
| **HITL** | `POST /risk-flags/{id}/approve` | 同意 AI 标记 |
| | `POST /risk-flags/{id}/edit` | 修正 AI 标记 |
| | `POST /risk-flags/{id}/reject` | 驳回 AI 标记 |
| | `POST /risk-flags/batch-approve` | 中风险批量确认 |
| | `POST /risk-flags/sample` | 低风险抽样审计 |
| | `POST /risk-flags/{id}/escalate` | 升级风险等级 |
| | `POST /risk-flags/manual` | 手动补充标记 |
| | `POST /documents/{id}/submit` | 提交审阅 |
| | `POST /documents/{id}/save-draft` | 暂存草稿 |
| **报告** | `GET /documents/{id}/report` | 获取审阅报告 |
| | `GET /documents/{id}/report/export` | 导出 PDF 报告 |
| | `POST /documents/{id}/report/sign` | 签署报告 |
| | `GET /documents/{id}/audit-logs` | 审计日志 |
| **其他** | `GET /dashboard/stats` | 工作台统计 |
| | `GET /documents/{id}/events` | SSE 实时事件流 |
| | `GET /playbooks` | Playbook 规则列表 |

## 项目结构

```
Agent_Teams_Project/
├── frontend/                     # React 18 + Vite + TypeScript
│   ├── src/
│   │   ├── api/                  # API 客户端 (5 个模块)
│   │   ├── components/           # UI 组件
│   │   │   ├── approval/         # 审批卡片、驳回对话框
│   │   │   ├── layout/           # 侧边栏、全局布局
│   │   │   └── shared/           # 通用组件 (Badge, Pagination, 等)
│   │   ├── pages/                # 7 个页面组件
│   │   ├── styles/               # 全局样式 + CSS 变量
│   │   └── types/                # TypeScript 类型定义
│   └── vite.config.ts            # Vite 配置 (含 /api 代理)
├── backend/                      # FastAPI + SQLAlchemy + LangGraph
│   ├── src/
│   │   ├── agents/               # 4 个 AI Agent 定义
│   │   ├── api/routes/           # 4 个路由组
│   │   ├── core/                 # 配置、数据库、认证、异常
│   │   ├── hitl/                 # HITL 中断点、约束、会话管理
│   │   ├── models/               # 14 个 ORM 数据模型
│   │   ├── schemas/              # Pydantic 请求/响应模型
│   │   ├── services/             # 业务逻辑层
│   │   ├── utils/                # 文件校验、哈希链、分页
│   │   └── workflow/             # LangGraph 工作流定义
│   ├── tests/                    # 51 个测试用例
│   └── pyproject.toml            # Python 项目配置
├── docs/                         # 设计与规范文档 (12 阶段)
│   ├── 00_setup/                 # 项目初始化与规范搭建
│   ├── 01_business_research/     # 业务调研
│   ├── 02_competitive_analysis/  # 竞品分析
│   ├── 03_business_modeling/     # 业务问题建模
│   ├── 04_interaction_design/    # 核心交互链路设计
│   ├── 05_product_prototype/     # 产品原型规范
│   ├── 06_system_architecture/   # 系统架构设计
│   ├── 07_data_model/            # 数据模型
│   ├── 08_api_specification/     # API 规范
│   ├── 09_frontend_plan/         # 前端实现计划
│   ├── 10_backend_plan/          # 后端实现计划
│   ├── 11_integration/           # 联调方案
│   └── 12_deployment/            # 发布和部署
├── .claude/                      # Claude Code 配置
│   ├── agents/                   # 自定义 Agent 定义
│   └── settings.json             # Agent Teams + MCP 配置
├── CLAUDE.md                     # 项目级 AI 开发指引
├── README.md                     # 本文件
└── .gitignore
```

## 开发说明

### 后端开发模式

当前 MVP 阶段使用 **Mock Services** 替代真实 AI Agent 调用。Mock 服务返回完整的条款、风险标记和审批数据，前端可独立进行全流程开发和测试。

真实 LangGraph 工作流集成路径：`backend/src/workflow/` 目录包含完整的工作流定义和 Agent 实现，待接入 LLM API 后即可替换 Mock 层。

### 运行测试

```bash
cd backend
python -m pytest tests/ -v  # 51 passed, 4 skipped
```

### 开发 Token

MVP 阶段使用 `Authorization: Bearer dev-token` 跳过认证。生产环境需配置 JWT 密钥并实现真实用户系统。

## License

MIT
