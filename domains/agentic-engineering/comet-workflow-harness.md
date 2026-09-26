---
scope: cross-project
status: provisional
source: first-hand README analysis of github.com/rpamis/comet (master branch, ~3.1k stars, MIT, v0.4.0, latest commit 899d1fb05cd4 2026-09-22)
source_version: 2026-09-24
applies_to: 选型或借鉴「AI 编码流程编排状态机 / 阶段门禁 / 可恢复任务 / Skill 评测闭环」时参考；长任务跨会话接续、多 Agent worktree 并行、以机器门禁替代口头断言的场景
excludes: 未逐行读源码，机制均为 README 自述；评测数字为项目方自报未独立复现；未做本地安装验证；pre-1.0 API 可能变动
---

# Comet：AI 编码的流程编排状态机（Native/Classic 双工作流）

> 一句话定位：把「想法 → 验证 → 归档」固化成状态机的 Agent Skill Harness，阶段推进不依赖 Agent 口头声称「完成了」。本条目来自 README 自述与官方页面，未实测。

## 定位

- GitHub 仓库 `rpamis/comet`，MIT，v0.4.0 stable（2026-09 活跃维护，~3.1k stars）。
- README 自述：*"Comet is a resumable long-running task workflow and Skill platform for coding"*；副标题「agent skill harness for turning ideas into evaluated workflows」。
- 解决的要害：Agent 写代码「说完成就算完成」——没有阶段门禁、没有状态留存、中断即丢失。Comet 的对应主张：*"phase exits do not rely on an agent saying 'done'"*，由 `comet-guard.mjs` / `comet-state.mjs` 等脚本在推进前检查任务、状态字段、验证证据与归档条件。
- 与自研 agentic-engineering-framework 属**同类竞品**（同为「状态机 + 阶段门禁 + 评测」路线），适合当参考实现对比吸收。

## 双工作流：为什么要两个

分界线是**模型能力**，不是任务大小：

| | Native | Classic |
| --- | --- | --- |
| 适用 | *"strong models that can plan and verify autonomously"* | *"scenarios that benefit from a complete phased methodology and stronger constraints"* |
| 约束方式 | 需求确认后 plan/implement/test/review 由模型自选；Comet 只管状态检查、验收、可恢复归档 | 把 OpenSpec + Superpowers 合成五阶段流程（状态机 + 阶段检查 + 脚本） |

不能合成一个自适应流程的两个理由：

1. **代价不对称**：Comet 自报评测（Native vs Classic，16 任务 × 48 运行）：Native 总 token 少 76.8%、Agent 轮次少 57.4%、耗时长少 47.4%；pass^3 87.5% vs 75%。对强模型，五阶段门禁是纯开销；对弱模型，它是救命约束。
2. **作者拒绝「猜」**：`/comet` 读 `.comet/config.yaml` 确定性转发，*"does not guess from task size or mix changes, state, or directories across workflows"*——让 agent 猜「该用哪档流程」本身就是不确定性来源，用配置钉死。

README 明确：*"Native and Classic are not lightweight and heavyweight tiers, and neither upgrades into the other"*——平行独立、不能互相升级，仅共享底座（config、状态、Dashboard、Eval）。

推断（README 未明说）：Classic 是原有产品（0.3.9），Native 为 0.4.0 新增运行时；保留 Classic 客观上留住了既有 OpenSpec + Superpowers 用户，但全文无 migration 字样。

## 机制要点（README 自述）

- **可恢复**：每个 change 的 `.comet.yaml` 记录阶段、执行模式、验证结果、归档状态；`comet resume-probe` 续跑。
- **门禁靠脚本不靠口头**：Hook 默认禁止写路径（`hook.allow_paths` 为空），`.comet` 与工作流产物不可绕过保护；文档同步由脚本接管，替代「记得更新设计文档」式提醒。
- **Supervisor Changes**：复杂需求拆子变更 DAG，多 Agent 在隔离 worktree 独立实现验证，按依赖序集成后父变更最终 Verify。
- **运行时**：纯 Node.js（Windows/macOS/Linux，无需 Bash/WSL）；产物人读部分在 `docs/comet/`，机器状态在 `.comet/runtime/`。
- **评测闭环**：`comet eval` 用 Rubric + Pass@k + Pass^k 驱动 Skill 演进，可接 LangSmith/LangFuse。

## 安装与使用（README 自述）

```bash
npm install -g @rpamis/comet   # Node.js 22.16+ 或 24+
comet init                      # 项目内初始化，--workflow classic|both|native
# 宿主中调用 /comet（统一入口，按配置转发）；通用平台：npx skills add rpamis/comet
```

- 声称支持 37 个 AI coding 平台（Claude Code、Codex、Cursor、Gemini CLI 等），各平台写入专属 Skills 目录。
- 低门槛起步：两条 skill（`/comet`、`/comet-any`）+ 一条命令（`comet eval`）。

## 适用与冷静面

**适用**：长任务跨会话接续（状态留存 + 续跑）；多 Agent 并行实现（DAG + worktree 隔离 + 集成门禁）；想把「验证过了才进下一阶段」变成机器门禁的团队；给自有 workflow 做 A/B 评测。

**冷静面**：
- pre-1.0（0.4.0），API 可能变动。
- 评测数字为项目方自报，README 自注明受 conditions and limitations 约束，未独立复现。
- Classic 绑定 OpenSpec + Superpowers 生态，不用该栈则价值打折（Native 可绕开）。
- 维护者人数、issue 响应、`SECURITY.md` 未核查，供应链上按惯例先隔离试用。

## 相关条目

- [Omnigent：编排多编码 Agent 的 meta-harness](omnigent-meta-harness.md) —— 相邻方案：Omnigent 编排「多个现成 agent」，Comet 编排「单个 agent 的开发流程」。
- [多 Agent 协作工程协议设计](multi-agent-collaboration-protocol.md) —— 同属多 Agent 协作，Comet 的 Supervisor Changes 是产品化实现之一。
