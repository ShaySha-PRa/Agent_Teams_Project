# 前端架构规范 v1.0

> **版本**: v1.0
> **创建日期**: 2026-07-30
> **来源**: Teammate 1（页面结构+路由）+ Teammate 2（审核组件模块）+ Teammate 3（HITL UI 交互）
> **Lead 汇总**: 综合 3 份前端规划文档，覆盖路由架构、19 组件、9 操作交互、5,394 行

---

## 一、Agent Team 执行摘要

| Teammate | 输出文件 | 规模 | 覆盖 |
|----------|---------|:--:|------|
| Teammate 1 | `page_structure_routing-v1.0.md` | 1,281 行 | 9 路由 + P1-P4 + 全局组件 |
| Teammate 2 | `review_components-v1.0.md` | 2,064 行 | 19 组件 + 17 TypeScript 类型 |
| Teammate 3 | `hitl_ui_flow-v1.0.md` | 2,049 行 | 9 操作 × 6 阶段流程 |
| **总计** | — | **5,394 行** | — |

---

## 二、前端架构总览

### 2.1 路由架构

```
┌─────────────────────────────────────────────────────────────┐
│                     React + React Router v6                  │
│                                                             │
│  /login              → LoginPage                            │
│  /dashboard          → P1 Dashboard                         │
│  /review/new         → P2 Upload & Config                   │
│  /review/:id/parsing → P3 Parsing Progress  (status guard)  │
│  /review/:id/reviewing→ P4 AI Review        (status guard)  │
│  /review/:id/workspace→ P5 Workspace        (status guard)  │
│  /review/:id/report  → P6 Report            (status guard)  │
│  /review/history     → P7 History                            │
│                                                             │
│  Guards: AuthGuard (JWT) + DocumentStatusGuard (9-state)    │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 页面层级

```
P1  Dashboard
    ├── TopNav
    ├── StatCards (4 cards)
    ├── QuickActions (最近审阅 + 快捷上传)
    └── TaskList (筛选 + 分页)

P2  Upload & Config  [Stepper: 1→2→3→4]
    ├── UploadZone (拖拽/选择/进度)
    ├── ValidationPanel (5层校验结果)
    ├── ConfigForm (NDA + Playbook)
    └── LaunchBar (开始解析)

P3  Parsing Progress  [SSE: parse.*]
    ├── OverallProgress (环形图 + 预估时间)
    ├── AgentProgressCards ×4 (条款/风控/合规/报告)
    ├── OperationLogStream (实时日志)
    └── FailurePanel (条件渲染)

P4  AI Review Progress  [SSE: review.*]
    ├── AgentOrchestrationView (Supervisor + 4 Agent 卡片)
    ├── ReviewFailurePanel (条件)
    ├── PartialSuccessPanel (条件: 完成区/待审区)
    ├── PauseResumeBar (条件: 暂停/恢复)
    └── ReviewCompleteSummary (条件: 进入 P5)

P5  Workspace (并排视图)  ← 核心页面
    ├── WorkspaceToolbar (进度 + 暂存 + 提交)
    ├── 左: DocumentPanel
    │   ├── DocumentViewer (PDF/DOCX 渲染)
    │   ├── ClauseHighlightOverlay (3 色高亮)
    │   └── TextSelectionToolbar (浮动工具条)
    └── 右: RiskReviewPanel
        ├── RiskDashboard (统计 + Tab 切换)
        ├── HighRiskPanel → ApprovalCard[] (6 区)
        ├── MediumRiskBatchPanel (批量)
        ├── LowRiskPanel (折叠 + 抽样)
        └── ManualFlagForm (手动标记)

P6  Report Preview
    ├── RiskSummary
    ├── HighRiskList / MediumRiskList
    ├── AuditTimeline
    └── Sign + Export

P7  History
    └── SearchFilter + TaskList + Pagination
```

### 2.3 组件树总图

```
App
├── AuthGuard
├── TopNav (Logo + Breadcrumb + UserMenu)
├── PageLoading / PageError / PageEmpty (全局)
├── ToastProvider
│
├── P1: Dashboard
├── P2: UploadPage
│   ├── Stepper
│   ├── UploadZone → ProgressBar
│   ├── ValidationPanel → ValidationResult[]
│   ├── ConfigForm → PlaybookSelect
│   └── LaunchBar
├── P3: ParsingPage
│   ├── OverallProgress → CircularProgress
│   ├── AgentProgressCards → ProgressBar ×4
│   ├── OperationLogStream → LogEntry[]
│   └── FailurePanel
├── P4: ReviewProgressPage
│   ├── SupervisorStatusBar
│   ├── AgentCard ×4
│   ├── ReviewLogStream
│   ├── ReviewFailurePanel / PartialSuccessPanel / TimeoutPanel
│   └── PauseResumeBar / ReviewCompleteSummary
├── P5: WorkspacePage
│   ├── WorkspaceToolbar → SubmitButton (disabled logic)
│   ├── DocumentPanel
│   │   ├── DocumentViewer → PageNavigator + SearchBar
│   │   ├── ClauseHighlightOverlay → HighlightRect[]
│   │   └── TextSelectionToolbar
│   ├── RiskReviewPanel
│   │   ├── RiskDashboard → StatBadge ×3 + ApprovalProgress
│   │   ├── RiskTabNav (High / Medium / Low)
│   │   ├── HighRiskPanel → ApprovalCard[]
│   │   │   ├── ClauseLocationBar
│   │   │   ├── AIJudgment → ConfidenceRing
│   │   │   ├── PlaybookDiff → DiffViewer
│   │   │   ├── SuggestionBox
│   │   │   ├── DecisionHistory
│   │   │   └── ActionBar → [Approve] [Edit] [Reject]
│   │   ├── MediumRiskBatchPanel → BatchActionBar + ApprovalCard[]
│   │   ├── LowRiskPanel → SpotCheckButton
│   │   └── ManualFlagForm
│   └── SubmitConfirmDialog
├── P6: ReportPage
└── P7: HistoryPage
```

---

## 三、数据流与 SSE 事件

```
REST API (请求-响应)                    SSE Event Stream (实时推送)
─────────────────────                  ──────────────────────────
POST /documents/upload                 GET /documents/{id}/events
GET  /documents/{id}                        │
POST /documents/{id}/parse                  ├── parse.progress   → P3 进度条
GET  /documents/{id}/clauses                ├── parse.complete   → P3→P4 跳转
GET  /documents/{id}/risk-flags             ├── parse.failed     → P3 失败面板
POST /risk-flags/{id}/approve               ├── review.progress  → P4 Agent 卡片
POST /risk-flags/{id}/edit                  ├── review.log       → P4 日志
POST /risk-flags/{id}/reject                ├── review.complete  → P4→P5 跳转
POST /risk-flags/batch-approve              ├── review.failed    → P4 失败面板
POST /risk-flags/sample                     ├── review.timeout   → P4 超时面板
POST /risk-flags/{id}/escalate              └── interrupt.ready  → P5 审批卡片
POST /risk-flags/manual
POST /documents/{id}/submit
POST /documents/{id}/save-draft
GET  /documents/{id}/report
```

---

## 四、乐观更新策略总表

| 操作 | 乐观更新 | 回滚策略 |
|------|:--:|------|
| **Approve** | 卡片 → CONFIRMED + 绿边框 + slideOutRight 300ms | 卡片滑回 + 恢复 PENDING_REVIEW |
| **Edit** | 卡片 → AMENDED + 修改字段即时更新 | snapshot 恢复 |
| **Reject** | 卡片 slideOutLeft + Toast "可撤销"(5s) | DOM 重新插入 + 恢复 |
| **Batch Approve** | 列表项逐个 checkmark 动画(50ms间隔) | per-item 恢复 |
| **Spot Check** | 无乐观（必须等 API） | — |
| **Escalate** | 卡片跨 Tab 迁移 + 自动切到 High Tab | 卡片迁回 |
| **Manual Add** | 临时 ID 替换 | 删除临时项 |
| **Submit** | **无乐观（关键操作）** | — |
| **Save Draft** | Toast "已保存" | — |

---

## 五、4 层不可跳过约束的实现

| 层级 | 位置 | 实现方式 |
|:--:|------|---------|
| L1 | 前端 SSE 监听 | `interrupt.ready` 事件 → 渲染 ApprovalCard，无对应中断时不渲染 |
| L2 | 前端 Submit(409) | 409 → 关闭提交对话框 → Toast "剩余 N 项" → 切到 High Tab → 脉冲动画 |
| L3 | 前端 UI disabled | `all_high_risk_resolved === false` → SubmitButton gray + tooltip |
| L4 | 前端 423 处理 | 并发锁冲突 → Toast "另一会话正在编辑此条款" |

---

## 六、"未开发"标注清单

> 所有后端 API 当前均处于规划阶段，前端标注为 ⚠️ 未开发，不伪造 mock 数据

| # | API | Teammate 引用 | 前端处理 |
|---|-----|:--:|------|
| 1 | `POST /documents/upload` | Teammate 1 §P2 | ⚠️ 未开发 — UploadZone 展示 loading placeholder |
| 2 | `POST /documents/{id}/parse` | Teammate 1 §P2 | ⚠️ 未开发 — LaunchBar disabled |
| 3 | `GET /documents/{id}/events` (SSE) | Teammate 1 §P3/P4 | ⚠️ 未开发 — SSE 连接 pending |
| 4 | `POST /documents/{id}/review` | Teammate 1 §P4 | ⚠️ 未开发 |
| 5 | `GET /documents/{id}/risk-flags` | Teammate 2 §ApprovalCard | ⚠️ 未开发 — 卡片渲染 "No data" |
| 6 | `POST /risk-flags/{id}/approve` | Teammate 3 §3 | ⚠️ 未开发 |
| 7 | `POST /risk-flags/{id}/edit` | Teammate 3 §4 | ⚠️ 未开发 |
| 8 | `POST /risk-flags/{id}/reject` | Teammate 3 §5 | ⚠️ 未开发 |
| 9 | `POST /risk-flags/batch-approve` | Teammate 3 §6 | ⚠️ 未开发 |
| 10 | `POST /risk-flags/sample` | Teammate 3 §7 | ⚠️ 未开发 |
| 11 | `POST /risk-flags/{id}/escalate` | Teammate 3 §8 | ⚠️ 未开发 |
| 12 | `POST /risk-flags/manual` | Teammate 3 §9 | ⚠️ 未开发 |
| 13 | `POST /documents/{id}/submit` | Teammate 3 §10 | ⚠️ 未开发 — SubmitButton disabled |
| 14 | `POST /documents/{id}/save-draft` | Teammate 3 §11 | ⚠️ 未开发 |

---

## 七、上游对齐验证

| # | 约束 | 来源 | Teammate 1 | Teammate 2 | Teammate 3 |
|---|------|------|:--:|:--:|:--:|
| 1 | 7 页面路由 | `frontend_design_spec` | ✅ 9 routes | — | — |
| 2 | 并排视图 | `frontend_design_spec` | — | ✅ 左+右面板 | ✅ 同步交互 |
| 3 | 分级告警 3 色 | `langchain_hitl_arch` | — | ✅ 高亮覆盖层 | ✅ Tab 切换 |
| 4 | 解释性字段突出 | `frontend_design_spec` | — | ✅ 4 字段前置 | — |
| 5 | 8 操作映射 | `langchain_hitl_arch` | — | — | ✅ 9 操作 |
| 6 | 4 层不可跳过 | `langchain_hitl_arch` | — | — | ✅ L1-L4 |
| 7 | SSE 9 事件 | `api_spec` | ✅ parse/review | — | ✅ interrupt.ready |
| 8 | 32 API 端点 | `api_spec` | ✅ P1-P4 映射 | ✅ P5 映射 | ✅ 9 操作映射 |
| 9 | 数据字段映射 | `data_model_spec` | ✅ field tables | ✅ 17 TS types | — |
| 10 | 乐观更新 | `flow_state_spec` | — | — | ✅ per-operation |
| 11 | ⚠️ 未开发标注 | 用户要求 | ✅ 12 items | ✅ API table | ✅ 10 items |

---

## 八、Lead 审批记录

| 时间 | 事件 | 决议 |
|------|------|------|
| 2026-07-30 | Teammate 1 提交页面路由计划 | ✅ 批准（9路由 + P1-P4 + 全局） |
| 2026-07-30 | Teammate 2 提交审核组件计划 | ✅ 批准（19 组件 + TS 类型） |
| 2026-07-30 | Teammate 3 提交 HITL UI 计划 | ✅ 批准（9 操作 × 5 状态机） |
| 2026-07-30 | Teammate 1 完成 | ✅ 1,281 行 |
| 2026-07-30 | Teammate 2 完成 | ✅ 2,064 行 |
| 2026-07-30 | Teammate 3 完成 | ✅ 2,049 行 |
| 2026-07-30 | Lead 汇总 | ✅ 本文件 |

---

> **上游文档**:
> - `../04_interaction_design/langchain_hitl_arch-v1.0.md` — HITL 架构
> - `./frontend_design_spec-v1.0.md` — 前端设计规范
> - `./frontend_backend_boundary_spec-v1.0.md` — 前后端边界
> - `../08_api_specification/api_spec-v1.0.md` — API 规范
> **下游文档**:
> - `../09_frontend_plan/` — 前端实现
> - `../11_integration/` — 联调
