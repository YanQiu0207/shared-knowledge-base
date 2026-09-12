---
scope: cross-project
status: provisional
source: official documentation from Zhipu BigModel and DeepSeek; CN tier prices from third-party reports (Zhihu, 36Kr)
source_version: 2026-09-12
applies_to: choosing between Zhipu GLM Coding Plan (CN) and DeepSeek pay-as-you-go API for coding-agent use
excludes: non-CN regional plans, model-quality conclusions without controlled evaluation, third-party relay reliability
---

# GLM Coding Plan 与 DeepSeek API 选型：订阅额度 vs 按量计费

## 结论

- 选型取决于用量模式：每天重度使用选订阅 Plan（成本封顶，重度时比按量便宜约一半）；低频使用（如一周 1 天全天）选按量 API（账单打平，无窗口限流，无闲置额度浪费）。
- 智谱 Coding Plan（国区）：Lite ¥49 / Pro ¥149 / Max ¥469 每月，积分制；Lite 每 5 小时 2,000 积分（滚动刷新）+ 每周 10,000 积分；额度耗尽后等待刷新，不扣账户余额；仅限官方支持工具内调用才享额度。
- DeepSeek API：按量计费、无月费；deepseek-flash 空闲时段输入未命中 1 元/M、输出 4 元/M，工作日 9–12、14–18 点高峰翻倍；deepseek-v4-pro 约为 Flash 的 4.5 倍价；提供 Anthropic 兼容端点，Claude Code 可直连。

## 用量与价格对照

| 服务 | 计费 | 额度 / 限制 | 适合场景 |
| --- | --- | --- | --- |
| 智谱 Lite | ¥49/月 | 2,000 积分/5 小时（滚动）+ 1 万积分/周；高峰（工作日 14–18 点）积分 1 倍消耗，其余 0.5 倍 | 每天重度使用、可接受窗口限流 |
| 智谱 Pro | ¥149/月 | 12,000 积分/5 小时 + 6 万积分/周 | 高频复杂项目 |
| 智谱 Max | ¥469/月 | 28,000 积分/5 小时 + 14 万积分/周 | 重度使用 |
| DeepSeek Flash | 按量 | 无窗口限制；上下文 1 M；并发 2,500 | 低频、波动用量 |
| DeepSeek V4 Pro | 按量，约 Flash 4.5 倍价 | 上下文 1 M；并发 500 | 临时切换更强模型 |

套餐内模型：GLM-5.3 与 GLM-5.3-Flash。官方「可用额度参考」给出 Lite 周额度折合 GLM-5.3 约 0.48–0.97 亿 token（95% 缓存命中）。

## 决策框架

1. 先判断用量模式：每天重度 → 订阅 Plan；一周 1 天全天 → 按量 API。
2. 按月账单决策：Plan 是固定支出，API 可先按量用一个月拿到真实账单再对比。
3. 关键差异：
    - Plan 的 5 小时滚动窗口是全天高强度使用的真实瓶颈，会「跑着跑着没额度」
    - Plan 的周额度 7 天刷新、不结转，低频使用时大量闲置
    - API 无用量上限，但 agent 失控会持续烧钱，建议设置余额提醒
4. 错峰：双方高峰时段仅工作日，周末全天可享低价（DeepSeek 半价、智谱积分 0.5 倍）。
5. 估算参考（假设 agent 典型结构 90% 缓存命中 + 5% 输出）：一周 1 天全天约消耗 2,000–4,000 万 token，用 Flash 空闲时段约 8–16 元/天、月 4 天约 32–64 元，与 Lite 的 ¥49/月打平；此时按量更优（无窗口限流、不用不花钱）。

## 证据与限制

- [智谱 Coding Plan 套餐概览（官方文档）](https://docs.bigmodel.cn/cn/coding-plan/overview)
- [DeepSeek 模型与价格（官方文档）](https://api-docs.deepseek.com/zh-cn/quick_start/pricing/)
- 国区三档价格（¥49/149/469）来自第三方报道（知乎、36 氪），官方概览页未列价格，订阅前以结算页为准
- 订阅套餐之间的横向对比见 [coding-plan-subscription-selection.md](coding-plan-subscription-selection.md)
- 本条目状态为 `provisional`：价格、积分系数与高峰时段可能变化；「一天全天 token 消耗」为估算值，用于选型判断而非精确账单
