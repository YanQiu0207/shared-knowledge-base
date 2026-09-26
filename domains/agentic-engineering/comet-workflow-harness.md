---
scope: cross-project
status: provisional
source: first-hand README + bundled SKILL.md + comet-resume-probe source verification of github.com/rpamis/comet (master branch, ~3.1k stars, MIT, v0.4.0, latest commit 899d1fb05cd4 2026-09-22)
source_version: 2026-09-28
applies_to: 选型或借鉴「AI 编码流程编排状态机 / 阶段门禁 / 可恢复任务 / Skill 评测闭环 / 工作流扩展模型」时参考；长任务跨会话接续、多 Agent worktree 并行、以机器门禁替代口头断言的场景
excludes: 打包分发脚本（esbuild 产物）内部校验逻辑未逐行反读，门禁细节依随包 SKILL.md 与 resume-probe 可读源码；未做本地安装与端到端实测；/comet-any 扩展管线未实跑；评测数字为项目方自报未独立复现；pre-1.0 API 可能变动
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

## 机制要点（SKILL.md + resume-probe 源码确认）

**可恢复的实现**（comet-resume-probe.mjs 可读源码核验）：
- 状态外置：每个 change 的 `.comet.yaml` 记 `workflow`、`phase`、`verifyResult`、`buildPause`、`archived`；逐字段校验，未知字段直接判 invalid state；归档区目录名 `YYYY-MM-DD-<name>` 解析回 change 名，「已归档但交付未完成」会捞回待恢复列表。
- 恢复判定是四选一确定性分类器（非 LLM 自由发挥）：输入 `{utterance, agent_context}` → 输出 `auto_resume | ask_user | out_of_scope | none` + confidence + reason + evidence。素材三路：磁盘状态（phase→命令硬编码映射）、`git status --short`（有脏文件一律 ask_user：「uncommitted worktree changes require attribution」）、话语关键词表（恢复词「继续/接着/恢复/跑完/提交/验证/归档/修刚才」；疑问词「是什么/为什么/explain」→ out_of_scope；拒绝词「不要恢复/skip comet」→ 退出）。
- 策略偏保守：多 active change、决策点（buildPause、verify fail）一律 ask_user；SKILL.md 规定只有 `auto_resume` 才自动进入。

**门禁的实现**（SKILL.md 确认；guard 脚本为 esbuild 打包产物，内部未逐行反读）：
- 门禁点在 phase 推进：过脚本校验（任务完成、状态字段齐、验证证据在）才写 state、返回下一条 `continuation`；Native 版 Agent 「works only on the phase specified by Runtime」。
- 口头越级三重堵死：SKILL.md 明文对话不得授权改 phase；`.comet` 目录 Hook 保护不可豁免；坏 state 报错不猜（「Report malformed state rather than guessing a phase」）。
- 并发安全：Native 命令带 `--expected-state-version` / `--expected-action` 乐观锁，多 Agent 同改一个 change 时旧版本号命令被拒。

**评测闭环**（eval/README.md 确认）：pytest + Rubric（通用 7 维/工作流 9 维//comet-any 生成包 11 维）+ LLM-as-judge（Judge 用独立模型独立凭据 `BENCH_JUDGE_*`，不继承主任务配置）；被测 Agent 跑在 Docker 镜像（预装 Claude Code/Codex/Qoder/CodeBuddy），可接 LangSmith/LangFuse 存 trace。**是评测驱动的人工迭代，非自进化**——仓库无「eval 结果自动回写 Skill」闭环。

**扩展模型**（comet-any/SKILL.md + ARCHITECTURE.md 确认）：三层扩展面，编译为 `workflow-protocol.json`（runtime source of truth，Factory/Eval/review/readiness 共用）：
1. Required Skill Call（最轻）：节点绑「必调依赖」，如 execute 必调 elementui、review 必调 whitebox-code-standard；
2. Overlay（覆写 Classic）：`comet-five-phase-overlay` 保五阶段控制流与 `.comet.yaml` 语义；节点分权——control 节点（open/execute/verify/archive）不可覆写，producer 节点（design/plan）可覆但须满足原 Output Schema，handoff/guardrail 可增强；
3. Workflow Kernel（完全自定义）：自建状态模型 + Output Schema + Guardrail，Native 本身即 kernel 成品示范。
扩展物也过门禁：每个绑定/Schema 标强制级别（guarded/handoff-guarded/evidence-only/advisory）；「failed eval, skipped eval, or stale-hash evidence cannot become ready」；publish 须人工批准、install 先 preview 确认零写入。Hook 侧 `hook.allow_paths` 默认空，扩展需写共享文件时加项目相对目录，`.comet` 永不可豁免。

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
