---
status: verified
source: 本地实测（TencentDB Agent Memory feat/server_team @0468a2a 三容器栈：memory-core 8420 / memory-hub 8125 / tdai-proxy 8096）+ 官方 README 与 agents/claude-code、agents/codex 文档
source_version: 2026-09-12
applies_to: 用 Context Proxy 透明接入 TencentDB Agent Memory 的本地 workstream（Claude Code / Codex）
excludes: MCP Bridge 显式调用方案；订阅制账号（走 OAuth 直连，不在链路上）
---

# TencentDB Agent Memory 记忆层工作机制（注入 · 记录 · 检索）

## 结论

- 记忆不是「客户端里的一个工具」，而是**代理链路上的三个动作**：注入（把记忆塞进请求）、记录（把对话写回记忆库）、检索（按需查询）。客户端只做一件事——把 base URL 指向代理。
- 记忆分四层蒸馏：L0 对话 → L1 原子 → L2 场景 → L3 画像。**L2/L3 每轮自动注入**；L0/L1 不自动召回，由模型按需检索（避免每轮请求都携带大量原文、破坏前缀缓存）。
- 模型侧的「记忆工具」= **注入的说明文本 + 一组只读 HTTP 接口**。不是 MCP，也不是本地程序：代理往 system 里塞一段「要查记忆就用 curl 打这些路径」的说明，模型照做时由代理补身份与鉴权。

## 一次请求的时序（实测）

| # | 动作 | 日志关键字 |
| --- | --- | --- |
| 1 | 客户端把请求发到代理（不直连上游） | `→ REQ model=… msgs=N` |
| 2 | 代理验身份：user_key → user_id | `[asset-capability] user=…` |
| 3 | 会话归属初始化（新会话弹表单，见下节） | `[session-init:cc] … pending_asset_confirm` |
| 4 | 注入：往 system 追加若干块 | `injection.hook.done` / `*-injector` |
| 5 | 转发上游并流式回传 | `→ FORWARD upstream=…`、`← FORWARD status=…` |
| 6 | 记录 L0，归属到 team/agent/user/session | `tdai-recorder:write-l0 {team,agent,user,session,task,…}` |

注入块清单（实测的注入器 → 产物）：

| 注入器 | 产物 | 内容 |
| --- | --- | --- |
| `tdai-profile-memory-injector` | `<tdai_profile_memory>` | L3 画像 + L2 场景索引（可含「借入」的其他智能体分段） |
| `tdai-memory-tools-injector` | `<tdai_memory_tools>` | 检索接口清单与使用约束 |
| `skill-tools-injector` | `<skill_tools>` | 云端 skill 工具（同类机制） |
| `knowledge-tools-injector` | `<knowledge_tools>` | 知识库工具（同类机制） |

注入点：Anthropic 协议追加到 `body.system`；OpenAI 协议随 `messages` 携带。

## L0–L3 分层

| 层 | 是什么 | 生成 | 消费 |
| --- | --- | --- | --- |
| L0 对话 | 原始对话全文 | 每轮自动记录 | 按需检索 |
| L1 原子 | 从对话提炼的事实、偏好、约束、事件 | 后台异步流水线 | 按需检索（向量 + BM25 混合） |
| L2 场景 | 按项目或场景组织的知识块 | 同上 | 索引每轮注入，正文按需读 |
| L3 画像 | 长期画像、稳定模式 | 同上 | 每轮注入 |

两个推论：L0 全量记录并按（user, team, agent, session）归属 → 换会话仍能记得；L2/L3 每轮注入 → 新会话开场即带长期上下文。

## 检索接口（模型侧「工具」的真身）

只读 HTTP 接口，路径前缀 `/memory-bridge/v3/`：

| 接口 | 用途 |
| --- | --- |
| `atomic/search` | L1 原子记忆检索（dense + BM25 双路） |
| `atomic/query` | 按类型/时间窗拉取 L1 |
| `conversation/search` | L0 原文检索 |
| `conversation/query` | 按会话顺序读 L0 |
| `scenario/ls`、`scenario/read` | L2 索引/正文 |

约束：只读；检索类调用有每轮次数上限（实测默认 ≤ 3 次）；跨智能体检索默认同时覆盖自有与借入分段，结果带 `source_agent_*` 标注来源。

## 会话归属（团队资产）

- 新会话首个请求被代理拦截，弹「是否关联团队资产」表单；选「否」→ 本会话不注入、不归属。
- 选「是」后进入 team → agent → task 级联；**单团队/单智能体/单任务会自动选定**，不逐级弹窗。
- 归属状态按会话 id 持久化：仅「待答复（pending）」有 30 分钟 TTL，已初始化状态不设过期。客户端重开/续接同一会话**不会**改变归属（实测）；代理进程重启的「已初始化会话回灌」有源码支持，容器级重建未实测。
- 取消归属：在客户端输入框键入 `mem:session-reset`（代理拦截这条用户消息、重弹表单），选「否」。以助手身份写出来无效——必须由用户经输入框发送。
- 自动 bypass 的情形：无 user_id、内核不可达、名下无智能体、非交互会话下表单不可用（依赖交互式提问工具，被禁用时直接 bypass）、或请求头预置身份与内核记录不符。

## 边界

- 与 MCP Bridge 方案的区别：Bridge 是显式工具调用（模型主动存取），Proxy 是链路透明（自动记录 + 自动注入）；两者不互斥。接入与模型绑定的细节见 [Proxy 透明接入与模型绑定](tencentdb-agent-memory-proxy-mode.md)。
- 同一环境可能并存其他记忆层（插件式 MCP 记忆、文件记忆如 `CLAUDE.md` / `MEMORY.md`）：互不替代，排查「记忆为什么不生效/为什么生效」时先确认是哪一层在起作用。

## 验证方法

- 日志：`*-injector`（注入）、`tdai-recorder:write-l0`（记录）、`session-init`（归属变更）。
- 面板（memory-hub）可查看会话与记忆条目。
- 直观验证：换一个新会话直接问该智能体的旧结论，答对即说明注入与记录都在工作。

## 证据

- 官方 README（[链接](https://github.com/TencentCloud/TencentDB-Agent-Memory/blob/feat/server_team/README.md)）：分层定义原文「L0 Conversation → L1 Atom → L2 Scenario → L3 Persona — raw conversations are distilled layer by layer」及四层职责表。
- 本地实测：时序、注入块、归属状态机与 TTL/恢复语义、接口清单与约束，均以代理源码 + 运行日志双向核实。
