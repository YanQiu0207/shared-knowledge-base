---
status: provisional
source: OpenAI Codex and Anthropic Claude Code official documentation plus linked GitHub repositories
source_version: 2026-07-19
applies_to: local coding-agent workflows that need native delegation or cross-product agent invocation
excludes: hosted agent platforms without local CLI or MCP access and production use without independent security review
---

# Codex 与 Claude Code 调用其他 Coding Agent

## 结论

调用其他 Coding Agent 分为两类：

1. **原生子 Agent**：由 Codex 或 Claude Code 在自身产品内创建隔离上下文的工作线程。
2. **跨产品 Agent**：一个 Coding Agent 通过非交互 CLI、Skill 或 MCP 调用另一个 Coding Agent。

默认选择原生子 Agent。只有需要不同模型家族交叉审查、特定产品能力或统一多 Agent 编排时，才引入跨产品调用。

## 能力边界

| 方式 | 作用 | 不适合 |
| --- | --- | --- |
| 原生子 Agent | 并行探索、测试、审查和摘要 | 获得另一模型家族的独立判断 |
| Skill 调用 CLI | 封装稳定、可复用的单一工作流 | 复杂的长期会话和多 Agent 通信 |
| MCP | 暴露结构化工具、会话和外部系统 | 只需一条本地命令的简单任务 |
| Agent 编排层 | 统一启动、并行、跟踪和聚合多种 CLI Agent | 低频、单 Agent 任务 |
| 协调层 | 为已运行的 Agent 提供消息、任务或文件预约 | 替代 Agent 启动器 |

Skill 和 MCP 可以组合：Skill 定义何时调用及操作流程，MCP 提供结构化执行接口。

## Codex 内的调用方式

### 原生子 Agent

Codex 可按用户的直接指令，或按适用的 `AGENTS.md` 和 Skill 指令委派子 Agent。适合的起步任务是代码探索、测试、故障分类和审查。多个 Agent 同时写代码可能增加冲突和协调成本。

示例提示：

```text
启动 3 个并行子 Agent：分别检查安全风险、测试缺口和可维护性。
等待全部完成后，按类别汇总，并附文件位置。
```

### 调用 Claude Code

最小实现是创建 Skill，让 Codex 调用 Claude Code 的非交互模式：

```powershell
claude -p "审查当前 git diff，只报告能通过代码证据确认的问题" `
    --output-format json
```

Skill 应明确工作目录、权限、超时、输出协议和会话恢复方式。只做交叉审查时，应禁止外部 Agent 写入代码。

## Claude Code 内的调用方式

### Subagent 与 Agent Teams

Claude Code Subagent 在独立上下文中工作，并将结果返回主会话。Agent Teams 则运行多个独立 Claude Code 实例，支持共享任务和直接通信，但它是实验功能，成本和协调开销高于 Subagent。

### 调用 Codex

两种常用方式：

1. 通过 Skill 包装 `codex exec`，适合日常审查、咨询和边界清晰的实现任务。
2. 通过官方 `codex mcp-server` 暴露的 `codex` 和 `codex-reply` 工具，创建和继续 Codex 会话。该接口当前为实验性能力。

将 Codex MCP Server 添加到 Claude Code：

```bash
claude mcp add --scope user codex -- codex mcp-server
```

GitHub 上的 [`skills-directory/skill-codex`](https://github.com/skills-directory/skill-codex) 是一个已有的 Claude Code Skill / Plugin，通过 `codex exec` 及会话恢复调用 Codex。

## 开源方案选型

| 项目 | 定位 | 适合场景 | 主要限制 |
| --- | --- | --- | --- |
| [`skills-directory/skill-codex`](https://github.com/skills-directory/skill-codex) | Claude Code 调用 Codex 的 Skill / Plugin | 单向委派、审查、咨询 | 不是通用多 Agent 编排器 |
| [`mkXultra/ai-cli-mcp`](https://github.com/mkXultra/ai-cli-mcp) | 后台调用 Claude、Codex、Gemini 等 CLI 的 MCP Server | 跨产品并行执行 | 默认使用绕过权限或沙箱的参数，必须先安全审核 |
| [`coder/agentapi`](https://github.com/coder/agentapi) | 将多种 Coding Agent 包装成统一 HTTP API | 自建编排平台、统一 UI 或会话管理 | 不是可直接触发的 Codex / Claude Code Skill |
| [`Dicklesworthstone/mcp_agent_mail`](https://github.com/Dicklesworthstone/mcp_agent_mail) | 多 Agent 消息、搜索和文件预约层 | 已启动 Agent 之间的协作 | 不负责启动 Agent |

外部项目的 Stars、版本、参数和默认行为会变化。采纳前应审查当前代码、发布物、权限参数和最小动态用例，不能只看 README 或 Stars。

## 最小落地方案

第一阶段只开放三类只读任务：

1. 第二模型代码审查。
2. 方案交叉验证。
3. 故障假设的独立分析。

参考拓扑：

```text
Claude Code
    └── Skill
        └── codex exec --sandbox read-only

Codex
    └── Skill
        └── claude -p --output-format json
```

稳定后再增加多轮会话、后台并行和代码写入。写入模式必须配合明确的写集、Git Worktree、机器验证和最终独立审查。

## 安全和运行约束

- 只读任务默认禁止写文件、安装依赖和修改 Git 状态。
- 不将 `--dangerously-skip-permissions` 或绕过沙箱的参数设为公共默认值。
- 外部 Agent 只获得目标任务所需的最小目录、工具和凭证。
- 限制递归委派深度，避免 Agent 相互调用形成无界扩散。
- 并行写入前声明写集和所有权；无法证明无冲突时，使用独立 Worktree。
- 记录 Agent、模型、会话 ID、权限、超时、退出码和结果摘要，便于审计与失败恢复。
- 将跨 Agent 输出视为建议，不视为已验证事实；最终结论仍需代码、测试和运行证据。

## 证据与限制

- [Codex Subagents](https://developers.openai.com/codex/subagents)
- [Use Codex with the Agents SDK](https://developers.openai.com/codex/guides/agents-sdk)
- [Claude Code Subagents](https://code.claude.com/docs/en/sub-agents)
- [Claude Code Agent Teams](https://code.claude.com/docs/en/agent-teams)
- [Run Claude Code programmatically](https://code.claude.com/docs/en/headless)
- [Connect Claude Code to tools via MCP](https://code.claude.com/docs/en/mcp)

本条目的证据等级为 `provisional`：官方文档能证明原生子 Agent、非交互 CLI 和 MCP 接入能力；第三方编排项目的安全性、稳定性与 Windows 兼容性仍需在实际环境中独立验证。
