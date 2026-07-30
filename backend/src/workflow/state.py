"""
DocumentReviewState TypedDict + sub-types + custom reducers.

对齐: langchain_hitl_arch-v1.0.md §4.2
MVP: clauses (Annotated + operator.add)、risk_flags (merge_risk_flags reducer)、
      review_decisions (operator.add)
"""

from typing import Annotated, Any, Optional, TypedDict
import operator


# ─────────────────────────────────────────────────────────────────
# 子类型定义
# ─────────────────────────────────────────────────────────────────

class ClauseDict(TypedDict, total=False):
    """条款字典 — NDA 10 类条款"""
    clause_id: str
    clause_type: str                    # 保密义务 / 保密期限 / 例外情形 / 违约救济 /
                                        # 存续条款 / 管辖法律 / 争议解决 / 通知条款 /
                                        # 可转让性 / 完整协议
    clause_text: str                    # 原文字段
    extraction_confidence: float        # 0.0 - 1.0
    page_number: int
    paragraph_number: int
    char_offset_start: int
    char_offset_end: int
    text_hash: str
    source: str                         # "AI" / "MANUAL"


class RiskFlagDict(TypedDict, total=False):
    """风险标记字典 — AI 对条款的风险判定"""
    risk_flag_id: str
    clause_id: str
    document_id: str
    risk_level: str                     # "HIGH" / "MEDIUM" / "LOW"
    risk_category: str                  # 合规风险 / 财务风险 / 法律风险 / ...
    ai_confidence: float                # 0.0 - 1.0
    status: str                         # PENDING_REVIEW / CONFIRMED / AMENDED /
                                        # REJECTED / UNREVIEWED_AUTO_PASSED / ...
    source: str                         # "AI_GENERATED" / "MANUALLY_ADDED"
    agent_name: str                     # 来源 Agent: "risk_control" / "compliance"
    rationale_text: str                 # AI 解释性判定依据
    playbook_diff_text: str             # 与标准条款的差异描述
    regulation_reference: str           # 法规引用
    suggested_wording: str              # AI 修改建议
    clause_location: dict               # {page_number, char_offset_start, char_offset_end}
    escalated: bool
    escalated_from: Optional[str]
    sampled: bool
    created_at: Optional[str]
    created_by: Optional[str]


class DecisionDict(TypedDict, total=False):
    """审阅决策字典"""
    decision_id: str
    risk_flag_id: str
    decision_type: str                  # APPROVE / EDIT / REJECT /
                                        # MANUAL_ADD / BATCH_CONFIRM / ESCALATE
    reviewer_id: str
    comment: str
    modified_fields: Optional[dict]     # 编辑模式下的字段变更
    original_values: Optional[dict]     # 编辑前快照
    timestamp: str


class ComplianceResultDict(TypedDict, total=False):
    """合规检查结果字典"""
    check_id: str
    clause_id: str
    regulation: str                     # "GDPR" / "CCPA"
    compliance_status: str              # "compliant" / "non_compliant" / "needs_review"
    detail: str
    risk_level: str                     # 若不合规的风险等级


# ─────────────────────────────────────────────────────────────────
# 自定义 Reducer: merge_risk_flags
# ─────────────────────────────────────────────────────────────────

def merge_risk_flags(
    existing: list[dict],
    incoming: list[dict],
) -> list[dict]:
    """
    自定义 reducer：按 risk_flag_id 去重合并，同 ID 的后到者覆盖。
    来源: langchain_hitl_arch-v1.0.md §4.2 risk_flags reducer。

    风险分析和合规检查并行写入时，通过 agent_name 区分来源，
    相同 flag_id 的会覆盖，不同 flag_id 的会追加。
    """
    merged: dict[str, dict] = {}
    for flag in existing:
        merged[flag.get("risk_flag_id", "")] = flag
    for flag in incoming:
        fid = flag.get("risk_flag_id", "")
        if fid in merged:
            # 同 ID: 后到者覆盖（保留更完整的字段）
            merged[fid] = {**merged[fid], **flag}
        else:
            merged[fid] = flag
    return list(merged.values())


# ─────────────────────────────────────────────────────────────────
# DocumentReviewState (对齐 §4.2 + §2.3 State 类型定义)
# ─────────────────────────────────────────────────────────────────

class DocumentReviewState(TypedDict, total=False):
    """
    文档审核工作流完整状态定义。

    Reducer 语义:
      - clauses: operator.add (追加，支持并行)
      - risk_flags: merge_risk_flags (按 flag_id 去重合并)
      - review_decisions: operator.add (仅追加)
      - 其他字段: 默认覆盖 (最后写入者胜出)
    """
    # ── 文档级 ──
    document_id: str
    doc_status: str                     # CREATED / UPLOADED / PARSING / PARSED /
                                        # REVIEWING / REVIEWED / HUMAN_REVIEW /
                                        # COMPLETED / FAILED / CANCELLED
    doc_metadata: dict                  # {title, document_type, format, uploaded_at, ...}

    # ── 条款级 (Annotated + operator.add 并行安全) ──
    clauses: Annotated[list[ClauseDict], operator.add]

    # ── 风险级 (自定义 merge_risk_flags reducer) ──
    risk_flags: Annotated[list[RiskFlagDict], merge_risk_flags]

    # ── 合规结果 ──
    compliance_results: Annotated[list[ComplianceResultDict], operator.add]

    # ── 报告草稿 (覆盖语义) ──
    report_draft: Optional[dict]

    # ── 决策级 (append-only) ──
    review_decisions: Annotated[list[DecisionDict], operator.add]

    # ── 中断控制 ──
    interrupt_state: str                # idle / waiting / resolved
    pending_interrupts: list[str]       # 活跃中断 ID 列表

    # ── 错误控制 ──
    error_info: Annotated[
        Optional[dict],
        lambda existing, incoming: (
            incoming
            if incoming is not None
            else existing
        ),
    ]
    retry_count: int
