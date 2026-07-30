# 前后端功能边界规范 v1.0

> **版本**: v1.0
> **创建日期**: 2026-07-30
> **文档性质**: 收口规范 — 严格基于上游设计文档，不自主发散
> **上游依赖**:
> - `docs/03_business_modeling/business_model.md` — 业务问题建模（MVP 范围、业务实体、HITL 约束）
> - `docs/04_interaction_design/flow_state_spec.md` — 状态流转规范（三阶段职责边界）
> - `docs/06_system_architecture/frontend_design_spec-v1.0.md` — 前端设计规范（7 页面、8 操作）
> **下游读者**: 后端实现计划 (`docs/10_backend_plan/`)、API 规范 (`docs/08_api_specification/`)、数据模型设计 (`docs/07_data_model/`)

---

## 一、总体原则

> **来源**: `flow_state_spec.md` §2.2 三阶段职责边界

```
前端 = 用户交互的发起者 + 数据展示的消费者
后端 = 业务逻辑的执行者 + 数据的唯一真实来源（Source of Truth）
```

| 原则 | 说明 |
|------|------|
| 后端是唯一数据源 | 前端不产生业务数据，所有 RiskFlag、ReviewDecision、AuditLog 由后端生成和持久化 |
| 前端只做展示逻辑 | 风险等级的视觉映射（🔴🟡🟢）、进度条渲染、页面跳转控制等归前端 |
| 后端执行所有判定 | 条款提取、风险识别、合规检查、报告生成全部在后端 Agent 中执行 |
| 前端发起 HITL 操作 | approve / edit / reject / batch_approve / manual_add / final_submit 由前端触发，后端执行和记录 |

---

## 二、功能归属矩阵

### 2.1 阶段 1: 上传与解析

> **来源**: `flow_state_spec.md` §3.1 + `frontend_design_spec-v1.0.md` P2, P3

| 功能 | 前端负责 | 后端负责 | 边界说明 |
|------|:--:|:--:|---------|
| 拖拽/选择文件 | ✅ | — | 浏览器原生 File API |
| 客户端格式预检 | ✅ | — | 前端校验文件扩展名 + MIME type（PDF/DOCX 白名单） |
| 文件大小/页数预检 | ✅ | — | 前端读取文件 size 属性，不发送到后端 |
| 文件上传 | ✅ (发送) | ✅ (接收+存储) | 前端通过 multipart/form-data 上传；后端返回 document_id + 存储路径 |
| 服务端格式校验 | — | ✅ | 后端校验文件 magic bytes，确保文件真实格式 |
| 加密检测 | — | ✅ | 后端检测 PDF 加密标记，返回 `encrypted: true/false` |
| 损坏检测 | — | ✅ | 后端尝试解析文件结构，失败则返回 `corrupted: true` + 错误详情 |
| OCR 检测与处理 | — | ✅ | 后端检测扫描版 PDF（无文本层），异步执行 OCR |
| OCR 模式选择 | ✅ (发送) | ✅ (执行) | 前端发送用户选择（immediate / background），后端按模式执行 |
| 上传进度展示 | ✅ | — | 前端通过 XHR progress event 或 fetch + ReadableStream 展示进度条 |
| 文档类型/标题/标签配置 | ✅ (表单) | ✅ (存储) | 前端发送配置数据，后端更新 Document 元数据 |
| Playbook 选择 | ✅ (下拉框) | ✅ (提供可选列表) | 后端提供可用 Playbook 列表；前端展示并提交选择 |
| 解析任务触发 | ✅ (按钮) | ✅ (执行) | 前端发送 POST 触发；后端创建解析任务并入队 |
| 解析进度展示 | ✅ (渲染) | ✅ (推送事件) | 后端通过 SSE 推送 4 Agent 解析进度事件；前端接收并渲染进度条 |
| 解析完成/失败状态 | ✅ (展示) | ✅ (判定+推送) | 后端判定解析最终状态并推送；前端展示对应 UI |
| 解析重试 | ✅ (按钮) | ✅ (Checkpointer 断点续传) | 前端发送重试请求；后端利用 Checkpointer 从失败点恢复 |
| 并发上传排队 | ✅ (提示) | ✅ (队列管理) | 后端管理任务队列和并发限制；前端展示排队状态 |

### 2.2 阶段 2: AI 审核执行

> **来源**: `flow_state_spec.md` §3.2 + `frontend_design_spec-v1.0.md` P4

| 功能 | 前端负责 | 后端负责 | 边界说明 |
|------|:--:|:--:|---------|
| 审核任务启动 | ✅ (按钮/自动) | ✅ (Agent 编排) | 前端发送启动审核请求；后端 Supervisor 编排 4 Agent |
| 4 Agent 并行进度展示 | ✅ (渲染) | ✅ (推送事件) | 后端通过 SSE 推送每个 Agent 的状态（条款数、进度%、当前分析维度） |
| 实时操作日志流 | ✅ (渲染) | ✅ (推送事件) | 后端推送结构化日志事件；前端渲染日志流 |
| 审核完成判定 | — | ✅ | 后端所有 Agent 完成或失败后判定最终状态 |
| 审核完成摘要 | ✅ (展示) | ✅ (提供聚合数据) | 后端返回风险统计摘要（高/中/低风险数量）；前端渲染 |
| 审核失败处理 | ✅ (错误展示+操作入口) | ✅ (失败判定+原因) | 后端判定失败类别（服务不可用/解析残留/超时）并返回；前端展示对应操作按钮 |
| 部分成功处理 | ✅ (三区结果面板) | ✅ (完成区/待审区数据分离) | 后端分别返回已完成和未完成条款的数据；前端渲染三区面板 |
| 暂停审核 | ✅ (按钮) | ✅ (暂停 Agent 执行) | 前端发送暂停请求；后端在下一个 safe-point 暂停并保存 checkpoint |
| 断点恢复 | ✅ (提示+按钮) | ✅ (Checkpointer 恢复) | 后端检测未完成任务并返回恢复状态；前端提示"是否从中断处继续？" |
| 审核生命周期状态 | ✅ (状态标签) | ✅ (状态管理) | 后端管理 9 状态生命周期（创建→排队→执行→...）；前端展示当前状态 |
| 审核取消 | ✅ (按钮) | ✅ (终止执行+保存状态) | 前端发送取消请求；后端终止 Agent 执行并标记 CANCELLED |

### 2.3 阶段 3: 人工审批

> **来源**: `flow_state_spec.md` §3.3 + `frontend_design_spec-v1.0.md` P5

| 功能 | 前端负责 | 后端负责 | 边界说明 |
|------|:--:|:--:|---------|
| 审批仪表盘统计 | ✅ (渲染) | ✅ (聚合数据) | 后端返回高/中/低风险计数 + 审批进度；前端渲染统计卡片 |
| 文档原文渲染 | ✅ (PDF/DOCX → HTML) | ✅ (提供渲染文件) | 后端提供可渲染的文档文件 URL 或 base64；前端执行渲染 |
| 条款高亮位置数据 | ✅ (高亮覆盖层) | ✅ (提供位置坐标) | 后端返回 Clause.position（页/段落/字符偏移）；前端计算高亮位置 |
| 并排视图同步滚动 | ✅ | — | 纯前端交互逻辑（点击风险卡片→ documentPanel.scrollTo(clausePosition)） |
| 风险卡片数据 | ✅ (渲染) | ✅ (提供) | 后端返回 RiskFlag 列表 + PlaybookRule 对比 + AI 置信度 + 修改建议 |
| **approve 操作** | ✅ (按钮+UI) | ✅ (记录决策+状态变更) | 前端发送 `approve` 请求；后端更新 RiskFlag.status → CONFIRMED + 写入 ReviewDecision + AuditLog |
| **edit 操作** | ✅ (表单+按钮) | ✅ (记录决策+保存修改) | 前端发送 `edit` 请求 + 修改字段；后端更新 RiskFlag.status → AMENDED + 保存修改字段 + 写入 ReviewDecision + AuditLog |
| **reject 操作** | ✅ (拒绝原因对话框+按钮) | ✅ (记录决策+移除标记) | 前端发送 `reject` 请求 + 原因；后端更新 RiskFlag.status → REJECTED + 写入 ReviewDecision + AuditLog |
| **batch_approve 操作** | ✅ (确认按钮) | ✅ (批量更新标记) | 前端发送 `batch_approve` 请求；后端批量更新所有中风险 RiskFlag.status → UNREVIEWED_AUTO_PASSED |
| **spot_check 操作** | ✅ (触发按钮) | ✅ (确定性随机抽样) | 后端使用确定性种子抽样 N%，返回被抽中的 RiskFlag 列表；前端展示抽样结果 |
| **escalate 操作** | ✅ (升级确认对话框) | ✅ (升级风险等级) | 前端发送 `escalate` 请求；后端将该 RiskFlag.risk_level → HIGH + 加入高风险审批队列 |
| **manual_add 操作** | ✅ (划选+浮动工具条+表单) | ✅ (创建人工标记) | 前端发送划选位置 + 风险等级/类别/说明；后端创建人工来源 RiskFlag（标记为 MANUALLY_ADDED） |
| **final_submit 操作** | ✅ (审阅摘要+确认对话框) | ✅ (校验+报告生成+状态变更) | 前端发送 `submit` 请求；后端校验高风险审批完整性 → 生成 ReviewReport → 更新 Document.status → 写入 AuditLog |
| 高风险审批完整性校验 | ✅ (UI 置灰提交按钮) | ✅ (API 409 拦截) | 前端：所有高风险项完成前按钮 disabled；后端：API 层再次校验，不完整返回 409 |
| 暂存草稿 | ✅ (按钮) | ✅ (保存当前状态) | 前端发送 `save_draft` 请求；后端保存当前所有审批状态 + Document.status → DRAFT |
| 键盘快捷键 | ✅ | — | 纯前端交互（J/K 导航、Enter 确认、Esc 返回） |

### 2.4 报告与导出

> **来源**: `frontend_design_spec-v1.0.md` P6

| 功能 | 前端负责 | 后端负责 | 边界说明 |
|------|:--:|:--:|---------|
| 审阅报告数据 | ✅ (渲染) | ✅ (聚合+提供) | 后端生成 ReviewReport（含风险摘要、条款清单、审计时间线、签署状态） |
| 审计追踪时间线 | ✅ (渲染) | ✅ (提供 AuditLog) | 后端返回按时间排序的 AuditLog 条目列表 |
| PDF 报告导出 | ✅ (触发下载) | ✅ (生成 PDF) | 后端生成 PDF 报告文件；前端提供下载链接或直接下载 |
| 报告签署 | ✅ (按钮) | ✅ (签名记录) | 前端发送签署请求；后端记录签署人+时间戳 + 更新报告签署状态 |

---

## 三、数据归属规范

### 3.1 数据由后端提供展示

> **来源**: `business_model.md` §4.3 实体定义

以下数据**全部由后端生成和持久化**，前端仅做展示渲染：

| 数据类别 | 实体 | 后端提供接口 | 前端展示位置 |
|---------|------|------------|------------|
| 文档信息 | Document | `GET /documents/{id}` | P2 解析配置, P5 顶部工具栏 |
| 文档原文 | Document (文件) | `GET /documents/{id}/file` | P5 左面板文档渲染 |
| 条款列表 | Clause[] | `GET /documents/{id}/clauses` | P3, P5 高亮覆盖层 |
| 条款位置数据 | Clause.position | (含在 Clause 对象中) | P5 高亮定位 |
| 风险标记列表 | RiskFlag[] | `GET /documents/{id}/risk-flags` | P5 右面板审批卡片 |
| AI 置信度 | RiskFlag.confidence | (含在 RiskFlag 对象中) | P5 审批卡片 AI 判定区 |
| Playbook 规则 | PlaybookRule | `GET /playbooks` (选择), `GET /risk-flags/{id}/playbook-diff` (对比) | P2 下拉框, P5 Playbook 对比区 |
| 修改建议 | RiskFlag.suggestion | (含在 RiskFlag 对象中) | P5 审批卡片修改建议区 |
| 审阅决策历史 | ReviewDecision[] | `GET /risk-flags/{id}/decisions` | P5 审批卡片历史区 |
| 审批统计 | 聚合数据 | `GET /documents/{id}/review-summary` | P1 统计卡片, P5 审批进度, P6 风险摘要 |
| 审计日志 | AuditLog[] | `GET /documents/{id}/audit-logs` | P6 审计追踪时间线 |
| 审阅报告 | ReviewReport | `GET /documents/{id}/report` | P6 报告内容区 |
| Dashboard 统计 | 聚合数据 | `GET /dashboard/stats` | P1 统计卡片行 |
| 任务列表 | Document[] (分页) | `GET /documents?status=&page=&size=` | P1 审阅任务列表, P7 历史列表 |
| 可用 Playbook 列表 | PlaybookRule[] (摘要) | `GET /playbooks?doc_type=NDA` | P2 Playbook 下拉框 |
| 解析/AI 审核实时事件 | SSE 事件流 | `GET /documents/{id}/events` (SSE) | P3 进度条, P4 Agent 卡片, 实时日志 |

### 3.2 操作流程必须由前端发起

> **来源**: `flow_state_spec.md` §三 — 三阶段人工角色 + `frontend_design_spec-v1.0.md` §5.2 操作规范

以下操作**必须由用户在前端界面主动触发**，后端不自动执行：

| 操作 | 发起页面 | 对应的后端 API | 说明 |
|------|:------:|--------------|------|
| 上传文件 | P2 | `POST /documents/upload` | 用户主动选择文件 |
| 启动解析 | P2 | `POST /documents/{id}/parse` | 用户点击"开始解析" |
| 选择 OCR 模式 | P2 | (含在 parse 请求中) | 用户选择 immediate / background |
| 启动 AI 审核 | P3→P4 | `POST /documents/{id}/review` | 解析完成后自动或手动触发 |
| 暂停审核 | P4 | `POST /documents/{id}/review/pause` | 用户主动暂停 |
| 恢复审核 | P4 | `POST /documents/{id}/review/resume` | 用户确认"从中断处继续" |
| 取消审核 | P4 | `POST /documents/{id}/review/cancel` | 用户主动取消 |
| **approve** | P5 | `POST /risk-flags/{id}/approve` | 用户点击"同意" |
| **edit** | P5 | `POST /risk-flags/{id}/edit` | 用户修改后点击保存 |
| **reject** | P5 | `POST /risk-flags/{id}/reject` | 用户填写原因后点击"驳回" |
| **batch_approve** | P5 | `POST /risk-flags/batch-approve` | 用户点击中风险"全部确认" |
| **spot_check** | P5 | `POST /risk-flags/sample` | 用户点击低风险"抽样审计" |
| **escalate** | P5 | `POST /risk-flags/{id}/escalate` | 用户确认升级 |
| **manual_add** | P5 | `POST /risk-flags/manual` | 用户划选原文 + 填写标记表单 |
| **final_submit** | P5 | `POST /documents/{id}/submit` | 用户确认提交 |
| **save_draft** | P5 | `POST /documents/{id}/save-draft` | 用户点击"暂存草稿" |
| 签署报告 | P6 | `POST /documents/{id}/report/sign` | 用户点击"确认签署" |
| 导出 PDF 报告 | P6 | `GET /documents/{id}/report/export?format=pdf` | 用户点击"导出 PDF 报告" |
| 重试解析 | P3 | `POST /documents/{id}/parse/retry` | 用户点击"重试" |
| 重试审核 | P4 | `POST /documents/{id}/review/retry` | 用户点击"重试" |

---

## 四、通信模式规范

> **来源**: `flow_state_spec.md` 三阶段设计中的实时推送需求

### 4.1 请求-响应模式（REST API）

| 适用场景 | 方法 | 示例 |
|---------|------|------|
| 页面初始数据加载 | `GET` | 获取文档列表、Dashboard 统计 |
| 用户触发操作 | `POST` | 上传、approve/edit/reject、提交 |
| 数据更新 | `PUT/PATCH` | 更新文档元数据 |

### 4.2 实时推送模式（SSE）

| 适用场景 | 事件类型 | 推送内容 |
|---------|---------|---------|
| 解析进度 | `parse.progress` | { agent_name, progress_pct, current_clause_type } |
| 解析完成 | `parse.complete` | { document_id, clause_count } |
| 解析失败 | `parse.failed` | { error_type, error_message, recoverable } |
| AI 审核进度 | `review.progress` | { agent_name, clauses_processed, total_clauses, current_dimension } |
| 审核日志 | `review.log` | { timestamp, agent_name, message } |
| 审核完成 | `review.complete` | { summary: { high, medium, low } } |
| 审核失败 | `review.failed` | { fail_category, message, partial_results_available } |
| 审核超时 | `review.timeout` | { completed_count, total_count } |

### 4.3 文件传输模式

| 场景 | 方法 | Content-Type |
|------|------|-------------|
| 文档上传 | `POST` | `multipart/form-data` |
| 文档原文加载 | `GET` | `application/pdf` / `application/octet-stream` |
| 报告下载 | `GET` | `application/pdf` |

---

## 五、前端不允许的操作

> **来源**: `business_model.md` §1.2 问题本质 — AI 定位为辅助工具 + `flow_state_spec.md` HITL 架构约束

以下操作**严格禁止在前端执行**，必须由后端 Agent 或后端业务逻辑完成：

| 禁止操作 | 原因 | 应在何处执行 |
|---------|------|------------|
| 直接调用 LLM API | API Key 暴露风险；前端不可见内部推理 | 后端 Agent 层 |
| 直接生成 RiskFlag | 风险判定需访问 Playbook 规则库和 AI Agent，前端不应自行判定 | 后端 Agent 层 |
| 直接计算 AI 置信度 | 置信度来自模型输出的 logprobs 或后处理，前端不可自行估算 | 后端 Agent 层 |
| 直接执行条款提取 | 条款提取需 NLP 模型 + 分段算法 + Playbook 知识库 | 后端解析 Agent |
| 直接生成审阅报告 | 报告需聚合全量 RiskFlag + ReviewDecision + AuditLog | 后端报告 Agent |
| 直接写入 AuditLog | 审计日志必须由后端在数据变更时自动生成，不可篡改 | 后端中间件 |
| 绕过 interrrupt 提交审批 | API 409 校验是第二层约束，前端 UI 置灰是第一层 | 后端 API 层 |
| 直接调用 OCR 服务 | OCR 需专用服务依赖和计算资源 | 后端 OCR 服务 |
| 缓存 AI 判定结果到本地 | 法律审阅数据安全要求；数据一致性问题 | 后端数据库 |

---

## 六、边界检查清单（API 设计输入）

> **来源**: 本文 §二至§四 的规范汇总

以下为 API 规范设计的最小端点集（`docs/08_api_specification/` 将在此基础上展开）：

| # | 方法 | 路径 | 触发方 | 说明 |
|---|------|------|:--:|------|
| 1 | `GET` | `/dashboard/stats` | 前端 | Dashboard 统计聚合 |
| 2 | `GET` | `/documents` | 前端 | 文档列表（分页+筛选） |
| 3 | `POST` | `/documents/upload` | 前端 | 上传文档 |
| 4 | `GET` | `/documents/{id}` | 前端 | 文档详情 |
| 5 | `GET` | `/documents/{id}/file` | 前端 | 文档原文文件 |
| 6 | `GET` | `/documents/{id}/clauses` | 前端 | 条款列表 |
| 7 | `POST` | `/documents/{id}/parse` | 前端 | 启动解析 |
| 8 | `POST` | `/documents/{id}/parse/retry` | 前端 | 重试解析 |
| 9 | `GET` | `/documents/{id}/events` | 前端 | SSE 事件流（解析+审核进度） |
| 10 | `POST` | `/documents/{id}/review` | 前端 | 启动 AI 审核 |
| 11 | `POST` | `/documents/{id}/review/pause` | 前端 | 暂停审核 |
| 12 | `POST` | `/documents/{id}/review/resume` | 前端 | 恢复审核 |
| 13 | `POST` | `/documents/{id}/review/cancel` | 前端 | 取消审核 |
| 14 | `POST` | `/documents/{id}/review/retry` | 前端 | 重试审核 |
| 15 | `GET` | `/documents/{id}/risk-flags` | 前端 | AI 风险标记列表 |
| 16 | `POST` | `/risk-flags/{id}/approve` | 前端 (approve) | 同意风险标记 |
| 17 | `POST` | `/risk-flags/{id}/edit` | 前端 (edit) | 编辑修正风险标记 |
| 18 | `POST` | `/risk-flags/{id}/reject` | 前端 (reject) | 驳回风险标记 |
| 19 | `POST` | `/risk-flags/batch-approve` | 前端 (batch) | 批量确认中风险 |
| 20 | `POST` | `/risk-flags/sample` | 前端 (spot_check) | 低风险抽样 |
| 21 | `POST` | `/risk-flags/{id}/escalate` | 前端 (escalate) | 升级风险等级 |
| 22 | `POST` | `/risk-flags/manual` | 前端 (manual_add) | 手动补充标记 |
| 23 | `GET` | `/risk-flags/{id}/decisions` | 前端 | 某风险标记的审批历史 |
| 24 | `GET` | `/risk-flags/{id}/playbook-diff` | 前端 | Playbook 标准条款对比 |
| 25 | `POST` | `/documents/{id}/submit` | 前端 (final_submit) | 提交审阅 |
| 26 | `POST` | `/documents/{id}/save-draft` | 前端 | 暂存草稿 |
| 27 | `GET` | `/documents/{id}/review-summary` | 前端 | 审批统计摘要 |
| 28 | `GET` | `/documents/{id}/audit-logs` | 前端 | 审计日志 |
| 29 | `GET` | `/documents/{id}/report` | 前端 | 审阅报告 |
| 30 | `GET` | `/documents/{id}/report/export?format=pdf` | 前端 | 导出 PDF 报告 |
| 31 | `POST` | `/documents/{id}/report/sign` | 前端 | 签署报告 |
| 32 | `GET` | `/playbooks?doc_type=NDA` | 前端 | 可用 Playbook 列表 |

---

> **上游文档**:
> - `../03_business_modeling/business_model.md` — 业务问题建模
> - `../04_interaction_design/flow_state_spec.md` — 状态流转规范
> - `./frontend_design_spec-v1.0.md` — 前端设计规范
> **下游文档**:
> - `../07_data_model/` — 数据模型设计
> - `../08_api_specification/` — API 规范
> - `../10_backend_plan/` — 后端实现计划
