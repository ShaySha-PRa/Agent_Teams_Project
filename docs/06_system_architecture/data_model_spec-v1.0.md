# 数据模型规范 v1.0

> **版本**: v1.0
> **创建日期**: 2026-07-30
> **来源**: Teammate 1（文档+任务模型）+ Teammate 2（审核规则+解释模型）+ Teammate 3（HITL 交互模型）
> **Lead 汇总**: 综合 16 个模型、~200 字段、3 份 ER 图，标注前端展示与后端存储归属

---

## 一、Agent Team 执行摘要

| Teammate | 输出文件 | 规模 | 模型数 | 字段数 |
|----------|---------|:--:|:--:|:--:|
| Teammate 1 | `document_task_models-v1.0.md` | 770 行 | 5 | ~92 |
| Teammate 2 | `review_analysis_models-v1.0.md` | 817 行 | 6 | ~75 |
| Teammate 3 | `hitl_interaction_models-v1.0.md` | 1,021 行 | 5 | ~80 |
| **总计** | — | **2,608 行** | **16** | **~247** |

---

## 二、全数据模型 ER 总图

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                          数据模型关系总图                                        │
│                                                                              │
│  ┌──────────┐         ┌──────────────┐                                       │
│  │ Document │──1:N──▶│    Clause    │──1:N──▶┌──────────┐    ┌──────────────┐│
│  └────┬─────┘         └──────┬───────┘        │ RiskFlag │──1:1─▶│PlaybookMatch ││
│       │                      │                └────┬─────┘    └──────┬───────┘│
│       │ 1:1                  │ 1:1                  │                 │       │
│       ▼                      ▼                      │ 1:N             │ N:1   │
│  ┌──────────┐         ┌──────────────┐              │                 │       │
│  │UploadTask│         │ClauseLocation│              │ 1:1             ▼       │
│  └──────────┘         └──────────────┘              │          ┌────────────┐ │
│       │                                             │          │PlaybookRule│ │
│       │ 1:1                                         ▼          └─────┬──────┘ │
│       ▼                                       ┌──────────────┐         │       │
│  ┌──────────┐                                 │ReviewDecision│         │ 1:1   │
│  │ParseTask │                                 └──────┬───────┘         │       │
│  └──────────┘                                        │                 ▼       │
│       │                                              │ N:1   ┌──────────────┐│
│       │ 1:1                                          ├──────▶│ AuditLog     ││
│       ▼                                              │       └──────────────┘│
│  ┌──────────┐                                        │                         │
│  │ReviewTask│                                        │ 1:1                     │
│  └────┬─────┘                                        ▼                         │
│       │ 1:1                                   ┌──────────────┐                │
│       ▼                                       │   ReviewReport│                │
│  ┌────────────────┐                           └──────────────┘                │
│  │StateTransition │                                                            │
│  └────────────────┘      ┌──────────────────┐                                  │
│                          │InterruptSession  │                                  │
│                          └────────┬─────────┘                                  │
│                                   │ N:1                                        │
│                                   ▼                                            │
│                          ┌─────────────────┐                                   │
│                          │ApprovalProgress │                                   │
│                          └─────────────────┘                                   │
│                                                                              │
│  ┌─ Teammate 1 (5 models) ──┐  ┌─ Teammate 2 (6 models) ──┐                 │
│  │ Document / UploadTask     │  │ Clause / RiskFlag         │                 │
│  │ ParseTask / ReviewTask    │  │ PlaybookRule / Match      │                 │
│  │ StateTransition           │  │ ClauseLocation            │                 │
│  └───────────────────────────┘  │ ExplanationChain          │                 │
│                                 └───────────────────────────┘                 │
│          ┌─ Teammate 3 (5 models) ──┐                                         │
│          │ ReviewDecision / AuditLog│                                         │
│          │ ReviewReport             │                                         │
│          │ InterruptSession         │                                         │
│          │ ApprovalProgress         │                                         │
│          └──────────────────────────┘                                         │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 三、16 模型清单：字段、含义、关系

### 3.1 Teammate 1：文档与任务模型

| 模型 | 业务含义 | 关键字段 | 关系 |
|------|---------|---------|------|
| **Document** | 一份待审阅的合同/法务文档 | 25 字段：id、original_filename、title、document_type(NDA)、format(PDF/DOCX)、file_size_bytes、page_count、uploaded_at、md5_hash、status(10 状态)、storage_path、ocr_status、encryption_status、parse_task_id(FK)、review_thread_id | UploadTask 1:1、ParseTask 1:1、ReviewTask 1:1、Clause 1:N、StateTransition 1:N |
| **UploadTask** | 文件上传异步任务记录 | 16 字段：id、document_id(FK)、status(pending/uploading/completed/failed)、bytes_uploaded、total_bytes、upload_speed、format_validation_passed、encryption_detected、corruption_detected、ocr_detected | Document N:1 |
| **ParseTask** | 文档解析异步任务 | 15 字段：id、document_id(FK)、status(queued/parsing/completed/failed)、progress_clause_extraction(0-1)、progress_risk_analysis(0-1)、progress_compliance(0-1)、progress_report(0-1)、extracted_clause_count、checkpointer_token、celery_task_id | Document N:1 |
| **ReviewTask** | AI 审核执行任务 | 23 字段：id、document_id(FK)、status(5 审核状态)、thread_id(LangGraph)、4 Agent 进度字段、high/medium/low_risk_count、completed_clause_count、total_clause_count、is_partial_success、checkpoint_id | Document N:1、InterruptSession 1:N |
| **StateTransition** | 不可篡改的状态流转日志 | 13 字段：id、document_id(FK)、from_status、to_status、trigger_reason、operator_type(human/system/agent)、operator_id、timestamp、metadata(JSONB)、prev_entry_hash、entry_hash(链式SHA-256) | Document N:1 |

### 3.2 Teammate 2：审核规则与解释模型

| 模型 | 业务含义 | 关键字段 | 关系 |
|------|---------|---------|------|
| **Clause** | 从文档中提取的结构化条款单元 | 14 字段：id、document_id(FK)、clause_type(10 NDA 类型枚举)、clause_text、extraction_confidence、page_number、paragraph_number、char_offset_start/end、text_hash、source(AI/MANUAL) | Document N:1、ClauseLocation 1:1、RiskFlag 1:N |
| **RiskFlag** | AI 对条款的风险判定（核心模型） | 25 字段：id、clause_id(FK)、document_id(FK)、risk_level(HIGH/MEDIUM/LOW)、risk_category(15 类)、ai_confidence、status(14 状态)、source(AI_GENERATED/MANUALLY_ADDED)、**rationale_text**(解释性)、**playbook_diff_text**(解释性)、**regulation_reference**(解释性)、**suggested_wording**(解释性)、escalated、sampled、reviewed_by、locked_by(v2) | Clause N:1、PlaybookMatch 1:1、ReviewDecision 1:N、ExplanationChain 1:1 |
| **PlaybookRule** | 企业自定义审阅标准 | 12 字段：id、name、applicable_doc_type(NDA)、risk_level、risk_category、standard_clause_text、rule_logic_description、is_active、version | PlaybookMatch 1:N |
| **PlaybookMatch** | 条款与规则的匹配详情 | 7 字段：id、risk_flag_id(FK)、playbook_rule_id(FK)、match_type(EXACT/SEMANTIC/PARTIAL/NO_MATCH)、similarity_score、diff_items(JSONB) | RiskFlag N:1、PlaybookRule N:1 |
| **ClauseLocation** | 条款在文档中的精确定位 | 12 字段：id、clause_id(FK)、page_number、paragraph_number、line_number_start/end、char_offset_start/end、bounding_box(JSON)、text_hash | Clause 1:1 |
| **ExplanationChain** | AI 判定的完整解释链路 | 5 字段：id、risk_flag_id(FK)、explanation_steps(JSONB：step_order + source_type(PLAYBOOK/REGULATION/MODEL/BENCHMARK) + source_reference + explanation_text + confidence_contribution)、total_confidence | RiskFlag 1:1 |

### 3.3 Teammate 3：HITL 交互模型

| 模型 | 业务含义 | 关键字段 | 关系 |
|------|---------|---------|------|
| **ReviewDecision** | 人类审核员的单次裁定 | ~20 字段：decision_id、risk_flag_id(FK)、decision_type(APPROVE/EDIT/REJECT/MANUAL_ADD/BATCH_CONFIRM/ESCALATE)、reviewer_id、timestamp、[EDIT 条件字段]modified_risk_level/risk_category/suggestion、[REJECT 条件字段]reject_reason(≥10字符)、[MANUAL_ADD 条件字段]clause_location/manual_risk_level/manual_risk_category/description、is_finalized、version(乐观锁) | RiskFlag N:1、AuditLog 1:N |
| **AuditLog** | 不可篡改的哈希链式审计日志 | ~15 字段：log_id、timestamp、operation_type(26 枚举)、user_id、agent_name、document_id/clause_id/risk_flag_id/decision_id(实体引用)、before_snapshot(JSON)、after_snapshot(JSON)、prev_hash、current_hash(SHA-256 链式) | Document N:1 |
| **ReviewReport** | 一次完整审阅的汇总输出 | ~15 字段：report_id、document_id(FK)、generated_at、sign_status、high_confirmed/amended/rejected、medium_auto_passed/reviewed、low_auto_passed/spot_checked、manual_added、last_exported_at | Document 1:1 |
| **InterruptSession** | LangGraph interrupt 会话记录 | ~12 字段：interrupt_id、interrupt_point(IP-1/IP-2/IP-3)、status(waiting/resolved/timeout)、thread_id(LangGraph)、checkpoint_id、interrupt_payload(JSON)、resume_payload(JSON)、created_at、resumed_at、timeout_at | Document N:1 |
| **ApprovalProgress** | 前端审批进度追踪聚合 | ~8 字段：total_high_risk、approved_high_risk、total_medium_risk、reviewed_medium_risk、low_risk_sample_checked、completion_rate_pct(%) | 派生视图（非存储表） |

---

## 四、前端必须展示的字段（按页面归属）

> **来源**: 三份模型文档中每个字段的「前端展示」标注 + `frontend_design_spec-v1.0.md` 7 页面

| 页面 | 前端必须展示的关键字段 |
|------|---------------------|
| **P1 Dashboard** | Document.status、Document.document_type、Document.uploaded_at、ReviewTask.high/medium/low_risk_count(聚合)、ApprovalProgress.completion_rate_pct |
| **P2 上传配置** | Document.original_filename、Document.title、Document.document_type、Document.format；UploadTask.status、UploadTask.format_validation_passed、UploadTask.encryption_detected、UploadTask.ocr_detected |
| **P3 解析进度** | ParseTask.status、ParseTask.progress_clause_extraction/risk_analysis/compliance/report(4 维度)、ParseTask.extracted_clause_count、ParseTask.error_message |
| **P4 AI 审核** | ReviewTask.status、ReviewTask 4 Agent 进度、ReviewTask.high/medium/low_risk_count、ReviewTask.completed_clause_count/total_clause_count、ReviewTask.is_partial_success |
| **P5 审阅工作台** | **左面板**: Clause.clause_text、ClauseLocation(全部字段)、Document 原文文件。**右面板**: RiskFlag(全部 25 字段)、PlaybookRule.standard_clause_text、PlaybookMatch.diff_items、ExplanationChain.explanation_steps、ReviewDecision(历史列表)。**操作**: approve/edit/reject/submit |
| **P6 报告预览** | ReviewReport(全部聚合字段)、AuditLog(时间线)、RiskFlag 最终状态、ReviewDecision 裁定类型+时间 |
| **P7 历史列表** | Document.title、Document.document_type、Document.status、ReviewTask.high/medium/low_risk_count(摘要)、Document.uploaded_at |

---

## 五、后端必须存储的字段（按模型归属）

> **来源**: 三份模型文档中每个字段的「后端存储」标注（全部 ✅）

### 5.1 后端存储策略

| 字段类别 | 存储方式 | 示例模型 |
|---------|---------|---------|
| 标量字段 | PostgreSQL 列 | Document.title、RiskFlag.ai_confidence、Clause.page_number |
| JSON 聚合字段 | PostgreSQL JSONB | PlaybookMatch.diff_items、ExplanationChain.explanation_steps、InterruptSession.interrupt_payload |
| 大文本字段 | PostgreSQL TEXT | Clause.clause_text、RiskFlag.rationale_text、ReviewDecision.reject_reason |
| 文件二进制 | MinIO / S3 对象存储 | Document 原文文件 (PDF/DOCX) |
| 不可变日志 | PostgreSQL (append-only table) | AuditLog、StateTransition（链式哈希） |
| LangGraph 状态 | Checkpointer (AsyncPostgresSaver) | StateGraph checkpoint（thread_id 索引） |
| 派生聚合 | 实时计算 或 物化视图 | ApprovalProgress |

### 5.2 后端必须存储的核心枚举

| 枚举 | 值 |
|------|-----|
| Document.status | CREATED / UPLOADED / PARSING / PARSED / REVIEWING / REVIEWED / HUMAN_REVIEW / COMPLETED / FAILED / CANCELLED |
| Clause.clause_type | 保密义务 / 保密期限 / 例外情形 / 违约救济 / 存续条款 / 管辖法律 / 争议解决 / 通知条款 / 可转让性 / 完整协议 |
| RiskFlag.risk_level | HIGH / MEDIUM / LOW |
| RiskFlag.status | PENDING_REVIEW / CONFIRMED / AMENDED / REJECTED / UNREVIEWED_AUTO_PASSED / ESCALATED_TO_HIGH / ... (14 状态) |
| ReviewDecision.decision_type | APPROVE / EDIT / REJECT / MANUAL_ADD / BATCH_CONFIRM / ESCALATE |
| AuditLog.operation_type | 26 种操作类型（UPLOAD → REPORT_SIGNED） |

---

## 六、模型关系总图（ERM）

```
Document 1──N Clause 1──N RiskFlag 1──1 PlaybookMatch N──1 PlaybookRule
    │            │             │
    │ 1:1        │ 1:1         │ 1:N
    ▼            ▼             ▼
ParseTask   ClauseLocation  ReviewDecision
    │                           │
    │ 1:1                       │ 1:N
    ▼                           ▼
ReviewTask ──1:N── InterruptSession
    │
    │ 1:N
    ▼
StateTransition

Document 1──N AuditLog
Document 1──1 ReviewReport

ApprovalProgress (派生视图, not stored)
```

---

## 七、Lead 审批记录

| 时间 | 事件 | 决议 |
|------|------|------|
| 2026-07-30 | Teammate 1 提交文档+任务模型计划 | ✅ 批准（5 模型 / 92 字段） |
| 2026-07-30 | Teammate 2 提交审核+解释模型计划 | ✅ 批准（6 模型 / 75 字段） |
| 2026-07-30 | Teammate 3 提交 HITL 交互模型计划 | ✅ 批准（5 模型 / 80 字段） |
| 2026-07-30 | Teammate 1 完成 | ✅ `document_task_models-v1.0.md`（770 行） |
| 2026-07-30 | Teammate 2 完成 | ✅ `review_analysis_models-v1.0.md`（817 行） |
| 2026-07-30 | Teammate 3 完成 | ✅ `hitl_interaction_models-v1.0.md`（1,021 行） |
| 2026-07-30 | Lead 汇总 | ✅ 本文件（`data_model_spec-v1.0.md`） |

---

> **上游文档**:
> - `../03_business_modeling/business_model.md` — 业务实体定义
> - `../04_interaction_design/langchain_hitl_arch-v1.0.md` — HITL 架构规范
> - `./backend_service_arch-v1.0.md` — 后端服务架构
> - `./langchain_hitl_workflow-v1.0.md` — LangChain HITL 工作流
> - `./frontend_backend_boundary_spec-v1.0.md` — 前后端边界规范
> **下游文档**:
> - `../08_api_specification/` — API 规范
> - `../09_frontend_plan/` — 前端实现计划
> - `../10_backend_plan/` — 后端实现计划
