---
scope: cross-project
status: provisional
source: Kimi 开放平台官方文档、OpenAI Codex 官方配置文档与社区实测教程
source_version: 2026-07-21
applies_to: 想在 Claude Code 或 Codex 中改用 Kimi 模型（替代官方 Claude/GPT）省 token 的本地 coding agent 工作流
excludes: Kimi 模型质量与基准评测、非 Kimi 厂商的协议兼容性、Kimi Code CLI 相对原版 Codex 的特性同步情况
---

# Kimi 接入 Claude Code 与 Codex 的协议兼容差异

## 结论

Kimi 官方为 Claude Code 专门提供了 **Anthropic 兼容端点**，Claude Code 可零依赖直连；但 Kimi **未提供 OpenAI Responses 兼容端点**，而 Codex 自 2026-02 起只支持 Responses API 并移除了 Chat Completions 支持，因此 Codex **不能直连** Kimi 官方端点，必须经本地转译层（如 LiteLLM）或第三方云端 Responses 兼容端点中转。

常见误区是「Kimi 是 OpenAI 兼容协议，所以 Claude Code 用不了、Codex 能直接用」——实际情况正好相反：Claude Code 有官方直连方案，Codex 反而需要转译。

## 协议兼容矩阵

| 工具 | 原生协议 | 直连 Kimi 官方端点 | 方案来源 | 可靠度 |
| --- | --- | --- | --- | --- |
| Claude Code | Anthropic Messages | ✅ `api.moonshot.cn/anthropic` | Kimi 官方文档 | 官方，较可靠 |
| Codex | OpenAI Responses（2026-02 起删掉 Chat Completions） | ❌ `api.moonshot.cn/v1` + `wire_api=responses` 会 404 | 社区教程 + Codex 官方 provider 指南 | 需自建转译 |

## Claude Code 直连 Kimi

将下列变量写入用户级 `~/.claude/settings.json` 的 `env` 字段（长期生效）或终端临时 export：

```json
{
  "env": {
    "ANTHROPIC_BASE_URL": "https://api.moonshot.cn/anthropic",
    "ANTHROPIC_AUTH_TOKEN": "你的_Kimi_API_Key",
    "ANTHROPIC_MODEL": "kimi-k3[1m]",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "kimi-k3[1m]",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "kimi-k3[1m]",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "kimi-k3[1m]",
    "ANTHROPIC_DEFAULT_FABLE_MODEL": "kimi-k3[1m]",
    "CLAUDE_CODE_SUBAGENT_MODEL": "kimi-k3[1m]",
    "ENABLE_TOOL_SEARCH": "false",
    "CLAUDE_CODE_AUTO_COMPACT_WINDOW": "1048576",
    "CLAUDE_CODE_EFFORT_LEVEL": "max"
  }
}
```

关键约束（来自 Kimi 官方文档）：

- 鉴权用 `ANTHROPIC_AUTH_TOKEN`，不是 `ANTHROPIC_API_KEY`；若同时残留 `ANTHROPIC_API_KEY` 会冲突并 401，需先清理。
- `settings.json` 的 `env` 会覆盖终端 export 的同名变量；改配置前先清掉 `env` 里残留的旧 `ANTHROPIC_*`。
- `ENABLE_TOOL_SEARCH` 必须设为 `false`，Kimi 端点不支持该特性。
- `CLAUDE_CODE_AUTO_COMPACT_WINDOW` 需与模型上下文一致：`kimi-k3` 为 1M（`1048576`），`kimi-k2.7-code` 为 256K（`262144`）；设错会过早压缩丢上下文或报超限。
- `/model` 菜单不会显示 Kimi 模型（是内置固定别名列表），以 `/status` 显示的 Base URL 与 Model 为准。

## 模型与思考行为

| 模型 | 思考行为 | 使用要点 |
| --- | --- | --- |
| `kimi-k3` | 默认开启思考 | 开箱即用，1M 上下文，ID 写 `kimi-k3[1m]` |
| `kimi-k2.7-code` | 始终开启思考 | 请求必须显式开启思考，否则报 `400 invalid thinking: only type=enabled is allowed`；高速版 `kimi-k2.7-code-highspeed` 速度约 5~6 倍 |
| `kimi-k2.6` | 思考可选 | 可关闭思考，适合延迟敏感的简单任务 |

切换模型时，必须把配置里所有模型变量值一并替换，不能只改 `ANTHROPIC_MODEL`。

## Codex 接 Kimi 的约束

Codex 官方 provider 框架要求 `wire_api` 只能为 `responses`，且会忽略项目级 `.codex/config.toml` 中的 `model_providers`、`model_provider` 和鉴权重定向（凭据类配置只能写用户级 `~/.codex/config.toml`）。两条社区路径：

**A. 本地 LiteLLM 转译（开源、不加价）**——起本地 LiteLLM，把 Codex 的 Responses 请求转成 Kimi 的 Chat Completions，配置开 `drop_params: true` 过滤 Kimi 不认的字段。Codex 端配置：

```toml
model = "kimi-k3"
model_provider = "kimi_via_router"

[model_providers.kimi_via_router]
name = "Kimi via local LiteLLM"
base_url = "http://127.0.0.1:4000"
env_key = "MOONSHOT_API_KEY"
wire_api = "responses"
```

**B. 第三方云端 Responses 兼容端点**——无需本地服务，但第三方会加价，且需先确认 `/v1/models` 返回中包含目标模型 ID（K3 不一定上架）。

不要把 `base_url = https://api.moonshot.cn/v1` 与 `wire_api = responses` 直接组合，会请求到 Kimi 未提供的 Responses 路径，常见结果 404、请求格式错误或流式中断。

## 选型权衡

目标是「省 token 用 Kimi」时，阻力最小路径是 **Claude Code 直连**（零依赖、官方维护）。坚持用 Codex 则需长期维护本地 LiteLLM 或依赖第三方云端，且原 Codex 的 computer-use、plugins、marketplaces 等特性在切到 Kimi provider 后是否仍可用、效果如何，缺乏公开验证数据，需在实际环境中独立测试。

## 证据与限制

- [在 Claude Code 中使用 Kimi（Kimi 开放平台官方）](https://platform.kimi.com/docs/guide/claude-code-kimi)
- [Kimi K2.6 Quickstart（含 OpenAI 兼容说明）](https://platform.kimi.com/docs/guide/kimi-k2-6-quickstart)
- [Codex CLI Custom Model Providers 指南（wire_api 只剩 responses）](https://codex.danielvaughan.com/2026/04/23/codex-cli-custom-model-providers-configuration-guide/)
- [Codex Configuration Reference（官方）](https://developers.openai.com/codex/config-reference)
- [Kimi K3 接入 Codex：Responses 兼容层配置教程](http://www.lpnh.cn/news/1350099)
- [LiteLLM 转译 Codex 请求](https://docs.litellm.ai/docs/tutorials/openai_codex)

本条目状态为 `provisional`：Claude Code 直连方案来自 Kimi 官方文档，较可靠；Codex 接入方案来自社区教程与 Codex 官方 provider 文档的拼接，未经同环境长期实测。Kimi 端点、模型 ID、Codex 配置项和第三方兼容层界面可能随版本变更，使用前应重新核对官方文档并跑只读小任务验证。
