---
status: verified
source: Windows 本机请求捕获与回放对照；WncFht/devin2api 源码和排查文档
source_version: devin-2api v0.18.0；Claude Code 2.1.325；2026-11-15
applies_to: Claude Code 经 devin-2api 使用 claude-opus-5-5-medium 时返回 invalid_argument
excludes: 所有 Claude 模型或其他代理均存在相同问题；断言上游具体拒绝规则；账号套餐权限判断
---

# Devin 代理下 Opus 遇到 ScheduleWakeup 返回 400

## 结论

特定实测环境中，Claude Code 默认工具集含 `ScheduleWakeup` 时，`claude-opus-5-5-medium` 通过 devin-2api 请求返回 `400 invalid_argument`。**禁用该工具后，同一客户端和模型的简单文本请求成功。** 这是可复现的兼容性触发条件，不足以认定代理或上游的具体缺陷，也不能据此建议升级账号。

## 排查证据

1. 代理直接发送最小文本请求成功；Claude Code 在无工具、仅 `Read`、常用文件与终端工具等组合下成功。默认完整工具集失败；`swe-2-high` 的默认工具集成功。
2. 禁用已配置的 MCP 服务后默认工具集仍失败，不能直接归因于 MCP。对成功、失败的真实请求做工具集合二分：在成功集合中单独加入 `ScheduleWakeup` 即复现 400；其他被单独测试的候选工具未复现。
3. 实际 Claude Code 请求使用 `--disallowedTools ScheduleWakeup` 后成功；将 `permissions.deny` 加入该工具后，经本机启动脚本发起的简单 Opus 请求也成功。
4. 将 `ScheduleWakeup` 的参数 Schema 改为空对象后，回放成功；逐个保留单字段也成功。**尚未确定具体是哪个字段组合、Schema 转换、工具总数、请求大小或其他上游约束导致失败**，因此不应声称已找到底层规则。

## 临时处置

在新会话中单次禁用：

```powershell
claude --model claude-opus-5-5-medium --disallowedTools ScheduleWakeup
```

若确认长期不需要该工具，可备份 `~/.claude/settings.json`，在已有 `permissions.deny` 数组中追加 `ScheduleWakeup`，保留原有权限规则。新会话验证 Opus 和常用工具；此方案会影响所有使用该配置的模型，且会禁用 `ScheduleWakeup`，不是上游兼容性修复。

需区分默认模型设置：`ANTHROPIC_MODEL` 存在时会影响新会话的模型选择；`/model` 在当前会话切换成功不代表新会话一定沿用该模型。

## 排查隐私与边界

- 代理调试日志可能记录完整请求、系统提示、项目指令、工具 Schema 和响应；必须获得用户同意，使用最小测试，并在结束后恢复原有日志配置。
- 调试记录的删除或保留应经用户确认；不要在聊天、公开 Issue 或知识库粘贴原始请求、账号信息、令牌或私人路径。
- 测试成功只证明所测文本请求可用；真实工具调用、其他模型版本及后续版本是否正常仍须另行验证。

## 来源

- [devin-2api 排查指南](https://github.com/WncFht/devin2api/blob/main/docs/upstream-debug-playbook.md)。
- 本机同一代理、同一账号和模型的请求二分与实际 Claude Code 启动验证；上游只返回笼统的 `invalid_argument`，未提供具体拒绝字段。
