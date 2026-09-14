---
scope: cross-project
status: provisional
source: first-hand README analysis of github.com/omnigent-ai/omnigent (main branch, ~9.9k stars, Apache-2.0, alpha)
source_version: 2026-09-15
applies_to: 选型或借鉴「编排现成编码 agent CLI 的统一 harness 层」时参考；多 agent 混编、跨设备接力、云沙箱与治理策略场景
excludes: 未做本地安装运行验证；性能与稳定性无一手证据；alpha 阶段能力随时可能变化
---

# Omnigent：编排多编码 Agent 的 meta-harness

> 一句话定位：在 Claude Code / Codex / Cursor / OpenCode 等现成编码 agent 之上加一层统一编排——不重写 agent 就能换 harness、混编多 agent、强制沙箱与治理策略。本条目来自 README 自述，未实测。

## 定位

- GitHub 仓库 `omnigent-ai/omnigent`，Python，Apache-2.0，alpha 阶段（约 9.9k stars / 3.7k commits，2026-09 活跃维护中）。
- 自称「The open-source meta-harness for all your AI agents」，核心主张：「swap or combine harnesses without rewriting, enforce policies and sandboxing」。
- 与自研框架的关系是**相邻方案而非同层竞品**：omnigent 走「编排现成 agent CLI」路线（自身不实现 RunLoop，复用各 harness 的 CLI），不是自建 agent 运行时。

## 适用场景（README「Why Omnigent」六点）

| 场景 | 说明 |
| --- | --- |
| 多设备接力 | 终端发起 → 浏览器继续 → 手机接手；消息、子 agent、终端、文件全同步 |
| 混编多 agent | 同一会话混用 Claude Code、Codex、Cursor、OpenCode、Hermes、Pi 及 YAML 自定义 agent；可让 A 审查 B 的产出 |
| 任意模型接入 | API key、Claude/ChatGPT 订阅、OpenRouter/Ollama 兼容网关均一等公民 |
| 云沙箱运行 | 不依赖本机：Modal、Daytona、E2B、Kubernetes 等十余种沙箱后端 |
| 团队协作 | 分享会话实时围观、co-drive（队友消息在你机器上执行）、fork 会话 |
| 治理策略 | 高危操作先暂停等审批、限制花费、限定可用工具；分 server/agent/session 三层叠加 |

## 安装与使用（README 自述）

安装三选一：

```bash
# 1. 一键脚本（可加 --extra modal,e2b 等沙箱 extras）
curl -fsSL https://raw.githubusercontent.com/omnigent-ai/omnigent/main/scripts/install_oss.sh | sh
# 2. Python 包
uv tool install omnigent        # 或 pip install omnigent
# 3. Homebrew（macOS/Linux）
brew install omnigent-ai/tap/omnigent
```

前置要求：Python 3.12+、`uv`、`git`、Node.js 22 LTS+（harness CLI 与 web UI）、`tmux`（原生终端封装）；Linux 沙箱需 `bubblewrap`，macOS 用自带 seatbelt。

基本用法：

```bash
omnigent                  # 交互选模型开会话，同时起本地 web UI（localhost:6767）
omnigent claude           # 指定 runtime（也支持 codex/cursor/opencode/hermes/pi 等）
omnigent setup            # 管理凭据（API key / 订阅 / Gateway / Databricks）
omnigent run examples/polly/   # 官方示例：Polly 多 agent 编排、Debby 双脑辩论、deep-research
```

- 会话中 `/model` 切模型；自定义 agent 是一个 YAML（name / prompt / executor.harness / tools）。
- `omnigent start / login / host` 用于部署服务器并注册本机为 host。
- agent 接入形态：直接启动七种 CLI；ACP 协议接 Grok Build、Devin（需先装厂商 CLI 并登录）；YAML executor 可选 claude-sdk / claude-native / codex(-native) / cursor(-native) / opencode / pi(-native) / openai-agents 等。

## 关键限制与风险

- **Windows 原生可用但降级**：无 tmux/PTY 终端封装、无文件系统/网络隔离（仅 Job Object 进程树约束）——沙箱治理能力在 Windows 上基本拿不到，全功能建议走 WSL。
- alpha 阶段：API 与能力随时变化，不宜直接深度依赖进生产流程。
- 本条目未做本地安装与运行验证；「十余种沙箱后端」「订阅一等公民」等均为 README 自述。

## 与相关条目的关系

- 与 [多 Agent 协作工程协议设计](multi-agent-collaboration-protocol.md) 互补：AWS 样例是「协议设计参考」（无运行时强制的提示词协议），omnigent 是「可运行的编排工具」（自身提供运行时与策略强制）；前者借鉴设计判断，后者评估直接引入。

## 来源与证据等级

- **README 自述（代码确认层面：README 存在于仓库）**：定位、场景、安装、用法、系统要求。
- **GitHub 搜索页元数据**：star 数、活跃度。
- **缺失证据**：未本地安装运行；未核对源码中沙箱与策略层实现；未验证 Windows 降级细节。
