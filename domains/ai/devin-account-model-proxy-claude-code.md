---
status: verified
source: 本机 Windows 实测；Devin 官方 API 文档；WncFht/devin2api 项目文档与源码；Claude Code 网关发现问题报告
source_version: devin-2api v0.18.0；Claude Code 2.1.325；2026-11-14
applies_to: 使用 Devin 账号可用模型，通过本机代理接入 Claude Code；Windows 登录启动与故障排查
excludes: 复用 Devin 完整 Agent harness；将会话 API 视作模型补全 API；未授权的凭据共享
---

# Devin 账号模型接入 Claude Code：代理、认证与 Windows 启动

## 结论

- Devin 的模型代理与 Devin Agent harness 是两回事：Claude Code 仍负责自身的工具调用、上下文和执行流程；代理提供模型协议转换。
- 个人访问令牌（PAT）可用于官方会话 API，不代表能用于代理的内部模型接口。本次实测 PAT、另一种组织 API Key 均无法通过代理换票；服务用户的 `cog_` 密钥通过认证。不能据此断言 Devin 改过接口，也不能泛化为所有同类令牌均不可用。
- `devin-2api` 的 Anthropic Messages 兼容端点可接 Claude Code。本次 `swe-2-high` 文本调用成功；底层权重、工具调用、长上下文和其他模型未逐项验证。
- Windows 重启会结束普通后台进程。用任务计划程序的「用户登录时」触发可恢复服务；自动重启崩溃进程则需要另行配置看门狗或服务管理器。

## 认证与排查

| 凭据或链路 | 本次证据 | 边界 |
| --- | --- | --- |
| PAT → 官方 `/v1/sessions` | 创建测试会话成功 | 会话 API 是运行 Devin 任务，不是模型补全接口 |
| PAT / 组织 API Key → 代理的内部换票接口 | 返回 `401 invalid api key` | 仅限本次账号、凭据及代理版本，不能断言接口变更 |
| `cog_` 服务用户密钥 → 代理换票 | 代理账号验证成功，模型列表可读取 | 依赖非官方内部接口，可能随上游变化；账号权限各异 |
| Devin CLI 登录凭据 | 项目文档列为替代来源 | 本次未以它验证代理链路 |

代理项目通过 `GetSelfDevinSessionToken` 换取会话令牌；失败时先区分令牌用途和上游返回，不要将官方会话 API 成功误判为模型接口成功。凭据不得粘贴到聊天、命令行参数或公开仓库；曾暴露的令牌应及时撤销并轮换。

## Claude Code 配置与模型菜单

1. 接入前备份 `~/.claude/settings.json`，保留原配置及回滚路径。通过代理时检查 `ANTHROPIC_BASE_URL`、认证方式、模型 ID 和已有自定义请求头；不要把代理上游密钥当作客户端密钥公开。
2. 网关的 `/v1/models` 可提供账号可见的模型目录。设置 `CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY=1` 后，本次用户反馈 `/model` 菜单出现了更多模型；未逐个核对全部模型是否出现或可调用。
3. 曾有 Claude Code 较早版本的问题报告称，设置 `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` 会阻止模型发现；本次为排查而移除了该变量。移除可能恢复其他非必要流量，当前版本是否仍受该问题影响未单独验证。
4. `ANTHROPIC_DEFAULT_FABLE_MODEL`、`ANTHROPIC_DEFAULT_OPUS_MODEL`、`ANTHROPIC_DEFAULT_SONNET_MODEL`、`ANTHROPIC_DEFAULT_HAIKU_MODEL` 等别名配置与显示名称可能覆盖或混淆菜单。若把所有别名映射到同一 ID，菜单项并不代表调用不同模型；模型发现和别名映射应分别核验。
5. `/model` 显示的是客户端选用的模型标识，不是底层权重的独立证明。Claude Code 注入的身份提示可能与代理模型 ID 不一致；不要将模型自述当作权重验证。
6. 各模型上下文窗口可能不同，代理目录中的模型元数据可作配置参考；固定全局窗口时不要假定对所有模型都适用。切换模型后应检查真实限制与自动压缩配置。

## Windows 启动与看门狗

- 登录触发任务负责启动，不等于看门狗；进程运行中崩溃后是否自动恢复，取决于是否另有监控、服务恢复设置或定期健康检查。
- 本次使用已有的本机通用任务配置管理器注册登录任务，再手动触发并检查健康接口和模型列表。未做真实重启验收。
- 本机管理器会按配置双向同步其命名前缀下的任务；同步前必须比较系统任务与配置，避免删除未列出的任务。这是该管理器的行为，不是 Windows 任务计划程序的通用规则。
- 本机 TencentDB Agent Memory 使用专用脚本定期检查服务并按需拉起；该专用看门狗不能直接视作通用进程看门狗。`pythonw.exe` 可避免 Python 控制台窗口；PowerShell 启动任务仍可能闪窗，本次未做真实登录验证。
- 登录启动任务应使用最小权限和本机监听；检查工作目录、状态数据库位置、启动失败日志及账号凭据读取权限。不要将无认证的管理面板或接口暴露到局域网或公网；即使仅绑定回环地址，也需考虑同机其他用户访问。

## 相关踩坑

- [Opus 搭配 ScheduleWakeup 返回 400](../../issues/devin-proxy-opus-schedule-wakeup-invalid-argument.md) — 本次禁用该工具后文本请求成功，具体上游拒绝规则未确认。

## 相关条目

- [本地 LLM 代理出网面审计](local-llm-proxy-egress-audit.md) — devin-2api 源码出网清单：仅 base_url 与 GitHub 自更新，无隐蔽上传；空密码面板开放的边界。

## 来源与证据

- [devin2api 项目与认证说明](https://github.com/WncFht/devin2api)；[代理账号配置](https://github.com/WncFht/devin2api/blob/main/docs/devin-accounts.md)；[Claude Code 接入指南](https://github.com/WncFht/devin2api/blob/main/docs/client-setup.md)。
- [Devin API Overview](https://docs.devin.ai/api-reference/overview)：区分服务用户凭据和个人访问令牌。
- [Claude Code 模型配置](https://code.claude.com/docs/en/model-config)；[网关发现与非必要流量选项的历史问题报告](https://github.com/anthropics/claude-code/issues/61112)。
- 本次本机执行证据：服务健康接口正常；模型列表可读取；Claude Code 文本请求返回 `OK`；登录任务手动触发结果为 `0`。所有这些均不等于模型、工具调用或系统重启的全面验收。
