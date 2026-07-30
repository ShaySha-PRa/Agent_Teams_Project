"""
Clause Extraction Agent — NDA 10 类条款结构化提取。

输入: DocumentReviewState (含 doc_metadata 中已解析的文档全文)
输出: clauses[] (10 类 NDA 条款 + 位置标注 + 置信度)
"""

from __future__ import annotations

import hashlib
import uuid
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.language_models import BaseChatModel

# NDA 10 类条款枚举
NDA_CLAUSE_TYPES = [
    "保密义务",
    "保密期限",
    "例外情形",
    "违约救济",
    "存续条款",
    "管辖法律",
    "争议解决",
    "通知条款",
    "可转让性",
    "完整协议",
]

EXTRACTION_SYSTEM_PROMPT = """你是一位专业的合同条款提取专家。你的任务是从给定的 NDA（保密协议）文档文本中，识别并提取出标准化的 10 类关键条款。

对于每一类条款，你需要：
1. 判断该条款是否在文档中存在
2. 如果存在，提取完整的条款原文
3. 标注条款在原文中的位置（字符偏移量、页码、段落号）
4. 给出提取置信度（0.0-1.0）

## 输出格式
请以 JSON 数组格式输出，每个元素包含以下字段：
```json
[
  {
    "clause_type": "保密义务",
    "clause_text": "条款原文...",
    "extraction_confidence": 0.95,
    "page_number": 2,
    "paragraph_number": 3,
    "char_offset_start": 1420,
    "char_offset_end": 1650,
    "found": true
  }
]
```

对于文档中不存在的条款类型，found 设为 false，clause_text 设为空字符串。

## NDA 10 类条款说明
- **保密义务 (Confidentiality Obligation)**: 定义保密信息的范围和双方的保密义务
- **保密期限 (Confidentiality Term)**: 规定保密义务的持续时间
- **例外情形 (Exceptions)**: 列出不适用保密义务的信息类型（如已公开信息、独立开发等）
- **违约救济 (Breach Remedies)**: 规定违反保密义务时的救济措施和赔偿责任
- **存续条款 (Survival Clause)**: 协议终止后保密义务继续有效
- **管辖法律 (Governing Law)**: 约定适用法律和管辖法院
- **争议解决 (Dispute Resolution)**: 争议解决方式（诉讼/仲裁）
- **通知条款 (Notice Clause)**: 双方的通知方式和送达规则
- **可转让性 (Assignability)**: 协议权利义务的可转让性
- **完整协议 (Entire Agreement)**: 声明本协议构成完整协议，取代先前所有约定
"""


async def run_clause_extraction(
    state: dict[str, Any],
    model: BaseChatModel,
) -> dict[str, Any]:
    """
    Clause Extraction Agent — 从文档全文中提取 NDA 10 类条款。

    Args:
        state: DocumentReviewState 的当前快照
        model: LLM 模型实例

    Returns:
        更新 dict: {"clauses": [ClauseDict, ...]}
    """
    document_id = state.get("document_id", "")
    doc_metadata = state.get("doc_metadata", {})
    doc_text = doc_metadata.get("full_text", "")

    if not doc_text:
        return {
            "clauses": [],
            "error_info": {
                "error_type": "extraction_failed",
                "error_message": "文档文本为空，无法提取条款",
                "recoverable": False,
            },
        }

    # 截断过长文本（LLM context window 限制）
    max_chars = 15000
    truncated_text = doc_text[:max_chars]

    messages = [
        SystemMessage(content=EXTRACTION_SYSTEM_PROMPT),
        HumanMessage(
            content=f"""请从以下 NDA 文档文本中提取 10 类关键条款。

文档 ID: {document_id}

原文:
---
{truncated_text}
---

请严格按照 JSON 数组格式输出结果。"""
        ),
    ]

    try:
        response = await model.ainvoke(messages)
        response_text = response.content

        # 解析 LLM 输出的 JSON
        import json
        import re

        # 尝试提取 JSON 数组
        json_match = re.search(
            r"\[\s*\{.*?\}\s*\]", response_text, re.DOTALL
        )
        if json_match:
            extracted = json.loads(json_match.group())
        else:
            extracted = json.loads(response_text)

        # 转换为 ClauseDict 格式
        clauses: list[dict] = []
        for item in extracted:
            if not item.get("found", False):
                continue

            clause = {
                "clause_id": f"cl_{uuid.uuid4().hex[:12]}",
                "clause_type": item.get("clause_type", "未知"),
                "clause_text": item.get("clause_text", ""),
                "extraction_confidence": float(
                    item.get("extraction_confidence", 0.8)
                ),
                "page_number": int(item.get("page_number", 1)),
                "paragraph_number": int(
                    item.get("paragraph_number", 0)
                ),
                "char_offset_start": int(
                    item.get("char_offset_start", 0)
                ),
                "char_offset_end": int(item.get("char_offset_end", 0)),
                "text_hash": hashlib.sha256(
                    item.get("clause_text", "").encode()
                ).hexdigest()[:16],
                "source": "AI",
            }
            clauses.append(clause)

        return {"clauses": clauses}

    except Exception as e:
        return {
            "clauses": [],
            "error_info": {
                "error_type": "extraction_failed",
                "error_message": f"条款提取失败: {str(e)}",
                "recoverable": True,
            },
        }
