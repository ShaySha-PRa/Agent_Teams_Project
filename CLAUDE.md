# Agent Teams 项目

## 项目概述

本项目使用 Claude Code Agent Teams 进行协作式 AI 驱动开发。Agent Teams 允许多个 Claude Code 实例协同工作，具有共享任务列表、代理间直接消息传递和集中协调的能力。

## 项目目录结构

```
Agent_Teams_Project/
├── frontend/                     # 前端应用 (React/Vue 等)
│   └── src/                      # 前端源码
├── backend/                      # 后端应用 (Python/FastAPI 等)
│   ├── src/                      # 后端源码
│   └── .env.example              # 环境变量模板
├── docs/                         # 项目文档
│   ├── 00_setup/                 # 项目初始化与规范搭建
│   ├── 01_business_research/     # 业务调研
│   ├── 02_competitive_analysis/  # 竞品分析
│   ├── 03_business_modeling/     # 业务问题建模
│   ├── 04_interaction_design/    # 核心交互链路设计
│   ├── 05_product_prototype/     # 产品的原型规范
│   ├── 06_system_architecture/   # 系统的架构设计
│   ├── 07_data_model/            # 数据模型
│   ├── 08_api_specification/     # API 规范
│   ├── 09_frontend_plan/         # 前端的实现计划
│   ├── 10_backend_plan/          # 后端的实现计划
│   ├── 11_integration/           # 联调
│   └── 12_deployment/            # 发布和部署
├── .claude/                      # Claude Code 配置
│   ├── settings.json             # Agent Teams 启用 + MCP 配置
│   └── agents/                   # 自定义 agent 定义
├── CLAUDE.md                     # 本文件 - 项目级 AI 指引
└── .gitignore
```

---

## 一、Frontend / Backend / Docs 职责边界

### Frontend (`frontend/`)

| 职责 | 说明 |
|------|------|
| UI/UX 实现 | 所有用户界面组件、页面、交互逻辑 |
| 状态管理 | 前端状态（路由状态、UI 状态、缓存数据状态） |
| API 消费 | 调用后端 API，处理请求/响应/错误 |
| 构建与优化 | 打包、代码分割、性能优化 |
| 不负责 | 业务逻辑判定、数据持久化、权限验证（仅消费后端返回的权限状态） |

**前端启动命令**：

```bash
# 1. 进入前端目录
cd frontend/

# 2. 安装依赖（首次运行或 package.json 有变更时）
npm install

# 3. 启动开发服务器（默认端口 5173）
npm run dev

# 4. 生产构建
npm run build

# 5. TypeScript 类型检查（不产生输出文件）
npm run typecheck
```

| 项 | 值 |
|------|-----|
| 技术栈 | React 18 + TypeScript + Vite + React Router v6 |
| 启动路径 | `frontend/` |
| 启动命令 | `npm run dev` |
| 默认端口 | `http://localhost:3000` |
| 路由数 | 7 个页面路由（P1-P7） |
| API 状态 | 全部 32 个后端 API 标记为「⚠️ 未开发」 |

### Backend (`backend/`)

| 职责 | 说明 |
|------|------|
| 业务逻辑 | 所有业务规则、流程控制、数据校验 |
| 数据持久化 | 数据库操作、ORM、迁移脚本 |
| API 提供 | REST/GraphQL 端点，请求验证，响应序列化 |
| 认证与授权 | 用户身份验证、权限控制 |
| 不负责 | UI 渲染、前端路由、浏览器兼容性 |

### Docs (`docs/`)

| 职责 | 说明 |
|------|------|
| 设计文档 | 架构设计、数据模型、API 规范、交互链路 |
| 计划文档 | 前后端实现计划、发布部署方案 |
| 分析文档 | 业务调研、竞品分析、问题建模 |
| 规范文档 | 项目规则、原型规范、联调方案 |
| 不负责 | 任何可执行代码、配置文件（除模板外） |

### 交互原则

```
用户需求 → docs (调研→设计→规范) → backend (API) + frontend (UI)
                                         │
                          docs (联调→部署) ←┘
```

---

## 二、后端配置管理规范

### 环境变量管理 (.env)

- **统一使用 `.env` 文件**管理所有后端配置
- `backend/.env.example` 作为模板文件提交到版本控制
- `backend/.env` 包含实际敏感值，**禁止提交**（已在 `.gitignore` 中排除）
- 所有环境变量在应用启动时集中加载
- 环境变量命名规范：`UPPER_SNAKE_CASE`，按模块使用前缀

### Python 虚拟环境管理 (uv)

- **统一使用 `uv`** 管理 Python 虚拟环境和依赖
- 项目初始化：`uv init` 或 `uv venv`
- 添加依赖：`uv add <package>`
- 运行脚本：`uv run python -m backend.src.main`
- `uv.lock` 文件提交到版本控制以锁定依赖版本
- 不在项目中创建除 `backend/.venv/` 以外的虚拟环境

---

## 三、Agent Teams 工作规范

### 核心原则：复杂任务，先 Plan 再实施

**所有复杂任务（涉及多个文件、架构决策、新功能）必须先进入 Plan Mode（`EnterPlanMode`），制定方案并获得批准后再实施。**

```
复杂任务
  │
  ▼
Plan Mode ──→ 分析需求 ──→ 设计方案 ──→ 用户审批
                                         │
                               ┌─────────┘
                               ▼
                          实施阶段
                    （可分配 teammate 并行执行）
```

### 每个阶段必须有明确输出文件

| 阶段 | 输出目录 | 至少输出 |
|------|---------|---------|
| 业务调研 | `docs/01_business_research/` | `research_report.md` |
| 竞品分析 | `docs/02_competitive_analysis/` | `analysis_report.md` |
| 业务问题建模 | `docs/03_business_modeling/` | `business_model.md` |
| 核心交互链路设计 | `docs/04_interaction_design/` | `interaction_flows.md` |
| 产品原型规范 | `docs/05_product_prototype/` | `prototype_spec.md` |
| 系统架构设计 | `docs/06_system_architecture/` | `architecture.md` |
| 数据模型 | `docs/07_data_model/` | `data_model.md` 或 `schema.md` |
| API 规范 | `docs/08_api_specification/` | `api_spec.md` 或 `openapi.yaml` |
| 前端实现计划 | `docs/09_frontend_plan/` | `frontend_plan.md` |
| 后端实现计划 | `docs/10_backend_plan/` | `backend_plan.md` |
| 联调 | `docs/11_integration/` | `integration_plan.md` + `integration_report.md` |
| 发布和部署 | `docs/12_deployment/` | `deployment_plan.md` |

**规则**：
- 每个阶段开始前，在对应的 `docs/` 目录下创建输出文件
- 阶段完成后，确保输出文件已写入完整内容
- Agent Team 的每个 teammate 完成工作后，由 lead 汇总到阶段输出文件中

### Team Lead 职责

- 在启动 teammate 前先评估任务复杂度
- 复杂任务必须先用 Plan Mode 做方案设计
- 确保每个 teammate 的输出有明确的文件目标
- 汇总 teammates 的结果到阶段输出文件
- 不要让 teammates 编辑同一个文件（避免冲突）

### Teammate 职责

- 从 `CLAUDE.md` 加载项目上下文
- 遵循本文件中的所有规范
- 产出明确、可审查的输出文件
- 完成后通知 lead

---

## 四、可用 Agent 类型

以下 agent 定义位于 `.claude/agents/`，可作为 subagent 或 teammate 使用：

| Agent | 工具权限 | 适用场景 |
|-------|---------|---------|
| `code-reviewer` | Read, Grep, Glob, Bash | 代码审查：质量、安全、可维护性 |
| `debugger` | Read, Edit, Bash, Grep, Glob | 调试诊断：定位并修复错误 |
| `security-reviewer` | Read, Grep, Glob, Bash | 安全审计：OWASP Top 10 覆盖 |
| `architect` | Read, Grep, Glob, Bash | 架构设计：技术方案评估与规划 |

---

## 五、版本控制规范

- 使用 conventional commit 格式：`type(scope): description`
- Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `style`
- 每个 commit 应该是原子性的（一个逻辑变更）
- PR 合并前需要 code review（调动 `code-reviewer` agent）

## 六、配置说明

- Agent Teams 已启用（`.claude/settings.json`）
- LangChain MCP 已接入（`docs-langchain` + `reference-langchain`）
- 配置详情见 `docs/00_setup/agent_teams_langchain_mcp_setup.md`
- 项目规则见 `docs/00_setup/project_rules.md`
