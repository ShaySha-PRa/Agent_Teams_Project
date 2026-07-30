"""
Risk Control Agent — 风控识别：识别高风险条款并分级。

输入: DocumentReviewState (clauses[])
输出: risk_flags[] (HIGH/MEDIUM/LOW + 判定依据 + 修改建议)
"""

from __future__ import annotations

import uuid
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.language_models import BaseChatModel

RISK_SYSTEM_PROMPT = """你是一位专业的合同风控专家。你的任务是对 NDA（保密协议）的各项条款进行风险分析和分级。

## 风险等级定义
- **HIGH (高)**: 条款对甲方明显不利，可能导致重大法律或财务风险，必须人工审批
  - 例: 保密期限"永久"、赔偿无上限、管辖法院在对方所在地
- **MEDIUM (中)**: 条款存在一定风险，但可协商调整
  - 例: 通知方式不明确、保密范围稍有宽泛
- **LOW (低)**: 条款符合行业标准，无实质性风险
  - 例: 标准通知条款、标准完整协议条款

## 风险类别（15 类）
1. 合规风险 — 违反 GDPR/CCPA 等法规
2. 财务风险 — 赔偿责任、赔偿上限
3. 法律风险 — 管辖法律、争议解决对己方不利
4. 定义过宽 — 保密信息范围过于宽泛
5. 期限不合理 — 保密期限过长或过短
6. 缺失关键条款 — 重要保护条款缺失
7. 例外情形不完整 — 保密例外条款缺失要素
8. 违约救济失衡 — 违约责任不均衡
9. 存续条款不明确 — 终止后义务描述不清
10. 管辖法律不利 — 适用法律对己方不利
11. 争议解决不公正 — 仲裁/诉讼地点不公正
12. 通知条款模糊 — 通知方式不明确
13. 可转让性过宽 — 权利义务可随意转让
14. 完整协议过于宽泛 — 可能覆盖其他重要协议
15. 其他 — 未归类的风险

## 输出格式
对于每个条款，请输出风险分析结果。对于没有风险的条款，设置 risk_level 为 "LOW"。
请以 JSON 数组格式输出：

```json
[
  {
    "clause_id": "cl_xxx",
    "clause_type": "保密期限",
    "risk_level": "HIGH",
    "risk_category": "期限不合理",
    "ai_confidence": 0.92,
    "rationale_text": "保密期限为'永久'，超过行业标准的3-5年...",
    "playbook_diff_text": "标准: 保密期限不超过5年\\n实际: 保密义务永久有效",
    "regulation_reference": "参照《商业秘密保护规定》第12条...",
    "suggested_wording": "建议修改为: 保密义务自披露之日起5年内有效"
  }
]
```
"""


async def run_risk_analysis(
    state: dict[str, Any],
    model: BaseChatModel,
) -> dict[str, Any]:
    """
    Risk Control Agent — 分析条款风险并生成风险标记。

    Args:
        state: DocumentReviewState 的当前快照
        model: LLM 模型实例

    Returns:
        更新 dict: {"risk_flags": [RiskFlagDict, ...]}
    """
    document_id = state.get("document_id", "")
    clauses = state.get("clauses", [])

    if not clauses:
        return {"risk_flags": []}

    # 构造条款摘要供 LLM 分析
    clauses_text_parts: list[str] = []
    for clause in clauses:
        clauses_text_parts.append(
            f"### 条款 ID: {clause.get('clause_id', 'N/A')}\n"
            f"类型: {clause.get('clause_type', '未知')}\n"
            f"原文: {clause.get('clause_text', '')}\n"
            f"位置: 第{clause.get('page_number', 1)}页"
            f"第{clause.get('paragraph_number', 0)}段\n"
        )
    clauses_text = "\n---\n".join(clauses_text_parts)

    messages = [
        SystemMessage(content=RISK_SYSTEM_PROMPT),
        HumanMessage(
            content=f"""请对以下 NDA 文档的各条款进行风险分析。

文档 ID: {document_id}

条款列表:
{clauses_text}

请严格按照 JSON 数组格式输出每个条款的风险分析结果。
对每个条款都必须输出分析结果（低风险条款 risk_level 设为 "LOW"）。"""
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
            risk_items = json.loads(json_match.group())
        else:
            risk_items = json.loads(response_text)

        risk_flags: list[dict] = []
        for item in risk_items:
            clause_id = item.get("clause_id", "")
            risk_level = item.get("risk_level", "LOW").upper()

            # 校准风险等级为 HIGH / MEDIUM / LOW
            if risk_level not in ("HIGH", "MEDIUM", "LOW"):
                risk_level = "LOW"

            flag = {
                "risk_flag_id": f"rf_{uuid.uuid4().hex[:12]}",
                "clause_id": clause_id,
                "document_id": document_id,
                "risk_level": risk_level,
                "risk_category": item.get(
                    "risk_category", "其他"
                ),
                "ai_confidence": float(
                    item.get("ai_confidence", 0.8)
                ),
                "status": (
                    "PENDING_REVIEW" if risk_level == "HIGH"
                    else "UNREVIEWED_AUTO_PASSED"
                ),
                "source": "AI_GENERATED",
                "agent_name": "risk_control",
                "rationale_text": item.get("rationale_text", ""),
                "playbook_diff_text": item.get(
                    "playbook_diff_text", ""
                ),
                "regulation_reference": item.get(
                    "regulation_reference", ""
                ),
                "suggested_wording": item.get(
                    "suggested_wording", ""
                ),
                "clause_location": {},
                "escalated": False,
                "escalated_from": None,
                "sampled": False,
                "created_at": "",
                "created_by": "risk_control_agent",
            }

            # 补充 clause_location 从原始 clauses 中
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

        return {"risk_flags": risk_flags}

    except Exception as e:
        return {
            "risk_flags": [],
            "error_info": {
                "error_type": "risk_analysis_failed",
                "error_message": f"风险分析失败: {str(e)}",
                "recoverable": True,
            },
        }
