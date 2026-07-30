# CLM & Analytics Tier: 审核结果呈现原始调研数据

> 调研日期: 2026-07-29
> 调研范围: Lexion (现 DocuSign IAM) 与 Evisort (现 Workday CLM)
> 研究方法: 多轮 WebSearch + WebFetch，覆盖官网、产品页、博客、专利文献、第三方评测（G2、Capterra、Artificial Lawyer、Forrester Wave、Gartner Magic Quadrant）

---

## 1. Lexion

> **产品定位**: AI 驱动的合同全生命周期管理 (CLM) 平台。2019 年创立于 Allen Institute for AI，2024 年 5 月被 DocuSign 以 ~$165M 收购。核心差异化：Microsoft Word 内嵌的 GPT 驱动的合同审查助手 + 智能合同仓库 + 邮件优先的工作流。

### 维度 1: 风险项的展示

#### 1.1 风险条款的呈现布局

Lexion 的风险条款呈现分布在两个界面中：

**a) Deal Review Dashboard（专利描述的合同审阅仪表盘）**
根据 Lexion 专利 US20200026916A1 的描述，合同审阅界面采用**并排对比视图 (side-by-side comparison)**：
- 左侧展示当前合同中提取的条款
- 右侧展示仓库中存储的标准/首选条款
- 每条对比项可**展开/折叠**，展开后显示从各来源文档中提取的源文本
- 用户可**动态接受或拒绝**对比的合同条款

信息来源: US Patent US20200026916A1 — "Document term extraction and comparison" (FIG. 4A, 4B)

**b) Microsoft Word 内嵌的 AI Contract Assist**
审查结果直接显示在 Microsoft Word 的修订模式中：
- AI 根据 Playbook 规则标记不合规语言
- 标记以 Word 的**修订（Track Changes）格式**呈现：插入/删除以红色标注
- 用户选中任意条款后可请求 AI 生成修订建议（"Modify"功能）

信息来源: https://www.lexion.ai/products/ai-contract-assist

**c) 中央仪表盘**
- 工作流卡片视图：每个合同/工作流以卡片形式展示状态
- Deal Review List：列包括任务名、负责人、创建日期、产品、状态、被拒项目、完成百分比
- 支持搜索栏查找特定交易

信息来源: https://www.lexion.ai/products/workflow

#### 1.2 风险分级（高/中/低）的视觉呈现方式

**未找到明确的"高/中/低"三级风险评分系统。**

Lexion 采用的是**二元合规判断**模式——基于 Playbook 规则，条款要么合规、要么不合规（被标记）。在工作流层面，状态使用颜色编码：
- 绿色 = 已签署/已完成
- 黄色 = 等待审核/进行中
- 红色 = 逾期

信息来源: G2 用户评论汇总; https://www.lexion.ai/post/the-value-of-a-contract-management-dashboard

> **⚠️ UX 反模式**: 缺乏颗粒化的风险分级可能迫使审阅者对所有标记一视同仁，无法优先处理高影响条款。相较于竞品（如 Luminance 的红色/琥珀色/绿色风险评分），Lexion 的方法更粗放。

#### 1.3 风险分类的组织方式

风险按 **Playbook 维度**组织，而非按风险类型分类：
- 用户通过自然语言创建自定义 Playbook 规则（"用简单语言解释你希望合同遵循的规则"）
- 预装 5 个行业标准 Playbook（常见合同类型）
- 可为同一合同类型保存多个 Playbook
- AI 根据最匹配的 Playbook 规则进行标记

**未找到按财务风险/合规风险/运营风险等标准风险分类体系的公开信息。**

信息来源: https://www.lexion.ai/products/ai-contract-assist

#### 1.4 风险摘要仪表盘/概览页

**KPI Reports 仪表盘**：
- 合同审阅量（总法律项目数）
- 平均审阅时间
- 可按任务类型、项目负责人、状态和时间范围筛选
- 以**图表和图形**形式呈现效率数据

**管理仪表盘**：
- 所有开放项目及团队进度
- 任务状态指标（告知下一步行动）
- 活动日志（显示每个项目的工作内容和执行人）
- 讨论线程（团队沟通记录）

文档索引起始日期等关键信息被记录在仪表盘上，防止合同"漏网"。

信息来源: https://www.lexion.ai/post/the-value-of-a-contract-management-dashboard; https://www.lexion.ai/post/prove-your-value-and-optimize-your-contracting-workflow-with-data

> **⚠️ UX 反模式**: SpotDraft 等竞品比较指出 Lexion 可能缺乏"开箱即用的仪表盘和预构建图表"，分析能力相对基础。G2 用户评论也提到"高级报告功能有限"。（来源: SpotDraft vs Lexion 对比页面; G2 评论）

#### 1.5 风险项的排序和筛选能力

- KPI 报告支持按**任务类型、项目负责人、状态和时间范围**筛选
- Deal Review List 包含搜索功能
- 智能仓库支持 AI 驱动的搜索和自定义报告
- 可按合同类型、状态、日期、用户、标签等生成报告

**未找到针对风险严重程度或影响范围进行排序的公开信息。**

信息来源: https://www.saasworthy.com/product/lexion-ai

#### 1.6 风险趋势分析

**版本控制功能**提供跨版本的差异追踪：
- 文档比较（Document Comparison）功能：自动识别两个版本间的差异
- 修订历史：所有版本存储在仓库中，AI 索引
- 分支文件追踪：当用户复制某版本进行修订时，系统自动追踪分支间的差异

但**未找到显式的"风险趋势仪表盘"或"同一合同多版本风险变化分析"功能**。版本追踪侧重于文本差异而非风险指标演变。

信息来源: https://www.lexion.ai/post/advantages-version-control-in-clm

---

### 维度 2: 原文定位与导航

#### 2.1 点击风险标记后如何定位到合同原文

**两种定位路径**：

a) **专利描述的仪表盘内定位**：在 Deal Review Dashboard 中，用户点击对比项后，展开相关文本，显示从源文档提取的具体段落。系统自动关联到原文位置。

b) **Word 内嵌定位**：AI Contract Assist 直接在 Microsoft Word 中运作，标记直接在文档原文中以修订模式显示——无需"跳转"，标记即是原文上的标注。

信息来源: US Patent US20200026916A1; https://www.lexion.ai/integrations/microsoft-word

#### 2.2 原文高亮方式

- **Microsoft Word 修订模式**：插入以红色下划线标注，删除以红色删除线标注——采用 Word 原生 Track Changes 视觉规范
- Playbook 标记的"不合规语言"以 Word 的批注/修订形式呈现

**未找到非 Word 环境下的专用高亮方案（如 Web 端阅读器的颜色标记、侧边标注等）的公开信息。**

信息来源: https://www.lexion.ai/post/best-practices-contract-redlining

#### 2.3 并排视图支持

**支持，但为特定用途设计：**

- **专利描述的并排视图**：左（提取的合同条款）vs 右（仓库标准条款）——用于条款对比验证，而非合同原文 vs 风险分析的并行阅读
- **文档比较的并排视图**：支持并排对比两份文档版本
- **Word 内不支持独立的并排分析面板**——所有工作在同一文档窗口内完成

信息来源: US Patent US20200026916A1; https://www.lexion.ai/post/best-practices-contract-redlining

> **⚠️ UX 反模式**: 缺乏"左原文、右分析"的专用审阅布局。用户必须在 Word 修订模式中工作，或切换到仪表盘查看结构化对比。对于深度法律审阅，这可能不够直观。

#### 2.4 条款间跳转

**支持但有限**：
- AI 仓库可搜索跨合同的特定条款
- "Ask"功能允许自然语言问答（"这个合同关于终止的通知期是多久？"）
- 但**未找到从定义条款跳转到引用处、或条款间超链接导航的公开信息**

信息来源: https://www.lexion.ai/products/ai-contract-assist

#### 2.5 文档内搜索与导航

- AI 仓库支持**直观的搜索功能**：用户可按合同版本搜索，或跨同一合同的多个版本搜索
- 支持搜索 **120+ 预定义的 AI 字段**（当事方名称、日期、终止期、管辖法律、续约日期、义务等）
- 支持自定义报告生成（"几秒内构建关于你合同的自定义自动化报告"）

信息来源: https://www.lexion.ai/post/advantages-version-control-in-clm; https://www.lexion.ai/resources/artificial-intelligence

#### 2.6 多文档关联导航

- **仓库集中化**：所有合同、修订协议、附件存储在单一 AI 仓库中
- **版本分支追踪**：支持分支文件的来源追踪
- **关联搜索**：支持跨合同版本搜索

但**未找到显式的"主合同-修订协议-附件"层级关联导航界面**的公开信息。

信息来源: https://www.lexion.ai/post/advantages-version-control-in-clm

---

### 维度 3: 中间解释性数据展示

#### 3.1 AI 判定风险的理由/依据

**上下文信息有限。** Lexion 的判定逻辑基于：
- Playbook 规则匹配：AI 检查合同条款是否与预设的 Playbook 标准一致
- 标记基于规则偏离（deviation detection），而非基于法律推理的"解释"

**未找到 AI 对每个标记提供详细推理文本的公开信息。** 产品页面仅提到 AI "标记需要注意的语言"并"提供建议以使其回归合规"，但没有描述为何某条款被标记的解释性文字。

信息来源: https://www.lexion.ai/products/ai-contract-assist

> **⚠️ UX 反模式（关键缺失）**: 这是 Lexion 审阅结果呈现中最大的信息缺口。缺乏"为什么这个条款有问题"的解释会降低审阅者对 AI 判断的信任度，并增加审阅者自行判断的时间成本。对于非法律背景的合同管理者尤其成问题。

#### 3.2 Playbook 标准条款与实际条款的对比（Diff 视图）

**部分支持：**
- Deal Review Dashboard 的并排对比视图就是为此设计的——一侧显示提取的条款，另一侧显示仓库标准
- Word 中的修订模式提供了实际的文本差异视图
- 文档比较功能提供版本间差异

但**标准 Playbook 条款 vs 实际条款的专用 diff 视图未在公开信息中找到**。

信息来源: US Patent US20200026916A1; https://www.lexion.ai/post/advantages-version-control-in-clm

#### 3.3 相关法规原文引用

**未找到公开信息。** Lexion 的产品页面和文档中未提及法规引用功能。Playbook 方法侧重于公司的内部标准而非外部法规。

#### 3.4 置信度/风险评分的可视化

**未找到公开信息。** Lexion 的产品材料中未出现置信度评分、概率百分比或风险量化评分的视觉呈现。

信息来源: 所有 Lexion 相关搜索结果

#### 3.5 历史相似条款的审阅决策参考

**部分支持：**
- 仓库存储了所有历史合同和修改版本
- 专利描述的对比功能将当前条款与"仓库中的条款"进行对比——这本质上使用了历史数据作为参考基准
- 但**未找到显式的"类似情况下的历史审阅决策"推荐功能**

信息来源: US Patent US20200026916A1

#### 3.6 数据来源的可追溯性

- AI 字段提取：120+ 字段的来源可追溯到原文
- 专利中的"展开"功能显示从源文档提取的文本
- 审计追踪记录谁签署、何时、何种签名类型
- **但 AI 判定逻辑的可追溯性（"为什么 AI 认为这有问题"）有限**

信息来源: US Patent US20200026916A1; https://www.lexion.ai/post/advantages-version-control-in-clm

---

### 维度 4: 修改建议与协作

#### 4.1 修改建议的呈现形式

**以 Microsoft Word 原生修订（Track Changes）格式呈现：**
- **内联修订**：AI 建议直接在 Word 文档中以红色标注的插入/删除形式呈现
- **修订建议**：用户可通过 "Modify" 功能选中条款并用自然语言描述修改需求，AI 生成修订建议
- **条款生成**："Add" 功能允许用自然语言描述需求，AI 直接生成新条款文本
- 支持生成**多个替代方案**（"another option"）

信息来源: https://www.lexion.ai/products/ai-contract-assist; https://www.accesswire.com/834274/lexion-launches-stand-alone-version-of-ai-contract-assist

#### 4.2 一键接受/拒绝修改

- **支持**：Lexion 的红线最佳实践指南明确提到"软件使接受或拒绝红线修改变得容易"
- 在 Word 中，用户可使用 Microsoft Word 原生的接受/拒绝修订功能
- Lexion 平台使其"容易接受或拒绝红线、管理插入和删除、以及发表评论"

信息来源: https://www.lexion.ai/post/best-practices-contract-redlining

#### 4.3 手动编辑 AI 建议

- **支持**：因为 AI Contract Assist 在 Word 中运作，用户可以自由编辑任何 AI 建议
- 用户可请求 AI 生成替代方案（"生成另一个选项"）
- 用户可直接修改 AI 建议的文本，如同编辑普通 Word 文档

信息来源: https://www.lexion.ai/products/ai-contract-assist

#### 4.4 多人协作审阅时的批注与讨论功能

- **讨论线程**：每个合同任务内置集中式讨论，沟通与工作绑定
- **内部/外部评论**：支持内部评论（仅团队可见）和外部评论（与对方共享）
- **邮件驱动的协作**：利益相关方可通过邮件提交合同和回复，自动转化为仪表盘任务
- **实时协作可见性**：Word 插件显示团队成员何时正在编辑文档，避免版本冲突
- **自动通知**：关键节点自动提醒利益相关方

信息来源: https://www.lexion.ai/post/the-value-of-a-contract-management-dashboard; https://www.lexion.ai/integrations/microsoft-word

#### 4.5 版本对比

- **文档比较功能**：自动识别版本间差异，以"易于阅读的格式"呈现
- **修订历史**：所有版本集中存储，仪表盘清晰显示最新版本和历史版本
- **分支文件差异追踪**：自动追踪从原始文件分支出的副本的差异
- **签署版本记录**：捕获签署时的实时版本、签署人、签署时间和签名类型

信息来源: https://www.lexion.ai/post/advantages-version-control-in-clm

---

### 维度 5: 报告与导出

#### 5.1 审阅报告的生成格式

- KPI 报告支持**下载和分享**
- 支持**PDF 合同转 DOCX**
- 自定义报告可按合同类型、状态、日期、用户、标签等维度生成
- 报告可**一键下载或发送**

**未找到具体的 PDF/Word/在线报告页格式细节。**

信息来源: https://www.saasworthy.com/product/lexion-ai; https://www.lexion.ai/post/prove-your-value-and-optimize-your-contracting-workflow-with-data

#### 5.2 报告内容的可定制性

- 用户可构建"自定义自动化报告"（维度包括合同类型、状态、日期、用户、标签等）
- KPI 报告可按任务类型、项目负责人、状态和时间范围筛选
- **但 G2 用户反馈指出报告功能"有限"**，某些自定义 AI 字段识别和前合同管理功能在开发中

信息来源: G2 用户评论; https://www.lexion.ai/post/advantages-version-control-in-clm

#### 5.3 导出为 Redline/修订版合同

- **支持**：红线合同可通过 Word 另存为修订版
- Word 插件支持**一键上传回 Lexion**作为新版本
- PDF 可转换为 DOCX 后再进行修订

信息来源: https://www.lexion.ai/post/edit-your-pdfs-in-microsoft-word; https://www.lexion.ai/integrations/microsoft-word

#### 5.4 审计追踪的呈现

- **标准审计追踪功能**：记录团队成员何时查看或修改合同
- **签署证明**：记录谁签署、何时、何种签名类型、签署时的合同版本
- **活动日志**：完整日志记录所有活动、消息历史
- **审批追踪**：追踪审批流程，确保关键利益相关方未被遗漏
- **安全认证**：SOC 2 Type II、ISO 27001 认证、AES-256 加密

> ⚠️ SpotDraft 对比将 Lexion 的审计追踪描述为"Basic audit trail, Fragmented email tracking"，表明追踪功能可能不如某些竞品全面。

信息来源: https://www.softwareadvice.com/ca/legal/evisort-profile/reviews/ — SpotDraft 对比; https://www.softwaresuggest.com/lexion

#### 5.5 数据导出能力

- **下载/分享报告**：支持报告下载
- **API**：发现 Lexion OpenAPI 规范文档在 GitHub（`api-evangelist/lexion` 仓库），确认存在 REST API
- **集成**：Salesforce 集成、Adobe Acrobat Sign 集成、Box/Google Drive/SharePoint/Dropbox/OneDrive 集成

信息来源: https://raw.githubusercontent.com/api-evangelist/lexion/refs/heads/main/openapi/lexion-openapi.yml

#### 5.6 与项目管理/合同管理系统的集成报告

- **Salesforce 集成**：销售团队可直接在 Salesforce 中查看法律审阅状态，状态随合同进展自动更新
- **KPI 报告**：量化法律团队价值和贡献，可分享给利益相关方
- **数据驱动决策**：效率数据以"图表和图形"呈现，供利益相关方做出数据驱动决策

信息来源: https://www.lexion.ai/post/accelerate-sales-lexion-salesforce; https://www.lexion.ai/post/prove-your-value-and-optimize-your-contracting-workflow-with-data

---

### 收购后演变: Lexion -> DocuSign IAM

- **2024 年 4 月**：DocuSign 推出 Intelligent Agreement Management (IAM) 平台（Navigator 智能仓库 + Maestro 无代码工作流）
- **2024 年 5 月**：以 $154-165M 收购 Lexion
- **2025 年初**：Lexion 技术整合为 DocuSign "Contract Intelligence" 功能：自动红线修订、风险评估、AI 合同审阅（基于 Playbook）、文档问答和条款洞察
- **2025 年 4 月**：DocuSign 推出 AI 合同代理（由 DocuSign Iris 专有 GenAI 引擎驱动）
- **2025 Release 1**：Obligation Management（自动义务审阅和追踪）、与 Salesforce Agentforce 集成、Custom extractions

截至 2025 Q3，超过 25,000 客户已迁移至 IAM 平台，Net Dollar Retention 回升至 102%+。

信息来源: https://investor.wedbush.com/wedbush/article/marketminute-2026-1-1-beyond-the-dotted-line-how-docusign-reinvented-itself-for-the-ai-era; https://preview.docusign.com/blog/docusign-2025-release-1

---

## 2. Evisort

> **产品定位**: AI 合同智能平台。2016 年创立，2024 年 9 月被 Workday 以 $311M 收购。核心差异化：智能仪表盘（自填充、交互式）+ 120+ 预训练 AI 模型 + Document X-Ray 自定义模型构建器 + Workday 生态系统集成。

### 维度 1: 风险项的展示

#### 1.1 风险条款的呈现布局

**a) 并排条款导航视图 (Pre-Signature Workflow)**
根据多篇博客和产品描述，Evisort 的合同审阅界面采用**经典的双面板布局**：
- **左侧**：完整的合同草稿文本（文档查看器）
- **右侧**：AI 识别的**关键条款列表**（"Clauses"侧边栏），按条款类型分组（例如：Assignment, Audit, Confidentiality, Indemnification, Insurance 等）
- 每条条款旁有**状态指示器**（绿色勾号表示标准条款，感叹号图标表示需要注意的条款）
- 条款列表随编辑自动更新
- 点击条款列表中的任一条款，**直接跳转**到合同文档中对应位置

信息来源: https://evisort-d288ab.webflow.io/blog/how-evisorts-ai-powers-pre-signature-workflows-and-custom-dashboard（页面包含详细截图描述）

**b) 智能仪表盘 (Intelligent Dashboarding)**
四个主要仪表盘（位于 Insights 选项卡下）：
1. **Documents Dashboard**：合同量（按当事方、执行状态、合同类型、语言、文件类型、管辖法律）；付款条款、违约通知期、终止通知期；重复文件识别
2. **Expirations Dashboard**：即将到期的合同续约通知和到期日（按续约类型拆分）
3. **Tickets Dashboard**：开放的工作流工单（含阶段和老化报告）
4. **Workflows Dashboard**：生产力和吞吐量指标（积压趋势、周期时间、开关率）

**c) 自定义仪表盘**
拖拽式自定义仪表盘，支持布尔逻辑和累积搜索，可将所有 Evisort AI 提取的数据点可视化。

信息来源: https://www.evisort.com/blog/evisort-intelligent-dashboarding-for-contracts（现已重定向至 Workday）; https://www.legaltechdaily.com/2021/10/evisort-now-self-populates-contract-dashboards-to-quickly-visualize-data-and-summarize-key-metrics/

#### 1.2 风险分级（高/中/低）的视觉呈现方式

- **条款级图标指示**：在 Pre-signature 的条款列表中，绿色勾号表示合规/标准条款，感叹号图标表示需要审阅的例外条款
- **Playbook 驱动的异常标记**：Workday Contract Negotiation Agent 对照企业 Playbook 分析合同，标记风险点和不合规条款

**未找到明确的三级（高/中/低）颜色编码风险分级。** Evisort 似乎更侧重于"例外优先 (exception-first)"的二元标记——即条款要么符合标准、要么需要关注。

信息来源: https://evisort-d288ab.webflow.io/blog/how-evisorts-ai-powers-pre-signature-workflows-and-custom-dashboard; https://blog.workday.com/en-gb/agentic-contract-review-redlining-here.html

#### 1.3 风险分类的组织方式

- **条款类型维度**：AI 自动识别 230+ 预训练条款类型，并按条款类别组织（Assignment, Audit, Confidentiality, Indemnification, Insurance 等）
- **自定义 AI 模型维度**：120+ 预构建模型覆盖 HR 协议、供应商合同、金融、法律、IT、销售交易等领域
- **Playbook 维度**：用户可通过保存和组织 "Ask AI" 问题构建**虚拟合规 Playbook**
- **自定义分类**：Document X-Ray 允许用户用自然语言定义任何追踪维度

信息来源: https://www.evisort.com/blog/document-xray-empowers-customers-in-unprecedented-ways; https://www.artificiallawyer.com/2025/10/22/workday-launches-contract-ai-library/

#### 1.4 风险摘要仪表盘/概览页

**Intelligent Dashboarding 是 Evisort 的旗舰分析能力：**
- **自填充**：无需手动数据录入，合同导入后仪表盘自动生成
- **交互式**：所有图表支持交叉筛选和钻取——点击图表某部分可细化所有图表
- **钻取到文档**：从任意图表可直接导航到底层合同文档
- **角色权限控制**：仪表盘可见性基于用户权限

**实际影响**：CEO Jerry Ting 声称"周一导入 10,000 份合同，周二就能带着交互式仪表盘走进董事会议室"。

**真实使用案例**：
- 某医疗机构合规官："我直接把 Evisort 合同仪表盘打印出来放进董事会报告"
- McKesson：将合同审阅时间从 5 天减少到 1 天，并创建了面向客户的安全门户仪表盘

信息来源: https://www.legaltechdaily.com/2021/10/evisort-now-self-populates-contract-dashboards-to-quickly-visualize-data-and-summarize-key-metrics/; https://www.workday.com/en-au/customer-stories/i-p/mckesson-streamlines-clm-with-ai-insights.html

> **⚠️ UX 反模式**: 多个用户评论指出"报告和仪表盘不可自定义"，预构建视图给人留下深刻印象后，高级用户可能会因为无法深度定制而感到沮丧。同时，仪表盘数据提取问题和编辑器问题也存在。

#### 1.5 风险项的排序和筛选能力

- **Advanced Search**：使用术语和连接符的强大搜索，条款级内容搜索，模板变体搜索——能够"审问整个合同组合"
- **交叉筛选仪表盘**：点击任意图表元素可按合同类型、日期、当事方、管辖地、文件名等维度过滤所有图表
- **可保存搜索**：自定义仪表盘的搜索条件可保存
- **布尔逻辑**：自定义仪表盘支持完整布尔逻辑和累积搜索构建

信息来源: https://www.evisort.com/blog/getting-started-with-dashboards-in-evisort; 软件评测汇总

#### 1.6 风险趋势分析

- **Workflows Dashboard** 提供时间序列分析：积压趋势、周期时间、开关率随时间变化
- **异常优先对比**：跨文档版本和合同群组的条款对比，突出偏差
- **义务追踪**：监控从偏差分析中浮现的截止日期、续约和义务条款

**未找到专门的"同一合同多版本风险评分趋势图"功能，但仪表盘的时间序列框架可以支持此类分析。**

信息来源: https://www.workday.com/en-au/products/contract-management/contract-lifecycle-management.html

---

### 维度 2: 原文定位与导航

#### 2.1 点击风险标记后如何定位到合同原文

**一键跳转定位**：
- 用户在右侧条款列表中点击条款（如 "Assignment"）
- 左侧合同文档自动**滚动到对应条款位置**
- 条款列表随合同编辑**自动更新**，确保导航始终准确
- 2022 年新的文档查看器支持在 PDF 原文中**搜索并链接**到关键条款和字段

信息来源: https://evisort-d288ab.webflow.io/blog/how-evisorts-ai-powers-pre-signature-workflows-and-custom-dashboard; https://www.getapp.com.au/software/2036483/evisort

#### 2.2 原文高亮方式

- **文档查看器中的上下文高亮**：点击条款后在原文中显示上下文
- **PDF 预览和评论**：2022 年更新的文档查看器支持在 PDF 原文中直接添加评论
- **并排视图中的关联高亮**：条款选中状态在左侧文档中对应显示

**未找到颜色编码高亮方案的具体细节（如不同风险等级使用不同颜色标记）。**

信息来源: https://www.getapp.com.au/software/2036483/evisort; https://www.artificiallawyer.com/2022/01/19/product-walk-through-evisort-contract-intelligence/

#### 2.3 并排视图支持

**高度支持，这是 Evisort 审阅 UI 的核心**：

- **条款列表 + 完整文档的并排视图**：右侧结构化条款导航，左侧完整合同原文
- **合同原文 + AI 提取字段的并排视图**：用户评论特别赞扬此功能为"绝对的时间节省器"
- **文档更改和评论的并排视图**：在单一屏幕上查看变更和讨论

信息来源: https://www.getapp.com.au/software/2036483/evisort; https://evisort-d288ab.webflow.io/blog/how-evisorts-ai-powers-pre-signature-workflows-and-custom-dashboard

#### 2.4 条款间跳转

- **条款列表导航**：在结构化条款列表和完整合同之间跳转
- **Ask AI 自然语言问答**：向合同提问（"早期终止会发生什么？""是否有折扣可用？""可以收取部分履行的费用吗？"），答案附带**指向具体条款的链接**
- **跨文档搜索**：可搜索整个合同组合中的特定条款

但**未找到从定义条款自动跳转到引用处的超链接导航。**

信息来源: https://www.evisort.com/blog/ask-anything-track-everything-with-document-xray

#### 2.5 文档内搜索与导航

Evisort 的搜索被多个用户评价为**"同类最佳"**：
- 条款级内容搜索
- 术语和连接符搜索
- 模板变体搜索
- 过滤功能允许堆叠多个条件
- 合同组合级别的批量搜索

信息来源: 软件评测汇总（G2, Capterra, Software Advice）

#### 2.6 多文档关联导航

- 仓库集中存储所有合同
- **跨合同条款对比**：跨文档比较条款差异
- Google Drive/OneDrive 自动同步导入

**但一个已知限制**：AI 无法跨关联合同进行分析——分析仅限于单个文档。这意味着主合同和修订协议之间的条款关联不会被 AI 自动识别。

信息来源: https://www.rfp.wiki/legal-compliance/contract-lifecycle-management/advanced-contract-analytics/evisort （Support Reality 评测）

> **⚠️ UX 反模式（关键限制）**: Evisort 的 AI 分析不支持跨关联文档。如果一份主合同有三份修订协议，AI 不会自动关联分析这些文件。对于复杂的合同层级结构，这是一个显著的局限性。

---

### 维度 3: 中间解释性数据展示

#### 3.1 AI 判定风险的理由/依据

**Workday Contract Negotiation Agent 提供明确的理由说明：**
- 每个编辑建议附带**"清晰的、即时的上下文"**
- 详细说明"**为什么特定条款被标记**"以及"**提议的编辑如何与你的 Playbook 参数一致**"
- 目的是消除审阅者的猜测工作

**Ask AI 提供源链接回答：**
- 自然语言问题获得"清晰、有理有据的答案"
- 答案附带**指向告知答案的具体合同条款的链接**

信息来源: https://blog.workday.com/en-gb/agentic-contract-review-redlining-here.html; https://www.evisort.com/blog/ask-anything-track-everything-with-document-xray

#### 3.2 Playbook 标准条款与实际条款的对比（Diff 视图）

**"异常优先对比"方法是 Evisort 的核心差异化：**
- 与其要求审阅者逐行阅读全文，AI 自动**高亮条款差异和偏差**
- 支持**跨文档条款级对比**（版本间对比、与标准库对比、跨合同组合对比）
- **精确定位红线 (pinpoint redlines)**：最小必要修改，而非整体替换条款——使对方更容易接受

信息来源: https://wifitalents.com/best/contract-analysis-software/; https://blog.workday.com/en-gb/agentic-contract-review-redlining-here.html

#### 3.3 相关法规原文引用

- Workday CLM 提到 **"合规性追踪"**作为核心能力
- **HIPAA 合规监控**（医疗行业使用案例）
- **KYC/AML 语言追踪**（金融服务使用案例）
- **POPIA 合规**（南非市场案例）

但**未找到 AI 直接引用具体法律条文或法规原文的公开信息。**

信息来源: https://www.evisort.com/blog/ask-anything-track-everything-with-document-xray; https://techcentral.co.za/workday-evisort-popia-sa-contracts/269572/

#### 3.4 置信度/风险评分的可视化

**未找到公开信息。** 尽管 Document X-Ray 使用 AI 编排引擎（运行数百次实验以选择最佳 LLM 和优化提示语言），但系统不向用户展示数值置信度评分。准确度以定性术语描述（"惊人的准确度""高度准确的 AI""可信"）。

信息来源: 所有 Evisort 相关搜索结果; https://www.artificiallawyer.com/2022/07/20/evisort-focuses-on-nlp-training-after-no-humans-in-the-loop-push/

#### 3.5 历史相似条款的审阅决策参考

- **条款库和模板**：维护首选和备选语言目录作为基准
- **自定义 AI 模型**：用户可训练 AI 识别组织特定的条款和合规需求（只需少量示例）
- **已保存的 Ask AI 问题**：团队可共享已保存的问题，构建虚拟 Playbook
- 但**未找到显式的"此条款在历史上被 80% 的审阅者接受"这类历史决策统计**

信息来源: https://www.evisort.com/blog/document-xray-empowers-customers-in-unprecedented-ways; https://www.precognio.com/evisort/

#### 3.6 数据来源的可追溯性

- **Ask AI 答案附带源链接**：告知答案的具体合同条款
- **仪表盘钻取**：从图表直接导航到底层合同文档
- **AI 编排引擎**：Document X-Ray 在发布模型前运行数百次实验，选择最佳 LLM 并推荐优化提示语言——但这种**内部编排过程对用户不可见**
- **审计追踪**：合同从初稿到执行的完整历史

信息来源: https://www.evisort.com/blog/ask-anything-track-everything-with-document-xray; https://finance.yahoo.com/news/evisort-extends-ai-leadership-advanced-130000776.html

---

### 维度 4: 修改建议与协作

#### 4.1 修改建议的呈现形式

**多层次呈现：**

a) **精确定位红线 (Pinpoint Redlines)**：
- 在合同原文上进行**最小必要修改**
- 例如：调整赔偿条款的*影响范围*以匹配批准条款，而非替换整个条款
- 设计原则：使对方更容易理解和接受修改

b) **Track Changes 格式**：
- 标准的插入/删除修订标记
- 支持**内部评论/红线**（仅团队可见）和**外部评论/红线**（与对方共享）

c) **生成式 AI 辅助**：
- 自动化红线修订
- 基于现有 AI 合同数据和大语言模型的条款创建和合同起草

信息来源: https://blog.workday.com/en-gb/agentic-contract-review-redlining-here.html; https://www.workday.com/en-au/products/contract-management/contract-lifecycle-management.html

#### 4.2 一键接受/拒绝修改

- Workday Contract Negotiation Agent 描述为 **"human-in-the-loop"** 方法
- 专业人士可以"评估理由，自信地批准更改"
- **但具体的接受/拒绝 UI 控件（按钮、复选框、审批托盘等）未在公开材料中详细描述**

信息来源: https://blog.workday.com/en-gb/agentic-contract-review-redlining-here.html

#### 4.3 手动编辑 AI 建议

- **支持**：审阅者可以在接受前编辑 AI 建议
- AI 提供的是"建议"而非"自动修改"
- 用户可自定义 AI 模型（用组织特定数据训练），间接影响建议质量
- **但 AI 建议的直接文本编辑能力未在公开材料中详细描述**

信息来源: https://blog.workday.com/en-gb/agentic-contract-review-redlining-here.html

#### 4.4 多人协作审阅时的批注与讨论功能

- **2022 年 PDF 预览和评论**：可在原始 PDF 文档中直接添加评论
- **内部/外部评论分离**：团队内部评论和对手方可见评论分开管理
- **平台内协作**：协作和红线追踪统一在一个平台内完成
- **审批路由**：合同可自动路由至适当的利益相关方审批

信息来源: https://www.getapp.com.au/software/2036483/evisort; https://www.legalreader.com/evisort-empowers-clm-customers-with-ai-in-pre-signature-contract-workflows/

> **⚠️ UX 反模式**: 多个评论指出"工作流创建有明显的学习曲线"，不如某些竞品直观。新用户界面"一开始不知所措"（too much, too soon）。某些功能"难找，因为一开始不明显"，功能的可发现性是反复出现的痛点。

#### 4.5 版本对比

- **异常优先合同对比**：高亮版本间条款差异和偏差
- **跨文档条款级对比**：识别不同版本和合同组合间的偏差
- **审阅者协作标记**：支持团队协作编辑和追踪决策
- **审计就绪输出**：所有决策有完整记录

信息来源: https://www.workday.com/en-au/products/contract-management/contract-lifecycle-management.html; https://www.wesuggestsoftware.com/project-management/evisort/

---

### 维度 5: 报告与导出

#### 5.1 审阅报告的生成格式

- **交互式在线仪表盘**：主要报告形式是在线交互式可视化
- **可打印仪表盘**：用户可打印仪表盘用于董事会报告（实际使用案例）
- **仪表盘导出**：支持数据导出用于外部报告
- **面向客户的门户**：可创建安全门户，向客户展示仪表盘（McKesson 案例）

**未找到 PDF 或 Word 格式的静态审阅报告生成功能的明确描述。**

信息来源: https://www.evisort.com/blog/evisort-intelligent-dashboarding-for-contracts; https://www.workday.com/en-au/customer-stories/i-p/mckesson-streamlines-clm-with-ai-insights.html

#### 5.2 报告内容的可定制性

- **拖拽式自定义仪表盘**："优雅的可视化图表和报告"
- **Advanced Search 集成**：在合同组合中精确定位特定数据
- **可保存仪表盘布局**：追踪关键数据点随时间变化
- **生成面向高管的报告**：回答高度具体的合同问题
- 可发现节省机会、未开发收入或合规差距

> 但**用户反馈指出仪表盘自定义能力有限**：预构建仪表盘虽好，但完全自定义的仪表盘体验受限。用户"希望有更多开箱即用的标准条款"。

信息来源: https://evisort-d288ab.webflow.io/blog/how-evisorts-ai-powers-pre-signature-workflows-and-custom-dashboard; 用户评论汇总

#### 5.3 导出为 Redline/修订版合同

- **支持**：Track Changes 格式的修订版合同
- 平台内红线追踪和导出
- 但与 Lexion 不同，**Evisort 不以 Microsoft Word 为中心——其文档编辑器是平台原生的**

信息来源: https://www.workday.com/en-au/products/contract-management/contract-lifecycle-management.html

#### 5.4 审计追踪的呈现

- **记录的审计追踪**：合同从初稿到执行有完整文档化的审计追踪
- **活动仪表盘**：平台包含活动追踪/活动仪表盘功能
- **REST API 审计端点**：
  - `Activities` 端点：获取实体活动
  - `Records` 端点：获取大量审计日志
  - `Users` 端点：导出当前客户的用户电子表格
- **ISO/IEC 42001 认证**：负责任 AI 的国际标准——Workday 是报告中唯一拥有此认证的合同管理解决方案

信息来源: https://docs.celigo.com/hc/en-us/articles/36725556778011-Available-Evisort-APIs; https://www.wesuggestsoftware.com/project-management/evisort/

#### 5.5 数据导出能力

- **REST API**：经 Celigo 集成文档确认，包含 Activities, Records, Users 等端点
- **数据导入/导出**：功能列表确认支持通用数据导入/导出
- **仪表盘数据导出**：支持外部报告
- **自定义仪表盘导出**：仪表盘数据可导出用于其他工具

**未找到 CSV/Excel 导出的明确 UI 确认——虽然 API 端点存在，但前端导出按钮未在公开材料中确认。**

信息来源: https://docs.celigo.com/hc/en-us/articles/36725556778011-Available-Evisort-APIs

#### 5.6 与项目管理/合同管理系统的集成报告

- **Workday 生态系统深度集成**：作为 Workday 的一部分，与财务、采购和 HR 系统无缝连接
- **ServiceNow 集成**：Evisort AI 合同提取 + ServiceNow 工作流能力
- **Salesforce/SharePoint/Box 集成**
- **可嵌入仪表盘**：仪表盘可嵌入外部系统（如面向客户的安全门户）
- **Workday Legal 作为 "Customer Zero"**：管理 100,000+ 合同，每季度节省 45,000 小时，实现 3,500% ROI

信息来源: https://www.workday.com/en-us/customer-stories/q-z/workday-legal-customer-zero-contract-intelligence.html; https://www.evisort.com/news/evisort-announces-a-new-integration-with-servicenow-legal-service-delivery-to-streamline-contract-management-with-artificial-intelligence

---

### 收购后演变: Evisort -> Workday CLM

- **2024 年 9 月**：Workday 宣布以 $311M 收购 Evisort（$44M 分配给已开发技术，$28M 分配给客户关系，$223M 分配给商誉）
- **2024 年 10 月 8 日**：交易正式完成
- **Jerry Ting** 成为 Workday 的 VP, Head of Agentic AI & Evisort
- 产品重命名为 **Workday Contract Intelligence** 和 **Workday Contract Lifecycle Management (CLM)**
- **2025 年 10 月**：Custom AI Model Library 发布——120+ 预构建 AI 模型，无需数据科学家可通过无代码界面训练和优化
- **Contract Negotiation Agent**：代理式全文档审阅和红线修订
- **ISO/IEC 42001 认证**：负责任 AI——宣称是唯一拥有此认证的合同管理解决方案
- Workday Legal 作为 "Customer Zero" 展示了从法律费用规避中实现 **3,500% ROI** 的成果

信息来源: https://fortune.com/2024/09/18/workday-acquisition-document-platform-evisort-ai-workplace/; https://www.artificiallawyer.com/2025/10/22/workday-launches-contract-ai-library/; https://www.enterprisetimes.co.uk/2025/10/24/workday-unleashes-over-120-ai-models-for-clm/

---

## 3. Lexion vs Evisort: 审阅结果呈现对比总结

| 维度 | Lexion (DocuSign IAM) | Evisort (Workday CLM) |
|---|---|---|
| **风险展示布局** | Word 修订模式 + 专利描述的并排条款对比仪表盘 + 任务卡片视图 | 并排条款列表+全文文档 + 4大智能仪表盘 + 拖拽自定义仪表盘 |
| **风险分级** | 二元合规/不合规（基于 Playbook）+ 工作流颜色状态（绿/黄/红） | 绿色勾号/感叹号图标 + Playbook 异常标记；无明确三级风险分级 |
| **风险分类** | 按 Playbook 规则组织；预装 5 个行业标准 Playbook | 230+ 预训练条款类型 + 120+ 自定义 AI 模型类别 + 虚拟 Playbook |
| **原文定位** | Word 内直接标记 + 仪表盘并排对比 | 条款列表点击跳转到原文 + 全文查看器滚动定位 |
| **并排视图** | 专利描述的条款对比视图 + 文档版本对比 | 核心 UX 模式：条款列表+全文、原文+提取字段、变更+评论 |
| **AI 理由说明** | 未找到公开信息（关键缺失） | 支持：每条建议附带清晰理由和 Playbook 对齐说明 |
| **置信度评分** | 未找到公开信息 | 未找到公开信息（AI 编排在后台运行但对用户不可见） |
| **修改建议** | Word Track Changes + Modify/Add/Ask 四大功能 | Precision Redlines（最小必要修改）+ 内外部评论分离 |
| **版本对比** | 文档比较 + 分支追踪 + 签署版本记录 | 异常优先对比 + 跨文档条款级比较 |
| **仪表盘能力** | KPI 报告（基础图表）; G2 反馈称"有限" | 4大自填充仪表盘 + 拖拽自定义；行业标杆但完全自定义受限 |
| **审计追踪** | SOC 2 Type II + ISO 27001; 被评"基础" | ISO/IEC 42001 + REST API 审计端点 |
| **报告导出** | 下载/分享 KPI 报告；Word/PDF 导出 | 交互式仪表盘 + API + 可嵌入门户；静态报告格式未明确 |
| **集成生态** | Salesforce + Adobe Sign + Microsoft 365 + Box/Dropbox | Workday 全栈（财务/HR/采购）+ ServiceNow + Salesforce |
| **关键 UX 问题** | 缺乏 AI 理由说明；报告功能基础；无颗粒化风险分级 | 功能可发现性差；学习曲线陡峭；仪表盘自定义受限；AI 不跨关联文档 |
| **收购后状态** | 已整合为 DocuSign IAM 的 Contract Intelligence 层 | 已重命名为 Workday CLM，成为 Workday agentic AI 战略核心支柱 |

---

## 附录: 研究方法与信息来源

### 搜索策略
每个竞品执行了 6 组以上的关键词搜索（中英文），覆盖产品 UI、仪表盘、分析可视化、审阅流程、报告导出等维度。

### 主要信息来源
**Lexion:**
- lexion.ai 官网产品页 (AI Contract Assist, Workflow, Repository)
- 博客文章 (Version Control, Dashboard, Redlining Best Practices)
- US Patent US20200026916A1 ("Document term extraction and comparison")
- G2, Capterra, TrustRadius 用户评测
- SpotDraft 竞品对比页面
- DocuSign 官方博客 (2025 Release 1)
- Wedbush 投资者分析报告
- SaaSworthy, SoftwareSuggest, ToolCentral 功能列表

**Evisort:**
- evisort.com 官网产品页和博客 (Intelligent Dashboarding, Document X-Ray, Automation Hub, Pre-Signature Workflows)
- workday.com 产品页和客户案例 (McKesson, Northern Inyo Healthcare, Workday Legal Customer Zero)
- blog.workday.com (Agentic Contract Review and Redlining)
- Artificial Lawyer 产品演示报道 (2022, 2025)
- diginomica.com Workday Rising 25 展会报道
- Fortune, TechCentral 收购报道
- G2, Capterra, Software Advice, Gartner Peer Insights 用户评测
- Forrester Wave 2023 CLM 报告
- Celigo API 集成文档
- Legal Reader, SalesTechStar, CIOReview 产品评测
- RFP.wiki, ToolWorthy 对比评测
