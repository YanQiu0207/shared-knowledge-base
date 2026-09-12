---
status: verified
source: 本地实测（TencentDB Agent Memory feat/server_team @0468a2a 的 deploy/global-images 三容器栈）+ 官方 agents/claude-code/README.md、agents/codex/README.md
source_version: 2026-09-12
applies_to: 用 Context Proxy 透明劫持方式接入 TencentDB Agent Memory 的本地 workstream（Claude Code / Codex）
excludes: MCP Bridge 接入方案（见同目录 tencentdb-agent-memory-claude-codex.md）、面板与知识库运维、凭证管理
---

# TencentDB Agent Memory 的 Proxy 透明接入与模型绑定

## 结论

TencentDB Agent Memory 有两条接入路径，容易混淆：

| 维度 | MCP Bridge 方案 | Proxy 方案（本篇） |
| --- | --- | --- |
| 接入点 | MCP 工具，显式调用 | LLM API 链路，透明劫持 |
| 记忆写入 | 手动 `memory_capture` | 自动捕获每轮对话 |
| 客户端改动 | 注册 MCP server | 改 API base URL |
| 适用 | 想精确控制写入 | 想全程自动沉淀 |

Proxy 方案的**核心约束是模型绑定**：proxy 只做转发、不做模型名映射，因此客户端必须显式指定一个「上游真实支持」的模型名。用哪个模型不取决于本工具，取决于你把上游指向了哪家。

由这条约束派生出一个结构性限制：**订阅制账号（ChatGPT Plus / Claude Pro 等）用不了本工具**，因为它们走 OAuth 直连厂商后端，而 proxy 只支持 API key 形态的上游。

另有一条客户端侧的配套约束：Claude Code 不认识第三方模型名时会按 200k 兜底上下文窗口，需要在模型名后加 `[1M]` 标记声明（见下文「第三方模型的窗口标记」）。

## 模型名为什么必须显式设

结论：**proxy 是透明转发，客户端发什么模型名就原样转给上游，不改写、不校验。**

证据三条：

1. proxy 的 `config.yaml` 没有 `model` 字段，只有 `upstream.url` 与 `upstream.apiKey`。
2. 部署 `.env` 里的 `PROXY_UPSTREAM_MODEL` 在 proxy 源码中**零引用**——它只出现在部署脚本的交互提示与 `start-all.sh` 的打印里，实际作用是「告诉用户该往客户端填什么」。
3. 官方文档明确写：`ANTHROPIC_MODEL`：上游模型名（也可以用 `--model` 参数指定）。

因此上游是 DeepSeek 时只能填 `deepseek-flash` 一类的名字；填 `claude-opus-4.7` 或 `gpt-5.6-sol` 会被**上游**拒绝（不是被 proxy 拒绝）。

若确实要用原生模型，需把上游换成对应厂商的 API：`claude-*` 需 Anthropic 端点与 key，`gpt-*` 需 OpenAI 端点与 key。proxy 支持**按 agent 分别配上游**（`upstream.agents.<agent>.url`），所以可以让 Claude Code 与 Codex 各走各的上游——这也正是 Codex 必需的（见下）。

## 第三方模型的窗口标记（`[1M]`）

Claude Code 会校验模型名是否在其内置「模型目录」中。**目录里没有的第三方模型名**（`deepseek-flash`、`deepseek-v4-pro` 这类），客户端无法确定上下文窗口，于是打印下面这条提示，并**按 200k 兜底**计算 auto-compact 阈值：

```
"deepseek-flash" isn't described by this version's model catalog; update Claude Code, or map it with behavesAs on a modelPicker row (or modelOverrides, if it is a provider id of a model this version knows). Until then auto-compact keeps this session within 200k tokens (the context window it assumes); if the model accepts more, append [1m] to the model name for 1M, or set CLAUDE_CODE_MAX_CONTEXT_TOKENS to its real window; CLAUDE_CODE_DISABLE_UNKNOWN_MODEL_WINDOW_ENFORCEMENT=1 restores the previous wait-for-the-API behavior.
```

修法三选一：

| 做法 | 写法 | 说明 |
| --- | --- | --- |
| 模型名加标记（推荐） | `--model 'deepseek-flash[1M]'`；`ANTHROPIC_MODEL` 同理 | 声明 1M 窗口；标记由**客户端剥离**，不会发往上游 |
| 声明真实窗口 | `CLAUDE_CODE_MAX_CONTEXT_TOKENS=<真实窗口>` | 最精确；真实窗口不是 1M 时用这条 |
| 关闭校验 | `CLAUDE_CODE_DISABLE_UNKNOWN_MODEL_WINDOW_ENFORCEMENT=1` | 回到旧行为 |

实测要点（本地截获客户端请求确认）：

- 加标记后，请求体里的 `"model"` 仍是 `deepseek-flash`——**后缀不泄漏给上游**；大小写等效（`[1m]` / `[1M]` 都识别，内部归一为 `[1m]`）。
- 代价：请求会带上 `context-1m-2025-08-07` beta 头；实测带该头的调用经 proxy 全链路未被上游拒绝（失败均为内容类错误）。
- 不加标记只是提示，不影响功能：真正的差别只在「何时触发自动压缩」——模型真窗口大于 200k 时会被过早压缩。
- `[1M]` 是**断言**而非开关：等于告诉客户端该模型有 1M 窗口，要按真实窗口填。
- 这是 Claude Code 客户端行为，不限于本 proxy：任何第三方 `ANTHROPIC_BASE_URL` 组合都一样。旧版（2.1.226）有同类提示、措辞不同；2.1.269 换成了「model catalog / behavesAs / modelOverrides」的说法。

## 订阅制账号为什么用不了

memory 工具必须插在「客户端 → 模型」链路中间才能注入记忆，而订阅制的调用不经由此处：

| 用法 | 实际链路 | 能否注入记忆 |
| --- | --- | --- |
| 裸客户端 + 订阅登录 | 客户端 OAuth → 厂商后端 | 否，不在链路上 |
| 裸客户端 + API key（指向 proxy） | 客户端 → proxy → 上游 | 是 |
| 包装脚本指向 proxy | 同上 | 是 |

订阅与 proxy 二者不能同时生效——这是结构性的，不是配置问题。

> 订阅制仍有一条可用路径：**客户端 Hook**（见[Hook 接入（免 proxy）](tencentdb-agent-memory-hook-mode.md)）不占用模型链路，因此订阅登录与记忆注入可以并存，代价是资产上下文需要自行补齐。

> **未验证的例外**：Codex 二进制中存在 `requires_openai_auth` 字段（可把 ChatGPT token 发给自定义 provider），而 proxy 支持透传客户端 Authorization。二者组合在理论上可实现「订阅 + 记忆注入」，但需关闭 proxy 自身 auth 并手工指向厂商后端，**未实测**；且订阅流量绕经中间层的合规性未查证。

## 客户端接入

### Claude Code

改 `~/.claude/settings.json` 的 `env`，或临时 export：

```json
{
  "env": {
    "ANTHROPIC_BASE_URL": "http://127.0.0.1:8096/claude-code/default",
    "ANTHROPIC_AUTH_TOKEN": "<user_key>",
    "ANTHROPIC_MODEL": "<上游模型名>"
  }
}
```

`/claude-code/default` 路径中的 `default` 是 memory 实例 ID（即 `x-tdai-service-id`），本地部署固定为 `default`。**这个 agent 前缀不能省**：auth 的 service_id 从路径解析，形如 `/v1/messages` 的裸路径会因取不到 spaceId 而 401。

### Codex

```toml
model_provider = "tdai"
model = "<上游模型名>"
disable_response_storage = true      # ← 必须顶层

[model_providers.tdai]
wire_api = "responses"
base_url = "http://127.0.0.1:8096/codex/default/v1"
experimental_bearer_token = "<user_key>"
```

Codex 有三个与 Claude Code 不同的硬约束：

1. **`wire_api = "responses"` 必填**：Codex 走 OpenAI Responses API，不是 Chat Completions。因此上游必须是支持 `/responses` 的端点——DeepSeek 的 OpenAI 兼容端点支持，但其 Anthropic 端点不支持，必须用 `upstream.agents.codex.url` 单独指向。
2. **`disable_response_storage = true` 必须在顶层**：写进 `[model_providers.*]` 段内不生效，会导致 Codex 省略 reasoning 内容，上游报 `reasoning_text ... must be passed back`。
3. **首次对话需切到 Plan 模式**：session-init 借 Codex 的 `request_user_input` 工具弹表单，而该工具仅在 Plan 模式可用；默认模式下会返回一次「未开启 Plan 模式」提示并落 bypass，第二轮起正常透传。这是设计行为，与模型无关。

## 部署形态

官方 `deploy/global-images` 提供三容器栈：

| 容器 | 端口 | 职责 |
| --- | --- | --- |
| memory-core | 8420 | 记忆内核（L0–L3、skill、元数据） |
| memory-hub | 8125 / 8424 | 面板 UI + 知识服务 |
| tdai-proxy | 8096 | 劫持点，转发上游并注入记忆 |

`PROXY_FULL_STACK=1` 一次打开 auth / sessionInit / tdai 三个能力开关。

## 已知坑

- **代理层误剥离 thinking 块导致上游 400**：`content[].thinking` 与 `reasoning_text` 两条报错的成因、定位与修复，见[思考内容回传缺失导致上游 400](../../issues/thinking-passthrough-400.md)。

## 证据

- 官方客户端文档：[`agents/claude-code/README.md`](https://github.com/TencentCloud/TencentDB-Agent-Memory/blob/feat/server_team/agents/claude-code/README.md)、[`agents/codex/README.md`](https://github.com/TencentCloud/TencentDB-Agent-Memory/blob/feat/server_team/agents/codex/README.md)
- 本地实测：三容器栈启动后，Claude Code 与 Codex 经 proxy 转发 DeepSeek 均成功应答；模型名、路径前缀、`disable_response_storage` 层级三项均以「改动—复测」方式确认。

## 相关条目

- [记忆层工作机制（注入 · 记录 · 检索）](tencentdb-agent-memory-mechanics.md)——同一系统的运行机制、会话归属、检索接口与验证方法。
- [Hook 接入（免 proxy）](tencentdb-agent-memory-hook-mode.md)——客户端生命周期事件接入；订阅制可用、无逐会话交互；资产上下文需自行补齐。
