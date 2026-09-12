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

由这条约束派生出一个结构性限制：订阅制账号通常走 OAuth 直连厂商后端，不能直接套用只接受 API Key 的 Proxy 配置。Codex 存在已实测的双凭据例外，见下文；Claude Code 订阅链路尚未验证同类方案。

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

传统单凭据配置下，订阅与 Proxy 不能同时生效；根因是上游 OAuth 与 Memory User Key 竞争同一个 `Authorization` Header。若客户端允许追加独立 Header，且 Proxy 能分离两类凭据，则可解除该冲突。

> 订阅制仍有一条可用路径：**客户端 Hook**（见[Hook 接入（免 proxy）](tencentdb-agent-memory-hook-mode.md)）不占用模型链路，因此订阅登录与记忆注入可以并存，代价是资产上下文需要自行补齐。

> **已验证的 Codex 例外（2026-09-12）**：Codex 自定义 provider 同时启用 `requires_openai_auth = true` 与 `http_headers`，可用 `Authorization` 透传 ChatGPT OAuth，并用 `x-tdai-user-key` 单独完成 Memory Proxy 鉴权。Proxy 需优先从 `x-tdai-user-key` 取 Memory 凭证，并禁止将该 Header 转发到上游。实测完成 sessionInit、注入 4 个上下文块、转发 `https://chatgpt.com/backend-api/codex/responses` 返回 HTTP 200，并成功写入 L0。该方案仍未核查订阅流量经自建代理转发的合规性。

### Claude Code 与 Codex 共用一个 Proxy

两种客户端可以共用同一个 Proxy 实例，因为路由前缀和协议不同：Claude Code 使用 `/claude-code/<instance>/v1/messages`，Codex 使用 `/codex/<instance>/v1/responses`。配置时保留 Claude Code 所需的全局 Anthropic 上游及 API Key，再为 Codex 设置独立上游：

```yaml
upstream:
  url: "https://open.bigmodel.cn/api/anthropic/v1"
  apiKey: "<anthropic-api-key>"
  agents:
    codex:
      url: "https://chatgpt.com/backend-api/codex"
```

这里 `upstream.agents.codex.apiKey` 必须缺省：其语义是「Codex 显式选择独立上游，但沿用客户端传入的 OAuth」，不能回退到全局 Anthropic API Key。Proxy 的授权优先级应为：

1. 存在 Agent 上游且配置了 API Key → 使用 Agent API Key。
2. 存在 Agent 上游但未配置 API Key → 保留客户端 `Authorization`。
3. 不存在 Agent 上游 → 使用全局 API Key。

本机共享实例验证中，Codex 通过该配置返回 HTTP 200，完成 4 个上下文块注入与 L0 写入。Claude Code 在同一实例中已完成 sessionInit 与 4 个上下文块注入，但智谱上游当时连接失败；旧独立实例同时出现相同 502，因此 Claude 上游成功应答仍待上游恢复后补验。

### 从 Hook 切换到 Proxy 后的清理

Proxy 已自动完成提示注入和会话归档时，原 TDAI Memory 的 `UserPromptSubmit` 与 `SessionEnd` Hook 会形成重复链路，可以解除注册。建议先保留 Hook 文件和带时间戳的客户端配置备份，待 Proxy 端到端验证稳定后再决定是否物理删除。

Memory MCP 不与 Proxy 完全重复：Proxy 负责自动注入与记录，MCP 提供显式检索或写入工具。需要主动检索能力时可保留 MCP；不要把移除重复 Hook 等同于移除 MCP。

## 跨机器快速复制

下面的流程以 TencentDB Agent Memory 基线 `0468a2a5b50eaafc54758ed1e2e6609472e5b6ce` 为准。仓库版本不同应先执行 `git apply --check`，不要跳过兼容性检查。

### 1. 应用 Codex OAuth Proxy 补丁

可直接使用知识库保存的补丁：[Codex OAuth Proxy 补丁](../../sources/patches/tencentdb-agent-memory-codex-oauth-proxy.patch)。它包含以下已验证能力：

- `Authorization` 保留 ChatGPT OAuth；
- `x-tdai-user-key` 单独用于 Memory 鉴权，并在转发前剥离；
- Claude Code 与 Codex 共用一个 Proxy 时，Codex 不继承全局 Anthropic API Key；
- 透传 Codex 启动时的 `GET /models`，保留 `client_version` Query；
- `/models` 同样验证 Memory User Key，匿名请求返回 HTTP 401。

```powershell
git apply --check E:/work/shared-knowledge-base/sources/patches/tencentdb-agent-memory-codex-oauth-proxy.patch
git apply E:/work/shared-knowledge-base/sources/patches/tencentdb-agent-memory-codex-oauth-proxy.patch
```

补丁对应的本地提交为 `22ba97d`、`4890793`、`51264f5`。若这些提交已进入目标分支，不要重复应用补丁。

### 2. 配置共享 Proxy

```yaml
upstream:
  url: "https://open.bigmodel.cn/api/anthropic/v1"
  apiKey: "<zhipu-api-key>"
  agents:
    codex:
      url: "https://chatgpt.com/backend-api/codex"

auth:
  enabled: true

sessionInit:
  enabled: true

injection:
  enabled: true
  externalGatewayUrl: "http://127.0.0.1:8097"
  injectors:
    - skill
    - knowledge
    - tdai-memory
```

`upstream.agents.codex.apiKey` 必须缺省；写入任何值都会替代 Codex 客户端 OAuth。`externalGatewayUrl` 必须是客户端可访问的地址，不能依赖 Docker 自动生成的 `172.*` 容器 IP。

构建并启动：

```powershell
docker build -t tdai-memory-proxy:codex-oauth E:/github/TencentDB-Agent-Memory/MemoryProxy
docker run -d --name tdai-proxy-shared `
  --network tdai-memory-stack `
  -p 8097:8096 `
  --restart unless-stopped `
  -v "E:/github/TencentDB-Agent-Memory/deploy/global-images/.proxy-config-shared/config.yaml:/data/config.yaml:ro" `
  tdai-memory-proxy:codex-oauth
```

### 3. 配置 Claude Code

`~/.claude/settings.json`：

```json
{
  "env": {
    "ANTHROPIC_BASE_URL": "http://127.0.0.1:8097/claude-code/default",
    "ANTHROPIC_AUTH_TOKEN": "<memory-user-key>",
    "ANTHROPIC_MODEL": "glm-5.3-flash"
  }
}
```

保留文件中的其他现有字段。写入后完全退出并重新启动 Claude Code，在新会话中关联 Team 与 Agent。

### 4. 配置 Codex

`~/.codex/config.toml`：

```toml
model_provider = "team-proxy"
model = "gpt-5.6-sol"

[model_providers.team-proxy]
wire_api = "responses"
base_url = "http://127.0.0.1:8097/codex/default/v1"
requires_openai_auth = true

[model_providers.team-proxy.http_headers]
x-tdai-user-key = "<memory-user-key>"
```

Codex 必须先通过 ChatGPT OAuth 登录。`requires_openai_auth = true` 让客户端把 OAuth 放进 `Authorization`；`http_headers` 中的 Memory User Key 供 Proxy 鉴权，两者不能互换。

默认不预填 `x-team-id`、`x-agent-id`、`x-task-id`，使新会话与 Claude Code 一样进入交互式资产关联。首次请求前需切到 Plan 模式，以便 Codex 接收 `request_user_input` 表单。

只有自动化测试、CI、健康检查或无人值守诊断需要避免交互表单时，才额外预填 Team、Agent 和 Task Header。预填后 Proxy 会自动关联并跳过表单；这是测试与运维手段，不是面向用户的默认接入方式。

### 5. 最小验收清单

1. 启动 Codex 时 `/models` 不再报 404。
2. Codex `/responses` 返回 HTTP 200，日志中的上游为 `https://chatgpt.com/backend-api/codex/responses`。
3. Proxy 日志显示 sessionInit 成功、`totalBlockCount=4`、`tdai-recorder:write-l0`。
4. Claude Code 正常回答，Memory Bridge 地址使用 `127.0.0.1:8097`，`atomic/search` 返回 `code=0`。
5. 未带 Memory User Key 请求 `/codex/default/v1/models` 时返回 HTTP 401。
6. Codex 新会话在 Plan 模式弹出资产关联表单；选择后日志显示对应 Team 与 Agent 初始化成功。

### 6. Hook 与 MCP 收尾

确认 Proxy 自动注入和 L0 写入后，可解除旧 TDAI `UserPromptSubmit`、`SessionEnd` Hook 注册，避免重复注入与重复归档。先保留 Hook 文件和客户端配置备份。Memory MCP 提供显式检索能力，可按需保留。

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
requires_openai_auth = true

[model_providers.tdai.http_headers]
x-tdai-user-key = "<memory-user-key>"
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
