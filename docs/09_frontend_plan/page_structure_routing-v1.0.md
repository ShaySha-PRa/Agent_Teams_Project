# 前端页面结构与路由设计规范 v1.0

> **版本**: v1.0
> **创建日期**: 2026-07-30
> **文档性质**: 收口规范 -- 严格基于上游 API 规范、前端设计规范、前后端边界规范、HITL 架构
> **上游依赖**:
> - `docs/06_system_architecture/frontend_design_spec-v1.0.md` -- 7 页面清单、组件树、交互规范
> - `docs/08_api_specification/api_spec-v1.0.md` -- 32 接口、请求/响应格式、SSE 事件类型
> - `docs/06_system_architecture/frontend_backend_boundary_spec-v1.0.md` -- 前后端功能归属矩阵
> - `docs/04_interaction_design/langchain_hitl_arch-v1.0.md` -- 9 状态生命周期、3 中断点、Checkpointer
> **下游读者**: 前端开发团队（React 实现）

---

## 目录

1. [路由架构设计](#一路由架构设计)
2. [P1 Dashboard 页面详细设计](#二p1-dashboard-页面详细设计)
3. [P2 上传与配置页面详细设计](#三p2-上传与配置页面详细设计)
4. [P3 解析进度页面详细设计](#四p3-解析进度页面详细设计)
5. [P4 AI 审核进度页面详细设计](#五p4-ai-审核进度页面详细设计)
6. [全局组件](#六全局组件)

---

## 一、路由架构设计

> **来源**: `frontend_design_spec-v1.0.md`  §二 页面清单 + §四 页面跳转关系 + `api_spec-v1.0.md` §一 接口总览

### 1.1 技术选型

| 项目 | 选型 | 说明 |
|------|------|------|
| 框架 | React 18+ | Web SPA |
| 路由库 | React Router v6 | `createBrowserRouter` + 嵌套路由 |
| 状态管理 | React Context + useReducer | 页面级状态隔离，不引入 Redux（MVP） |
| HTTP 客户端 | fetch + SSE (EventSource) | 原生 API，不引入 Axios（轻量 MVP） |
| TypeScript | 严格模式 | 所有组件 Props 和 API 响应均定义接口 |

### 1.2 完整路由表

| 路由路径 | 页面 ID | 页面名称 | 路由层级 | 必需数据接口（页面加载时） | 页面级渲染状态 |
|---------|:------:|---------|:------:|--------------------------|--------------|
| `/dashboard` | P1 | 工作台首页 | 顶层 | `GET /dashboard/stats` + `GET /documents?page=1&size=20` | loading / success / error |
| `/review/new` | P2 | 新建审阅 | 顶层 | `GET /playbooks?doc_type=NDA` | success (表单始终可用) |
| `/review/:documentId/parsing` | P3 | 解析进度 | 嵌套 `/review/:documentId/` | `GET /documents/{id}` + SSE `GET /documents/{id}/events` | loading / streaming / complete / failed / error |
| `/review/:documentId/reviewing` | P4 | AI 审核进度 | 嵌套 `/review/:documentId/` | `GET /documents/{id}` + SSE `GET /documents/{id}/events` | loading / streaming / complete / partial-success / failed / timeout / error |
| `/review/:documentId/workspace` | P5 | 审阅工作台 | 嵌套 `/review/:documentId/` | `GET /documents/{id}/clauses` + `GET /documents/{id}/risk-flags` + `GET /documents/{id}/review-summary` | loading / success / draft / error |
| `/review/:documentId/report` | P6 | 审阅报告 | 嵌套 `/review/:documentId/` | `GET /documents/{id}/report` + `GET /documents/{id}/audit-logs` | loading / success / unsigned / signed / error |
| `/review/history` | P7 | 历史审阅列表 | 顶层 | `GET /documents?status=&page=1&size=20` | loading / empty / success / error |
| `/login` | -- | 登录页 | 顶层 | -- | -- |
| `*` | -- | 404 页面 | 顶层 | -- | -- |

**路由组织策略**:
- 使用 `:documentId` (kebab-case) 作为动态路径参数，替代上游文档中的 `{id}`
- P3/P4/P5/P6 共享 `/review/:documentId/` 前缀，便于实现 `DocumentLayout` 共享壳（顶部文档信息栏 + 子路由 `<Outlet />`）

### 1.3 路由守卫设计

#### 1.3.1 认证守卫 (AuthGuard)

```
所有路由（除 /login）均包裹 AuthGuard:
  if (token 不存在 || token 过期):
    -> 重定向到 /login?redirect=<原始路径>
  else:
    -> 渲染子路由
```

**数据来源**: JWT 存储在 `localStorage`，前端解析 `exp` 字段判断过期。

**⚠️ 未开发**: 后端认证接口（JWT 签发 / refresh）尚未在 API 规范中定义，当前设计假设为 `POST /auth/login` + `POST /auth/refresh`。前端 AuthGuard 暂时以本地 token 校验为准，待后端接口就绪后接入。

#### 1.3.2 文档状态守卫 (DocumentStatusGuard)

每个嵌套在 `/review/:documentId/` 下的页面均包裹 DocumentStatusGuard，根据 `document.status` 决定渲染目标页面或重定向:

```
GET /documents/:documentId -> 读取 status 字段

路由匹配规则:
  /review/:documentId/parsing:
    status IN (UPLOADED, PARSING)  -> 渲染 P3
    status = PARSED                -> 重定向到 /review/:documentId/reviewing
    status IN (REVIEWING, REVIEWED, HUMAN_REVIEW, COMPLETED) -> 重定向到 /review/:documentId/workspace
    status = FAILED 且 fail_stage = PARSE -> 渲染 P3 (显示重试面板)

  /review/:documentId/reviewing:
    status = PARSED                -> 渲染 P4 (显示"启动审核"按钮)
    status = REVIEWING             -> 渲染 P4 (连接 SSE 显示进度)
    status = REVIEWED              -> 重定向到 /review/:documentId/workspace
    status IN (HUMAN_REVIEW, COMPLETED) -> 重定向到 /review/:documentId/workspace
    status = FAILED 且 fail_stage = REVIEW -> 渲染 P4 (显示失败面板)

  /review/:documentId/workspace:
    status IN (REVIEWED, HUMAN_REVIEW) -> 渲染 P5
    status = COMPLETED             -> 重定向到 /review/:documentId/report
    status IN (CREATED, UPLOADED, PARSING) -> 重定向到 /review/:documentId/parsing
    status = PARSED                -> 重定向到 /review/:documentId/reviewing
    status = REVIEWING             -> 重定向到 /review/:documentId/reviewing
    status = DRAFT                 -> 渲染 P5 (恢复草稿)

  /review/:documentId/report:
    status = COMPLETED             -> 渲染 P6
    otherwise                      -> 重定向到对应的状态页面
```

**状态枚举来源**: `api_spec-v1.0.md` Document.status 字段（`CREATED` / `UPLOADED` / `PARSING` / `PARSED` / `REVIEWING` / `REVIEWED` / `HUMAN_REVIEW` / `COMPLETED` / `FAILED` / `CANCELLED` / `DRAFT`）

**⚠️ 未开发**: `fail_stage` 字段（PARSE / REVIEW）和 `DRAFT` 状态尚未在 API 响应中明确定义，前端路由守卫在字段缺失时降级为仅使用 `status` 判断。

### 1.4 页面间路由跳转参数传递

`documentId` 在整个主流程中传递路径:

```
P2 上传成功 -> 获得 document_id -> navigate(`/review/${documentId}/parsing`)

         ┌─────────────────────────────────────────┐
         │  document_id = "d_abc123"               │
         │  通过 URL path param 贯穿全链路:          │
         │                                         │
         │  /review/d_abc123/parsing    (P3)       │
         │  /review/d_abc123/reviewing  (P4)       │
         │  /review/d_abc123/workspace   (P5)       │
         │  /review/d_abc123/report      (P6)       │
         └─────────────────────────────────────────┘
```

**跳转触发条件与来源**: 参见 `frontend_design_spec-v1.0.md` §四 表格。

| 跳转 | 触发方式 | 触发组件 | 传递参数 |
|------|---------|---------|---------|
| P1 -> P2 | 点击"新建审阅"按钮 | P1 TopNav CTA | 无参数 |
| P2 -> P3 | 上传成功 + 点击"开始解析" | P2 LaunchBar | `documentId` (来自 upload 201 响应) |
| P3 -> P4 | SSE `parse.complete` 事件 | P3 自动跳转 | `documentId` (URL 已有) |
| P4 -> P5 | SSE `review.complete` 事件 + 用户点击"进入审批" | P4 ReviewCompleteSummary | `documentId` (URL 已有) |
| P5 -> P6 | 用户点击"确认提交" | P5 SubmitConfirmDialog | `documentId` (URL 已有) |
| P1 -> P5/P6 | 点击历史/最近审阅行 | P1 TaskList / RecentCards | `documentId` + 目标路径 (根据 status) |

**P2 -> P3 的两种模式**:
1. **标准模式** (手动触发): 用户在 P2 Step 4 点击"开始解析" -> `POST /documents/{id}/parse` -> 成功 (202) -> `navigate(/review/${id}/parsing)`
2. **自动触发模式**: 用户在 P2 开启"自动触发"开关 -> 上传成功后自动调用 parse -> 跳转 P3

---

## 二、P1 Dashboard 页面详细设计

> **来源**: `frontend_design_spec-v1.0.md` §三 P1 + `api_spec-v1.0.md` §六 6.5/6.6 + §三 3.6

### 2.1 页面级状态机

```
P1 Page
  ├── loading   -- 首次进入，等待两个 API 返回
  ├── success   -- 数据全部就绪，渲染完整页面
  └── error     -- 任一关键 API 失败（非 401/403）
```

**部分加载策略**: Dashboard 的两个 API (`stats` + `documents`) 同时发起。若 `stats` 失败但 `documents` 成功，统计卡片区渲染为 `error` 状态（带 "重试" 按钮），任务列表正常渲染。

### 2.2 组件层次树

```
P1: DashboardPage
│
├── TopNav                              (全局组件，详见 §六)
│
├── StatCards                           (行容器，flex-row gap-4)
│   ├── StatCard (pendingReviews)       (原子组件，复用 4 次)
│   │   ├── label: "待处理审阅"
│   │   ├── value: number
│   │   ├── icon: ClockIcon
│   │   └── trend: +/- N% (可选)
│   ├── StatCard (completedThisWeek)    (label: "本周完成")
│   │   ├── value: number
│   │   └── icon: CheckCircleIcon
│   ├── StatCard (avgReviewTime)        (label: "平均耗时")
│   │   ├── value: "18 分钟"
│   │   └── icon: TimerIcon
│   └── StatCard (totalRisksFound)      (label: "发现风险数")
│       ├── value: number
│       └── icon: AlertTriangleIcon
│
├── QuickActions                        (行容器)
│   ├── RecentReviewCards               (水平滚动卡片列表)
│   │   └── RecentReviewCard[]          (点击 -> navigate 到对应页面)
│   │       ├── title: string           (doc.title)
│   │       ├── status: StatusBadge     (doc.status)
│   │       ├── updatedAt: string       (相对时间 "2 小时前")
│   │       └── riskSummary: RiskDots   (🔴N 🟡M 🟢K)
│   └── QuickUploadZone                 (拖拽区，快捷入口 -> P2)
│       └── "拖拽文件到此处开始新审阅" / "选择文件"
│
├── TaskList                            (section 容器)
│   ├── TaskListHeader
│   │   ├── title: "审阅任务"
│   │   ├── StatusFilter                (下拉: 全部 / 待处理 / 已完成 / 失败)
│   │   └── SortSelect                  (排序: 最近更新 / 创建时间)
│   ├── TaskListBody
│   │   ├── TaskRow[]                   (每条一个审阅任务)
│   │   │   ├── docTitle: string        (doc.title)
│   │   │   ├── docType: "NDA"          (doc.document_type)
│   │   │   ├── status: StatusBadge     (doc.status)
│   │   │   ├── uploadedAt: string      (格式化日期)
│   │   │   ├── riskSummary: RiskDots   (🔴N 🟡M 🟢K, 仅在 REVIEWED+ 状态)
│   │   │   └── onClick -> navigate(根据 status 决定目标)
│   │   └── TaskListEmpty               (条件渲染: items.length === 0)
│   │       └── "暂无审阅记录，点击上方按钮开始"
│   └── Pagination                      (分页器)
│       ├── page: number
│       ├── total: number
│       └── onPageChange: (page) => void
│
└── PageError                           (条件渲染: pageState === 'error')
    ├── errorMessage: string
    └── retryButton: "重试"
```

### 2.3 API 接口映射

#### 2.3.1 `GET /dashboard/stats` -> StatCards

| API 响应字段 | 前端 State 字段 | 渲染组件 | 数据转换 |
|-------------|---------------|---------|---------|
| `data.pending_reviews` | `stats.pendingReviews` | `StatCard[0]` | 直接渲染 number |
| `data.completed_this_week` | `stats.completedThisWeek` | `StatCard[1]` | 直接渲染 number |
| `data.avg_review_time_minutes` | `stats.avgReviewTime` | `StatCard[2]` | 格式化为 "N 分钟" |
| `data.total_risks_found` | `stats.totalRisksFound` | `StatCard[3]` | 直接渲染 number |

**请求参数**: 无
**错误处理**:
- 401 -> 触发 AuthGuard 重定向到 `/login`
- 500/503 -> StatCards 区域渲染错误状态 + "重试" 按钮

#### 2.3.2 `GET /documents?status=&page=1&size=20` -> TaskList

| API 响应字段 | 前端 State 字段 | 渲染组件 | 数据转换 |
|-------------|---------------|---------|---------|
| `data.items[]` | `tasks.items[]` | `TaskRow` | -- |
| `items[].document_id` | `task.id` | `TaskRow` | onClick 跳转目标路径计算 |
| `items[].title` | `task.title` | `TaskRow > docTitle` | 截断过长标题 (>50 字符) |
| `items[].document_type` | `task.docType` | `TaskRow > docType` | "NDA" -> "NDA 协议" |
| `items[].status` | `task.status` | `TaskRow > StatusBadge` | 映射颜色和中文标签 (见下) |
| `items[].uploaded_at` | `task.uploadedAt` | `TaskRow > uploadedAt` | ISO -> 相对时间或 "YYYY-MM-DD HH:mm" |
| `items[].risk_summary.high` | `task.riskHigh` | `TaskRow > RiskDots` | -- |
| `items[].risk_summary.medium` | `task.riskMedium` | `TaskRow > RiskDots` | -- |
| `items[].risk_summary.low` | `task.riskLow` | `TaskRow > RiskDots` | -- |
| `data.page` | `tasks.pagination.page` | `Pagination` | -- |
| `data.size` | `tasks.pagination.size` | `Pagination` | -- |
| `data.total` | `tasks.pagination.total` | `Pagination` | -- |

**请求参数**:
- `status`: 来自 StatusFilter 组件，可选值: `""` (全部) / `"PARSED"` / `"REVIEWING"` / `"HUMAN_REVIEW"` / `"COMPLETED"` / `"FAILED"`
- `page`: 当前页码 (默认 1)
- `size`: 每页条数 (默认 20)

**status -> statusLabel 映射表**:

| status | 中文标签 | 徽章颜色 | 点击跳转 |
|--------|---------|:------:|---------|
| `CREATED` | 待上传 | gray | `/review/{id}/parsing` |
| `UPLOADED` | 已上传 | blue | `/review/{id}/parsing` |
| `PARSING` | 解析中 | blue (animated) | `/review/{id}/parsing` |
| `PARSED` | 待审核 | green | `/review/{id}/reviewing` |
| `REVIEWING` | AI 审核中 | purple (animated) | `/review/{id}/reviewing` |
| `REVIEWED` | 待审批 | orange | `/review/{id}/workspace` |
| `HUMAN_REVIEW` | 审批中 | orange (animated) | `/review/{id}/workspace` |
| `COMPLETED` | 已完成 | green | `/review/{id}/report` |
| `FAILED` | 失败 | red | 视 fail_stage 决定 |
| `CANCELLED` | 已取消 | gray | 无跳转 (可查看) |

#### 2.3.3 RecentReviewCards 数据来源

**⚠️ 未开发**: 当前无专用"最近审阅"API。两种后端对接方案:
- 方案 A (推荐): 后端新增 `GET /dashboard/recent?limit=5`，返回最近 5 条非 CANCELLED 状态的 Document 摘要
- 方案 B (MVP 临时): 前端使用 `GET /documents?sort=uploaded_at:desc&size=5` 作为最近审阅

前端组件已预留 `RecentReview[]` 数据接口，待后端接口确定后接入。

### 2.4 每个组件的渲染状态

| 组件 | States | 数据结构依赖 |
|------|--------|------------|
| `StatCard` | (a) loading: 骨架屏占位 (b) success: 数字+标签 (c) error: "--" 占位 | `stats` |
| `RecentReviewCards` | (a) loading: 3 张骨架卡片 (b) empty: "暂无最近审阅" (c) success: 卡片列表 (d) error: 隐藏区域 | `recentReviews[]` |
| `QuickUploadZone` | (a) idle: 拖拽提示 (b) dragOver: 高亮边框 (c) uploading: 进度条 (可选) | 无 (纯交互) |
| `TaskListBody` | (a) loading: 5 行骨架屏 (b) empty: `TaskListEmpty` (c) success: `TaskRow[]` (d) error: inline error + retry 按钮 | `tasks.items[]` |
| `TaskRow` | (a) normal: 完整行 (b) hover: 背景色变化 (c) active: 选中态 | `task: TaskItem` |
| `StatusBadge` | 根据 status 渲染不同颜色圆点+文字 | `status: string` |
| `Pagination` | (a) hidden: total <= size (b) normal: 页码按钮 (c) disabled: loading 态 | `pagination: {page, size, total}` |

---

## 三、P2 上传与配置页面详细设计

> **来源**: `frontend_design_spec-v1.0.md` §三 P2 + `api_spec-v1.0.md` §三 + `frontend_backend_boundary_spec-v1.0.md` §2.1

### 3.1 页面级状态机

```
P2 Page
  ├── step 1: UPLOAD           -- 选择/拖拽文件
  │   ├── idle                 -- 初始状态，无文件
  │   ├── dragOver             -- 用户拖拽中 (纯 CSS 交互)
  │   ├── uploading            -- 正在上传 (显示进度)
  │   ├── uploaded             -- 上传成功，获得 document_id
  │   └── uploadError          -- 上传失败 (格式/大小/加密/损坏)
  │
  ├── step 2: VALIDATION       -- 文件逐项校验 (依赖 step 1 uploaded)
  │   ├── checking             -- 等待服务端校验结果
  │   ├── allPassed            -- 5 项全部通过
  │   ├── partialFailed        -- 某项失败 (如 OCR 需确认)
  │   └── fatalFailed          -- 致命失败 (加密/损坏)
  │
  ├── step 3: CONFIG           -- 配置表单 (依赖 step 2 allPassed)
  │   ├── filling              -- 用户填写中
  │   └── valid                -- 表单校验通过 (标题非空)
  │
  └── step 4: LAUNCH           -- 启动确认 (依赖 step 3 valid)
      ├── reviewing            -- 用户确认前 (配置摘要)
      ├── launching            -- 正在发送 parse 请求
      └── launched             -- parse 请求成功，准备跳转 P3
```

**步骤间导航规则**:
- 步骤仅可**前进**（通过校验门控），回退通过点击 Stepper 的已完成步骤实现
- 前进条件: 当前步骤满足 `allPassed` / `valid` 状态
- 若前进失败，在步骤指示器上显示错误标记

### 3.2 组件层次树

```
P2: UploadPage
│
├── TopNav                              (全局组件)
│
├── Stepper                             (步骤指示器，4 步)
│   ├── StepIndicator[1]: "上传文档"     (states: inactive / active / completed / error)
│   ├── StepIndicator[2]: "文件校验"     (states: inactive / active / completed / error)
│   ├── StepIndicator[3]: "解析配置"     (states: inactive / active / completed)
│   └── StepIndicator[4]: "启动解析"     (states: inactive / active / completed)
│
├── Step 1: UploadZone                  (条件渲染: currentStep === 1)
│   ├── DragDropArea
│   │   ├── state="idle": 云上传图标 + "拖拽文件到此处" + "仅支持 PDF / DOCX 格式"
│   │   ├── state="dragOver": 高亮边框 + "释放以上传文件"
│   │   └── state="hasFile": 文件名 + 文件大小 + 文件图标
│   ├── FileSelectButton                ("选择文件" button, accept=".pdf,.docx")
│   ├── PasteHintText                   ("或使用 Ctrl+V 从剪贴板粘贴")
│   ├── UploadProgressBar               (条件渲染: uploading)
│   │   ├── percentage: number          (0-100)
│   │   ├── speed: string               ("1.2 MB/s")
│   │   └── CancelButton                (取消上传，终止 XHR)
│   └── UploadErrorAlert                (条件渲染: uploadError)
│       ├── errorType: UNSUPPORTED_FORMAT / FILE_TOO_LARGE / FILE_ENCRYPTED / FILE_CORRUPTED / NETWORK_ERROR
│       ├── errorMessage: string
│       ├── supportedFormatsHint: "支持格式: PDF (.pdf), Word (.docx)"
│       └── retryButton / reSelectButton
│
├── Step 2: ValidationPanel             (条件渲染: currentStep === 2)
│   ├── ValidationItem (formatCheck)
│   │   ├── label: "格式校验"
│   │   ├── status: pass / fail / checking
│   │   ├── detail: "通过" / 错误原因 + "支持: PDF (.pdf), Word (.docx)"
│   │   └── passIcon / failIcon / spinnerIcon
│   ├── ValidationItem (sizeCheck)      (⚠️ 未开发: 服务端校验)
│   │   ├── label: "文件大小 / 页数校验"
│   │   ├── status: pass / fail / pending
│   │   ├── detail: "2.5 MB, 8 页" / "文件过大，最大 50MB" / "页数超限，最大 200 页"
│   │   └── passIcon / failIcon
│   ├── ValidationItem (encryptionCheck) (⚠️ 未开发: 服务端校验)
│   │   ├── label: "加密检测"
│   │   ├── status: pass / fail / pending
│   │   ├── detail: "通过" / "文件已加密，请解除保护后重试"
│   │   └── passIcon / failIcon
│   ├── ValidationItem (corruptionCheck) (⚠️ 未开发: 服务端校验)
│   │   ├── label: "损坏检测"
│   │   ├── status: pass / fail / pending
│   │   ├── detail: "通过" / "文件可能已损坏，请重新导出 PDF"
│   │   └── passIcon / failIcon
│   └── ValidationItem (ocrCheck)       (⚠️ 未开发: 服务端校验)
│       ├── label: "OCR 检测"
│       ├── status: pass / fail / pending
│       ├── detail: "文件包含文本层，无需 OCR" / "检测到扫描版 PDF"
│       ├── ocrModeSelector              (条件渲染: ocrCheck === fail)
│       │   ├── label: "OCR 处理模式"
│       │   ├── RadioGroup:
│       │   │   ├── "立即处理" (immediate) -- 等待 OCR 完成后进入解析
│       │   │   └── "后台处理并通知" (background) -- 先执行解析，OCR 异步补全
│       │   └── helperText: "立即处理可能需要几分钟"
│       └── passIcon / warningIcon
│
├── Step 3: ConfigForm                  (条件渲染: currentStep === 3)
│   ├── FormField (documentType)
│   │   ├── label: "文档类型"
│   │   ├── Select (disabled, value="NDA")
│   │   ├── helperText: "MVP 阶段仅支持保密协议 (NDA)"
│   │   └── value: "NDA"
│   ├── FormField (title)
│   │   ├── label: "文档标题"
│   │   ├── Input (defaultValue=originalFilename 去后缀)
│   │   ├── validation: required + maxLength=100
│   │   └── charCount: "N/100"
│   ├── FormField (tags)                 (可选)
│   │   ├── label: "标签"
│   │   ├── TagInput (回车添加标签)
│   │   └── helperText: "按回车键添加标签"
│   └── FormField (playbook)
│       ├── label: "Playbook 规则集"
│       ├── Select (options from GET /playbooks)
│       │   └── MVP 默认值: "NDA Standard Playbook"
│       └── helperText: "选择用于审核的 Playbook 规则集"
│
├── Step 4: LaunchBar                   (条件渲染: currentStep === 4)
│   ├── ConfigSummary                    (回显 Step 3 的配置)
│   │   ├── fileName: string
│   │   ├── fileInfo: "PDF, 2.5MB, 8页"
│   │   ├── docType: "NDA 协议"
│   │   ├── title: string
│   │   └── playbook: string
│   ├── LaunchButton
│   │   ├── state="idle": "开始解析"
│   │   ├── state="loading": spinner + "正在启动解析..."
│   │   └── state="disabled": (前置条件不满足)
│   └── AutoTriggerToggle
│       ├── Switch: 自动触发模式 (默认关闭)
│       └── helperText: "开启后，上传完成将自动启动解析"
│
└── StepNavigation                      (底部步骤按钮)
    ├── PrevButton: "上一步"             (step > 1 时显示)
    └── NextButton:
        ├── step < 4: "下一步"           (disabled 直到当前步骤完成)
        └── step = 4: "开始解析"          (触发 launch)
```

### 3.3 API 接口映射

#### 3.3.1 `POST /documents/upload` -> UploadZone

**请求**:
```
Content-Type: multipart/form-data
Body:
  file: File (PDF/DOCX)
  title: string (optional, 默认文件名去后缀)
  document_type: "NDA" (optional, MVP 固定)
```

**前端上传流程**:
```
1. 用户在 UploadZone 选择/拖拽文件
2. 客户端预检 (同步执行):
   a. 格式预检: file.type 或扩展名是否在 ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"] 白名单中
      -> 不通过: 直接渲染 UploadErrorAlert，不发起请求
   b. 大小预检: file.size <= 50 * 1024 * 1024 (50MB)
      -> 不通过: 直接渲染 UploadErrorAlert，不发起请求
3. 预检通过 -> 发起 multipart/form-data POST
4. 使用 XMLHttpRequest 监听 upload.progress 事件 (fetch 不支持上传进度)
5. 渲染 UploadProgressBar (percentage, speed, cancel)
6. 等待响应:
   - 201: 获得 document_id, 进入 Step 2
   - 422: 渲染对应的 UploadErrorAlert (格式/加密/损坏/过大/页数)
   - 429: "当前上传任务较多，请稍后重试"
   - 500: "服务器错误，请稍后重试"
```

**5 层校验归属**:

| 层级 | 校验项 | 执行位置 | 实现方式 | 失败处理 |
|:--:|-------|:------:|---------|---------|
| 1 | 客户端格式预检 | **前端** | `file.type` + 扩展名白名单 | 即时拒绝，显示 UploadErrorAlert |
| 2 | 客户端大小预检 | **前端** | `file.size <= 50MB` | 即时拒绝，显示 UploadErrorAlert |
| 3 | 服务端 magic byte | **后端** | 读文件头字节校验真实格式 | 422 UNSUPPORTED_FORMAT -> 显示 UploadErrorAlert |
| 4 | 加密检测 | **后端** | 检测 PDF 加密标记 | 422 FILE_ENCRYPTED -> 显示 ValidationPanel 致命失败 |
| 5 | 损坏检测 | **后端** | 尝试解析文件结构 | 422 FILE_CORRUPTED -> 显示 ValidationPanel 致命失败 |
| 5b | OCR 检测 | **后端** | 检测文本层存在性 | 无文本层 -> 显示 OCR 模式选择 |

**成功响应 (201) -> 前端 State 更新**:

| API 响应字段 | 前端 State 字段 | 后续使用 |
|-------------|---------------|---------|
| `data.document_id` | `documentId` | URL 导航参数、parse 请求路径 |
| `data.original_filename` | `fileName` (原始) | Step 3 title 默认值、Step 4 ConfigSummary |
| `data.title` | `title` (初始) | Step 3 title 输入框默认值 |
| `data.document_type` | `docType` | Step 3 文档类型下拉 (disabled) |
| `data.format` | `format` | Step 4 ConfigSummary |
| `data.file_size_bytes` | `fileSize` | 格式化 "2.5 MB" |
| `data.page_count` | `pageCount` | 格式化 "8 页" |
| `data.status` | `status` | "UPLOADED" |
| `data.md5_hash` | `md5Hash` | 重复文件检测 (警告提示) |
| `data.ocr_status` | `ocrStatus` | Step 2 OCR 检测项的状态 (NOT_NEEDED / NEEDED / PROCESSING) |
| `data.encryption_status` | `encryptionStatus` | Step 2 加密检测项的状态 (NONE / ENCRYPTED) |

#### 3.3.2 `GET /playbooks?doc_type=NDA` -> ConfigForm Playbook 下拉框

| API 响应字段 | 前端 State 字段 | 渲染组件 | 数据转换 |
|-------------|---------------|---------|---------|
| `data[].playbook_rule_id` | `playbook.id` | `<option value={id}>` | -- |
| `data[].name` | `playbook.name` | `<option>` 显示文本 | -- |
| `data[].applicable_doc_type` | (用于客户端筛选) | -- | MVP 仅 NDA |
| `data[].risk_level` | (用于后续审核) | -- | -- |

**MVP 行为**: 下拉框默认选中 `"NDA Standard Playbook"`（假设为唯一选项），用户无需操作。

**⚠️ 未开发**: Playbook 列表接口假设返回摘要字段 (`id`, `name`, `applicable_doc_type`, `risk_level`)，实际字段以 API 实现为准。MVP 阶段仅 1 个 Playbook，下拉框可降级为文字展示。

#### 3.3.3 `POST /documents/{id}/parse` -> LaunchBar

**请求**:
```json
{
  "playbook_id": "pr_001",           // 来自 Step 3 选择
  "ocr_mode": "immediate"            // 来自 Step 2 OCR 选择
}
```

**响应 (202) -> 前端 State 更新**:

| API 响应字段 | 前端 State 字段 | 后续动作 |
|-------------|---------------|---------|
| `data.document_id` | `documentId` (确认) | -- |
| `data.parse_task_id` | `parseTaskId` | SSE 事件关联 (可选) |
| `data.status` | -- | -- |
| `data.message` | -- | Toast 提示 |

**成功后**: `navigate(/review/${documentId}/parsing)`，P3 页面接管。

**错误处理**:
- 422: 参数校验失败（如缺少 playbook_id）-> Toast 错误提示
- 409: 状态冲突（文档非 UPLOADED 状态）-> Toast 提示 + 刷新页面状态

### 3.4 Stepper 步骤状态管理

```
interface StepState {
  step: 1 | 2 | 3 | 4;
  status: 'idle' | 'active' | 'completed' | 'error';
  isAccessible: boolean;          // 是否允许回退到此步骤
}

步骤转换规则:
  step 1: idle -> active (用户选择页面) -> completed (上传成功) -> error (上传失败)
  step 2: idle -> active (step 1 completed) -> completed (全部校验通过) -> error (致命失败)
  step 3: idle -> active (step 2 completed) -> completed (表单校验通过)
  step 4: idle -> active (step 3 completed) -> completed (parse 成功，跳转 P3)

回退规则:
  - 点击已完成的步骤可回退 (isAccessible=true)
  - 回退时保留已填写的数据 (不重置表单)
  - 回退后修改配置 -> 前方步骤可能变为 error (需重新校验)
```

---

## 四、P3 解析进度页面详细设计

> **来源**: `frontend_design_spec-v1.0.md` §三 P3 + `api_spec-v1.0.md` §七 SSE + `langchain_hitl_arch-v1.0.md` §四/§六

### 4.1 页面级状态机

```
P3 Page
  ├── loading             -- 初始化: 等待 GET /documents/{id} 返回
  ├── streaming           -- SSE 连接已建立，接收 parse.progress 事件
  ├── completed           -- 收到 parse.complete 事件 -> 自动跳转 P4
  ├── failed-recoverable  -- 收到 parse.failed (recoverable=true) -> 显示重试面板
  ├── failed-fatal        -- 收到 parse.failed (recoverable=false) -> 显示重新上传面板
  └── error               -- SSE 连接失败或文档 API 失败
```

**自动跳转逻辑**:
```
on SSE event "parse.complete":
  1. 更新页面状态为 completed
  2. 显示完成动画 (1 秒)
  3. setTimeout(() => navigate(`/review/${documentId}/reviewing`), 1000)
  4. 跳转前关闭 SSE 连接
```

### 4.2 组件层次树

```
P3: ParsingProgressPage
│
├── DocumentHeader                      (共享壳: 文档标题栏)
│   ├── title: string                   (来自 GET /documents/{id}.title)
│   ├── docTypeBadge: "NDA 协议"        (来自 document_type)
│   └── GlobalStatusBadge               (来自 SSE 事件流解析)
│       ├── state="streaming":  "解析中" (blue, animated)
│       ├── state="completed":  "解析完成" (green)
│       ├── state="failed-rec": "解析失败 (可恢复)" (orange)
│       └── state="failed-fatal":"解析失败" (red)
│
├── OverallProgress                     (总体进度区)
│   ├── ProgressRing                    (SVG 环形进度图)
│   │   ├── progressPct: 0-100
│   │   ├── strokeColor: 渐变色 (根据进度)
│   │   └── centerText: "62%" + "已完成 5/10 步骤"
│   └── EstimatedTimeRemaining          (from SSE parse.progress 或计算)
│       ├── visible: 有预估数据时
│       └── text: "预计剩余 45 秒" / "预计剩余 2 分钟"
│
├── AgentProgressCards                  (4 Agent 分进度卡片)
│   ├── AgentProgressCard (clause_extraction)
│   │   ├── agentName: "条款提取 Agent"
│   │   ├── progressBar: [████████░░] 80%
│   │   ├── detailText: "已提取 8/10 类条款"
│   │   ├── currentItem: "正在识别: 赔偿条款"
│   │   └── agentIcon: FileSearchIcon
│   ├── AgentProgressCard (risk_control)
│   │   ├── agentName: "风控 Agent"
│   │   ├── progressBar: [████████░░] 80%
│   │   ├── detailText: "已扫描 12/20 个条款"    (⚠️ 未开发: 解析阶段风控数据)
│   │   ├── currentItem: "进行中..."
│   │   └── agentIcon: ShieldIcon
│   ├── AgentProgressCard (compliance)
│   │   ├── agentName: "合规 Agent"
│   │   ├── progressBar: [██████████] 100%
│   │   ├── detailText: "已完成"
│   │   ├── currentItem: (none)
│   │   └── agentIcon: CheckBadgeIcon
│   └── AgentProgressCard (report)
│       ├── agentName: "报告 Agent"
│       ├── progressBar: [░░░░░░░░░░] 0%
│       ├── detailText: "等待上游完成..."
│       ├── currentItem: (none)
│       ├── isWaiting: true               (特殊样式: 虚线边框 + 灰色)
│       └── agentIcon: DocumentReportIcon
│
├── OperationLogStream                  (实时操作日志流)
│   ├── LogStreamHeader
│   │   ├── title: "实时解析日志"
│   │   └── autoScrollToggle: Switch     (默认开启自动滚动)
│   ├── LogStreamBody                    (max-height + overflow-y: auto)
│   │   ├── LogEntry[]                   (每条日志)
│   │   │   ├── timestamp: "10:23:15"
│   │   │   ├── agentName: "条款提取 Agent"
│   │   │   ├── message: "识别'保密义务'条款"
│   │   │   └── type: info / warning / error
│   │   └── LogStreamEmpty                (条件渲染: 无日志)
│   │       └── "等待解析任务开始..."
│   └── LogStreamFooter
│       └── entryCount: "共 42 条日志"
│
├── FailurePanel                         (条件渲染: failed-recoverable || failed-fatal)
│   ├── FailureHeader
│   │   ├── errorType: "CORRUPTED" / "OCR_FAILED" / "EXTRACTION_FAILED" 等
│   │   ├── errorMessage: string         (来自 SSE parse.failed)
│   │   └── errorIcon
│   ├── FailureBody
│   │   ├── errorDetail: string          (详细错误描述)
│   │   ├── completedProgress: "已完成进度: 60% (条款提取 Agent 已完成)"
│   │   └── recoverableNote:             (条件渲染: recoverable=true)
│   │       └── "系统已保存解析进度，重试将从失败点继续"
│   └── FailureActions
│       ├── RetryButton                  (条件渲染: recoverable=true)
│       │   ├── label: "重试解析"
│       │   ├── api: POST /documents/{id}/parse/retry
│       │   └── onClick: 调用重试接口 -> 重新连接 SSE
│       └── ReuploadButton               (条件渲染: recoverable=false)
│           ├── label: "重新上传"
│           ├── onClick: navigate(`/review/new`)
│           └── variant: secondary
│
└── BottomActionBar
    ├── CancelButton: "取消解析"
    │   ├── onClick: 显示确认对话框 -> POST /documents/{id}/review/cancel (或专用取消接口)
    │   └── variant: secondary
    └── NextStepIndicator                (条件渲染: completed)
        ├── text: "解析完成，正在进入 AI 审核..."
        └── SpinnerIcon (1 秒后自动跳转)
```

### 4.3 SSE 事件订阅映射

**SSE 连接**: `GET /documents/{id}/events` (Accept: text/event-stream)

**连接建立时机**: P3 页面 `onMount` -> 先调用 `GET /documents/{id}` 确认文档存在 -> 建立 SSE 连接

**连接关闭时机**:
1. 收到 `parse.complete` -> 跳转前关闭
2. 收到 `parse.failed` -> 保持连接等待用户操作
3. 用户点击"取消解析" -> 关闭
4. 用户离开页面 (P3 unmount) -> 关闭

#### 4.3.1 SSE 事件 -> 组件映射表

| SSE event | data 字段 | 目标组件 | 更新动作 |
|-----------|----------|---------|---------|
| `parse.progress` | `agent_name` | `AgentProgressCard[{agent_name}]` | 更新进度条和 detailText |
|  | `progress_pct` | `AgentProgressCard[{agent_name}] > progressBar` | `progressPct = data.progress_pct * 100` |
|  | `current_clause_type` | `AgentProgressCard[{agent_name}] > currentItem` | 更新 "正在识别: ..." |
|  | (aggregated) | `OverallProgress > ProgressRing` | 取 4 Agent 的平均进度 |
|  | (aggregated) | `OverallProgress > EstimatedTime` | 根据剩余进度和速度计算 |
| `parse.complete` | `document_id` | `OverallProgress`, `GlobalStatusBadge` | 状态 -> completed |
|  | `clause_count` | `AgentProgressCard[report]` | 显示 "已提取 N 个条款" |
| `parse.failed` | `error_type` | `FailurePanel > FailureHeader` | 显示错误类型 |
|  | `error_message` | `FailurePanel > FailureBody` | 显示错误详情 |
|  | `recoverable` | `FailurePanel > FailureActions` | true -> 显示 RetryButton, false -> 显示 ReuploadButton |

**`parse.progress` 数据结构 (来自 `api_spec-v1.0.md` §7.2)**:
```json
{
  "agent_name": "clause_extraction",       // clause_extraction / risk_control / compliance / report
  "progress_pct": 0.6,                     // 0.0 ~ 1.0
  "current_clause_type": "保密义务"         // 当前正在提取/分析的条款类型
}
```

**⚠️ 未开发**: 解析阶段的 `agent_name` 枚举值 (`risk_control` / `compliance` / `report`) 是否在解析阶段就有进度事件，还是仅在审核阶段才有，需后端确认。若解析阶段仅 `clause_extraction` Agent 工作，则其他 3 张卡片显示 "等待中" 状态。前端 AgentProgressCard 已预留 4 张卡片的渲染逻辑，根据 SSE 事件动态决定显示内容。

#### 4.3.2 日志流渲染

解析阶段的日志以 SSE `parse.progress` 事件中的 `current_clause_type` 字段为信息来源:
```
收到 SSE: parse.progress { agent_name: "clause_extraction", current_clause_type: "保密义务", progress_pct: 0.5 }

前端生成日志行:
  timestamp: new Date().toLocaleTimeString("zh-CN")
  agentName: "条款提取 Agent"
  message: "识别'保密义务'条款"
  type: "info"
```

**⚠️ 未开发**: 若后端在解析阶段也提供 `review.log` 风格的独立日志事件，则优先使用。当前设计以 `parse.progress.current_clause_type` 为日志来源。

### 4.4 失败面板条件渲染规则

```
if pageState === 'failed-recoverable':
  显示 FailurePanel (
    title: "解析失败",
    errorType: data.error_type,
    errorMessage: data.error_message,
    showRetry: true,       // POST /documents/{id}/parse/retry
    showReupload: false
  )

if pageState === 'failed-fatal':
  显示 FailurePanel (
    title: "解析失败",
    errorType: data.error_type,
    errorMessage: data.error_message,
    showRetry: false,
    showReupload: true     // navigate -> /review/new
  )
```

### 4.5 数据模型字段映射 (来自 `GET /documents/{id}`)

| API 响应字段 | 前端 State | 渲染组件 |
|-------------|-----------|---------|
| `data.title` | `docInfo.title` | `DocumentHeader > title` |
| `data.document_type` | `docInfo.docType` | `DocumentHeader > docTypeBadge` |
| `data.status` | `docInfo.status` | `DocumentHeader > GlobalStatusBadge` (初始值) |
| `data.parse_task.status` | `parseStatus` | 决定页面级状态机初始状态 |
| `data.parse_task.extracted_clause_count` | `totalClauses` | `AgentProgressCard[clause_extraction] > detailText` |

---

## 五、P4 AI 审核进度页面详细设计

> **来源**: `frontend_design_spec-v1.0.md` §三 P4 + `api_spec-v1.0.md` §四 + `langchain_hitl_arch-v1.0.md` §四 StateGraph + §六 Checkpointer

### 5.1 页面级状态机

```
P4 Page
  ├── idle                 -- 文档 status=PARSED，显示"启动审核"按钮 (未自动触发)
  ├── starting             -- POST /documents/{id}/review 请求中
  ├── streaming            -- SSE 连接已建立，接收 review.progress/log 事件
  ├── completed            -- 收到 review.complete -> 显示审核完成摘要 + "进入审批"按钮
  ├── partial-success      -- 收到 review.complete (部分条款未完成) -> 显示三区结果面板
  ├── failed-service       -- 收到 review.failed (AI 服务不可用)
  ├── failed-parse-error   -- 收到 review.failed (解析残留错误)
  ├── timeout              -- 收到 review.timeout
  ├── paused               -- 用户暂停审核，等待恢复
  └── error                -- SSE 连接失败或其他网络错误
```

**初始状态判定** (页面 onMount):
```
GET /documents/{id} -> 读取 status:
  status = PARSED  -> pageState = idle (等待用户点击"启动审核")
  status = REVIEWING -> pageState = streaming (立即连接 SSE)
  status = REVIEWED -> 重定向到 P5
  status = FAILED (fail_stage=REVIEW) -> 根据 failed 详情决定 pageState
```

### 5.2 组件层次树

```
P4: ReviewProgressPage
│
├── DocumentHeader                      (共享壳: 文档标题栏，同 P3)
│   ├── title: string
│   ├── docTypeBadge: "NDA 协议"
│   └── GlobalStatusBadge
│       ├── state="idle":            "待启动审核" (gray)
│       ├── state="starting":        "正在启动..." (blue, animated)
│       ├── state="streaming":       "AI 审核中" (purple, animated)
│       ├── state="completed":       "审核完成" (green)
│       ├── state="partial-success": "部分成功" (orange)
│       ├── state="failed-*":        "审核失败" (red)
│       ├── state="timeout":         "审核超时" (orange)
│       └── state="paused":          "已暂停" (yellow)
│
├── AgentOrchestrationView             (Agent 编排视图，页面核心区域)
│   │
│   ├── SupervisorStatusBar            (Supervisor 状态栏)
│   │   ├── text: "已编排 4 个 Agent，正在并行执行" / "等待启动审核"
│   │   └── threadId: (可选) "Thread: lg_thread_xyz"
│   │
│   ├── ParallelAgentCards             (并行 Agent 卡片组，2+1+1 布局)
│   │   │
│   │   ├── AgentReviewCard (risk_control)          ← 并行
│   │   │   ├── agentName: "风控 Agent"
│   │   │   ├── statusIcon: running / completed / failed / waiting
│   │   │   ├── progressBar: [████████░░] 60%
│   │   │   ├── clausesProgress: "已扫描 12/20 个条款"
│   │   │   ├── riskCounts:                      (条件渲染: 有风险发现时)
│   │   │   │   ├── highCount: number (🔴)
│   │   │   │   ├── mediumCount: number (🟡)
│   │   │   │   └── lowCount: number (🟢)
│   │   │   ├── currentDimension: "当前分析维度: 赔偿条款"
│   │   │   ├── lastActivity: "3 秒前"            (相对时间)
│   │   │   └── agentIcon: ShieldIcon
│   │   │
│   │   ├── AgentReviewCard (compliance)           ← 并行
│   │   │   ├── agentName: "合规 Agent"
│   │   │   ├── statusIcon: running / completed / failed
│   │   │   ├── progressBar: [██████████] 100%
│   │   │   ├── clausesProgress: "已完成 10/10 合规项"
│   │   │   ├── completedCount: "发现 2 项合规风险"
│   │   │   ├── currentDimension: (none, completed)
│   │   │   └── agentIcon: CheckBadgeIcon
│   │   │
│   │   └── AgentReviewCard (report)               ← 串行依赖 (等待上游)
│   │       ├── agentName: "报告 Agent"
│   │       ├── statusIcon: waiting (虚线边框)
│   │       ├── waitingText: "等待风控 + 合规 Agent 完成"
│   │       ├── dependenciesList: "依赖: 风控 Agent, 合规 Agent"
│   │       ├── progressBar: [░░░░░░░░░░] 0%
│   │       └── agentIcon: DocumentReportIcon
│   │
│   └── ReviewLogStream                  (实时审核日志流，结构同 P3 OperationLogStream)
│       ├── LogStreamHeader
│       ├── LogStreamBody
│       │   ├── LogEntry[]
│       │   │   ├── timestamp: "10:23:22"
│       │   │   ├── agentName: "风控 Agent"
│       │   │   ├── message: "发现高风险项 — '保密期限超过行业标准'"
│       │   │   └── type: info / warning / error / risk
│       │   └── LogStreamEmpty
│       └── LogStreamFooter
│
├── ReviewFailurePanel                   (条件渲染: failed-service / failed-parse-error)
│   ├── failCategory: SERVICE_UNAVAILABLE / PARSE_ERROR / UNKNOWN
│   ├── failMessage: string
│   ├── partialResultsAvailable: boolean
│   ├── ActionButtons:
│   │   ├── RetryButton                  (POST /documents/{id}/review/retry)
│   │   ├── ManualTakeoverButton         ("人工接管" -> 跳转 P5 使用已有数据) (⚠️ 未开发)
│   │   └── ContactSupportButton         ("联系支持")
│   └── retainedDataNote:                (条件渲染: partialResultsAvailable)
│       └── "已完成的条款风险数据保留可用"
│
├── PartialSuccessPanel                  (条件渲染: partial-success)
│   ├── CompletedSection                 (🟢 完成区)
│   │   ├── header: "已成功审阅的条款 (12/20)"
│   │   ├── completedClauseList[]         (可展开查看风险详情)
│   │   └── badge: "风险数据完整可查看"
│   ├── PendingSection                   (🟠 待审区)
│   │   ├── header: "未完成审阅的条款 (8/20)"
│   │   ├── pendingClauseList[]           (原文可见)
│   │   ├── SingleRetryButton             (单个条款重试) (⚠️ 未开发)
│   │   └── badge: "支持手动审阅 / 单个重试"
│   └── WarningBanner
│       └── "⚠ 风险统计仅覆盖已完成条款 (12/20)，完整数据需继续审核或人工补充"
│
├── PauseResumeBar                       (条件渲染: streaming / paused)
│   ├── PauseButton                      (条件渲染: streaming)
│   │   ├── label: "暂停审核"
│   │   ├── onClick: 显示暂停确认对话框
│   │   └── icon: PauseIcon
│   ├── PauseConfirmDialog               (Modal)
│   │   ├── text: "暂停后可在当前进度恢复，已完成的审核数据将被保存"
│   │   ├── ConfirmButton -> POST /documents/{id}/review/pause
│   │   └── CancelButton
│   └── ResumePrompt                     (条件渲染: paused)
│       ├── text: "检测到未完成的审核任务"
│       ├── progressSaved: "已完成 12/20 条 (60%)"
│       ├── ResumeButton -> POST /documents/{id}/review/resume
│       └── DiscardButton -> POST /documents/{id}/review/cancel
│
├── ReviewCompleteSummary                (条件渲染: completed)
│   ├── riskSummary:
│   │   ├── "🔴 高风险 N 项"
│   │   ├── "🟡 中风险 M 项"
│   │   └── "🟢 低风险 K 项"
│   ├── clauseCount: "共识别 20 个条款"
│   └── EnterApprovalButton
│       ├── label: "进入人工审批"
│       ├── onClick: navigate(`/review/${documentId}/workspace`)
│       └── icon: ArrowRightIcon
│
├── TimeoutPanel                         (条件渲染: timeout)
│   ├── timeoutMessage: "审核超时，但已完成条款的风险数据保留可用"
│   ├── completedCount / totalCount
│   ├── ViewCompletedButton
│   └── RetryButton
│
├── StartReviewButton                    (条件渲染: idle)
│   ├── label: "启动 AI 审核"
│   ├── icon: PlayIcon
│   ├── onClick: POST /documents/{id}/review -> 成功后连接 SSE
│   └── helperText: "将启动 4 个 AI Agent 并行审核文档"
│
└── BottomActionBar
    ├── LifecycleStatusLabel
    │   └── "审核状态: CREATED -> QUEUED -> EXECUTING -> ..." (来自 9 状态生命周期)
    └── QuickActions
        ├── "查看已解析条款" (link to clauses list, modal or side panel) (⚠️ 未开发)
        └── "预览文档" (link to document file, new tab) (⚠️ 未开发)
```

### 5.3 SSE 事件订阅映射

#### 5.3.1 SSE 事件 -> 组件映射表

| SSE event | data 字段 | 目标组件 | 更新动作 |
|-----------|----------|---------|---------|
| `review.progress` | `agent_name` | `AgentReviewCard[{agent_name}]` | 更新卡片进度 |
|  | `clauses_processed` | `AgentReviewCard[{agent_name}] > clausesProgress` | "已扫描 12/20 个条款" |
|  | `total_clauses` | `AgentReviewCard[{agent_name}] > clausesProgress` | 总数显示 |
|  | `current_dimension` | `AgentReviewCard[{agent_name}] > currentDimension` | "当前分析维度: 赔偿条款" |
| `review.log` | `timestamp` | `ReviewLogStream > LogEntry` | 追加新日志行 |
|  | `agent_name` | `ReviewLogStream > LogEntry > agentName` | -- |
|  | `message` | `ReviewLogStream > LogEntry > message` | -- |
| `review.complete` | `summary.high` | `ReviewCompleteSummary > riskSummary` | "🔴 高风险 N 项" |
|  | `summary.medium` | `ReviewCompleteSummary > riskSummary` | "🟡 中风险 M 项" |
|  | `summary.low` | `ReviewCompleteSummary > riskSummary` | "🟢 低风险 K 项" |
| `review.failed` | `fail_category` | `ReviewFailurePanel` | 决定显示哪个失败面板 |
|  | `message` | `ReviewFailurePanel > failMessage` | -- |
|  | `partial_results_available` | `ReviewFailurePanel > ActionButtons` | 决定是否显示 "查看已完成条款" |
| `review.timeout` | `completed_count` | `TimeoutPanel` | "已完成 N 项" |
|  | `total_count` | `TimeoutPanel` | "共 M 项" |

**`review.progress` 数据结构 (来自 `api_spec-v1.0.md` §7.2)**:
```json
{
  "agent_name": "risk_control",          // risk_control / compliance / report (clause_extraction 可能不在审核阶段)
  "clauses_processed": 8,
  "total_clauses": 20,
  "current_dimension": "赔偿条款"          // 当前分析维度
}
```

**`review.log` 数据结构**:
```json
{
  "timestamp": "10:23:22",
  "agent_name": "risk_control",
  "message": "发现高风险项 — '保密期限超过行业标准'"
}
```

**日志行的 type 推断规则 (前端逻辑)**:
```
if message.includes("高风险") or message.includes("严重"):
  type = "error"
else if message.includes("中风险") or message.includes("警告"):
  type = "warning"
else if message.includes("完成") or message.includes("通过"):
  type = "success"
else:
  type = "info"
```

### 5.4 Checkpointer 断点恢复交互

#### 5.4.1 暂停流程

```
用户点击 "暂停审核" 按钮:
  1. 显示 PauseConfirmDialog:
     "暂停后可在当前进度恢复，已完成的审核数据将被保存"
  2. 用户确认 -> POST /documents/{id}/review/pause
  3. 等待后端在下一个 safe-point 暂停并保存 checkpoint
  4. 收到暂停成功响应:
     - pageState = paused
     - 显示 ResumePrompt
     - 保持 SSE 连接或关闭 (待后端确认)
```

#### 5.4.2 恢复流程 (断点恢复)

```
场景 A: 用户在当前会话中恢复:
  1. ResumePrompt 显示 "已完成 12/20 条 (60%)"
  2. 用户点击 "继续审核" -> POST /documents/{id}/review/resume
  3. 后端从 checkpoint 恢复 -> 重新推送 review.progress 事件
  4. pageState = streaming

场景 B: 用户离开后返回 (新会话):
  1. P4 页面 onMount -> GET /documents/{id}
  2. 检测到 status = REVIEWING (暂停中) 或有未完成的 checkpoint
  3. 自动显示 ResumePrompt:
     "检测到未完成的审核任务，是否从中断处继续？"
  4. 用户选择:
     - "继续" -> POST /documents/{id}/review/resume
     - "放弃" -> POST /documents/{id}/review/cancel -> 回到 idle
```

**Checkpointer 状态检测**: 前端不直接访问 Checkpointer。状态判定完全通过 `GET /documents/{id}` 返回的 `status` 字段和 `review_task` 状态。

**⚠️ 未开发**: 恢复后的进度回填（已完成条款数、风险发现数等）依赖后端的 checkpoint 恢复机制。前端 ResumePrompt 中显示的 "已完成 12/20 条" 数据来源需后端在 resume 响应或首个 SSE 事件中提供当前进度快照。

### 5.5 数据模型字段映射 (来自 `GET /documents/{id}`)

| API 响应字段 | 前端 State | 渲染组件 |
|-------------|-----------|---------|
| `data.title` | `docInfo.title` | `DocumentHeader > title` |
| `data.document_type` | `docInfo.docType` | `DocumentHeader > docTypeBadge` |
| `data.status` | `docInfo.status` | `DocumentHeader > GlobalStatusBadge` |
| `data.parse_task.status` | `parseStatus` | (确认解析已完成) |
| `data.parse_task.extracted_clause_count` | `totalClauses` | `AgentReviewCard > clausesProgress total` |

**⚠️ 未开发**: `review_task` 对象（`review_task_id`, `status`, `thread_id`）在 `GET /documents/{id}` 响应中尚未定义。前端在 P4 onMount 和 SSE review 事件中依赖此数据。当前设计假设 `review_task` 嵌套在 document 对象中（类似 `parse_task`），若后端采用独立接口则需调整。

---

## 六、全局组件

> **来源**: `frontend_design_spec-v1.0.md` §三 (各页面的 TopNav) + 通用交互需求

### 6.1 TopNav 顶部导航栏

**组件层次**:
```
TopNav
├── Logo
│   └── 系统名称: "Agent 文档审核系统" (或 SVG Logo)
│   └── onClick -> navigate('/dashboard')
├── Breadcrumb                           (条件渲染: 当前路由非 /dashboard)
│   └── 动态面包屑:
│       P2: "工作台 > 新建审阅"
│       P3: "工作台 > 审阅详情 > 解析进度"
│       P4: "工作台 > 审阅详情 > AI 审核"
│       P5: "工作台 > 审阅详情 > 审阅工作台"
│       P6: "工作台 > 审阅详情 > 审阅报告"
│       P7: "工作台 > 历史审阅"
├── UserMenu
│   ├── Avatar (用户头像 + 用户名缩写)
│   └── Dropdown:
│       ├── "个人设置" (⚠️ 未开发)
│       └── "退出登录" -> clearToken() -> navigate('/login')
└── 全局 CTA: "新建审阅"                  (仅在 /dashboard 和 /review/history 显示)
    └── onClick -> navigate('/review/new')
```

**TopNav 的渲染状态**:
- `loading`: 用户信息尚未加载 (显示骨架头像)
- `authenticated`: 显示头像 + 用户名 + 下拉菜单
- `anonymous`: (不应出现，AuthGuard 会拦截)

**路由感知**:
- 当前路由包含 `/review/:documentId/` 时，在面包屑中显示文档标题（从 Context 或 URL state 获取）
- 文档标题通过路由 state 传递: `navigate(path, { state: { docTitle } })`，避免面包屑的额外 API 调用

### 6.2 全局 Loading 组件 (PageLoading)

```
PageLoading                              (全页面加载状态)
├── Spinner / Skeleton
│   ├── variant="page": 居中 spinner + "加载中..."
│   └── variant="inline": 局部骨架屏 (由各页面自行决定)
└── overlay: boolean                     (是否覆盖整个视口)
```

**使用场景**:
- P1: 初始化 Dashboard 数据
- P3: 初始化文档 API 调用
- P4: 初始化文档 API 调用
- P5: 初始化条款 + 风险标记数据
- P6: 初始化报告数据

### 6.3 全局 Error 组件 (PageError)

```
PageError
├── ErrorIcon
├── errorTitle: "数据加载失败" / "服务暂不可用"
├── errorMessage: string                 (来自 API 错误响应或默认文本)
├── errorDetail: string                  (可选，request_id 等调试信息)
└── ActionButtons
    ├── RetryButton                      (重新调用当前页面的数据 API)
    └── GoHomeButton                     navigate('/dashboard')
```

**页面级 error 的触发条件**:

| 页面 | 触发条件 | 错误类型 |
|------|---------|---------|
| P1 | `GET /dashboard/stats` 或 `GET /documents` 返回 500/503 | `system_error` |
| P3 | `GET /documents/{id}` 返回 404 | `not_found` |
| P4 | `GET /documents/{id}` 返回 500/503 | `system_error` |
| P5 | 关键 API 失败 | `system_error` |
| P6 | `GET /documents/{id}/report` 返回 404/500 | `not_found` / `system_error` |

### 6.4 全局 Empty 组件 (PageEmpty)

```
PageEmpty
├── EmptyIcon
├── emptyTitle: string                   (如 "暂无审阅记录")
├── emptyDescription: string             (如 "点击上方 '新建审阅' 按钮开始")
└── ActionButton                         (可选，如 "新建审阅")
```

**使用场景**:
- P1: `tasks.items[]` 为空时，TaskList 区域显示 Empty
- P7: `documents.items[]` 为空时，列表区域显示 Empty
- Dashboard StatCards 按 0 值正常显示（非 empty）

### 6.5 Toast 通知组件

```
ToastContainer                           (固定定位, top-right)
└── ToastItem[]
    ├── type: success / error / warning / info
    ├── icon: CheckCircleIcon / XCircleIcon / AlertTriangleIcon / InfoIcon
    ├── title: string                    (如 "上传成功")
    ├── message: string                  (如 "文件 NDA-供应商-2026.pdf 已上传")
    ├── duration: number                 (ms, 默认 5000, error 类型不自动关闭)
    └── onClose: () => void
```

**Toast 触发场景 (全局)**:

| 场景 | type | title | message | 来源 |
|------|:----:|-------|---------|------|
| 上传成功 | success | "上传成功" | 文件名 + 大小 | P2 |
| 上传失败 | error | "上传失败" | 错误原因 (422) | P2 |
| 解析启动 | info | "解析已启动" | "文档解析任务已入队" | P2 LaunchBar |
| 解析完成 | success | "解析完成" | "已提取 N 个条款" (仅在 P3 后台收到时) | P3 SSE |
| 解析失败 | error | "解析失败" | 错误摘要 | P3 SSE |
| AI 审核启动 | info | "AI 审核已启动" | "4 Agent 并行执行中" | P4 StartReviewButton |
| 审核完成 | success | "审核完成" | "发现 N 项风险" | P4 SSE |
| 审核暂停 | warning | "审核已暂停" | "可从当前进度恢复" | P4 PauseResumeBar |
| 操作成功 (approve/edit/reject) | success | (操作名) | RiskFlag 摘要 | P5 |
| 操作失败 (409) | error | "提交失败" | "仍有 N 项高风险条款待审批" | P5 Submit |
| 网络异常 | error | "网络异常" | "请检查网络连接后重试" | 全局 fetch 拦截 |
| Token 过期 | warning | "登录已过期" | "请重新登录" | 全局 fetch 拦截 |

**实现**: 使用 React Context (`ToastContext`) 提供全局 `showToast({ type, title, message })` 方法。

---

## 附录 A: 未开发接口清单

以下后端接口在当前规范中被前端组件引用，但尚未在 `api_spec-v1.0.md` 中完整定义或尚未实现，标注为 **⚠️ 未开发**:

| # | 接口 | 引用位置 | 说明 |
|:--:|------|---------|------|
| 1 | `POST /auth/login` + `POST /auth/refresh` | §1.3.1 AuthGuard | JWT 签发的登录和刷新接口 |
| 2 | `GET /dashboard/recent?limit=5` | §2.3.3 RecentReviewCards | 专用"最近审阅"API (可选，MVP 可用 documents 替代) |
| 3 | `fail_stage` 字段 (PARSE / REVIEW) | §1.3.2 DocumentStatusGuard | Document.status=FAILED 时区分失败阶段 |
| 4 | `DRAFT` 状态 | §1.3.2 DocumentStatusGuard | Document.status=DRAFT 的返回和路由守卫 |
| 5 | `review_task` 对象 (嵌套) | §5.5 P4 数据映射 | `GET /documents/{id}` 响应中的 review_task 嵌套对象 |
| 6 | 解析阶段的 4 Agent SSE 事件 | §4.3.1 SSE 映射 | 除 clause_extraction 外的 Agent 解析进度事件 |
| 7 | 独立解析日志事件 | §4.3.2 日志流 | 类似 review.log 的解析阶段日志事件 |
| 8 | 恢复后的进度快照 | §5.4.2 断点恢复 | resume 响应或 SSE 事件中的已完成进度数据 |
| 9 | 单条款重试 | §5.2 PartialSuccessPanel | 部分成功时对单个待审条款的重试接口 |
| 10 | 人工接管 | §5.2 ReviewFailurePanel | 审核失败时的人工接管流程和接口 |
| 11 | 查看已解析条款 | §5.2 BottomActionBar | P4 阶段的条款预览接口 |
| 12 | 用户设置 | §6.1 TopNav UserMenu | 用户个人信息设置页面和接口 |

**前端应对策略**: 这些功能的前端组件和交互逻辑已在本规范中完整设计，但对应的 API 调用部分标记为 `⚠️ 未开发`。开发时应先实现有后端支持的路径，未开发部分以 "disabled" 或 "敬请期待" 状态渲染，**绝不伪造数据或模拟后端行为**。

---

## 附录 B: React Router 路由配置参考

```typescript
// router.tsx (Not actual code -- configuration reference)
//
// const router = createBrowserRouter([
//   {
//     path: '/login',
//     element: <LoginPage />,
//   },
//   {
//     path: '/',
//     element: <AuthGuard />,           // 认证守卫
//     children: [
//       {
//         index: true,
//         element: <Navigate to="/dashboard" replace />,
//       },
//       {
//         path: 'dashboard',
//         element: <DashboardPage />,
//       },
//       {
//         path: 'review/new',
//         element: <UploadPage />,
//       },
//       {
//         path: 'review/history',
//         element: <HistoryPage />,
//       },
//       {
//         path: 'review/:documentId',
//         element: <DocumentLayout />,   // 共享壳: DocumentHeader
//         loader: documentLoader,        // GET /documents/:documentId
//         children: [
//           {
//             index: true,
//             element: <StatusRedirect />,  // 根据 status 重定向
//           },
//           {
//             path: 'parsing',
//             element: <StatusGuard requiredStatus={['UPLOADED','PARSING','FAILED']} />,
//             children: [
//               { index: true, element: <ParsingProgressPage /> },
//             ],
//           },
//           {
//             path: 'reviewing',
//             element: <StatusGuard requiredStatus={['PARSED','REVIEWING','FAILED']} />,
//             children: [
//               { index: true, element: <ReviewProgressPage /> },
//             ],
//           },
//           {
//             path: 'workspace',
//             element: <StatusGuard requiredStatus={['REVIEWED','HUMAN_REVIEW','DRAFT']} />,
//             children: [
//               { index: true, element: <WorkspacePage /> },
//             ],
//           },
//           {
//             path: 'report',
//             element: <StatusGuard requiredStatus={['COMPLETED']} />,
//             children: [
//               { index: true, element: <ReportPage /> },
//             ],
//           },
//         ],
//       },
//       {
//         path: '*',
//         element: <NotFoundPage />,
//       },
//     ],
//   },
// ]);
```

**DocumentLayout 共享壳**:
```
DocumentLayout
├── TopNav
├── DocumentHeader                       (所有 /review/:documentId/* 子页面共享)
└── <Outlet />                           (子页面内容替换此处)
```

`DocumentHeader` 显示文档标题、类型、当前状态，数据来自父路由的 `loader` (`GET /documents/:documentId`)，通过 `useOutletContext()` 传递给子页面。

---

> **上游文档**:
> - `../06_system_architecture/frontend_design_spec-v1.0.md` -- 前端设计规范
> - `../08_api_specification/api_spec-v1.0.md` -- API 接口规范
> - `../06_system_architecture/frontend_backend_boundary_spec-v1.0.md` -- 前后端边界规范
> - `../04_interaction_design/langchain_hitl_arch-v1.0.md` -- HITL 架构规范
> **下游文档**:
> - 前端开发实现 (React 组件开发)
> - 前后端联调
