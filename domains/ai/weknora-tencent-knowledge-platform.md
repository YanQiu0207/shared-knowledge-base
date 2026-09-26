---
status: provisional
source: Tencent/WeKnora official GitHub README and weknora.weixin.qq.com official docs
source_version: accessed 2026-09-28 (v0.8.2, released 2026-09-24)
applies_to: 跨项目选型企业知识库 / RAG 平台、批量文档转 Markdown、给 Claude Code 等 AI 工具接知识库检索的场景
excludes: 微信对话开放平台在线版的计费与配额细节、生产集群运维、各解析引擎的内部实现源码分析
---

# WeKnora：腾讯开源企业知识平台（RAG + Agent + Wiki）

## 结论

腾讯微信团队开源的企业级知识管理框架（GitHub `Tencent/WeKnora`，MIT，2025-08 开源；截至 2026-09-28 约 30.1k stars，最新 v0.8.2）。一套系统三种能力共用同一知识库：RAG 问答（混合检索 + 原文引用）、Agent 执行（多步推理 + 技能沙箱 + 长期记忆）、自动 Wiki（文档生成互链页面 + 知识图谱）。核心判断：

- **「转 Markdown」是入库解析的中间产物，不是对外主打功能**。文档进知识库后统一转为 Markdown 再分块检索，分块可编辑、有一键 Markdown 导出；但纯「批量转 .md 文件」场景应直接用它的底层引擎 AnyDoc（Firecrawl 的 Rust 库，独立开源）或 MarkItDown / MinerU / Docling，不必部署整套 WeKnora。
- **差异化在中文生态集成与对外输出**：内置飞书 / 企业微信 / 钉钉 / 语雀 / Notion / Confluence / GitLab / RSS 自动同步，27 家模型厂商目录；内置按空间隔离的 MCP Server，Claude Code / Cursor 可直连检索——这是给编码 Agent 接团队知识库的现成通道。
- **部署门槛低**：Docker Compose / K8s(Helm) / Lite 单机版（SQLite + 内存队列）/ 桌面版（需源码构建）。官方明确建议部署内网、勿暴露公网。

## 文档解析能力（转 Markdown 的边界）

解析链路：文件 → Markdown + 图片引用 → 分块 → OCR/图片描述（Go 侧）→ 向量化。支持的格式：PDF、Word（doc/docx）、PPT、Excel（xls/xlsx）、EPUB、XMind、txt/Markdown/CSV/JSON、网页 URL、HTML/MHTML、图片（需视觉模型）、音频（需 ASR 模型）。

| 引擎 | 说明 | 边界 |
| --- | --- | --- |
| anydoc（默认，Docker 镜像内置） | Rust 库经 cgo 进程内直转 Office → GFM Markdown，不经 Python 服务 | 只抽 PDF 文字层（扫描件丢内容，自动移交 builtin）；纵向合并单元格不回填（后续行留空） |
| docreader/builtin | 独立 Python gRPC 服务，逐页识别 | 扫描件走 OCR（PaddleOCR-VL 在 Go 侧） |
| 可选替换 | MarkItDown / OpenDataLoader / MinerU | 按知识库解析设置按格式指定 |

图片处理：默认抽取嵌入图并改写为 `images/image-N.ext` 链接，保留原位置；扫描页与插图由 Go 侧做 OCR 与 VLM caption。Excel 可开「首行作为表头」。

## 相比同类（RAGFlow / Dify / FastGPT）的定位

- Dify 是通用 AI 应用 / 工作流构建器，Agent 编排更灵活；RAGFlow 主攻深度文档解析；FastGPT 主打简单易用；WeKnora 定位「知识库工作台」三合一，中文数据源官方支持最全。
- 未做深度横评，各家检索质量对比缺乏可靠第三方基准——选型以自己数据实测为准。

## 版本演进要点（证明活跃度，升级前查官方 notes）

- v0.8.2（2026-09-24）：BrowserSkill 让 Agent 操作本机 Chrome/Edge；内置 MCP Server（旧 Python `mcp-server/` 废弃）；对话可中途追加要求 / 分叉 / 回滚。**Breaking**：沙箱命令以 root 运行、钉钉渠道改 Stream-only。
- v0.8.0：技能沙箱（Docker/E2B/Cube）、跨会话长期记忆、anydoc 进程内解析。

## 相关条目

- 试用后若确认 MCP Server 接 Claude Code / Codex 的接线细节，另建条目并在此互链。
