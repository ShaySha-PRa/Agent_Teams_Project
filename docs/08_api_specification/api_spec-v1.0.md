# API 接口规范 v1.0

> **版本**: v1.0
> **创建日期**: 2026-07-30
> **文档性质**: 收口规范 — 严格基于上游数据模型、HITL 架构、业务建模、状态流转
> **上游依赖**:
> - `docs/03_business_modeling/business_model.md` — MVP 范围、业务实体、分级告警
> - `docs/04_interaction_design/flow_state_spec.md` — 三阶段 54 节点、状态流转
> - `docs/04_interaction_design/langchain_hitl_arch-v1.0.md` — 3 中断点、8 操作映射、SSE 事件
> - `docs/06_system_architecture/data_model_spec-v1.0.md` — 16 模型、字段定义、枚举全集
> **下游读者**: 前端实现计划、后端实现计划、联调

---

## 目录

1. [接口总览](#一接口总览)
2. [通用规范](#二通用规范)
3. [文档上传接口组](#三文档上传接口组)
4. [审核查询接口组](#四审核查询接口组)
5. [人工审核接口组](#五人工审核接口组)
6. [报告与导出接口组](#六报告与导出接口组)
7. [SSE 实时事件接口](#七sse-实时事件接口)
8. [前后端联调接入顺序](#八前后端联调接入顺序)

---

## 一、接口总览

> **来源**: `data_model_spec-v1.0.md` 16 模型关系 + `langchain_hitl_arch-v1.0.md` §5.1 8 操作映射

| # | 方法 | 路径 | 接口组 | 所属阶段 |
|:--:|------|------|--------|:--:|
| 1 | `GET` | `/dashboard/stats` | 查询 | — |
| 2 | `POST` | `/documents/upload` | 上传 | 阶段 1 |
| 3 | `GET` | `/documents` | 查询 | — |
| 4 | `GET` | `/documents/{id}` | 查询 | 阶段 1 |
| 5 | `GET` | `/documents/{id}/file` | 上传 | 阶段 1 |
| 6 | `POST` | `/documents/{id}/parse` | 上传 | 阶段 1 |
| 7 | `POST` | `/documents/{id}/parse/retry` | 上传 | 阶段 1 |
| 8 | `GET` | `/documents/{id}/events` | SSE | 阶段 1-3 |
| 9 | `POST` | `/documents/{id}/review` | 审核 | 阶段 2 |
| 10 | `POST` | `/documents/{id}/review/pause` | 审核 | 阶段 2 |
| 11 | `POST` | `/documents/{id}/review/resume` | 审核 | 阶段 2 |
| 12 | `POST` | `/documents/{id}/review/cancel` | 审核 | 阶段 2 |
| 13 | `POST` | `/documents/{id}/review/retry` | 审核 | 阶段 2 |
| 14 | `GET` | `/documents/{id}/clauses` | 查询 | 阶段 2 |
| 15 | `GET` | `/documents/{id}/risk-flags` | 查询 | 阶段 2-3 |
| 16 | `GET` | `/risk-flags/{id}/playbook-diff` | 查询 | 阶段 3 |
| 17 | `GET` | `/risk-flags/{id}/decisions` | 查询 | 阶段 3 |
| 18 | `POST` | `/risk-flags/{id}/approve` | **人工审核** | 阶段 3 |
| 19 | `POST` | `/risk-flags/{id}/edit` | **人工审核** | 阶段 3 |
| 20 | `POST` | `/risk-flags/{id}/reject` | **人工审核** | 阶段 3 |
| 21 | `POST` | `/risk-flags/batch-approve` | **人工审核** | 阶段 3 |
| 22 | `POST` | `/risk-flags/sample` | **人工审核** | 阶段 3 |
| 23 | `POST` | `/risk-flags/{id}/escalate` | **人工审核** | 阶段 3 |
| 24 | `POST` | `/risk-flags/manual` | **人工审核** | 阶段 3 |
| 25 | `GET` | `/documents/{id}/review-summary` | 查询 | 阶段 3 |
| 26 | `POST` | `/documents/{id}/submit` | **人工审核** | 阶段 3 |
| 27 | `POST` | `/documents/{id}/save-draft` | **人工审核** | 阶段 3 |
| 28 | `GET` | `/documents/{id}/audit-logs` | 查询 | 阶段 3 |
| 29 | `GET` | `/documents/{id}/report` | 报告 | 阶段 3 |
| 30 | `GET` | `/documents/{id}/report/export` | 报告 | 阶段 3 |
| 31 | `POST` | `/documents/{id}/report/sign` | 报告 | 阶段 3 |
| 32 | `GET` | `/playbooks` | 查询 | 阶段 1 |

---

## 二、通用规范

### 2.1 基础信息

| 项 | 值 |
|------|-----|
| Base URL | `/api/v1` |
| 认证方式 | `Authorization: Bearer <JWT>` |
| Content-Type | `application/json`（上传除外） |
| 字符编码 | UTF-8 |

### 2.2 通用响应格式

```json
{
  "code": 0,
  "message": "success",
  "data": { },
  "request_id": "uuid"
}
```

### 2.3 通用错误码

| HTTP 状态码 | code | 含义 |
|:--------:|------|------|
| 400 | `INVALID_PARAMS` | 请求参数校验失败 |
| 401 | `UNAUTHORIZED` | 未认证或 Token 过期 |
| 403 | `FORBIDDEN` | 无权限 |
| 404 | `NOT_FOUND` | 资源不存在 |
| 409 | `CONFLICT` | 状态冲突（如高风险审批未完成时提交） |
| 422 | `VALIDATION_FAILED` | 业务校验失败（如 reject_reason < 10 字符） |
| 429 | `RATE_LIMITED` | 请求过于频繁 |
| 500 | `INTERNAL_ERROR` | 服务器内部错误 |
| 503 | `SERVICE_UNAVAILABLE` | AI Agent 服务不可用 |

### 2.4 分页参数

```json
{
  "page": 1,
  "size": 20,
  "total": 150,
  "items": []
}
```

---

## 三、文档上传接口组

> **来源**: `data_model_spec-v1.0.md` §3.1 Document/UploadTask/ParseTask 模型 + `flow_state_spec.md` §3.1 阶段 1

### 3.1 上传文档

```
POST /documents/upload
Content-Type: multipart/form-data
```

**请求**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|:--:|------|
| `file` | file(binary) | ✅ | 合同文件（仅 PDF/DOCX） |
| `title` | string | ❌ | 文档标题，默认取文件名 |
| `document_type` | string | ❌ | MVP 固定 `"NDA"` |

**后端处理流程** (5 层校验链):
1. 客户端格式预检 (前端 MIME type)
2. 服务端 magic byte 校验 (PDF: `%PDF-`, DOCX: `PK\x03\x04`)
3. 加密检测
4. 损坏检测
5. OCR 检测

**成功响应** `201`:

```json
{
  "code": 0,
  "data": {
    "document_id": "d_abc123",
    "original_filename": "NDA-供应商-2026.pdf",
    "title": "NDA-供应商-2026",
    "document_type": "NDA",
    "format": "PDF",
    "file_size_bytes": 245760,
    "page_count": 8,
    "status": "UPLOADED",
    "uploaded_at": "2026-07-30T10:15:00Z",
    "md5_hash": "d41d8cd98f00b204e9800998ecf8427e",
    "ocr_status": "NOT_NEEDED",
    "encryption_status": "NONE"
  },
  "request_id": "req_xyz"
}
```

**错误响应**:

| 场景 | HTTP | code | 说明 |
|------|:--:|------|------|
| 格式不支持 | 422 | `UNSUPPORTED_FORMAT` | 仅支持 PDF/DOCX |
| 文件加密 | 422 | `FILE_ENCRYPTED` | 请解除保护后重试 |
| 文件损坏 | 422 | `FILE_CORRUPTED` | 请重新导出 PDF |
| 文件过大 | 422 | `FILE_TOO_LARGE` | 最大 50MB |
| 页数超限 | 422 | `PAGE_LIMIT_EXCEEDED` | 最大 200 页 |

### 3.2 获取文档信息

```
GET /documents/{id}
```

**成功响应** `200`:

```json
{
  "code": 0,
  "data": {
    "document_id": "d_abc123",
    "original_filename": "NDA-供应商-2026.pdf",
    "title": "NDA-供应商-2026",
    "document_type": "NDA",
    "format": "PDF",
    "file_size_bytes": 245760,
    "page_count": 8,
    "status": "PARSED",
    "uploaded_at": "2026-07-30T10:15:00Z",
    "md5_hash": "d41d8cd98f00b204e9800998ecf8427e",
    "ocr_status": "NOT_NEEDED",
    "encryption_status": "NONE",
    "parse_task": {
      "parse_task_id": "pt_001",
      "status": "completed",
      "extracted_clause_count": 12
    }
  },
  "request_id": "req_xyz"
}
```

### 3.3 获取文档原文文件

```
GET /documents/{id}/file
```

**响应**: `200` — `Content-Type: application/pdf` 或 `application/vnd.openxmlformats-officedocument.wordprocessingml.document`

### 3.4 启动解析

```
POST /documents/{id}/parse
```

**请求**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|:--:|------|
| `playbook_id` | string | ❌ | Playbook ID，默认 NDA Standard |
| `ocr_mode` | string | ❌ | `"immediate"` / `"background"`，默认 `"immediate"` |

**成功响应** `202`:

```json
{
  "code": 0,
  "data": {
    "document_id": "d_abc123",
    "parse_task_id": "pt_001",
    "status": "queued",
    "message": "解析任务已入队"
  },
  "request_id": "req_xyz"
}
```

### 3.5 重试解析

```
POST /documents/{id}/parse/retry
```

**前置条件**: `status = FAILED` 且 `recoverable = true`

**成功响应** `202`: 同 3.4

### 3.6 文档列表

```
GET /documents?status=PARSED&page=1&size=20
```

**响应** `200`:

```json
{
  "code": 0,
  "data": {
    "page": 1,
    "size": 20,
    "total": 42,
    "items": [
      {
        "document_id": "d_abc123",
        "title": "NDA-供应商-2026",
        "document_type": "NDA",
        "status": "PARSED",
        "uploaded_at": "2026-07-30T10:15:00Z",
        "risk_summary": { "high": 3, "medium": 5, "low": 4 }
      }
    ]
  },
  "request_id": "req_xyz"
}
```

---

## 四、审核查询接口组

> **来源**: `data_model_spec-v1.0.md` §3.2 Clause/RiskFlag/PlaybookMatch/ExplanationChain 模型 + `langchain_hitl_arch-v1.0.md` §四 StateGraph

### 4.1 启动 AI 审核

```
POST /documents/{id}/review
```

**前置条件**: `status = PARSED`

**成功响应** `202`:

```json
{
  "code": 0,
  "data": {
    "document_id": "d_abc123",
    "review_task_id": "rt_001",
    "status": "REVIEWING",
    "thread_id": "lg_thread_xyz",
    "message": "AI 审核已启动，4 Agent 并行执行中"
  },
  "request_id": "req_xyz"
}
```

### 4.2 审核控制（暂停/恢复/取消/重试）

| 操作 | 方法+路径 | 前置状态 | 说明 |
|------|---------|---------|------|
| 暂停 | `POST /documents/{id}/review/pause` | REVIEWING | 下一个 safe-point 暂停并 save checkpoint |
| 恢复 | `POST /documents/{id}/review/resume` | REVIEWING(暂停中) | 从 checkpoint 恢复 |
| 取消 | `POST /documents/{id}/review/cancel` | REVIEWING | 终止并标记 CANCELLED |
| 重试 | `POST /documents/{id}/review/retry` | FAILED | 从 checkpoint 恢复重试 |

**响应**: `200` — 返回更新后的 ReviewTask 状态

### 4.3 获取条款列表

```
GET /documents/{id}/clauses
```

**响应** `200`:

```json
{
  "code": 0,
  "data": {
    "clauses": [
      {
        "clause_id": "cl_001",
        "clause_type": "保密义务",
        "clause_text": "接收方同意对披露方的保密信息予以严格保密...",
        "extraction_confidence": 0.95,
        "location": {
          "page_number": 3,
          "paragraph_number": 2,
          "char_offset_start": 1240,
          "char_offset_end": 1580,
          "text_hash": "a1b2c3"
        }
      }
    ]
  },
  "request_id": "req_xyz"
}
```

### 4.4 获取风险标记列表

```
GET /documents/{id}/risk-flags?level=HIGH&status=PENDING_REVIEW
```

**响应** `200`:

```json
{
  "code": 0,
  "data": {
    "risk_flags": [
      {
        "risk_flag_id": "rf_001",
        "clause_id": "cl_003",
        "risk_level": "HIGH",
        "risk_category": "合规风险",
        "ai_confidence": 0.87,
        "status": "PENDING_REVIEW",
        "source": "AI_GENERATED",
        "rationale_text": "保密期限为'永久'，超过行业标准的 3-5 年...",
        "playbook_diff_text": "标准条款: 保密期限不超过 5 年\n实际条款: 保密义务在协议终止后永久有效",
        "regulation_reference": "参照《商业秘密保护规定》第 12 条，保密期限应合理...",
        "suggested_wording": "建议修改为: 保密义务自披露之日起 5 年内有效",
        "clause_location": {
          "page_number": 3,
          "char_offset_start": 1240,
          "char_offset_end": 1580
        }
      }
    ]
  },
  "request_id": "req_xyz"
}
```

**查询参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `level` | string | HIGH / MEDIUM / LOW |
| `status` | string | 14 状态枚举 |
| `category` | string | 15 风险类别枚举 |
| `source` | string | AI_GENERATED / MANUALLY_ADDED |

### 4.5 获取 Playbook 对比

```
GET /risk-flags/{id}/playbook-diff
```

**响应** `200`:

```json
{
  "code": 0,
  "data": {
    "risk_flag_id": "rf_001",
    "playbook_rule": {
      "playbook_rule_id": "pr_001",
      "name": "NDA-保密期限",
      "standard_clause_text": "保密义务自披露之日起 3 年内有效",
      "risk_level": "HIGH",
      "risk_category": "合规风险"
    },
    "match": {
      "match_type": "PARTIAL",
      "similarity_score": 0.42,
      "diff_items": [
        {
          "field": "保密期限",
          "standard_value": "3 年",
          "actual_value": "永久",
          "deviation_type": "MISMATCHED"
        }
      ]
    }
  },
  "request_id": "req_xyz"
}
```

### 4.6 获取审批历史

```
GET /risk-flags/{id}/decisions
```

**响应** `200`:

```json
{
  "code": 0,
  "data": {
    "risk_flag_id": "rf_001",
    "decisions": [
      {
        "decision_id": "d_001",
        "decision_type": "EDIT",
        "reviewer_id": "user_001",
        "timestamp": "2026-07-30T10:35:00Z",
        "comment": "风险等级从 HIGH 降为 MEDIUM，保密期限可协商",
        "modified_risk_level": "MEDIUM"
      }
    ]
  },
  "request_id": "req_xyz"
}
```

### 4.7 审批进度摘要

```
GET /documents/{id}/review-summary
```

**响应** `200`:

```json
{
  "code": 0,
  "data": {
    "document_id": "d_abc123",
    "total_high_risk": 3,
    "approved_high_risk": 2,
    "total_medium_risk": 5,
    "reviewed_medium_risk": 1,
    "low_risk_auto_passed": 4,
    "manual_added": 1,
    "completion_rate_pct": 60.0,
    "all_high_risk_resolved": false
  },
  "request_id": "req_xyz"
}
```

**关键字段 `all_high_risk_resolved`**: 前端提交按钮的启用条件。仅当此字段为 `true` 时，P5 页面的"提交审阅"按钮可点击。

---

## 五、人工审核接口组

> **来源**: `langchain_hitl_arch-v1.0.md` §5.1 8 操作映射 + `data_model_spec-v1.0.md` §3.3 ReviewDecision/AuditLog/InterruptSession 模型

### 5.1 Approve — 同意 AI 标记

```
POST /risk-flags/{id}/approve
```

**请求**:

```json
{
  "comment": "确认，该条款确实存在风险"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|:--:|------|
| `comment` | string | ❌ | 可选备注 |

**后端处理**:
1. 更新 `RiskFlag.status` → `CONFIRMED`
2. 写入 `ReviewDecision` (decision_type=APPROVE)
3. 写入 `AuditLog` (operation_type=HUMAN_APPROVE)
4. 写入 `StateTransition`（如影响文档状态）
5. 通过 LangGraph `Command(resume={"decision": "approve"})` 恢复 IP-1

**成功响应** `200`:

```json
{
  "code": 0,
  "data": {
    "risk_flag_id": "rf_001",
    "status": "CONFIRMED",
    "decision_id": "d_002",
    "updated_review_summary": { "approved_high_risk": 3, "all_high_risk_resolved": true }
  },
  "request_id": "req_xyz"
}
```

### 5.2 Edit — 修正 AI 标记

```
POST /risk-flags/{id}/edit
```

**请求**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|:--:|------|
| `comment` | string | ✅ | 修改原因（≥10 字符） |
| `modified_risk_level` | string | ❌ | 修改后的风险等级 |
| `modified_risk_category` | string | ❌ | 修改后的风险类别 |
| `modified_suggestion` | string | ❌ | 修改后的建议措辞 |

```json
{
  "comment": "风险等级从 HIGH 降为 MEDIUM，保密期限可协商为 5 年",
  "modified_risk_level": "MEDIUM"
}
```

**降级规则** (`data_model_spec-v1.0.md` Teammate 3):
- HIGH → MEDIUM: ✅ 允许
- HIGH → LOW: ✅ 允许（需在 comment 中充分说明理由）
- MEDIUM → HIGH: 使用 escalate 接口（见 5.6）

**后端处理**:
1. 更新 `RiskFlag.status` → `AMENDED` + 保存修改字段
2. 写入 `ReviewDecision` (decision_type=EDIT)
3. 写入 `AuditLog` (operation_type=HUMAN_EDIT)
4. 通过 LangGraph `Command(resume={"decision": "edit", "modified_fields": {...}})` 恢复 IP-1

**成功响应** `200`:

```json
{
  "code": 0,
  "data": {
    "risk_flag_id": "rf_001",
    "status": "AMENDED",
    "modified_risk_level": "MEDIUM",
    "decision_id": "d_003",
    "updated_review_summary": { "approved_high_risk": 2, "all_high_risk_resolved": true }
  },
  "request_id": "req_xyz"
}
```

### 5.3 Reject — 驳回 AI 标记

```
POST /risk-flags/{id}/reject
```

**请求**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|:--:|------|
| `reject_reason` | string | ✅ | 驳回原因（**≥10 字符**） |

```json
{
  "reject_reason": "该条款为行业标准表述，不构成实质性风险"
}
```

**后端校验**: `reject_reason.length < 10` → `422 VALIDATION_FAILED`

**后端处理**:
1. 更新 `RiskFlag.status` → `REJECTED`
2. 写入 `ReviewDecision` (decision_type=REJECT)
3. 写入 `AuditLog` (operation_type=HUMAN_REJECT)
4. 通过 LangGraph `Command(resume={"decision": "reject", "comment": str})` 恢复 IP-1

**成功响应** `200`:

```json
{
  "code": 0,
  "data": {
    "risk_flag_id": "rf_001",
    "status": "REJECTED",
    "decision_id": "d_004",
    "message": "该风险标记已移除"
  },
  "request_id": "req_xyz"
}
```

### 5.4 Batch Approve — 中风险批量确认

```
POST /risk-flags/batch-approve
```

**请求**:

```json
{
  "document_id": "d_abc123",
  "risk_flag_ids": ["rf_010", "rf_011", "rf_012", "rf_013", "rf_014"]
}
```

**后端处理**:
1. 批量更新所有中风险 `RiskFlag.status` → `UNREVIEWED_AUTO_PASSED`
2. 写入 1 条 `ReviewDecision` (decision_type=BATCH_CONFIRM, 含所有 IDs)
3. 写入 `AuditLog` (operation_type=BATCH_CONFIRM)
4. 通过 LangGraph `Command(resume={"type": "batch_confirm", "items": [...]})` 恢复 IP-2

**成功响应** `200`:

```json
{
  "code": 0,
  "data": {
    "batch_approved_count": 5,
    "updated_review_summary": { "reviewed_medium_risk": 5 }
  },
  "request_id": "req_xyz"
}
```

### 5.5 Spot Check — 低风险抽样审计

```
POST /risk-flags/sample
```

**请求**:

```json
{
  "document_id": "d_abc123",
  "sample_ratio": 0.11
}
```

**后端处理**:
- 使用**确定性种子** (document_id + user_id) 抽取 N% 低风险 RiskFlag
- 返回被抽中的 RiskFlag 列表供审查
- 前端渲染抽样审计面板

**成功响应** `200`:

```json
{
  "code": 0,
  "data": {
    "sampled_risk_flags": [
      {
        "risk_flag_id": "rf_020",
        "risk_level": "LOW",
        "risk_category": "通知条款",
        "ai_confidence": 0.92,
        "status": "UNREVIEWED_AUTO_PASSED",
        "clause_text": "任何通知应以书面形式发送...",
        "rationale_text": "通知条款格式标准，无明显风险"
      }
    ],
    "sample_size": 1,
    "total_low_risk": 4,
    "seed_info": "sha256(d_abc123_user_001)[:8]"
  },
  "request_id": "req_xyz"
}
```

### 5.6 Escalate — 升级风险等级

```
POST /risk-flags/{id}/escalate
```

**请求**:

```json
{
  "new_level": "HIGH",
  "reason": "抽样审计发现该条款实际存在较高风险"
}
```

**后端处理**:
1. 更新 `RiskFlag.risk_level` → `HIGH`（**不可逆**）
2. 更新 `RiskFlag.status` → `ESCALATED_TO_HIGH`
3. 将该 RiskFlag 加入高风险审批队列
4. 写入 `ReviewDecision` (decision_type=ESCALATE)
5. 写入 `AuditLog` (operation_type=SPOT_CHECK_ESCALATE)

**成功响应** `200`:

```json
{
  "code": 0,
  "data": {
    "risk_flag_id": "rf_020",
    "new_level": "HIGH",
    "status": "ESCALATED_TO_HIGH",
    "message": "已升级为高风险，需强制人工审批"
  },
  "request_id": "req_xyz"
}
```

### 5.7 Manual Add — 手动补充标记

```
POST /risk-flags/manual
```

**请求**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|:--:|------|
| `document_id` | string | ✅ | 所属文档 |
| `clause_location` | object | ✅ | 划选位置（ClauseLocation 结构） |
| `risk_level` | string | ✅ | 手动设置的风险等级 |
| `risk_category` | string | ✅ | 手动选择的风险类别 |
| `description` | string | ✅ | 说明文本（≥10 字符） |
| `clause_text` | string | ❌ | 划选区域的原文文本 |

```json
{
  "document_id": "d_abc123",
  "clause_location": {
    "page_number": 5,
    "paragraph_number": 3,
    "char_offset_start": 2100,
    "char_offset_end": 2350,
    "text_hash": "e5f6g7"
  },
  "risk_level": "HIGH",
  "risk_category": "财务风险",
  "description": "赔偿上限条款使用了模糊的'合理费用'表述，可能导致争议",
  "clause_text": "违约方应赔偿守约方因此产生的合理费用..."
}
```

**后端处理**:
1. 创建 `RiskFlag` (source=MANUALLY_ADDED, status=PENDING_REVIEW)
2. 创建 `Clause` (source=MANUAL)
3. 写入 `ReviewDecision` (decision_type=MANUAL_ADD)
4. 写入 `AuditLog` (operation_type=MANUAL_ADD)
5. 加入高风险审批队列（MVP 单人场景直接生效）
6. **不通过 interrupt** — 直接写入 State

**成功响应** `201`:

```json
{
  "code": 0,
  "data": {
    "risk_flag_id": "rf_030",
    "clause_id": "cl_015",
    "risk_level": "HIGH",
    "status": "PENDING_REVIEW",
    "source": "MANUALLY_ADDED"
  },
  "request_id": "req_xyz"
}
```

### 5.8 Final Submit — 提交审阅

```
POST /documents/{id}/submit
```

**前置条件**: `all_high_risk_resolved = true`（所有高风险项已审批完成）

**前置校验（4 层约束中的第 2 层）**:
- API 层校验高风险审批完整性
- 不完整 → `409 CONFLICT` — `"仍有 {N} 项高风险条款待审批"`

**请求**:

```json
{
  "comment": "审阅完成，提交最终报告"
}
```

**后端处理**:
1. 更新 `Document.status` → `COMPLETED`
2. 生成 `ReviewReport`（聚合所有 RiskFlag 最终状态 + ReviewDecision）
3. 写入 `AuditLog` (operation_type=FINAL_SUBMIT)
4. 通过 LangGraph `Command(resume={"action": "confirm_submit"})` 恢复 IP-3
5. 触发报告 Agent 生成最终 PDF 报告

**成功响应** `200`:

```json
{
  "code": 0,
  "data": {
    "document_id": "d_abc123",
    "status": "COMPLETED",
    "report_id": "rpt_001",
    "message": "审阅已提交，报告生成中"
  },
  "request_id": "req_xyz"
}
```

### 5.9 Save Draft — 暂存草稿

```
POST /documents/{id}/save-draft
```

**任意状态可调用**。保存当前所有审批状态，`Document.status` 不变。

---

## 六、报告与导出接口组

> **来源**: `data_model_spec-v1.0.md` §3.3 ReviewReport/AuditLog 模型

### 6.1 获取审阅报告

```
GET /documents/{id}/report
```

**响应** `200`:

```json
{
  "code": 0,
  "data": {
    "report_id": "rpt_001",
    "document_id": "d_abc123",
    "generated_at": "2026-07-30T10:45:00Z",
    "sign_status": "UNSIGNED",
    "risk_aggregation": {
      "high_confirmed": 2,
      "high_amended": 1,
      "high_rejected": 0,
      "medium_auto_passed": 4,
      "medium_reviewed": 1,
      "low_auto_passed": 3,
      "low_spot_checked": 1,
      "manual_added": 1
    },
    "high_risk_details": [
      {
        "risk_flag_id": "rf_001",
        "clause_type": "保密期限",
        "risk_category": "合规风险",
        "ai_confidence": 0.87,
        "final_status": "CONFIRMED",
        "final_decision": "APPROVE",
        "reviewer_id": "user_001"
      }
    ],
    "audit_timeline": []
  },
  "request_id": "req_xyz"
}
```

### 6.2 导出 PDF 报告

```
GET /documents/{id}/report/export?format=pdf
```

**响应**: `200` — `Content-Type: application/pdf` + `Content-Disposition: attachment`

### 6.3 签署报告

```
POST /documents/{id}/report/sign
```

**成功响应** `200`:

```json
{
  "code": 0,
  "data": {
    "report_id": "rpt_001",
    "sign_status": "SIGNED",
    "signer_name": "张三",
    "signed_at": "2026-07-30T11:00:00Z"
  },
  "request_id": "req_xyz"
}
```

### 6.4 获取审计日志

```
GET /documents/{id}/audit-logs?page=1&size=50
```

**响应** `200` — 按时间倒序的 AuditLog 条目列表，每项含 `prev_hash` + `current_hash` 链式验证字段。

### 6.5 Dashboard 统计

```
GET /dashboard/stats
```

**响应** `200`:

```json
{
  "code": 0,
  "data": {
    "pending_reviews": 5,
    "completed_this_week": 12,
    "avg_review_time_minutes": 18,
    "total_risks_found": 87
  },
  "request_id": "req_xyz"
}
```

### 6.6 Playbook 列表

```
GET /playbooks?doc_type=NDA
```

**响应** `200` — 可用 PlaybookRule 列表（摘要字段：id, name, applicable_doc_type, risk_level）

---

## 七、SSE 实时事件接口

> **来源**: `langchain_hitl_arch-v1.0.md` §6.3 SSE 事件类型

### 7.1 连接事件流

```
GET /documents/{id}/events
Accept: text/event-stream
```

**连接建立** `200`:

```
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive
```

### 7.2 事件类型定义

| event | data 结构 | 触发时机 | 前端处理 |
|-------|----------|---------|---------|
| `parse.progress` | `{"agent_name":"clause_extraction","progress_pct":0.6,"current_clause_type":"保密义务"}` | 解析进行中 | P3 更新进度条 |
| `parse.complete` | `{"document_id":"d_abc123","clause_count":12}` | 解析完成 | P3→P4 自动跳转 |
| `parse.failed` | `{"error_type":"CORRUPTED","error_message":"...","recoverable":false}` | 解析失败 | P3 显示失败面板 |
| `review.progress` | `{"agent_name":"risk_control","clauses_processed":8,"total_clauses":20,"current_dimension":"赔偿条款"}` | 审核进行中 | P4 更新 Agent 卡片 |
| `review.log` | `{"timestamp":"10:23:22","agent_name":"risk_control","message":"发现高风险项"}` | Agent 有新发现 | P4 追加日志行 |
| `review.complete` | `{"summary":{"high":3,"medium":5,"low":4}}` | AI 审核完成 | P4→P5 跳转 |
| `review.failed` | `{"fail_category":"SERVICE_UNAVAILABLE","message":"...","partial_results_available":true}` | 审核失败 | P4 显示失败面板 |
| `review.timeout` | `{"completed_count":12,"total_count":20}` | 审核超时 | P4 显示超时面板 |
| `interrupt.ready` | `{"interrupt_id":"ip_001","interrupt_type":"IP-1","payload":{...}}` | 中断就绪 | P5 渲染审批卡片 |

### 7.3 SSE 连接生命周期

```
前端连接 SSE → 后端推送事件流 → 前端渲染
    │                                │
    │  文档状态变更 (PARSED→REVIEWING)  │
    │  AI 审核进行中 (REVIEWING)        │
    │  中断触发 (interrupt.ready)       │
    │  前端发送 POST (approve/edit/...) │
    │  后端推送下一个 interrupt.ready    │
    │  ...                             │
    │  文档状态变更 (COMPLETED)          │
    │                                  │
    └─ 前端主动断开 SSE 连接 ───────────┘
```

---

## 八、前后端联调接入顺序

> **来源**: `flow_state_spec.md` 三阶段串联 + `business_model.md` 场景间数据关系

### 8.1 联调阶段划分

```
Phase 1: 基础设施 (P1, P7)           Phase 2: 文档流转 (P2, P3)        Phase 3: AI 审核 (P4)
───────────────────────────         ───────────────────────────       ───────────────────────────
1.1 GET /dashboard/stats            2.1 POST /documents/upload        3.1 POST /documents/{id}/review
1.2 GET /documents                  2.2 GET  /documents/{id}          3.2 GET  /documents/{id}/events (SSE)
1.3 GET /playbooks                  2.3 GET  /documents/{id}/file     3.3 POST /documents/{id}/review/pause
                                    2.4 POST /documents/{id}/parse    3.4 POST /documents/{id}/review/resume
                                    2.5 GET  /documents/{id}/events   3.5 GET  /documents/{id}/clauses
                                        (SSE: parse.*)                3.6 POST /documents/{id}/review/cancel
                                    2.6 POST /documents/{id}/parse    3.7 POST /documents/{id}/review/retry
                                        /retry
                                    ✅ 里程碑: 文档解析成功            ✅ 里程碑: AI 审核完成

Phase 4: 人工审批 (P5)               Phase 5: 报告与收尾 (P6)         Phase 6: 全链路验收
───────────────────────────         ───────────────────────────       ───────────────────────────
4.1 GET  /documents/{id}/           5.1 GET  /documents/{id}/report   6.1 全流程串联:
    risk-flags                      5.2 GET  /documents/{id}/audit    上传→校验→解析→AI审核→
4.2 GET  /risk-flags/{id}/              -logs                            高风险审批→中风险批量→
    playbook-diff                   5.3 GET  /documents/{id}/report       低风险抽样→提交→报告→
4.3 GET  /risk-flags/{id}/              /export                          签署
    decisions                       5.4 POST /documents/{id}/report   6.2 异常路径测试:
4.4 POST /risk-flags/{id}/approve       /sign                            上传失败/解析失败/AI失败/
4.5 POST /risk-flags/{id}/edit      5.5 GET  /documents/{id}              部分成功/中断恢复/超时
4.6 POST /risk-flags/{id}/reject    (确认 COMPLETED 状态)
4.7 POST /risk-flags/batch-approve  ✅ 里程碑: 报告生成+签署
4.8 POST /risk-flags/sample
4.9 POST /risk-flags/{id}/escalate
4.10 POST /risk-flags/manual
4.11 GET  /documents/{id}/
     review-summary
4.12 POST /documents/{id}/submit
4.13 POST /documents/{id}/save-draft
✅ 里程碑: 人工审批完成
```

### 8.2 接口依赖关系

```
      ┌─────────────────┐
      │ POST /upload     │  ← 起点
      └────────┬────────┘
               │ document_id
               ▼
      ┌─────────────────┐
      │ POST /parse      │
      └────────┬────────┘
               │ status = PARSED
               ▼
      ┌─────────────────┐
      │ POST /review     │
      └────────┬────────┘
               │ SSE: review.complete
               ▼
      ┌─────────────────┐
      │ GET /risk-flags  │  ← 获取审批项
      └────────┬────────┘
               │
     ┌─────────┼─────────┐
     ▼         ▼         ▼
  approve   edit     reject    batch     manual   escalate
     │         │         │        │         │         │
     └─────────┴─────────┴────────┴─────────┴─────────┘
               │ all_high_risk_resolved = true
               ▼
      ┌─────────────────┐
      │ POST /submit     │
      └────────┬────────┘
               │ status = COMPLETED
               ▼
      ┌─────────────────┐
      │ GET  /report     │
      │ POST /report/sign│
      └─────────────────┘
```

### 8.3 联调检查清单

| 阶段 | 检查项 | 验收标准 |
|:--:|------|---------|
| Phase 1 | Dashboard 统计 | P1 页面渲染 4 张统计卡片 |
| Phase 2 | 文件上传 | PDF/DOCX 上传成功，格式错误被拦截 |
| Phase 2 | 5 层校验 | 加密/损坏文件正确拒绝 |
| Phase 2 | 解析流程 | SSE 推送 4 Agent 进度，P3 页面渲染 |
| Phase 3 | AI 审核启动 | SSE 推送 review.progress，P4 Agent 并行卡片更新 |
| Phase 3 | 暂停/恢复 | Checkpointer 正确保存和恢复状态 |
| Phase 4 | 高风险审批 | approve/edit/reject 正确更新 RiskFlag 状态 |
| Phase 4 | 409 拦截 | all_high_risk_resolved=false 时 submit 返回 409 |
| Phase 4 | 中风险批量 | batch_approve 正确标记 UNREVIEWED_AUTO_PASSED |
| Phase 4 | 低风险抽样 | 确定性种子抽取一致结果 |
| Phase 4 | 手动补充 | manual_add 正确创建 RiskFlag + Clause |
| Phase 5 | 报告生成 | ReviewReport 聚合数据正确 |
| Phase 5 | 审计日志 | AuditLog 链式哈希可验证 |
| Phase 6 | 全流程串联 | CREATED → COMPLETED 完整链路通过 |
| Phase 6 | 异常路径 | 6 种异常场景正确处理 |

---

> **上游文档**:
> - `../03_business_modeling/business_model.md` — 业务问题建模
> - `../04_interaction_design/flow_state_spec.md` — 状态流转规范
> - `../04_interaction_design/langchain_hitl_arch-v1.0.md` — HITL 架构规范
> - `../06_system_architecture/data_model_spec-v1.0.md` — 数据模型规范
> **下游文档**:
> - `../09_frontend_plan/` — 前端实现计划
> - `../10_backend_plan/` — 后端实现计划
> - `../11_integration/` — 联调
