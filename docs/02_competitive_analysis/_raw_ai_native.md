# AI-Native Tier: 审核结果呈现原始调研数据

> 调研日期：2026-07-29
> 调研范围：Harvey、Robin AI、Spellbook 三个 AI-Native 竞品的审核结果呈现方式

---

## 1. Harvey

**产品概述**：Harvey 是基于 GPT-4（及多模型编排）的通用型法律 AI 平台，最初以对话式助手起步，2024-2025 年逐步演化为覆盖合同起草、审阅、尽职调查、法律研究的统一平台。定价约 $1,000–$1,200/律师/月。核心界面包括 Web 平台（Assistant + Vault + Review Tables）、Microsoft Word Add-In、Command Center（分析仪表盘）。

**关键信息来源**：
- https://www.harvey.ai/blog/a-more-unified-harvey-experience (统一界面)
- https://www.harvey.ai/blog/improved-word-experience (Word Add-In 改进)
- https://www.harvey.ai/blog/collaborative-review-tables (协作 Review Tables)
- https://www.harvey.ai/blog/rebuilding-harveys-review-algorithm (Review 算法重建)
- https://www.harvey.ai/blog/harvey-in-practice-build-and-run-playbooks-in-word (Word 中 Playbook)
- https://www.harvey.ai/blog/from-intake-to-deliverable-with-harvey (端到端工作流)
- https://www.harvey.ai/blog/the-brief-june-2025, the-brief-november-2025 (产品更新)
- https://www.harvey.ai/blog/create-and-edit-files-in-harvey (文件创建与编辑)
- https://www.harvey.ai/blog/scaling-ai-evaluation-through-expertise (评估方法论)
- https://growlaw.co/blog/harvey-ai-review (第三方评测)

---

### 维度 1: 风险项的展示

#### 1.1 风险条款的呈现布局

Harvey 的风险条款呈现采用**多层次布局**，根据使用场景不同而不同：

**A. Review Tables（表格视图，Web 端主导）**
- 以**结构化网格/电子表格**形式呈现审阅结果。每行代表一份合同或一个条款，每列代表一个审阅维度（如"管辖法律""转让条款""终止权利"等）。
- 表格支持**自然语言创建列**：用户输入"change-of-control provisions"，Harvey 的 Improve Prompt 功能自动将模糊的自然语言改写为精确的提取指令。
- 每个单元格展示两部分内容：**Answer（答案摘要）+ Reasoning（推理过程）**。用户可展开单元格查看完整的分析推理链。
- 支持**条件列（Conditional Columns）**：一列的提取结果可触发下一列的逻辑（例如：先提取管辖法律 -> 再触发该管辖区特定的检查）。

**B. Playbook Review（Word Add-In 内，内联呈现）**
- 在 Microsoft Word 文档内直接运行 Playbook 审阅。
- 对每条条款进行**逐条分析**，结果以 Word 原生评论（comments）和 Track Changes 红线的形式呈现。
- 可过滤仅查看已被红线标记的文本（"filter to review only redlined text"）。
- 用户可查看每项 Playbook 规则对应的评论，解释该条款为何被标记。

**C. Assistant 对话界面（聊天式呈现）**
- 在统一对话线程中，用户可以边起草边提问（如"我的语言中是否有模糊之处？"），审阅结果以对话回复的形式呈现。

**信息来源**：Harvey Unified Experience blog, Collaborative Review Tables blog, Harvey In Practice blog

#### 1.2 风险分级的视觉呈现方式

Harvey 使用**三级颜色编码系统**：

| 等级 | 标签 | 含义 |
|------|------|------|
| Acceptable | 绿色 / 可接受 | 条款符合 Playbook 标准 |
| Needs Review | 黄色 / 需审查 | 条款处于灰色地带，需要人工判断 |
| Unacceptable | 红色 / 不可接受 | 条款违反 Playbook 标准 |

在 Review Tables 中，团队协作使用时还引入了**多色标记系统**：
- **红色标记** = 交易破坏项（deal-breakers）
- **橙色标记** = 谈判要点（negotiation points）
- **黄色标记** = 标准条款（standard terms）

这些标记与人工评论、验证状态共同构成"数据集中风险的视觉地图（visual map of risk across the dataset）"。

**信息来源**：Harvey In Practice blog, Collaborative Review Tables blog, Icertis Playbook Review 页面

#### 1.3 风险分类的组织方式

风险通过以下层次组织：
- **按合同条款类型分类**：即 Playbook 中定义的具体规则类别（如赔偿条款、责任上限、终止条款等）。每个 Playbook 规则可定义适用的条款类型。
- **按审阅工作流定义**：Admins 可创建自定义 Vault Review 工作流（Custom Vault Review Workflows），将特定的审阅类别发布为可复用模板。
- **Review Table 列即分类**：每列代表一个特定的审阅/尽职调查维度，列可编辑、可链式关联。
- **未找到公开的风险大类分类法**（如"财务风险""合规风险""运营风险"这样的高层分类）。Harvey 的风险分类更倾向于条款级别（如"赔偿条款风险""转让条款风险"），而非企业风险管理框架下的高阶分类。

**信息来源**：Harvey Vault Review Workflows, Review Tables documentation

#### 1.4 风险摘要仪表盘/概览页

**A. Review Table 状态面板（Status Panel）**
- 可通过侧边滑出面板查看审阅进度：已分配/已验证/已标记的计数。
- 三种新过滤器：(un)verified, (un)flagged, (un)assigned。

**B. Command Center（领导者仪表盘）**
- 面向创新团队和法律运营团队的专用分析控制台。
- 提供**采用率数据（adoption data）和行业对标（peer benchmarks）**。
- 包含**对话式 Command Center Agent**，可回答关于数据的问题并生成自定义报告。
- **智能产品推荐**：建议应为哪些用户启用哪些功能。
- 可见性覆盖：采用趋势、高价值用例、利用率不足的群体、培训需求、策略合规性。

**C. 统一首页（Unified Homepage）**
- 个性化建议（基于用户工作模式）
- 快速访问常用知识源
- 上下文相关的工作流推荐
- 非传统意义上的"风险仪表盘"，而是"智能工作起点"

**信息来源**：Harvey Unified Experience blog, Command Center page, The Brief July 2025

#### 1.5 风险项的排序和筛选能力

- **Review Tables**：支持按列过滤、排序；支持三种标记过滤器（已验证/未验证、已标记/未标记、已分配/未分配）。用户可通过自然语言查询表格（如"summarize all red-flagged tenant obligations"）。
- **Workflow Builder** 中的助理工作流：用户可按主题（topic）或重要性（materiality）过滤红线摘要。
- **Playbook Review（Word Add-In）**：支持过滤仅查看被红线标记的文本，支持按条款逐条审查或批量查看。
- **Admin 管理**：可按职称、执业领域、语言过滤用户配置。

**信息来源**：Collaborative Review Tables blog, The Brief June 2025

#### 1.6 风险趋势分析

- **Playbook 版本历史（Version History）**：可查看 Playbook 的版本历史，包括谁最后编辑以及做了哪些更改。这提供了**规则层面**（而非合同层面）的变更追踪。
- **Command Center 提供采用趋势分析**：并非合同风险趋势，而是 AI 使用趋势的监控。
- **未找到合同多次版本间的风险变化趋势分析功能**。Harvey 更侧重于单次审阅的效率和质量，而非跨版本的风险趋势追踪。

**信息来源**：Harvey In Practice blog, Command Center page
**标注**：维度 1.6 "风险趋势分析（同一合同多次版本的风险变化）"——未找到明确的公开信息。

---

### 维度 2: 原文定位与导航

#### 2.1 点击风险标记后如何定位到合同原文

**A. Review Tables 中**
- 每个提取结果包含**句子级引用（sentence-level citations）**，可链接回源文档的精确句子位置。
- 点击引用后导航到 Vault 中存储的原始文档对应位置。
- 推理（Reasoning）字段中的每个要点都**脚注到源文档的具体行**。

**B. Word Add-In Playbook Review 中**
- 标注的条款在 Word 文档中被**高亮显示**，Harvey 通过 Word 原生评论系统留下解释性评论。
- 用户可在文档内逐条点击查看条款详情和推理。

**C. Redlines 工作流中**
- 自动生成引用和参考文献，简化分析流程。

**信息来源**：Rebuilding Harvey's Review Algorithm blog, Harvey In Practice blog

#### 2.2 原文高亮方式

- **Word Add-In**：使用 Word 原生的评论（comment bubbles）标注每条规则关联的条款。被 Playbook 审阅过的条款会被**高亮标记**。
- **Review Tables**：不直接在原文中高亮，而是通过引用链接回原文。引用精确到句子级别。
- **Redlines Recognition**：Vault 能识别 Word 文件的 Track Changes 和评论气泡，以及 PDF 的红/蓝标记。

**信息来源**：The Brief November 2025, Low Latency Redline Detection blog

#### 2.3 并排视图

- **未找到明确的"左原文右分析"并排视图**描述。
- Harvey 的 Review Tables 采用**表格视图**，每列是分析维度，引用链接将用户导航回原文单独查看——但这不是严格意义上的并排视图。
- Word Add-In 中的审阅是**内联模式**（分析和原文在同一个 Word 窗口内，通过评论/高亮关联）。
- **Vault Redlines 工作流**：可生成 Issues List 表格，但未描述并排对比视图。

**信息来源**：综合多个 Harvey 产品页面
**标注**：维度 2.3 "并排视图"——未找到明确的并排视图功能描述。

#### 2.4 条款间跳转

- **Review Definitions 工作流**（2025年12月推出）：专门识别定义不一致或缺失的已定义术语——这意味着存在从术语使用处跳转到定义处的功能。
- **条件链式列（Conditional Columns）**：Review Table 中一列的逻辑可关联到另一列（如"是否有转让条款" -> "提取同意要求"），这是逻辑层面的关联，而非合同原文中的超链接跳转。
- **未找到从定义跳转到引用处的明确导航功能描述。**

**信息来源**：The Brief November 2025
**标注**：维度 2.4 "条款间跳转"——部分支持（定义审阅），但未找到通用条款间导航的描述。

#### 2.5 文档内搜索与导航能力

- **Vault** 支持在大量文档中进行自然语言搜索和语义搜索（基于 Harvey 定制的 voyage-law-2-harvey 嵌入模型，200万亿法律 token 训练，16K 上下文窗口）。
- **Assistant** 支持跨 Vault 中的知识源进行检索。
- **Workflow Builder** 中的过滤功能：按主题或重要性过滤。
- **未找到 Word Add-In 内的文档搜索功能描述**（Harvey 主要依赖 AI 问答而非传统关键词搜索）。

**信息来源**：Scaling AI Evaluation blog, Harvey product pages

#### 2.6 多文档关联导航

- **Vault** 是核心多文档管理工具：安全存储、组织和批量分析法律文件，最多支持 1,000+ 文档。
- **Review Tables** 跨合同提取数据：每行代表不同的合同，每列是统一的提取维度。用户可以跨整个数据集进行自然语言查询。
- **Shared Spaces**：跨组织协作审阅（律所 + 客户），但侧重于权限和共享，而非文档间互联导航。
- **未找到明确的主合同<->修订协议<->附件的关联导航功能描述。**

**信息来源**：Harvey Unified Experience, Vault product page
**标注**：维度 2.6 "多文档关联导航"——支持跨文档数据提取和查询，但未找到主合同与附件/修订协议之间的结构化关联导航。

---

### 维度 3: 中间解释性数据展示

#### 3.1 AI 判定风险的理由/依据呈现

这是 Harvey 2025-2026 年最重大的产品改进之一。Review Tables 的**重建算法**引入了：

- **Answer + Reasoning 双字段结构**：每个结果包含简洁答案和完整推理过程。推理字段描述"文档说了什么、Harvey 如何解读、以及为什么得出该结论"。
- **逐步逻辑展示**：用户可查看模型的完整分析思路。
- **无结果时的解释**：当 Harvey 返回"—"（未找到相关信息）时，Reasoning 会解释**在文档的哪些位置搜索过**以及为什么没找到——而非仅显示空白。
- **Playbook Review 中的解释**：每条被标记的条款都附带评论，解释该条款关联的 Playbook 规则。

**信息来源**：Rebuilding Harvey's Review Algorithm blog

#### 3.2 Playbook 标准与实际条款的对比

- **Playbook Review（Word Add-In）**：Harvey 可直接在 Word 文档内应用 Playbook 生成的红线修改，使用户看到"实际条款"与"标准条款"的差异——通过 Track Changes 红线呈现。
- **Review Tables 的列对照**：用户可创建列来提取实际条款内容，与 Playbook 规则进行间接对比。但这不是明确的 diff 视图。
- **未找到专用的两栏对比（左：标准条款，右：实际条款）视图。**

**信息来源**：Harvey In Practice blog
**标注**：维度 3.2 "Playbook 标准与实际条款对比"——通过红线隐式呈现，但未找到专用 diff 视图。

#### 3.3 相关法规原文引用

- **80+ 区域特定知识源（Knowledge Sources）**：Harvey 集成了 80 多个地区特定的法律知识源作为起草和编辑的基础上下文。
- **LexisNexis Shepard's Citations 集成**：提供实时法律有效性指示器——红色（已推翻）、黄色（可能负面处理）、绿色（仍然有效）——嵌入在界面中。
- **Citation-Backed Outputs**：生成文件时，提供引用支持的解释，可追溯任何输出到源文档。
- **未找到法规原文的直接引用展示**（如显示具体的法律条文文本）。Harvey 的引用更侧重于案例法和合同源文档。

**信息来源**：Scaling AI Evaluation blog, Improved Word Experience blog

#### 3.4 置信度/风险评分的可视化

- **BigLaw Bench 评分系统**：Harvey 使用内部评估系统对输出进行打分，但这不是面向终端用户的功能，而是内部质量控制。
- **内部自动评估产生两项输出**：Grade（质量等级）+ Confidence Score（置信度分数）。这用于产品监控而非用户界面。
- **计划中的功能**："confidence-based scoring to prioritize review"（基于置信度的评分以优先审阅）——在 Rebuilding Harvey's Review Algorithm 博客中列为未来计划。
- **Playbook 的三级分类**（Acceptable / Needs Review / Unacceptable）是目前面向用户的最接近"风险评分"的呈现方式。

**信息来源**：Rebuilding Harvey's Review Algorithm blog, Scaling AI Evaluation blog
**标注**：维度 3.4 "置信度可视化"——面向终端用户的置信度评分尚在路线图中，当前用户看到的是三分类 Playbook 判定。

#### 3.5 历史相似条款的审阅决策参考

- **未找到明确的历史相似条款审阅决策参考功能**。
- Harvey 的 Knowledge 功能可检索内部先例和模板，但这是在审阅前的参考，而非在审阅结果中主动推荐"类似条款的历史决策"。
- Playbook 版本历史可追踪规则的演变，但不追踪具体条款的历史审阅决策。

**信息来源**：综合多个 Harvey 产品页面
**标注**：维度 3.5 "历史相似条款审阅决策参考"——未找到公开信息。

#### 3.6 数据来源可追溯性

这是 Harvey 最突出的优势之一。**三层验证架构**：

- **Layer 1 — 精准引用引擎**：提取结构化元数据（标题、章节、条款号），使用 voyage-law-2-harvey 定制嵌入模型进行语义搜索，LLM 执行二元文档匹配确认，准确率 >95%。
- **Layer 2 — 实时 Shepardization**：通过 LexisNexis API 自动验证每个引用案例。
- **Layer 3 — 内部幻觉检测（Claim Decomposition）**：将生成的答案分解为原子事实声明，逐一交叉参考源文档，标记不支持的声明。内部幻觉率降至约 0.2%。

**用户体验层面的可追溯性**：
- 句子级引用（Sentence-level citations）替代了旧的单元格级引用
- 每个推理要点的脚注精确到源文档行
- Citation-Backed 导出
- 完整的审计日志：保留提示词、来源和输出
- SSO + 基于角色的权限 + 数据驻留选项

**信息来源**：Scaling AI Evaluation blog, Rebuilding Harvey's Review Algorithm blog

---

### 维度 4: 修改建议与协作

#### 4.1 修改建议的呈现形式

**A. Word Add-In（内联修订 + 评论）**
- AI 生成的修改以**Word 原生 Track Changes（红线）**形式直接呈现在文档中。
- 建议的措辞以**评论（comment bubbles）**形式显示，解释每条规则对应的修改理由。
- 支持 Required Language Flags（强制语言标记）内联显示。

**B. 平台内 Word 编辑器（In-Platform Word Editing）**
- Harvey 平台内置了 Word 编辑能力，用户可在平台内审阅 Track Changes 和红线。
- 自动红线对照（automatic redlining against original）：在上传原始文档后，任何修订自动生成红线。

**C. Review Tables**
- 以表格形式呈现修改建议的摘要，而非内联修订。

**信息来源**：Improved Word Experience blog, From Intake to Deliverable blog

#### 4.2 一键接受/拒绝修改

- **Word Add-In Playbook Review**：支持一键应用 Harvey 生成的红线修改（"apply Harvey-generated redlines with one click"）。可以逐条接受或批量应用所有修改。
- **拒绝与回退**：用户可以拒绝红线并回退到原始文本。
- **Redact 工作流**：一键扫描并删除敏感信息（如 PII）。

**信息来源**：Harvey In Practice blog, The Brief November 2025

#### 4.3 手动编辑 AI 建议

- **Review Tables**：支持**行内单元格编辑（in-line cell editing）**——无需打开单独模态窗口即可直接修正任何单元格内容。
- **条件列覆盖（Override Columns）**：Review Table 生成后，用户可编辑/添加列来自定义分析。
- **平台内 Word 编辑器**：支持完整格式化、手动文本编辑、从空白文档开始。
- **Playbook Review 中的编辑**：用户可查看和修改建议的措辞——在 Word 中直接编辑。

**信息来源**：Collaborative Review Tables blog, From Intake to Deliverable blog

#### 4.4 多人协作审阅的批注与讨论

- **Shared Spaces**：跨组织（律所 + 客户 + 对手方律师）的安全协作空间。可共享：Agentic 工作流、Playbooks、Vaults、草稿、Review Tables。
- **Review Tables 协作**：多色标记（红/橙/黄）+ 评论 + 手动输入列——团队成员可在表格内直接标注、解释标记原因、与同事解决问题。
- **Harvey 可读取 Word 评论**：在文档分析中理解内联注释和被追踪的对话。
- **单元级分配**：支持单元格级别的分配（assignment）、标记（flagging）和验证（verification）。
- **Workspace 级别的权限管理**：Admins 可将 Review 工作流发布给特定用户或整个 workspace。
- **未找到实时共同编辑功能**（如 Google Docs 风格的多人同时编辑同一文档）。

**信息来源**：Shared Spaces video page, Collaborative Review Tables blog

#### 4.5 版本对比

- **Playbook 版本历史**：查看谁最后编辑了 Playbook 以及做了哪些更改。
- **自动红线对照**：在上传原始文档后，Harvey 在平台内自动对新版本进行红线对照。
- **Vault Redlines Recognition**：自动检测 Word 的 Track Changes 和 PDF 的红/蓝标记。
- **未找到明确的多版本并排对比功能**（如"原合同 vs AI 修改版 vs 最终版"的三栏对比）。

**信息来源**：Harvey In Practice blog, From Intake to Deliverable blog
**标注**：维度 4.5 "版本对比"——支持基于 Track Changes 的隐式对比，但未找到专用多版本并排对比界面。

---

### 维度 5: 报告与导出

#### 5.1 审阅报告的生成格式

Harvey 支持**多格式导出**：
- **Word (.docx)**：客户就绪的格式化 Word 文档，保留原始格式
- **Excel (.xlsx)**：Review Tables 可导出为 Excel，支持保留标记颜色（绿色=已验证，红色=已标记）
- **PowerPoint (.pptx)**：可从研究直接生成幻灯片
- **CSV**：数据导出
- **PDF**：Playbook 审阅结果可下载为格式化 PDF

**信息来源**：Create and Edit Files blog, The Brief September 2025

#### 5.2 报告内容的可定制性

- **自定义格式模板**：Admins 可上传自定义格式模板（边距、字体、页眉、表格、编号），确保所有导出符合组织标准。
- **模板驱动的自动化**：上传尽职调查请求列表模板 -> Harvey 自动翻译为表格列。
- **自然语言查询**：可在 Review Tables 中通过自然语言生成摘要和综合报告。
- **Workflow Builder**：可创建自定义自动化工作流来定制分析报告的结构和内容。

**信息来源**：Create and Edit Files blog, From Intake to Deliverable blog

#### 5.3 导出为 Redline/修订版合同

- **Word Add-In**：Playbook Review 生成的修改以 Track Changes 形式直接存在于 Word 文档中，天然可保存为红线版。
- **平台内编辑器**：从平台导出时，红线已包含在 .docx 中。
- **Draft from Template 工作流**：修改以 tracked edits 形式导出。

**信息来源**：Improved Word Experience blog

#### 5.4 审计追踪的呈现

- **完整的审计日志**：保留提示词、来源和输出，用于合规。
- **引用可追溯性**：所有输出均可追溯到源段落，审核者可在导出前验证。
- **Admin 控制**：SSO、基于角色的权限、数据驻留选项、全面审计日志记录。
- **Playbook 版本历史**显示编辑人和更改内容。
- **未找到面向终端用户的审计追踪可视化界面描述**（如时间线视图或活动日志仪表盘）。

**信息来源**：Harvey security and compliance pages, Scaling AI Evaluation blog
**标注**：维度 5.4 "审计追踪"——后端功能齐全，但未找到面向用户的审计追踪 UI 描述。

#### 5.5 数据导出能力

- **API**：未找到 Harvey 的公开 API 文档（与 Robin AI 不同，Harvey 似乎未提供开放的 REST API）。
- **CSV / Excel 导出**：支持。
- **结构化数据格式**：支持（通过 Review Tables 导出）。
- **批量文件创建**：可在单一线程中同时编辑多个相关文档（PowerPoint + Excel + Word）。

**信息来源**：Create and Edit Files blog
**标注**：维度 5.5 "API 导出"——未找到公开 API 信息。

#### 5.6 与项目管理/合同管理系统的集成报告

- **Ecosystem**：Harvey 设有 Ecosystem 页面，列出与现有工具的集成，包括 Microsoft 365 Copilot、LexisNexis、SharePoint（单向同步）。
- **SharePoint 单向同步**：将内部文档同步到 Harvey Knowledge base。
- **未找到与 CLM（如 Ironclad、ContractPodAi）或项目管理系统的具体集成报告功能描述。**

**信息来源**：Harvey Ecosystem page, The Brief updates
**标注**：维度 5.6 "集成报告"——与 Microsoft 生态深度集成，但未找到与第三方 CLM/项目管理系统的集成报告。

---

## 2. Robin AI

**产品概述**：Robin AI 是伦敦总部的法律智能平台（2019年创立），定位为"AI Lawyer"和法律智能平台。使用 Anthropic Claude 模型。定价约 $2,000–$5,000/座/年。**注意：Robin AI 于 2025 年末在未能完成 $50M 融资轮后倒闭，其托管服务部门被 Scissero 收购（2025年12月），工程团队被 Microsoft 收购（2026年1月）。以下分析基于其倒闭前的产品功能。**

**关键信息来源**：
- https://robinai.com/news-and-resources/robin-university/tables-turn-contracts-into-structured-insights (Tables 功能)
- https://robinai.com/news-and-resources/blog/answer-types-now-available-in-robin-ai-reports (Answer Types)
- https://robinai.com/news-and-resources/news/fresh-designs-in-robins-platform-deliver-end-to-end-workflow-experience (平台设计)
- https://robinai.com/help/review-documents-with-playbook (Review with Playbook)
- https://robinai.com/news-and-resources/robin-university/chat-get-instant-verifiable-legal-analysis (Chat 功能)
- https://robinai.com/news-and-resources/blog/obligations-management (义务管理)
- https://robinai.com/news-and-resources/robin-university/legal-intelligence-platform-an-ai-powered-hub-for-all-your-legal-data (平台概览)
- https://robinai.com/news-and-resources/blog/introducing-robins-tables-api-unlock-structured-data-from-legal-documents (Tables API)
- https://gotranscript.com/public/enhance-contract-review-with-robin-ai-free-tools-for-lawyers (演示文字记录)
- https://www.g2.com/sellers/robin-3c61c2bb-d26c-40e8-8eb9-c83c6adc0c7b (G2 评测)

---

### 维度 1: 风险项的展示

#### 1.1 风险条款的呈现布局

Robin AI 采用**多界面并行**的呈现策略：

**A. Tables（电子表格视图，核心呈现方式）**
- 以**可定制的电子表格/网格**形式呈现结构化审阅结果。行 = 单个合同，列 = 定义的审阅问题/提示词（按章节分组：如 Indemnities、Renewal Clauses、Payment Terms）。
- 用户通过 Prompt Names 定义列，每个 Prompt 有独立的**Answer Format**（答案格式）设置。
- 文档名称列可**冻结**，在横向滚动大表格时保持可见。
- 支持**预览模式**（Preview）：在运行完整表格前测试答案格式。
- 若 AI 无法定位答案，单元格显示**"N/A"**。

**B. Chat 界面（对话式呈现）**
- 通过自然语言对话获取合同分析结果，支持多轮追问。
- 回复可按用户要求的格式输出（列表、邮件草稿、对比表格、条款引用等）。

**C. Word Add-In（内联呈现）**
- AI 建议以 Track Changes 形式在 Word 文档内呈现。
- Review with Playbook 的结果是**可下载的 .docx 红线文件**。

**D. Workspaces Dashboard（动态时间线）**
- 显示最近的 Tables 和 Conversations 的动态时间线，带有快速访问模板。

**信息来源**：Tables documentation, Fresh Designs blog

#### 1.2 风险分级的视觉呈现方式

- Robin AI 的风险分级主要通过 **Playbook 规则定义**：标准位置（接受）、备选位置（修订/替代）、底线触发（拒绝/升级）。
- 在 Obligation Management 仪表盘中，义务按**优先级（priority）和状态（status）**组织。
- PowerBI 集成允许用户在 BI 仪表盘中可视化合同组合的风险。
- **未找到 Harvey 式的明确三色分类系统或风险评分 UI。**

**信息来源**：Obligations Management blog, Review with Playbook help
**标注**：维度 1.2 "风险分级的视觉呈现"——风险分级更倾向于通过 Playbook 规则和 BI 工具间接实现，而非产品内置的端到端风险评分 UI。

#### 1.3 风险分类的组织方式

- **按审阅模板分类**：预建模板（Due Diligence、MSA Risk Review、Compliance Audits 等）提供预设的分类结构。
- **按 Answer Types 结构化**：Yes/No（是否存在风险）、Select/Multi-Select（风险类型分类）、Text Summary（风险描述）。
- **按合同条款类型分组**：Prompt Names 作为章节（Indemnities, Payment Terms, Termination Rights 等）。
- **未找到预设的风险分类法**（如"财务风险""合规风险"等企业风险管理框架分类）。

**信息来源**：Tables documentation, Answer Types blog

#### 1.4 风险摘要仪表盘/概览页

- **Workspaces Dashboard**：作为操作枢纽，显示动态时间线、快速访问模板、核心功能入口。但这不是专门的风险仪表盘。
- **Obligation Management Dashboard**：提供组织所有合同义务的统一视图，按优先级和状态组织。包含详细视图（链接到源条款）、可导出审计追踪、升级工作流、可操作清单。
- **PowerBI 集成**：先进的合同风险和趋势监控分析仪表盘——但这是通过外部 BI 工具实现的，而非产品内置。

**信息来源**：Obligations Management blog, Fresh Designs blog

#### 1.5 风险项的排序和筛选能力

- **Tables**：结果可搜索、排序、过滤。文档名称列可冻结。列支持 Answer Types 格式化输出，使排序和筛选更精确。
- **Workspaces 搜索**：跨所有文档的关键词搜索 + 按合同类型过滤（如"Vendor Agreements"）。
- **Chat**：文档筛选使用多属性面板式选择系统（Document Type、Permission Groups、Document Properties、Keyword）。
- **未找到按风险等级的排序/筛选功能。**

**信息来源**：Tables documentation, Chat documentation

#### 1.6 风险趋势分析

- **Compare Versions（版本对比）**：可对比任意两个版本的合同，变更以红线标示。但这是"版本对比"而非"风险趋势分析"。
- **PowerBI 集成**允许跨时间维度的风险趋势分析——但这是在外部 BI 工具中实现的。
- **Obligation Management** 提供截止日期和合同承诺的监控，但不具体追踪"同一合同多次版本的风险变化"。
- **未找到产品内置的风险趋势分析功能。**

**信息来源**：Contract Review Process blog, Obligations Management blog
**标注**：维度 1.6 "风险趋势分析"——通过 BI 集成间接支持，产品内置功能未找到。

---

### 维度 2: 原文定位与导航

#### 2.1 点击风险标记后如何定位到合同原文

- **Tables 中的可点击引用（Clickable Citations）**：每个提取的答案包含可点击引用，**直接链接到原始合同中的相关条款**。这是 Robin AI 最突出的 UX 特性之一。
- **Chat 中的引用**：每条回复都带有可点击引用，跳转到原始文档条款。系统设计强调"Always verify with the source"。
- **Obligation Management**：详细视图将每条义务链接到其源合同条款。

**信息来源**：Tables documentation, Chat documentation

#### 2.2 原文高亮方式

- **Tables 中**：点击引用后跳转到源文档，具体高亮方式未详述。
- **Review with Playbook**：输出为 .docx 文件，使用 Word Track Changes 高亮修改。
- **未找到 Table 内的原文高亮机制描述**（如颜色标记、下划线等）。

**信息来源**：Tables documentation, Review with Playbook help
**标注**：维度 2.2 "原文高亮方式"——引用导航机制强大，但具体高亮样式信息不足。

#### 2.3 并排视图

- **未找到明确的"左侧合同原文、右侧风险分析"并排视图描述**。
- Tables 的引用机制提供了一种验证流程：点击引用 -> 跳转到原文 -> 回到表格。这是跳转式而非并排式。
- Word Add-In 的审阅是内联模式（在 Word 内显示 Track Changes）。
- **Compare Versions** 提供版本间的并排对比，但这是版本比较而非风险分析并排视图。

**信息来源**：综合多个 Robin AI 页面
**标注**：维度 2.3 "并排视图"——未找到专用的分析-原文并排视图。

#### 2.4 条款间跳转

- **Copilot（AI 助手）**：可提供定义和管辖区指导，建议更清晰的定义——但未描述从引用处跳转到定义处的功能。
- **未找到条款间交叉引用导航功能。**

**信息来源**：综合多个 Robin AI 页面
**标注**：维度 2.4 "条款间跳转"——未找到公开信息。

#### 2.5 文档内搜索与导航能力

- **Workspaces 搜索**：跨所有文档的关键词搜索 + 按合同类型过滤 + 多属性过滤器。
- **Chat 文档选择器**：支持按 Document Type、Permission Groups、Document Properties、Keyword 搜索。
- **Legal Library**：智能、可搜索的文档仓库。

**信息来源**：Chat documentation, Legal Intelligence Platform overview

#### 2.6 多文档关联导航

- **Tables**：跨合同提取数据的核心工具，按行组织不同合同，按列组织统一维度。但不提供合同间的关联导航。
- **Chat**：可跨选定文档集合进行问答（建议限制在 2-5 个文档以获得最佳效果）。
- **Obligation Management**：从整个合同组合中提取义务，但按义务而非文档组织。
- **未找到主合同<->修订协议<->附件之间的结构化关联导航。**

**信息来源**：Tables documentation, Chat documentation
**标注**：维度 2.6 "多文档关联导航"——跨文档数据提取强，但文档间关联导航弱。

---

### 维度 3: 中间解释性数据展示

#### 3.1 AI 判定风险的理由/依据呈现

- **Tables 引用系统**：每条答案附带可点击引用，但未描述类似 Harvey 的 "Reasoning" 字段。
- **Word Add-In（根据演示文字记录）**：AI 建议附带"AI 生成的解释性评论"——类似 Grammarly 的模式。
- **Playbook 规则匹配**：当备选位置（fallback position）匹配文档条款时，显示勾号以及"解释为什么满足该位置的推理"。
- **Compared to Harvey**：Robin AI 的解释性数据呈现不如 Harvey 的 Answer + Reasoning 双字段结构详细和系统化。

**信息来源**：Review with Playbook help, 演示文字记录

#### 3.2 Playbook 标准与实际条款的对比

- **Review with Playbook**：上传 Playbook + 合同 -> 输出 .docx 红线文件，红线本身即为对比。
- **备选位置（Fallback Positions）**：Playbook 规则可定义多层备选位置，审核时显示哪个备选位置匹配（或不匹配）当前条款。
- **未找到专用的并排 diff 视图（标准 vs 实际）。**

**信息来源**：Review with Playbook help, Fallback Positions help

#### 3.3 相关法规原文引用

- **未找到法规原文引用功能**。Robin AI 的引用系统主要指向用户自己的合同文档，而非外部法律法规。
- Copilot 可提供"管辖区指导"，但未描述具体的法规引用。

**信息来源**：综合多个 Robin AI 页面
**标注**：维度 3.3 "法规原文引用"——未找到公开信息。

#### 3.4 置信度/风险评分的可视化

- **Answer Types 系统**：通过结构化答案格式（Yes/No、Select 等）提供确定性指示。N/A 表示无法确定答案——这是隐式的不确定性指示。
- **未找到显式的置信度评分/风险评分可视化**。

**信息来源**：Answer Types blog
**标注**：维度 3.4 "置信度可视化"——未找到公开信息。

#### 3.5 历史相似条款的审阅决策参考

- **未找到此功能**。
- Robin AI 的 Chat 可搜索先例语言（"surfacing and ranking relevant precedent language based on usefulness"），但这更接近于搜索功能而非主动推荐。

**信息来源**：综合多个 Robin AI 页面
**标注**：维度 3.5 "历史相似条款审阅决策参考"——未找到公开信息。

#### 3.6 数据来源可追溯性

- **可点击引用**是所有界面的核心设计原则：Tables、Chat、Reports 都包含直接链接回源文档条款的引用。
- **Tables API** 返回的 JSON 包含引用数据。
- **Review 审核流程**被设计为"Verify with citations"作为独立步骤。
- **Obligation Management** 将义务链接回源条款。
- 设计理念强调**透明性和可验证性（transparency and verifiability）**。

**信息来源**：Tables documentation, Chat documentation, Fresh Designs blog

---

### 维度 4: 修改建议与协作

#### 4.1 修改建议的呈现形式

- **Review with Playbook（主要形式）**：输出为**可下载的 .docx 红线文件**。用户需在 Word 中打开文件进一步审阅和编辑。
- **Word Add-In**：AI 建议以 **Track Changes** 形式呈现在 Word 文档中。用户可直接在 Word 中接受/拒绝/修改。
- **Tables**：以表格单元格中的结构化数据呈现修改建议的摘要，非内联修订。
- **Chat**：以对话文本形式提供建议。

**信息来源**：Review with Playbook help, 演示文字记录

#### 4.2 一键接受/拒绝修改

- **Word Add-In**：根据演示文字记录，"click a suggestion and the edit auto-applies"——点击建议即自动应用修改。但未描述明确的一键接受/拒绝按钮。
- **Review with Playbook 工作流**：输出红线文件后，用户在 Word 中手动接受/拒绝 Track Changes。
- **Playbook 规则**：规则本身定义了接受/修订/拒绝的逻辑，但在用户界面中体现为备选位置的匹配状态。

**信息来源**：演示文字记录, Review with Playbook help

#### 4.3 手动编辑 AI 建议

- **Word Add-In**：用户可在 Word 中直接编辑 AI 建议的措辞。
- **Tables**：答案格式为结构化输出（Yes/No、Date、Currency 等），Table 本身是数据提取而非编辑工具。
- **Clean Version toggle**：可切换去除标记以查看不含红线的最终合同。

**信息来源**：演示文字记录

#### 4.4 多人协作审阅的批注与讨论

- **Tables 分享**：通过"Add member"图标分享 Tables，支持查看和编辑权限。
- **Workspaces**：统一的安全中心，集中讨论、决策和文档。保持所有团队成员、对话和文档版本同步。提供结构化的审批路由。
- **Chat 对话**：可设为私有、公开或邀请协作者。
- **Playbook 协作**：Playbook 可跨团队共享（通过 Robin Library）。但 Playbook 编辑是单用户的。
- **局限性**：无实时共同编辑（如 Google Docs），无原生电子签名集成。协作侧重于审阅阶段的审批流程而非实时共同编辑。

**信息来源**：Tables documentation, Fresh Designs blog, Contract Review Process blog

#### 4.5 版本对比

- **Compare Versions**：可并排对比任意两个合同版本（如原版 vs 最新版，或 v3 vs v4）。变更以红线标示。
- **Version History**：通过"See History"功能查看完整版本历史，包括最后编辑人信息。每个修订完全可追溯。
- **AI 修改区分**：系统区分用户编辑和对手方编辑。所有 AI 建议与手动更改分层呈现。

**信息来源**：Contract Review Process blog, 对比评测

---

### 维度 5: 报告与导出

#### 5.1 审阅报告的生成格式

- **Word (.docx)**：最适合单合同审阅（单文档审阅的报告格式）。
- **Excel (.xlsx)**：最适合多文档审计和大型项目——可进一步排序、筛选和分析。
- **邮件发送**：报告生成后直接发送到用户收件箱。
- **Tables API**：返回结构化 JSON，用于编程式集成。

**信息来源**：Answer Types blog, Tables documentation

#### 5.2 报告内容的可定制性

- **自服务报告构建器（Self-Service Report Builder）**：用户可编辑模板或从头构建报告——修改问题、调整答案类型、重新组织主题（如 Payment Terms、Termination Rights、Data Protection）。
- **Answer Types**：10种答案格式（Text Summary, Text Word/Phrase, Yes/No, Date, Number, Currency, Duration, Percentage, Select, Multi-Select）让报告输出高度结构化。
- **答案预览**：实时测试单个问题以微调措辞和答案格式。
- **模板库**：预建模板（LPA summaries, MSA audits, due diligence）+ 可保存和跨团队共享自定义模板。

**信息来源**：Answer Types blog, Customizing Report Templates documentation

#### 5.3 导出为 Redline/修订版合同

- **Review with Playbook**：核心输出即为**可下载的 .docx 红线文件**（"a downloadable .docx file with redlines showing all suggested edits"）。
- Word Add-In 中的 Track Changes 可直接在原文档中保存为红线版。
- **局限性**：仅支持 .docx 文件，不支持 PDF 红线输出。仅应用第一轮 Playbook 立场，升级/备选立场不自动应用。

**信息来源**：Review with Playbook help

#### 5.4 审计追踪的呈现

- **Version History / See History**：显示谁最后编辑了合同及完整版本演变。每次修订完全可追溯。
- **Obligation Management**：可导出的审计追踪用于监管合规。
- **局限性**：与 HyperStart 的竞争对比指出 Robin AI "缺乏强大的审计追踪能力"——虽然有版本历史，但可能不够全面（如无完整的决策审计日志）。

**信息来源**：Contract Review Process blog, HyperStart comparison
**标注**：维度 5.4 "审计追踪"——有基础版本历史，但第三方评测指出审计追踪不够全面。

#### 5.5 数据导出能力

- **REST API（OpenAPI 3.1.0）**：公开 API 位于 `https://api.robinai.com`（X-API-Key 认证）。包含 Tables API（批量提取）、Documents API、Templates API、Properties API、Groups API。支持游标分页（limit 最高 1000 + starting_after）、ISO 8601 日期范围过滤。
- **Excel 导出**：Tables 和 Reports 的主要导出格式。
- **CLM/CRM/ERP 集成**：通过 API 自动填充合同元数据到企业系统。
- **PowerBI 集成**：结构化数据导出到 BI 仪表盘。

**信息来源**：Tables API blog, Robin API page

#### 5.6 与项目管理/合同管理系统的集成报告

- **CLM/CRM/ERP 系统**：通过 API 和 PowerBI 连接器实现。
- **AWS Marketplace & Microsoft AppSource**：企业部署选项。
- **Reports API 驱动**：Tables API 产生结构化 JSON -> 可馈送到任何下游系统。
- **未找到特定的项目管理/CLM 集成报告描述**。

**信息来源**：Tables API blog, Robin API page

---

## 3. Spellbook

**产品概述**：Spellbook 是多伦多团队的 AI 合同工具（2022年推出），核心特点是**深度集成在 Microsoft Word 中**（Word Add-In，支持 Windows、Mac、Web）。定价约 $99–$350/座/月（不公开定价）。2025年10月完成 $50M Series B，2026年3月成为加拿大律师协会独家 AI 合同合作伙伴。**Spellbook 的独特之处在于它本质上是一个 Word 插件，几乎所有核心功能都在 Word 内完成**，这与 Harvey 和 Robin AI 的 "Web 平台 + Word 插件" 双轨策略形成鲜明对比。

**关键信息来源**：
- https://help.spellbook.legal/en/articles/15656286-how-to-use-comprehensive-review (Comprehensive Review)
- https://help.spellbook.legal/en/articles/12002974-how-to-use-review-tables-in-associate (Review Tables)
- https://help.spellbook.legal/en/articles/16042055-how-to-use-tabular-reports (Tabular Reports)
- https://help.spellbook.legal/en/articles/11554251-how-to-integrate-playbooks-into-a-workflow (Playbooks)
- https://help.spellbook.legal/en/articles/11327960-best-practices-for-creating-your-own-playbooks (Playbook 最佳实践)
- https://help.spellbook.legal/en/articles/12398925-how-to-use-compare-to-market (Compare to Market)
- https://www.spellbook.legal/associate (Associate 产品页)
- https://www.artificiallawyer.com/2026/01/13/spellbook-rolls-out-compare-to-market-aka-contract-money-ball/ (Compare to Market 发布)
- https://lawyerist.com/reviews/artificial-intelligence-in-law-firms/spellbook-review-artificial-intelligence-for-lawyers/ (Lawyerist 评测)
- https://gc.ai/blog/spellbook-legal-ai-review (GC AI 评测)
- https://help.spellbook.legal/en/articles/10438652-how-to-use-spellbook-s-associate-an-overview (Associate 概览)
- https://spellbook.com/learn/legal-ai-agent-features (法律 AI Agent 特性)

---

### 维度 1: 风险项的展示

#### 1.1 风险条款的呈现布局

Spellbook 的呈现布局因使用场景分为**两个完全不同的界面**：

**A. Word Add-In Sidebar（核心界面，内联模式）**
- 在 Word 右侧显示一个**侧边栏面板**。
- 通过点击 **">"** 键打开扩展功能菜单，选择审阅模式。
- 三种审阅模式可选：**General Review**（广泛扫描风险）、**Negotiate Review**（偏向所代表方）、**Custom Review**（按自定义指令进行窄范围检查）。
- 审阅结果以两个**切换标签**形式呈现：**"General Risks"**和**"Proofread"**——两个独立的结果类别。
- 每个被标记的问题下方显示**推理说明**（"reasoning as to why that issue was flagged"）。
- **铅笔图标**用于编辑任何修订或评论。
- **"Show" 按钮**跳转到文档中问题所在的段落。
- **"Apply" 按钮**接受建议的修改。
- 支持三种标记深度：**Light Markup**（仅关键问题）、**Standard Markup**（平衡审阅）、**Heavy Markup**（标记所有问题，包括次要措辞问题）。

**B. Associate Web App（Web 端，多文档模式）**
- **Review Tables**：以表格形式呈现对多个文档的问答提取结果。上传文件 -> 输入问题列表 -> 点击箭头开始 -> 获得 Q&A 表格。
- **Tabular Reports**：AI 优先的表格合同报告，自动提取元数据到可编辑视图。支持最多 500 个文档。
- **Due Diligence Reporting**：专用的尽职调查报告工作流。

**信息来源**：Comprehensive Review help, Review Tables in Associate help, Tabular Reports help

#### 1.2 风险分级的视觉呈现方式

- **Playbook 规则中的 Risk Levels（风险等级）**：可在每个 Playbook 规则上添加 Risk Level 元数据字段。但具体等级划分（如高/中/低）未在帮助文档中明确说明。
- **Compare to Market（市场对标）**：以统计分布呈现——条款被分类为**above / at / below market standard**，以及**Favourable / Unfavourable**（对你方有利/不利）。
- **Benchmarks（基准检查）**：分配**Coverage Score（覆盖分数）**，基于文档对标准/要求的满足程度。标记缺失条款和空白。
- **Playbook 备选位置（Fallback Positions）**：当规则失败时，显示备选位置匹配状态（勾号标记匹配的备选位置 + 推理说明）。
- **审阅标记深度**：Light / Standard / Heavy Markup 三个层次——这是对"标记多少问题"的控制而非风险评分。

**信息来源**：Playbook help, Compare to Market help, Benchmarks blog

#### 1.3 风险分类的组织方式

- **按 Playbook 规则分类**：Playbook 由具体的规则组成（如"条款不得超过12个月""责任上限不低于$500,000"）。每条规则可独立定义风险等级。
- **按 General Risks vs Proofread 分类**：Comprehensive Review 的结果分为两大类别切换。
- **按合同条款类型分类**：Compare to Market 支持 14 种合同类型和每种合同 15-20 个交易要点。
- **Standards Library**：Spellbook 的标准库提供预定义的检查类别。
- **未找到企业风险管理框架级别的高阶分类**。

**信息来源**：Comprehensive Review help, Compare to Market help

#### 1.4 风险摘要仪表盘/概览页

- **未找到 Web 端的风险摘要仪表盘**。Spellbook 是 Word 原生工具，其设计哲学是"所有分析在 Word 内完成"，而非提供独立的仪表盘。
- **Associate 的 Tabular Reports** 可作为跨合同风险概览的一种形式——在一个视图中查看多个合同的元数据。
- **Compare to Market** 提供统计概览（术语分布），但这更像分析快照而非持续更新的仪表盘。
- **Benchmarks Coverage Score** 提供单一的"合同健康分数"。
- **未找到类似 Harvey Command Center 或 Robin AI Obligation Dashboard 的专用仪表盘。**

**信息来源**：综合多个 Spellbook 页面
**标注**：维度 1.4 "风险摘要仪表盘"——Spellbook 作为 Word 原生工具，仪表盘功能明显弱于 web 端竞品。

#### 1.5 风险项的排序和筛选能力

- **Comprehensive Review 侧边栏**：通过 General Risks / Proofread 标签切换结果类别。
- **Review Tables**：未明确描述排序/筛选功能。可通过添加问题和保存问题来组织审阅维度。
- **Tabular Reports**：通过自定义列（Custom Columns）和视图（Views）来组织数据——支持多个已保存视图。
- **Playbook Rules**：按风险等级组织（但具体的排序/筛选 UI 未描述）。
- **局限性**：与 Harvey 的 Review Tables（多色标记 + 三种过滤器 + 自然语言查询）相比，Spellbook 的排序和筛选能力明显较弱。

**信息来源**：Review Tables help, Tabular Reports help
**标注**：维度 1.5 "排序和筛选"——功能明显弱于 Harvey，缺乏高级过滤和自然语言查询表格的能力。

#### 1.6 风险趋势分析

- **Playbook 草稿/已发布版本管理**：自动保存草稿，已发布版本带有未发布更改的版本区分。但这是规则级别的版本管理，而非合同风险趋势。
- **未找到同一合同多次版本的风险变化追踪功能。**
- **未找到跨时间维度的风险趋势分析。**

**信息来源**：综合多个 Spellbook 页面
**标注**：维度 1.6 "风险趋势分析"——未找到公开信息。

---

### 维度 2: 原文定位与导航

#### 2.1 点击风险标记后如何定位到合同原文

- **Comprehensive Review 侧边栏**："Show"按钮定位到文档中问题所在段落——这是 Word Add-In 的原生优势，因为审阅和文档在同一个窗口中。
- **Compare to Market**："Show"按钮跳转到文档的相关部分。
- **Associate Review Tables**：点击单个文档可预览其内容——内联预览功能。但未描述从表格单元格跳转到原文具体段落的机制（与 Robin AI 的"可点击引用"不同）。
- **Associate Tabular Reports**：点击单个文档可在表内预览内容。

**信息来源**：Comprehensive Review help, Compare to Market help, Tabular Reports help

#### 2.2 原文高亮方式

- **Word Add-In 内**：使用 **Word 原生 Track Changes** 对建议的修改进行高亮（红线标记）。这是 Spellbook 的核心优势——所有 AI 建议直接以律师最熟悉的格式体现。
- **修改建议的呈现**：可在"Show revisions"（内联红线）和"Show comments"（仅评论）之间切换。
- **"Use tracked changes" 开关**：开启后 Spellbook 自动对修订进行红线标记。
- **Playbook Review**：对检测到的偏离自动应用"外科手术式红线"。
- **未描述颜色编码或下划线等特定的高亮样式。**

**信息来源**：Comprehensive Review help, Playbook help

#### 2.3 并排视图

- **未找到"左侧合同原文、右侧风险分析"的并排视图**。
- Word Add-In 采用侧边栏 + 主文档的布局：主文档区域显示合同和 Track Changes，右侧面板显示审阅结果列表——这是一种"并排"形式的近似实现，但并非传统的两栏原文-分析对比。
- Associate 的文档比较功能支持表格式对比——但这是文档间对比而非原文-分析并排。
- **未找到专用的原文-分析并排视图。**

**信息来源**：综合多个 Spellbook 页面
**标注**：维度 2.3 "并排视图"——Word Add-In 侧边栏模式提供了一种近似体验（文档在左主面板，分析在右侧边栏），但不是严格意义上的并排视图。

#### 2.4 条款间跳转

- **Review Definitions 类功能**：Associate 可跨文档检查定义术语的一致性——"cross-check defined terms across ancillary documents alongside a principal agreement"。但未描述从引用处跳转到定义处的交互。
- **未找到通用的条款间交叉引用导航功能。**

**信息来源**：Associate overview, Legal AI Agent Features
**标注**：维度 2.4 "条款间跳转"——未找到明确的导航功能描述。

#### 2.5 文档内搜索与导航能力

- **Word 的原生搜索功能**：作为 Word Add-In，Spellbook 天然可利用 Word 自带的搜索/导航。
- **Ask（文档问答）**：通过侧边栏的聊天式界面询问关于合同内容的问题，附带对特定条款的引用。可消除手动搜寻长文档的需求。
- **Associate 中的文档管理**：支持 OneDrive、SharePoint、Dropbox、iManage、Google Drive 云集成和直接上传。
- **未找到 Spellbook 特有的文档内搜索功能**。

**信息来源**：Ask help, Associate help, Tabular Reports help

#### 2.6 多文档关联导航

- **Associate（核心多文档工具）**：独立的 Web 应用程序，可处理多个文件并发现跨文档关联。
- **多文档 Q&A**：上传多个文档 -> 提问 -> Associate 审阅所有上传文档并提供答案。
- **文档对比**：上传多个文档 -> 提示 Associate 以表格格式对比差异。
- **跨文档定义检查**：检查辅助文档与主协议之间的定义术语一致性。
- **Reference Documents in Ask**：在 Word Add-In 的 Ask 功能中上传参考文档，辅助分析。
- **Tabular Reports**：跨最多 500 个文档的结构化元数据提取。
- **未找到主合同<->修订协议<->附件的结构化关联导航机制。**

**信息来源**：Associate help, Tabular Reports help, Compare Documents help
**标注**：维度 2.6 "多文档关联导航"——Associate 提供跨文档分析能力，但结构化关联导航未明确。

---

### 维度 3: 中间解释性数据展示

#### 3.1 AI 判定风险的理由/依据呈现

- **Comprehensive Review**：每个被标记问题下方显示**推理说明**（"reasoning as to why that issue was flagged"）。
- **Playbook Fallback Positions**：当备选位置匹配文档条款时，显示勾号标记 + 解释为何满足该位置的推理。
- **Compare to Market**：展示条款分布数据，而非个别条款的推理。
- **Associate Chat 模式**：提供持续对话能力以获取更多细节和简明摘要。
- **与 Harvey 的 Answer + Reasoning 双字段结构相比**：Spellbook 的解释更偏向简要说明，而非详细的分析推理。

**信息来源**：Comprehensive Review help, Playbook help

#### 3.2 Playbook 标准与实际条款的对比

- **Playbook 红线即为对比**：运行 Playbook 后，AI 自动标记合同内容与 Playbook 规则的差异，并以红线标记建议的修改——修改即是"标准"与"实际"的差异可视化。
- **Fallback Positions 匹配视图**：规则失败时，显示备选位置与文档条款的匹配状态——这是结构化的"标准 vs 实际"对比。
- **Compare to Market**：提供"实际条款 vs 市场标准"的统计对比。
- **未找到专用两栏 diff 视图**。

**信息来源**：Playbook help, Compare to Market help

#### 3.3 相关法规原文引用

- **未找到法规原文引用功能**。Spellbook 的引用主要指向 Playbook 规则和用户文档。
- 审阅工具可选择特定**管辖区域（jurisdiction）**来调整分析，但这不等于展示法规原文。

**信息来源**：综合多个 Spellbook 页面
**标注**：维度 3.3 "法规原文引用"——未找到公开信息。Spellbook 是合同审阅工具，不具备 Harvey 的法律研究功能。

#### 3.4 置信度/风险评分的可视化

- **Playbook Risk Levels**：规则级别的风险等级元数据——最接近风险评分的概念，但未描述在 UI 中如何可视化。
- **Compare to Market 统计分布**：以分布图展示条款相对于市场的位置——这是数据驱动的"风险指示"而非置信度评分。
- **Benchmarks Coverage Score**：文档满足标准的程度分数。
- **未找到 Harvey 式的内部评估/置信度评分系统。**

**信息来源**：Playbook help, Compare to Market help, Benchmarks help
**标注**：维度 3.4 "置信度可视化"——有限的评分机制（Coverage Score、Risk Levels），但无系统化的置信度评分 UI。

#### 3.5 历史相似条款的审阅决策参考

- **Playbook 最佳实践**建议"使用一致的命名"、"保存可复用规则"、"从模板文档创建"——这些支持标准化和复用，但不是主动的"历史审阅决策推荐"。
- **未找到基于历史审阅数据的条款决策推荐功能。**

**信息来源**：综合多个 Spellbook 页面
**标注**：维度 3.5 "历史相似条款审阅决策参考"——未找到公开信息。

#### 3.6 数据来源可追溯性

- **Associate 审计追踪**：提供完整的时间戳审计日志记录——"plans and executes projects across document sets with full audit trail logging"。每次编辑、批准、义务均可追溯。捕获版本、评论和签批在防篡改审计追踪中。
- **引用（Citations）**：每个标记附带引用，可追溯建议到源 Playbook 规则（在 Playbook Review 中）。
- **合规认证**：SOC 2 Type II、HIPAA、GDPR、CCPA、PIPEDA。
- **基于角色的权限 + 访问日志 + 加密**。
- **"Audit-ready"输出**：时间戳批准、编辑历史、例外理由，便于审计和董事会验证。
- **Compare to Market 数据出处**：来源为"数千个类似合同"——但不提供单个合同的追溯（出于匿名化考虑）。

**信息来源**：Legal AI Agent Features page, Spellbook compliance pages

---

### 维度 4: 修改建议与协作

#### 4.1 修改建议的呈现形式

这是 Spellbook 最强维度的特性。所有修改建议**直接以 Word 原生 Track Changes 形式在文档内呈现**：

- **内联修订（Inline Redlines）**：AI 生成的修改直接以 Word Track Changes 红线标记在文档中。
- **评论标注（Comments）**：AI 生成的建议同时以 Word 评论形式呈现。
- **切换模式**：用户可在"Show revisions"（内联红线）和"Show comments"（仅评论）之间切换。
- **"Use tracked changes"开关**：控制是否自动对修订进行红线标记。
- **修改深度控制**：Light/Standard/Heavy Markup 三个层次——控制建议的数量和粒度。
- **第一方 Playbooks（First Party Playbooks）**：直接在 Track Changes 上运行 Playbook，发现偏离并推荐 Accept/Reject/Revise 操作，附带自动生成的评论。

**信息来源**：Comprehensive Review help, First Party Playbooks help

#### 4.2 一键接受/拒绝修改

- **Apply 按钮**：在侧边栏中对每个建议的修改提供 Apply 按钮来接受修改。
- **直接丢弃（Discard）**：可选择不应用建议的修改。
- **Playbook 自动红线**：运行 Playbook 后自动应用所有红线——用户随后审阅并逐条接受/拒绝。
- **Word 原生 Track Changes 的接受/拒绝**：由于修改以 Word 原生 Track Changes 形式存在，用户可使用 Word 自带的"Accept/Reject"功能。

**信息来源**：Comprehensive Review help, Playbook help

#### 4.3 手动编辑 AI 建议

- **侧边栏铅笔图标**：可编辑任何被标记的修订或评论——直接修改 AI 建议的措辞。
- **Word 文档内直接编辑**：因为修改以 Track Changes 形式存在，用户可在文档内直接修改建议文本。
- **Playbook 规则编辑**：通过"Enhance Rule"图标使用 AI 进一步优化规则。

**信息来源**：Comprehensive Review help, Playbook help

#### 4.4 多人协作审阅的批注与讨论

- **Playbook 协作模型**：
  - **单人编辑**：Playbook 采用单人创建者模型，只有创建者可编辑。其他贡献者需通过**所有权转移**或**克隆**方式参与。
  - **可见性控制**：Personal（仅创建者可见）或 Organization（与同事共享使用）。
  - **Reviewer Notes（审核者注释）**：可在规则中添加内部注释（如"需要注意的标记标准"或"需要额外批准"）。
  - **Suggested Comments（建议评论）**：外部谈判时可用的评论语言。
- **Associate 协作**：通过共享工作区和统一文档管理实现团队协作。
- **局限性显著**：无实时共同编辑 Playbook、无 Google Docs 风格的多人同时审阅、无原生的讨论/批注线程功能。协作模型更适合小团队或单律师主导的审阅流程。

**信息来源**：Playbook help, Associate help
**标注**：UI/UX 反模式——Playbook 的单人编辑模型限制了团队协作效率。相比之下 Harvey 的 Shared Spaces 和 Review Table 的多用户标记/评论系统更加成熟。

#### 4.5 版本对比

- **Playbook 版本管理**：自动保存草稿（"First Draft"下拉菜单），已发布版本与未发布更改分离（"Unpublished Changes"下拉菜单）。但这不是完整的版本历史（如时间戳、diff 视图）。
- **Associate 的版本和审计追踪**：完整的审计日志记录所有操作。
- **文档对比功能**：通过 Associate 可对比两个文档并以表格格式展示差异 -> 导出为 Excel。
- **未找到"原合同 vs AI 修改版 vs 最终版"的三栏对比视图。**

**信息来源**：Playbook help, Associate help
**标注**：维度 4.5 "版本对比"——有基础的 Playbook 版本管理和文档对比，但缺乏律师审阅中常用的多版本并排对比功能。

---

### 维度 5: 报告与导出

#### 5.1 审阅报告的生成格式

- **Review Tables / Tabular Reports**：可下载和导出表格（格式未明确，但 Associcate 文档对比支持 Excel 导出）。
- **Compare to Market**：可导出可下载报告，选择要包含的条款。
- **Word (.docx)**：这不是"报告"导出，而是审阅后的**红线文档**本身。由于 Spellbook 工作在 Word 中，修改后的文档自然就是最终交付物。
- **Ask 的 "Download Results Matrix"**：将多文档问答结果导出为 Excel 表格。
- **未提及 PDF、PowerPoint 导出。**

**信息来源**：Review Tables help, Compare to Market help, Ask help
**标注**：维度 5.1 "报告生成格式"——导出格式较少（主要 Excel），不如 Harvey（Word/Excel/PPT/CSV/PDF）丰富。

#### 5.2 报告内容的可定制性

- **Tabular Reports**：可添加自定义列、选择推荐列、创建多个视图、用提示词配置报告。
- **Review Tables**：可添加新问题、保存问题以供复用。
- **Compare to Market**：可自定义选择要包含的条款、选择代表方、添加交易上下文。
- **Standards Library**：可自定义检查标准。
- **未找到类似 Harvey 的自定义格式模板功能**（边距、字体、页眉等）。

**信息来源**：Tabular Reports help, Compare to Market help

#### 5.3 导出为 Redline/修订版合同

- **天然支持**：因为 Spellbook 核心工作流在 Word 内，所有修改都以 Track Changes 形式存在——保存文档即为红线版本。
- **Associate 的文件修订**：可使用参考文档修订 .docx 模板，下载包含 Track Changes 的完整文档。
- **Playbook Review 后**：自动红线应用的文档可直接保存为 .docx 红线文件。

**信息来源**：Comprehensive Review help, Associate help

#### 5.4 审计追踪的呈现

- **Associate 审计日志**："plans and executes projects across document sets with full audit trail logging and lawyer oversight at every step"。
- **时间戳批准 + 编辑历史 + 例外理由**。
- **Playbook 草稿/已发布版本区分**。
- **合规认证**：SOC 2 Type II、HIPAA、GDPR——支持监管审计要求。
- **未描述面向用户的审计追踪 UI**（如活动日志仪表盘或时间线视图）。

**信息来源**：Legal AI Agent Features page
**标注**：维度 5.4 "审计追踪"——后端审计日志存在，但用户界面的审计追踪可视化描述不详。

#### 5.5 数据导出能力

- **Excel 导出**：Review Tables、文档对比结果、Ask "Download Results Matrix" 均支持 Excel。
- **云存储集成**：OneDrive、SharePoint、Dropbox、iManage、Google Drive——支持从云存储导入和导出。
- **未找到 REST API 或编程式数据导出功能。**

**信息来源**：Associate help, Tabular Reports help
**标注**：维度 5.5 "API 导出"——未找到公开 API。与 Robin AI 的完整 REST API 相比差距显著。

#### 5.6 与项目管理/合同管理系统的集成报告

- **Document Management Systems**：支持与 NetDocuments、iManage、SharePoint 等 DMS 集成。
- **云存储集成**：OneDrive、SharePoint、Dropbox、Google Drive。
- **未找到与 CLM 或项目管理系统的特定集成报告。**
- **未找到类似 Robin AI 的 PowerBI 连接或 Harvey 的 Ecosystem 集成市场。**

**信息来源**：Legal AI Agent Features page, Associate help
**标注**：维度 5.6 "集成报告"——与文档管理系统集成但缺乏企业 CLM/项目管理集成。

---

## 附录：竞品横向对比速览表

| 维度 | Harvey | Robin AI | Spellbook |
|------|--------|----------|-----------|
| **主要界面模式** | Web 平台 + Word Add-In | Web 平台 + Word Add-In | **Word Add-In 主导** + Associate Web |
| **风险呈现** | Review Tables + Playbook 三级分类 | Tables + Chat + Word Track Changes | Word 侧边栏 + Track Changes |
| **风险分级** | 三色：Acceptable/Needs Review/Unacceptable + 多色标记 | Playbook 规则定义 + BI 工具 | Risk Levels 元数据 + Coverage Score |
| **原文定位** | 句子级引用 + Vault 跳转 | 可点击引用（最成熟） | Show 按钮 + Word 内原生定位 |
| **解释性数据** | Answer + Reasoning 双字段（最强） | 简要评论 + 引用链接 | 简要推理 + Fallback 匹配状态 |
| **置信度评分** | 内部评估系统（未面向用户） | N/A | Coverage Score / Risk Levels |
| **法规引用** | Shepard's Citations + 80+ 知识源 | 未找到 | 未找到 |
| **修改建议** | Track Changes + 评论 + 平台内编辑器 | Track Changes + 可下载 .docx | **Track Changes（最原生）** |
| **协作能力** | Shared Spaces + 多色标记 + 评论（最强） | Workspaces + Tables 分享 | 单人 Playbook 编辑（最弱） |
| **版本对比** | Playbook 版本历史 + 自动红线 | Compare Versions + Version History | Playbook 草稿/已发布 + 文档对比 |
| **报告导出** | Word/Excel/PPT/CSV/PDF（最丰富） | Word/Excel + API JSON | Excel（最有限） |
| **API** | 未找到公开 API | 完整 REST API（OpenAPI 3.1） | 未找到 |
| **审计追踪** | 完整审计日志 + 引用追溯 | Version History（基础） | Associate 审计日志 |
| **仪表盘** | Command Center（最强） | Obligation Dashboard | 无专用仪表盘 |
| **独特优势** | 全平台统一 + 端到端工作流 + 句子级引用 | API 优先 + 可点击引用 + PowerBI | **原生 Word Track Changes + 市场对标** |
| **已知局限性** | 学习曲线陡峭、价格高昂 | 已倒闭（历史数据） | 协作弱、报告格式少、无 API |

---

> **调研备注**：
> - Robin AI 已于 2025 年末倒闭，以上为其历史产品能力分析，可能不代表 Microsoft 整合后的功能走向。
> - 所有数据基于公开信息（官网、帮助中心、博客、第三方评测），可能未涵盖企业定制功能。
> - "未找到公开信息"标注表示在本次调研的搜索和网页抓取范围内未找到相关信息，不代表该功能一定不存在。
