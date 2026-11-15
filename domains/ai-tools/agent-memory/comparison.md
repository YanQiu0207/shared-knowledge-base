---
scope: cross-project
status: provisional
source: 各项目官方 GitHub README 与官方文档；TencentDB Agent Memory 本地部署实测数据（配置、日志、导出记录）
source_version: accessed 2026-11-15；TencentDB Agent Memory 最新发布 v2.0.3（2026-10-26）；causal-memory v0.10.0
applies_to: 为 Claude Code、Codex 等 Coding Agent 选择跨会话记忆层或共享知识库，并评估自动沉淀的模型调用成本
excludes: 性能或质量排名（README 中的评测均为项目方自报）、商用许可证法律判断、穷尽各公司开源项目
---

# Agent 记忆与知识管理工具：调研与选型

## 结论

- **先区分两类需求**：「记忆层」放未审核、可快速召回的经验；「知识库」放审核过的定论。两者都需要写清触发时机（设计、编码、审核前读；验证后写），工具本身不解决「什么时候读写」。
- **自动沉淀的成本跟着对话量走，不跟着记忆有没有用走**。另起一个 LLM 自动提炼每轮对话的方案（如 TencentDB Agent Memory 的 proxy 模式），即使最后判定「无可沉淀」，模型也已读完整段对话。重视额度时，优先选「Agent 显式调用才写入」的工具。
- 同时支持 Claude Code 与 Codex、且已核实的：OpenViking（官方插件）、Basic Memory（官方文档）、causal-memory（官方安装脚本）。ReMe 的 Claude Code 插件已核实，Codex 未核实。
- 本机实际选择：causal-memory 作为共享记忆层，跨项目知识库继续用 Markdown 仓库。安装与使用见 [causal-memory 条目](causal-memory-setup.md)，原方案停用记录见 [TencentDB Agent Memory 停用](tencentdb-agent-memory-deactivation.md)。

## 大厂开源项目（2026-11-15 快照）

| 公司 | 项目 | 定位 | 备注 |
| --- | --- | --- | --- |
| 腾讯 | [TencentDB Agent Memory](https://github.com/TencentCloud/TencentDB-Agent-Memory) | 分层记忆引擎（L0 → L3），后扩展为团队记忆中心（Chat Memory、Skill、Wiki、CodeGraph） | MIT；Claude Code 与 Codex 的官方接入至 v2.0.3 仍只有 proxy 模式，hook 仅提供给 OpenClaw 插件 |
| 腾讯 | [WeKnora](https://github.com/Tencent/WeKnora) | RAG + Agent + Wiki 企业知识平台 | 详见 [WeKnora 条目](../../ai/weknora-tencent-knowledge-platform.md) |
| 腾讯 | Hy-Memory、octop-memory 等 | 见 [腾讯 AI 开源项目发现](../../ai/tencent-ai-open-source-landscape.md) | 未运行验证 |
| 字节（火山引擎） | [OpenViking](https://github.com/volcengine/OpenViking) | Agent 上下文数据库，用文件系统统一管理记忆、资源与技能 | Claude Code 与 Codex 官方插件共用安装器；连同一 server、同一用户即共享记忆；自动记录会话并提炼 |
| 字节（火山引擎） | [MineContext](https://github.com/volcengine/minecontext) | 主动推送的上下文感知 AI 应用 | 偏个人上下文管理 |
| 字节 Seed | [MemAgent](https://github.com/BytedTsinghua-SIA/MemAgent)、M3-Agent | 用强化学习训练长上下文记忆；多模态长期记忆 | 研究向，不是开箱即用的工具 |
| 阿里 | [ReMe](https://github.com/agentscope-ai/ReMe)（前身 MemoryScope） | 把记忆存成可读、可编辑的 Markdown；CLI、HTTP、MCP、Python API | Apache-2.0；两者的继承关系为推断 |
| 阿里云 | Agentic Memory 智能体记忆服务 | 商业服务 | 非开源 |
| 美团 | 未发现同类项目 | 开源以 LongCat 系列模型为主 | 仅限当日检索结果 |

## 非大厂项目

| 项目 | 定位 | 两个 CLI 均支持 | 特点与代价 |
| --- | --- | --- | --- |
| [causal-memory](https://github.com/JingxuanC/causal-memory) | 记录「决策 → 结果」因果边，执行前预警 | ✅ 官方安装脚本 | Rust 实现，SQLite；不配 LLM 时 BM25 检索可用；alpha 阶段的个人项目 |
| [Basic Memory](https://github.com/basicmachines-co/basic-memory) | 以 Markdown 文件为准的知识库，经 MCP 检索 | ✅ 官方文档 | AGPL-3.0；本地 FastEmbed 向量检索，不需要外部模型 API；需 Python 3.12+ 与 `uv` |
| mem0 | 通用记忆层，擅长事实召回 | 未核实 | 写入时调用 LLM 提炼 |

## 值得吸收的设计思想

| 思想 | 来源 | 落地方式 |
| --- | --- | --- |
| 先读摘要再读正文：目录摘要（L0）、概览（L1）判断相关性后才打开全文（L2） | OpenViking | 知识库按「根索引 → 主题索引 → 条目」逐层下钻 |
| 记忆存成人可读、可改的 Markdown | ReMe、OpenViking | 审核的前提 |
| 召回内容非权威，以当前代码与测试为准 | 通用 | 写进 Agent 全局规则 |
| 分级提炼：原始对话 → 提炼 → 定论 | TencentDB Agent Memory、OpenViking | 先进记忆层当候选，审核后升级为知识库条目 |
| 动作前预警：危险操作前先查相关教训 | causal-memory `intervention_query` | 规则要求高风险操作前查询；踩坑条目加 `triggers` 字段 |
| 记录「错误做法 → 后果」，不只记正确做法 | causal-memory 的 `caused` / `prevented` 边 | 踩坑条目正文必含该段 |
| 过时结论标注作废而不删除 | causal-memory `superseded_by` | 条目改 `status: superseded` 并指向新条目 |
| 记录知识的使用反馈，淘汰无用条目 | Comet `knowledge feedback` | 暂未落地 |

## TencentDB Agent Memory 的成本实测

本地部署（镜像构建于 2026-09-07）的配置与数据：

- 提炼模型为 DeepSeek `deepseek-flash`，使用独立 key，与 Coding Agent 的模型额度无关。
- proxy 开启 `writeL0: true` 时逐轮记录原始对话；每 5 轮或空闲 10 分钟触发一次 L1 提炼（`everyNConversations: 5`、`l1IdleTimeoutSeconds: 600`），另有场景归纳（15 到 60 分钟）、画像（每 50 轮）和技能提取（最多 16 轮迭代）。
- 原始对话累计 59 MB，提炼出 8094 条记忆：事实 3348、方法 2508、任务 1188、产出物 1050。多个高对话量日期提炼结果为 0。
- 方法中被标为反模式或约束的去重后只有 550 条，抽查可见不少只是复述已有的 Agent 全局规则。
- DeepSeek 余额耗尽后，L1 提炼持续报 `Insufficient Balance`，proxy 仍在照常记录原始对话，形成「只花钱不产出」的状态。

具体金额无法统计：本地没有用量报表，memory-core 日志一天上百万行。
