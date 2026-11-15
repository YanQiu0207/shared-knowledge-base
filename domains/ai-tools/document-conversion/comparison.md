---
status: provisional
source: 各项目官方 GitHub README；IBM Research 官方资料；公共库 WeKnora 条目中的历史核读记录
source_version: accessed 2026-11-15；未固定发布版本；美团为当日限定检索结果
applies_to: 图片、PDF、HTML、Excel 等文件转 Markdown，供 LLM 或知识库使用的跨项目选型
excludes: 穷尽公司项目、性能或质量排名、高保真与无损转换承诺、商用许可证法律判断
---

# 多格式文件转 Markdown：工具对比与选型

## 结论

默认起点可选 MarkItDown，但不应把它设为所有文件的唯一解析器。按格式和验收目标路由：普通文档先用轻量转换，扫描件补 OCR，复杂 PDF 做结构解析并核验，动态网页先获取渲染内容。

「各大公司都有类似产品」不等于所有项目处于同一层次：通用转换工具、OCR／版面解析模型、文档理解模型和知识平台应分开评估。以下能力来自官方资料，优先建议属于基于能力的判断，不是同批文件实测排名。

## 项目说明与对比

| 公司／机构 | 项目与官方来源 | 定位及已确认能力 | 替代边界 |
| --- | --- | --- | --- |
| 微软 | [MarkItDown](https://github.com/microsoft/markitdown) | 轻量 Python 多格式转 Markdown 工具，覆盖 PDF、Office、HTML、图片等，面向 LLM 和文本分析 | 官方不以面向人的高保真转换为目标；默认图片支持不等于完整 OCR |
| IBM Research 发起，现由 LF AI & Data 托管 | [Docling](https://github.com/docling-project/docling) | 多格式文档解析，支持 PDF、Office、HTML、图片，提供 OCR、阅读顺序、表格与版面理解，导出 Markdown／JSON | 可作为统一解析候选，复杂文档效果仍需样本验证 |
| 百度飞桨 | [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) | OCR 与文档解析工具链；PP-StructureV3、PaddleOCR-VL 支持 PDF／图片转 Markdown／JSON；当前 README 也列 Office 转 Markdown | 不应只理解为文字识别；具体格式入口与依赖按所选管线核对 |
| 腾讯 | [WeVisDoc](https://github.com/Tencent/WeVisDoc) | 文档页面图像转结构化 Markdown，包含 LaTeX 公式、HTML 表格；示例支持图片目录 | PDF 先渲染为页面图片；不是原生 Excel／HTML 通用转换器 |
| 腾讯混元 | [HunyuanOCR](https://github.com/Tencent-Hunyuan/HunyuanOCR) | OCR 视觉语言模型及推理工具 | 不能仅凭模型能力认定具备完整多格式转换、资源导出和批处理工作流 |
| 字节跳动 | [Dolphin](https://github.com/bytedance/Dolphin) | 文档解析模型及推理框架；提供文档图片、多页 PDF 解析，页面级输出 JSON、Markdown | PDF／图片解析候选；本轮未确认原生 Excel、HTML 转换 |
| 阿里 | [mPLUG-DocOwl](https://github.com/X-PLUG/mPLUG-DocOwl) | 仓库明确标注 Alibaba Group，侧重 OCR-free 文档理解与多页文档理解 | 本轮未确认完整多格式转 Markdown 流程，不与通用转换器直接等同 |
| 美团 | 本轮未确认可推荐的同类官方仓库 | 检索美团、Meituan、Meituan-AutoML 与 OCR、PDF、文档解析、Markdown 的组合，未取得足以推荐的官方项目证据 | 仅表示限定检索未命中，不表示美团没有相关项目 |
| OpenDataLab | [MinerU](https://github.com/opendatalab/MinerU) | 当前 README 覆盖 PDF、图片、Office、HTML 等输入，支持 Markdown 等结构化输出 | 不是大厂公司项目；输入格式、解析档位和导出能力按版本与入口核对 |
| Firecrawl | [AnyDoc](https://github.com/firecrawl/anydoc) | 既有知识记录其 Office、文本型 PDF 转 Markdown 能力 | 不是腾讯项目；本轮未重新核读该仓库，历史限制见下节 |
| Unstructured | [unstructured](https://github.com/Unstructured-IO/unstructured) | 文档接入、切分与预处理，服务 LLM 数据管线 | 不只是生成 Markdown 文件，不能把全部结构化输出默认视为 Markdown |
| Datalab | [Marker](https://github.com/datalab-to/marker) | 支持 PDF、图片、Office、HTML 等转 Markdown／JSON 等格式 | 采用前分别核对代码与模型许可证，不直接采信其自报横评作为本地排名 |

IBM 发起背景另见 [IBM Research 的 Docling 论文介绍](https://research.ibm.com/publications/docling-an-efficient-open-source-toolkit-for-ai-driven-document-conversion)。公司归属不用于推断质量、许可证或生产可用性。

## 推荐路由

| 输入／目标 | 建议起点 | 必须检查 |
| --- | --- | --- |
| Excel、普通 Office、静态 HTML | MarkItDown；需要更统一的文档模型时评估 Docling | 表头、合并单元格、工作表覆盖、图片遗漏；Markdown 不是原文件无损替代 |
| 普通文本 PDF | 先试 MarkItDown | 多栏阅读顺序、标题、表格、页间衔接与遗漏 |
| 扫描 PDF、图片文字 | 对测 PaddleOCR、Docling、MinerU、Dolphin、WeVisDoc 等适合当前环境的候选 | OCR 错字、漏页、公式、表格、资源消耗；WeVisDoc 需先把 PDF 渲染成图片 |
| 复杂排版 PDF，要求忠实还原 | 专门解析流程，加页面渲染和人工／程序核验 | 内容顺序、图文对应、公式、表格；不能承诺一键高保真 |
| 需要 JavaScript 渲染的网页 | 先用浏览器取得目标内容，再转 Markdown | 是否只取到空壳、是否包含展开内容、是否混入导航与广告 |
| 团队知识检索、Agent 或 Wiki | 再评估 WeKnora 等知识平台 | 平台能力与转换需求分开验收，不为纯转换部署整个平台 |

最小选型可以先比较 MarkItDown 与 Docling；扫描件占比较高时再加入一种专门解析方案，不必一次部署全部候选。

## 容易混淆的边界

1. **图片描述不等于 OCR**：MarkItDown 默认图片路径包括 EXIF 与可选描述；额外 OCR 可通过相应插件或服务获得，不能承诺基础安装自动完整识别。官方列出的图像描述、语音及 Azure 增强能力涉及云服务，敏感文件采用前需确认出网与费用。
2. **模型不等于产品管线**：识别模型之外，可能还需 PDF 渲染、分页、批处理、结果拼接、图片资源保存与失败恢复；逐项核对实际工具入口，不凭名称推断。
3. **WeKnora 不等于 AnyDoc**：WeKnora 是腾讯知识平台，转换是入库步骤；AnyDoc 属于 Firecrawl。既有核读记录指出 AnyDoc 本地核心不做 OCR、当时支持列表未列 HTML，嵌入图片也不能默认承诺导出为完整本地资源目录。这里是历史记录，不是本轮最新版确认，采用前应重查。
4. **自报评测不等于选型结论**：同批文件、同目标输出和可比硬件下测试，才适合比较质量与资源成本。不同项目的宣传分数不能直接横排。

## 最小验收与证据限制

保留原文件，选择包含文本 PDF、扫描 PDF、中文图片、复杂表格 Excel 和 HTML 的实际样本，逐项检查漏字、漏页、顺序、表格、公式、图片引用与编码，并记录失败与资源消耗。先定义「给 LLM 读」还是「给人忠实阅读」，再判断输出合格。

- 本轮核读官方 README，不含本机安装、转换测试或独立复现实验，状态为暂定。
- 不是各公司及关联组织的穷尽清单；没有搜到不能推导为不存在。
- 当前仓库文档可能领先于发布包，部署时固定版本并重新核对依赖、硬件、代码及模型许可证。
- 不把纯 Markdown 输出视为公式计算、交互页面或原版式的完整替代。

## 关联知识与来源

- 上表链接为各工具官方仓库来源，查阅于 2026-11-15；AnyDoc 除外，其说明继承下述既有知识记录，未在本轮重复核验。
- [WeKnora：腾讯开源企业知识平台](../../ai/weknora-tencent-knowledge-platform.md)，重点参见「2026-11-15 补充核实：纯转换的最小选型」；用于定位 AnyDoc 与知识平台的边界，不将历史版本结论冒充现状。

沉淀授权：用户于 2026-11-15 明确要求写入跨项目知识库；内容已泛化，不含项目私有信息。
