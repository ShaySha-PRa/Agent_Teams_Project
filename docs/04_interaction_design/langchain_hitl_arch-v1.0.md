# Agent 智能文档审核系统 — LangChain HITL 架构规范 v1.0

> **版本**: v1.0
> **创建日期**: 2026-07-30
> **文档性质**: 收口架构规范 — 综合后端服务架构 + LangChain HITL 工作流设计
> **来源**: Teammate 1（后端服务架构）+ Teammate 2（LangChain HITL 工作流）+ LangChain 官方 MCP 规范研究
> **Lead 汇总**: 综合两份报告与 MCP 研究，不添加新设计内容

---

## 一、Agent Team 执行摘要

| 角色 | Teammate | 输出文件 | 规模 | MCP 查询 | 核心交付 |
|------|----------|---------|:--:|:--:|---------|
| 后端服务架构 | Teammate 1 (Sonnet) | `backend_service_arch-v1.0.md` | 1,018 行 | 3 主题 | 5 层架构 + 9 状态生命周期 + Checkpointer 选型 |
| LangChain HITL 工作流 | Teammate 2 (Sonnet) | `langchain_hitl_workflow-v1.0.md` | 基于 MCP 验证 | 11 次查询 | 7 节点 StateGraph + 3 中断点 + 8 操作 Command 映射 |
| **Lead 汇总** | 当前会话 | `langchain_hitl_arch-v1.0.md`（本文件） | — | — | 架构总览 + MCP 验证 API 清单 + 状态流转合图 |

---

## 二、架构总览

### 2.1 5 层系统架构

> **来源**: Teammate 1 §1 架构总览

```
┌─────────────────────────────────────────────────────────────────┐
│  Presentation Layer (Frontend — 7 pages)                        │
│  P1-P7: Dashboard → Upload → Parse → Review → Workspace → Report│
└──────────────────────────┬──────────────────────────────────────┘
                           │ REST + SSE
┌──────────────────────────▼──────────────────────────────────────┐
│  API Gateway Layer                                               │
│  Rate limiting / Auth (JWT) / Request routing / SSE hub          │
└──────┬────────────────┬──────────────────┬──────────────────────┘
       │                │                  │
┌──────▼──────┐  ┌──────▼──────┐  ┌───────▼────────┐
│ Upload      │  │ Task State  │  │ Review Result   │
│ Service     │  │ Manager     │  │ Query Service   │
│             │  │             │  │                 │
│ 5-layer     │  │ 9-state     │  │ RiskFlag query  │
│ validation  │  │ lifecycle   │  │ Audit log       │
│ Async OCR   │  │ Concurrency │  │ Side-by-side    │
│ MinIO store │  │ Celery+Redis│  │ data provision  │
└──────┬──────┘  └──────┬──────┘  └───────┬─────────┘
       │                │                  │
       └────────────────┼──────────────────┘
                        │
┌───────────────────────▼──────────────────────────────────────────┐
│  Agent Orchestration Layer (LangGraph StateGraph)                │
│                                                                  │
│  Supervisor Agent                                                │
│      │                                                           │
│      ├── Clause Extraction Agent (条款提取)                       │
│      ├── Risk Control Agent (风控识别)      ← 并行               │
│      ├── Compliance Agent (合规检查)        ← 并行               │
│      └── Report Agent (报告生成)            ← 串行依赖上游         │
│                                                                  │
│  + HumanInTheLoopMiddleware (3 interrupt points)                  │
│  + Checkpointer (AsyncPostgresSaver)                             │
│  + SSE Event Stream (9 event types)                              │
└───────────────────────┬──────────────────────────────────────────┘
                        │
┌───────────────────────▼──────────────────────────────────────────┐
│  Data Persistence Layer                                          │
│  PostgreSQL (business data) + MinIO (files) + Audit Log (hash)   │
└──────────────────────────────────────────────────────────────────┘
```

### 2.2 LangChain MCP 官方规范验证

> **来源**: Teammate 2 §Phase 2 MCP 研究（11 次查询）

以下 API 签名均已通过 LangChain 官方 reference MCP 验证：

| API | 验证后签名 | 用途 |
|-----|----------|------|
| `interrupt()` | `interrupt(value: Any) -> Any` | 暂停执行，返回载荷给前端 |
| `Command` | `Command(*, graph=None, update=None, resume: dict[str, Any] \| Any \| None = None, goto=())` | 人类决策后恢复执行 |
| `Interrupt` | `Interrupt(value: Any, id: str)` — `.value` + `.id` 属性 | 中断事件数据结构 |
| `create_agent` | `create_agent(model, tools, *, system_prompt, middleware, checkpointer, ...) -> CompiledStateGraph` | 创建 Agent（含 HITL 中间件） |
| `HumanInTheLoopMiddleware` | `HumanInTheLoopMiddleware(interrupt_on: dict[str, bool \| InterruptOnConfig], *, description_prefix: str)` | 工具级 HITL 中断控制 |
| `InterruptOnConfig` | TypedDict: `allowed_decisions`, `description`, `args_schema`, `when` | 单工具中断配置 |
| `AgentState` | TypedDict: `messages: Annotated[list[AnyMessage], add_messages]` | Agent 基础 State 类型 |
| 多中断恢复 | `Command(resume={interrupt_id: resume_value, ...})` | ID→值 映射精确恢复每个中断 |

---

## 三、核心状态机：9 状态生命周期

> **来源**: Teammate 1 §3 任务状态管理器

```
CREATED → UPLOADED → PARSING → PARSED → REVIEWING → REVIEWED → HUMAN_REVIEW → COMPLETED
                                         │            │            │
                                         ▼            ▼            ▼
                                      FAILED       FAILED       FAILED
                                                    │
                                                    ▼
                                               CANCELLED
```

| 状态 | 含义 | Checkpoint | 用户可操作 |
|------|------|:--:|---------|
| CREATED | 用户点击"新建审阅" | — | 上传文件 |
| UPLOADED | 文件上传+校验完成 | — | 配置标题/Playbook → 启动解析 |
| PARSING | 解析进行中 | — | 查看进度 / 取消 |
| PARSED | 解析完成 | ✅ | 启动 AI 审核 |
| REVIEWING | 4 Agent 并行审核中 | ✅ | 查看进度 / 暂停 / 取消 |
| REVIEWED | AI 审核完成，待人工审批 | ✅ | 进入审批 |
| HUMAN_REVIEW | 人工审批进行中 | ✅ | approve/edit/reject/submit/save-draft |
| COMPLETED | 审阅提交完成 | ✅ | 查看/导出报告 |
| FAILED | 解析/AI 审核失败 | ✅ | 重试(断点续传) / 重新上传 |
| CANCELLED | 用户主动取消 | ✅ | 归档 |

---

## 四、LangGraph StateGraph 工作流

> **来源**: Teammate 2 §1-§2 工作流定义 + State 类型定义

### 4.1 7 节点 StateGraph

```
                    ┌────────────────┐
                    │ parse_document  │
                    └───────┬────────┘
                            │
                    ┌───────▼────────┐
                    │ extract_clauses │
                    └───────┬────────┘
                            │
              ┌─────────────┼─────────────┐
              │             │             │
     ┌────────▼──────┐ ┌───▼──────────┐  │
     │ risk_analysis │ │ compliance   │  │  ← 并行节点
     │ (风控 Agent)   │ │ _check       │  │    (reducer 合并输出)
     └────────┬──────┘ └───┬──────────┘  │
              │            │              │
              └────────────┼──────────────┘
                           │
                  ┌────────▼─────────┐
                  │ generate_report  │  ← 串行依赖（等待风控+合规）
                  │ _draft           │
                  └────────┬─────────┘
                           │
                  ┌────────▼─────────┐
                  │ human_review     │  ← 多 interrupt 节点
                  │ ┌──────────────┐ │
                  │ │ IP-1: 高风险  │ │     不可跳过
                  │ │ IP-2: 中风险  │ │     批量可选
                  │ │ IP-3: 最终确认│ │     最终提交
                  │ └──────────────┘ │
                  └────────┬─────────┘
                           │
                  ┌────────▼─────────┐
                  │ finalize_report  │
                  └──────────────────┘
```

### 4.2 状态定义核心字段

> **来源**: Teammate 2 §2 State 定义

```python
class DocumentReviewState(TypedDict):
    # 文档级
    document_id: str
    doc_status: str                    # 9-state lifecycle
    doc_metadata: dict                 # 标题、类型(NDA)、上传时间

    # 条款级 (Annotated + operator.add 实现并发安全写入)
    clauses: Annotated[list[ClauseDict], operator.add]

    # 风险级 (reducer 按 agent 来源去重合并)
    risk_flags: Annotated[list[RiskFlagDict], merge_risk_flags]

    # 决策级 (append-only)
    review_decisions: Annotated[list[DecisionDict], operator.add]

    # 中断控制
    interrupt_state: str               # idle / waiting / resolved
    pending_interrupts: list[str]      # 活跃中断 ID 列表

    # 错误控制
    error_info: Optional[dict]
    retry_count: int
```

---

## 五、3 个中断点定义

> **来源**: Teammate 2 §3 + `business_model.md` §4.1 分级告警 + `human_approval_flow.md` 8 操作规范

| 中断点 | 触发位置 | 风险等级 | Payload 结构 | Resume 处理 | 是否可跳过 |
|--------|---------|:------:|------------|-----------|:--------:|
| **IP-1** | `human_review` → 高风险子节点 | 🔴 高 | `{clause_id, risk_level, risk_category, ai_confidence, playbook_diff, suggestion, original_text, clause_location}` | `Command(resume={"decision": approve\|edit\|reject, "comment": str, "modified_fields": ...})` | **不可跳过** |
| **IP-2** | `human_review` → 中风险子节点 | 🟡 中 | `[{clause_id, risk_category, ai_confidence, clause_summary}, ...]` (批量) | `Command(resume={"type": batch_confirm\|deep_dive, "items": [...]})` | 可批量跳过 (auto-passed) |
| **IP-3** | `human_review` → 确认子节点 | 全部 | `{high_risk_summary, medium_risk_summary, low_risk_summary, manual_additions, audit_summary}` | `Command(resume={"action": confirm_submit\|save_draft\|back_to_review})` | 不可跳过 |

### 5.1 前端 8 操作 → Command(resume) 映射

> **来源**: Teammate 2 §5 前端操作映射

| 前端操作 | HTTP 端点 | Command(resume=...) | 中断点 |
|---------|----------|-------------------|:--:|
| approve | `POST /risk-flags/{id}/approve` | `Command(resume={"decision": "approve"})` | IP-1 |
| edit | `POST /risk-flags/{id}/edit` | `Command(resume={"decision": "edit", "modified_fields": {...}})` | IP-1 |
| reject | `POST /risk-flags/{id}/reject` | `Command(resume={"decision": "reject", "comment": str})` | IP-1 |
| batch_approve | `POST /risk-flags/batch-approve` | `Command(resume={"type": "batch_confirm", "items": [...]})` | IP-2 |
| spot_check | `POST /risk-flags/sample` | `Command(resume={"type": "deep_dive", "items": [...]})` | IP-2 |
| escalate | `POST /risk-flags/{id}/escalate` | `Command(resume={"decision": "escalate", "new_level": "high"})` | IP-1 / IP-2 |
| manual_add | `POST /risk-flags/manual` | 不通过 interrupt（直接写入 RiskFlag 列表 + append ReviewDecision） | — |
| final_submit | `POST /documents/{id}/submit` | `Command(resume={"action": "confirm_submit"})` | IP-3 |

---

## 六、Checkpointer 与 SSE 架构

> **来源**: Teammate 1 §5 + Teammate 2 §6

### 6.1 Checkpointer 选型

| 维度 | PostgreSQL (AsyncPostgresSaver) ✅ | MongoDB (MongoDBSaver) |
|------|:--:|------|
| 技术栈统一 | 主业务数据库同为 PostgreSQL | 需要额外 MongoDB 实例 |
| ACID | 原生事务支持 | 非关系型 |
| Checkpoint 查询 | SQL 直接查询状态快照 | 需要 Mongo 查询 |
| 生产成熟度 | LangGraph 官方推荐 | 可用 |
| **MVP 结论** | **✅ 选择** | 不选择 |

**MVP 策略**: `InMemorySaver`（开发环境）→ `AsyncPostgresSaver`（生产环境）

### 6.2 Checkpoint 创建时机

| 时机 | 内容 | 用途 |
|------|------|------|
| 每个 node 完成时 | 完整 State 快照 | super-step 边界持久化 |
| `interrupt()` 调用时 | State + 中断载荷 | 断点恢复时的起点 |
| 用户暂停时 | State + 当前进度 | 用户恢复时从此 checkpoint 继续 |
| 异常发生时 | State + error_info | 错误后重试的起点 |

### 6.3 SSE 事件类型

| 事件类型 | 推送内容 | 前端展示 |
|---------|---------|---------|
| `parse.progress` | {agent_name, progress_pct, current_clause_type} | P3 解析进度条 |
| `parse.complete` | {document_id, clause_count} | P3→P4 跳转触发 |
| `parse.failed` | {error_type, error_message, recoverable} | P3 失败面板 |
| `review.progress` | {agent_name, clauses_processed, total_clauses, current_dimension} | P4 Agent 并行卡片 |
| `review.log` | {timestamp, agent_name, message} | P4 实时日志流 |
| `review.complete` | {summary: {high, medium, low}} | P4→P5 跳转触发 |
| `review.failed` | {fail_category, message, partial_results_available} | P4 失败面板 |
| `review.timeout` | {completed_count, total_count} | P4 超时面板 |
| `interrupt.ready` | {interrupt_id, interrupt_type, payload} | P5 审批卡片 |

---

## 七、上游约束对齐验证

| # | 约束 | 来源 | Teammate 1 | Teammate 2 |
|---|------|------|:--:|:--:|
| 1 | MVP 仅 NDA | `business_model.md` | ✅ | ✅ |
| 2 | PDF + DOCX | `boundary_spec` | ✅ 5层校验链 | — |
| 3 | 多 Agent 架构 | `business_model.md` | ✅ Supervisor+4 | ✅ 7节点StateGraph |
| 4 | 分级告警 | `business_model.md` | ✅ | ✅ IP-1/2/3 |
| 5 | interrupt 不可跳过 | `flow_state_spec` | ✅ 4层约束 | ✅ IP-1 non-skippable |
| 6 | 并排视图数据提供 | `boundary_spec` | ✅ JSONB 聚合查询 | — |
| 7 | 解释性数据透明 | `boundary_spec` | ✅ RiskFlag 字段 | ✅ IP payload |
| 8 | 32 API 端点 | `boundary_spec` | ✅ 全部覆盖 | ✅ 8 操作映射 |
| 9 | SSE 实时推送 | `boundary_spec` | ✅ 9 event types | ✅ stream_events |
| 10 | Checkpointer 选型 | `boundary_spec` | ✅ PostgreSQL | ✅ InMemory→Postgres |
| 11 | 审计日志不可篡改 | `boundary_spec` | ✅ Chain-hash | — |
| 12 | OCR 双模式 | `flow_state_spec` | ✅ Celery 异步任务 | — |
| 13 | 部分成功处理 | `flow_state_spec` | ✅ | ✅ reducer 合并 |

---

## 八、Lead 审批记录

| 时间 | 事件 | 决议 |
|------|------|------|
| 2026-07-30 | Teammate 1 提交后端架构计划 | ✅ 批准（4 域 / 5 层 / MCP 3 主题） |
| 2026-07-30 | Teammate 2 提交 HITL 工作流计划 | ✅ 批准（7 节点 / 3 中断点 / 8 操作映射） |
| 2026-07-30 | Teammate 1 MCP 研究 | ✅ 验证 interrupt/StateGraph/Checkpointer/Subagents API |
| 2026-07-30 | Teammate 2 MCP 研究 | ✅ 11 次查询验证 8 个核心 API 签名 |
| 2026-07-30 | Teammate 1 完成 | ✅ `backend_service_arch-v1.0.md`（1,018 行） |
| 2026-07-30 | Teammate 2 完成 | ✅ `langchain_hitl_workflow-v1.0.md` |
| 2026-07-30 | Lead 汇总 | ✅ 本文件（`langchain_hitl_arch-v1.0.md`） |

---

> **相关文档**:
> - `../06_system_architecture/backend_service_arch-v1.0.md` — 后端服务架构
> - `../06_system_architecture/langchain_hitl_workflow-v1.0.md` — LangChain HITL 工作流
> - `../03_business_modeling/business_model.md` — 业务问题建模
> - `flow_state_spec.md` — 状态流转规范
> - `../06_system_architecture/frontend_backend_boundary_spec-v1.0.md` — 前后端边界规范
