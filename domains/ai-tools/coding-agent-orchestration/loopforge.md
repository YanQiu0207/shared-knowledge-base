---
status: verified
source: Tencent/LoopForge 官方 README 与 Local 使用指南；三次 Claude Code headless 实测
source_version: 实测于 2026-11-15；仓库 main 分支当日版本
applies_to: 个人开发者试用 Local 版、评估同类编排工具、向团队推广平台版之前的判断依据
excludes: 平台版团队部署的实测（未做）；官方宣称的腾讯内部使用数据（无法核实）；Windows 原生运行平台版
---

# Tencent LoopForge

## 结论

LoopForge 是腾讯轻量云团队开源的 MIT 平台，自己不写代码，而是编排 CodeBuddy、Codex、Claude Code 等 10 种 Agent CLI：管角色分工、沙箱、SOP 流水线、人工审批关口和留痕。个人试用优先用 **LoopForge Local**（npx 一条命令装进 Claude Code），平台版适合团队，但安装脚本只声明支持 Linux / macOS。

## Local 版实测记录（Windows，Claude Code，headless）

安装：项目目录执行 `npx -y loopforge-cli@latest install claude`，写入 85 个文件，全部在 `.claude/`（agents / commands / rules / skills / workflows），另生成 `.devflow/` 存安装状态。**不写 `settings.json`，不会自动挂 hook**；`agent-observability` 内置腾讯云 CLS 上报代码，但需手动配置 `CLS_CODINGAGENT_ENABLED` + endpoint + 密钥才生效，默认不外传。

三条路径的实测差异：

| | small（SOLO） | medium（完整流程） |
| --- | --- | --- |
| 触发 | Phase 0 由 LLM 按改动量 / 影响模块 / 风险判定 | 需求里明确写「按 medium 处理」才触发 |
| agent | 1 个 `devflow-solo-developer` | 主线程 + architect / developer / code-reviewer / test-engineer / leader / knowledge-engineer 共 6 个 |
| 澄清 | 不问，直接做 | 一次只问一题；实测第一题就挖到需求里两处矛盾（「整数输出」口径 × 「默认保持当前行为」） |
| 审查 | 自我复核 | 独立角色输出 P0/P1/P2 评级报告 |
| 产物 | 2–3 个文件 | 约 10 份（phase0-scan、需求、设计、计划、变更报告、审查报告、测试报告、知识沉淀） |
| 实测耗时 / 费用 | ~2.5 min / ~$1.3 | 续跑 ~7.5 min / ~$3.8（约 SOLO 3 倍） |

实测发现的问题：

- **规模判定偏保守**：新建 CLI + 测试这类需求在小仓库里仍会被判 small 走 SOLO，想看完整流水线要在需求文本里强制指定。
- **人工关口是软的**：headless 模式下对流程说「预先批准」即可直接放行；拦截能力依赖使用者不授权。
- **状态文件可被事后手改**：solo 报告里的结束事件名写错（`SOLO_completed` vs `workflow_completed`）由主线程手动修正 JSON，没有程序校验。
- **文件名不一致**：协议要求读 `.claude/rules/global.mdc`，实际安装为 `global.md`（未观察到运行时故障）。

## 平台版要点（未实测）

- `./start.sh` 拉取 GHCR pin 镜像 + MySQL，第一个注册账号成为管理员；模型 Key 与 GitHub 授权在 Web 界面配置。
- **安全边界**：通过 Docker socket 控制宿主机、默认监听 `0.0.0.0`、开放自助注册——仅适合可信团队；对团队外开放前需 `AGENTFLOW_ALLOW_SIGNUP=false` + HTTPS。
- 官方文档未声明 Windows 支持；WSL2 + Docker Desktop 理论上可跑，未验证。
- 同类对照：OpenHands / Multica / agent-orchestrator / agentrove 偏「并行多 Agent + worktree 隔离」，LoopForge 的差异点在可复用 SOP、角色分离评审和人工签字关口。

## 使用建议

- 个人 / 小改动：Local 版默认路径足够，完整流程对小型需求性价比不高。
- 想体验完整流水线：在需求中写明「按 medium 规模处理」，并在交互式会话中回答澄清问题——headless 时关口形同虚设。
- 不要把 Local 装进已运行其他阶段化工作流（如 Comet、OpenSpec）的仓库：两套 `.claude/` 规则与命令会叠加冲突。

## 来源

- [Tencent/LoopForge](https://github.com/Tencent/LoopForge)，README 与 docs/local/usage.zh-CN.md，查阅于 2026-11-15。
- 实测环境：Windows 11 + Git Bash + Claude Code 2.1.325，测试仓库为最小 Python 项目（calc.py + pytest）。
