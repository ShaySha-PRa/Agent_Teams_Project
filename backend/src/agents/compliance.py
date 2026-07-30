"""
Compliance Agent — 合规检查：GDPR/CCPA 法规对照检查。

输入: DocumentReviewState (clauses[])
输出: compliance_results[] + risk_flags[] (合规风险相关)
"""

from __future__ import annotations

import uuid
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.language_models import BaseChatModel

COMPLIANCE_SYSTEM_PROMPT = """你是一位专业的 NDA 合规审查专家，精通 GDPR（欧盟通用数据保护条例）和 CCPA（加州消费者隐私法案）。

你的任务是对 NDA 文档中的各条款进行合规检查，判断是否违反或缺少法规要求的保护性条款。

## 检查维度
1. **数据保护**: 保密信息中是否包含个人数据？条款是否满足 GDPR 第 28 条（数据处理者义务）的要求？
2. **数据跨境传输**: 是否涉及跨境数据传输？是否满足 GDPR 第 44-49 条的要求？
3. **数据主体权利**: 条款是否与 GDPR 第 12-22 条的数据主体权利（访问权、删除权、可携权）冲突？
4. **数据保留期限**: 保密期限是否与 GDPR 第 5(1)(e) 条的存储限制原则一致？
5. **CCPA 消费者权利**: 条款是否限制了 CCPA 下的消费者知情权、删除权、退出权？
6. **数据处理协议 (DPA)**: 是否缺少必要的数据处理协议引用？
7. **安全措施**: 是否缺少 GDPR 第 32 条要求的安全措施描述？

## 输出格式
请以 JSON 数组格式输出合规检查结果：

```json
[
  {
    "clause_id": "cl_xxx",
    "regulation": "GDPR",
    "compliance_status": "non_compliant",
    "detail": "保密期限为'永久'，违反GDPR第5(1)(e)条存储限制原则...",
    "risk_level": "HIGH",
    "clause_type": "保密期限",
    "regulation_article": "Art. 5(1)(e)",
    "recommendation": "建议添加明确的保留期限，如'自披露之日起5年内有效'"
  }
]
```

compliance_status 取值:
- "compliant" — 完全合规
- "non_compliant" — 不合规（仅对高风险项输出）
- "needs_review" — 需进一步审查
"""


async def run_compliance_check(
    state: dict[str, Any],
    model: BaseChatModel,
) -> dict[str, Any]:
    """
    Compliance Agent — GDPR/CCPA 合规检查。

    Args:
        state: DocumentReviewState 的当前快照
        model: LLM 模型实例

    Returns:
        更新 dict: {
            "compliance_results": [ComplianceResultDict, ...],
            "risk_flags": [RiskFlagDict, ...] (合规风险)
        }
    """
    document_id = state.get("document_id", "")
    clauses = state.get("clauses", [])

    if not clauses:
        return {"compliance_results": [], "risk_flags": []}

    clauses_text_parts: list[str] = []
    for clause in clauses:
        clauses_text_parts.append(
            f"### 条款 ID: {clause.get('clause_id', 'N/A')}\n"
            f"类型: {clause.get('clause_type', '未知')}\n"
            f"原文: {clause.get('clause_text', '')}\n"
        )
    clauses_text = "\n---\n".join(clauses_text_parts)

    messages = [
        SystemMessage(content=COMPLIANCE_SYSTEM_PROMPT),
        HumanMessage(
            content=f"""请对以下 NDA 文档进行 GDPR/CCPA 合规检查。

文档 ID: {document_id}

条款列表:
{clauses_text}

请严格按照 JSON 数组格式输出合规检查结果。
对所有条款都必须输出检查结果。合规的条款 compliance_status 设为 "compliant"。"""
        ),
    ]

    try:
        response = await model.ainvoke(messages)
        response_text = response.content

        import json
        import re

        json_match = re.search(
            r"\[\s*\{.*?\}\s*\]", response_text, re.DOTALL
        )
        if json_match:
            compliance_items = json.loads(json_match.group())
        else:
            compliance_items = json.loads(response_text)

        compliance_results: list[dict] = []
        risk_flags: list[dict] = []

        for item in compliance_items:
            clause_id = item.get("clause_id", "")
            compliance_status = item.get(
                "compliance_status", "compliant"
            )

            # 合规检查结果
            result = {
                "check_id": f"cc_{uuid.uuid4().hex[:12]}",
                "clause_id": clause_id,
                "regulation": item.get("regulation", "GDPR"),
                "compliance_status": compliance_status,
                "detail": item.get("detail", ""),
            }
            compliance_results.append(result)

            # 不合规项生成风险标记
            if compliance_status in ("non_compliant", "needs_review"):
                risk_level = item.get("risk_level", "MEDIUM").upper()
                if risk_level not in ("HIGH", "MEDIUM", "LOW"):
                    risk_level = "MEDIUM"

                flag = {
                    "risk_flag_id": f"rf_{uuid.uuid4().hex[:12]}",
                    "clause_id": clause_id,
                    "document_id": document_id,
                    "risk_level": risk_level,
                    "risk_category": "合规风险",
                    "ai_confidence": 0.85,
                    "status": (
                        "PENDING_REVIEW" if risk_level == "HIGH"
                        else "UNREVIEWED_AUTO_PASSED"
                    ),
                    "source": "AI_GENERATED",
                    "agent_name": "compliance",
                    "rationale_text": item.get("detail", ""),
                    "playbook_diff_text": (
                        f"法规要求: {item.get('regulation_article', 'N/A')}\n"
                        f"合规建议: {item.get('recommendation', '')}"
                    ),
                    "regulation_reference": item.get(
                        "regulation_article", ""
                    ),
                    "suggested_wording": item.get("recommendation", ""),
                    "clause_location": {},
                    "escalated": False,
                    "escalated_from": None,
                    "sampled": False,
                    "created_at": "",
                    "created_by": "compliance_agent",
                }

                for c in clauses:
                    if c.get("clause_id") == clause_id:
                        flag["clause_location"] = {
                            "page_number": c.get("page_number", 1),
                            "char_offset_start": c.get(
                                "char_offset_start", 0
                            ),
                            "char_offset_end": c.get(
                                "char_offset_end", 0
                            ),
                        }
                        break

                risk_flags.append(flag)

        return {
            "compliance_results": compliance_results,
            "risk_flags": risk_flags,
        }

    except Exception as e:
        return {
            "compliance_results": [],
            "risk_flags": [],
            "error_info": {
                "error_type": "compliance_check_failed",
                "error_message": f"合规检查失败: {str(e)}",
                "recoverable": True,
            },
        }
