"""
Report Agent — 汇总所有 RiskFlag → 生成审阅报告草稿。

输入: DocumentReviewState (risk_flags[], compliance_results[], clauses[])
输出: report_draft (结构化报告摘要)
"""

from __future__ import annotations

import uuid
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.language_models import BaseChatModel

REPORT_SYSTEM_PROMPT = """你是一位专业的法律审阅报告撰写专家。你的任务是根据 AI 风险分析结果，生成一份结构化的审阅报告草稿。

## 报告结构
1. **文档概览**: 文档基本信息、条款总数、风险分布
2. **高风险条款详情**: 逐条列出 HIGH 风险条款的完整信息
3. **中风险条款摘要**: 列出 MEDIUM 风险条款的核心问题
4. **合规检查发现**: GDPR/CCPA 合规问题
5. **总体建议**: 基于风险分布的综合建议和后续行动

## 输出格式
请以 JSON 格式输出报告草稿：

```json
{
  "report_id": "rpt_xxx",
  "document_summary": {
    "total_clauses": 10,
    "high_risk_count": 2,
    "medium_risk_count": 3,
    "low_risk_count": 5,
    "compliance_issues": 1
  },
  "high_risk_details": [...],
  "medium_risk_summary": "...",
  "compliance_findings": "...",
  "overall_recommendation": "...",
  "risk_distribution": {
    "high": 2,
    "medium": 3,
    "low": 5
  }
}
```
"""


async def run_report_generation(
    state: dict[str, Any],
    model: BaseChatModel,
) -> dict[str, Any]:
    """
    Report Agent — 汇总风险数据，生成结构化报告草稿。

    Args:
        state: DocumentReviewState 的当前快照
        model: LLM 模型实例

    Returns:
        更新 dict: {"report_draft": {...}}
    """
    document_id = state.get("document_id", "")
    risk_flags = state.get("risk_flags", [])
    compliance_results = state.get("compliance_results", [])
    clauses = state.get("clauses", [])

    # 构建风险摘要
    high_flags = [f for f in risk_flags if f.get("risk_level") == "HIGH"]
    medium_flags = [
        f for f in risk_flags if f.get("risk_level") == "MEDIUM"
    ]
    low_flags = [f for f in risk_flags if f.get("risk_level") == "LOW"]

    # 高风险详情文本
    high_details_text_parts: list[str] = []
    for flag in high_flags:
        flag_text = (
            f"- **风险标记 ID**: {flag.get('risk_flag_id', 'N/A')}\n"
            f"  - 条款 ID: {flag.get('clause_id', 'N/A')}\n"
            f"  - 风险类别: {flag.get('risk_category', '未知')}\n"
            f"  - 置信度: {flag.get('ai_confidence', 0)}\n"
            f"  - 判定依据: {flag.get('rationale_text', '')}\n"
            f"  - 修改建议: {flag.get('suggested_wording', '')}\n"
        )
        high_details_text_parts.append(flag_text)
    high_details_text = "\n".join(high_details_text_parts) if high_details_text_parts else "无高风险条款"

    # 中风险摘要文本
    medium_summary_parts: list[str] = []
    for flag in medium_flags:
        medium_summary_parts.append(
            f"- {flag.get('risk_category', '未知')}: "
            f"{flag.get('rationale_text', '无详情')[:200]}"
        )
    medium_summary_text = (
        "\n".join(medium_summary_parts)
        if medium_summary_parts
        else "无中风险条款"
    )

    # 合规检查摘要
    non_compliant = [
        c
        for c in compliance_results
        if c.get("compliance_status") in ("non_compliant", "needs_review")
    ]
    compliance_text_parts: list[str] = []
    for item in non_compliant:
        compliance_text_parts.append(
            f"- {item.get('regulation', '')}: {item.get('detail', '')[:300]}"
        )
    compliance_text = (
        "\n".join(compliance_text_parts) if compliance_text_parts else "未发现合规问题"
    )

    messages = [
        SystemMessage(content=REPORT_SYSTEM_PROMPT),
        HumanMessage(
            content=f"""请根据以下数据生成审阅报告草稿。

文档 ID: {document_id}

## 条款统计
- 条款总数: {len(clauses)}
- 高风险: {len(high_flags)}
- 中风险: {len(medium_flags)}
- 低风险: {len(low_flags)}

## 高风险条款详情
{high_details_text}

## 中风险条款摘要
{medium_summary_text}

## 合规检查发现
{compliance_text}

请以 JSON 格式输出报告草稿，包含 document_summary、overall_recommendation 等关键字段。"""
        ),
    ]

    try:
        response = await model.ainvoke(messages)
        response_text = response.content

        import json
        import re

        json_match = re.search(
            r"\{.*?\}", response_text, re.DOTALL
        )
        if json_match:
            report = json.loads(json_match.group())
        else:
            report = json.loads(response_text)

        # 补充统计字段（确保数据一致性）
        report["report_id"] = f"rpt_{uuid.uuid4().hex[:12]}"
        report["document_id"] = document_id
        report["risk_distribution"] = {
            "high": len(high_flags),
            "medium": len(medium_flags),
            "low": len(low_flags),
        }
        report["document_summary"] = report.get(
            "document_summary", {}
        )
        report["document_summary"]["total_clauses"] = len(clauses)
        report["document_summary"]["high_risk_count"] = len(
            high_flags
        )
        report["document_summary"]["medium_risk_count"] = len(
            medium_flags
        )
        report["document_summary"]["low_risk_count"] = len(low_flags)

        return {"report_draft": report}

    except Exception as e:
        # 即使 LLM 调用失败，也生成基础统计报告
        fallback_report = {
            "report_id": f"rpt_{uuid.uuid4().hex[:12]}",
            "document_id": document_id,
            "document_summary": {
                "total_clauses": len(clauses),
                "high_risk_count": len(high_flags),
                "medium_risk_count": len(medium_flags),
                "low_risk_count": len(low_flags),
            },
            "risk_distribution": {
                "high": len(high_flags),
                "medium": len(medium_flags),
                "low": len(low_flags),
            },
            "overall_recommendation": (
                f"共发现 {len(high_flags)} 条高风险条款，建议优先处理。"
                if high_flags
                else "未发现高风险条款，建议继续执行标准审批流程。"
            ),
            "note": f"LLM 报告生成异常，此为自动统计摘要: {str(e)}",
        }
        return {"report_draft": fallback_report}
