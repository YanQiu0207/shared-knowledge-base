---
scope: cross-project
status: provisional
source: official documentation from OpenCode, Z.AI, and Anthropic
source_version: 2026-07-21
applies_to: comparing OpenCode Go, OpenCode Zen, Z.AI international GLM Coding Plan, and Claude Pro for coding-agent use
excludes: exchange-rate calculations, undocumented payment-region guarantees, model-quality conclusions without controlled evaluation, and third-party proxy reliability
---

# Coding Plan 订阅选型：OpenCode Go、Zen、智谱国际区与 Claude Pro

## 结论

- **OpenCode Go**：$5 首月、之后 $10/月；面向开源 Coding 模型，包含 GLM、Kimi、MiniMax、Qwen、DeepSeek 等模型。其官方接入方式主要是 OpenCode 的 Provider 流程。
- **OpenCode Go 提供 API 端点**：`https://opencode.ai/zen/go/v1`，主要是 OpenAI Chat Completions 兼容接口。它不是 Anthropic Messages 接口，因此不能直接把该 URL 当作 Claude Code 的 `ANTHROPIC_BASE_URL` 使用；接入 Claude Code 需要协议转换层，第三方代理的兼容性和条款风险需单独评估。
- **OpenCode Zen**：不是订阅套餐，而是按请求用量计费的预付费网关；适合偶尔使用 GPT、Claude 等高端模型，不适合作为高强度 Coding 的固定月费替代品。
- **智谱国际区 GLM Coding Plan**：Lite $18/月、Pro $72/月、Max $160/月；官方支持 Claude Code 和 OpenCode，并提供 Anthropic 兼容端点。Lite 价格接近 Claude Pro，主要价值在于直接使用 GLM 模型，不在于低价。
- **Claude Pro**：美国月付 $20，包含 Claude Code；价格只比智谱国际区 Lite 高 $2，但模型生态和 Claude Code 原生兼容性更完整。

## 用量与价格对照

| 服务 | 月费 | 官方用量口径 | 适合场景 |
| --- | ---: | --- | --- |
| OpenCode Go | $5 首月，之后 $10 | 5 小时 $12、每周 $30、每月 $60 的用量值；不同模型对应不同请求数 | 低成本使用多种开源 Coding 模型 |
| OpenCode Zen | 无固定月费 | 按请求计费，可充值并设置消费上限 | 偶尔调用高端模型，按实际用量付费 |
| 智谱国际 Lite | $18/月 | 约 80 prompts/5 小时、400 prompts/周 | 想在 Claude Code 中直接使用 GLM |
| 智谱国际 Pro | $72/月 | 约 400 prompts/5 小时、2,000 prompts/周 | 高频使用 GLM Coding |
| 智谱国际 Max | $160/月 | 约 1,600 prompts/5 小时、8,000 prompts/周 | 重度 GLM Coding |
| Claude Pro | $20/月，或 $200/年 | 每 5 小时重置，并有周限额；消息数取决于模型、上下文和任务长度 | 原生 Claude Code 与 Claude 模型 |

两家的 prompt/request 定义不同，不能直接将 OpenCode Go 的请求数与智谱的 prompt 数一一换算。智谱还说明 GLM-5.2 在高峰期按 3 倍、非高峰期按 2 倍消耗额度，限时低峰优惠除外。

## 决策建议

1. 主要使用 GLM：先比较智谱中国区能否正常购买；抢不到时，智谱国际 Lite 是兼容性直接但价格较高的备用方案。
2. 需要 Claude Code 原生体验：Claude Pro 与智谱国际 Lite 价格接近，优先 Claude Pro。
3. 想低成本混用开源模型：OpenCode Go 更划算，但优先在 OpenCode 等兼容工具中使用，不要默认它能直连 Claude Code。
4. 只是偶尔需要 GPT/Claude：使用 OpenCode Zen，并设置消费上限，避免固定订阅浪费。
5. 任何订阅购买前，先确认账号地区、支付方式、自动续费和退款规则；不要仅凭宣传页的「支持某工具」推断协议完全兼容。

## 证据与限制

- [OpenCode Go 官方页面](https://opencode.ai/go)
- [OpenCode Go 官方文档](https://opencode.ai/docs/go/)
- [OpenCode Zen 官方页面](https://opencode.ai/zen)
- [Z.AI Coding Plan 官方文档](https://docs.z.ai/devpack/overview)
- [Z.AI 快速开始与工具接入](https://docs.z.ai/devpack/quick-start)
- [Claude Pro 官方说明](https://support.claude.com/en/articles/8325606-what-is-the-pro-plan)
- [Claude 官方套餐价格](https://www.anthropic.com/pricing)

本条目状态为 `provisional`：价格、模型列表、限额、支付可用性和协议支持可能变化。购买前应重新核对官方页面；第三方协议转换代理不属于上述官方服务保证范围。
