# Agent Teams & LangChain MCP 环境配置报告

> **创建日期**: 2026-07-29
> **项目路径**: `I:\Users\Joshu\Desktop\Agent_Teams_Project`

---

## 目录

1. [Agent Teams 启用状态](#1-agent-teams-启用状态)
2. [LangChain MCP 接入状态](#2-langchain-mcp-接入状态)
3. [LangChain MCP 深度解析](#3-langchain-mcp-深度解析)
4. [LangChain Interpreter 深度解析](#4-langchain-interpreter-深度解析)
5. [Human-in-the-Loop 流程详解](#5-human-in-the-loop-流程详解)
6. [结论](#6-结论)

---

## 1. Agent Teams 启用状态

### 验证结果：✅ 已启用

**配置文件**: `.claude/settings.json`

```json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  },
  "teammateMode": "in-process"
}
```

### 配置说明

| 配置项 | 值 | 说明 |
|--------|-----|------|
| `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` | `"1"` | 启用 Agent Teams 实验性功能 |
| `teammateMode` | `"in-process"` | 所有队友在主终端内运行，通过 agent 面板交互（无需 tmux/iTerm2） |

### 项目级 Agent 定义

项目包含 4 个预定义的 agent 类型，位于 `.claude/agents/`：

| Agent | 文件 | 工具权限 | 用途 |
|-------|------|----------|------|
| `code-reviewer` | `code-reviewer.md` | Read, Grep, Glob, Bash | 代码审查：质量、安全、可维护性 |
| `debugger` | `debugger.md` | Read, Edit, Bash, Grep, Glob | 调试专家：诊断并修复错误 |
| `security-reviewer` | `security-reviewer.md` | Read, Grep, Glob, Bash | 安全审计：OWASP Top 10 全覆盖 |
| `architect` | `architect.md` | Read, Grep, Glob, Bash | 架构设计：技术方案评估与规划 |

这些 agent 定义既可作为 subagent 委托使用，也可作为 Agent Team 的队友类型引用。

### Agent Teams 架构概览

```
┌─────────────────────────────────────────────────┐
│                  Team Lead                       │
│          (主 Claude Code 会话)                    │
│                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │ Teammate │  │ Teammate │  │ Teammate │       │
│  │    1     │  │    2     │  │    3     │       │
│  │ 独立上下文 │  │ 独立上下文 │  │ 独立上下文 │       │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘       │
│       │             │             │              │
│       └──────┬──────┴──────┬──────┘              │
│              │             │                      │
│     ┌────────▼─────┐ ┌────▼──────────┐           │
│     │  Shared Task  │ │   Mailboxes   │           │
│     │     List      │ │ (JSON files)  │           │
│     └──────────────┘ └───────────────┘           │
└─────────────────────────────────────────────────┘
```

**核心特性**:
- 队友之间可以直接通信（`SendMessage`），无需通过 team lead 中转
- 共享任务列表支持自我协调（pending → in-progress → completed）
- 任务支持依赖关系（blockedBy / blocks）
- 每个队友有独立的 context window，不继承 lead 的对话历史
- 队友从项目根目录自动加载 `CLAUDE.md`、MCP servers 和 skills

---

## 2. LangChain MCP 接入状态

### 验证结果：✅ 已接入并测试通过

**配置文件**: `C:\Users\Joshu\.claude.json`（project 级别）

### MCP 服务器列表

| 服务器名称 | 端点 URL | 传输方式 | 认证 | 连通性测试 | 功能测试 |
|-----------|----------|---------|------|-----------|---------|
| `docs-langchain` | `https://docs.langchain.com/mcp` | HTTP (Streamable) | 无需认证 | ✅ HTTP 200 (MCP initialize) | ✅ 搜索返回正确结果 |
| `reference-langchain` | `https://reference.langchain.com/mcp` | HTTP (Streamable) | 无需认证 | ✅ HTTP 200 (MCP initialize) | ✅ API 搜索返回正确结果 |

### 连通性测试详情

#### docs-langchain — MCP initialize 响应

```json
{
  "protocolVersion": "2024-11-05",
  "capabilities": {
    "tools": { "listChanged": true },
    "resources": { "listChanged": true }
  },
  "serverInfo": {
    "name": "Docs by LangChain",
    "version": "1.0.0"
  }
}
```

**提供的工具**:
- `search_docs_by_lang_chain` — 全文搜索 LangChain 文档
- `query_docs_filesystem_docs_by_lang_chain` — 虚拟文件系统查询（支持 `rg`、`cat`、`head`、`tree` 等）
- `submit_feedback` — 提交文档反馈

#### reference-langchain — MCP initialize 响应

```json
{
  "protocolVersion": "2024-11-05",
  "serverInfo": {
    "name": "langchain-reference",
    "version": "1.0.0"
  }
}
```

**提供的工具**:
- `search_api` — 跨语言搜索 API 参考（Python, JavaScript, Java, Go）
- `get_symbol` — 获取特定类/函数的详细文档

### 功能测试结果

| 测试项 | 服务器 | 操作 | 结果 |
|--------|--------|------|------|
| 文档搜索 | docs-langchain | 搜索 "LangChain agent teams multi-agent" | ✅ 返回 10 条相关结果 |
| 文件系统查询 | docs-langchain | 列出 `/langsmith/` 目录 | ✅ 正确返回文件列表 |
| API 搜索 | reference-langchain | 搜索 "ChatOpenAI" | ✅ 返回 Python/JS 双语言文档 |
| API 详情 | reference-langchain | 获取 `ChatOpenAI` 符号详情 | ✅ 返回完整 API 文档 |

---

## 3. LangChain MCP 深度解析

### 3.1 什么是 MCP（Model Context Protocol）

MCP 是一种**开放协议**，标准化了应用程序如何向 LLM 提供工具和上下文。它使 LLM 能够通过结构化 API 发现和使用外部工具。

### 3.2 LangChain 提供的 MCP 服务器

LangChain 通过两个互补的 MCP 服务器覆盖了完整的文档生态：

| 服务器 | 覆盖范围 | 典型用途 |
|--------|---------|---------|
| **docs-langchain** | 概念指南、操作指南、教程、产品文档 | 学习 "怎么做" 和 "为什么" |
| **reference-langchain** | API 参考：类、方法、参数、签名 | 查询精确的函数签名和类型定义 |

### 3.3 docs-langchain 详细工具

```
search_docs_by_lang_chain(query: string)
  → 全文搜索 LangChain 知识库
  → 返回上下文内容 + 文档直达链接

query_docs_filesystem_docs_by_lang_chain(command: string)
  → 虚拟文件系统查询（类似 Unix shell）
  → 支持: rg, grep, cat, head, tail, tree, ls, find, jq 等
  → 根路径为 /，包含 .mdx 格式的文档页面

submit_feedback(path: string, feedback: string)
  → 报告文档问题（错误、过时、不清楚、不完整）
  → 反馈直接送达 LangChain 文档团队
```

### 3.4 reference-langchain 详细工具

```
search_api(query: string, language?: string, limit?: number)
  → 搜索 API 参考文档
  → 可过滤 Python / JavaScript / Java / Go
  → 返回类、函数、方法列表

get_symbol(package: string, symbol: string, language?: string)
  → 获取特定符号的完整文档
  → 包含签名、参数、示例代码
```

### 3.5 MCP 在 LangChain 生态中的角色

```
┌──────────────────────────────────────────────────┐
│                  LangChain 生态                    │
│                                                   │
│  ┌──────────────┐    ┌──────────────────┐         │
│  │ docs-langchain│    │reference-langchain│        │
│  │   (MCP 服务器) │    │   (MCP 服务器)      │        │
│  │              │    │                   │         │
│  │ 概念指南      │    │ API 参考           │         │
│  │ How-to 教程  │    │ 类/方法/签名       │         │
│  │ 产品文档      │    │ 参数/示例代码      │         │
│  └──────┬───────┘    └────────┬──────────┘         │
│         │                     │                    │
│         └──────────┬──────────┘                    │
│                    │                               │
│         ┌──────────▼──────────┐                    │
│         │   Claude Code / IDE  │                   │
│         │   (MCP 客户端)        │                   │
│         │                     │                    │
│         │ "告诉我 LangChain    │                   │
│         │  最新的 Agent API"   │                   │
│         └─────────────────────┘                    │
└──────────────────────────────────────────────────┘
```

**MCP 协议的价值**: 让 AI 编码助手（如 Claude Code）能够**实时获取官方最新文档**，而非依赖训练数据中可能过时的知识。

---

## 4. LangChain Interpreter 深度解析

### 4.1 什么是 Interpreter

Interpreter 是 **Deep Agents** 中的一个中间件（middleware），为 agent 提供一个**可编程的内存工作空间**（programmable in-memory workspace）。它使用 **QuickJS** 轻量级 JavaScript 运行时，在 agent 循环内部执行代码。

### 4.2 Interpreter 与 Sandbox 的区别

| 维度 | Interpreter | Sandbox |
|------|-------------|---------|
| **运行环境** | QuickJS（纯内存，无文件系统/网络/Shell） | 完整 OS 环境 |
| **用途** | 编排工具、保持状态、数据转换 | 执行 Shell 命令、安装依赖、编辑文件 |
| **隔离性** | 仅 JS 运行时，无外部访问 | 完整系统隔离 |
| **典型场景** | 循环、分支、重试、并行批处理 | 运行测试、安装包、命令行操作 |

### 4.3 Interpreter 核心能力

```
┌────────────────────────────────────────┐
│            Deep Agent Loop              │
│                                        │
│  Model ←→ 中间件层 ←→ 工具层            │
│              │                         │
│         ┌────▼────┐                    │
│         │ eval 工具 │  ← Interpreter   │
│         │ (QuickJS) │    加入此工具     │
│         └────┬────┘                    │
│              │                         │
│     ┌────────┼────────┐                │
│     │        │        │                │
│  ┌──▼──┐ ┌──▼──┐ ┌──▼──────┐         │
│  │ PTC │ │子agent│ │状态保持 │         │
│  │工具调用│ │调度  │ │数据转换 │         │
│  └─────┘ └─────┘ └─────────┘         │
└────────────────────────────────────────┘
```

#### 4.3.1 编程式工具调用（Programmatic Tool Calling, PTC）

Agent 可以在 JS 代码中调用工具，实现：
- **循环调用**: 遍历列表，对每个元素调用工具
- **条件分支**: 根据工具返回结果决定下一步
- **重试逻辑**: 失败时自动重试
- **并行批处理**: 同时调用多个工具

```javascript
// Interpreter 中的 PTC 示例
const results = [];
for (const url of urls) {
  const result = await tools.fetch_page({ url });
  if (result.status === 200) {
    results.push(await tools.summarize({ text: result.content }));
  }
}
results; // 仅最终结果返回给模型，中间产物不消耗 context
```

#### 4.3.2 动态子 agent（Dynamic Subagents）

Agent 可以在代码中通过 `task()` 全局函数调度子 agent：
- **扇出（Fan-out）**: 并行分派多个子 agent 处理独立任务
- **验证（Verification）**: 多个子 agent 交叉验证结果
- **递归（Recursive）**: 对大输入进行递归分解

#### 4.3.3 状态保持与数据转换

- **状态保持**: 在多次 `eval` 调用之间保持变量状态（`mode="thread"`）
- **确定性数据转换**: 排序、分组、解析、验证、评分、聚合 — 无需额外的模型轮次
- **Context 节省**: 中间结果只在 QuickJS 运行时中，不会进入模型的 context window

### 4.4 何时使用 Interpreter

| 需求 | 推荐方案 |
|------|---------|
| 1-2 个简单的工具调用 | 普通 tool calling |
| 纯内存 JS：循环、分支、重试、数据转换（无外部工具） | Interpreter |
| 从代码编排多个外部工具调用 | Interpreter + PTC |
| 大量独立工作单元、多视角分析、递归分析 | Interpreter + Dynamic Subagents |
| Shell 命令、包安装、测试、文件系统操作 | Sandbox |

---

## 5. Human-in-the-Loop 流程详解

### 5.1 什么是 Human-in-the-Loop（HITL）

Human-in-the-Loop 是 LangGraph 提供的一种机制，允许在 agent 或工作流执行过程中**暂停执行、等待人类输入、然后继续执行**。它通过 `interrupt()` 函数实现动态中断。

### 5.2 核心机制

```
┌──────────────────────────────────────────────────────┐
│                  HITL 执行流程                         │
│                                                      │
│  ┌──────────┐     ┌──────────┐     ┌──────────────┐  │
│  │ 1. 执行   │────▶│ 2. 中断   │────▶│ 3. 等待人类   │  │
│  │  agent    │     │interrupt()│     │   输入        │  │
│  └──────────┘     └──────────┘     └──────┬───────┘  │
│                                           │          │
│                                           ▼          │
│  ┌──────────┐     ┌──────────┐     ┌──────────────┐  │
│  │ 6. 继续   │◀────│ 5. 恢复   │◀────│ 4. 人类审查   │  │
│  │  后续步骤  │     │Command()  │     │   并决策      │  │
│  └──────────┘     └──────────┘     └──────────────┘  │
│                                                      │
│  关键组件:                                            │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────┐  │
│  │ Checkpointer│  │  thread_id   │  │ Command()   │  │
│  │ 状态持久化   │  │ 会话标识指针  │  │ 恢复执行指令  │  │
│  └─────────────┘  └──────────────┘  └─────────────┘  │
└──────────────────────────────────────────────────────┘
```

### 5.3 关键步骤

#### Step 1: 定义中断点

在 graph 的 node 函数中调用 `interrupt()`：

```python
from langgraph.types import interrupt

def approval_node(state: State):
    # 暂停执行，向人类展示待审批内容
    approved = interrupt({
        "action": "delete_user",
        "user_id": state["user_id"],
        "message": "是否确认删除此用户？"
    })

    # 人类响应后，返回值即为人类输入
    return {"approved": approved}
```

#### Step 2: 运行到中断点

```python
# 使用事件流驱动 graph 执行
config = {"configurable": {"thread_id": "thread-1"}}
stream = graph.stream_events(
    {"input": "data"},
    config=config,
    version="v3"
)

# 等待执行完成（或中断）
final = stream.output

# 检查是否发生中断
if stream.interrupted:
    print(stream.interrupts)  # 人类审查中断信息
```

#### Step 3: 人类决策并恢复

```python
from langgraph.types import Command

# 人类做出决策后，恢复执行
resumed = graph.stream_events(
    Command(resume=True),   # 同意
    # Command(resume=False),  # 拒绝
    config=config,
    version="v3"
)
final = resumed.output
```

### 5.4 典型应用场景

| 场景 | 描述 | 中断时机 |
|------|------|---------|
| **审批工作流** | 执行关键操作前（API 调用、数据库修改、金融交易）需要人类批准 | 执行操作前 |
| **审查与编辑** | 人类审查并修改 LLM 输出或工具调用结果 | LLM 生成后、工具执行前 |
| **工具调用拦截** | 在工具执行前暂停，让人类审查工具调用参数 | 工具调用前 |
| **输入验证** | 人类验证输入数据再继续下一步 | 接收输入后 |
| **多中断协调** | 并行分支同时中断时，通过 ID 映射精确恢复每个中断 | 并行分支中 |

### 5.5 与 Agent Teams 的结合

在 Claude Code 的 Agent Teams 中，HITL 通过以下机制实现：

```
┌──────────────────────────────────────────┐
│              Team Lead                    │
│                                          │
│  任务: "重构认证模块，需要计划审批"         │
│                                          │
│  ┌──────────────────────┐                │
│  │ Architect Teammate    │                │
│  │                      │                │
│  │ 1. 进入 Plan Mode    │                │
│  │ 2. 研究代码库         │                │
│  │ 3. 提出方案           │                │
│  │ 4. 发送审批请求 ──────────▶ Lead 审查   │
│  │ 5. 收到批准 ────────────▶ Lead 批准    │
│  │ 6. 退出 Plan Mode    │                │
│  │ 7. 开始实施           │                │
│  └──────────────────────┘                │
└──────────────────────────────────────────┘
```

Teammate 的 Plan Approval 流程：
1. Lead 生成 teammate 时要求计划审批（`Require plan approval`）
2. Teammate 在只读 Plan Mode 下工作，研究并设计方案
3. Teammate 向 Lead 发送 `plan_approval_request`
4. Lead 自主审查并批准/拒绝（可附带反馈）
5. 批准后 teammate 退出 Plan Mode 并开始实施

### 5.6 核心技术要点

- **Checkpointer 持久化状态**: `interrupt()` 调用时 graph 状态被保存，确保可随时恢复
- **`thread_id` 是会话指针**: 使用相同的 `thread_id` 恢复同一会话
- **动态中断 vs 静态断点**: `interrupt()` 可放在代码任意位置，支持条件判断
- **事件流 v3**: 通过 `stream_events(version="v3")` 获取 `stream.interrupts` 和 `stream.interrupted`
- **Node 重新执行**: 恢复后，节点从头重新执行（`interrupt()` 之前的代码会再次运行）

---

## 6. 结论

### LangChain MCP 的核心定位

> **LangChain 的 MCP 服务器主要负责提供官方最新的文档规范和 API 参考。**

这一结论基于以下事实：

1. **docs-langchain** 的内容来源是 `docs.langchain.com` 上发布的所有官方文档，包括概念指南、操作教程、产品文档。它的 `serverInfo` 明确标识为 `"Docs by LangChain"`。

2. **reference-langchain** 的内容来源是 `reference.langchain.com` 上的 API 参考文档，覆盖 `langchain-core`、`langchain-openai`、`@langchain/openai` 等所有官方包的类、方法、签名和参数。

3. **两个 MCP 服务器都是只读的**（`submit_feedback` 除外），不执行实际代码、不操作数据库、不管理部署。它们的作用就是让 AI 编码助手能够**实时检索 LangChain 生态的最新文档规范**。

4. **与 LangSmith MCP 的区别**: LangSmith 另有独立的 MCP 服务器（`api.smith.langchain.com/mcp`），用于读取会话历史、prompts、runs/traces、datasets 等运行时数据。那两个文档 MCP 服务器专注于**文档规范本身**。

### 配置总结

| 配置项 | 文件 | 状态 |
|--------|------|------|
| Agent Teams 启用 | `.claude/settings.json` | ✅ `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` |
| 队友显示模式 | `.claude/settings.json` | ✅ `teammateMode: "in-process"` |
| 项目 Agent 定义 | `.claude/agents/*.md` | ✅ 4 个 agent 类型可用 |
| 项目上下文 | `CLAUDE.md` | ✅ 包含 Agent Teams 使用指引 |
| docs-langchain MCP | `.claude.json` (project) | ✅ 已连接，功能验证通过 |
| reference-langchain MCP | `.claude.json` (project) | ✅ 已连接，功能验证通过 |

### 项目文件结构

```
Agent_Teams_Project/
├── .claude/
│   ├── settings.json              # Agent Teams 启用配置
│   └── agents/
│       ├── architect.md           # 架构设计 agent
│       ├── code-reviewer.md       # 代码审查 agent
│       ├── debugger.md            # 调试专家 agent
│       └── security-reviewer.md   # 安全审计 agent
├── CLAUDE.md                      # 项目上下文指引
└── docs/
    └── 00_setup/
        └── agent_teams_langchain_mcp_setup.md  # 本文件
```
