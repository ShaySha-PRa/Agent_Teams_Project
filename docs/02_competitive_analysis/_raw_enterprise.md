# Enterprise Tier: 审核结果呈现原始调研数据

> 调研日期: 2026-07-29
> 研究方法: WebSearch (中英文关键词) + WebFetch (官网、产品页、博客、第三方评测)
> 信息来源: 竞品官网、G2、Capterra、TrustRadius、Gartner Peer Insights、ArtificialLawyer、LegalTechTalk、Law.com、StayModern、AICenter 等

---

## 1. Ironclad

**产品概述**: Ironclad 是一款企业级合同生命周期管理 (CLM) 平台，核心 AI 能力包括 Jurist AI 合同伙伴、AI Playbooks 自动审核、AI Assist 智能修订、Contract AI (CAI) 对话式分析。定位中大型企业法务团队，年费 $50,000-$200,000+。覆盖 Create -> Review -> Sign -> Store -> Analyze -> Fulfill 全生命周期。

**核心数据**: G2 评分 4.4-4.5/5 (约 226-301 条评价)，用户界面评分约 4.5/5。采用 OpenAI GPT-4 结合自有法律训练数据，基于 20 亿+ 合同模式训练。

---

### 1.1 风险项的展示

#### 1.1.1 风险条款的呈现布局

**多视图混合模式**:
- **文档预览器 + 右侧边栏布局**: 在 Workflow 审阅阶段，左侧显示合同文档，右侧边栏显示 Clauses 列表（位于 Properties 下方），列出所有被标记的条款，点击可快速跳转。文档顶部显示 clause error banner，说明条款问题。
- **模态弹窗视图**: AI Precise Redlining 中，修订建议以模态弹窗展示，按"从少到多的变更量"排序（least to most changes）。
- **建议卡片式**: 每条 AI 生成的 redline 建议以卡片形式呈现，包含条款名称、问题简述、风险等级、推理说明、Playbook 规则来源。
- **内联追踪修订视图**: 在 Ironclad Editor 中，redline 以追踪修订 (Track Changes) 的形式内联显示在文档中。蓝色下划线表示新增，红色删除线表示删除。

信息来源:
- https://support.ironcladapp.com/hc/en-us/articles/12275585451159-Use-Playbooks-in-Workflows-and-Contract-Reviews
- https://support.ironcladapp.com/hc/en-us/articles/28661084734999-Use-AI-Precise-Redlining-to-Review-a-Contract
- https://ironcladapp.com/product/review-contracts

#### 1.1.2 风险分级（高/中/低）的视觉呈现方式

- **三级风险标签**: High、Medium、Low，以标签形式附着在每条修订建议上。
- **红色状态药丸 (Status Pills)**: 在 Documents 区域，条款错误以红色药丸标记出现，点击导航至文档预览器。
- **颜色编码**: 高风险使用红色标记，通过状态药丸和建议卡片上的风险等级标签区分。

**UI/UX 反模式 - 风险分级缺乏概览仪表盘**: 虽然在单条款级别有清晰的风险标签，但在合同级别缺乏聚合风险计分卡或风险热力图（如"本合同共 X 个高风险、Y 个中风险、Z 个低风险条款"的摘要视图未在文档中找到描述）。

信息来源:
- https://ironcladapp.com/resources/articles/jurist-redlining-playbooks
- https://www.techno-pulse.com/2026/04/best-ai-contract-management-tools-in.html

#### 1.1.3 风险分类（财务风险、合规风险、运营风险等）的组织方式

- **三大风险类别**: Jurist 识别并提取法律风险、财务风险和运营风险 (legal, financial, and operational risks)，基于公司 Playbook 和历史定位进行分类。
- **Playbook 驱动分类**: 风险分类通过 AI Playbooks 的规则配置决定。用户可在 Playbook 中定义哪些条款类型归属哪个风险类别。

信息来源:
- https://ironcladapp.com/product/jurist

#### 1.1.4 是否提供风险摘要仪表盘/概览页？其布局和关键指标

- **Deal Review Dashboard**: 提供概览列表视图，列出 Task Name、Assignee、Creation Date、Product、Status、Rejected items、Percentage Complete 等列。包含搜索功能。
- **Ironclad Insights 分析平台**: 可配置的合同分析工具，支持柱状图、条形图、环形图、时间序列图。包含预置报告模板：Company Overview（公司概览）、Repository（合同库）、Productivity（效率指标）。
- **预置 KPI**: 进行中的工作流按阶段/配置/受让人统计、已执行合同按负责人/配置统计、中位执行时间、审批人工作量分布、模板生成合同占比、对手方纸质合同占比等。
- **多部门定制**: 针对法务、销售、财务、采购、HR、市场、IT 等不同部门提供专门的 KPI 指标视图。
- **即将到期合同仪表盘** (April 2026 新增): AI 驱动的即将续约合同面板，显示业务关系、生效日期、续约退出日期、年度合同价值、允许续约次数。

信息来源:
- https://support.ironcladapp.com/hc/en-us/articles/12447748332695-Ironclad-Insights-Overview
- https://support.ironcladapp.com/hc/en-us/articles/25972696753175-Eight-Insights-Charts-to-Increase-Contracting-Efficiency
- https://ironcladapp.com/product/analyze-contracts

#### 1.1.5 风险项的排序和筛选能力

- **Insights 仪表盘筛选**: 支持按工作流配置、参与者、受让人、所有者、部门、地理位置、条款、Playbook 数据、自定义属性等维度筛选。每类别最多显示 15 项。
- **CAI 对话式查询**: 支持自然语言查询，如"哪些供应商合同在 Q3 到期且包含自动续约条款？"瞬间返回答案。
- **Dashboard 统一搜索**: April 2025 更新后统一了 Dashboard 和 Repository 的搜索和筛选体验。
- **审计日志搜索**: 支持按用户、日期范围、合同类型、操作类型筛选。

信息来源:
- https://support.ironcladapp.com/hc/en-us/articles/12446887780887-Insights-Chart-Settings-Overview
- https://www.techno-pulse.com/2026/04/best-ai-contract-management-tools-in.html

#### 1.1.6 风险趋势分析（同一合同多次版本的风险变化）

**未找到明确的版本间风险变化追踪功能描述**。Ironclad 提供 Insights 的时间序列图表（Timeseries 和 Cumulative Timeseries），可追踪合同执行时间等流程指标的变化趋势，但未找到针对"同一合同多个版本间风险评分变化"的专门分析工具。

信息来源: 未找到公开信息（仅找到流程效率趋势分析，非合同版本间风险对比）

---

### 1.2 原文定位与导航

#### 1.2.1 点击风险标记后如何定位到合同原文？

- **位置图钉图标**: 展开建议卡片后，点击 location pin icon 可直接跳转到文档中对应条款位置，该部分被高亮显示。
- **状态药丸导航**: 红色状态药丸点击后导航到文档预览器中的对应条款。
- **侧边栏快速链接**: 右侧 Clauses 列表中的条款项作为快速跳转链接。

信息来源:
- https://support.ironcladapp.com/hc/en-us/articles/40398187533847-Ironclad-Jurist-for-Microsoft-Word

#### 1.2.2 原文高亮方式（颜色标记、下划线、侧边标注等）

- **追踪修订内联标记**: 蓝色下划线（新增内容）、红色删除线（删除内容）。
- **文档内高亮**: 从建议卡片跳转到条款时，对应部分被高亮显示以便上下文审阅。
- **Redline 工作方式**: 在 Ironclad Editor 和 Jurist for Word 中，均以内联追踪修订方式呈现，等同于 Word 原生 Track Changes 体验。

信息来源:
- https://ironcladapp.com/product/jurist
- https://ironcladapp.com/resources/articles/jurist-redlining-playbooks

#### 1.2.3 是否支持并排视图（左：合同原文，右：风险分析）？

- **Ironclad Editor Compare 模式**: 支持并排版本对比 (side-by-side comparison)，可在原版本和修订版本之间切换查看差异。
- **侧边栏+文档视图**: 不是严格意义的并排，但 Word Add-In 在右侧面板展示风险分析，左侧为文档原文。
- **CAI 对话式分析**: 在 Dashboard 中搜索时，结果展示 in-context snippets，显示合同匹配上下文而无需打开文件。

**UI/UX 反模式 - 缺乏专用分屏风险审阅视图**: 与专门的 AI 合同审阅工具不同，Ironclad 没有在 User Research 中发现明确的"左原文/右分析"专用分屏布局，风险分析信息在侧边栏或弹窗中呈现，而非与原文实时并排关联。

信息来源:
- https://support.ironcladapp.com/hc/en-us/articles/12274871100055-Use-Ironclad-Editor
- https://ironcladapp.com/product/review-contracts

#### 1.2.4 是否支持条款间跳转（如从定义跳转到引用处）？

**未找到明确的跨条款智能跳转功能描述**。文档中提到 Jurist 支持"Location pin icon"跳转到条款位置，但未说明是否支持从一个条款引用自动跳转到其定义条款或关联条款。

信息来源: 未找到公开信息

#### 1.2.5 文档内搜索与导航能力

- **Conversational Search (Beta)**: AI 驱动的自然语言搜索，Dashboard 内直接搜索合同内容。返回 in-context snippets、AI 摘要（计数、总计、分组答案、跨合同快速比较）。支持 follow-up prompts 细化结果集。
- **CAI 自然语言界面**: 无需训练或复杂搜索过滤器，任何人都可进行复杂合同分析查询。
- **Saved Views 和 Saved Searches**: April 2025 更新后支持保存常用搜索和视图。

信息来源:
- https://support.ironcladapp.com/hc/en-us/articles/38644784178583-Use-Conversational-Search-on-the-Dashboard
- https://ironcladapp.com/resources/articles/meet-ironclad-contract-ai

#### 1.2.6 多文档关联导航（主合同 ↔ 修订协议 ↔ 附件）

**未找到明确的多文档关联导航功能描述**。Ironclad 支持 Repository 中存储所有合同文档，但未找到主合同与修订协议或附件之间自动关联导航的具体功能说明。

信息来源: 未找到公开信息

---

### 1.3 中间解释性数据展示

#### 1.3.1 AI 判定风险的理由/依据如何呈现？

- **内联推理说明**: 每个 redline 建议附带 clear, defensible rationale（清晰、可辩护的理由），说明变更了什么、为什么重要、建议如何解决检测到的问题。
- **Playbook 规则溯源**: 每条建议标注来源 Playbook 规则，明确 AI 依据的哪条组织标准。
- **CAI "Open Book" 透明推理**: 分步骤展示分析过程——将复杂问题分解为子任务，依次完成并评估结果，最终展示完整推理链。例如分析销售订单座位的查询展示了：(1)拉取六种合同类型，(2)审查四条属性数据，(3)搜索关键条款。

**截图描述（来自 Jurist 产品页）**: 一条责任限制条款的 redline 展示：Jurist 标记不符规定，基于 playbook 提出费用上限方案，解释当前上限为何不足，同时展示备选方案 (fallback position)。

信息来源:
- https://ironcladapp.com/product/jurist
- https://ironcladapp.com/resources/articles/meet-ironclad-contract-ai
- https://ironcladapp.com/resources/articles/jurist-redlining-playbooks

#### 1.3.2 是否展示 Playbook 标准条款与实际条款的对比（diff 视图）？

- **版本对比 (Compare)**: Ironclad Editor 内置 Compare 功能，支持并排对比合同版本间的差异。
- **Redline 卡片**: 非传统 diff 视图，但建议卡片中展示 proposed change 与原文的对比。
- **三路合并逻辑**: 来自不同编辑环境的变更通过三路合并 (three-way merge) 协调，冲突以界面方式呈现。

信息来源:
- https://support.ironcladapp.com/hc/en-us/articles/12274871100055-Use-Ironclad-Editor
- https://ironcladapp.com/resources/articles/ironclad-word-google-doc-integration

#### 1.3.3 是否提供相关法规原文引用？

**未找到明确的法规原文引用功能**。Ironclad 的 Jurist 声称可访问"经过审核的法律知识来源"的互联网实时数据，但未描述在审阅结果中直接引用法规原文（如 GDPR 第 X 条、UCC 第 Y 条等）的功能。

信息来源: 未找到公开信息

#### 1.3.4 置信度/风险评分的可视化

**未找到数值化置信度评分**。Ironclad 使用 H/M/L 三级风险标签，而非百分比或数值化的置信度/风险评分。CAI 的透明推理步骤可视化了分析过程，但不以数值置信度形式呈现。

信息来源: 未找到公开信息（风险以定性标签呈现，非定量评分）

#### 1.3.5 历史相似条款的审阅决策参考

**部分支持**: Jurist 的 redlining 基于组织 Playbook 和历史定位 (historical positions) 进行建议，表明历史决策数据被用于训练和指导 AI。但未找到 explicit "查看历史上类似条款如何处理" 的用户界面功能。

**Jurist 谈判立场**: 支持 Negotiation stances (Light, Balanced, Firm) 和 Position toggling (Preferred, Fallback, 或不修改)，表明历史决策影响了当前建议的参数选择。

信息来源:
- https://ironcladapp.com/product/jurist
- https://support.ironcladapp.com/hc/en-us/articles/34188767294359-Use-Jurist-Redlining-Agent-with-Playbooks

#### 1.3.6 数据来源的可追溯性（AI 的依据是什么？）

**高度可追溯**:
- 每条 redline 建议追溯至具体的 Playbook 规则。
- CAI 通过 Rivet 开源可视化编程环境，逐个步骤展示分析过程，被 CEO 称为 "open book"（而非 "black box"）。
- 建议卡片包含 Source 字段，明确显示触发的 playbook 规则。
- Counterparty-ready comments 中的理由来自 Playbook 定义的立场。

**数据使用透明**:
- 明确声明不基于客户敏感数据训练第三方 LLM
- 提供 Zero Data Retention (ZDR) 协议
- ISO 27001 和 SOC 2 Type II 认证

信息来源:
- https://ironcladapp.com/resources/articles/meet-ironclad-contract-ai
- https://ironcladapp.com/product/jurist
- https://ironcladapp.com/resources/articles/jurist-redlining-playbooks

---

### 1.4 修改建议与协作

#### 1.4.1 修改建议的呈现形式（内联修订、建议批注、修改对照表）

**多种呈现形式混合**:
- **内联追踪修订 (Track Changes)**: 在 Ironclad Editor、Jurist for Word 中均以原生 Word Track Changes 形式呈现。
- **建议卡片 + 模态弹窗**: AI Assist 和 AI Precise Redlining 中，建议以卡片形式在侧边栏或弹窗中列出，展示 proposed change 和详细解释。
- **Redline 摘要文档**: Jurist 可生成 "Summary of redlines" 伴随文档，汇总所有建议变更，适用于长合同（40+ 页）的快速审阅。
- **Playbook 规则摘要**: 可选择生成 "Extracted rules from playbook" 伴随文档。

信息来源:
- https://support.ironcladapp.com/hc/en-us/articles/34188767294359-Use-Jurist-Redlining-Agent-with-Playbooks
- https://support.ironcladapp.com/hc/en-us/articles/28661084734999-Use-AI-Precise-Redlining-to-Review-a-Contract

#### 1.4.2 是否支持一键接受/拒绝修改？

**完全支持**:
- Accept all changes（批量接受全部修改）
- Accept changes（逐条接受）
- Reject changes（逐条拒绝）
- Modify（接受后手动调整）
- Insert Redline（一键插入到文档）
- Position toggling: Preferred / Fallback / No redline

信息来源:
- https://ironcladapp.com/resources/articles/jurist-redlining-playbooks
- https://support.ironcladapp.com/hc/en-us/articles/28661084734999-Use-AI-Precise-Redlining-to-Review-a-Contract

#### 1.4.3 是否支持手动编辑 AI 建议？

**支持**:
- "Rewrite with Input" 选项（在 Jurist 的红色建议弹窗中），允许用户用自己的语言重写条款。
- "Modify" 功能允许在接受建议的基础上进行调整。
- AI 生成 redline 后用户可直接在文档中编辑文本（原生编辑器功能）。

信息来源:
- https://ironcladapp.com/product/jurist
- https://support.ironcladapp.com/hc/en-us/articles/28661084734999-Use-AI-Precise-Redlining-to-Review-a-Contract

#### 1.4.4 多人协作审阅时的批注与讨论功能

- **内部/外部评论隔离**: 区分 internal comments（仅团队可见）和 external comments（对手方可见）。
- **@提及**: 在 Editor 中使用 @mentions 直接标记队友。
- **Activity Feed 时间线**: 所有评论、版本变更、审批、签名事件汇总为统一的时间线。
- **跨环境评论**: Google Docs 和 Word 中的评论和修订建议在同步回 Ironclad 时保留。
- **版本摘要评论**: 保存变更时提示添加摘要评论，记录在 Activity Feed 中。
- **Turn Tracking**: 追踪谈判轮次变更，标识哪些合同需要关注、哪些在等对方回复。

**UI/UX 反模式 - Activity Feed 信息过载**: 评论、版本变更、审批、审计事件全部混合在同一 Activity Feed 中，缺乏分类过滤，可能在复杂合同中造成信息过载。

信息来源:
- https://support.ironcladapp.com/hc/en-us/articles/12274871100055-Use-Ironclad-Editor
- https://ironcladapp.com/resources/articles/ironclad-word-google-doc-integration

#### 1.4.5 版本对比（原合同 vs AI 修改版 vs 最终版）

- **Compare 模式**: Ironclad Editor 支持并排或叠加对比不同版本。
- **三路合并**: 处理来自不同编辑环境（Google Docs、Word、Editor）的冲突变更。
- **清洁版本管理**: 外部编辑器修改发布为单一有意义的版本，避免"版本过载"。
- **Turn Tracking**: 记录谈判过程中各方的修改轮次。

信息来源:
- https://support.ironcladapp.com/hc/en-us/articles/12274871100055-Use-Ironclad-Editor
- https://ironcladapp.com/resources/articles/ironclad-word-google-doc-integration

---

### 1.5 报告与导出

#### 1.5.1 审阅报告的生成格式（PDF、Word、在线报告页）

- **"Summary of redlines" 文档**: 与 redlined 合同一起生成的伴随文档，以 DOCX 格式输出。
- **Insights 图表导出**: JPEG、PNG、SVG、PDF、CSV 格式。
- **审计日志导出**: CSV、PDF 格式。
- **DOCX 输出**: Jurist 生成的合同文件和伴随文档可直接下载为 .docx。
- **PDF 上传和导出**: 支持 PDF 输入（自动转 DOCX 处理）和输出。
- **在线报告模板**: Company Overview、Repository、Productivity 三个预置报告模板，可自定义组合多图表为单个报告页。

信息来源:
- https://support.ironcladapp.com/hc/en-us/articles/34188767294359-Use-Jurist-Redlining-Agent-with-Playbooks
- https://support.ironcladapp.com/hc/en-us/articles/12447748332695-Ironclad-Insights-Overview
- https://ironcladapp.com/product/analyze-contracts

#### 1.5.2 报告内容的可定制性

- **Insights 自定义图表**: 支持自定义图表类型（柱状、条形、环形、时间序列）、分组维度（配置、人员、部门、地理、条款等）、聚合方法（计数、求和、中位数、均值）。
- **自定义报告**: 将多张图表组合为可定制的报告视图，支持并排排列。
- **可分享图表**: 图表副本可通过链接分享给跨团队协作人员。
- **Jurist 伴随文档生成选项**: 可选择生成 "Summary of redlines" 和 "Extracted rules from playbook"。

信息来源:
- https://support.ironcladapp.com/hc/en-us/articles/12446887780887-Insights-Chart-Settings-Overview

#### 1.5.3 是否支持导出为 Redline/修订版合同？

**完全支持**:
- Jurist 输出 redlined .docx 文件，可直接下载。
- Jurist for Word 中，redline 直接插入文档，保存为标准 Word 追踪修订文件。
- Ironclad Editor 的 Compare 功能允许查看并接受/拒绝修订后保存为清洁版本。

信息来源:
- https://ironcladapp.com/product/jurist
- https://support.ironcladapp.com/hc/en-us/articles/40398187533847-Ironclad-Jurist-for-Microsoft-Word

#### 1.5.4 审计追踪的呈现（谁在什么时候做了什么决定）

**高度完善**:
- **不可篡改审计日志**: 覆盖合同全生命周期——草稿创建、条款编辑、审批、拒绝、签名事件、访问事件、签署后修订、元数据变更。
- **条款级粒度**: 记录到条款级别 (clause-level changes)，包含旧值和新值对比。
- **签名证书**: eSignature 事件生成防篡改证书，绑定签名者身份与执行文件。
- **安全特性**: 追加式存储、加密哈希、管理员也无法编辑历史记录。
- **AI 异常检测**: AI 可自动标记异常模式（如非原工作流中的人在签署后访问合同）。
- **合规支持**: 符合 SOX、GDPR、HIPAA 等框架要求。
- **API 集成**: 可接入 SIEM 系统和合规工具。

信息来源:
- https://ironcladapp.com/resources/articles/contract-audit-logs

#### 1.5.5 数据导出能力（API、CSV、Excel）

- **Insights 图表导出**: JPEG、PNG、SVG、PDF、CSV
- **审计日志导出**: CSV、PDF
- **合同文档导出**: DOCX、PDF
- **Smart Import 通过 Email**: 签署后合同转发至指定地址，自动 OCR 扫描并存储
- **第三方集成**: Salesforce 集成；Filament Analytics 等外部分析工具可接入
- **API**: 审计日志可通过 API 导出至 SIEM 和合规工具

信息来源:
- https://ironcladapp.com/resources/articles/contract-audit-logs
- https://support.ironcladapp.com/hc/en-us/articles/12447748332695-Ironclad-Insights-Overview

#### 1.5.6 与项目管理/合同管理系统的集成报告

- **Salesforce 集成**: 结合交易数据和合同数据，端到端预测和可见性。
- **Google Docs 集成**: 实时协同编辑。
- **Microsoft Word Add-In**: 从 Word 内直接操作 Ironclad 元数据、审批和操作。
- **Word Online**: 云端协同编辑。
- **Anthropic 集成**: AI 模型合作伙伴集成。
- **Filament Analytics**: 第三方分析工具集成，可构建额外合同仪表盘。

信息来源:
- https://ironcladapp.com/product/integrations/anthropic
- https://filamentanalytics.com/integrations/ironclad

---

## 2. Kira Systems (Litera)

**产品概述**: Kira 是 Litera 旗下的 AI 驱动合同审查平台，以高精度条款提取著称。内置 1,400+ 律师训练的智能字段，覆盖 40+ 实质性领域。被 64% 的 AmLaw 100 律所和全部四大会计师事务所采用。核心应用场景为大规模 M&A 尽职调查。2021 年被 Litera 收购后与 Litera Compare、Litera Transact 等产品集成。

**核心数据**: TrustRadius 评分 7.6/10，Gitnux 2026 评分 8.0/10。提取准确率 90-95%（标准条款类型，开箱即用）。年费约 $100K+。2025 年经历了重大 UX 改版，推出 GenAI 功能和 Analysis Chart（网格化审阅界面）。

---

### 2.1 风险项的展示

#### 1.1.1 风险条款的呈现布局

**网格/表格视图 (Analysis Chart)**:
- **新一代 Analysis Chart**: 2025 年推出的类 Excel 体验，以表格形式展示所有文档中的提取语言和答案。是 Kira 近年来最重大的 UI 变革。
- **传统提取网格 (Extraction Grid)**: 旧版界面，条款提取结果以网格表格呈现，支持导出为 Excel 进一步分析。
- **分析图表 (Analysis Grid)**: 作为 Dashboard 替代方案，提供跨文档的风险和趋势即时概览，以 clean, intuitive layout 呈现。
- **文档查看器**: 点击网格中的条款可打开文档查看器，在原位查看提取内容。
- **Smart Summaries**: AI 生成的条款摘要，帮助快速起草尽职调查报告。

**截图描述**: Analysis Chart 界面以类似电子表格的布局展示，每行代表一个文档或条款，每列代表一个智能字段。支持显示/隐藏字段列、调整行高、全屏切换（New Look 开关）。

信息来源:
- https://support.litera.com/article/What-s-Coming-in-Kira-June-2025
- https://www.artificiallawyer.com/2025/07/28/litera-expands-kira-with-added-genai-features/
- https://www.litera.com/products/kira

#### 1.1.2 风险分级（高/中/低）的视觉呈现方式

**未找到明确的三级风险标签系统描述**。Kira 更侧重于条款提取的准确度和一致性检测，而非类似 Ironclad 的 H/M/L 明确风险评级。其风险呈现主要通过以下方式:
- **部分匹配 (Partial Matching)**: 对比提取结果与基线时，通过图形显示每条提取中的变更数量，使用滑块调整匹配度阈值。
- **标志和标签 (Flags/Tags)**: 对文档进行标记、分组和分配，用于人为风险分类。
- **数据可视化仪表盘**: 展示相对频率或关键条款间的关系，间接呈现风险模式。

**UI/UX 反模式 - 缺乏直观风险评级**: Kira 在设计上更偏向提取工具而非风险审阅工具，缺乏用户预期的一目了然的风险评级标签（如红/黄/绿），用户需自行判断提取结果的风险程度。

信息来源:
- https://support.litera.com/article/What-s-Coming-in-Kira-April-2025
- https://www.litera.com/products/kira

#### 1.1.3 风险分类（财务风险、合规风险、运营风险等）的组织方式

- **40+ 实质性领域的内置智能字段**: 涵盖常见合同条款、义务、日期、当事方等。
- **自定义智能字段**: 用户可通过自然语言提示创建任何类别的提取字段。
- **标签和分组**: 通过 Tags, grouping, document assignment 对文档进行分类组织。

信息来源:
- https://aicenter.ai/tools/kira-systems
- https://www.litera.com/products/kira

#### 1.1.4 是否提供风险摘要仪表盘/概览页？其布局和关键指标

- **Analysis Chart 作为仪表盘替代**: 不像传统仪表盘，但 Analysis Chart 提供跨文档的 risks and trends 即时概览。
- **Litera Transact 集成仪表盘**: 可在 Transact 仪表盘中直接查看合同审查进度和审查者数量。
- **数据可视化工具**: 集中式在线平台包含数据可视化工具，可即时追踪进度、查看聚合数据详情（如关键条款的相对频率或关系）。

**UI/UX 反模式 - 缺乏专用风险仪表盘**: 相比 Ironclad 的 Insights，Kira 缺乏独立的仪表盘产品。分析能力更多嵌入在审阅工作流中而非独立的 BI 层。

信息来源:
- https://www.litera.com/products/kira
- https://www.artificiallawyer.com/2025/07/28/litera-expands-kira-with-added-genai-features/

#### 1.1.5 风险项的排序和筛选能力

- **Analysis Chart 交互**: 在网格界面中可按任何列排序和筛选。
- **部分匹配滑块**: 通过百分比滑块调整匹配阈值，筛选相似但非完全匹配的条款。
- **批量操作**: 可对部分匹配结果执行批量接受/拒绝。
- **Concept Search**: 用单一示例跨文档搜索任何法律概念。

信息来源:
- https://support.litera.com/article/What-s-Coming-in-Kira-April-2025

#### 1.1.6 风险趋势分析（同一合同多次版本的风险变化）

**部分支持**:
- **部分匹配 + Redline**: 对比提取结果与基线版本时，可直接 redline 部分匹配中的变更内容，可视化查看差异。
- **跨文档一致性检测**: Kira 的设计重点在于跨整个文档集发现条款一致性问题，通过将每次提取与基线对比来发现偏差。

**局限性**: Kira 更关注跨文档的一致性分析，而非同一合同不同版本的风险变化追踪。

信息来源:
- https://support.litera.com/article/What-s-Coming-in-Kira-April-2025

---

### 2.2 原文定位与导航

#### 2.2.1 点击风险标记后如何定位到合同原文？

- **内联引用/Source Clauses**: Analysis Grid 中的结果旁显示 exact source clauses，用户可追溯答案回原始文本。
- **文档查看器导航**: 点击网格中的任意提取项可打开文档查看器，在原位查看该条款。
- **Lito "Analyze in Grid"**: 动态矩阵界面支持同时跨多个文档运行多个提示，集成文档查看器进行流线化验证。

信息来源:
- https://www.litera.com/products/kira
- https://www.artificiallawyer.com/2025/07/28/litera-expands-kira-with-added-genai-features/

#### 2.2.2 原文高亮方式（颜色标记、下划线、侧边标注等）

- **文档查看器高亮**: Kira 在文档查看器中对提取出的条款进行高亮标记（具体颜色和标注方式未在公开文档中详细描述）。
- **Redline 标记**: 部分匹配对比中，redline 以标准的增删标记显示变更（类似 Word 追踪修订）。
- **Litera Compare 集成**: 通过 Litera Compare 可实现详细的文档对比（蓝色下划线 = 新增，红色删除线 = 删除，格式变更标记）。

信息来源:
- https://support.litera.com/article/What-s-Coming-in-Kira-April-2025
- https://support.litera.com/article/Viewing-comparisons-537422

#### 2.2.3 是否支持并排视图（左：合同原文，右：风险分析）？

**部分支持**:
- **文档查看器 + Analysis Chart**: 两者同时打开时形成非严格并排的工作体验。
- **Lito "Analyze in Grid"**: 动态矩阵界面配集成文档查看器。
- **Litera Compare 三面板视图**: 通过 Litera Compare 可实现三面板同步视图（原文、修改版、redline）。

**UI/UX 反模式 - 并排视图不够紧密集成**: Kira 的核心审阅界面是网格/表格，文档查看器是独立窗口而非严格并排分屏。用户需要在网格和文档查看器之间切换，增加操作摩擦。

信息来源:
- https://support.litera.com/article/Viewing-comparisons-537422

#### 2.2.4 是否支持条款间跳转（如从定义跳转到引用处）？

**未找到公开信息**。Kira 的强项是条款提取而非文档内的交叉引用导航。

信息来源: 未找到公开信息

#### 2.2.5 文档内搜索与导航能力

- **Chat 界面**: 内置于 Analysis Chart 的对话功能，支持自然语言提问并返回上下文答案（带引用）。
- **Concept Search**: 基于 LLM，用一个示例短语跨项目文档识别法律概念。
- **语言/司法管辖区检测**: 自动检测文档语言和法律管辖区。

信息来源:
- https://www.artificiallawyer.com/2025/07/28/litera-expands-kira-with-added-genai-features/

#### 2.2.6 多文档关联导航（主合同 ↔ 修订协议 ↔ 附件）

**部分支持**:
- **文档分组**: Kira 自动分类文档类型并分组合同及其相关修订。
- **重复检测 (Deduplication)**: 批量导入时自动检测和去重。

信息来源:
- https://www.litera.com/products/kira
- https://aicenter.ai/tools/kira-systems

---

### 2.3 中间解释性数据展示

#### 2.3.1 AI 判定风险的理由/依据如何呈现？

- **内联引用 (Built-In Citations)**: Analysis Grid 结果旁展示 exact source clauses，完整可追溯。
- **Chat 链接引用**: Chat 答案附带 linked citations 以确保可信度。
- **置信度评分**: Quick Study 自定义智能字段的提取结果附带 high-precision confidence scoring（高精度置信度评分）。

信息来源:
- https://www.litera.com/products/kira
- https://aitocore.com/en/tool/kira-systems

#### 2.3.2 是否展示 Playbook 标准条款与实际条款的对比（diff 视图）？

**部分支持**:
- **部分匹配 Redline (Partial Matching Redlining)**: April 2025 新增功能，可在部分匹配中 redline 变更，查看提取结果与基线的差异。滑块调整匹配阈值。
- **Litera Compare**: 提供详细的文档对比和 redline 功能。

信息来源:
- https://support.litera.com/article/What-s-Coming-in-Kira-April-2025

#### 2.3.3 是否提供相关法规原文引用？

**未找到公开信息**。Kira 是条款提取和尽职调查工具，不以内置法律法规数据库为特点。

信息来源: 未找到公开信息

#### 2.3.4 置信度/风险评分的可视化

- **Quick Study 置信度评分**: 自定义智能字段的提取结果附带 high-precision confidence scoring。具体呈现方式（百分比、星级等）在公开资料中未详细描述。
- **部分匹配图形**: 使用图表可视化每条提取中的变更数量，滑块调整匹配参数。

信息来源:
- https://aitocore.com/en/tool/kira-systems
- https://support.litera.com/article/What-s-Coming-in-Kira-April-2025

#### 2.3.5 历史相似条款的审阅决策参考

**Quick Study 的增量学习**:
- Quick Study 通过用户反馈持续学习改进，但这是模型级别的学习而非向用户展示历史相似条款的决策。
- **生成式智能字段**: 可用自然语言定义需提取的内容，但不直接展示历史决策。

**局限性**: Kira 的环境更偏向每次审查独立进行，不内置类似 Ironclad Playbook 的历史决策知识库。

信息来源: 未找到类似 Playbook 知识库的历史决策参考功能描述

#### 2.3.6 数据来源的可追溯性（AI 的依据是什么？）

**高度可追溯**:
- 所有结果附带 source clauses 引用。
- Chat 答案附带 linked citations。
- 差分隐私算法保障训练数据保密性——为法律 AI 行业首创，数学上保证训练数据不可逆向工程。

信息来源:
- https://www.litera.com/products/kira
- https://www.legaltechmonitor.com/2020/11/in-first-for-contracts-ai-kira-creates-algorithm-to-protect-inferential-confidentiality-of-training-data/

---

### 2.4 修改建议与协作

#### 2.4.1 修改建议的呈现形式（内联修订、建议批注、修改对照表）

- **部分匹配 Redline**: 以 redline 形式展示提取结果与基线的差异，支持批量操作。
- **Litera Compare**: 通过集成 Litera Compare 实现完整的文档对比和 redline——支持 Word、PDF、Excel、PowerPoint 等多格式交叉对比。
- **项目内协作工具**: 原地编辑、工作流工具用于优化结果。

信息来源:
- https://support.litera.com/article/What-s-Coming-in-Kira-April-2025
- https://support.litera.com/article/Viewing-comparisons-537422

#### 2.4.2 是否支持一键接受/拒绝修改？

**支持批量操作**: 可对 exact matches 和 partial matches 执行批量接受/拒绝操作。(但 Kira 的"修改建议"概念不同于 Ironclad——Kira 更关注条款的存在/不存在检测和一致性验证，而非替代语言建议。)

信息来源:
- https://support.litera.com/article/What-s-Coming-in-Kira-April-2025

#### 2.4.3 是否支持手动编辑 AI 建议？

**支持**:
- 原地编辑功能用于优化提取结果。
- 工作流工具支持手动修正。

信息来源:
- https://aicenter.ai/tools/kira-systems

#### 2.4.4 多人协作审阅时的批注与讨论功能

- **标记、分组、分配 (Tags, Grouping, Assignment)**: 支持对文档进行分类、标记和分配给特定审阅者。
- **进度追踪**: 追踪项目进度和审查者活动。
- **数据室集成**: 与 HighQ、Intralinks 等数据室集成，实现协作式文档管理。
- **多同时审阅者**: 云端平台支持多个审阅者同时高效工作。

**UI/UX 反模式 - 缺乏实时协作评论功能**: TrustRadius 评论指出缺乏通知/提醒机制，协作更多依赖标签和分配而非实时讨论。

信息来源:
- https://www.trustradius.com/products/litera-kira/reviews
- https://www.litera.com/products/kira

#### 2.4.5 版本对比（原合同 vs AI 修改版 vs 最终版）

**Litera Compare 集成**:
- 支持跨格式对比（Word 对 PDF、PDF 对 Word、Excel 对 Word 等）。
- 三面板同步视图（原文、修改版、redline）。
- "Changed Pages" 选项仅查看/下载有变更的页面。
- 通过 OCR 支持扫描文档对比。
- 对比结果可保存为 PDF、DOCX、Track Changes DOCX 或 Changed Pages PDF。

信息来源:
- https://support.litera.com/article/Viewing-comparisons-537422

---

### 2.5 报告与导出

#### 2.5.1 审阅报告的生成格式（PDF、Word、在线报告页）

- **Word (DOCX)**: 通过 UI 和 API 支持
- **Excel**: 提取结果以电子表格导出
- **PDF**: 通过 UI 和 API 支持
- **HighQ**: 自定义格式集成
- **Litera Compare 导出**: 另存为 PDF、DOCX、Track Changes DOCX、Changed Pages PDF。可通过邮件分享对比结果（PDF、PDF/A、ZIP 等格式）。

信息来源:
- https://www.litera.com/products/kira
- https://support.litera.com/article/Viewing-comparisons-537422

#### 2.5.2 报告内容的可定制性

- **自定义摘要图表**: 可为任何数据点导出自定义摘要图表。
- **Smart Summaries**: AI 生成的提取条款摘要作为报告草稿的起点。
- **生成式智能字段**: 通过自然语言提示创建自定义提取字段，间接定制报告内容。

**UI/UX 反模式 - 导出定制性受限**: TrustRadius 用户评论明确指出"希望有更多导出结果的自定义选项"。

信息来源:
- https://www.trustradius.com/products/litera-kira/reviews
- https://www.litera.com/products/kira

#### 2.5.3 是否支持导出为 Redline/修订版合同？

**支持（通过 Litera Compare）**:
- 可导出 Track Changes DOCX（带追踪修订的 Word 文件）。
- 可导出 Changed Pages PDF。
- 部分匹配中的 redline 结果可作为 deliverables 分享。

信息来源:
- https://support.litera.com/article/Viewing-comparisons-537422
- https://www.litera.com/products/kira

#### 2.5.4 审计追踪的呈现（谁在什么时候做了什么决定）

**项目级进度追踪**:
- 追踪项目进度和审查者活动。
- 通过 Litera Transact 仪表盘查看审查进度和审查者数量。
- **项目级 GenAI 治理**: 可对每个 Kira 项目启用或禁用 GenAI 功能，符合外部法律顾问指南要求。

**局限性**: 未找到类似 Ironclad 的条款级不可篡改审计日志。Kira 的追踪更偏项目管理和进度追踪而非法务审计。

信息来源:
- https://www.litera.com/products/kira
- https://www.artificiallawyer.com/2025/07/28/litera-expands-kira-with-added-genai-features/

#### 2.5.5 数据导出能力（API、CSV、Excel）

- **API**: 良好的 API 用于批量合同分析。
- **Excel**: 提取结果的核心导出格式。
- **Word & PDF**: 通过 UI 和 API。
- **数据室集成导出**: 与 HighQ、Intralinks 等集成。

信息来源:
- https://www.litera.com/products/kira

#### 2.5.6 与项目管理/合同管理系统的集成报告

- **Litera Transact**: 交易管理集成，查看审查进度。
- **HighQ**: 协作和数据室集成。
- **Intralinks**: 数据室集成。
- **iManage / NetDocuments**: 文档管理系统集成。
- **Litera Draft**: 文档起草集成。

信息来源:
- https://www.litera.com/products/kira

---

## 3. Luminance

**产品概述**: Luminance 是英国法律 AI 公司，以自研 Legal Pre-trained Transformer (LPT) 模型为核心，训练于 1.5 亿+ 法律验证文档。旗舰功能为 Traffic Light Analysis（交通灯风险分析）和多语言支持（80+ 语言）。定位为 Legal-Grade AI，覆盖合同审查、谈判、合规、发现和尽职调查。600+ 组织在 70+ 国家使用。提供本地部署选项和 ISO 认证。

**核心数据**: G2 评分 4.9/5 (5 条验证评价)，SoftwareFinder 4.8/5。易用性评分 7.7/10（相比 Kira 的 7.2/10）。合同审查时间节省 50-90%，条款识别准确率 94%（完成定制训练后）。实现周期 1-4 周。

---

### 3.1 风险项的展示

#### 1.1.1 风险条款的呈现布局

**交通灯分析 (Traffic Light Analysis) 为核心**:
- **内联颜色标记**: 合同打开时自动进行首轮审查，直接在文档中以颜色标记每个条款的风险状态。这是 Luminance 的标志性功能。
- **Word 插件内展示**: 风险分析、摘要、推理和修订建议都整合在 Word 插件内，用户在熟悉的环境中审查。
- **分步检查清单 (Step-by-Step Checklist)**: 以清晰的清单格式聚焦谈判核心立场，每完成一项可勾选。
- **每个条款三项信息**: Summary（条款摘要）+ Reason（为何不符合标准）+ Mark-Up（建议替代语言，一键插入）。

**UI/UX 亮点 - Position-Level 全局分析**: 不同于其他竞品逐条审阅，Luminance 在合同全文中进行 position-level 分析，交叉引用相关条款（如第 3 页的责任限制条款和第 5 页知识产权条款中对其的引用一起考量），提供整体摘要而非碎片化分析。

信息来源:
- https://www.luminance.com/resources/blog/product-feature-spotlight-accelerate-negotiations-with-luminance%c2%92s-ai-powered-checklists/
- https://www.luminance.com/negotiate/
- https://www.luminance.com/resources/blog/the-next-frontier-for-contract-work-legal-grade-ai-that-understands-the-bigger-picture/

#### 1.1.2 风险分级（高/中/低）的视觉呈现方式

**交通灯三色系统**:
- **绿色 (Green)**: 条款可接受，符合组织内部标准。
- **琥珀色/黄色 (Amber)**: 需要进一步审查。
- **红色 (Red)**: 不符合或偏离标准条款。

分析粒度达到 **子条款级别 (sub-clause level)**，可精确定位问题（如管辖法律条款中具体哪个用词有问题）。

**UI/UX 亮点 - 即时视觉判断力**: 法律专业人员可在数秒内了解应将注意力集中在何处，减少对人工 redline 的依赖。IDEXX Laboratories 报告：30 秒内即可识别 incoming contracts 中的问题。

信息来源:
- https://www.staymodern.ai/solutions/luminance-legal-grade-ai/detailed

#### 1.1.3 风险分类（财务风险、合规风险、运营风险等）的组织方式

- **合规风险模块 (Compliance Module)**: 2025 年 7 月推出，实时检查合同是否符合 DORA (EU)、CCPA (California) 等法规。自动识别正确工作流并执行定制合规检查。
- **可配置仪表盘**: 显示所有在行合同的实时风险敞口 (real-time exposure across all active contracts)。
- **尽职调查场景**: 在 Discovery/Diligence 模块中，热图按概念相似性组织文档集群，颜色深度表示已审查比例。

信息来源:
- https://www.artificiallawyer.com/2025/07/08/luminance-launches-ai-driven-compliance-module/
- https://www.luminance.com/resources/blog/legal-technology-for-the-financial-sector-appraising-risk-and-unlocking-business-intelligence-with-ai/

#### 1.1.4 是否提供风险摘要仪表盘/概览页？其布局和关键指标

- **可配置仪表盘 (Customizable Dashboard)**: 每个团队可配置显示对其最重要的信息。可按需添加数据列（如 logo 使用权限），Lumi 即时跨所有相关协议给出答案。
- **交互式可视化 (Interactive Visualizations)**: 审查结果以一系列交互式可视化呈现，让团队一眼了解审查广度并快速聚焦关键信息。
- **Insights 屏幕**: 提供审计追踪、报告和分析，支持高级过滤和搜索选项。
- **合规仪表盘 (Compliance Dashboard)**: 完全可配置，显示所有在行合同的实时风险敞口，带优先级待办事项列表和自动升级的失败检查项。
- **实时 KPI 追踪**: 用户活动的实时报告，用于项目洞察和 KPI 追踪。

信息来源:
- https://www.luminance.com/contract-intelligence/
- https://www.artificiallawyer.com/2025/07/08/luminance-launches-ai-driven-compliance-module/

#### 1.1.5 风险项的排序和筛选能力

- **Insights 屏幕高级筛选**: 提供 advanced filter and search options（具体筛选项在公开资料中未详细描述）。
- **仪表盘自定义列**: 可为特定数据点（如 logo 使用权限）添加列并即时获取跨合同答案。
- **合规待办事项优先级**: 合规仪表盘提供 prioritized to-do lists，已排序的升级事项。

信息来源:
- https://www.luminance.com/contract-intelligence/

#### 1.1.6 风险趋势分析（同一合同多次版本的风险变化）

**部分支持**:
- **Lumi 版本对比**: Lumi 可将新草案与早期版本对比，解释变更内容和风险敞口如何变化。让团队了解谈判过程中风险的演变。
- **文档家族分析**: 将修正、附属信函和相关协议视为一个不断演变的关系整体来解读，确定优先条款。

**UI/UX 亮点 - 上下文持久性**: Luminance 的理解贯穿合同的整个生命周期——从首次审查到组合洞察——而非每次独立分析。

信息来源:
- https://www.luminance.com/resources/blog/the-next-frontier-for-contract-work-legal-grade-ai-that-understands-the-bigger-picture/

---

### 3.2 原文定位与导航

#### 3.2.1 点击风险标记后如何定位到合同原文？

- **Word 插件内原生定位**: 因为风险标记直接显示在 Word 文档中，用户已经在原文位置。
- **Source-Level Citations**: 每个洞察附带 source-level citations，可追溯至具体条款原文。

信息来源:
- https://www.luminance.com/negotiate/
- https://www.luminance.com/resources/blog/the-next-frontier-for-contract-work-legal-grade-ai-that-understands-the-bigger-picture/

#### 3.2.2 原文高亮方式（颜色标记、下划线、侧边标注等）

- **Traffic Light 颜色标记**: 绿色/琥珀色/红色在文档中直接以颜色高亮标记条款。
- **Word 原生编辑**: 修订建议以 Word 原生格式在文档中呈现。

信息来源:
- https://www.luminance.com/negotiate/
- https://www.luminance.com/resources/blog/product-feature-spotlight-accelerate-negotiations-with-luminance%c2%92s-ai-powered-checklists/

#### 3.2.3 是否支持并排视图（左：合同原文，右：风险分析）？

**以 Word 插件为核心**，Luminance 的风险分析、检查清单、Lumi 聊天等都集成在 Word 侧边栏中。这构成了自然的"左文档/右分析"布局，是最接近理想并排视图的设计之一。

信息来源:
- https://www.luminance.com/negotiate/
- https://www.luminance.com/resources/blog/product-feature-spotlight-accelerate-negotiations-with-luminance%c2%92s-ai-powered-checklists/

#### 3.2.4 是否支持条款间跳转（如从定义跳转到引用处）？

**支持交叉引用分析**:
- 检查清单在 position level 而非逐条处理——自动交叉引用相关条款（如第 3 页责任限制条款和第 5 页对其的引用）。
- 在概念层面理解条款间的关联。

信息来源:
- https://www.luminance.com/resources/blog/product-feature-spotlight-accelerate-negotiations-with-luminance%c2%92s-ai-powered-checklists/

#### 3.2.5 文档内搜索与导航能力

- **Lumi 对话式查询**: "Ask Lumi" 自然语言聊天机器人，可总结合同、按需重新起草条款、回答任何合同查询，提供法律准确的回答。聊天记录自动保存。
- **跨组合查询**: 快速查询完整合同、合同族、修正和债务。
- **概念相似性聚类**: 在 Discovery/Diligence 模块中，按概念聚类文档以便导航。

信息来源:
- https://www.luminance.com/resources/blog/the-next-frontier-for-contract-work-legal-grade-ai-that-understands-the-bigger-picture/
- https://www.luminance.com/legal-ai-software/

#### 3.2.6 多文档关联导航（主合同 ↔ 修订协议 ↔ 附件）

**文档家族概念**:
- Luminance 将修正、附属信函和相关协议解读为"单一、不断演变的关系"来确定优先条款。
- 跨合同组合对话式查询支持查询相关文档族。
- 上下文感知自动化理解每个合同的状态并编排下一步操作。

信息来源:
- https://www.luminance.com/resources/blog/the-next-frontier-for-contract-work-legal-grade-ai-that-understands-the-bigger-picture/

---

### 3.3 中间解释性数据展示

#### 3.3.1 AI 判定风险的理由/依据如何呈现？

**每条款三项解释数据**:
- **Summary（摘要）**: 合同中的条款提出了什么。
- **Reason（理由）**: 为何该条款不符合内部基准。
- **Mark-Up（建议修订）**: 可一键插入的替代语言。

**对话式推理**: Lumi 可解释为何某条款被标记，并提供历史先例作为支撑。

**来源级引用**: 所有洞察附带 source-level citations and clear reasoning。

信息来源:
- https://www.luminance.com/resources/blog/product-feature-spotlight-accelerate-negotiations-with-luminance%c2%92s-ai-powered-checklists/
- https://www.luminance.com/resources/blog/the-next-frontier-for-contract-work-legal-grade-ai-that-understands-the-bigger-picture/

#### 3.3.2 是否展示 Playbook 标准条款与实际条款的对比（diff 视图）？

**自动对比 Playbook**:
- 自动将合同条款与公司 Playbook 比较，标记差异。
- 推荐 preferred 和 fallback 立场以及之前谈判中接受/未接受的类似条款。
- 提供最有可能获得批准的替代语言。

信息来源:
- https://www.luminance.com/negotiate/

#### 3.3.3 是否提供相关法规原文引用？

**合规模块提供法规检查**:
- 自动检查 DORA (欧盟)、CCPA (加州) 等法规的合规性。
- 标记不合规问题（如审计权不足）。
- 未明确描述是否展示完整法规原文引用或条文链接。

信息来源:
- https://www.artificiallawyer.com/2025/07/08/luminance-launches-ai-driven-compliance-module/

#### 3.3.4 置信度/风险评分的可视化

**交通灯分析替代了数值评分**: 使用颜色编码（R/A/G）而非百分比或数值评分。不过该分析粒度达到子条款级别，实际上提供了比简单 H/M/L 标签更细致的风险沟通。

**未见独立置信度评分可视化**。

信息来源: 未找到数值化置信度评分功能的公开信息

#### 3.3.5 历史相似条款的审阅决策参考

**基于真实先例而非静态 Playbook**:
- 在谈判中，Lumi 建议的修订基于 similar past negotiations 中的 real precedent（真实先例），而非静态 Playbook 或猜测。
- 如果组织之前与某个对手方（或类似方）谈过判，该历史影响当前交易。
- 展示在类似谈判中 business has or hasn't accepted 的对比信息。
- 新团队成员获得 institutional knowledge 的即时访问。

**这是 Luminance 的显著差异化特性**——其他竞品更依赖预定义 Playbook 规则，而非动态历史先例。

信息来源:
- https://www.luminance.com/resources/blog/the-next-frontier-for-contract-work-legal-grade-ai-that-understands-the-bigger-picture/
- https://www.luminance.com/resources/blog/product-feature-spotlight-accelerate-negotiations-with-luminance%c2%92s-ai-powered-checklists/

#### 3.3.6 数据来源的可追溯性（AI 的依据是什么？）

- **Source-level citations**: 每个洞察可追溯回具体条款。
- **Clear reasoning**: 所有输出附带清晰推理说明。
- **自研模型透明度**: 采用 "Panel of Judges" 方法——组合多种基础、自研和微调模型，配以超过十年实际使用积累的法律数据集。AI 精心控制每个阶段考虑的信息。
- **自研而非套壳**: 运行自研法律训练 AI 模型（非 OpenAI 套壳），对此部分用户视为优势。

信息来源:
- https://www.luminance.com/resources/blog/the-next-frontier-for-contract-work-legal-grade-ai-that-understands-the-bigger-picture/

---

### 3.4 修改建议与协作

#### 3.4.1 修改建议的呈现形式（内联修订、建议批注、修改对照表）

- **Word 内联 Mark-Up**: AI 自动进行首轮审查并标记问题条款后，提供可一键插入的替代语言（preferred/fallback positions）。
- **检查清单形式**: 以清晰步骤聚焦核心立场的清单界面，逐项勾选完成。提供: Summary + Reason + Mark-Up。
- **Lumi 对话式起草**: 用户向 Lumi 解释商业优先级（如季末速度优先），Lumi 返回针对性的 mark-up，最小化 redline 同时保护核心标准。

信息来源:
- https://www.luminance.com/negotiate/
- https://www.luminance.com/resources/blog/product-feature-spotlight-accelerate-negotiations-with-luminance%c2%92s-ai-powered-checklists/

#### 3.4.2 是否支持一键接受/拒绝修改？

**支持一键插入**:
- 替代语言可 "inserted with a single click"。
- 可接受先前同意的措辞 "at the click of a button"。
- 自动 Mark-Up 可 "surgically inserts mark-ups" 使合同符合金标准。

**Lumi Go 自动谈判**: 对手方也可收到实时 AI 反馈，告知其修改是否可能被接受，并一键插入高通过率替代语言。

信息来源:
- https://www.luminance.com/negotiate/
- https://www.artificiallawyer.com/2024/12/11/luminance-offers-lumi-go-auto-negotiation-capability/

#### 3.4.3 是否支持手动编辑 AI 建议？

**完全支持**:
- 所有功能运行在 Microsoft Word 中——用户可直接在文档中编辑任何内容。
- 用户在应用 AI 建议后可根据需要手动调整。

信息来源:
- https://www.luminance.com/negotiate/

#### 3.4.4 多人协作审阅时的批注与讨论功能

- **实时用户活动报告**: 用于项目洞察和 KPI 追踪。
- **合规任务升级**: 失败的检查自动升级至合规团队，附带通知和优先级待办事项列表。
- **工作流自动化**: AI 代理理解合同状态并自动触发下一步操作，通知相关人员。
- **可分享报告**: Lumi 可生成可下载和分享的定制报告。

**UI/UX 反模式 - 非协作优先平台**: 第三方评测指出审查结果"通常需要通过其他渠道导出或沟通"，暗示 Luminance 不是作为安全协作工作空间设计的，内部团队讨论和批注功能相对较弱。

信息来源:
- https://www.staymodern.ai/solutions/luminance-legal-grade-ai/detailed
- https://www.artificiallawyer.com/2025/07/08/luminance-launches-ai-driven-compliance-module/

#### 3.4.5 版本对比（原合同 vs AI 修改版 vs 最终版）

**Lumi 版本对比**:
- Lumi 将新草案与早期版本对比，解释变更内容和风险敞口变化。
- **文档家族概念**: 不仅对比单一合同的版本，而是将修正、附属信函视为"不断演变的关系"进行整体比较。

信息来源:
- https://www.luminance.com/resources/blog/the-next-frontier-for-contract-work-legal-grade-ai-that-understands-the-bigger-picture/

---

### 3.5 报告与导出

#### 3.5.1 审阅报告的生成格式（PDF、Word、在线报告页）

- **在线仪表盘和可视化**: 交互式可视化、Insights 屏幕、可配置仪表盘提供在线报告体验。
- **Lumi 生成报告**: Lumi 可按需生成定制报告，可下载和分享。
- **Lumi 执行摘要**: Lumi 可用多种语言生成合同关键内容和风险的执行摘要。
- **Word 原生环境**: 所有工作在 Word 中完成，最终输出为 Word 文档。

**未在公开资料中找到具体的报告导出格式清单（如 PDF、CSV 等详细说明）**。

信息来源:
- https://www.luminance.com/contract-intelligence/
- https://www.staymodern.ai/solutions/luminance-legal-grade-ai/detailed

#### 3.5.2 报告内容的可定制性

- **仪表盘可配置**: 每个团队可配置仪表盘显示对其最重要的信息。
- **可添加数据列**: 可为特定数据点（如 logo 使用权限）添加列。
- **Lumi 定制报告**: 按需生成定制报告。
- **合规仪表盘完全可配置**: 显示实时风险敞口。

**但未找到专用报告构建器或模板系统的详细描述**。

信息来源:
- https://www.luminance.com/contract-intelligence/
- https://www.artificiallawyer.com/2025/07/08/luminance-launches-ai-driven-compliance-module/

#### 3.5.3 是否支持导出为 Redline/修订版合同？

**支持**:
- Word 中直接进行 mark-up，保存为标准 Word 文档即为 redline 版本。
- 一键插入替代语言后，合同可直接返回对手方。
- "Auto Mark-Up" 自动插入修订使合同符合标准。

信息来源:
- https://www.luminance.com/negotiate/

#### 3.5.4 审计追踪的呈现（谁在什么时候做了什么决定）

- **合规模块审计追踪**: Comply 功能监控 evolving standards 并"提供全球可审计的合规追踪"。
- **Insights 屏幕**: 提供审计追踪、报告和分析。
- **用户活动实时报告**: 用于项目洞察和 KPI 追踪。

**局限性**: 公开资料中对审计日志的粒度和不可篡改性描述不如 Ironclad 详细。

信息来源:
- https://www.luminance.com/legal-ai-software/
- https://www.luminance.com/contract-intelligence/

#### 3.5.5 数据导出能力（API、CSV、Excel）

- **有限 API 访问**: 第三方评测指出 Luminance 是"更封闭的平台，API 访问有限"。
- 合同审查结果"通常需要通过其他渠道导出"。
- **AWS Marketplace 上架**: 可在 AWS 上部署。

信息来源:
- https://www.staymodern.ai/solutions/luminance-legal-grade-ai/detailed

#### 3.5.6 与项目管理/合同管理系统的集成报告

- **Microsoft Word 原生集成**: 核心工作环境。
- **Microsoft Outlook 集成**: 邮件和日历集成。
- **AWS Marketplace**: 云部署选项。
- **本地部署**: 敏感数据可选择本地部署方案。

信息来源:
- https://www.luminance.com/legal-ai-software/
- https://www.staymodern.ai/solutions/luminance-legal-grade-ai/detailed

---

## 跨竞品关键发现汇总

### 各维度对比矩阵

| 维度 | Ironclad | Kira Systems | Luminance |
|------|----------|-------------|-----------|
| **1.1 条款布局** | 内联追踪修订 + 侧边栏 + 建议卡片 | 网格/表格视图 (Analysis Chart) | 内联颜色标记 + Word 清单 |
| **1.2 风险分级** | H/M/L 标签 + 红色药丸 | 未使用明确三级标签 | 绿色/琥珀色/红色 交通灯 |
| **1.4 仪表盘** | Insights 完整 BI 平台 | Analysis Chart 替代传统仪表盘 | 可配置仪表盘 + 交互式可视化 |
| **2.1 原文定位** | 位置图钉跳转 + 文档高亮 | 原文引用 + 文档查看器 | Word 内原生定位 |
| **2.3 并排视图** | Compare 模式 + 侧边栏文档 | Lito 网格 + 文档查看器 | Word 侧边栏自然布局 |
| **3.1 推理依据** | Playbook 规则溯源 + CAI 分步透明 | Built-in citations + Chat 引用 | Summary + Reason + Mark-Up 三项 |
| **3.2 Playbook 对比** | Playbook 驱动的 Redline 对比 | 部分匹配 Redline 对比 | 自动对比 Playbook + 历史先例 |
| **3.4 置信度评分** | 定性风险标签，无数值评分 | Quick Study 置信度评分 | 交通灯替代数值评分 |
| **3.5 历史参考** | Playbook 历史定位影响建议 | Quick Study 增量学习（模型级） | 真实先例谈判记录（显著特色） |
| **4.1 修改建议** | 内联追踪修订 + 建议卡片 | Redline 对比 + Litera Compare | Word 内联 Mark-Up + 清单 |
| **4.2 一键接受** | 完全支持（批量+逐条） | 批量接受/拒绝 | 一键插入替代语言 |
| **4.4 协作** | 评论/@提及/Activity Feed | 标签/分组/分配（非实时讨论） | 工作流自动化（非协作优先） |
| **5.1 报告格式** | DOCX/PDF/CSV/PNG/JPEG/SVG | Word/Excel/PDF | 在线仪表盘 + Word 原生 |
| **5.4 审计追踪** | 条款级不可篡改审计日志 | 项目级进度追踪 | 合规审计追踪 |
| **5.5 API** | 审计日志 API + 第三方集成 | 良好 API 批量分析 | 有限 API（封闭平台） |

### UI/UX 反模式汇总

| 反模式 | 竞品 | 描述 |
|--------|------|------|
| 缺乏合同级风险聚合视图 | Ironclad | 单条款风险标签清晰，但缺乏合同级风险计分卡 |
| Activity Feed 信息过载 | Ironclad | 评论、版本、审计混合在同一 Feed，缺乏分类过滤 |
| 缺乏专用分屏风险审阅视图 | Ironclad | 风险信息在侧边栏/弹窗中，非实时并排 |
| 缺乏直观风险评级标签 | Kira | 偏向提取工具，无红/黄/绿直观风险标记 |
| 缺乏专用风险仪表盘 | Kira | 分析能力嵌入工作流而非独立 BI 层 |
| 并排视图不够紧密集成 | Kira | 网格与文档查看器是独立窗口，需频繁切换 |
| 缺乏实时协作评论功能 | Kira | 协作依赖标签分配而非实时讨论 |
| 导出定制性受限 | Kira | 用户期望更多导出自定义选项 |
| 非协作优先平台 | Luminance | 结果需通过其他渠道导出沟通 |
| 学习曲线陡峭 | Luminance | 分层界面需要引导式入职和持续培训 |
| API 有限 | Luminance | 封闭平台，API 访问受限 |
| 不是安全协作工作空间 | Luminance | 缺乏内置讨论和批注功能 |

### 各竞品核心差异化优势

1. **Ironclad**: 最完整的 CLM 生态 + BI 分析 + 不可篡改审计追踪。适合需要全生命周期合同管理的中大型企业法务团队。
2. **Kira Systems**: 最深度的条款提取库（1,400+ 字段）+ Quick Study 自定义训练。适合大规模 M&A 尽职调查和需要高精度条款提取的场景。
3. **Luminance**: 最直观的风险可视化（交通灯）+ 多语言支持（80+ 语言）+ 基于真实历史先例的谈判建议。适合跨国企业和需要快速直观风险判断的场景。
