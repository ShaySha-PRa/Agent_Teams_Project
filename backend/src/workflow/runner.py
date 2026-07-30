"""
Workflow Runner — 触发 StateGraph 执行 + SSE 事件流生成。

对齐: langchain_hitl_arch-v1.0.md §6.3 SSE 事件类型
支持:
  - stream_events(version="v3") 事件流
  - 9 种 SSE 事件类型
  - Command(resume=...) 中断恢复
  - thread_id 隔离并发审阅
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, AsyncGenerator

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from .state import DocumentReviewState
from .graph import compile_graph

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────
# 9 SSE 事件类型 (对齐 §6.3)
# ─────────────────────────────────────────────────────────────────

SSE_EVENT_TYPES = frozenset({
    "parse.progress",
    "parse.complete",
    "parse.failed",
    "review.progress",
    "review.log",
    "review.complete",
    "review.failed",
    "review.timeout",
    "interrupt.ready",
})


# ─────────────────────────────────────────────────────────────────
# Workflow Runner
# ─────────────────────────────────────────────────────────────────

class WorkflowRunner:
    """
    工作流执行器 — 封装 StateGraph 的生命周期管理。

    每个 runner 实例对应一个独立的 InMemorySaver 检查点存储。
    通过 thread_id 隔离不同的文档审阅会话。
    """

    def __init__(self, checkpointer: InMemorySaver | None = None):
        self.checkpointer = checkpointer or InMemorySaver()
        self.graph = compile_graph(checkpointer=self.checkpointer)

    async def start_review(
        self,
        document_id: str,
        doc_metadata: dict[str, Any],
        thread_id: str,
    ) -> AsyncGenerator[str, None]:
        """
        启动一个新的文档审核工作流。

        Args:
            document_id: 文档唯一 ID
            doc_metadata: 文档元数据 (含 full_text, title, document_type, format 等)
            thread_id: LangGraph 线程 ID，用于 checkpoint 隔离

        Yields:
            SSE 格式化的事件字符串
        """
        initial_input: dict[str, Any] = {
            "document_id": document_id,
            "doc_status": "UPLOADED",
            "doc_metadata": doc_metadata,
            "clauses": [],
            "risk_flags": [],
            "compliance_results": [],
            "report_draft": None,
            "review_decisions": [],
            "interrupt_state": "idle",
            "pending_interrupts": [],
            "error_info": None,
            "retry_count": 0,
        }

        config = {"configurable": {"thread_id": thread_id}}

        events = await self.graph.astream_events(
            initial_input,
            config=config,
            version="v3",
        )
        async for event in events:
            sse_text = self._map_event_to_sse(event)
            if sse_text:
                yield sse_text

    async def resume_review(
        self,
        resume_data: dict[str, Any],
        thread_id: str,
    ) -> AsyncGenerator[str, None]:
        """
        恢复被中断的审阅流程。

        Args:
            resume_data: 前端提交的审批决策数据
            thread_id: LangGraph 线程 ID，必须与中断时的 thread_id 一致

        Yields:
            SSE 格式化的事件字符串
        """
        config = {"configurable": {"thread_id": thread_id}}
        command = Command(resume=resume_data)

        async for event in self.graph.astream_events(
            command,
            config=config,
            version="v3",
        ):
            sse_text = self._map_event_to_sse(event)
            if sse_text:
                yield sse_text

    async def get_state(self, thread_id: str) -> dict[str, Any] | None:
        """
        获取当前线程的 State 快照（不推进执行）。

        Args:
            thread_id: LangGraph 线程 ID

        Returns:
            当前 State 快照，若不存在则返回 None
        """
        config = {"configurable": {"thread_id": thread_id}}
        try:
            state = self.graph.get_state(config)
            if state and state.values:
                return state.values
            return None
        except Exception:
            return None

    async def update_state_direct(
        self,
        thread_id: str,
        updates: dict[str, Any],
    ) -> None:
        """
        直接更新 State（不触发节点执行）。
        用于 manual_add 操作等不需要通过 interrupt 的流程。

        Args:
            thread_id: LangGraph 线程 ID
            updates: 要更新的 State 字段
        """
        config = {"configurable": {"thread_id": thread_id}}
        self.graph.update_state(config, updates)

    # ─────────────────────────────────────────────
    # Event → SSE 映射
    # ─────────────────────────────────────────────

    def _map_event_to_sse(self, event: dict[str, Any]) -> str | None:
        """
        将 LangGraph stream_events(v3) 事件映射为 SSE 字符串。

        Args:
            event: LangGraph 流事件

        Returns:
            SSE 格式化字符串 "event: <type>\ndata: <json>\n\n"
            或 None (不推送的事件)
        """
        event_type = event.get("event", "")
        event_name = event.get("name", "")

        # ── on_chain_start 事件 ──
        if event_type == "on_chain_start":
            return self._handle_chain_start(event_name, event)

        # ── on_chain_end 事件 ──
        if event_type == "on_chain_end":
            return self._handle_chain_end(event_name, event)

        # ── on_chat_model_stream (LLM token 流，用于 review.log) ──
        if event_type == "on_chat_model_stream":
            return self._handle_llm_stream(event)

        # ── on_custom_event (interrupt 等自定义事件) ──
        if event_type == "on_custom_event":
            return self._handle_custom_event(event)

        return None

    def _handle_chain_start(
        self, name: str, event: dict[str, Any]
    ) -> str | None:
        """处理节点开始事件 -> review.progress / parse.progress"""
        data = event.get("data", {})

        if name == "parse_document":
            return self._sse(
                "parse.progress",
                {
                    "agent_name": "parser",
                    "progress_pct": 0.0,
                    "current_clause_type": "初始化",
                },
            )

        if name == "extract_clauses":
            return self._sse(
                "parse.progress",
                {
                    "agent_name": "clause_extraction",
                    "progress_pct": 0.2,
                    "current_clause_type": "条款提取中",
                },
            )

        if name == "risk_analysis":
            return self._sse(
                "review.progress",
                {
                    "agent_name": "risk_control",
                    "clauses_processed": 0,
                    "total_clauses": data.get("input", {})
                    .get("clauses", [])
                    .__len__()
                    if isinstance(
                        data.get("input", {}).get("clauses"), list
                    )
                    else 0,
                    "current_dimension": "风险分析启动",
                },
            )

        if name == "compliance_check":
            return self._sse(
                "review.progress",
                {
                    "agent_name": "compliance",
                    "clauses_processed": 0,
                    "total_clauses": data.get("input", {})
                    .get("clauses", [])
                    .__len__()
                    if isinstance(
                        data.get("input", {}).get("clauses"), list
                    )
                    else 0,
                    "current_dimension": "合规检查启动",
                },
            )

        if name == "generate_report_draft":
            return self._sse(
                "review.progress",
                {
                    "agent_name": "report",
                    "clauses_processed": 0,
                    "total_clauses": 0,
                    "current_dimension": "报告生成中",
                },
            )

        # HITL 子节点进度
        if name == "human_review_router":
            return self._sse(
                "review.progress",
                {
                    "agent_name": "hitl_router",
                    "clauses_processed": 0,
                    "total_clauses": 0,
                    "current_dimension": "进入人工审批路由",
                },
            )

        if name == "human_review_ip1":
            return self._sse(
                "review.progress",
                {
                    "agent_name": "hitl",
                    "clauses_processed": 0,
                    "total_clauses": 0,
                    "current_dimension": "高风险条款审批",
                },
            )

        if name == "human_review_ip2":
            return self._sse(
                "review.progress",
                {
                    "agent_name": "hitl",
                    "clauses_processed": 0,
                    "total_clauses": 0,
                    "current_dimension": "中风险批量审批",
                },
            )

        if name == "human_review_ip3":
            return self._sse(
                "review.progress",
                {
                    "agent_name": "hitl",
                    "clauses_processed": 0,
                    "total_clauses": 0,
                    "current_dimension": "最终确认",
                },
            )

        return None

    def _handle_chain_end(
        self, name: str, event: dict[str, Any]
    ) -> str | None:
        """处理节点结束事件 -> parse.complete / review.complete / review.failed"""
        data = event.get("data", {})
        output = data.get("output", {})

        if name == "extract_clauses":
            clauses = output.get("clauses", [])
            error = output.get("error_info")

            if error:
                return self._sse("parse.failed", error)
            return self._sse(
                "parse.complete",
                {
                    "document_id": output.get("document_id", ""),
                    "clause_count": len(clauses),
                },
            )

        # 并行节点完成时检查错误
        if name in ("risk_analysis", "compliance_check"):
            error = output.get("error_info")
            if error:
                return self._sse(
                    "review.failed",
                    {
                        "fail_category": error.get(
                            "error_type", "agent_error"
                        ),
                        "message": error.get("error_message", ""),
                        "partial_results_available": True,
                    },
                )

        if name == "generate_report_draft":
            report = output.get("report_draft", {})
            dist = report.get("risk_distribution", {})
            return self._sse(
                "review.complete",
                {
                    "summary": {
                        "high": dist.get("high", 0),
                        "medium": dist.get("medium", 0),
                        "low": dist.get("low", 0),
                    }
                },
            )

        return None

    def _handle_llm_stream(
        self, event: dict[str, Any]
    ) -> str | None:
        """处理 LLM token 流 -> review.log"""
        data = event.get("data", {})
        chunk = data.get("chunk", {})

        # 仅在非流式总结时推送
        content = ""
        if hasattr(chunk, "content"):
            content = chunk.content
        elif isinstance(chunk, dict):
            content = chunk.get("content", "")

        if content and len(str(content)) > 50:
            return self._sse(
                "review.log",
                {
                    "timestamp": "",
                    "agent_name": data.get("name", "agent"),
                    "message": str(content)[:500],
                },
            )

        return None

    def _handle_custom_event(
        self, event: dict[str, Any]
    ) -> str | None:
        """处理自定义事件 (interrupt 等) -> interrupt.ready"""
        data = event.get("data", {})
        event_name = event.get("name", "")

        if "__interrupt__" in str(event_name) or "interrupt" in str(
            event_name
        ):
            if isinstance(data, dict) and "interrupt_point" in data:
                return self._sse(
                    "interrupt.ready",
                    {
                        "interrupt_id": data.get(
                            "interrupt_point", ""
                        ),
                        "interrupt_type": data.get(
                            "interrupt_type", ""
                        ),
                        "payload": data,
                    },
                )

        return None

    # ─────────────────────────────────────────────
    # SSE 格式化
    # ─────────────────────────────────────────────

    @staticmethod
    def _sse(event_type: str, data: dict[str, Any]) -> str:
        """格式化为 SSE 字符串。"""
        return (
            f"event: {event_type}\n"
            f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
        )


# ─────────────────────────────────────────────────────────────────
# SSE 事件生成器（FastAPI StreamingResponse 兼容）
# ─────────────────────────────────────────────────────────────────

async def generate_sse_events(
    runner: WorkflowRunner,
    document_id: str,
    doc_metadata: dict[str, Any],
    thread_id: str,
    heartbeat_interval: int = 30,
) -> AsyncGenerator[str, None]:
    """
    SSE 事件生成器 — 供 FastAPI StreamingResponse 使用。

    生成事件流直到工作流完成，并发送 heartbeat 保持连接。

    Args:
        runner: WorkflowRunner 实例
        document_id: 文档 ID
        doc_metadata: 文档元数据
        thread_id: LangGraph 线程 ID
        heartbeat_interval: 心跳间隔（秒）

    Yields:
        SSE 格式化事件字符串
    """
    review_task = asyncio.create_task(
        _collect_sse_events(
            runner.start_review(document_id, doc_metadata, thread_id)
        )
    )

    # 轮询方式检查任务完成，同时发送心跳
    while not review_task.done():
        try:
            # 从已完成的结果中取事件
            done, _ = await asyncio.wait(
                {review_task}, timeout=heartbeat_interval
            )
            if done:
                break
            # 发送心跳
            yield ": heartbeat\n\n"
        except Exception:
            break

    try:
        events = await review_task
        for sse_text in events:
            yield sse_text
    except Exception as e:
        yield f"event: review.failed\ndata: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"


async def _collect_sse_events(
    generator: AsyncGenerator[str, None],
) -> list[str]:
    """收集异步生成器中的所有事件。"""
    events: list[str] = []
    async for event_text in generator:
        events.append(event_text)
    return events


async def generate_resume_sse_events(
    runner: WorkflowRunner,
    resume_data: dict[str, Any],
    thread_id: str,
    heartbeat_interval: int = 30,
) -> AsyncGenerator[str, None]:
    """
    中断恢复的 SSE 事件生成器。

    Args:
        runner: WorkflowRunner 实例
        resume_data: 审批决策数据
        thread_id: LangGraph 线程 ID
        heartbeat_interval: 心跳间隔

    Yields:
        SSE 格式化事件字符串
    """
    async for event_text in runner.resume_review(
        resume_data, thread_id
    ):
        yield event_text


# ─────────────────────────────────────────────────────────────────
# CLI 入口 (开发/调试用)
# ─────────────────────────────────────────────────────────────────

async def run_sample_workflow() -> None:
    """
    运行一个示例工作流，用于开发调试。

    使用示例 NDA 文本模拟完整流程。
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    # 示例 NDA 文本
    sample_nda_text = """
保密协议 (NDA)

第一条 保密义务
接收方同意对披露方以书面形式明确标识为"保密"的信息承担保密义务。
保密信息包括但不限于：技术资料、商业计划、客户名单、财务数据。

第二条 保密期限
本协议项下的保密义务自披露之日起永久有效。

第三条 例外情形
保密义务不适用于以下信息：
(a) 非因接收方违反本协议而已进入公有领域的信息；

第四条 违约救济
如接收方违反本协议的保密义务，应赔偿披露方因此遭受的全部损失，
包括直接损失、间接损失和利润损失。

第五条 存续条款
本协议终止后，保密义务继续有效。

第六条 管辖法律
本协议适用美国加州法律。

第七条 争议解决
因本协议引起的争议，提交加州法院诉讼解决。

第八条 通知条款
任何通知应以书面形式发出。

第九条 可转让性
本协议项下的权利义务不得转让。

第十条 完整协议
本协议构成双方关于保密事项的完整协议，取代先前所有口头或书面约定。
"""

    runner = WorkflowRunner()
    doc_id = "doc_sample_001"
    thread_id = "thread_sample_001"

    print("=" * 60)
    print("Agent 智能文档审核系统 - Sample Workflow")
    print("=" * 60)

    async for sse_text in runner.start_review(
        document_id=doc_id,
        doc_metadata={
            "title": "NDA-示例协议-2026",
            "document_type": "NDA",
            "format": "PDF",
            "full_text": sample_nda_text,
        },
        thread_id=thread_id,
    ):
        # 解析 SSE 文本并打印
        lines = sse_text.strip().split("\n")
        for line in lines:
            if line.startswith("event:"):
                event_type = line[len("event: "):]
            elif line.startswith("data:"):
                data = line[len("data: "):]
                try:
                    payload = json.loads(data)
                    if event_type == "interrupt.ready":
                        print(f"\n[中断] {payload.get('interrupt_type')}")

                        # 读取 payload 详情...
                        # 在真实场景，这里会等待前端返回 resume_data
                        # 此处模拟自动审批所有高风险项
                        print("  -> 模拟自动审批")

                        # 模拟 resume
                        interrupt_point = payload.get(
                            "payload", {}
                        ).get("interrupt_point", "")
                        risk_flag = payload.get("payload", {}).get(
                            "risk_flag", {}
                        )

                        if interrupt_point == "IP-1":
                            resume_data = {
                                "decision": "approve",
                                "risk_flag_id": risk_flag.get(
                                    "risk_flag_id", ""
                                ),
                                "comment": "自动审批通过",
                            }
                            # 需要中断流程并重新启动
                            print(
                                f"  审批: {risk_flag.get('risk_category')}"
                            )
                        elif interrupt_point == "IP-2":
                            resume_data = {
                                "decision": "batch_confirm",
                                "comment": "批量确认中风险",
                            }
                            print("  中风险批量确认")
                        elif interrupt_point == "IP-3":
                            resume_data = {
                                "decision": "confirm_submit",
                            }
                            print("  确认提交")
                    elif event_type == "review.complete":
                        print(
                            f"\n[完成] 审核完成: "
                            f"H:{payload.get('summary', {}).get('high',0)} "
                            f"M:{payload.get('summary', {}).get('medium',0)} "
                            f"L:{payload.get('summary', {}).get('low',0)}"
                        )
                    elif event_type == "parse.complete":
                        print(
                            f"\n[解析完成] 提取 {payload.get('clause_count', 0)} 条条款"
                        )
                    else:
                        print(
                            f"[{event_type}] {json.dumps(payload, ensure_ascii=False)[:200]}"
                        )
                except json.JSONDecodeError:
                    print(f"[{event_type}] {data[:200]}")

    # 检查最终状态
    state = await runner.get_state(thread_id)
    if state:
        print(f"\n最终状态: {state.get('doc_status', 'N/A')}")
        print(
            f"条款数: {len(state.get('clauses', []))}"
        )
        print(
            f"风险标记数: {len(state.get('risk_flags', []))}"
        )
        print(
            f"审阅决策数: {len(state.get('review_decisions', []))}"
        )


if __name__ == "__main__":
    asyncio.run(run_sample_workflow())
