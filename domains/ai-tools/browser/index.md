# 浏览器工具

## 结论

BrowserSkill 与 Tabbit CLI 是 Agent 浏览器操作入口；Playwright 既能提供底层自动化能力，也通过 Playwright Test 提供回归测试体系。Tabbit CLI 复用 Playwright，但本文所据官方文章仅描述对 Tabbit 浏览器的支持，不应视为通用 Chrome 控制工具。

开发选型按任务划分：Chrome／Edge 登录态操作评估 BrowserSkill，已使用 Tabbit 时评估 Tabbit CLI，跨浏览器回归与 CI 门禁保留 Playwright Test。事实来源、限制和建议见下列条目。

## 工具说明

| 工具 | 定位 | 说明 |
| --- | --- | --- |
| BrowserSkill | Agent 连接已有 Chrome／Edge，复用登录态 | [工具说明](browserskill.md) |
| Tabbit CLI | Agent 操作 Tabbit 浏览器，内部复用 Playwright | [工具说明](tabbit-cli.md) |
| Playwright | 通用浏览器自动化能力与 Playwright Test 测试体系 | [工具说明](playwright.md) |

## 对比与选型

- [三者的关系、替代边界与开发选型](comparison.md)
