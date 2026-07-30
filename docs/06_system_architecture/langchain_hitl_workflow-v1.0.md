# LangChain HITL 文档审核工作流设计 v1.0

> **版本**: v1.0
> **创建日期**: 2026-07-30
> **文档性质**: 系统架构设计 -- 基于 LangChain 官方 MCP 规范，定义完整的人机交互审核工作流
> **上游依赖**:
> - `docs/03_business_modeling/business_model.md` -- 业务问题建模（MVP 范围、核心实体、分级告警策略）
> - `docs/04_interaction_design/flow_state_spec.md` -- 状态流转规范（三阶段职责边界、54 个交互节点）
> - `docs/04_interaction_design/human_approval_flow.md` -- 人工审批交互链路（8 操作 6 要素、分级处置、不可跳过约束）
> - `docs/06_system_architecture/frontend_backend_boundary_spec-v1.0.md` -- 前后端边界规范（32 API 端点、SSE 事件类型、数据归属）
> **下游读者**: 后端实现计划 (`docs/10_backend_plan/`)、API 规范 (`docs/08_api_specification/`)、数据模型设计 (`docs/07_data_model/`)

---

## 目录

1. [整体工作流定义](#一整体工作流定义)
2. [状态定义](#二状态定义基于-langgraph-state)
3. [中断点设计](#三中断点设计-interrupt-points)
4. [状态流转规则](#四状态流转规则)
5. [与前端 HITL 操作的映射](#五与前端-hitl-操作的映射)
6. [Checkpointer 配置](#六checkpointer-配置)

---

## 一、整体工作流定义

### 1.1 工作流概述

本工作流基于LangGraph `StateGraph` 构建，实现文档解析到人工审批的端到端自动化审核流程。工作流以 `interrupt()` 机制嵌入三级人机交互中断点，与 `business_model.md` 的分级告警策略对齐。

### 1.2 技术基础（基于LangChain官方MCP规范验证）

| 组件 | 来源 | 官方 API 签名 |
|------|------|-------------|
| 中断机制 | `langgraph.types.interrupt` | `interrupt(value: Any) -> Any` |
| 恢复机制 | `langgraph.types.Command` | `Command(*, graph: str \| None = None, update: Any \| None = None, resume: dict[str, Any] \| Any \| None = None, goto: Send \| Sequence[Send \| N] \| N = ())` |
| 中断事件 | `langgraph.types.Interrupt` | `Interrupt(value: Any, id: str)` -- 包含 `.value` 和 `.id` 属性 |
| Agent 创建 | `langchain.agents.create_agent` | `create_agent(model, tools, *, system_prompt, middleware, checkpointer, state_schema, context_schema, ...) -> CompiledStateGraph` |
| HITL 中间件 | `langchain.agents.middleware.HumanInTheLoopMiddleware` | `HumanInTheLoopMiddleware(interrupt_on: dict[str, bool \| InterruptOnConfig], *, description_prefix: str)` |
| 中断配置 | `langchain.agents.middleware.InterruptOnConfig` | `InterruptOnConfig(allowed_decisions: list[DecisionType], description: NotRequired[str \| _DescriptionFactory], args_schema: NotRequired[dict[str, Any]], when: NotRequired[Callable[[ToolCallRequest], bool]])` |
| Agent State | `langchain.agents.middleware.types.AgentState` | `AgentState(messages: Required[Annotated[list[AnyMessage], add_messages]], jump_to: NotRequired[...], structured_response: NotRequired[...])` |
| 事件流 | `graph.stream_events(...)` | `stream_events(input, config, *, version="v3")` -- 返回 `.messages`, `.values`, `.interrupts`, `.interrupted`, `.output` |
| Checkpointer | `langgraph.checkpoint.memory.InMemorySaver` | `InMemorySaver()` -- 内存实现 |
| 生产 Checkpointer | `langgraph.checkpoint.postgres.aio.AsyncPostgresSaver` | `AsyncPostgresSaver.from_conn_string(DB_URI)` |

> **重要**: 以上所有 API 签名均来自 LangChain 官方 MCP 查询结果。`interrupt()` 函数签名来自`langgraph.types`模块（`interrupt(value: Any) -> Any`），`Command` 类的 `resume` 参数支持 `dict[str, Any] | Any | None` 类型，其中 `dict[str, Any]` 用于多中断映射（中断 ID -> 恢复值）。

### 1.3 工作流节点清单

基于 `business_model.md` SS 4.1 功能到业务实体的映射和 `flow_state_spec.md` 三阶段职责边界，定义 7 个核心工作流节点：

| # | 节点名称 | 节点类型 | Agent 归属 | 输入 | 输出 | 说明 |
|---|---------|---------|-----------|------|------|------|
| 1 | `parse_document` | 数据预处理 | Parser Agent | Document 二进制流 | clauses[] 列表 | 格式检测、OCR、文档分段、条款结构提取 |
| 2 | `extract_clauses` | Agent 节点 | Clause Extraction Agent | parse_document 输出 | 结构化 clauses[] | 条款类型分类、关键实体提取、位置标注 |
| 3 | `risk_analysis` | Agent 节点 | Risk Analysis Agent | clauses[] + Playbook | risk_flags[] | 风险分级标记（高/中/低）、置信度评分、判定依据生成 |
| 4 | `compliance_check` | Agent 节点 | Compliance Agent | clauses[] + 法规库 | compliance_results[] | NDA 合规检查（GDPR/CCPA/PIPL 条款符合性） |
| 5 | `generate_report_draft` | Agent 节点 | Report Agent | risk_flags[] + compliance_results[] | report_draft | 风险摘要、条款清单、Playbook 对比、修改建议汇总 |
| 6 | `human_review` | 中断节点 | 无（HITL 控制） | report_draft + risk_flags[] | review_decisions[] | **三个中断点所在节点**，处理高/中/低风险分级审批 |
| 7 | `finalize_report` | Agent 节点 | Report Agent | review_decisions[] + report_draft | final_report | 合并人工裁定、生成可签署的最终审阅报告 |

### 1.4 工作流图结构 (Python / LangGraph)

以下代码展示基于 LangGraph `StateGraph` 的完整工作流拓扑结构（仅拓扑，不含完整节点实现）：

```python
from typing import Annotated, TypedDict, Optional
import operator
import uuid

from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command, interrupt
from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langgraph.checkpoint.memory import InMemorySaver

# ─────────────────────────────────────────────────────────────────
# State 定义（详见§二完整定义）
# ─────────────────────────────────────────────────────────────────
class DocumentReviewState(TypedDict):
    document_id: str
    doc_status: str
    clauses: Annotated[list[dict], operator.add]
    risk_flags: Annotated[list[dict], operator.add]
    compliance_results: Annotated[list[dict], operator.add]
    report_draft: Optional[dict]
    review_decisions: Annotated[list[dict], operator.add]
    current_stage: str
    interrupt_state: Optional[dict]
    error_info: Optional[dict]


# ─────────────────────────────────────────────────────────────────
# 节点函数（仅签名，具体实现见各节）
# ─────────────────────────────────────────────────────────────────
def node_parse_document(state: DocumentReviewState) -> dict:
    """阶段1: 文档解析 -- 格式检测、OCR、条款提取"""
    # ... 实现逻辑 ...
    pass

def node_extract_clauses(state: DocumentReviewState) -> dict:
    """阶段1: 条款结构化 -- 类型分类、实体提取"""
    # ... 实现逻辑 ...
    pass

def node_risk_analysis(state: DocumentReviewState) -> dict:
    """阶段2: 风险分析 -- 分级标记、置信度评分"""
    # ... 实现逻辑 ...
    pass

def node_compliance_check(state: DocumentReviewState) -> dict:
    """阶段2: 合规检查 -- NDA 法规符合性"""
    # ... 实现逻辑 ...
    pass

def node_generate_report_draft(state: DocumentReviewState) -> dict:
    """阶段2: 报告草稿生成"""
    # ... 实现逻辑 ...
    pass

def node_human_review(state: DocumentReviewState) -> dict:
    """阶段3: 人工审批 -- 包含三个中断点（详见§三）"""
    # 中断的详细设计见 §三
    pass

def node_finalize_report(state: DocumentReviewState) -> dict:
    """阶段3: 最终报告生成"""
    # ... 实现逻辑 ...
    pass


# ─────────────────────────────────────────────────────────────────
# 构建 StateGraph
# ─────────────────────────────────────────────────────────────────
graph = StateGraph(DocumentReviewState)

graph.add_node("parse_document", node_parse_document)
graph.add_node("extract_clauses", node_extract_clauses)
graph.add_node("risk_analysis", node_risk_analysis)
graph.add_node("compliance_check", node_compliance_check)
graph.add_node("generate_report_draft", node_generate_report_draft)
graph.add_node("human_review", node_human_review)
graph.add_node("finalize_report", node_finalize_report)

# 主路径
graph.add_edge(START, "parse_document")
graph.add_edge("parse_document", "extract_clauses")
# 风险分析和合规检查并行（reduce 合并到共享 state.risk_flags 和 state.compliance_results）
graph.add_edge("extract_clauses", "risk_analysis")
graph.add_edge("extract_clauses", "compliance_check")
# 等待两个并行节点完成，进入报告生成
graph.add_edge("risk_analysis", "generate_report_draft")
graph.add_edge("compliance_check", "generate_report_draft")
graph.add_edge("generate_report_draft", "human_review")
graph.add_edge("human_review", "finalize_report")
graph.add_edge("finalize_report", END)

checkpointer = InMemorySaver()
compiled_graph = graph.compile(checkpointer=checkpointer)
```

### 1.5 并行节点与 Reducer 语义

`risk_analysis` 和 `compliance_check` 从 `extract_clauses` 并行分叉（fan-out），两者同时执行。由于两者都向 `state.risk_flags` 和 `state.compliance_results` 写入数据，必须使用 `operator.add` reducer（`Annotated[list[dict], operator.add]`）确保并发写入时执行列表追加而非覆盖。

参考 LangGraph 官方 reducer 模式：

```python
# 官方模式：Annotated 装饰器指定 reducer 函数
from typing import Annotated
import operator

class State(TypedDict):
    risk_flags: Annotated[list[dict], operator.add]
    # 等价于：每次节点返回 {"risk_flags": [new_item]} 时，
    # 自动追加而非覆盖：risk_flags = old_risk_flags + new_risk_flags
```

---

## 二、状态定义（基于 LangGraph State）

### 2.1 完整 State 类型定义

```python
from typing import Annotated, TypedDict, Optional, Literal
import operator
from datetime import datetime


# ─────────── 枚举类型 ───────────
RiskLevel = Literal["高", "中", "低"]
DocStatus = Literal[
    "UPLOADED", "PARSING", "PARSE_COMPLETE", "PARSE_FAILED",
    "AI_REVIEWING", "AI_REVIEW_COMPLETE", "AI_REVIEW_FAILED",
    "PARTIAL_SUCCESS",
    "IN_REVIEW", "HIGH_RISK_ALL_REVIEWED",
    "SUBMITTED", "DRAFT", "REPORT_GENERATING", "REPORT_READY",
    "CANCELLED", "PAUSED"
]
DecisionType = Literal["approve", "edit", "reject"]
ReviewStage = Literal[
    "initializing", "high_risk_review", "medium_risk_review",
    "low_risk_spot_check", "final_confirmation", "completed"
]


# ─────────── 子类型定义 ───────────
class ClauseDict(TypedDict, total=False):
    """条款字典"""
    clause_id: str
    clause_type: str                    # "保密义务" / "保密期限" / "除外信息" / ...
    raw_text: str
    position_start: int                 # 字符偏移
    position_end: int
    page_number: int
    source: str                         # "AI" / "MANUAL"


class RiskFlagDict(TypedDict, total=False):
    """风险标记字典"""
    flag_id: str
    clause_id: str
    risk_level: RiskLevel               # "高" / "中" / "低"
    risk_category: str                  # "定义过宽" / "期限不合理" / "缺失关键条款" / ...
    ai_confidence: float                # 0.0 - 1.0, 仅 AI 来源
    reasoning: str                      # AI 判定依据
    suggestion: Optional[str]           # AI 修改建议
    playbook_rule_id: Optional[str]
    playbook_diff: Optional[str]        # 与标准条款的差异描述
    status: str                         # "PENDING_REVIEW" / "CONFIRMED" / "MODIFIED" / "REJECTED" / ...
    source: str                         # "AI" / "MANUAL"
    resolution: Optional[str]           # "HUMAN_CONFIRMED" / "UNREVIEWED_AUTO_PASSED" / "REVIEWED_CONFIRMED" / ...
    escalated: bool
    escalated_from: Optional[str]
    sampled: bool
    created_by: Optional[str]
    created_at: Optional[str]


class ReviewDecisionDict(TypedDict, total=False):
    """审阅决策字典"""
    decision_id: str
    risk_flag_id: str
    decision_type: DecisionType         # "approve" / "edit" / "reject"
    reviewer_id: str
    comment: str
    modified_fields: Optional[dict]     # 编辑模式下的字段变更
    original_values: Optional[dict]     # 编辑前快照
    new_values: Optional[dict]          # 编辑后值
    timestamp: str


class ComplianceResultDict(TypedDict, total=False):
    """合规检查结果字典"""
    check_id: str
    clause_id: str
    regulation: str                     # "GDPR" / "CCPA" / "PIPL"
    compliance_status: str              # "compliant" / "non_compliant" / "needs_review"
    detail: str


class InterruptStateDict(TypedDict, total=False):
    """中断状态字典"""
    active_interrupt: Optional[str]     # 当前活跃的中断点标识: "IP-1" / "IP-2" / "IP-3"
    pending_high_risk_ids: list[str]    # 待审批的高风险 flag_id 列表
    pending_medium_risk_ids: list[str]  # 待批量审批的中风险 flag_id 列表
    interrupt_payload: Optional[dict]   # 传给前端的当前中断数据


class ErrorInfoDict(TypedDict, total=False):
    """错误信息字典"""
    error_type: str                     # "parse_failure" / "review_timeout" / "agent_error"
    error_message: str
    recoverable: bool
    retry_count: int
    failed_node: str


# ─────────── 完整 State 类型 ───────────
class DocumentReviewState(TypedDict, total=False):
    """
    文档审核工作流的完整状态定义。

    字段使用 Annotated reducer 控制合并语义：
    - operator.add: 列表字段使用追加语义，支持并行节点安全写入
    - 未注解字段: 默认覆盖语义（最后一个写入者胜出）
    """
    # ── 文档标识 ──
    document_id: str
    doc_filename: str
    doc_format: str                     # "PDF" / "DOCX"
    doc_status: DocStatus

    # ── 条款数据（追加 reducer：并行节点安全）──
    clauses: Annotated[list[ClauseDict], operator.add]

    # ── 风险数据（追加 reducer：risk_analysis 和 compliance_check 并行写入）──
    risk_flags: Annotated[list[RiskFlagDict], operator.add]

    # ── 合规数据（追加 reducer）──
    compliance_results: Annotated[list[ComplianceResultDict], operator.add]

    # ── 报告草稿（覆盖语义：仅 report agent 写入）──
    report_draft: Optional[dict]

    # ── 审阅决策（追加 reducer：每次人工操作追加一条）──
    review_decisions: Annotated[list[ReviewDecisionDict], operator.add]

    # ── 控制字段 ──
    current_stage: ReviewStage
    interrupt_state: Optional[InterruptStateDict]
    error_info: Optional[ErrorInfoDict]
```

### 2.2 Reducer 语义说明

| 字段 | Reducer | 语义 | 并行安全性 |
|------|---------|------|:--------:|
| `clauses` | `operator.add` | 列表追加：`new_list = old_list + node_output` | ✅ 安全（fan-out 到多个 clause 提取 Agent 时各自追加） |
| `risk_flags` | `operator.add` | 列表追加：`risk_analysis` 和 `compliance_check` 并行写入，自动合并 | ✅ 安全 |
| `compliance_results` | `operator.add` | 列表追加：同上 | ✅ 安全 |
| `review_decisions` | `operator.add` | 列表追加：每次人工审批操作追加一条决策记录 | ✅ 安全（顺序调用，不存在并发） |
| `report_draft` | 默认覆盖 | 最后写入者胜出：仅 `generate_report_draft` 单选写入 | N/A |
| `document_id` 等 | 默认覆盖 | 最后写入者胜出：仅初始化时写入一次 | N/A |
| `current_stage` | 默认覆盖 | 每个节点更新当前阶段标识 | N/A |
| `interrupt_state` | 默认覆盖 | 中断节点更新当前中断上下文 | N/A |

### 2.3 状态在各节点间的流转方式

```
parse_document:
  输入: { document_id, doc_filename, doc_format, doc_status: "UPLOADED" }
  输出: { clauses: [ClauseDict...], doc_status: "PARSE_COMPLETE" }
    └─ 操作：将提取的 ClauseDict 列表写入 state.clauses（追加），更新状态

extract_clauses:
  输入: state.clauses (来自 parse_document)
  输出: { clauses: [结构化 ClauseDict...] }
    └─ 操作：丰富条款数据（类型分类、实体提取），替换/更新 clauses

risk_analysis ┐
              ├─ (并行 fan-out)
compliance_check ┘
  输入: state.clauses
  输出: { risk_flags: [RiskFlagDict...], compliance_results: [ComplianceResultDict...] }
    └─ 操作：并行追加风险标记和合规结果，通过 operator.add reducer 自动合并

generate_report_draft:
  输入: { risk_flags, compliance_results, clauses }
  输出: { report_draft: { summary_stats, ... } }
    └─ 操作：聚合全量数据生成报告草稿（覆盖写入）

human_review:
  输入: { report_draft, risk_flags, review_decisions, clauses }
  输出: { review_decisions: [ReviewDecisionDict...], current_stage: ..., interrupt_state: ... }
    └─ 操作：通过 interrupt() 暂停，等待前端人工审批后 resume
    └─ 关键：所有高风险项必须从 PENDING_REVIEW 转为非 PENDING_REVIEW 状态后才允许 resume IP-3

finalize_report:
  输入: { report_draft, review_decisions, risk_flags, clauses, compliance_results }
  输出: { doc_status: "REPORT_READY" }
    └─ 操作：合并人工裁定、生成最终报告
```

---

## 三、中断点设计 (Interrupt Points)

### 3.1 中断点总览

基于 `business_model.md` SS 4.1 分级告警策略（高风险 100% 强制、中风险批量可选、低风险自动通过 + 抽样），在 `human_review` 节点中定义 3 个中断点，均使用 `interrupt()` 实现动态暂停：

| 中断点 | 触发位置 | 风险等级 | 是否可跳过 | 中断模式 | 对应前端操作 |
|:---:|---------|:------:|:--------:|---------|------------|
| **IP-1** | `human_review` 节点内，遍历所有 `risk_level == "高"` 且 `status == "PENDING_REVIEW"` 的 RiskFlag | 高 | **否**（不可跳过） | 逐条中断：每项触发一次 `interrupt()` | approve / edit / reject |
| **IP-2** | IP-1 完成后，汇总所有 `risk_level == "中"` 且未审核的 RiskFlag | 中 | 是（可一键全部确认） | 批量中断：一次 `interrupt()` 提交全量列表 | batch_approve / deep_dive / 逐个处理 |
| **IP-3** | IP-2 完成后，提交最终审阅摘要 | 全部 | 否（必须决策） | 确认中断：一次 `interrupt()` 提交完整摘要 | final_submit / save_draft |

**中断触发顺序**：

```
human_review 节点入口
    │
    ├─ 阶段 A: IP-1 高风险逐条审批
    │     while 存在 status == "PENDING_REVIEW" 的 high-risk flag:
    │         interrupt(high_risk_payload)  →  等待 resume
    │         根据 resume 更新 ReviewDecision + RiskFlag.status
    │
    ├─ 阶段 B: IP-2 中风险批量审批
    │     interrupt(medium_risk_batch_payload)  →  等待 resume
    │     根据 resume 批量更新中风险项状态
    │
    └─ 阶段 C: IP-3 最终确认
          interrupt(final_confirmation_payload)  →  等待 resume
          根据 resume 决定 submit / save_draft / back_to_review
```

### 3.2 IP-1: 高风险条款逐条审批

#### 中断 payload 结构（传给前端的数据）

```python
# IP-1 Payload（每个高风险条款的 `interrupt()` 参数）
high_risk_payload = {
    "interrupt_type": "HIGH_RISK_APPROVAL",          # 中断类型标识
    "interrupt_point": "IP-1",                       # 中断点编号
    "risk_flag": {
        "flag_id": "rf_001",
        "clause_id": "cl_015",
        "risk_level": "高",
        "risk_category": "定义过宽",
        "ai_confidence": 0.92,
        "reasoning": "1. '任何及所有信息' -- 范围无边界，未排除以下信息：\n"
                     "   a) 接收方在披露前已合法持有的信息\n"
                     "   b) 非因接收方过错而进入公有领域的信息\n"
                     "   c) 接收方从有权披露的第三方合法获得的信息\n"
                     "2. 未要求披露方对保密信息进行合理标识",
        "suggestion": "建议将'与披露方有关的任何及所有信息'替换为: '披露方以书面形式"
                      "明确标识为'保密'的信息，但不包括：\n"
                      "(i) 接收方在披露前已合法持有的信息；\n"
                      "(ii) 非因接收方违反本协议而进入公有领域的信息；\n"
                      "(iii) 接收方从有权披露的第三方合法获得的信息。'",
        "playbook_rule_id": "PB-NDA-003",
        "playbook_diff": "缺少标识要求 + 缺少三项标准排除",
    },
    "clause_context": {
        "clause_type": "保密义务范围",
        "clause_text": "接收方承诺对其因履行本协议而知悉的、与披露方有关的任何及所有"
                       "信息（下称'保密信息'）承担保密义务。",
        "position_start": 1420,
        "position_end": 1520,
        "page_number": 2,
    },
    "review_progress": {
        "current_index": 1,                          # 当前第几条高风险项（1-based）
        "total_high_risk": 3,                        # 高风险项总数
        "remaining": 2,                              # 剩余未审批数
    },
    "allowed_decisions": ["approve", "edit", "reject"],
    "constraints": {
        "reject_requires_reason": True,              # 驳回必须填写原因
        "reason_min_length": 10,                     # 驳回原因最少 10 字符
        "edit_requires_changes": True,               # 编辑必须实际修改内容
    }
}
```

#### Resume 处理逻辑

```python
# 前端通过 Command(resume=...) 返回的决策结构
# 三种决策类型的 resume 结构：

# (a) 同意
resume_approve = {
    "interrupt_point": "IP-1",
    "flag_id": "rf_001",
    "decision": "approve",
    # comment 可选
}

# (b) 编辑
resume_edit = {
    "interrupt_point": "IP-1",
    "flag_id": "rf_001",
    "decision": "edit",
    "modified_fields": {
        "risk_level": "中",                          # 可选：调整风险等级
        "risk_category": "期限不合理",               # 可选：调整风险类别
        "suggestion": "..."                          # 可选：编辑修改建议
    },
    "comment": "等级下调为中风险，因为...",           # 必填 >= 10 字符
}

# (c) 驳回
resume_reject = {
    "interrupt_point": "IP-1",
    "flag_id": "rf_001",
    "decision": "reject",
    "comment": "该条款为行业标准表述，在实际司法实践中此类措辞已被广泛接受。",  # 必填 >= 10 字符
}
```

#### 节点内 resume 处理代码（IP-1 部分）

```python
def _handle_ip1_resume(state: DocumentReviewState, flag: RiskFlagDict, resume_data: dict) -> dict:
    """
    处理 IP-1 的 resume 数据，更新 RiskFlag 状态并生成 ReviewDecision。

    resume_data 来自 Command(resume=...) 的返回值，即前端提交的决策数据。
    """
    decision_type = resume_data["decision"]
    flag_id = resume_data["flag_id"]

    decision_record = {
        "decision_id": f"dec_{uuid.uuid4().hex[:12]}",
        "risk_flag_id": flag_id,
        "decision_type": decision_type,
        "reviewer_id": resume_data.get("reviewer_id", "unknown"),
        "comment": resume_data.get("comment", ""),
        "timestamp": datetime.utcnow().isoformat(),
    }

    if decision_type == "approve":
        # 确认 AI 标记：status -> CONFIRMED
        new_flag_status = "CONFIRMED"
        new_flag_resolution = "HUMAN_CONFIRMED"

    elif decision_type == "edit":
        # 修正 AI 标记
        decision_record["modified_fields"] = resume_data.get("modified_fields", {})
        decision_record["new_values"] = resume_data.get("modified_fields", {})
        new_flag_status = "MODIFIED"
        new_flag_resolution = "HUMAN_MODIFIED"

        # 如果等级被降级为中/低风险，该项移出高风险队列
        # 高->中：进入 IP-2 的处理范围
        # 高->低：进入低风险自动通过
        if resume_data.get("modified_fields", {}).get("risk_level") == "无风险-驳回":
            new_flag_status = "REJECTED"

    elif decision_type == "reject":
        # 驳回 AI 标记
        new_flag_status = "REJECTED"
        new_flag_resolution = "HUMAN_REJECTED"

    else:
        raise ValueError(f"Invalid decision type: {decision_type}")

    # 更新 RiskFlag（通过追加到 state.risk_flags 触发 reducer，实际实现中需用 update_state）
    updated_flag = {**flag, "status": new_flag_status, "resolution": new_flag_resolution}

    return {
        "review_decisions": [decision_record],
        # 使用 getState/updateState 更新 risk_flags 中的对应条目
        # 此处返回供外部 update_state 调用
        "_updated_flag": updated_flag,
    }
```

### 3.3 IP-2: 中风险条款批量审批

#### 中断 payload 结构

```python
# IP-2 Payload（所有中风险条款的批量汇总，一次 interrupt() 提交）
medium_risk_batch_payload = {
    "interrupt_type": "MEDIUM_RISK_BATCH_APPROVAL",  # 中断类型标识
    "interrupt_point": "IP-2",                       # 中断点编号
    "summary": {
        "total_medium_risk": 12,                     # 中风险总数
        "already_reviewed": 2,                       # 已深入审核数
        "auto_pass_candidates": 10,                  # 可自动通过的候选数
        "default_action": "auto_pass",               # 默认操作为自动通过
    },
    "items": [                                       # 所有中风险项列表
        {
            "flag_id": "rf_010",
            "clause_id": "cl_030",
            "risk_category": "法域不利",
            "ai_confidence": 0.78,
            "clause_type": "管辖法律",
            "status": "PENDING_REVIEW",
            "resolved": False,                       # 是否已经处理（深入审核过的）
        },
        # ... 更多中风险项
    ],
    "allowed_decisions": ["batch_confirm", "deep_dive"],
    "note": "未审核的中风险条款将自动标记为 '未审核-自动通过'。建议对不确定的条款使用 '深入审核'。"
}
```

#### Resume 处理逻辑

```python
# (a) 批量确认（一键将剩余未审核项全部标记为自动通过）
resume_batch_confirm = {
    "interrupt_point": "IP-2",
    "decision": "batch_confirm",
    # 批量确认：所有 status == "PENDING_REVIEW" 的中风险项
    # 标记为 status = "AUTO_APPROVED", resolution = "UNREVIEWED_AUTO_PASSED"
    "items_to_auto_pass": ["rf_011", "rf_012", "rf_013", ...],  # 可选：指定具体项
}

# (b) 深入审核单条后返回批量列表（对单条做出决策后继续中断循环等待其余项）
resume_deep_dive = {
    "interrupt_point": "IP-2",
    "decision": "deep_dive",
    "flag_id": "rf_010",
    "sub_decision": "approve",                       # approve / edit / reject
    "comment": "确认 AI 标记准确",
    # 深入审核的模式与 IP-1 相同，但操作完成后返回 IP-2 的中断状态
    # 而不是推进下一个高风险项
}
```

#### IP-2 节点内循环逻辑

```python
# IP-2 处理伪代码
# 中风险：可全部确认或部分深入审核
medium_risk_items = [f for f in state["risk_flags"]
                     if f["risk_level"] == "中" and f.get("status") == "PENDING_REVIEW"]

batch_payload = _build_ip2_payload(medium_risk_items)  # 见上面 payload 结构

resume_data = interrupt(batch_payload)  # 暂停，等待前端决策

if resume_data["decision"] == "batch_confirm":
    # 批量确认：所有未审核中风险 -> AUTO_APPROVED
    for item in medium_risk_items:
        yield _auto_approve_medium_risk(item)  # status=AUTO_APPROVED, resolution=UNREVIEWED_AUTO_PASSED

elif resume_data["decision"] == "deep_dive":
    # 深入审核单条：该条按 IP-1 相同逻辑处理（approve/edit/reject）
    flag = _find_flag(resume_data["flag_id"])
    yield _handle_single_review(flag, resume_data["sub_decision"], resume_data)
    # 处理完一条后，回到 IP-2 重新构建剩余列表并再次中断
    # （通过 human_review 节点重入实现，因为 interrupt() 后节点从开头重执行）
```

### 3.4 IP-3: 最终报告确认

#### 中断 payload 结构

```python
# IP-3 Payload（最终审阅摘要，在所有高/中风险处理完毕后触发）
final_confirmation_payload = {
    "interrupt_type": "FINAL_REVIEW_CONFIRMATION",   # 中断类型标识
    "interrupt_point": "IP-3",                       # 中断点编号
    "precondition_check": {
        "all_high_risk_resolved": True,              # 高风险全部非 PENDING_REVIEW
        "has_at_least_one_operation": True,          # 至少有一次审批操作
    },
    "summary": {
        "total_ai_flags": 60,
        "high_risk": {
            "total": 3,
            "confirmed": 2,
            "modified": 0,
            "rejected": 1,
        },
        "medium_risk": {
            "total": 12,
            "reviewed_confirmed": 2,
            "auto_passed": 10,
        },
        "low_risk": {
            "total": 45,
            "auto_passed": 40,
            "spot_checked": 5,
            "spot_check_confirmed": 4,
            "spot_check_skipped": 1,
        },
        "manual_additions": {
            "total": 2,
            "confirmed": 2,
        },
    },
    "high_risk_details": [                              # 高风险条款最终状态
        {
            "flag_id": "rf_001",
            "clause_type": "保密义务范围",
            "risk_category": "定义过宽",
            "final_status": "CONFIRMED",
        },
        {
            "flag_id": "rf_002",
            "clause_type": "保密期限",
            "risk_category": "期限不合理",
            "final_status": "CONFIRMED",
        },
        {
            "flag_id": "rf_003",
            "clause_type": "除外信息定义",
            "risk_category": "缺失关键条款",
            "final_status": "REJECTED",
            "reject_reason": "该条款将除外信息定义分散在第5条和第8条...",
        },
    ],
    "operations_breakdown": {
        "total_operations": 15,
        "approve": 6,
        "edit": 0,
        "reject": 1,
        "batch_approve": 1,
        "spot_check_confirm": 4,
        "skip": 1,
        "manual_add": 2,
    },
    "review_duration_minutes": 12,
    "allowed_decisions": ["confirm_submit", "save_draft", "back_to_review"],
}
```

#### Resume 处理逻辑

```python
# (a) 确认提交 -- 触发最终报告生成
resume_confirm_submit = {
    "interrupt_point": "IP-3",
    "decision": "confirm_submit",
}

# (b) 暂存草稿 -- 保持当前状态但不推进工作流
resume_save_draft = {
    "interrupt_point": "IP-3",
    "decision": "save_draft",
}

# (c) 返回继续审阅 -- 回到 IP-1 / IP-2 继续修改
resume_back_to_review = {
    "interrupt_point": "IP-3",
    "decision": "back_to_review",
}
```

#### IP-3 提交前验证逻辑

```python
# 后端在 IP-3 中断前和 resume confirm_submit 时均执行验证
def _validate_submit_readiness(state: DocumentReviewState) -> tuple[bool, str]:
    """
    验证是否可以提交审阅结果。
    返回 (is_ready, error_message)
    """
    risk_flags = state.get("risk_flags", [])

    # 检查 1: 所有高风险项必须已处理（不可跳过约束 -- API 409 级别）
    pending_high = [f for f in risk_flags
                    if f["risk_level"] == "高" and f.get("status") == "PENDING_REVIEW"]
    if pending_high:
        return False, f"存在 {len(pending_high)} 项高风险条款尚未审批，无法提交。"

    # 检查 2: 至少执行过一次操作（由 review_decisions 列表的非空性保证）
    if len(state.get("review_decisions", [])) == 0:
        return False, "尚未执行任何审批操作，无法提交。"

    return True, "OK"
```

### 3.5 完整的 `node_human_review` 实现

```python
def node_human_review(state: DocumentReviewState) -> dict:
    """
    阶段 3: 人工审批节点。

    本节点包含三个中断点 (IP-1, IP-2, IP-3)，按顺序触发。
    每个中断点使用 `interrupt()` 暂停执行，等待前端通过 Command(resume=...) 提交审批决策。

    关键约束：
    - IP-1 (高风险): 不可跳过，必须逐条审批
    - IP-2 (中风险): 可批量确认或选择性深入
    - IP-3 (最终确认): 必须决策（submit / save_draft / back_to_review）

    interrupt() 的 `value` 参数（payload）会通过 stream.interrupts 传递给前端；
    Command(resume=...) 的值会成为 interrupt() 的返回值，用于驱动后续逻辑。
    """
    output = {}
    risk_flags = state.get("risk_flags", [])

    # ─────────────────────────────────────────────
    # 阶段 A: IP-1 高风险逐条审批
    # ─────────────────────────────────────────────
    high_risk_pending = [
        f for f in risk_flags
        if f["risk_level"] == "高" and f.get("status") == "PENDING_REVIEW"
    ]

    for idx, flag in enumerate(high_risk_pending):
        # 构建 IP-1 payload
        payload = _build_ip1_payload(
            flag=flag,
            current_index=idx + 1,
            total=len(high_risk_pending),
            state=state,
        )

        # [中断] 暂停执行，payload 通过 stream.interrupts 传递给前端
        # 前端审批后通过 Command(resume=...) 返回决策
        resume_data = interrupt(payload)

        # [恢复] resume_data 是前端返回的决策结构
        decision_result = _handle_ip1_resume(state, flag, resume_data)
        output["review_decisions"] = state.get("review_decisions", []) + \
            decision_result.get("review_decisions", [])

        # 更新 risk_flags 中的对应条目
        if "_updated_flag" in decision_result:
            _update_flag_in_state(state, decision_result["_updated_flag"])

    # ─────────────────────────────────────────────
    # 阶段 B: IP-2 中风险批量审批
    # ─────────────────────────────────────────────
    medium_risk_pending = [
        f for f in state.get("risk_flags", [])
        if f["risk_level"] == "中" and f.get("status") == "PENDING_REVIEW"
    ]

    if medium_risk_pending:
        batch_payload = _build_ip2_payload(medium_risk_pending)

        resume_data = interrupt(batch_payload)

        if resume_data["decision"] == "batch_confirm":
            # 批量确认
            for item in medium_risk_pending:
                _auto_approve_medium(state, item, output)
        elif resume_data["decision"] == "deep_dive":
            # 深入审核单条（处理完后节点重入重新构建 medium_risk_pending）
            flag = _find_flag(state, resume_data["flag_id"])
            _handle_single_review(state, flag, resume_data["sub_decision"],
                                  resume_data, output)

    # ─────────────────────────────────────────────
    # 阶段 C: IP-3 最终确认
    # ─────────────────────────────────────────────
    # 提交前验证
    is_ready, error_msg = _validate_submit_readiness(state)
    if not is_ready:
        # 不应到达这里（前端应已阻止），防御性检查
        raise ValueError(error_msg)

    confirmation_payload = _build_ip3_payload(state)

    resume_data = interrupt(confirmation_payload)

    if resume_data["decision"] == "confirm_submit":
        output["doc_status"] = "SUBMITTED"
        output["current_stage"] = "completed"
    elif resume_data["decision"] == "save_draft":
        output["doc_status"] = "DRAFT"
        output["current_stage"] = "final_confirmation"
    elif resume_data["decision"] == "back_to_review":
        output["current_stage"] = "high_risk_review"
        # 节点返回后通过条件边重新进入 human_review

    return output
```

### 3.6 中断事件流与 SSE 推送

当使用 `graph.stream_events(..., version="v3")` 时，中断的事件流如下：

```python
from langgraph.types import Command

config = {"configurable": {"thread_id": "doc-review-001"}}

# 步骤 1: 启动工作流
stream = compiled_graph.stream_events(
    {"document_id": "doc_001", "doc_filename": "NDA_2026_v3.pdf",
     "doc_format": "PDF", "doc_status": "UPLOADED"},
    config=config,
    version="v3",
)

# 步骤 2: 驱动流到完成（或中断暂停）
try:
    final = stream.output  # 阻塞直到完成或中断
except Exception:
    pass

# 步骤 3: 检查是否被中断
if stream.interrupted:
    # stream.interrupts 是 tuple[Interrupt, ...]，每个 Interrupt 有 .value 和 .id
    for interrupt_item in stream.interrupts:
        payload = interrupt_item.value       # 传给 interrupt() 的 payload
        interrupt_id = interrupt_item.id     # 唯一中断 ID
        # 前端根据 payload 渲染审批 UI
        # 用户做出决策后，构建 resume_data

    # 步骤 4: 用 Command(resume=...) 恢复（支持单值和多中断映射）
    # 单中断恢复：
    stream = compiled_graph.stream_events(
        Command(resume=resume_data),
        config=config,
        version="v3",
    )
    final = stream.output

    # 多中断恢复（如果有多中断同时等待）：
    # resume_map = {interrupt_id: resume_value, ...}
    # stream = compiled_graph.stream_events(
    #     Command(resume=resume_map),
    #     config=config,
    #     version="v3",
    # )
```

**SSE 事件类型映射**（与 `frontend_backend_boundary_spec-v1.0.md` SS 4.2 对齐）：

| SSE 事件 | 来源 | 内容 |
|---------|------|------|
| `review.interrupt` | `stream.interrupted == True` | `{interrupt_point: "IP-1", payload: ..., interrupt_id: ...}` |
| `review.progress` | `stream.values` 快照 | `{current_stage: "high_risk_review", progress: "1/3"}` |
| `review.complete` | `stream.interrupted == False` + `stream.output` | `{doc_status: "SUBMITTED", ...}` |

---

## 四、状态流转规则

### 4.1 完整状态流转图

```mermaid
stateDiagram-v2
    [*] --> UPLOADED: 文档上传完成

    UPLOADED --> PARSING: 触发解析
    PARSING --> PARSE_COMPLETE: 解析成功
    PARSING --> PARSE_FAILED: 解析失败
    PARSE_FAILED --> PARSING: 重试解析

    PARSE_COMPLETE --> AI_REVIEWING: 触发 AI 审核
    AI_REVIEWING --> AI_REVIEW_COMPLETE: 审核完成
    AI_REVIEWING --> AI_REVIEW_FAILED: 审核失败
    AI_REVIEWING --> PAUSED: 用户暂停
    PAUSED --> AI_REVIEWING: 恢复审核
    AI_REVIEW_FAILED --> AI_REVIEWING: 重试审核

    AI_REVIEW_COMPLETE --> IN_REVIEW: 进入人工审批

    state IN_REVIEW {
        [*] --> HIGH_RISK_REVIEW: IP-1 高风险逐条审批
        HIGH_RISK_REVIEW --> HIGH_RISK_REVIEW: 审批下一条高风险
        HIGH_RISK_REVIEW --> MEDIUM_RISK_REVIEW: 所有高风险处理完毕

        MEDIUM_RISK_REVIEW --> MEDIUM_RISK_REVIEW: 深入审核返回批量列表
        MEDIUM_RISK_REVIEW --> FINAL_CONFIRMATION: 中风险全部处理完毕

        FINAL_CONFIRMATION --> HIGH_RISK_REVIEW: back_to_review
    }

    IN_REVIEW --> SUBMITTED: confirm_submit (IP-3)
    IN_REVIEW --> DRAFT: save_draft (IP-3)
    DRAFT --> IN_REVIEW: 恢复审阅

    SUBMITTED --> REPORT_GENERATING: 触发报告生成
    REPORT_GENERATING --> REPORT_READY: 报告生成完成
    REPORT_READY --> [*]: 审阅结束

    IN_REVIEW --> CANCELLED: 取消审阅
    AI_REVIEWING --> CANCELLED: 取消审核
```

### 4.2 正常路径

```
UPLOADED → PARSING → PARSE_COMPLETE → AI_REVIEWING
  → AI_REVIEW_COMPLETE → IN_REVIEW
    → IP-1 (高风险逐条) → IP-2 (中风险批量) → IP-3 (最终确认)
      → SUBMITTED → REPORT_GENERATING → REPORT_READY
```

### 4.3 异常路径

| 异常场景 | 触发条件 | 状态流转 | 恢复机制 |
|---------|---------|---------|---------|
| **解析失败** | 文件损坏、OCR 不可用 | `PARSING` -> `PARSE_FAILED` | 用户点击重试 -> `PARSING`，Checkpointer 保持已解析的部分数据 |
| **AI 审核失败** | Agent 超时、模型不可用 | `AI_REVIEWING` -> `AI_REVIEW_FAILED` | 用户重试 -> `AI_REVIEWING`，从最近 checkpoint 恢复 |
| **审核超时** | 4 Agent 并行超 5 分钟 | `AI_REVIEWING` -> `AI_REVIEW_FAILED` (error_type: "review_timeout") | 部分成功的 Agent 结果保留，仅重试失败的 Agent |
| **暂停恢复** | 用户在中途点击暂停 | `AI_REVIEWING` -> `PAUSED` | 用户点击恢复 -> `AI_REVIEWING`，从 PAUSED 时的 checkpoint 继续 |
| **审批中断超时** | 用户在 IP-1/IP-2/IP-3 中断后长时间未操作 | 状态保持当前中断点 | `thread_id` 持久化，用户可以随时用相同 config 恢复 |
| **中断后服务重启** | 服务器重启 | 中断状态通过 checkpointer 持久化 | 重启后使用相同 `thread_id` 调用 `graph.stream_events(Command(resume=...), config, version="v3")` 恢复 |
| **部分成功** | 部分 Agent 完成、部分失败 | `AI_REVIEW_COMPLETE` + `error_info.partial = True` | 已完成的结果保留在 RiskFlag 中，前端展示三区面板 |

### 4.4 Checkpointer 在异常恢复中的角色

```
中断发生时:
  interrupt("payload") 被调用
    → GraphInterrupt 异常触发
    → checkpointer.put(checkpoint) 保存当前状态快照
    → 返回给调用方: { __interrupt__: [Interrupt(value=payload, id=...)] }

恢复时:
  Command(resume=data) 被传入
    → checkpointer.get(config) 加载最近 checkpoint
    → 节点从头重执行（包括 interrupt() 之前的代码）
    → interrupt() 返回 resume 值而非再次暂停
    → 继续执行节点剩余逻辑
```

---

## 五、与前端 HITL 操作的映射

### 5.1 8 个前端审批操作到 `Command(resume=...)` 的完整映射

基于 `human_approval_flow.md` 定义的 8 个前端审批操作和 `frontend_backend_boundary_spec-v1.0.md` 的操作归属矩阵，每个操作对应特定的 `Command(resume=...)` 结构：

---

#### 操作 1: approve（同意 AI 标记）

| 维度 | 内容 |
|------|------|
| **描述** | 审核员确认 AI 风险标记准确无误 |
| **适用中断点** | IP-1 (高风险) / IP-2 深入模式 (中风险) / IP-2 低风险抽样 |
| **前端发起** | `POST /risk-flags/{id}/approve` |
| **后端 resume 结构** | 见下方 |
| **后端处理** | 更新 RiskFlag.status → `CONFIRMED` / `REVIEWED_CONFIRMED` / `SPOT_CHECK_CONFIRMED`，写入 ReviewDecision + AuditLog |
| **状态后置** | 高风险: 自动前进到下一条 PENDING_REVIEW 的高风险项；中风险: 返回 IP-2 批量列表 |

```python
# Resume 结构
resume_approve = {
    "interrupt_point": "IP-1",       # 或 "IP-2"
    "flag_id": "rf_001",
    "decision": "approve",
}
```

---

#### 操作 2: edit（编辑修正 AI 标记）

| 维度 | 内容 |
|------|------|
| **描述** | 审核员修改 AI 标记的风险等级、类别或建议措辞 |
| **适用中断点** | IP-1 (高风险) / IP-2 深入模式 (中风险) / IP-2 低风险抽样 |
| **前端发起** | `POST /risk-flags/{id}/edit` |
| **后端 resume 结构** | 见下方 |
| **后端处理** | 更新 RiskFlag.status → `MODIFIED`，记录 modified_fields / original_values / new_values 用于审计 |
| **等级降级处理** | 若修改后风险等级降为中/低 -> 该项移出当前队列；若降为"无风险-驳回" -> 等同于 reject |

```python
resume_edit = {
    "interrupt_point": "IP-1",
    "flag_id": "rf_001",
    "decision": "edit",
    "modified_fields": {
        "risk_level": "中",             # 可选
        "risk_category": "期限不合理",  # 可选
        "suggestion": "..."             # 可选
    },
    "comment": "等级下调为中风险，因为...",  # 必填 >= 10 字符
}
```

---

#### 操作 3: reject（驳回 AI 标记）

| 维度 | 内容 |
|------|------|
| **描述** | 审核员认为 AI 误报，驳回该风险标记 |
| **适用中断点** | IP-1 (高风险) / IP-2 深入模式 (中风险) |
| **前端发起** | `POST /risk-flags/{id}/reject` |
| **后端 resume 结构** | 见下方 |
| **后端处理** | 更新 RiskFlag.status → `REJECTED`，RiskFlag.is_active → `false`，写入驳回原因到 AuditLog |
| **验证** | `comment` 非空白且 >= 10 字符 |

```python
resume_reject = {
    "interrupt_point": "IP-1",
    "flag_id": "rf_001",
    "decision": "reject",
    "comment": "该条款为行业标准表述，在实际司法实践中此类措辞已被广泛接受。",  # >= 10 字符
}
```

---

#### 操作 4: batch（中风险批量确认）

| 维度 | 内容 |
|------|------|
| **描述** | 审核员一键将剩余未审核的中风险项全部标记为自动通过 |
| **适用中断点** | IP-2 |
| **前端发起** | `POST /risk-flags/batch-approve` |
| **后端 resume 结构** | 见下方 |
| **后端处理** | 批量更新所有 PENDING_REVIEW 中风险 RiskFlag.status → `AUTO_APPROVED`，resolution → `UNREVIEWED_AUTO_PASSED` |

```python
resume_batch = {
    "interrupt_point": "IP-2",
    "decision": "batch_confirm",
}
```

---

#### 操作 5: spot-check（低风险抽样审计）

| 维度 | 内容 |
|------|------|
| **描述** | 审核员对低风险抽样项执行审批操作 |
| **适用中断点** | IP-2（如果低风险抽样设计为单独中断）或作为 IP-2 的子模式 |
| **前端发起** | `POST /risk-flags/sample` (获取抽样列表) + 后续 approve/edit/reject |
| **后端 resume 结构** | 见下方 |
| **后端处理** | 低风险抽样使用确定性种子（基于 document_id），保证同文档每次看到相同样本 |
| **抽样参数** | `sample_rate = 0.11` (11%)，`min_samples = 1`，`seed = hash(document_id)` |

```python
resume_spot_check = {
    "interrupt_point": "IP-2",    # 作为 IP-2 的子模式
    "decision": "spot_check",
    "flag_id": "rf_050",
    "sub_decision": "approve",     # approve / edit / reject / skip
    "comment": "",
}
```

---

#### 操作 6: escalate（风险升级）

| 维度 | 内容 |
|------|------|
| **描述** | 审核员在抽样审计中认为 AI 低估了风险，将低/中风险升级为高/中风险 |
| **适用中断点** | IP-2 (作为 approve/edit 的附加操作) |
| **前端发起** | `POST /risk-flags/{id}/escalate` |
| **后端 resume 结构** | 见下方 |
| **后端处理** | 更新 RiskFlag.risk_level → 新等级，escalated → true，escalated_from → 原等级，status 回退为 PENDING_REVIEW |
| **升级不可逆** | 升级后不能降回原自动通过状态，但审核员仍可在高风险审批中执行 approve/edit/reject |

```python
resume_escalate = {
    "interrupt_point": "IP-2",
    "decision": "escalate",
    "flag_id": "rf_055",
    "new_risk_level": "高",          # "高" 或 "中"
    "comment": "该条款虽被AI标记为低风险，但...",
}
```

---

#### 操作 7: manual-add（手动补充标记）

| 维度 | 内容 |
|------|------|
| **描述** | 审核员在阅读原文时发现 AI 遗漏的风险条款，手动创建标记 |
| **适用中断点** | 不在 3 个中断点中，是独立的前端发起的 API 调用 |
| **前端发起** | `POST /risk-flags/manual` |
| **后端处理** | 创建人工来源的 Clause（source="MANUAL"）和 RiskFlag（source="MANUAL"，confidence=None，status="MANUAL_PENDING_CONFIRMATION"） |
| **设计决策** | MVP 单人审核场景手动标记提交后直接生效（`human_approval_flow.md` SS 6.3 的 5 条设计理由） |
| **与中断的关系** | 手动添加独立于 human_review 节点。添加后通过 `update_state()` 将新标记注入 state.risk_flags。若标记为高风险 -> 追加到 IP-1 循环中（节点重入后捕获） |

```python
# manual-add 不通过 resume 处理，而是通过独立的 API 端点
# 后端通过 graph.update_state() 将手动标记注入 state
POST /api/risk-flags/manual
{
    "document_id": "doc_001",
    "clause_text": "接收方不得将保密信息用于本协议目的之外的任何用途。",
    "position_start": 142,
    "position_end": 175,
    "risk_level": "高",
    "risk_category": "用途限制过宽",
    "description": "该条款未明确允许接收方在法规要求下使用保密信息，可能导致合规冲突。"
}
```

---

#### 操作 8: final-submit（最终提交）

| 维度 | 内容 |
|------|------|
| **描述** | 审核员在 IP-3 最终确认页确认提交审阅结果 |
| **适用中断点** | IP-3 |
| **前端发起** | `POST /documents/{id}/submit` |
| **后端 resume 结构** | 见下方 |
| **后端处理** | 双重验证（前端 + 后端）所有高风险处理完毕、至少一次操作 -> 返回 confirm_submit -> 工作流推进到 finalize_report |
| **提交后不可撤销** | 提交后 Document.status → SUBMITTED，报告异步生成 |

```python
resume_submit = {
    "interrupt_point": "IP-3",
    "decision": "confirm_submit",
}
```

### 5.2 Command(resume=...) 映射速查表

| 前端操作 | HTTP 端点 | resume 中的 `decision` 值 | 适用中断点 |
|---------|----------|-------------------------|:--------:|
| approve | `POST /risk-flags/{id}/approve` | `"approve"` | IP-1, IP-2 |
| edit | `POST /risk-flags/{id}/edit` | `"edit"` | IP-1, IP-2 |
| reject | `POST /risk-flags/{id}/reject` | `"reject"` | IP-1, IP-2 |
| batch_approve | `POST /risk-flags/batch-approve` | `"batch_confirm"` | IP-2 |
| spot_check | `POST /risk-flags/sample` + approve/edit/reject | `"spot_check"` | IP-2 |
| escalate | `POST /risk-flags/{id}/escalate` | `"escalate"` | IP-2 |
| manual_add | `POST /risk-flags/manual` | N/A (独立 API) | 无（独立于中断） |
| final_submit | `POST /documents/{id}/submit` | `"confirm_submit"` | IP-3 |
| save_draft | `POST /documents/{id}/save-draft` | `"save_draft"` | IP-3 |
| back_to_review | (IP-3 页面按钮) | `"back_to_review"` | IP-3 |

### 5.3 中断-前端交互完整流程图

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                          HITL 中断与前端交互全流程                              │
│                                                                              │
│  后端 (LangGraph)                              前端 (React/Vue)              │
│  ──────────────                               ────────────────               │
│                                                                              │
│  graph.stream_events(input, config, v3) ──────▶ SSE: review.progress         │
│       │                                                                      │
│       │  agent 节点执行到 human_review                                       │
│       │  interrupt(payload) 被调用                                           │
│       │                                                                      │
│       ▼                                                                      │
│  stream.interrupted == True ──────────────────▶ SSE: review.interrupt        │
│  stream.interrupts = [Interrupt(value=payload)]    │                         │
│       │                                            │                         │
│       │  (暂停等待)                                 ▼                         │
│       │                                    渲染审批卡片 (IP-1 / IP-2 / IP-3) │
│       │                                            │                         │
│       │                                    用户执行审批操作                    │
│       │                                    (approve / edit / reject / ...)    │
│       │                                            │                         │
│       │                                    POST /api/risk-flags/{id}/approve  │
│       │                                            │                         │
│       │                                    构建 resume_data                   │
│       │                                            │                         │
│       │  ◀───────────────────  graph.stream_events(                          │
│       │                           Command(resume=resume_data),               │
│       │                           config, version="v3")                      │
│       │                                                                      │
│       │  interrupt() 返回 resume_data                                        │
│       │  继续执行节点逻辑                                                      │
│       │  更新 RiskFlag + ReviewDecision + AuditLog                            │
│       │                                                                      │
│       │  下一个 interrupt() 或节点完成                                        │
│       │                                                                      │
│       ▼                                                                      │
│  stream.interrupted == False ────────────────▶ SSE: review.complete          │
│  stream.output == final_state                                                │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 六、Checkpointer 配置

### 6.1 各环境配置策略

基于 LangGraph 官方 Checkpointer 层级：

| 环境 | Checkpointer | 类路径 | 持久性 | 适用场景 |
|------|------------|--------|:----:|---------|
| **开发/测试** | `InMemorySaver` | `langgraph.checkpoint.memory.InMemorySaver()` | 进程内（重启丢失） | 本地开发、单元测试、快速原型 |
| **本地持久化** | `SqliteSaver` / `AsyncSqliteSaver` | `langgraph.checkpoint.sqlite.SqliteSaver` | 文件系统 | 本地持久化开发、小型部署 |
| **生产 (PostgreSQL)** | `AsyncPostgresSaver` | `langgraph.checkpoint.postgres.aio.AsyncPostgresSaver.from_conn_string(DB_URI)` | 数据库 | 生产环境推荐（与团队现有 PostgreSQL 基础设施一致） |
| **生产 (MongoDB)** | `AsyncMongoDBSaver` | `langgraph.checkpoint.mongodb.aio.AsyncMongoDBSaver.from_conn_string(MONGODB_URI)` | 数据库 | 高吞吐场景、MongoDB 已存在的基础设施 |

### 6.2 MVP 阶段配置

```python
# MVP 阶段配置：开发用 InMemorySaver，生产用 AsyncPostgresSaver
import os
from langgraph.checkpoint.memory import InMemorySaver

def _get_checkpointer():
    """根据环境变量选择 checkpointer。"""
    env = os.getenv("APP_ENV", "development")

    if env == "development":
        return InMemorySaver()

    elif env == "production":
        from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
        DB_URI = os.getenv("DATABASE_URI",
                           "postgresql://postgres:postgres@localhost:5432/langgraph?sslmode=disable")
        checkpointer = AsyncPostgresSaver.from_conn_string(DB_URI)
        # 首次使用需调用 await checkpointer.setup() 创建表
        return checkpointer

    else:
        raise ValueError(f"Unknown APP_ENV: {env}")

# 编译时注入
checkpointer = _get_checkpointer()
compiled_graph = graph.compile(checkpointer=checkpointer)
```

### 6.3 Checkpoint 的创建时机与恢复流程

#### 创建时机

LangGraph 在以下时机自动创建 checkpoint：

| 时机 | 触发条件 | Checkpoint 内容 |
|------|---------|---------------|
| **Super-Step 结束** | 每个节点（或并行节点组）执行完成，返回状态更新后 | 完整的 state 快照 + 待执行的下一节点列表 |
| **中断触发** | `interrupt()` 被调用时 | 当前 state + 中断元数据（Interrupt.id 和 Interrupt.value） |
| **节点失败** | 节点抛出异常时（如果其他同 super-step 节点成功） | 成功节点的 pending writes + 失败节点的错误信息 |

#### 恢复流程

```python
# 完整的中断-恢复流程示例
from langgraph.types import Command

def run_and_resume(document_input: dict, thread_id: str):
    """
    完整的中断->恢复流程示例。

    展示如何使用 stream_events + Command(resume=...) 实现
    前端交互式的 HITL 工作流。
    """
    config = {"configurable": {"thread_id": thread_id}}

    stream_input = document_input  # 初始输入: dict

    while True:
        # 使用 stream_events(version="v3") 驱动图形执行
        # stream.messages 提供 LLM token 流
        # stream.values 提供状态快照
        # stream.interrupted 指示是否暂停等待输入
        stream = compiled_graph.stream_events(
            stream_input,
            config=config,
            version="v3",
        )

        # 驱动流到完成或中断
        _ = stream.output  # 阻塞直到 graph 完成或中断

        if not stream.interrupted:
            # 工作流完成，返回最终状态
            return stream.output

        # 中断发生：提取 payload(s) 传给前端
        # stream.interrupts 是 tuple[Interrupt, ...]
        for interrupt_item in stream.interrupts:
            interrupt_id = interrupt_item.id
            payload = interrupt_item.value

            # 前端根据 payload.interrupt_point 渲染对应 UI
            # 用户完成审批操作后，前端构建 resume_data

        # 模拟：等待前端返回的 resume_data
        # 单中断：stream_input = Command(resume=resume_data)
        # 多中断：stream_input = Command(resume={interrupt_id: value, ...})
        resume_data = wait_for_frontend_response(stream.interrupts)
        stream_input = Command(resume=resume_data)

        # 循环继续：graph 从中断点恢复执行


def wait_for_frontend_response(interrupts: tuple) -> dict:
    """
    模拟前端交互等待。

    在生产环境中，此处为 HTTP 端点接收前端提交的 resume 数据。
    """
    # 实际实现：返回通过 API 接收到的前端决策
    pass
```

#### 中断后的状态检查

```python
# 使用 get_state() 检查当前状态而不恢复执行
def check_interrupt_status(thread_id: str) -> dict:
    """在恢复之前检查当前中断状态。"""
    config = {"configurable": {"thread_id": thread_id}}

    state = compiled_graph.get_state(config)

    # state.values: 当前 state 快照
    # state.next: 待执行的节点列表（中断时为空，因为当前 human_review 节点未完成）
    # state.metadata: 包含 checkpoint 元数据

    return {
        "current_stage": state.values.get("current_stage"),
        "doc_status": state.values.get("doc_status"),
        "pending_high_risk": [
            f for f in state.values.get("risk_flags", [])
            if f["risk_level"] == "高" and f.get("status") == "PENDING_REVIEW"
        ],
        "next_nodes": state.next,  # 中断时为 empty tuple
        "checkpoint_id": state.config["configurable"].get("checkpoint_id"),
    }
```

### 6.4 Checkpointer 与并发安全

```python
# 并发安全说明：
# 1. thread_id 隔离：不同文档审阅使用不同的 thread_id，checkpoint 天然隔离
#    thread_id = f"doc-review-{document_id}"
#
# 2. 同一文档的并发访问：
#    - LangGraph checkpointer 在执行期间持有 checkpoint 写锁
#    - 若两个请求同时尝试对同一 thread_id 执行 invoke，后者会收到冲突错误
#    - 前端实现：同一审批页面全局锁（RiskFlag.locked_by + locked_at，2 分钟超时）
#
# 3. 多人协同 (v2)：
#    - 使用分片 thread_id：主审 thread_id，复核 thread_id
#    - 或使用 sub-graph 隔离每个审核员的审批操作
```

### 6.5 Agent 级别的 HITL vs 自定义 StateGraph 级别的 HITL

本设计选择**自定义 StateGraph 级别的 HITL**（而非 Agent 级别的 `HumanInTheLoopMiddleware`），原因如下：

| 维度 | `HumanInTheLoopMiddleware` (Agent 级) | 自定义 `interrupt()` (StateGraph 级) |
|------|--------------------------------------|-------------------------------------|
| **控制粒度** | 工具调用级别（在每个 tool call 前中断） | 业务逻辑级别（在工作流节点中任意位置中断） |
| **中断 payload** | 标准化格式（action_requests + review_configs） | 完全自定义（任意 JSON-serializable 结构） |
| **决策类型** | `approve` / `edit` / `reject` / `respond`（固定 4 种） | 自定义决策类型（本设计的 8 种操作） |
| **适用场景** | 单个 Agent 的工具调用审批 | 多节点工作流的复杂业务中断 |
| **本系统适用性** | 可用于 Agent 内部工具调用的二次确认（如报告 Agent 的"确认导出"工具） | 主工作流的中断点（IP-1/IP-2/IP-3） |

**混合使用策略**：本设计的主工作流使用自定义 `interrupt()` (StateGraph 级)，但在以下场景可叠加 `HumanInTheLoopMiddleware`：

```python
# 示例：报告 Agent 在导出 PDF 前需要用户确认
report_agent = create_agent(
    model="claude-sonnet-4-6",
    tools=[export_pdf_tool, sign_report_tool],
    middleware=[
        HumanInTheLoopMiddleware(
            interrupt_on={
                "export_pdf": True,  # 所有决策类型允许
                "sign_report": {
                    "allowed_decisions": ["approve", "reject"],
                    "description": "签名操作为最终操作，不可编辑"
                },
                "read_data": False,  # 只读操作不中断
            },
        ),
    ],
    checkpointer=InMemorySaver(),
)
```

---

## 附录 A: 上游文档衔接点验证

| 上游文档 | 关键约束 | 本设计对应位置 |
|---------|---------|-------------|
| `business_model.md` SS 4.1 分级告警 | 高风险 100% 强制 / 中风险批量可选 / 低风险自动 + 抽样 | SS 三 IP-1/IP-2/IP-3 设计 |
| `business_model.md` SS 4.1 HITL 约束 | interrupt 不可跳过 | SS 三.5 IP-3 提交前验证 + API 409 |
| `business_model.md` SS 4.3 实体 | Document, Clause, RiskFlag, ReviewDecision, PlaybookRule, AuditLog, ReviewReport | SS 二 State 类型定义 |
| `business_model.md` SS 5.1 MVP 范围 | 仅 NDA + PDF/DOCX | SS 一.3 节点设计中的 doc_format 字段 |
| `flow_state_spec.md` SS 2.2 三阶段 | 上传解析 -> AI 审核 -> 人工审批 | SS 一.3 7 个节点对应 3 阶段 |
| `flow_state_spec.md` SS 4 交互图 | 阶段 2 到阶段 3 的状态流转 | SS 四 stateDiagram-v2 |
| `human_approval_flow.md` SS 九 | 11 条关键交互约束 | SS 三 每个中断点的 constraints 字段 |
| `human_approval_flow.md` SS 三-七 | 8 个审批操作 | SS 五 8 操作到 Command(resume=...) 映射 |
| `frontend_backend_boundary_spec-v1.0.md` SS 二.3 | 8 操作前后端边界 | SS 五.1 每个操作的"前端发起"映射 |
| `frontend_backend_boundary_spec-v1.0.md` SS 四 | SSE 通信模式 | SS 三.6 SSE 事件类型映射 |

---

## 附录 B: API 签名来源速查

| API 符号 | 完整导入路径 | 官方文档链接 |
|---------|------------|------------|
| `interrupt` | `from langgraph.types import interrupt` | https://reference.langchain.com/python/langgraph/types/interrupt |
| `Command` | `from langgraph.types import Command` | https://reference.langchain.com/python/langgraph/types/Command |
| `Interrupt` | `from langgraph.types import Interrupt` | https://reference.langchain.com/python/langgraph/types/Interrupt |
| `InMemorySaver` | `from langgraph.checkpoint.memory import InMemorySaver` | https://reference.langchain.com/python/langgraph/checkpoints |
| `AsyncPostgresSaver` | `from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver` | https://reference.langchain.com/python/langgraph/checkpoints |
| `StateGraph` | `from langgraph.graph import StateGraph` | https://docs.langchain.com/oss/python/langgraph/use-graph-api |
| `create_agent` | `from langchain.agents import create_agent` | https://reference.langchain.com/python/langchain/agents/factory/create_agent |
| `HumanInTheLoopMiddleware` | `from langchain.agents.middleware import HumanInTheLoopMiddleware` | https://reference.langchain.com/python/langchain/agents/middleware/human_in_the_loop/HumanInTheLoopMiddleware |
| `InterruptOnConfig` | `from langchain.agents.middleware import InterruptOnConfig` | https://reference.langchain.com/python/langchain/agents/middleware/human_in_the_loop/InterruptOnConfig |
| `AgentState` | `from langchain.agents.middleware.types import AgentState` | https://reference.langchain.com/python/langchain/agents/middleware/types/AgentState |

---

> **上游文档**:
> - `../03_business_modeling/business_model.md` -- 业务问题建模
> - `../04_interaction_design/flow_state_spec.md` -- 状态流转规范
> - `../04_interaction_design/human_approval_flow.md` -- 人工审批交互链路
> - `./frontend_backend_boundary_spec-v1.0.md` -- 前后端边界规范
> **下游文档**:
> - `../07_data_model/` -- 数据模型设计
> - `../08_api_specification/` -- API 规范
> - `../10_backend_plan/` -- 后端实现计划
> **MCP 查询来源**:
> - `docs-langchain` MCP: `search_docs_by_lang_chain` + `query_docs_filesystem_docs_by_lang_chain`
> - `reference-langchain` MCP: `search_api` + `get_symbol`
> - 所有 API 签名均来自以上 MCP 工具的真实查询结果，非编造
