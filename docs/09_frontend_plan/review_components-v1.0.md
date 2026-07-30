# P5 审阅工作台 -- 前端组件规范 v1.0

> **版本**: v1.0
> **创建日期**: 2026-07-30
> **文档性质**: 前端组件实现规范 -- 严格基于上游 API 和交互设计，不自主发散
> **上游依赖**:
> - `docs/06_system_architecture/frontend_design_spec-v1.0.md` S5 (P5 页面树 + S5.1-S5.5 交互规范)
> - `docs/08_api_specification/api_spec-v1.0.md` S4-S5 (审核查询接口组 + 人工审核接口组)
> - `docs/06_system_architecture/frontend_backend_boundary_spec-v1.0.md` S2.3 + S3 (阶段 3 边界 + 数据归属)
> **下游读者**: 前端开发团队、产品原型设计 (`docs/05_product_prototype/`)

---

## 目录

1. [页面总览](#一页面总览)
2. [共享类型定义](#二共享类型定义)
3. [左面板组件](#三左面板组件-documentpanel)
   - [3.1 DocumentViewer](#31-documentviewer)
   - [3.2 ClauseHighlightOverlay](#32-clausehighlightoverlay)
   - [3.3 TextSelectionToolbar](#33-textselectiontoolbar)
4. [右面板组件](#四右面板组件-riskreviewpanel)
   - [4.1 RiskDashboard](#41-riskdashboard)
   - [4.2 RiskTabNav](#42-risktabnav)
   - [4.3 HighRiskPanel](#43-highriskpanel)
   - [4.4 ApprovalCard](#44-approvalcard)
   - [4.5 ClauseLocationBar](#45-clauselocationbar)
   - [4.6 AIJudgment](#46-aijudgment)
   - [4.7 PlaybookDiff](#47-playbookdiff)
   - [4.8 SuggestionBox](#48-suggestionbox)
   - [4.9 DecisionHistory](#49-decisionhistory)
   - [4.10 ActionBar](#410-actionbar)
   - [4.11 MediumRiskBatchPanel](#411-mediumriskbatchpanel)
   - [4.12 LowRiskPanel](#412-lowriskpanel)
   - [4.13 ManualFlagForm](#413-manualflagform)
5. [顶层组件](#五顶层组件)
   - [5.1 WorkspaceToolbar](#51-workspacetoolbar)
   - [5.2 SubmitConfirmDialog](#52-submitconfirmdialog)
6. [共享微组件](#六共享微组件)
   - [6.1 ConfidenceRing](#61-confidencering)
7. [附录 A: ClauseLocation -> 像素映射逻辑](#附录-a-clauselocation--像素映射逻辑)
8. [附录 B: 组件树与数据流总图](#附录-b-组件树与数据流总图)

---

## 一、页面总览

P5 审阅工作台 (`/review/{id}/workspace`) 是整个人工审批流程的核心操作页面。页面采用**左右并排布局**：

```
┌──────────────────────────────────────────────────────────────────┐
│  WorkspaceToolbar                                                 │
│  [审阅任务标题]  审批进度: 18/25  [暂存草稿]  [提交审阅(disabled)] │
├────────────────────────────┬─────────────────────────────────────┤
│  DocumentPanel (50%)       │  RiskReviewPanel (50%)               │
│  ┌──────────────────────┐  │  ┌───────────────────────────────┐  │
│  │ DocumentViewer        │  │  │ RiskDashboard                 │  │
│  │  ├── 工具栏(导航/搜索) │  │  │  ├── 统计卡片                │  │
│  │  ├── 文档渲染层       │  │  │  └── RiskTabNav               │  │
│  │  └── ClauseHighlight   │  │  │                               │  │
│  │      Overlay           │  │  │ ┌─HighRiskPanel─────────────┐│  │
│  └──────────────────────┘  │  │ │ ApprovalCard × N            ││  │
│                            │  │ └─────────────────────────────┘│  │
│  TextSelectionToolbar      │  │ ┌─MediumRiskBatchPanel────────┐│  │
│  (条件渲染)                │  │ │ batch bar + expandable list  ││  │
│                            │  │ └─────────────────────────────┘│  │
│                            │  │ ┌─LowRiskPanel────────────────┐│  │
│                            │  │ │ collapsed list + spot-check  ││  │
│                            │  │ └─────────────────────────────┘│  │
│                            │  └───────────────────────────────┘  │
├────────────────────────────┴─────────────────────────────────────┤
│  SubmitConfirmDialog (Modal, 条件渲染)                             │
│  ManualFlagForm (Modal/Overlay, 条件渲染)                          │
└──────────────────────────────────────────────────────────────────┘
```

**双向同步规则**:
- 点击右面板风险卡片 -> 左面板自动 `scrollIntoView` + 高亮闪烁定位
- 左面板划选原文区域 -> 触发 `TextSelectionToolbar` (单向，右面板不滚动)
- 键盘快捷键: `J` 下一个风险项, `K` 上一个风险项, `Enter` 确认当前, `Esc` 取消

**不可跳过约束 (4 层)**:
- L1: 后端 LangGraph `interrupt()` -- 永久等待
- L2: API 409 Conflict -- 后端校验高风险审批完整性
- L3: UI 置灰 -- "提交审阅"按钮在所有高风险审批完成前 disabled
- L4: 并发锁 -- 同一审批项不允许两个会话同时修改

---

## 二、共享类型定义

以下类型定义由本规范中所有组件共享，来自上游 API 响应数据模型。

```typescript
// ============================================================
// 枚举
// ============================================================

type RiskLevel = 'HIGH' | 'MEDIUM' | 'LOW';

type RiskFlagStatus =
  | 'PENDING_REVIEW'
  | 'CONFIRMED'
  | 'AMENDED'
  | 'REJECTED'
  | 'UNREVIEWED_AUTO_PASSED'
  | 'REVIEWED_CONFIRMED'
  | 'ESCALATED_TO_HIGH';

type RiskFlagSource = 'AI_GENERATED' | 'MANUALLY_ADDED';

type DecisionType =
  | 'APPROVE'
  | 'EDIT'
  | 'REJECT'
  | 'BATCH_CONFIRM'
  | 'SPOT_CHECK_CONFIRM'
  | 'ESCALATE'
  | 'MANUAL_ADD';

type MatchType = 'FULL' | 'PARTIAL' | 'NONE';

type DeviationType = 'MISMATCHED' | 'MISSING' | 'EXTRA';

type RenderState =
  | 'initial'   // 组件已挂载但尚未发起数据请求
  | 'loading'   // 数据请求进行中
  | 'empty'     // 数据请求成功但返回空结果集
  | 'error'     // 数据请求失败
  | 'success';  // 数据请求成功且结果非空

// ============================================================
// 核心数据模型 (来自 API 响应)
// ============================================================

interface ClauseLocation {
  page_number: number;
  paragraph_number?: number;
  char_offset_start: number;
  char_offset_end: number;
  text_hash?: string;
}

interface BoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
  page_number: number;
}

interface DiffItem {
  field: string;
  standard_value: string;
  actual_value: string;
  deviation_type: DeviationType;
}

// ============================================================
// RiskFlag (GET /documents/{id}/risk-flags)
// ============================================================

interface RiskFlag {
  risk_flag_id: string;
  clause_id: string;
  risk_level: RiskLevel;
  risk_category: string;           // e.g. "合规风险", "财务风险"
  ai_confidence: number;           // 0.0 - 1.0
  status: RiskFlagStatus;
  source: RiskFlagSource;

  // ★ 解释性字段 (差异化核心)
  rationale_text: string;          // AI 判定理由
  playbook_diff_text: string;      // Playbook 标准 vs 实际条款文本对比
  regulation_reference: string;    // 法条引用
  suggested_wording: string;       // AI 建议修改措辞

  clause_location: ClauseLocation;
  clause_text?: string;            // 条款原文 (部分接口返回)
}

// ============================================================
// Clause (GET /documents/{id}/clauses)
// ============================================================

interface Clause {
  clause_id: string;
  clause_type: string;             // e.g. "保密义务", "赔偿条款"
  clause_text: string;
  extraction_confidence: number;
  location: ClauseLocation;
}

// ============================================================
// PlaybookDiff (GET /risk-flags/{id}/playbook-diff)
// ============================================================

interface PlaybookRule {
  playbook_rule_id: string;
  name: string;                    // e.g. "NDA-保密期限"
  standard_clause_text: string;
  risk_level: RiskLevel;
  risk_category: string;
}

interface PlaybookMatch {
  match_type: MatchType;
  similarity_score: number;        // 0.0 - 1.0
  diff_items: DiffItem[];
}

interface PlaybookDiff {
  risk_flag_id: string;
  playbook_rule: PlaybookRule;
  match: PlaybookMatch;
}

// ============================================================
// ReviewDecision (GET /risk-flags/{id}/decisions)
// ============================================================

interface ReviewDecision {
  decision_id: string;
  decision_type: DecisionType;
  reviewer_id: string;
  timestamp: string;               // ISO 8601
  comment: string;
  modified_risk_level?: RiskLevel;
  modified_risk_category?: string;
  modified_suggestion?: string;
}

// ============================================================
// ReviewSummary (GET /documents/{id}/review-summary)
// ============================================================

interface ReviewSummary {
  document_id: string;
  total_high_risk: number;
  approved_high_risk: number;
  total_medium_risk: number;
  reviewed_medium_risk: number;
  low_risk_auto_passed: number;
  manual_added: number;
  completion_rate_pct: number;     // 0 - 100
  all_high_risk_resolved: boolean; // ★ 提交按钮启用条件
}

// ============================================================
// 组件间通信事件
// ============================================================

interface HighlightEvent {
  type: 'navigate_to_clause';
  clause_location: ClauseLocation;
  risk_flag_id: string;
}

interface RiskCardEvent {
  type: 'risk_selected' | 'risk_action_completed';
  risk_flag_id: string;
  action?: 'approve' | 'edit' | 'reject';
}

interface ManualAddAnchor {
  page_number: number;
  char_offset_start: number;
  char_offset_end: number;
  selected_text: string;
  bounding_box: BoundingBox;
}
```

---

## 三、左面板组件 (DocumentPanel)

### 3.1 DocumentViewer

**用途**: P5 左面板的根容器，负责文档 (PDF/DOCX) 的渲染、导航和缩放控制。

**层级**: 直接容纳文档渲染层 + `ClauseHighlightOverlay`。

```
┌─────────────────────────────────┐
│ 文档工具栏: [◀ 上一页] 第 3/8 页 [▶ 下一页]  │ 缩放: [-] 120% [+]  │ 搜索: [____]  │
├─────────────────────────────────┤
│                                 │
│     文档渲染区                   │
│     (PDF/DOCX -> HTML/Canvas)   │
│                                 │
│     ┌─────────────────────┐     │  ← 条款高亮覆盖层
│     │ ClauseHighlight      │     │    (position: absolute, z-index: 2)
│     │ Overlay              │     │
│     └─────────────────────┘     │
│                                 │
├─────────────────────────────────┤
│ 状态栏: 第 3 页  │  缩放: 120%  │  共 8 页  │
└─────────────────────────────────┘
```

#### Props 接口

```typescript
interface DocumentViewerProps {
  /** 文档 ID，用于拉取渲染文件 */
  documentId: string;

  /** 风险标记列表 (来自父容器)，用于驱动高亮覆盖层 */
  riskFlags: RiskFlag[];

  /** 当前激活的风险项 ID (从右面板点击联动) */
  activeRiskFlagId: string | null;

  /** 文档渲染源 URL，由父容器通过 GET /api/v1/documents/{id}/file 获取后传入 */
  fileUrl: string;

  /** 文档格式 */
  fileFormat: 'PDF' | 'DOCX';

  /** 总页数 */
  totalPages: number;

  /** 初始页码 */
  initialPage?: number;

  /** 初始化缩放比例 */
  initialScale?: number; // 默认 1.0

  /** 条款列表 (用于全文搜索定位) */
  clauses: Clause[];

  // -- 事件回调 --

  /** 用户划选文本触发 manual_add 流程 */
  onTextSelected: (anchor: ManualAddAnchor) => void;

  /** 用户点击高亮区域 -> 通知右面板滚动到对应卡片 */
  onHighlightClick: (event: HighlightEvent) => void;

  /** 页面变更 */
  onPageChange: (page: number) => void;

  /** 缩放变更 */
  onScaleChange: (scale: number) => void;
}
```

#### 渲染状态

| 状态 | 条件 | 渲染内容 |
|------|------|---------|
| `initial` | 组件挂载，`fileUrl` 尚未就绪 | 空占位符 + 文档图标 + "正在准备文档..." |
| `loading` | 文档文件正在下载 / 渲染引擎初始化中 | Skeleton 占位块 + 进度指示器 |
| `error` | 文档加载失败 (404/网络错误/格式不兼容) | 错误提示面板: "无法加载文档: {错误原因}" + "重试"按钮 + "下载原文"按钮 |
| `empty` | 文档为 0 页 | "此文档无可显示页面" |
| `success` | 文档成功渲染 | 完整文档渲染层 + 覆盖层 |

#### 调用的 API

| API | 方法 | 用途 | 触发时机 |
|-----|------|------|---------|
| `GET /documents/{id}/file` | 加载文档渲染文件 | 组件挂载 (由父容器调用，URL 通过 props 传入) |

#### 映射的数据模型字段

| 组件字段 | 数据模型来源 | 字段路径 |
|---------|------------|---------|
| `fileUrl` | Document.文件路径 | `GET /documents/{id}/file` 响应体 (Content-Type + body) |
| `riskFlags` | RiskFlag[] | `GET /documents/{id}/risk-flags` -> `data.risk_flags[]` |
| `clauses` | Clause[] | `GET /documents/{id}/clauses` -> `data.clauses[]` |
| `totalPages` | Document.page_count | `GET /documents/{id}` -> `data.page_count` |
| `fileFormat` | Document.format | `GET /documents/{id}` -> `data.format` |

#### 实现要点

- **渲染引擎选择**: PDF 使用 `pdf.js` 或 `react-pdf`; DOCX 使用 `mammoth.js` 转换为 HTML 后渲染。
- **字符级定位**: 渲染引擎必须暴露每个字符的页面坐标 `{char_index, page, x, y}`，供 `ClauseHighlightOverlay` 将 `char_offset_start/end` 映射为像素级 DOM 位置 (详见附录 A)。
- **缩放**: 通过 CSS `transform: scale()` 或 Canvas 重绘实现，缩放倍数变动时需同步重算高亮覆盖层像素坐标。
- **键盘导航**: 监听 `keydown` 事件，`J` 下一风险项，`K` 上一风险项，仅在焦点不在输入框内时触发。
- **全文搜索**: 基于 `clauses[].clause_text` 建立内存索引，搜索高亮走单独覆盖层 (与风险高亮层独立)。

---

### 3.2 ClauseHighlightOverlay

**用途**: 根据 `ClauseLocation` 数据在文档渲染层上方叠加三级颜色高亮区域，支持点击联动和键盘导航。

**层级**: `DocumentViewer` 的子组件，`position: absolute` / `z-index` 高于文档渲染层。

#### Props 接口

```typescript
interface ClauseHighlightOverlayProps {
  /** 风险标记列表 (驱动高亮数据源) */
  riskFlags: RiskFlag[];

  /** 当前激活的风险项 ID */
  activeRiskFlagId: string | null;

  /** 当前页码 (用于计算高亮区域的绝对坐标) */
  currentPage: number;

  /** 当前缩放比例 */
  scale: number;

  /** 当前页文本层的字符坐标映射表 (由 DocumentViewer 在渲染完成后传入) */
  charPositionMap: Map<number, { x: number; y: number; width: number; height: number }>;
  // key: char_offset (absolute across document)
  // value: pixel position relative to the document container

  /** 总页数 */
  totalPages: number;

  // -- 事件回调 --

  /** 点击高亮区域 -> 触发右面板同步滚动 */
  onHighlightClick: (riskFlagId: string, location: ClauseLocation) => void;
}
```

#### 三级颜色映射

```typescript
const RISK_LEVEL_HIGHLIGHT_COLORS: Record<RiskLevel, {
  background: string;
  border: string;
  activeBackground: string;
  label: string;
}> = {
  HIGH: {
    background: 'rgba(220, 38, 38, 0.18)',
    border: 'rgba(220, 38, 38, 0.6)',
    activeBackground: 'rgba(220, 38, 38, 0.35)',
    label: 'rgba(220, 38, 38, 1.0)',
  },
  MEDIUM: {
    background: 'rgba(234, 179, 8, 0.18)',
    border: 'rgba(234, 179, 8, 0.6)',
    activeBackground: 'rgba(234, 179, 8, 0.35)',
    label: 'rgba(180, 130, 0, 1.0)',
  },
  LOW: {
    background: 'rgba(34, 197, 94, 0.12)',
    border: 'rgba(34, 197, 94, 0.45)',
    activeBackground: 'rgba(34, 197, 94, 0.25)',
    label: 'rgba(21, 128, 61, 1.0)',
  },
};
```

#### 渲染状态

| 状态 | 条件 | 渲染内容 |
|------|------|---------|
| `initial` | `charPositionMap` 为空 (渲染引擎尚未完成当前页文本测绘) | 不渲染任何高亮 |
| `loading` | 文本层正在测绘中 | 半透明浅灰色占位条 (指示高亮区域已预留但坐标未就绪) |
| `empty` | `riskFlags.length === 0` | 不渲染 (无风险项，不需要高亮) |
| `error` | `charPositionMap` 构建失败 / 字符坐标不可用 | 静默降级: 不渲染高亮覆盖层，控制台 warn |
| `success` | `charPositionMap` 就绪 + `riskFlags.length > 0` | 渲染全部高亮区域 + 序号标记 |

#### 高亮区域 DOM 结构

每个高亮区域的渲染输出:

```html
<div
  class="clause-highlight"
  data-risk-flag-id="rf_001"
  data-risk-level="HIGH"
  style="position: absolute;
         left: {computedX}px;
         top: {computedY}px;
         width: {computedWidth}px;
         height: {computedHeight}px;
         background: rgba(220, 38, 38, 0.18);
         border-left: 3px solid rgba(220, 38, 38, 0.6);
         border-radius: 2px;
         cursor: pointer;
         transition: background 0.15s ease;"
  tabindex="0"
  role="button"
  aria-label="Risk flag rf_001: HIGH risk -- Confidentality Obligation"
>
  <span class="clause-highlight__index"
    style="position: absolute; top: -10px; left: 2px;
           font-size: 10px; font-weight: 700;
           color: rgba(220, 38, 38, 1.0);
           background: white; padding: 0 3px; border-radius: 2px;">
    #1
  </span>
</div>
```

#### 映射的数据模型字段

| 组件字段 | 数据模型来源 | 字段路径 |
|---------|------------|---------|
| 高亮位置 (left/top/width/height) | ClauseLocation | `risk_flag.clause_location.char_offset_start/end` -> 查 `charPositionMap` |
| 高亮颜色 | RiskFlag.risk_level | `risk_flag.risk_level` |
| 高亮序号标签 | RiskFlag 在已排序列表中的索引 | 前端本地 state 排序 (按 page_number + char_offset) |
| 当前页过滤 | ClauseLocation.page_number | `risk_flag.clause_location.page_number === currentPage` |

#### 关键实现: ClauseLocation -> 像素映射

详见 [附录 A](#附录-a-clauselocation--像素映射逻辑)。

---

### 3.3 TextSelectionToolbar

**用途**: 用户在文档区划选原文文本时，在划选区域上方/下方弹出的浮动工具条，作为 `manual_add` 流程的入口。

**层级**: `DocumentViewer` 的子组件，条件渲染 (仅在用户完成划选后出现)。

#### Props 接口

```typescript
interface TextSelectionToolbarProps {
  /** 划选锚点信息 (由 DocumentViewer 通过 onTextSelected 回调传入) */
  anchor: ManualAddAnchor | null;

  /** 是否可见 */
  visible: boolean;

  /** 文档容器 DOM ref (用于计算工具条的绝对定位) */
  containerRef: React.RefObject<HTMLDivElement>;

  // -- 事件回调 --

  /** 用户点击 "标记风险" */
  onMarkRisk: (anchor: ManualAddAnchor) => void;

  /** 用户点击关闭 / 在其他区域点击 */
  onDismiss: () => void;
}

interface ManualAddAnchor {
  page_number: number;
  char_offset_start: number;
  char_offset_end: number;
  selected_text: string;
  bounding_box: BoundingBox; // 划选区域在页面中的像素坐标
}
```

#### 渲染状态

| 状态 | 条件 | 渲染内容 |
|------|------|---------|
| `initial` | 组件挂载但 `visible=false` / `anchor=null` | 不渲染 (display: none) |
| `success` | `visible=true` + `anchor` 非空 | 浮动工具条 -- 显示"标记风险"按钮 + 选中的文本片段预览 |

#### 浮动工具条视觉结构

```
┌─────────────────────────────────────────────┐
│  选中文本: "违约方应赔偿守约方因此产生的..."   │  ← 截断到 40 字符
│  [🏴 标记风险]                                │  ← Primary 按钮
│  提示: 点击后将填写风险等级、类别、说明         │  ← 辅助文本
└─────────────────────────────────────────────┘
```

定位: `position: absolute`, 基于 `anchor.bounding_box` 计算, 默认显示在划选区域的**下方** (如超出视口则翻转到上方)。

#### 映射的数据模型字段

| 组件字段 | 来源 |
|---------|------|
| `anchor.page_number` | 前端从 Selection API + char position map 推算 |
| `anchor.char_offset_start/end` | 前端从 Selection API + char position map 推算 |
| `anchor.selected_text` | `window.getSelection().toString()` |
| `anchor.bounding_box` | `selection.getRangeAt(0).getBoundingClientRect()` 换算 |

---

## 四、右面板组件 (RiskReviewPanel)

### 4.1 RiskDashboard

**用途**: 右面板的顶层容器，展示审批进度统计卡片 + 三级 Tab 切换，根据 `activeTab` 渲染对应子面板。

```
┌─────────────────────────────────────────────────┐
│  RiskDashboard                                   │
│  ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌──────┐ │
│  │ 🔴 高 3 │ │ 🟡 中 5  │ │ 🟢 低 4  │ │ 60%  │ │  ← 统计卡片
│  │ 待审 1  │ │ 已审 1   │ │ 已通过   │ │ 完成 │ │
│  └─────────┘ └──────────┘ └──────────┘ └──────┘ │
│                                                  │
│  ┌──────────────┬──────────────┬──────────────┐  │
│  │ 高风险审批(3) │ 中风险批审(5) │ 低风险抽样(4) │  │  ← RiskTabNav
│  └──────────────┴──────────────┴──────────────┘  │
│                                                  │
│  ┌────────────────────────────────────────────┐  │
│  │  HighRiskPanel / MediumRiskBatchPanel /     │  │  ← Tab 内容区
│  │  LowRiskPanel (根据 activeTab 渲染)         │  │
│  └────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

#### Props 接口

```typescript
type RiskTab = 'high' | 'medium' | 'low';

interface RiskDashboardProps {
  /** 文档 ID */
  documentId: string;

  /** 全部风险标记列表 */
  riskFlags: RiskFlag[];

  /** 审批进度摘要 */
  reviewSummary: ReviewSummary;

  /** 初始激活 Tab */
  initialTab?: RiskTab; // 默认 'high'

  /** 审批摘要加载状态 */
  summaryState: RenderState;

  // -- 事件回调 --

  /** 审批操作完成后的回调 (更新 summary) */
  onActionCompleted: () => void;

  /** 手动标记创建完成后 */
  onManualFlagCreated: () => void;
}
```

#### 渲染状态

| 状态 | 条件 | 渲染内容 |
|------|------|---------|
| `initial` | 页面初始进入，尚未拉取数据 | 统计卡片 Skeleton |
| `loading` | `GET /review-summary` 或 `GET /risk-flags` 进行中 | 统计卡片 Skeleton + Tab 栏占位 |
| `error` | API 调用失败 | 错误提示: "无法加载审批数据" + "重试"按钮 |
| `empty` | `riskFlags.length === 0` | 空状态: "当前文档无 AI 发现的风险项" + "手动标记"入口 |
| `success` | 数据就绪 | 完整渲染统计卡片 + Tab 栏 + 对应面板 |

#### 调用的 API

| API | 用途 | 触发时机 |
|-----|------|---------|
| `GET /documents/{id}/review-summary` | 获取审批进度摘要 | 组件挂载 + onActionCompleted 回调 |
| `GET /documents/{id}/risk-flags` | 获取全部风险标记 | 组件挂载 |

#### 映射的数据模型字段

| 组件字段 | 数据模型来源 | 字段路径 |
|---------|------------|---------|
| 高风险统计 (总数/待审) | ReviewSummary | `total_high_risk` / `(total - approved)` |
| 中风险统计 (总数/已审) | ReviewSummary | `total_medium_risk` / `reviewed_medium_risk` |
| 低风险统计 (总数) | ReviewSummary | `low_risk_auto_passed` |
| 完成率进度环 | ReviewSummary | `completion_rate_pct` |
| Tab 数量徽标 | ReviewSummary | `total_high_risk` / `total_medium_risk` / `low_risk_auto_passed` |
| Tab 过滤后的 riskFlags | RiskFlag[] | `.filter(f => f.risk_level === tabLevel)` |

---

### 4.2 RiskTabNav

**用途**: 三级 Tab 导航栏，控制右面板在三个审批模式之间切换。属于 `RiskDashboard` 的子组件。

#### Props 接口

```typescript
interface RiskTabNavProps {
  /** 当前激活的 Tab */
  activeTab: RiskTab;

  /** 各 Tab 的风险项数量 */
  counts: { high: number; medium: number; low: number };

  /** 高风险是否全部解决 (影响低风险 Tab 的展示) */
  allHighRiskResolved: boolean;

  // -- 事件回调 --

  /** Tab 切换 */
  onTabChange: (tab: RiskTab) => void;
}
```

#### 渲染状态

| 状态 | 条件 | 渲染内容 |
|------|------|---------|
| `success` | 始终可渲染 (纯 UI 组件) | 三按钮 Tab 栏 |

#### 视觉规格

```
┌──────────────────┬──────────────────┬──────────────────┐
│ 🔴 高风险审批 (3) │ 🟡 中风险批审 (5) │ 🟢 低风险抽样 (4) │
│   [ACTIVE]       │                  │                  │
└──────────────────┴──────────────────┴──────────────────┘
```

激活态: 底部 2px 实色指示条 (颜色对应风险等级) + 粗体文字; 非激活态: 灰色文字 + `hover:opacity: 0.7`。

---

### 4.3 HighRiskPanel

**用途**: 高风险 Tab 的内容面板，渲染高风险逐条审批的 `ApprovalCard` 列表。强制执行逐条审批。

#### Props 接口

```typescript
interface HighRiskPanelProps {
  /** 高风险标记列表 (已按页面位置排序) */
  highRiskFlags: RiskFlag[];

  /** 当前正在审批的索引 */
  currentIndex: number;

  /** 当前文档的 Playbook 规则 (WARNING: 后端尚未实现批量查询接口) */
  playbookRules?: PlaybookRule[];

  // -- 事件回调 --

  /** 审批操作完成 (approve/edit/reject) */
  onActionComplete: (riskFlagId: string, decisionType: DecisionType) => void;

  /** 切换到前一个/后一个审批项 */
  onNavigate: (index: number) => void;

  /** 触发手动标记流程 */
  onManualAdd: () => void;
}
```

#### 渲染状态

| 状态 | 条件 | 渲染内容 |
|------|------|---------|
| `initial` | 数据尚未加载 | Skeleton 卡片占位 |
| `loading` | `risk-flags` API 加载中 | Skeleton 卡片占位 + "加载审批项..." |
| `empty` | `highRiskFlags.length === 0` | 空状态: "✅ 所有高风险条款已审批完成" + 引导切换 Tab |
| `error` | 加载失败 | "无法加载高风险审批项" + "重试" |
| `success` | 数据就绪 | 逐条渲染 ApprovalCard + "第 N/M 项" 计数器 |

#### 审批进度计数器

渲染于 ApprovalCard 列表顶部:

```
审批进度: 第 2 / 8 项 (已完成 1 项，剩余 6 项)
[▓▓▓▓░░░░░░░░░░░░░░░░] 25%
```

#### 强制约束

- 全部高风险审批完成前，父容器 `WorkspaceToolbar` 的"提交审阅"按钮置灰 disabled。
- 逐条模式下，每次只展示当前审批卡片 (或展示全部但已审批的折叠收起)。

---

### 4.4 ApprovalCard

**核心组件.** 风险审批卡片，包含 6 个结构化区域。被 `HighRiskPanel`、`MediumRiskBatchPanel`、`LowRiskPanel` 三处复用，通过 `mode` prop 控制交互级别。

```
┌───────────────────────────────────────────────────────┐
│ ① ClauseLocationBar                                    │
│    [保密义务] "接收方同意对披露方的保密信息予以严格..."   │
│    第 3 页 · 第 2 段          [📍 在文档中查看]         │
├───────────────────────────────────────────────────────┤
│ ② AIJudgment                                           │
│    🔴 HIGH 风险  │  合规风险  │  置信度 [◉ 87%]         │
├───────────────────────────────────────────────────────┤
│ ③ PlaybookDiff                                         │
│    ┌─ 标准条款 ──────────────────────────────────────┐ │
│    │ 保密义务自披露之日起 3 年内有效                    │ │
│    └────────────────────────────────────────────────┘ │
│    ┌─ 实际条款 ──────────────────────────────────────┐ │
│    │ 保密义务在协议终止后永久有效  [❌ 偏差]           │ │
│    └────────────────────────────────────────────────┘ │
│    相似度: 42% · 偏差项: 保密期限: 3年 → 永久           │
├───────────────────────────────────────────────────────┤
│ ④ SuggestionBox                                        │
│    💡 AI 建议修改措辞:                                  │
│    "保密义务自披露之日起 5 年内有效"                     │
│    [📋 复制建议措辞]                                    │
├───────────────────────────────────────────────────────┤
│ ⑤ DecisionHistory (条件渲染: decisions.length > 0)      │
│    📜 历史相似条款审阅决策:                              │
│    · 2026-07-15 张三: EDIT 降级至 MEDIUM "可协商5年"    │
│    · 2026-06-20 李四: APPROVE "确认存在风险"            │
├───────────────────────────────────────────────────────┤
│ ⑥ ActionBar                                            │
│    [✅ 同意 (Approve)]  [✏️ 编辑 (Edit)]  [❌ 驳回 (Reject)] │
└───────────────────────────────────────────────────────┘
```

#### Props 接口

```typescript
type ApprovalCardMode = 'full' | 'expanded' | 'readonly';

interface ApprovalCardProps {
  /** 风险标记数据 */
  riskFlag: RiskFlag;

  /** 卡片模式 */
  mode: ApprovalCardMode;
  // 'full' -- 高风险逐条审批: 6 区全部可交互
  // 'expanded' -- 中风险展开审批: 同 full 但批量操作优先
  // 'readonly' -- 低风险抽样展示 / 已审批查看: 所有区只读，ActionBar 隐藏

  /** Playbook 对比数据 */
  playbookDiff: PlaybookDiff | null;

  /** 审批历史 */
  decisions: ReviewDecision[];

  /** 是否当前聚焦 (从键盘导航联动) */
  isFocused: boolean;

  /** Playbook 对比数据加载状态 */
  diffState: RenderState;

  /** 审批历史加载状态 */
  decisionsState: RenderState;

  // -- 事件回调 --

  /** 同意 AI 标记 */
  onApprove: (riskFlagId: string, comment?: string) => void;

  /** 编辑修正 */
  onEdit: (riskFlagId: string, edits: EditPayload) => void;

  /** 驳回 (需填写理由) */
  onReject: (riskFlagId: string, reason: string) => void;

  /** 点击"在文档中查看" -> 触发左面板同步 */
  onViewInDocument: (clauseLocation: ClauseLocation) => void;

  /** 卡片获得焦点 */
  onFocus: (riskFlagId: string) => void;
}

interface EditPayload {
  comment: string;                         // 必填, >=10 字符
  modified_risk_level?: RiskLevel;
  modified_risk_category?: string;
  modified_suggestion?: string;
}
```

#### 渲染状态 (整体卡片)

| 状态 | 条件 | 渲染内容 |
|------|------|---------|
| `initial` | 卡片挂载但子数据未请求 | 6 区骨架占位 |
| `loading` | PlaybookDiff 或 Decisions 加载中 | Zone ③④ 显示 Skeleton; Zone ①② 可先行渲染 (数据来自 riskFlag) |
| `error` | 子数据加载失败 | Zone ③ 显示 "Playbook 对比数据暂不可用"; Zone ⑤ 显示 "历史记录加载失败"; ActionBar 仍可用 |
| `empty` | riskFlag 数据存在但 decisions 为空 | Zone ⑤ 不渲染 (无历史记录) |
| `success` | 全部数据就绪 | 6 区完整渲染 |

#### 调用的 API

| API | 用途 | 触发时机 |
|-----|------|---------|
| `GET /risk-flags/{id}/playbook-diff` | 获取 Playbook 对比 | 卡片展开/获得焦点时 (懒加载) |
| `GET /risk-flags/{id}/decisions` | 获取审批历史 | 卡片展开/获得焦点时 |
| `POST /risk-flags/{id}/approve` | 同意操作 | 用户点击"同意" |
| `POST /risk-flags/{id}/edit` | 编辑操作 | 用户修改后点击保存 |
| `POST /risk-flags/{id}/reject` | 驳回操作 | 用户填写理由后确认 |

#### 映射的数据模型字段

| Zone | 组件字段 | 数据模型来源 | 字段路径 |
|------|---------|------------|---------|
| ① | 条款类型 | Clause | `clause.clause_type` (需通过 `clause_id` 关联) |
| ① | 原文引用 | RiskFlag | `clause_text` (截取前 50 字符) |
| ① | 页面/段落 | ClauseLocation | `clause_location.page_number` / `.paragraph_number` |
| ② | 风险等级 | RiskFlag | `risk_level` |
| ② | 风险类别 | RiskFlag | `risk_category` |
| ② | AI 置信度 | RiskFlag | `ai_confidence` |
| ③ | 标准条款 | PlaybookDiff | `playbook_rule.standard_clause_text` |
| ③ | 实际条款 | PlaybookDiff | 由 `playbook_diff_text` + `match.diff_items[]` 生成 diff 视图 |
| ③ | 相似度 | PlaybookDiff | `match.similarity_score` |
| ④ | 修改建议 | RiskFlag | `suggested_wording` |
| ④ | AI 判定理由 | RiskFlag | `rationale_text` |
| ④ | 法条引用 | RiskFlag | `regulation_reference` |
| ⑤ | 历史决策列表 | ReviewDecision[] | `decisions[]` |
| ⑥ | 操作按钮状态 | RiskFlag | `status` (根据当前状态决定哪些按钮可用) |

---

### 4.5 ClauseLocationBar

**用途**: ApprovalCard 的 Zone ① -- 展示条款类型、原文引用片段、"在文档中查看"定位按钮。

#### Props 接口

```typescript
interface ClauseLocationBarProps {
  /** 条款类型 */
  clauseType: string;

  /** 原文引用 (截取至 80 字符) */
  textExcerpt: string;

  /** 条款位置 */
  location: ClauseLocation;

  /** 所在页码 (人类可读) */
  pageLabel: string;

  /** 所在段落 (如有) */
  paragraphLabel?: string;

  // -- 事件回调 --

  /** 点击"在文档中查看" -> 触发 DocumentViewer 滚动定位 */
  onViewInDocument: (location: ClauseLocation) => void;
}
```

#### 渲染状态

| 状态 | 条件 | 渲染内容 |
|------|------|---------|
| `success` | 始终可渲染 (纯展示) | 条款类型 Tag + 原文引用 + "在文档中查看"链接按钮 |

#### 视觉结构

```
┌───────────────────────────────────────────────────────┐
│ [保密义务] "接收方同意对披露方的保密信息予以严格保密..."  │
│  第 3 页 · 第 2 段                     [📍 在文档中查看] │
└───────────────────────────────────────────────────────┘
```

- 条款类型: 小 Tag (e.g. `#ef4444` 背景高线, 白色文字)
- 原文引用: 灰色斜体, `-webkit-line-clamp: 2`, 超出省略号
- "在文档中查看": 文本链接样式, 可选加一个定位图标

---

### 4.6 AIJudgment

**用途**: ApprovalCard 的 Zone ② -- 展示 AI 的风险判定结果: 风险等级标识、风险类别、AI 置信度进度环。

#### Props 接口

```typescript
interface AIJudgmentProps {
  /** 风险等级 */
  riskLevel: RiskLevel;

  /** 风险类别 */
  riskCategory: string;

  /** AI 置信度 (0.0 - 1.0) */
  aiConfidence: number;

  /** 标记来源 (影响展示样式) */
  source: RiskFlagSource;

  /** ★ 解释性字段: AI 判定理由 */
  rationaleText: string;

  /** ★ 解释性字段: 法条引用 */
  regulationReference: string;
}
```

#### 渲染状态

| 状态 | 条件 | 渲染内容 |
|------|------|---------|
| `success` | 始终可渲染 (纯展示) | 等级标识 + 类别 + ConfidenceRing + 可展开的理由/法条引用 |

#### 视觉结构

```
┌────────────────────────────────────────────────────────────┐
│  🔴 HIGH 风险    │    合规风险    │    [◉]  87% 置信度      │
│                                                             │
│  📋 AI 判定理由:                                             │
│  保密期限为'永久'，超过行业标准的 3-5 年，且未设定期限上限...   │  ← rationale_text
│                                                             │
│  📚 法规参考:                                                │
│  参照《商业秘密保护规定》第 12 条，保密期限应合理确定...       │  ← regulation_reference
└────────────────────────────────────────────────────────────┘
```

#### 关键设计: 置信度进度环

使用 `ConfidenceRing` 微组件渲染:
- 蓝色填充环 (`stroke-dasharray` = confidence * circumference)
- 中心数字百分比
- 置信度 < 60% 显示警告图标 (AI 不确定指示)

#### 映射的数据模型字段

| 组件字段 | 数据模型来源 | 字段路径 |
|---------|------------|---------|
| `riskLevel` | RiskFlag | `risk_level` |
| `riskCategory` | RiskFlag | `risk_category` |
| `aiConfidence` | RiskFlag | `ai_confidence` |
| `rationaleText` | RiskFlag | `rationale_text` |
| `regulationReference` | RiskFlag | `regulation_reference` |
| `source` | RiskFlag | `source` |

---

### 4.7 PlaybookDiff

**用途**: ApprovalCard 的 Zone ③ -- 标准条款与实际条款的 diff 对比视图。

#### Props 接口

```typescript
interface PlaybookDiffProps {
  /** Playbook 对比数据 */
  playbookDiff: PlaybookDiff | null;

  /** 加载状态 */
  state: RenderState;

  /** Playbook 对比的纯文本 (来自 riskFlag.playbook_diff_text, 用于降级展示) */
  fallbackDiffText: string;
}
```

#### 渲染状态

| 状态 | 条件 | 渲染内容 |
|------|------|---------|
| `initial` | 尚未触发加载 | 折叠状态: "Playbook 对比 [展开]" 按钮 |
| `loading` | API 调用进行中 | Skeleton: 两个并排文本框的占位 |
| `error` | API 调用失败 | 降级展示: 使用 `fallbackDiffText` 纯文本渲染; "结构化对比数据加载失败，以下是 AI 生成的对比摘要" |
| `empty` | `playbookDiff.match.match_type === 'FULL'` (完全匹配, 无差异) | "本条款与 Playbook 标准一致" 绿色文字 |
| `success` | 对比数据就绪 | 上 (标准条款) / 下 (实际条款) 对比视图 + 逐字段差异表 |

#### 视觉结构 (success 状态)

```
┌──────────────────────────────────────────────────────────┐
│  Playbook 对比                             相似度: 42%   │
│                                                           │
│  ┌─ 标准条款 (NDA-保密期限) ───────────────────────────┐  │
│  │ 保密义务自披露之日起 3 年内有效                       │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                           │
│  ┌─ 实际条款 ─────────────────────────────────────────┐  │
│  │ 保密义务在协议终止后永久有效       [❌ 偏差]          │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                           │
│  差异明细:                                                │
│  ┌──────────┬──────────┬──────────┬─────────────────┐    │
│  │ 字段     │ 标准值   │ 实际值   │ 偏差类型         │    │
│  ├──────────┼──────────┼──────────┼─────────────────┤    │
│  │ 保密期限 │ 3 年     │ 永久     │ 🔴 MISMATCHED   │    │
│  └──────────┴──────────┴──────────┴─────────────────┘    │
└──────────────────────────────────────────────────────────┘
```

#### 调用的 API

| API | 用途 | 触发时机 |
|-----|------|---------|
| `GET /risk-flags/{id}/playbook-diff` | 获取结构化 diff 数据 | 卡片展开时懒加载 |

⚠️ **标注**: 后端 PlaybookRule 管理接口 (CRUD `/playbooks`) **已定义但 P5 不直接调用** -- P5 仅通过 `GET /risk-flags/{id}/playbook-diff` 获取对比结果。

#### 映射的数据模型字段

| 组件字段 | 数据模型来源 | 字段路径 |
|---------|------------|---------|
| 标准条款文本 | PlaybookDiff | `playbook_rule.standard_clause_text` |
| 规则名称 | PlaybookDiff | `playbook_rule.name` |
| 匹配类型 | PlaybookDiff | `match.match_type` |
| 相似度 | PlaybookDiff | `match.similarity_score` |
| 逐字段差异 | PlaybookDiff | `match.diff_items[].field / .standard_value / .actual_value / .deviation_type` |
| 降级纯文本 | RiskFlag | `playbook_diff_text` |

---

### 4.8 SuggestionBox

**用途**: ApprovalCard 的 Zone ④ -- 展示 AI 建议的修改措辞，支持一键复制和编辑模式下修改。

#### Props 接口

```typescript
interface SuggestionBoxProps {
  /** AI 建议修改措辞 */
  suggestedWording: string;

  /** 是否处于编辑模式 */
  editable: boolean;

  /** 编辑模式下的修改值 (由父容器 ActionBar 的 edit 流程传入) */
  editValue?: string;

  // -- 事件回调 --

  /** 编辑模式下值变更 */
  onEditChange?: (value: string) => void;

  /** 一键复制建议措辞 */
  onCopy: (text: string) => void;
}
```

#### 渲染状态

| 状态 | 条件 | 渲染内容 |
|------|------|---------|
| `success` (展示) | `editable=false`, `suggestedWording` 非空 | 建议措辞文本 + "复制建议措辞"按钮 |
| `empty` (展示) | `suggestedWording` 为空或仅空白 | "AI 未提供修改建议" 灰色占位文字 |
| `success` (编辑) | `editable=true` | 可编辑的 textarea + 字符计数 |

#### 视觉结构

```
┌──────────────────────────────────────────────────────────┐
│  💡 AI 建议修改措辞                                       │
│                                                           │
│  "保密义务自披露之日起 5 年内有效"                          │  ← 可选中
│                                                           │
│  [📋 复制建议措辞]                                        │
└──────────────────────────────────────────────────────────┘
```

#### 映射的数据模型字段

| 组件字段 | 数据模型来源 | 字段路径 |
|---------|------------|---------|
| `suggestedWording` | RiskFlag | `suggested_wording` |

---

### 4.9 DecisionHistory

**用途**: ApprovalCard 的 Zone ⑤ -- 展示历史相似条款的审阅决策记录。

#### Props 接口

```typescript
interface DecisionHistoryProps {
  /** 审批决策历史列表 */
  decisions: ReviewDecision[];

  /** 加载状态 */
  state: RenderState;
}
```

#### 渲染状态

| 状态 | 条件 | 渲染内容 |
|------|------|---------|
| `loading` | API 进行中 | Skeleton 列表 (2 条占位) |
| `empty` | `decisions.length === 0` | 不渲染 (隐藏整个 Zone ⑤) |
| `error` | API 失败 | "历史记录加载失败" + "重试" |
| `success` | `decisions.length > 0` | 时间线列表 (最多显示最近 5 条, 更多 -> "查看全部 N 条记录") |

#### 视觉结构

```
┌──────────────────────────────────────────────────────────┐
│  📜 历史相似条款审阅决策 (2 条记录)                        │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐ │
│  │ 2026-07-15  张三 | EDIT                             │ │
│  │ 风险等级从 HIGH 降为 MEDIUM，保密期限可协商为 5 年     │ │
│  └─────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────┐ │
│  │ 2026-06-20  李四 | APPROVE                          │ │
│  │ 确认存在风险                                         │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                           │
│  [查看全部 2 条记录]                                       │
└──────────────────────────────────────────────────────────┘
```

#### 调用的 API

| API | 用途 | 触发时机 |
|-----|------|---------|
| `GET /risk-flags/{id}/decisions` | 获取某风险标记的审批历史 | 卡片展开时懒加载 |

#### 映射的数据模型字段

| 组件字段 | 数据模型来源 | 字段路径 |
|---------|------------|---------|
| 决策时间 | ReviewDecision | `timestamp` |
| 决策人 | ReviewDecision | `reviewer_id` |
| 决策类型 | ReviewDecision | `decision_type` |
| 决策备注 | ReviewDecision | `comment` |
| 修改后等级 | ReviewDecision | `modified_risk_level` |

---

### 4.10 ActionBar

**用途**: ApprovalCard 的 Zone ⑥ -- 三个操作按钮: 同意 / 编辑 / 驳回。

#### Props 接口

```typescript
interface ActionBarProps {
  /** 风险标记 ID */
  riskFlagId: string;

  /** 当前状态 (决定哪些按钮可用) */
  status: RiskFlagStatus;

  /** 卡片模式 */
  mode: ApprovalCardMode;

  /** 是否正在提交操作 (loading) */
  isSubmitting: boolean;

  /** 错误信息 (操作失败后显示) */
  errorMessage: string | null;

  // -- 事件回调 --

  /** 同意 */
  onApprove: (riskFlagId: string, comment?: string) => void;

  /** 编辑 (触发进入编辑模式) */
  onEdit: (riskFlagId: string, edits: EditPayload) => void;

  /** 驳回 (触发驳回对话框) */
  onReject: (riskFlagId: string, reason: string) => void;
}
```

#### 渲染状态

| 状态 | 条件 | 渲染内容 |
|------|------|---------|
| `success` (可操作) | `mode !== 'readonly'` 且 `status === PENDING_REVIEW` | [同意] [编辑] [驳回] 三个按钮均可用 |
| `success` (已操作) | `status !== PENDING_REVIEW` | 显示操作结果标签 (e.g. "已确认" / "已修正" / "已驳回") + "撤销"链接 (可选) |
| `readonly` | `mode === 'readonly'` | 不渲染操作按钮，仅显示只读状态标签 |
| `loading` (提交中) | `isSubmitting === true` | 按钮置灰 + loading spinner |
| `error` | `errorMessage` 非空 | 在按钮下方显示红色错误提示文字 |

#### 视觉结构 (可操作状态)

```
┌──────────────────────────────────────────────────────────┐
│  [✅ 同意 (Approve)]  [✏️ 编辑 (Edit)]  [❌ 驳回 (Reject)] │
│                                                           │
│  ⚠️ 操作失败: 网络连接超时，请重试                          │  ← 条件渲染
└──────────────────────────────────────────────────────────┘
```

#### 交互流程

**Approve 流程**:
1. 用户点击"同意"
2. 可选: 弹出微小备注输入框 (非必填)
3. 调用 `POST /risk-flags/{id}/approve`
4. 成功 -> `onApprove` 回调 -> 父容器更新 summary + 切换下一审批项
5. 失败 -> 显示 `errorMessage`

**Edit 流程**:
1. 用户点击"编辑"
2. 卡片切换为编辑模式: 可编辑区域 (risk_level 下拉框 / risk_category 下拉框 / suggestion 文本区)
3. 用户修改后点击"保存修改"
4. 调用 `POST /risk-flags/{id}/edit`
5. 成功 -> `onEdit` 回调
6. 失败 -> 显示错误

**Reject 流程**:
1. 用户点击"驳回"
2. 弹出驳回对话框: 文本输入框 (必填, >=10 字符) + 字符计数 + [取消] [确认驳回] 按钮
3. 用户填写理由并确认
4. 调用 `POST /risk-flags/{id}/reject`
5. 成功 -> `onReject` 回调 -> 该标记从卡片列表移除
6. 失败 -> 显示错误

#### 调用的 API

| API | 用途 |
|-----|------|
| `POST /risk-flags/{id}/approve` | 同意 |
| `POST /risk-flags/{id}/edit` | 编辑 |
| `POST /risk-flags/{id}/reject` | 驳回 |

---

### 4.11 MediumRiskBatchPanel

**用途**: 中风险 Tab 的内容面板。支持批量操作 ("全部确认") 和可展开列表项。

#### Props 接口

```typescript
interface MediumRiskBatchPanelProps {
  /** 中风险标记列表 */
  mediumRiskFlags: RiskFlag[];

  /** 全部风险标记 (用于获取 clause_type 等关联信息) */
  allClauses: Clause[];

  /** Playbook 对比数据缓存 (按 risk_flag_id 索引) */
  playbookDiffCache: Record<string, PlaybookDiff | null>;

  /** 审批历史缓存 */
  decisionsCache: Record<string, ReviewDecision[]>;

  /** 当前展开的风险项 ID */
  expandedFlagId: string | null;

  // -- 事件回调 --

  /** 批量确认 */
  onBatchApprove: (riskFlagIds: string[]) => void;

  /** 展开/折叠某个风险项 */
  onToggleExpand: (riskFlagId: string) => void;

  /** 个别审批操作 (复用 ApprovalCard 的 approve/edit/reject) */
  onApprove: (riskFlagId: string) => void;
  onEdit: (riskFlagId: string, edits: EditPayload) => void;
  onReject: (riskFlagId: string, reason: string) => void;

  /** "在文档中查看" */
  onViewInDocument: (clauseLocation: ClauseLocation) => void;
}
```

#### 渲染状态

| 状态 | 条件 | 渲染内容 |
|------|------|---------|
| `initial` | 数据尚未加载 | Skeleton 列表 + 批量操作条占位 |
| `loading` | `risk-flags` 或 clauses 加载中 | Skeleton 列表 |
| `empty` | `mediumRiskFlags.length === 0` | "无中风险条款" 空状态 |
| `error` | 加载失败 | 错误提示 + "重试" |
| `success` | 数据就绪 | 批量操作条 + 可展开列表 |

#### 视觉结构

```
┌──────────────────────────────────────────────────────────┐
│  批量操作: [✅ 全部确认 (5 项)]         已标记: 1 项已审   │
├──────────────────────────────────────────────────────────┤
│  ▶ 保密义务 · 合规风险 · UNREVIEWED_AUTO_PASSED    [展开]  │
│  ▼ 赔偿条款 · 财务风险 · REVIEWED_CONFIRMED        [折叠]  │
│  │  ┌──────────────────────────────────────────────┐     │
│  │  │  ApprovalCard (mode='expanded')               │     │  ← 展开后复用
│  │  └──────────────────────────────────────────────┘     │
│  ▶ 管辖法律 · 合规风险 · UNREVIEWED_AUTO_PASSED    [展开]  │
│  ▶ 终止条款 · 财务风险 · UNREVIEWED_AUTO_PASSED    [展开]  │
│  ▶ 通知条款 · 合规风险 · UNREVIEWED_AUTO_PASSED    [展开]  │
└──────────────────────────────────────────────────────────┘
```

#### 列表项 (未展开状态)

每行显示:
- 折叠/展开指示器 (`▶` / `▼`)
- 条款类型 (小 Tag)
- 风险类别
- **标记状态**: `UNREVIEWED_AUTO_PASSED` (灰色"未审核") vs `REVIEWED_CONFIRMED` (绿色"已确认")
- 展开按钮

#### 批量确认交互

1. 用户点击"全部确认"
2. 弹出确认对话框: "确认将全部 5 项中风险条款标记为自动通过？"
3. 用户确认
4. 调用 `POST /risk-flags/batch-approve` (传全部中风险 flag IDs)
5. 成功 -> 所有列表项标记更新为 `UNREVIEWED_AUTO_PASSED`; 或已个别审核的保持 `REVIEWED_CONFIRMED`
6. 失败 -> 错误提示

#### 调用的 API

| API | 用途 |
|-----|------|
| `POST /risk-flags/batch-approve` | 批量确认中风险 |
| `GET /risk-flags/{id}/playbook-diff` | 懒加载展开项的 Playbook 对比 |
| `GET /risk-flags/{id}/decisions` | 懒加载展开项的审批历史 |

---

### 4.12 LowRiskPanel

**用途**: 低风险 Tab 的内容面板。默认折叠列表 + 抽样审计入口。

#### Props 接口

```typescript
interface LowRiskPanelProps {
  /** 低风险标记列表 */
  lowRiskFlags: RiskFlag[];

  /** 抽样审计结果 (POST /sample 返回) */
  sampledFlags: RiskFlag[] | null;

  /** 抽样审计加载状态 */
  sampleState: RenderState;

  /** 抽样信息 */
  sampleInfo: {
    sample_size: number;
    total_low_risk: number;
    seed_info: string;
  } | null;

  // -- 事件回调 --

  /** 触發抽样审计 */
  onSpotCheck: (sampleRatio?: number) => void;

  /** 抽样中的升级操作 */
  onEscalate: (riskFlagId: string, reason: string) => void;

  /** 抽样中的确认操作 */
  onConfirm: (riskFlagId: string) => void;

  /** "在文档中查看" */
  onViewInDocument: (clauseLocation: ClauseLocation) => void;
}
```

#### 渲染状态

| 状态 | 条件 | 渲染内容 |
|------|------|---------|
| `loading` | 风险标记列表加载中 | Skeleton 折叠列表 |
| `empty` | `lowRiskFlags.length === 0` | "无低风险条款" 空状态 |
| `success` (折叠) | 默认状态，用户未展开 | 折叠列表: "AI 已自动通过 K 项低风险条款 [展开查看]" + 抽样入口 |
| `success` (展开) | 用户点击展开 | 低风险项完整列表 (只读表格) |
| `success` (抽样) | 抽样结果已展示 | 抽样审计详情面板 (复用 ApprovalCard readonly 模式) |

#### 视觉结构 (折叠状态)

```
┌──────────────────────────────────────────────────────────┐
│  ✅ AI 已自动通过 4 项低风险条款                  [展开查看]│
│                                                           │
│  ┌─────────────────────────────────────────────────────┐ │
│  │ 🔍 抽样审计                                         │ │
│  │ 根据确定性种子 (sha256(d_xxx_user_xxx)[:8]) 抽取      │ │
│  │ [抽查 1 项 (本次抽取 11%)]                           │ │
│  └─────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
```

#### 抽样审计详情 (展开后)

```
┌──────────────────────────────────────────────────────────┐
│  🔍 抽样审计结果 (1/4 项，抽取比例 11%)                    │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐ │
│  │ ApprovalCard (mode='readonly')                       │ │
│  │ ① 通知条款 · 第 7 页                                 │ │
│  │ ② LOW · 合规风险 · 置信度 92%                        │ │
│  │ ③ "通知条款格式标准，无明显风险"                      │ │
│  │ ④ AI 建议: 无需修改                                  │ │
│  │                                                      │ │
│  │ [✅ 确认无问题] [⚠️ 升级为高风险]                     │ │  ← 抽样操作
│  └─────────────────────────────────────────────────────┘ │
│                                                           │
│  [再抽一组] (11%)                                         │
└──────────────────────────────────────────────────────────┘
```

#### 调用的 API

| API | 用途 | 触发时机 |
|-----|------|---------|
| `POST /risk-flags/sample` | 确定性随机抽样 | 用户点击"抽查 N 项" |
| `POST /risk-flags/{id}/escalate` | 抽样中发现需升级项 | 用户点击"升级为高风险" |
| `POST /risk-flags/{id}/approve` | 抽样中确认通过 | 用户点击"确认无问题" |
| `GET /risk-flags/{id}/playbook-diff` | 抽样详情中的 Playbook 对比 | 抽样结果展示时懒加载 |
| `GET /risk-flags/{id}/decisions` | 抽样详情中的审批历史 | 抽样结果展示时懒加载 |

⚠️ **标注**: `POST /risk-flags/sample` 后端已定义但确定性种子算法细节取决于后端实现。前端仅需传递 `document_id` + `sample_ratio`。

#### 升级路径 (escalate)

1. 用户在抽样审计中发现问题项
2. 点击"升级为高风险"
3. 弹出升级确认对话框: "确认将'通知条款'升级为高风险？升级后需强制审批且不可逆"
4. 用户填写升级理由并确认
5. 调用 `POST /risk-flags/{id}/escalate`
6. 成功 -> 该项从低风险列表移除，出现在高风险队列中
7. 前端更新 `reviewSummary` + 切换 Tab 高亮提示

---

### 4.13 ManualFlagForm

**用途**: 手动补充标记的表单组件，可由两种方式触发: (1) 左面板划选文本 -> `TextSelectionToolbar` -> "标记风险"按钮; (2) 右面板直接点击"手动标记"按钮。

⚠️ **标注**: 此组件对应的 API `POST /risk-flags/manual` 后端已定义，但 MVP 阶段的多人协作场景 (`reviewer_id` 分配) 需根据实际用户系统确定。

#### Props 接口

```typescript
interface ManualFlagFormProps {
  /** 文档 ID */
  documentId: string;

  /** 划选锚点 (来自 TextSelectionToolbar; 如果是手动按钮触发则为 null) */
  anchor: ManualAddAnchor | null;

  /** 是否显示为模态框 / 滑出面板 */
  visible: boolean;

  /** 初始值 (用于编辑已有手动标记 -- v2) */
  initialValues?: ManualFlagInitialValues;

  // -- 事件回调 --

  /** 提交成功 */
  onSubmitSuccess: (riskFlagId: string) => void;

  /** 取消 */
  onCancel: () => void;
}

interface ManualFlagInitialValues {
  risk_level: RiskLevel;
  risk_category: string;
  description: string;
  clause_text?: string;
}
```

#### 渲染状态

| 状态 | 条件 | 渲染内容 |
|------|------|---------|
| `initial` | `visible=true`，表单尚未填写 | 空表单 (预填 `anchor.selected_text` 如果存在) |
| `loading` (提交中) | 表单已提交，等待 API 响应 | 表单字段 disabled + "正在创建标记..." 进度指示 |
| `error` (校验失败) | 前端校验不通过 | 字段级错误提示 (红色边框 + 错误文字) |
| `error` (提交失败) | API 返回错误 | 表单顶部红色横幅: "创建标记失败: {原因}" + "重试" |
| `success` (提交成功) | API 返回 201 | 短暂显示成功提示 -> 自动关闭 -> `onSubmitSuccess` 回调 |

#### 视觉结构

```
┌──────────────────────────────────────────────────────────┐
│  🏴 手动补充风险标记                                       │  [✕ 关闭]
├──────────────────────────────────────────────────────────┤
│                                                           │
│  选中原文 (如有):                                         │
│  ┌─────────────────────────────────────────────────────┐ │
│  │ "违约方应赔偿守约方因此产生的合理费用..."              │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                           │
│  风险等级 *                                               │
│  ┌──────────────────────────────────────┐                │
│  │ 🔴 HIGH  ▼                           │  ← 下拉选择框   │
│  └──────────────────────────────────────┘                │
│                                                           │
│  风险类别 *                                               │
│  ┌──────────────────────────────────────┐                │
│  │ 请选择风险类别  ▼                      │  ← 下拉选择框   │
│  │ ──────────────────────────────────── │                │
│  │ 合规风险                               │                │
│  │ 财务风险                               │                │
│  │ 数据保护风险                           │                │
│  │ ...                                   │                │
│  └──────────────────────────────────────┘                │
│                                                           │
│  补充说明 * (至少 10 个字符)                               │
│  ┌──────────────────────────────────────┐                │
│  │ 赔偿上限条款使用了模糊的'合理费用'      │  ← 文本域      │
│  │ 表述，可能导致争议。建议明确赔偿上      │                │
│  │ 限金额或计算方式。                     │                │
│  └──────────────────────────────────────┘                │
│  已输入 42 字符                                           │
│                                                           │
│  ⚠️ 手动标记将直接计入高风险队列，需强制人工审批              │
│                                                           │
├──────────────────────────────────────────────────────────┤
│                    [取消]  [🏴 创建标记]                    │
└──────────────────────────────────────────────────────────┘
```

#### 前端校验规则

| 字段 | 校验规则 | 错误提示 |
|------|---------|---------|
| `risk_level` | 必选 | "请选择风险等级" |
| `risk_category` | 必选 | "请选择风险类别" |
| `description` | 必填, >=10 字符 | "补充说明至少需要 10 个字符" |

#### 调用的 API

| API | 用途 |
|-----|------|
| `POST /risk-flags/manual` | 创建人工来源风险标记 |

#### 映射的数据模型字段

| 表单字段 | 请求字段 | 类型 |
|---------|---------|------|
| 风险等级 | `risk_level` | RiskLevel |
| 风险类别 | `risk_category` | string |
| 补充说明 | `description` | string |
| 划选位置 | `clause_location` | ClauseLocation (来自 anchor) |
| 划选原文 | `clause_text` | string (来自 anchor.selected_text) |
| 所属文档 | `document_id` | string |

---

## 五、顶层组件

### 5.1 WorkspaceToolbar

**用途**: P5 页面顶部工具栏，展示审阅任务标题、审批进度、操作按钮 (暂存草稿 / 提交审阅)。

#### Props 接口

```typescript
interface WorkspaceToolbarProps {
  /** 文档标题 */
  documentTitle: string;

  /** 文档 ID */
  documentId: string;

  /** 审批进度摘要 */
  reviewSummary: ReviewSummary;

  /** 摘要加载状态 */
  summaryState: RenderState;

  /** 提交按钮是否可用 (all_high_risk_resolved === true) */
  canSubmit: boolean;

  /** 是否正在提交 (loading) */
  isSubmitting: boolean;

  /** 最后保存时间 */
  lastSavedAt: string | null;

  // -- 事件回调 --

  /** 暂存草稿 */
  onSaveDraft: () => void;

  /** 点击提交 -> 打开 SubmitConfirmDialog */
  onSubmitClick: () => void;
}
```

#### 渲染状态

| 状态 | 条件 | 渲染内容 |
|------|------|---------|
| `success` | 数据就绪 | 完整工具栏 |
| `loading` | summary 加载中 | 标题 + 按钮 (进度数字显示为 "--") |

#### 视觉结构

```
┌────────────────────────────────────────────────────────────────┐
│  📄 NDA-供应商-2026.pdf    │  审批进度: 18/25 (72%)            │
│                            │  高风险 2/3 | 中风险 1/5 | 低 4   │
│                            │  [💾 暂存草稿]  [📤 提交审阅]     │
│                            │  最后保存: 10:32                   │
└────────────────────────────────────────────────────────────────┘
```

提交按钮行为:
- `canSubmit === false`: 按钮置灰 + tooltip "请先完成所有高风险条款审批"
- `canSubmit === true`: 按钮亮起 (Primary 蓝色), 可点击

#### 调用的 API

| API | 用途 |
|-----|------|
| `POST /documents/{id}/save-draft` | 暂存草稿 |
| `POST /documents/{id}/submit` | 提交审阅 (通过 SubmitConfirmDialog 触发) |

---

### 5.2 SubmitConfirmDialog

**用途**: 用户点击"提交审阅"后弹出的确认对话框，展示最终审阅摘要统计。

#### Props 接口

```typescript
interface SubmitConfirmDialogProps {
  /** 是否可见 */
  visible: boolean;

  /** 审批摘要统计 (提交前最终数据) */
  reviewSummary: ReviewSummary;

  /** 是否正在提交 (loading) */
  isSubmitting: boolean;

  /** 提交错误信息 */
  errorMessage: string | null;

  // -- 事件回调 --

  /** 确认提交 */
  onConfirm: (comment?: string) => void;

  /** 取消提交 */
  onCancel: () => void;
}
```

#### 视觉结构

```
┌──────────────────────────────────────────────────────────┐
│  📋 确认提交审阅                                           │  [✕]
├──────────────────────────────────────────────────────────┤
│                                                           │
│  审阅摘要:                                                │
│  ┌─────────────────────────────────────────────────────┐ │
│  │  ✅ 已确认 (Approve):   2 项                         │ │
│  │  ✏️ 已修正 (Edit):      1 项                         │ │
│  │  ❌ 已驳回 (Reject):    0 项                         │ │
│  │  🟡 中风险通过:         5 项                         │ │
│  │  🟢 低风险自动通过:     4 项                         │ │
│  │  🏴 手动补充标记:       1 项                         │ │
│  │  ───────────────────────────────────────────────    │ │
│  │  总计:                 13 项                         │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                           │
│  提交备注 (可选):                                          │
│  ┌─────────────────────────────────────────────────────┐ │
│  │                                                      │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                           │
│  ⚠️ 提交后将生成最终审阅报告，无法再修改审批结果              │
│                                                           │
│  ⚠️ 提交失败: 网络连接超时                                 │  ← 条件渲染
│                                                           │
├──────────────────────────────────────────────────────────┤
│                 [取消，继续审阅]  [✅ 确认提交]             │
└──────────────────────────────────────────────────────────┘
```

#### 调用的 API

| API | 用途 |
|-----|------|
| `POST /documents/{id}/submit` | 提交审阅，触发报告生成 |

#### 错误处理

- `409 CONFLICT`: "仍有 N 项高风险条款待审批" -- 关闭对话框，自动切换到高风险 Tab
- `500`: "提交失败: 服务器内部错误" -- 显示重试按钮
- 网络错误: "网络连接失败，请检查连接后重试"

---

## 六、共享微组件

### 6.1 ConfidenceRing

**用途**: 环形进度指示器，展示 AI 置信度百分比。

#### Props 接口

```typescript
interface ConfidenceRingProps {
  /** 置信度值 (0.0 - 1.0) */
  confidence: number;

  /** 环直径 (px) */
  size?: number; // 默认 48

  /** 环线宽 (px) */
  strokeWidth?: number; // 默认 4

  /** 颜色方案 */
  colorScheme?: 'default' | 'compact';

  /** 是否显示百分比文字 */
  showLabel?: boolean; // 默认 true
}
```

#### 视觉规格

```
      ┌──────────┐
     ╱   ◉ 87%   ╲        蓝色填充弧 (stroke-dasharray = 87% * circumference)
    │              │       灰色背景弧 (360度)
     ╲            ╱
      └──────────┘
```

颜色映射:
- confidence >= 80%: `#3b82f6` (蓝色，高置信度)
- confidence >= 60%: `#f59e0b` (琥珀色，中等置信度)
- confidence < 60%: `#ef4444` (红色，低置信度) + 警告图标

---

## 附录 A: ClauseLocation -> 像素映射逻辑

这是前端实现中技术难度最高的环节。核心问题: **将后端返回的字符偏移量 (`char_offset_start`, `char_offset_end`) 转换为文档渲染层上的像素坐标，以正确定位高亮覆盖层。**

### A.1 问题定义

后端 `ClauseLocation` 返回:
```json
{
  "page_number": 3,
  "char_offset_start": 1240,   // 从文档全文开始的字符偏移
  "char_offset_end": 1580
}
```

前端需要计算出: 在**当前渲染页面上**，该段文本对应的**绝对像素位置** (相对于文档容器)。

### A.2 前提条件

1. 文档渲染引擎 (pdf.js / mammoth.js) 能提供**每个字符的页面坐标**。
2. 前端在每页渲染完成后构建 `charPositionMap: Map<number, CharPixel>`。
3. 坐标换算需考虑: 当前页码、缩放比例、页面间间距。

### A.3 数据结构

```typescript
interface CharPixel {
  char_offset: number;   // 文档全文字符偏移
  page: number;          // 所在页码
  x: number;             // 字符左上角 x (相对当前页面左上角, px)
  y: number;             // 字符左上角 y
  width: number;         // 字符宽度
  height: number;        // 字符高度 (通常为一行的高度)
}

interface HighlightRect {
  left: number;
  top: number;
  width: number;
  height: number;
  page: number;
}
```

### A.4 计算流程

```
Step 1: 文档渲染完成后，对每页执行文本测绘
┌──────────────────────────────────────────────────────┐
│ for each page:                                        │
│   for each text item (pdf.js: TextItem[]):           │
│     提取 char_offset, page, x, y, width, height     │
│     存入 charPositionMap.set(char_offset, pixel)     │
└──────────────────────────────────────────────────────┘

Step 2: 对每个 RiskFlag，将 char_offset 范围映射为像素矩形
┌──────────────────────────────────────────────────────┐
│ function mapLocationToPixel(                           │
│   location: ClauseLocation,                           │
│   charMap: Map<number, CharPixel>,                    │
│   scale: number,                                      │
│   pageHeight: number  // 每页在容器中的高度 (含间距)    │
│ ): HighlightRect {                                    │
│                                                        │
│   const startChar = charMap.get(location.char_offset_start); │
│   const endChar = charMap.get(location.char_offset_end);     │
│                                                        │
│   if (!startChar || !endChar) {                       │
│     // 降级: 字符坐标不可用，使用 bounding_box 或跳过    │
│     return null;                                      │
│   }                                                    │
│                                                        │
│   // 计算行高 (取 start 行高度)                        │
│   const lineHeight = startChar.height;                 │
│                                                        │
│   // 计算矩形 (跨行场景需处理多行)                       │
│   const rect = {                                       │
│     left: startChar.x * scale,                        │
│     top: startChar.y * scale,                         │
│     width: (endChar.x + endChar.width - startChar.x) * scale, │
│     height: lineHeight * scale,                       │
│     page: location.page_number,                       │
│   };                                                   │
│                                                        │
│   // 加上页面偏移 (前面页面的累计高度)                   │
│   rect.top += (location.page_number - 1) * pageHeight; │
│                                                        │
│   return rect;                                        │
│ }                                                      │
└──────────────────────────────────────────────────────┘

Step 3: 跨行场景处理
┌──────────────────────────────────────────────────────┐
│ 如果 startChar.y !== endChar.y (跨多行):                │
│                                                        │
│   // 第一行: startChar.x -> 行尾                       │
│   // 中间行: 整行宽度                                  │
│   // 最后一行: 行首 -> endChar.x + endChar.width       │
│                                                        │
│   使用多矩形叠加 (多个 <div> 或 CSS clip-path)          │
│   或计算包围盒:                                         │
│     rect.top = startChar.y * scale                     │
│     rect.height = (endChar.y + endChar.height - startChar.y) * scale │
│     rect.width = max(clientWidth)                      │
│     第一行和最后一行使用独立的 inset 矩形               │
└──────────────────────────────────────────────────────┘
```

### A.5 降级策略 (当字符坐标不可用时)

| 场景 | 降级方案 |
|------|---------|
| pdf.js 未能提取字符坐标 | 使用 `clause_text` 进行 DOM 文本搜索 (全文匹配)，通过 `window.find()` 或 `TreeWalker` 定位 DOM 节点，再用 `Range.getBoundingClientRect()` 获取坐标 |
| DOCX 中 mammoth.js 不提供坐标 | 同上，通过 HTML 文本搜索定位 |
| 字符坐标部分覆盖 (跨页断裂) | 按页分割，缺失页使用文本搜索降级 |
| 所有方式均失败 | 静默降级: 高亮不显示，控制台 warn; 右面板"在文档中查看"按钮仍可用 (滚动到对应页号) |

### A.6 性能优化

- `charPositionMap` 按页分片 (`Map<number, Map<number, CharPixel>>`)，当前页切换时只查询当前页的坐标。
- 缩放变更时，使用 CSS `transform: scale()` 作用于整个覆盖层容器，避免逐像素重算。
- `charPositionMap` 使用 `Map` 而非对象，保证 O(1) 的 `get` 操作。
- 渲染层使用 `will-change: transform` 提示 GPU 加速。

---

## 附录 B: 组件树与数据流总图

### B.1 完整组件树

```
P5Workspace (Page Container)
├── WorkspaceToolbar
│   └── SubmitConfirmDialog (Modal)
│
├── DocumentPanel (Left 50%)
│   └── DocumentViewer
│       ├── DocumentToolbar (page nav / search / zoom)
│       ├── DocumentRenderLayer (pdf.js / mammoth.js)
│       ├── ClauseHighlightOverlay
│       └── TextSelectionToolbar (conditional overlay)
│
├── RiskReviewPanel (Right 50%)
│   └── RiskDashboard
│       ├── StatCards (high / medium / low / completion ring)
│       ├── RiskTabNav
│       ├── HighRiskPanel
│       │   └── ApprovalCard[] (mode='full')
│       │       ├── ClauseLocationBar
│       │       ├── AIJudgment
│       │       │   └── ConfidenceRing
│       │       ├── PlaybookDiff
│       │       ├── SuggestionBox
│       │       ├── DecisionHistory
│       │       └── ActionBar
│       ├── MediumRiskBatchPanel
│       │   └── ApprovalCard (mode='expanded', on expand)
│       └── LowRiskPanel
│           └── ApprovalCard (mode='readonly', on spot-check)
│
└── ManualFlagForm (Modal/Overlay, triggered by TextSelectionToolbar or button)
```

### B.2 核心数据流

```
GET /documents/{id}/review-summary  ──┬──> WorkspaceToolbar (canSubmit)
                                      ├──> RiskDashboard (stat cards)
                                      └──> SubmitConfirmDialog (summary)

GET /documents/{id}/risk-flags?level= ──> RiskDashboard
  ├── filter level=HIGH  ──> HighRiskPanel ──> ApprovalCard[] (full)
  ├── filter level=MEDIUM ──> MediumRiskBatchPanel ──> ApprovalCard[] (expanded)
  └── filter level=LOW   ──> LowRiskPanel ──> ApprovalCard[] (readonly)

GET /risk-flags/{id}/playbook-diff  ──> PlaybookDiff (per card, lazy)
GET /risk-flags/{id}/decisions      ──> DecisionHistory (per card, lazy)

POST /risk-flags/{id}/approve ──┬──> ActionBar.onApprove
POST /risk-flags/{id}/edit    ──┤──> ActionBar.onEdit
POST /risk-flags/{id}/reject  ──┘──> ActionBar.onReject

POST /risk-flags/batch-approve  ──> MediumRiskBatchPanel
POST /risk-flags/sample         ──> LowRiskPanel
POST /risk-flags/{id}/escalate  ──> LowRiskPanel (升级)

POST /risk-flags/manual  ──> ManualFlagForm
POST /documents/{id}/submit  ──> SubmitConfirmDialog
POST /documents/{id}/save-draft  ──> WorkspaceToolbar
```

### B.3 双向同步数据流

```
右面板点击 ApprovalCard "在文档中查看"
  │
  ├─ 1. 触发 onViewInDocument(clauseLocation)
  ├─ 2. DocumentPanel 接收事件
  ├─ 3. DocumentViewer.scrollToPage(location.page_number)
  ├─ 4. ClauseHighlightOverlay.setActiveFlag(riskFlagId) -> active 样式闪烁 500ms
  └─ 5. RiskReviewPanel 中对应卡片获得焦点高亮

左面板点击高亮区域
  │
  ├─ 1. 触发 onHighlightClick(riskFlagId, clauseLocation)
  ├─ 2. RiskDashboard 接收事件
  ├─ 3. 切换到对应 Tab
  ├─ 4. 滚动到对应 ApprovalCard
  └─ 5. ApprovalCard 获得焦点高亮 + isFocused=true

键盘导航 (J/K)
  │
  ├─ 1. DocumentViewer 监听 keydown
  ├─ 2. J: 按 page_number + char_offset 顺序跳到下一个高亮区域
  ├─ 3. K: 跳到上一个
  ├─ 4. 触发上述双向同步逻辑
  └─ 5. Enter: 如果焦点在 ApprovalCard -> 触发 approve; Esc: 返回文档视图
```

### B.4 已实现 / 未开发标注汇总

| 组件 / 功能 | API 状态 | 标注 |
|------------|:------:|------|
| DocumentViewer (PDF/DOCX 渲染) | 已定义 | `GET /documents/{id}/file` -- 文件渲染服务需确认 |
| ClauseHighlightOverlay | 已定义 | 依赖 char_offset 定位; 字符坐标提取取决于渲染引擎 |
| TextSelectionToolbar | 纯前端 | 不依赖后端 API |
| RiskDashboard | 已定义 | `GET /review-summary` + `GET /risk-flags` |
| RiskTabNav | 纯前端 | 不依赖后端 API |
| HighRiskPanel | 已定义 | 依赖 `GET /risk-flags?level=HIGH` |
| ApprovalCard (approve) | 已定义 | `POST /risk-flags/{id}/approve` |
| ApprovalCard (edit) | 已定义 | `POST /risk-flags/{id}/edit` |
| ApprovalCard (reject) | 已定义 | `POST /risk-flags/{id}/reject` |
| ClauseLocationBar | 纯展示 | 数据来自 RiskFlag + Clause |
| AIJudgment | 纯展示 | 数据来自 RiskFlag |
| PlaybookDiff | 已定义 | `GET /risk-flags/{id}/playbook-diff` |
| SuggestionBox | 纯展示 | 数据来自 RiskFlag.suggested_wording |
| DecisionHistory | 已定义 | `GET /risk-flags/{id}/decisions` |
| MediumRiskBatchPanel | 已定义 | `POST /risk-flags/batch-approve` |
| LowRiskPanel | 已定义 | `POST /risk-flags/sample` + `POST /risk-flags/{id}/escalate` |
| ManualFlagForm | 已定义 | `POST /risk-flags/manual` |
| WorkspaceToolbar | 已定义 | `POST /save-draft` + `POST /submit` |
| SubmitConfirmDialog | 已定义 | `POST /documents/{id}/submit` |
| ConfidenceRing | 纯前端 | 不依赖后端 API |

---

> **上游文档**:
> - `../06_system_architecture/frontend_design_spec-v1.0.md` -- 前端设计规范
> - `../08_api_specification/api_spec-v1.0.md` -- API 接口规范
> - `../06_system_architecture/frontend_backend_boundary_spec-v1.0.md` -- 前后端功能边界规范

> **下游文档**:
> - `../05_product_prototype/` -- 产品原型规范
> - 前端实现 (React/Vue 组件代码)
