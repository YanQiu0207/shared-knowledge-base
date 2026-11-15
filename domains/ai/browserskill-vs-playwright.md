---
status: superseded
source: Tencent/BrowserSkill 官方 README；Playwright 官方入门文档
source_version: accessed 2026-11-15；文档快照，未固定发布版本
applies_to: AI Agent 浏览器操作工具选型、登录态复用、前端探索与自动化回归的职责划分
excludes: 性能与稳定性排名、生产验收、全量 API 兼容判断、既有测试脚本的直接迁移承诺
---

# BrowserSkill 与 Playwright：替代边界与选型

**状态**：已被替代（2026-11-15）。当前说明与选型统一维护在 [AI 浏览器工具目录](../ai-tools/browser/index.md)；下文保留为历史快照，不再同步维护。

## 结论

BrowserSkill 可以替代部分 AI Agent 浏览器操作工具的用途，但不应据此直接替换项目中的 Playwright Test 回归测试和 CI 门禁。

两者能力有交集，侧重点不同：BrowserSkill 面向「让 AI 使用已有登录态的真实浏览器」，Playwright Test 面向「通过测试运行器、断言、隔离和报告重复验证软件」。这是基于官方能力说明的选型建议，不是实测优劣结论。[1][2]

## 名称与比较范围

- **BrowserSkill**：腾讯开源的浏览器自动化工具，通过 `bsk` CLI、daemon 和浏览器扩展连接浏览器；Agent 可通过 shell 或 MCP 使用。[1]
- **Playwright 与 Playwright Test**：不要把 Agent 使用的 Playwright 浏览器操作入口，与项目内的 Playwright Test 测试体系混为一谈。本文分别讨论「操作用途替代」与「测试体系替代」，不主张 API 或脚本可直接兼容。

## 能力与职责对比

| 维度 | BrowserSkill | Playwright Test |
| --- | --- | --- |
| 官方定位 | 将 AI Agent 连接到用户的浏览器，使用现有登录态 | 现代 Web 应用的端到端测试框架 |
| 浏览器范围 | 官方支持 Chrome、Microsoft Edge；其他 Chromium 浏览器兼容性不保证 | Chromium、Firefox、WebKit |
| 操作与探索 | 页面读取、点击、填表、拖动、截图、结构化提取；支持请求与控制台等调试证据 | 可编写端到端测试，并使用测试工具检查失败与执行结果 |
| 人机协作 | 独立 Agent Window、人工接管、显式借用已有标签页 | 本文不评价其人机共享控制体验 |
| 回归测试基础设施 | 本次查阅不足以证明可等价替代 Playwright Test 的完整测试体系 | 官方提供测试运行器、断言、隔离、并行、报告及本地／CI、有头／无头运行 |

上表依据官方文档。[1][2]「未证明等价」不表示 BrowserSkill 完全不能执行测试，也不表示 Playwright 只能测试、不能自动化日常任务。

## 场景选择

| 任务 | 建议 |
| --- | --- |
| AI 在已登录的网站查资料、填表、操作后台 | 优先评估 BrowserSkill，先用低风险流程验证 |
| AI 探索页面、截图、定位请求或控制台问题 | 可用 BrowserSkill 替代部分浏览器操作入口 |
| 提交代码后自动执行 E2E 回归，结果用于 CI 门禁 | 保留 Playwright Test；探索成功不能代替回归断言通过 |
| 检查 Firefox、WebKit 等跨浏览器兼容性 | 保留 Playwright 对应浏览器项目，不以 Chrome／Edge 操作结果替代 |
| 已有 Playwright 测试资产 | 不因工具功能重叠而整体重写；有具体迁移收益时再逐项验证 |

以上为选型建议，能力依据见 [1][2]。可采用「BrowserSkill 做交互探索与登录态操作，Playwright Test 做可重复回归」的组合，而非二选一。

## 安全与证据限制

1. BrowserSkill 复用真实账号，写操作可能影响真实数据；先限定账号、浏览器配置和任务范围，高影响操作应取得明确授权。
2. 官方说明调试历史可能保留响应正文与字段值，已知敏感信息过滤不保证完整，视频不会自动脱敏；分享证据前需人工检查。[1]
3. 本条目仅核读官方文档，未进行实机性能、稳定性、成功率或长期回归对测，不能断言哪一个更快、更可靠。
4. README 描述当前仓库，扩展商店版本可能滞后；安装或迁移时重新核对 CLI、运行中的 daemon 与扩展版本。[1]
5. 本条目不是现有项目实现的事实源；采用前应重新核读当前官方文档，并验证目标环境与验收需求。

## 来源

- [1] [Tencent/BrowserSkill 官方 README](https://github.com/Tencent/BrowserSkill#readme)：定位、功能、环境要求、隐私边界与更新限制，查阅于 2026-11-15。
- [2] [Playwright 官方入门文档](https://playwright.dev/docs/intro)：Playwright Test 定位、测试基础设施、浏览器范围与运行方式，查阅于 2026-11-15。

沉淀授权：用户于 2026-11-15 明确要求将两者对比写入跨项目知识库；不含项目私有信息。
