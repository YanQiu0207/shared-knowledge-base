---
status: provisional
source: Playwright 官方入门文档；美团技术团队 Tabbit CLI 技术文章
source_version: accessed 2026-11-15；官方文档未固定版本；美团文章发布于 2026-10-30
applies_to: 浏览器自动化、Agent 操作引擎与 E2E 回归测试的职责划分
excludes: 与上层 Agent 工具的性能排名、既有脚本的迁移兼容承诺
---

# Playwright 与 Playwright Test

## 结论

不要把 Playwright 仅理解成测试工具：它可以作为 Agent 工具的浏览器操作引擎；Playwright Test 则提供测试运行器、断言、隔离、并行和报告等端到端测试基础设施。[1][2]

## 能力与边界

- Playwright Test 支持 Chromium、Firefox、WebKit，可在本地或 CI 中以有头或无头方式运行。[1]
- Tabbit CLI 复用 Playwright 的定位器、自动等待、可操作性检查、输入和断言，同时适配页面观察与返回结果；这属于上层集成，不是弃用 Playwright。[2]
- 「使用 Playwright」可能指自动化库、Agent 的工具入口或 Playwright Test 测试资产，讨论替换前应明确对象。
- Playwright 也能自动化日常操作，不能把「Agent 操作」与「Playwright」视为互斥选项。

## 使用建议

已有测试资产、跨浏览器兼容性检查与 CI 回归门禁继续使用 Playwright Test。Agent 探索成功不能代替固定断言的回归通过；也不应仅因出现新入口而重写现有测试。完整路由见 [对比与选型](comparison.md)。

## 证据限制

本条目基于官方资料，未做与 BrowserSkill、Tabbit CLI 的实机对测，不作性能或稳定性优劣判断。

## 来源

- [1] [Playwright 官方入门文档](https://playwright.dev/docs/intro)，查阅于 2026-11-15。
- [2] [美团技术团队《为 Agent 构建浏览器工具：Tabbit CLI 的设计与实践》](https://mp.weixin.qq.com/s/4Cgmh9VPxao-fzx4jW0F9Q)，薄佑思，2026-10-30，查阅于 2026-11-15。
