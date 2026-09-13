---
status: provisional
source: OpenAI Codex and Anthropic Claude Code official documentation plus linked GitHub repositories
source_version: 2026-09-13
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

如果需要在 Codex 会话内结构化调用 Claude，可使用第三方 [`claude-in-codex`](https://github.com/briandconnelly/claude-in-codex) 插件：

```text
codex plugin marketplace add briandconnelly/claude-in-codex
codex plugin add claude-in-codex --marketplace claude-in-codex
```

重启 Codex 后，先调用 `claude_status` 检查 Claude CLI 和认证状态，再调用 `claude_review_changes` 审查当前工作区、暂存区或分支。调用时应显式传入绝对 `workspace_root`，避免 Claude 在错误目录中执行。该插件默认面向只读审查，提供同步、异步和对抗性审查工具；付费工具会把代码和提示发送给 Anthropic，并可能产生调用成本。

### Codex 插件安装排障

`codex plugin marketplace add` 只添加插件市场，不会安装具体插件。添加市场成功后，必须显式指定市场安装插件：

```bash
codex plugin add claude-in-codex --marketplace claude-in-codex
```

也可以使用完整选择器：

```bash
codex plugin add claude-in-codex@claude-in-codex
```

安装完成后，可用 `codex plugin list` 检查插件是否为 `installed, enabled`。插件工具通常在 Codex 进程启动时加载，因此首次安装或升级后需要重启 Codex；否则当前会话的工具列表中可能仍没有 `claude_status` 和 `claude_review_changes`。

如果不需要 MCP 或插件，也可以直接从 Codex 执行 `claude -p`。Claude Code 官方将该模式定义为程序化、非交互调用；脚本或 CI 可考虑使用 `--bare`，减少 Skill、插件、MCP 和自动记忆等外部状态的影响。该方式是「Codex → Shell → Claude Code」，不是 Codex 原生切换 Claude 模型。

注意区分调用方向：`openai/codex-plugin-cc` 是 Claude Code 调用 Codex 的反向方案，不是 Codex 调用 Claude Code 的实现。

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

## Windows 原生终端中的多轮协作

当使用者希望在 VS Code 的 PowerShell 终端中继续运行现有 Claude Code、Codex 等 CLI，并需要 Agent 之间进行多轮提示、等待和复审时，应区分「完整编排器」与「终端自动化运行时」。

### 代表性需求画像

这类选型可用以下需求画像约束候选项目：

1. 运行环境为 Windows，主要入口是 VS Code 内置 PowerShell 终端；不希望为了编排迁移到 WSL，也不希望重新配置 Windows 上已有的 Claude Code、Codex、Git、SSH、Skill、MCP 和认证环境。
2. 必须运行现有的真实 Coding Agent CLI，而不是绕过 CLI、直接用 API 重新实现 Agent；至少支持 Claude Code 和 Codex。
3. 使用者可以像普通终端一样查看、切换和直接介入每个 Agent，会话最好能够持久化和恢复。
4. Agent 之间需要多轮协作，而不只是一次性执行命令。代表性链路是：Codex 生成方案，Claude 审核，Codex 修改，Claude 复审并实现，Codex 审核代码，Claude 修复，Codex 最终确认。
5. 需要将 Agent 启动、发送 Prompt、等待、继续同一会话、读取结果和处理阻塞暴露为可由 Agent 或脚本调用的自动化接口。
6. 当前只希望外置使用工具，不修改现有项目框架的代码；接入成本应较低，不能为了试验先建设常驻服务、复杂 Web 平台或大规模 Swarm。
7. 长期可能把项目框架演进为管理其他 Agent 的 Orchestrator，但只有在出现并行任务、Worktree 隔离、依赖调度、消息路由、失败恢复、权限控制和统一 Review 等实际需求后才实施。
8. 交接不能只依赖截取终端文本。方案、Findings、Diff Review 和最终 Verdict 应保存为可验证 Artifact，并结合测试、Lint、Build 等机器证据判断是否完成。

候选项目应明确报告以下差距：是否原生支持 Windows PowerShell，是否要求 WSL、`tmux` 或容器，是否复用现有 CLI 配置，是否具备持久多轮会话与 Agent 间消息，是否只提供 GUI，以及实现完整审核闭环需要多少额外脚本或配置。

### CAO 与 Herdr 的边界

[`awslabs/cli-agent-orchestrator`](https://github.com/awslabs/cli-agent-orchestrator) 提供 `handoff`、`assign`、`send_message`、Inbox、Callback、Agent Profile 和定时 Flow，是完整的 Supervisor-Worker 编排器；但其官方安装要求包含 `tmux 3.3+`，不属于 Windows 原生 PowerShell 工作流。通过 PowerShell 调用 `wsl.exe` 只能把入口放在 Windows，Agent、`tmux`、配置路径和运行环境仍位于 WSL 内。

[`herdrdev/herdr`](https://github.com/herdrdev/herdr) 是较底层的 Agent 终端运行时。官方 Windows 文档确认它原生使用 ConPTY，支持 PowerShell、本地持久会话、Pane、Agent 命令发现、Git/Worktree 检测，以及 Claude Code、Codex 等 Agent Integration。它直接运行当前 Windows `PATH` 中已有的 CLI，因此通常不需要把 Windows CLI 配置迁移到 WSL。

Herdr 提供三层自动化原语：

1. Layout：创建 Workspace、Tab 和 Pane。
2. Pane：运行普通命令、发送输入、读取输出和等待文本。
3. Agent：启动已识别 Agent、发送 Prompt、等待生命周期状态和读取结果。

Herdr 可以实现「Codex 生成方案 → Claude 审核 → Codex 修改 → Claude 复审 → Claude 实现 → Codex 审核 → Claude 修复 → Codex 确认」，但这不是内置工作流。Supervisor Prompt 或外部脚本需要组合 `agent start`、`agent prompt --wait`、`agent wait` 和 `agent read`，自行定义角色、超时、结果格式和失败处理。

### 可靠交接约束

Herdr 的 `agent prompt --wait` 等待生命周期状态，不跟踪独立对话轮次；`idle` 或 `done` 只表示 Agent 可以继续接收输入，不能单独证明任务成功。终端读取也可能拿不到完整的全屏 Agent 历史。官方建议在完整响应不可用时，让 Agent 把结果写入 Markdown 文件并只回复文件路径。

因此，多轮协作应使用持久 Artifact 作为交接凭证：

```text
Agent 返回 idle/done
    + 目标 Artifact 存在且格式有效
    + 必要验证命令通过
    = 本轮工作完成
```

Review Artifact 至少应记录 Verdict、Findings、文件与行号、证据、严重级别、建议和残余风险。Agent 生命周期状态只用于调度，不替代测试、代码证据或验收结论。

### 选型原则

- 只有两个或少量 CLI 进行交叉审核时，优先使用非交互 CLI、Skill 或 Herdr，不先建设完整 Orchestrator。
- 需要 Windows 原生 PowerShell、持久 Pane、Agent 相互提示和人工随时介入时，Herdr 比依赖 `tmux` 的 CAO 更直接。
- 需要正式的 Handoff、异步 Callback、Inbox、权限 Profile、Fleet 管理和定时 Flow 时，完整 Orchestrator 才有足够收益。
- Agent 数量增长后，Orchestrator 主要解决人工调度瓶颈、工作区冲突、状态不可见、结果路由、无人值守恢复和团队治理；这些问题尚未出现时，不应只因架构先进而提前引入。

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
- [Codex CLI Reference](https://developers.openai.com/codex/cli/reference)
- [claude-in-codex](https://github.com/briandconnelly/claude-in-codex)
- [Connect Claude Code to tools via MCP](https://code.claude.com/docs/en/mcp)
- [CLI Agent Orchestrator 中文 README](https://github.com/awslabs/cli-agent-orchestrator/blob/main/README.zh-CN.md)
- [Herdr Agent Automation](https://herdr.dev/docs/agent-automation/)
- [Herdr Integrations](https://herdr.dev/docs/integrations/)
- [Herdr Windows Support](https://herdr.dev/docs/windows-beta/)

本条目的证据等级为 `provisional`：官方文档能证明原生子 Agent、非交互 CLI 和 MCP 接入能力；`claude-in-codex` 的 Codex → Claude 桥接方式、权限边界、费用和 Windows 兼容性仍需在实际环境中独立验证。
