---
scope: cross-project
status: provisional
source: first-hand code analysis of github.com/aws-samples/sample-codex-agent-team (main branch); runtime gaps from a secondary analysis article
source_version: 2026-08-02
applies_to: designing multi-agent collaboration protocols where agents share one code repository
excludes: production-readiness claims, Windows compatibility, non-Codex stacks, enterprise or data-compliance deployments
---

# 多 Agent 协作工程协议设计——以 AWS sample-codex-agent-team 为样例

> 本条目保存可跨项目复用的「多 Agent 共享代码仓库协作」协议设计方法，源自 AWS sample-codex-agent-team 的一手代码分析。只作通用参考；与具体项目实现冲突时以项目代码、配置和运行证据为准。

## 定位

AWS sample-codex-agent-team 不是一个调度框架，而是一份「多 Agent 协作工程协议」样例：不跑 API、不存任务状态、不做 Agent 间文件隔离，而是把一支工程团队如何分工、共享事实、证明完成、失败收口写成 Agent 可反复读取的配置（角色、Skill、Hook、命令护栏、Spec 模板）。它的价值在协议设计判断，不在可运行的控制平面——README 自声明「sample configuration, not a production-ready control plane」。

来源：github.com/aws-samples/sample-codex-agent-team，`main` 分支一手代码（5 个角色 Agent、9 个 Skill、3 个 Hook、命令护栏、8 份 Spec 模板）。底座依赖 Codex 加 OpenAI 模型。

## 适用与不适用

适用：

- 借鉴多 Agent 协作的协议设计，任何「多 Agent 共享代码仓库」场景。
- 隔离沙箱里跑无云资源的小任务，验证协作闭环。

不适用：

- 直接上生产：所有纪律均为提示词协议，无运行时强制，主线程遵守才工作，上下文压缩或提示词覆盖会静默失效。
- 跨平台（Windows）：Hook 硬编码 Unix 专有 `fcntl` 与 `/usr/bin/python3`。
- 企业或数据合规：MCP 用浮动版本、默认凭据、远程数据出口。
- 非 Codex 技术栈：配置格式专有。

## 协议设计

### 1. Spec 驱动的共享记忆

跨 Agent 状态放仓库文件，不依赖聊天记录：

| 文件 | 职责 |
| --- | --- |
| requirements | approved intent，显式 Out of Scope |
| spec | executable requirements，Interfaces And Contracts 独立成节，依赖任务前冻结 |
| design | 架构，含 Alternatives 与 Rollout 或 Rollback |
| tasks | 波次化任务，单行契约 |
| decisions | 追加式轻量 ADR：Context、Decision、Alternatives、Reversibility、Deviations |
| review | synthesizer 独占评审史 |

三条核心机制：

- **事实优先级**：当前文件与 diff 是实现状态权威，Spec 文件是需求与所有权权威，新鲜命令输出是验证权威，返回消息只是 evidence。stale 摘要与 silence 不覆盖当前磁盘。
- **任务状态语义**：ready、in-progress、completed-with-evidence、blocked-with-cause。不能仅凭 worker 声明标完成，必须 reconcile 返回结果、当前文件与新鲜命令输出。
- **任务契约**：`[角色] <动作> <结果> | <精确文件> | <验收>. Run: <命令>`，角色、文件、验收、验证命令一行闭合。

### 2. Spawn-Wait-Steer-Close 协调循环

显式协调原语（无共享 task store 时的解法）：

- **Spawn**：并发批量启动，pool size 等于当前波次 file-disjoint 宽度（不是 cap），under-provision 优先。
- **Wait**：等所有被请求的 agent 才 consolidate；首个返回不等于可推进；缺失结果记 evidence gap，禁止臆造。
- **Steer**：对活跃 worker 做最小纠正（澄清契约、传达决策、纠 scope drift、叫停到不安全边界前），不得扩宽文件 scope。
- **Close**：收割结果后关闭，最终前做 active-worker check。

Liveness 与 Recovery 精华：

- **Silence is not failure**：仅凭时间、无消息或无可见进程不是死亡证据。
- **Positive evidence before recovery**：明确终止错误、确认终止、输出损坏，或验收无法完成的持久证据，才允许恢复。
- 恢复只 respawn 未完成的精确 scope，不重做已完成，不在协调线程接管大规模实现。
- late output 当 stale result，与当前 ownership 和磁盘比对后再用。

### 3. 独立评审门禁

角色分离是权限边界：

- **Synthesizer**（唯一）：评审文件唯一作者，发唯一权威 verdict。
- **Analyst**（可选）：审一个 file-disjoint slice，不写任何文件，只返回结构化 findings。
- Lead 与 implementer 不能写权威 PASS；self-review 只是 TODO marker。

三轮预算（停止规则）：

- 整个目标共享最多 3 个 cycle，non-resetting。
- cycle 在 synthesizer spawn 时消耗（结果未知前）。
- 不因新 wave、fix、reviewer、file 或 resumed session 重置。
- 只有 cycle 1 或 2 的 FAIL 可产生一个 scoped fix wave；cycle 3 若 non-PASS，停止所有自动 fix 与 review，关闭 agent，保留证据，报告 blocked，永不自动 spawn cycle 4。

Evidence Discipline：引用前重读当前文件；Critical 主张能执行就实证，不能执行降级并标 requires live validation；每条 finding 标 evidence class；Verify the verifier（green 命令不够，要查 scope、CI-pinned 检查、acceptance 覆盖、断言完整）。

## 通用设计权衡

下列权衡在样例分析中浮现，对任意多 Agent 协作系统选型有参考价值。

| 权衡 | 样例选择 | 替代设计 | 选型考量 |
| --- | --- | --- | --- |
| 停止规则 | 全局 non-resetting 三轮预算 | per-scope 复审上限（每 scope 首轮加最多 N 轮） | 两者都能防无限自转。全局预算适合单一 integrated scope 评审；per-scope 上限适合多独立评审单元。核心是任一评审对象必须有硬上界并超限转人工 |
| 验证证据分级 | Live-Validation Gate 显式区分静态与运行时 | 只跑能验的机器检查 | 云、IaC、部署场景必须分级（静态 validate 证明不了真实部署）；纯软件代码场景机器测试即可 |
| 协调模型 | spawn-subagent 加显式 Steer 原语 | 声明式任务状态机（改任务定义重跑） | spawn 模型需显式纠偏原语；声明式模型通过改定义重跑天然支持纠偏。选型取决于底层是否有共享 task store |
| 中途决策落点 | 独立追加式 decisions 日志 | 决策并入 design 或 task 备注 | 独立日志利于中断恢复与多 Agent 交接；轻量项目并入 design 即可 |
| 并行隔离 | 文件 scope 声明（软约束） | 物理隔离（worktree、容器） | 软约束依赖主线程遵守，易被上下文压缩破坏；物理隔离是硬约束但成本高 |

## 来源、证据等级与限制

- **协议设计（三块）**：一手代码精读，证据等级高。
- **样例定位（非生产级）**：README 自声明，证据等级高。
- **运行时缺口**（如 `.gitignore` 缺失、MCP 浮动版本、跨平台限制）：来自二次分析文章，未由本条目复跑，证据等级中低，采用前需自行核实。
- **限制**：样例是提示词协议，无运行时强制；底座强依赖 Codex 与 OpenAI 模型；不提供 Agent 间文件隔离。
