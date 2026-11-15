---
status: provisional
source: Tencent/BrowserSkill 官方 README
source_version: accessed 2026-11-15；当前仓库文档，未固定发布版本
applies_to: Agent 操作已有 Chrome／Edge、复用登录态与人机协作
excludes: 生产验收、性能与稳定性排名、与 Playwright 的 API 兼容保证
---

# BrowserSkill

## 结论

BrowserSkill 是腾讯开源的 Agent 浏览器操作工具，通过 `bsk` CLI、daemon 与浏览器扩展连接用户的浏览器，复用已有登录态。官方支持 Chrome、Microsoft Edge；其他 Chromium 浏览器兼容性不保证。[1]

## 能力与边界

- Agent 可通过 shell 或 MCP 使用，工具本身不替用户选择 Agent 和模型。[1]
- 支持页面读取、点击、填表、拖动、截图、结构化提取，以及请求、响应正文和控制台等调试证据。[1]
- 使用独立 Agent Window，支持人工接管；操作已有用户标签页需要显式借用。[1]
- 本次资料核读不足以确认其底层是否依赖 Playwright，不能从 Tabbit 的架构类推。
- 功能重叠不表示测试脚本兼容，也不足以证明能等价替代 Playwright Test 的完整回归体系。

## 使用建议

日常使用 Chrome／Edge，且需要 Agent 操作现有登录态时，优先评估本工具；先用低风险流程验证，不以能点击或截图作为业务成功证据。完整路由见 [对比与选型](comparison.md)。

## 安全与限制

真实账号的写操作可能影响真实数据，应限定账号与任务范围。官方说明调试证据可能保留正文与字段值，敏感信息过滤不保证完整，视频不会自动脱敏；分享前应人工检查。[1]

README 描述当前仓库，扩展商店发布可能滞后；采用时重新核对 CLI、运行中的 daemon 和扩展版本。[1] 本条目未做实机稳定性、性能或成功率测试。

## 来源

- [1] [Tencent/BrowserSkill 官方 README](https://github.com/Tencent/BrowserSkill#readme)，查阅于 2026-11-15。
