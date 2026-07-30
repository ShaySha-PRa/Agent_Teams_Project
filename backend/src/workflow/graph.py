"""
7+2 节点 LangGraph StateGraph -- 文档审核核心工作流 (HITL 分节点版)。

对齐: langchain_hitl_arch-v1.0.md sections 四 / 五 / 六
拓扑:
  parse_document -> extract_clauses -> risk_analysis || compliance_check
                                       |                  |
                                       +--- generate_report_draft ---+
                                                                      |
                                                               human_review_router  (路由)
                                                                  /    |     \
                                                   human_review_ip1   ip2    ip3  (3 中断子节点)
                                                        |             |      |
                                                        +--- loop ----+      |
                                                                              |
                                                 confirm_submit -> finalize_report -> END
                                                 save_draft / back_to_review -> human_review_router

关键设计决策: 每个 interrupt() 独占一个节点, 利用 LangGraph super-step
checkpoint 边界天然避免 re-execution 导致的重复决策问题。
"""

from __future__ import annotations

import logging
import os
from typing import Any, Literal

from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import interrupt, Command
from langchain_openai import ChatOpenAI

try:
    from agents.clause_extraction import run_clause_extraction
    from agents.risk_control import run_risk_analysis
    from agents.compliance import run_compliance_check
    from agents.report import run_report_generation
except ImportError:
    from src.agents.clause_extraction import run_clause_extraction
    from src.agents.risk_control import run_risk_analysis
    from src.agents.compliance import run_compliance_check
    from src.agents.report import run_report_generation
from .state import DocumentReviewState

logger = logging.getLogger(__name__)

# ===================================================================
# 模型工厂
# ===================================================================

def create_model() -> ChatOpenAI:
    """创建 DeepSeek 模型实例 (通过 ChatOpenAI 兼容方式接入)。"""
    api_key = os.getenv("DEEPSEEK_API_KEY", "")
    return ChatOpenAI(
        model="deepseek-chat",
        base_url="https://api.deepseek.com/v1",
        api_key=api_key,
        temperature=0.1,
        max_tokens=4096,
    )


# ===================================================================
# 节点 1: parse_document
# ===================================================================

async def node_parse_document(
    state: DocumentReviewState,
) -> dict[str, Any]:
    """阶段 1: 文档解析 -- 初始化文档元数据。"""
    logger.info(
        f"[parse_document] 开始: {state.get('document_id', 'N/A')}"
    )
    doc_metadata = state.get("doc_metadata", {})
    doc_text = doc_metadata.get("full_text", "")

    if not doc_text:
        return {
            "doc_status": "FAILED",
            "error_info": {
                "error_type": "parse_failed",
                "error_message": "文档文本为空，无法进行后续分析",
                "recoverable": False,
            },
        }
    return {"doc_status": "PARSING", "clauses": []}


# ===================================================================
# 节点 2: extract_clauses
# ===================================================================

async def node_extract_clauses(
    state: DocumentReviewState,
) -> dict[str, Any]:
    """阶段 1: 条款提取 -- 调用 Clause Extraction Agent。"""
    logger.info(
        f"[extract_clauses] 开始条款提取: "
        f"{state.get('document_id', 'N/A')}"
    )
    model = create_model()
    result = await run_clause_extraction(state, model)

    clauses = result.get("clauses", [])
    error = result.get("error_info")

    if error:
        return {
            "doc_status": "FAILED",
            "clauses": clauses,
            "error_info": error,
        }

    logger.info(f"[extract_clauses] 提取完成: {len(clauses)} 条条款")
    return {"doc_status": "PARSED", "clauses": clauses}


# ===================================================================
# 节点 3: risk_analysis (并行)
# ===================================================================

async def node_risk_analysis(
    state: DocumentReviewState,
) -> dict[str, Any]:
    """阶段 2: 风险分析 -- 调用 Risk Control Agent。"""
    logger.info(
        f"[risk_analysis] 开始: {state.get('document_id', 'N/A')}"
    )
    model = create_model()
    result = await run_risk_analysis(state, model)
    risk_flags = result.get("risk_flags", [])
    error = result.get("error_info")

    logger.info(
        f"[risk_analysis] 完成: {len(risk_flags)} 条风险标记"
    )

    output: dict[str, Any] = {
        "doc_status": "REVIEWING",
        "risk_flags": risk_flags,
    }
    if error:
        output["error_info"] = error
    return output


# ===================================================================
# 节点 4: compliance_check (并行)
# ===================================================================

async def node_compliance_check(
    state: DocumentReviewState,
) -> dict[str, Any]:
    """阶段 2: 合规检查 -- 调用 Compliance Agent。"""
    logger.info(
        f"[compliance_check] 开始: {state.get('document_id', 'N/A')}"
    )
    model = create_model()
    result = await run_compliance_check(state, model)
    compliance_results = result.get("compliance_results", [])
    risk_flags = result.get("risk_flags", [])
    error = result.get("error_info")

    logger.info(
        f"[compliance_check] 完成: {len(compliance_results)} 条合规结果, "
        f"{len(risk_flags)} 条合规风险"
    )

    output: dict[str, Any] = {
        "compliance_results": compliance_results,
        "risk_flags": risk_flags,
    }
    if error:
        output["error_info"] = error
    return output


# ===================================================================
# 节点 5: generate_report_draft
# ===================================================================

async def node_generate_report_draft(
    state: DocumentReviewState,
) -> dict[str, Any]:
    """阶段 2: 报告草稿生成 -- 调用 Report Agent。"""
    logger.info(
        f"[generate_report_draft] 开始: {state.get('document_id', 'N/A')}"
    )
    model = create_model()
    result = await run_report_generation(state, model)
    report_draft = result.get("report_draft", {})

    logger.info(
        f"[generate_report_draft] 完成: {report_draft.get('report_id', 'N/A')}"
    )
    return {"doc_status": "REVIEWED", "report_draft": report_draft}


# ===================================================================
# HITL 子节点: 路由 + IP-1 + IP-2 + IP-3 (分节点架构，避免 re-execution 重复)
# ===================================================================

# -------------------------------------------------------------------
# 路由节点
# -------------------------------------------------------------------

async def node_human_review_router(
    state: DocumentReviewState,
) -> dict[str, Any]:
    """
    HITL 路由节点 -- 无业务逻辑, 仅提供 routing 给 StateGraph 条件边使用。
    每次从本节点出发, 根据当前 risk_flags 状态决定下一个中断点。
    """
    return {"interrupt_state": "waiting"}


def _route_human_review(
    state: DocumentReviewState,
) -> Literal["human_review_ip1", "human_review_ip2", "human_review_ip3"]:
    """
    条件路由: 优先级 IP-1 (有高风险待审批) > IP-2 (有中风险待处理) > IP-3 (最终确认)。

    LangGraph 在每次进入此函数时读取最新的 checkpoint 状态,
    因此 IP-1 每完成一个标志就返回 router, 由 router 再次检查是否有下一个待审批项。
    """
    risk_flags = state.get("risk_flags", [])

    # 检查是否有高风险待审批
    pending_high = [
        f for f in risk_flags
        if f.get("risk_level") == "HIGH" and f.get("status") == "PENDING_REVIEW"
    ]
    if pending_high:
        return "human_review_ip1"

    # 检查是否有中风险待处理 (尚未批量确认)
    pending_medium = [
        f for f in risk_flags
        if f.get("risk_level") == "MEDIUM"
        and f.get("status") not in ("UNREVIEWED_AUTO_PASSED", "AMENDED", "REJECTED", "REVIEWED_CONFIRMED")
    ]
    if pending_medium:
        return "human_review_ip2"

    return "human_review_ip3"


# -------------------------------------------------------------------
# IP-1: 高风险逐条审批 (每次只处理一条, 利用 checkpoint 边界)
# -------------------------------------------------------------------

async def node_human_review_ip1(
    state: DocumentReviewState,
) -> dict[str, Any]:
    """
    IP-1: 高风险条款逐条审批 (单条/次, 不可跳过)。

    每次只处理第一条 PENDING_REVIEW 高风险标志。
    节点返回后, 经 checkpoint 持久化, 再由 router 检查是否还有剩余的高风险项。
    若有则再次进入 IP-1; 若无则进入 IP-2。
    """
    document_id = state.get("document_id", "N/A")
    risk_flags = state.get("risk_flags", [])
    review_decisions = state.get("review_decisions", [])
    clauses = state.get("clauses", [])

    # 取第一条待审批的高风险标志
    pending_high = [
        f for f in risk_flags
        if f.get("risk_level") == "HIGH" and f.get("status") == "PENDING_REVIEW"
    ]
    if not pending_high:
        # 防御: 如果已经没有待审批的, 直接透传
        return {}

    flag = pending_high[0]

    # 构建 clause_context
    clause_context = {}
    for c in clauses:
        if c.get("clause_id") == flag.get("clause_id"):
            clause_context = {
                "clause_type": c.get("clause_type", ""),
                "clause_text": c.get("clause_text", ""),
                "page_number": c.get("page_number", 1),
            }
            break

    high_total = len([
        f for f in risk_flags
        if f.get("risk_level") == "HIGH" and f.get("status") == "PENDING_REVIEW"
    ])

    payload = {
        "interrupt_type": "HIGH_RISK_APPROVAL",
        "interrupt_point": "IP-1",
        "risk_flag": {
            "risk_flag_id": flag.get("risk_flag_id"),
            "clause_id": flag.get("clause_id"),
            "risk_level": flag.get("risk_level"),
            "risk_category": flag.get("risk_category"),
            "ai_confidence": flag.get("ai_confidence"),
            "rationale_text": flag.get("rationale_text", ""),
            "suggestion": flag.get("suggested_wording", ""),
            "playbook_diff": flag.get("playbook_diff_text", ""),
        },
        "clause_context": clause_context,
        "review_progress": {
            "current_index": 1,
            "total_high_risk": high_total,
            "remaining": high_total - 1,
        },
        "allowed_decisions": ["approve", "edit", "reject"],
    }

    logger.info(
        f"[IP-1] 触发高风险审批: {flag.get('risk_flag_id')} "
        f"({flag.get('risk_category', 'N/A')})"
    )

    # [中断 IP-1] -- 此节点仅此一个 interrupt()
    resume_data = interrupt(payload)

    # [恢复 IP-1] -- 节点从 checkpoint 恢复后从此处继续
    decision = resume_data.get("decision", "")
    flag_id = resume_data.get("risk_flag_id", flag.get("risk_flag_id"))

    # 构建决策记录
    decision_record = {
        "decision_id": f"dec_{flag_id}",
        "risk_flag_id": flag_id,
        "decision_type": decision.upper(),
        "reviewer_id": resume_data.get("reviewer_id", "human"),
        "comment": resume_data.get("comment", ""),
        "modified_fields": resume_data.get("modified_fields"),
        "original_values": {
            "risk_level": flag.get("risk_level"),
            "risk_category": flag.get("risk_category"),
            "suggested_wording": flag.get("suggested_wording"),
        },
        "timestamp": "",
    }

    # 更新当前 flag 状态
    if decision == "approve":
        flag["status"] = "CONFIRMED"
    elif decision == "edit":
        flag["status"] = "AMENDED"
        if resume_data.get("modified_fields"):
            for k, v in resume_data["modified_fields"].items():
                if k in flag:
                    flag[k] = v
    elif decision == "reject":
        flag["status"] = "REJECTED"

    return {
        "risk_flags": risk_flags,
        "review_decisions": review_decisions + [decision_record],
        "interrupt_state": "resolved",
    }


# -------------------------------------------------------------------
# IP-2: 中风险批量审批
# -------------------------------------------------------------------

async def node_human_review_ip2(
    state: DocumentReviewState,
) -> dict[str, Any]:
    """
    IP-2: 中风险批量审批 (可批量确认或逐条 deep_dive)。

    所有待处理的中风险项一次性呈现, 用户可选择 batch_confirm 或 deep_dive。
    """
    risk_flags = state.get("risk_flags", [])
    review_decisions = state.get("review_decisions", [])

    medium_risk_pending = [
        f for f in risk_flags
        if f.get("risk_level") == "MEDIUM"
        and f.get("status") not in (
            "UNREVIEWED_AUTO_PASSED", "AMENDED", "REJECTED", "REVIEWED_CONFIRMED"
        )
    ]

    if not medium_risk_pending:
        return {}

    logger.info(
        f"[IP-2] 中风险批量审批: {len(medium_risk_pending)} 条"
    )

    batch_payload = {
        "interrupt_type": "MEDIUM_RISK_BATCH_APPROVAL",
        "interrupt_point": "IP-2",
        "summary": {
            "total_medium_risk": len(medium_risk_pending),
            "default_action": "auto_pass",
        },
        "items": [
            {
                "risk_flag_id": f.get("risk_flag_id"),
                "clause_id": f.get("clause_id"),
                "risk_category": f.get("risk_category"),
                "ai_confidence": f.get("ai_confidence"),
                "status": f.get("status"),
            }
            for f in medium_risk_pending
        ],
        "allowed_decisions": ["batch_confirm", "deep_dive"],
    }

    # [中断 IP-2]
    resume_data = interrupt(batch_payload)

    # [恢复 IP-2]
    decision = resume_data.get("decision", "")

    if decision == "batch_confirm":
        for f in medium_risk_pending:
            f["status"] = "UNREVIEWED_AUTO_PASSED"

        batch_decision = {
            "decision_id": f"dec_batch_{len(review_decisions)}",
            "risk_flag_id": "batch",
            "decision_type": "BATCH_CONFIRM",
            "reviewer_id": resume_data.get("reviewer_id", "human"),
            "comment": "中风险批量确认",
            "timestamp": "",
        }
        return {
            "risk_flags": risk_flags,
            "review_decisions": review_decisions + [batch_decision],
            "interrupt_state": "resolved",
        }

    elif decision == "deep_dive":
        flag_id = resume_data.get("risk_flag_id", "")
        sub_decision = resume_data.get("sub_decision", "")

        target_flag = None
        for f in medium_risk_pending:
            if f.get("risk_flag_id") == flag_id:
                target_flag = f
                break

        if target_flag:
            dive_decision = {
                "decision_id": f"dec_{flag_id}_{len(review_decisions)}",
                "risk_flag_id": flag_id,
                "decision_type": sub_decision.upper(),
                "reviewer_id": resume_data.get("reviewer_id", "human"),
                "comment": resume_data.get("comment", ""),
                "modified_fields": resume_data.get("modified_fields"),
                "original_values": {
                    "risk_level": target_flag.get("risk_level"),
                    "risk_category": target_flag.get("risk_category"),
                },
                "timestamp": "",
            }

            if sub_decision == "approve":
                target_flag["status"] = "REVIEWED_CONFIRMED"
            elif sub_decision == "edit":
                target_flag["status"] = "AMENDED"
                if resume_data.get("modified_fields"):
                    for k, v in resume_data["modified_fields"].items():
                        if k in target_flag:
                            target_flag[k] = v
            elif sub_decision == "reject":
                target_flag["status"] = "REJECTED"
            elif sub_decision == "escalate":
                target_flag["risk_level"] = "HIGH"
                target_flag["status"] = "PENDING_REVIEW"
                target_flag["escalated"] = True
                target_flag["escalated_from"] = "MEDIUM"

            return {
                "risk_flags": risk_flags,
                "review_decisions": review_decisions + [dive_decision],
                "interrupt_state": "resolved",
            }

    # 未知决策: 透传
    return {}


# -------------------------------------------------------------------
# IP-3: 最终确认
# -------------------------------------------------------------------

async def node_human_review_ip3(
    state: DocumentReviewState,
) -> dict[str, Any]:
    """
    IP-3: 最终确认 (不可跳过)。

    汇总所有风险处理结果, 要求用户确认提交、保存草稿或返回继续审阅。
    """
    risk_flags = state.get("risk_flags", [])
    report_draft = state.get("report_draft", {})

    def _count(level: str, status: str) -> int:
        return len([
            f for f in risk_flags
            if f.get("risk_level") == level and f.get("status") == status
        ])

    high_total = len([f for f in risk_flags if f.get("risk_level") == "HIGH"])
    high_pending = _count("HIGH", "PENDING_REVIEW")

    confirmation_payload = {
        "interrupt_type": "FINAL_REVIEW_CONFIRMATION",
        "interrupt_point": "IP-3",
        "precondition_check": {
            "all_high_risk_resolved": high_pending == 0,
        },
        "summary": {
            "high_risk": {
                "total": high_total,
                "confirmed": _count("HIGH", "CONFIRMED"),
                "amended": _count("HIGH", "AMENDED"),
                "rejected": _count("HIGH", "REJECTED"),
                "pending": high_pending,
            },
            "report_draft": report_draft,
        },
        "allowed_decisions": ["confirm_submit", "save_draft", "back_to_review"],
    }

    logger.info(
        f"[IP-3] 最终确认: 高风险 {high_total} 条, "
        f"待审批 {high_pending} 条"
    )

    # [中断 IP-3]
    resume_data = interrupt(confirmation_payload)

    # [恢复 IP-3]
    decision = resume_data.get("decision", "")

    if decision == "confirm_submit":
        return {"doc_status": "COMPLETED", "interrupt_state": "resolved"}
    elif decision == "save_draft":
        return {"doc_status": "HUMAN_REVIEW", "interrupt_state": "waiting"}
    elif decision == "back_to_review":
        return {"doc_status": "HUMAN_REVIEW", "interrupt_state": "waiting"}

    # 防御: 拒绝未知决策
    raise ValueError(
        f"IP-3 收到未知决策类型: '{decision}'。"
        f"允许值: confirm_submit, save_draft, back_to_review"
    )


def _route_after_ip3(
    state: DocumentReviewState,
) -> Literal["finalize_report", "human_review_router"]:
    """IP-3 决策路由: confirm_submit -> finalize_report; 其他 -> router。"""
    doc_status = state.get("doc_status", "")
    if doc_status == "COMPLETED":
        return "finalize_report"
    return "human_review_router"


# ===================================================================
# 节点 7: finalize_report
# ===================================================================

async def node_finalize_report(
    state: DocumentReviewState,
) -> dict[str, Any]:
    """
    阶段 3: 最终报告生成 -- 合并人工裁定, 仅当 IP-3 确认提交后执行。
    """
    logger.info(
        f"[finalize_report] 生成最终报告: {state.get('document_id', 'N/A')}"
    )

    report_draft = state.get("report_draft", {})
    review_decisions = state.get("review_decisions", [])
    risk_flags = state.get("risk_flags", [])

    final_risk_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for flag in risk_flags:
        level = flag.get("risk_level", "LOW")
        final_risk_counts[level] = final_risk_counts.get(level, 0) + 1

    final_report = {
        **report_draft,
        "final_status": "COMPLETED",
        "final_risk_counts": final_risk_counts,
        "total_decisions": len(review_decisions),
        "approve_count": len([
            d for d in review_decisions
            if d.get("decision_type") in ("APPROVE", "BATCH_CONFIRM")
        ]),
        "edit_count": len([
            d for d in review_decisions
            if d.get("decision_type") == "EDIT"
        ]),
        "reject_count": len([
            d for d in review_decisions
            if d.get("decision_type") == "REJECT"
        ]),
    }

    return {"doc_status": "COMPLETED", "report_draft": final_report}


# ===================================================================
# 构建 StateGraph
# ===================================================================

def build_graph() -> StateGraph:
    """构建 7 业务节点 + 1 路由节点 StateGraph (含 HITL 分节点架构)。"""
    builder = StateGraph(DocumentReviewState)

    # -- 5 个阶段1-2 节点 --
    builder.add_node("parse_document", node_parse_document)
    builder.add_node("extract_clauses", node_extract_clauses)
    builder.add_node("risk_analysis", node_risk_analysis)
    builder.add_node("compliance_check", node_compliance_check)
    builder.add_node("generate_report_draft", node_generate_report_draft)

    # -- HITL 子节点 (路由器 + 3 中断节点) --
    builder.add_node("human_review_router", node_human_review_router)
    builder.add_node("human_review_ip1", node_human_review_ip1)
    builder.add_node("human_review_ip2", node_human_review_ip2)
    builder.add_node("human_review_ip3", node_human_review_ip3)

    # -- 收尾节点 --
    builder.add_node("finalize_report", node_finalize_report)

    # ---- 主路径 ----
    builder.add_edge(START, "parse_document")
    builder.add_edge("parse_document", "extract_clauses")

    # 条件: 提取失败 (不可恢复) -> END
    builder.add_conditional_edges(
        "extract_clauses",
        _route_after_extraction,
        ["risk_analysis", "compliance_check", END],
    )

    # 并行 fan-in
    builder.add_edge("risk_analysis", "generate_report_draft")
    builder.add_edge("compliance_check", "generate_report_draft")

    # 进入 HITL 路由
    builder.add_edge("generate_report_draft", "human_review_router")

    # ---- HITL 条件路由 (router -> ip1/ip2/ip3) ----
    builder.add_conditional_edges(
        "human_review_router",
        _route_human_review,
        ["human_review_ip1", "human_review_ip2", "human_review_ip3"],
    )

    # ---- IP-1: 完成后回到 router 检查是否需要继续 ----
    builder.add_edge("human_review_ip1", "human_review_router")

    # ---- IP-2: 完成后进入 IP-3 ----
    builder.add_edge("human_review_ip2", "human_review_ip3")

    # ---- IP-3: 条件路由 (confirm_submit -> finalize; 其他 -> router) ----
    builder.add_conditional_edges(
        "human_review_ip3",
        _route_after_ip3,
        ["finalize_report", "human_review_router"],
    )

    # ---- 收尾 ----
    builder.add_edge("finalize_report", END)

    return builder


# ---- 条件路由辅助函数 ----

def _route_after_extraction(
    state: DocumentReviewState,
) -> str | tuple[str, ...]:
    """条件路由: 不可恢复错误 -> END, 成功 -> fan-out 并行。"""
    error = state.get("error_info")
    if error and not error.get("recoverable", False):
        logger.warning(
            f"[route] extract_clauses 不可恢复错误: "
            f"{error.get('error_message')}"
        )
        return END
    return ("risk_analysis", "compliance_check")


def compile_graph(
    checkpointer: InMemorySaver | None = None,
) -> Any:
    """编译 StateGraph 并注入 Checkpointer。"""
    if checkpointer is None:
        checkpointer = InMemorySaver()
    builder = build_graph()
    return builder.compile(checkpointer=checkpointer)
