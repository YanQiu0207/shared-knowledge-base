---
status: verified
source: first-hand docs verification of docs.langchain.com, docs.letta.com, github.com/letta-ai/letta, github.com/mem0ai/mem0, github.com/badlogic/pi-mono, code.claude.com/docs (2026-09 实地核对)
source_version: 2026-09-27
applies_to: 为「带 Web/多用户外壳的 LLM agent 应用」补上下文管理、长期记忆、自进化能力时做组件选型
excludes: 纯 coding agent CLI 的选型（pi/Claude Code 本体）、无状态的单次任务 API 调用
scope: cross-project
---

# Agent 框架的记忆/上下文/自进化组件选型

## 结论

给已有 agent 应用补「上下文管理、持久化记忆、自进化」时，**先盘点框架官方组件，再考虑换框架或外挂中间件**。LangChain 1.x（≥1.3）官方已内置这三块的组件位，全部是「给 `create_agent` 加参数/中间件」级别的加装，不需要重写架构：

| 需求 | LangChain 官方组件 | 接入方式 |
| --- | --- | --- |
| 上下文自动压缩 | `SummarizationMiddleware`（`trigger` 按 tokens/条数/比例，`keep` 保留近 N 条） | `create_agent(middleware=[...])` |
| 工具输出膨胀 | `ContextEditingMiddleware` + `ClearToolUsesEdit`（自动清旧工具输出） | 同上 |
| 长期记忆 | `create_agent(store=...)`：namespace+key 的 JSON 文档存储，支持语义检索；工具内 `runtime.store` 读写；`context_schema` 传 `user_id` 做用户隔离 | 传 store + 写记忆工具 |
| 自进化 | LangMem（langchain-ai 官方）：hot-path 记忆工具 + background 后台提炼 | 可选加装 |
| 沙箱 | `ShellToolMiddleware.execution_policy`：Host/Docker/CodexSandbox 三档 | middleware 列表 |

## 开箱即用框架对比（2026-09 实测口径）

若六项需求（开箱即用、自动上下文、持久化记忆、自进化、Skill/Tool/MCP、沙箱）全要，逐项核对结果：

- **Claude Agent SDK**：六项全中（session 自动落盘 + resume/fork/跨机 SessionStore、auto-compaction、SKILL.md 自动加载、MCP 一等支持、Managed Agents 云沙箱）。代价：模型绑定 Anthropic 兼容 API，多模型 OpenAI 兼容端点收窄；多用户下每会话一个子进程。
- **Letta（原 MemGPT）**：自进化记忆最强（core memory 注入上下文、agent 用记忆工具自改记忆、压缩淘汰框架管、记忆全入 DB）。坑：源码已迁 `letta-code`、旧 Python V1 API server 进 archive，生态剧烈变动；自托管 Python 链路的 MCP/Skill 未证实。
- **pi（badlogic/pi-mono，110k star）**：coding agent CLI + 统一 LLM API，**无内置记忆**，终端形态，不适合嵌入 Web 产品。
- **Mem0**：只是记忆层（search/add 两行插入），不是 agent 框架；新版算法 ADD-only 不做冲突更新；完整算法收益绑定商业平台。
- **Agno**：memory/AgentOS 有证实，MCP client/沙箱/上下文自动管理在官方页未证实，观望。

## 判定规则

1. 「感觉框架原始」先查两件事：本机版本 vs PyPI 最新（当时 langchain 1.0.0 vs 1.4.2，middleware 精装修是 1.x 演进中逐步交付的）；官方组件清单有没有盘点过。选型时只用过最小 API 面 ≠ 框架没有该能力。
2. 「记忆」要拆三档再选型：会话内历史（自己拼 or checkpointer）、跨会话用户记忆（store）、后台自进化（LangMem/background manager）。混为一谈会高估换框架的收益。
3. 多用户产品「用户自带 OpenAI 兼容 key」是硬需求时，Claude Agent SDK 路线基本被排除，留在 LangChain 加装组件是改动最小的路线。
4. LangChain 官方 store 无 SQLite 后端（InMemoryStore 开发用；生产 Postgres/Redis/Mongo）。SQLite 项目要么引入 Postgres，要么自写薄 SQLite store 适配（新增类，不算重写）。

## 关键坑

- `SummarizationMiddleware` 旧参数名 `max_tokens_before_summary`/`messages_to_keep` 已废弃 → 用 `trigger`/`keep`。
- starlette 约束：langchain-mcp-adapters/mcp 依赖链会把 starlette 拉到 1.x，与 fastapi 0.115 冲突（`Router.__init__() got an unexpected keyword argument 'on_startup'`），需 pin `starlette<0.42`。升级 langchain 后重验此约束。
- LangMem 依赖 LLM 做记忆抽取（默认 OpenAI 系），接自建端点时需确认兼容。
