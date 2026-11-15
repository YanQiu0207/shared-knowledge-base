---
status: provisional
source: Tencent/BrowserSkill 官方 README；Playwright 官方入门文档；美团技术团队 Tabbit CLI 技术文章
source_version: accessed 2026-11-15；美团文章发布于 2026-10-30；未固定工具发布版本
applies_to: Agent 浏览器入口、底层操作引擎与回归测试体系的跨项目选型
excludes: 实机性能与稳定性排名、生产验收、API 兼容与脚本直接迁移承诺
---

# BrowserSkill、Tabbit CLI 与 Playwright：关系与开发选型

## 结论

不要统一指定一个赢家。先区分「Agent 操作入口」「底层自动化引擎」「回归测试体系」，再按目标浏览器、登录态与验收任务选择。以下建议基于官方文档，不是实机排名。

## 工具关系

| 工具 | 所处层次 | 浏览器与约束 | 详情与事实来源 |
| --- | --- | --- | --- |
| BrowserSkill | Agent 浏览器操作入口 | 官方支持 Chrome／Edge，复用已有登录态；底层是否依赖 Playwright 本次未确认 | [说明](browserskill.md)、[官方 README](https://github.com/Tencent/BrowserSkill#readme) |
| Tabbit CLI | Agent 浏览器操作入口，内部复用 Playwright | 本次官方文章描述面向 Tabbit，依赖其浏览器内置运行时与访问控制；不能据此认定支持普通 Chrome | [说明](tabbit-cli.md)、[官方文章](https://mp.weixin.qq.com/s/4Cgmh9VPxao-fzx4jW0F9Q) |
| Playwright / Playwright Test | 自动化引擎 / 测试体系 | Playwright Test 支持 Chromium、Firefox、WebKit，以及本地／CI、有头／无头运行 | [说明](playwright.md)、[官方文档](https://playwright.dev/docs/intro) |

BrowserSkill 与 Tabbit CLI 在 Agent 操作入口层有交集；Tabbit CLI 与 Playwright 则是上层集成与底层引擎的关系。更换 Agent 的操作入口，不等于移除底层引擎，更不等于可以删除已有回归测试。

## 开发选型建议

| 任务 | 建议优先选择 |
| --- | --- |
| Agent 操作已登录的 Chrome／Edge 后台 | 评估 BrowserSkill，先验证低风险流程 |
| 已使用 Tabbit，希望程序化连续操作、断言与中断恢复 | 评估 Tabbit CLI，不额外假设可控制普通 Chrome |
| Agent 探索页面、截图、联调 | 按现有浏览器与工具能力选择，不以文章评测直接判定优胜 |
| 已有 Playwright 测试、跨浏览器回归与 CI 门禁 | 保留 Playwright Test |
| 新项目选择操作入口 | 在相同环境、模型与任务下做最小对测，再决定 |

不建议仅因新工具出现而迁移浏览器、重写测试或增加并行工具栈。可采用「Agent 入口做探索与登录态操作，Playwright Test 做固定断言回归」的组合。

## 最小试用验收

选择测试账号与可恢复数据，执行「打开本地应用 → 操作表单 → 断言保存成功 → 检查失败证据 → 模拟响应中断并核对是否重复提交」。记录业务结果、误操作、虚假成功、恢复能力、模型输入和耗时，而非只看点击是否正常返回。

## 共通限制

- 程序成功不等于业务成功；提交后需核对实际结果。
- 未收到响应不等于未执行；写操作先核对状态，不能盲目重试。
- 复用真实登录态意味着真实数据风险，页面范围限制不等于账号隔离。
- 未对三者做实机性能、成功率或稳定性对测；Tabbit 文章的 47.2% 是特定内部比较的总输入降幅，不是三者排名或成本承诺，详见其说明条目。

沉淀授权：用户于 2026-11-15 明确要求按 `ai-tools/browser` 两级目录整理工具说明与对比；内容已泛化，不含项目私有信息。
