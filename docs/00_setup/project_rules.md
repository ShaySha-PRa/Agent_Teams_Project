# 项目规范

> 版本: v1.0
> 创建日期: 2026-07-29
> 状态: Active

---

## 目录

1. [项目结构](#1-项目结构)
2. [Frontend / Backend / Docs 职责边界](#2-职责边界)
3. [后端配置管理规范](#3-后端配置管理规范)
4. [Agent Teams 工作流规范](#4-agent-teams-工作流规范)
5. [开发规范](#5-开发规范)
6. [Git 工作流](#6-git-工作流)
7. [代码审查规范](#7-代码审查规范)
8. [文档规范](#8-文档规范)

---

## 1. 项目结构

```
Agent_Teams_Project/
├── frontend/                     # 前端应用
│   └── src/                      # 前端源码
├── backend/                      # 后端应用
│   ├── src/                      # 后端源码
│   ├── .env.example              # 环境变量模板（提交到 git）
│   └── .env                      # 实际环境变量（不提交，gitignore 中排除）
├── docs/                         # 项目文档（分层管理）
│   ├── 00_setup/                 # 项目初始化与规范搭建
│   ├── 01_business_research/     # 业务调研
│   ├── 02_competitive_analysis/  # 竞品分析
│   ├── 03_business_modeling/     # 业务问题建模
│   ├── 04_interaction_design/    # 核心交互链路设计
│   ├── 05_product_prototype/     # 产品的原型规范
│   ├── 06_system_architecture/   # 系统的架构设计
│   ├── 07_data_model/            # 数据模型
│   ├── 08_api_specification/     # API 规范
│   ├── 09_frontend_plan/         # 前端实现计划
│   ├── 10_backend_plan/          # 后端实现计划
│   ├── 11_integration/           # 联调
│   └── 12_deployment/            # 发布和部署
├── .claude/                      # Claude Code 配置
│   ├── settings.json
│   └── agents/
├── CLAUDE.md                     # 项目级 AI 指引
└── .gitignore
```

---

## 2. 职责边界

### 2.1 Frontend (`frontend/`)

**负责**:
- 用户界面组件与页面实现
- 前端路由与导航
- UI 状态管理（组件状态、全局状态）
- API 请求封装与响应处理
- 前端构建配置与性能优化
- 浏览器兼容性处理

**不负责**:
- 业务逻辑判定（仅消费后端提供的判定结果）
- 数据持久化（仅通过 API 与后端交互）
- 权限验证（仅消费后端返回的权限状态并据此渲染 UI）
- 第三方 API 密钥管理（应通过后端代理）

### 2.2 Backend (`backend/`)

**负责**:
- 所有业务逻辑实现
- 数据模型设计与数据库操作
- REST/GraphQL API 端点的提供
- 请求验证与响应序列化
- 用户认证与授权
- 环境变量与配置管理（`.env`）
- 第三方服务集成

**不负责**:
- UI 渲染
- 前端路由逻辑
- CSS 样式
- 浏览器端状态管理

### 2.3 Docs (`docs/`)

**负责**:
- 所有设计阶段的文档
- 业务分析与竞品分析报告
- 架构设计、数据模型、API 规范
- 前后端实现计划
- 联调方案与部署方案
- 项目规范与规则文档

**不负责**:
- 任何可执行代码
- 运行时配置文件（仅提供模板和说明）

### 2.4 交互原则

```
需求阶段
  docs/01-05 (调研 → 分析 → 建模 → 设计 → 原型)
          │
          ▼
架构与规范阶段
  docs/06-08 (架构 → 数据模型 → API 规范)
          │
    ┌─────┴─────┐
    ▼           ▼
frontend      backend
(09_plan)    (10_plan)
    │           │
    └─────┬─────┘
          ▼
docs/11-12 (联调 → 部署)
```

---

## 3. 后端配置管理规范

### 3.1 环境变量 (.env)

- **统一使用 `.env` 文件**管理所有后端配置
- `backend/.env.example` 作为**模板文件**，包含所有必需的变量名和默认值，**必须提交到 git**
- `backend/.env` 包含实际配置值（密钥、连接串等），**禁止提交**（已在 `.gitignore` 中排除）
- 变量命名：`UPPER_SNAKE_CASE`，按模块使用语义化前缀
- 在应用启动时集中加载（如使用 `python-dotenv`）
- 所有敏感信息（API Key、数据库密码等）只能存在于 `.env` 中，禁止硬编码

```
.env.example 示例格式:
  APP_NAME=myapp
  APP_ENV=development
  APP_PORT=8000
  DATABASE_URL=postgresql://user:password@localhost:5432/db
  API_KEY=
```

### 3.2 虚拟环境管理 (uv)

- **统一使用 `uv`** 管理 Python 虚拟环境和依赖
- 项目初始化:
  ```bash
  cd backend && uv venv
  ```
- 添加依赖:
  ```bash
  uv add <package-name>
  ```
- 移除依赖:
  ```bash
  uv remove <package-name>
  ```
- 运行应用:
  ```bash
  uv run python -m backend.src.main
  ```
- **`uv.lock` 文件提交到 git**，确保所有开发者和部署环境使用相同版本的依赖
- 不在项目目录中创建除 `backend/.venv/` 以外的虚拟环境
- 使用 `uv sync` 来根据 `uv.lock` 同步依赖

---

## 4. Agent Teams 工作流规范

### 4.1 核心原则：复杂任务先 Plan 再实施

```
任务复杂度评估
  │
  ├── 简单任务 (单文件修改、typo fix、小改)
  │     → 直接实施 → 审查
  │
  └── 复杂任务 (多文件、架构决策、新功能、跨层修改)
        → EnterPlanMode → 设计方案 → 用户审批 → 实施
```

**Plan Mode 触发条件**（满足任一即触发）:
- 涉及 3 个以上文件的修改
- 包含架构层面的决策
- 新功能或新模块的开发
- 跨前端和后端的修改
- 涉及数据库 schema 变更

**Plan Mode 输出要求**:
- 问题分析与需求理解
- 至少 2 个备选方案及利弊分析
- 推荐方案与理由
- 实施步骤与里程碑
- 风险点与缓解措施
- 涉及的文件列表

### 4.2 每个阶段必须有明确输出

| 阶段 | 输出目录 | 必需输出文件 |
|------|---------|-------------|
| 00 项目初始化 | `docs/00_setup/` | `agent_teams_langchain_mcp_setup.md`, `project_rules.md` |
| 01 业务调研 | `docs/01_business_research/` | `research_report.md` |
| 02 竞品分析 | `docs/02_competitive_analysis/` | `analysis_report.md` |
| 03 业务建模 | `docs/03_business_modeling/` | `business_model.md` |
| 04 交互设计 | `docs/04_interaction_design/` | `interaction_flows.md` |
| 05 原型规范 | `docs/05_product_prototype/` | `prototype_spec.md` |
| 06 架构设计 | `docs/06_system_architecture/` | `architecture.md` |
| 07 数据模型 | `docs/07_data_model/` | `data_model.md` |
| 08 API 规范 | `docs/08_api_specification/` | `api_spec.md` |
| 09 前端计划 | `docs/09_frontend_plan/` | `frontend_plan.md` |
| 10 后端计划 | `docs/10_backend_plan/` | `backend_plan.md` |
| 11 联调 | `docs/11_integration/` | `integration_plan.md` + `integration_report.md` |
| 12 部署 | `docs/12_deployment/` | `deployment_plan.md` |

### 4.3 Agent Team 协作模式

**Team Lead 职责**:
1. 接收用户需求，评估任务复杂度
2. 复杂任务先进入 Plan Mode
3. 将工作分解为独立、不冲突的子任务
4. 生成合适的 teammate（参考 `.claude/agents/` 中的预定义类型）
5. 监控 teammate 进度，必要时重定向
6. 汇总 teammate 输出到阶段文档
7. 确保 teammates 不编辑同一文件（避免冲突）

**Teammate 职责**:
1. 从 `CLAUDE.md` 加载项目规范
2. 遵循本文件中的所有约定
3. 将工作产出写入指定的输出文件
4. 完成后通知 team lead
5. 遇到阻塞时主动请求 lead 协助

### 4.4 Plan Approval 流程

当需要使用 Plan Mode 的 teammate 时:

```
Lead: "Spawn an architect teammate to design the API structure.
       Require plan approval before implementation."

Architect Teammate:
  1. 在只读 Plan Mode 中研究代码库
  2. 设计方案
  3. 向 Lead 发送 plan_approval_request
  4. Lead 审查方案（可自主批准或拒绝并反馈）
  5. 批准后退出 Plan Mode
  6. 开始实施
```

---

## 5. 开发规范

### 5.1 通用规范

- 代码优先考虑可读性，其次才是简洁性
- 函数保持单一职责，尽量控制在 50 行以内
- 显式处理所有可能的错误状态
- 使用有意义的变量名，避免缩写（除非是业界通用缩写）
- 注释解释 "为什么"，而不是 "做什么"

### 5.2 前端规范

- 遵循组件化架构
- 组件目录结构：
  ```
  ComponentName/
  ├── index.tsx         # 组件入口
  ├── ComponentName.tsx # 主组件
  ├── ComponentName.test.tsx
  └── styles.module.css # 样式隔离
  ```
- API 调用集中管理（统一的 API client 或 service 层）
- 状态管理方案在架构设计阶段确定
- 所有用户可见文本应支持国际化

### 5.3 后端规范

- 遵循分层架构：`router → service → repository`
- 目录结构（建议）：
  ```
  src/
  ├── main.py            # 应用入口
  ├── api/               # 路由层
  ├── services/          # 业务逻辑层
  ├── repositories/      # 数据访问层
  ├── models/            # 数据模型
  ├── schemas/           # 请求/响应 schema
  └── core/              # 配置、依赖注入、中间件
  ```
- 所有 API 端点必须有输入验证
- 数据库迁移使用迁移工具管理（如 Alembic）
- 关键业务逻辑必须有单元测试

### 5.4 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 文件名 | kebab-case | `user-service.ts`, `data_model.md` |
| 前端组件 | PascalCase | `UserProfile`, `DataTable` |
| Python 函数/变量 | snake_case | `get_user_by_id`, `user_count` |
| Python 类 | PascalCase | `UserService`, `OrderRepository` |
| TypeScript 函数/变量 | camelCase | `getUserById`, `userCount` |
| TypeScript 类/接口 | PascalCase | `UserService`, `IUserData` |
| 环境变量 | UPPER_SNAKE_CASE | `DATABASE_URL`, `API_KEY` |
| Git 分支 | kebab-case | `feat/user-auth`, `fix/login-error` |

---

## 6. Git 工作流

### 6.1 分支策略

```
main ──────────────────────────────────────────
  │
  ├── feat/xxx ──────→ PR → main
  ├── fix/xxx ───────→ PR → main
  └── docs/xxx ──────→ PR → main
```

### 6.2 Commit 规范

使用 Conventional Commits 格式：

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

| Type | 用途 |
|------|------|
| `feat` | 新功能 |
| `fix` | Bug 修复 |
| `docs` | 文档变更 |
| `refactor` | 代码重构（无功能变更） |
| `test` | 测试相关 |
| `chore` | 构建/工具/依赖变更 |
| `style` | 格式变更（不影响逻辑） |

示例:
```
feat(backend): add user authentication endpoint
fix(frontend): resolve login form validation error
docs(api): update API specification for v2
```

### 6.3 PR 流程

1. 从 `main` 创建功能分支
2. 开发并提交（原子性 commit）
3. 推送到远程并创建 PR
4. 调动 Claude Code 的 `code-reviewer` agent 进行代码审查
5. 审查通过后合并到 `main`

---

## 7. 代码审查规范

调动 `.claude/agents/code-reviewer.md` 进行审查，关注：

- 代码可读性与维护性
- 安全漏洞（注入、XSS、敏感数据暴露等）
- 错误处理完整性
- 测试覆盖充分性
- 性能考虑
- 与项目规范的一致性

---

## 8. 文档规范

### 8.1 文档格式

- 所有设计文档使用 Markdown 格式
- 在文档顶部标注版本号和创建日期
- 使用 Mermaid 或 ASCII art 绘制架构图、流程图
- API 规范使用 OpenAPI 3.x 格式（`.yaml` 或 `.json`）

### 8.2 文档目录分层说明

| 目录 | 阶段目标 | 关键问题 |
|------|---------|---------|
| `01_business_research/` | 理解业务背景和用户需求 | 谁在用？解决什么问题？现有方案是什么？ |
| `02_competitive_analysis/` | 分析竞品优劣势 | 有哪些竞品？我们的差异化优势是什么？ |
| `03_business_modeling/` | 将业务抽象为模型 | 核心实体是什么？实体间关系是什么？ |
| `04_interaction_design/` | 设计用户交互流程 | 用户如何完成核心任务？有哪些交互路径？ |
| `05_product_prototype/` | 定义产品原型规范 | 每个页面的布局和交互行为是什么？ |
| `06_system_architecture/` | 设计技术架构 | 前后端如何分层？如何通信？技术栈选型？ |
| `07_data_model/` | 定义数据模型 | 有哪些表/集合？字段和关系是什么？ |
| `08_api_specification/` | 定义 API 规范 | 有哪些端点？请求/响应格式是什么？ |
| `09_frontend_plan/` | 规划前端实现 | 组件树是什么？状态管理方案？路由设计？ |
| `10_backend_plan/` | 规划后端实现 | 模块划分？中间件链？部署架构？ |
| `11_integration/` | 前后端联调 | 接口匹配情况？问题跟踪？性能测试？ |
| `12_deployment/` | 发布部署 | 部署环境？CI/CD 流程？监控告警？ |

---

> **相关文档**:
> - `agent_teams_langchain_mcp_setup.md` — Agent Teams 和 LangChain MCP 配置报告
> - `../CLAUDE.md` — 项目级 AI 指引（team lead 和 teammate 的公共上下文）
