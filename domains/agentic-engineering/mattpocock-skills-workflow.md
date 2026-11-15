---
scope: cross-project
status: provisional
source: first-hand clone + README/SKILL.md/ask-matt source reading of github.com/mattpocock/skills (main branch, 270k stars, 472 commits, cloned 2026-10)
source_version: 2026-10-05
applies_to: 选型或借鉴「AI 编码工作流编排 / 技能分层设计 / 跨宿主（Claude Code + Codex）技能分发」时参考；需求对齐盘问、TDD 红绿循环、票据化多会话工程的场景
excludes: 未做端到端实跑验证（仅安装与 Codex 侧技能可见性验证）；docs/ 页面未逐一研读；各技能完整正文未逐行反读；star 数与技能清单为 2026-10 快照
---

# Matt Pocock Skills：小而组合的 AI 编码工作流技能集

> 一句话定位：反「全家桶框架」路线的技能集——不接管流程，用小技能组合覆盖「想法 → 上线」，靠显式的 Skill tool 调用图组装，双宿主行为一致。

## 定位

- GitHub 仓库 `mattpocock/skills`（270k stars / 22.7k forks，2026-10 快照），作者为 Total TypeScript 的 Matt Pocock。
- README 自述定位：「Skills For Real Engineers」——真实工程而非 vibe coding。明确点名批评 GSD、BMAD、Spec-Kit「接管整个流程」的方案，主张技能要**小、可改、可组合**，用户保留控制权。
- 正式发布 25 个技能（engineering 18 + productivity 7），按「谁能调用」分两层；`misc/`、`in-progress/`、`deprecated/` 不随插件发布。

## 双层调用模型（框架的核心设计）

| 层 | 标记 | description 写法 | 职责 |
| --- | --- | --- | --- |
| User-invoked | Claude Code：`disable-model-invocation: true`；Codex：`agents/openai.yaml` 的 `policy.allow_implicit_invocation: false` | 写给人看：一句话，去掉触发短语 | 只做编排，只能用户手动 `/` 调用 |
| Model-invoked | 双侧都不加标记 | 写给模型看：带触发短语（Use when the user says…） | 承载可复用方法论，agent 可自动触发 |

硬性不变式：user-invoked 可调 model-invoked，**绝不**调另一个 user-invoked；同一技能在两个宿主的分层必须一致。技能间依赖写成显式 `Call the Skill tool with "xxx"`（一次一个名字），不写 `/xxx` 也不跨目录相对链接——这是双宿主行为一致的关键。

## 主流程：想法 → 上线

前置：`/setup-matt-pocock-skills` 每仓库跑一次，探测 git remote 后确认三件事（issue tracker 位置、triage 标签、`CONTEXT.md`/ADR 布局），写入 `docs/agents/issue-tracker.md`；未配置时下游技能会拒绝并要求先跑它。

| 步骤 | 调用 | 内部再调用 | 产出 |
| --- | --- | --- | --- |
| ① 对齐想法 | `/grill-with-docs` | `grilling`（设计树逐轮盘问）+ `domain-modeling`（术语沉淀进 `CONTEXT.md`、决策进 ADR） | 对齐的方案 + 领域语言 |
| 　分支：问题需跑代码才能答 | `/handoff` 出 → `/prototype` → `/handoff` 回 | — | 丢弃式原型答案，折回主线 |
| ② 定规格 | `/to-spec` | **不盘问**，纯综合；与用户确认测试 seam 后发 tracker，打 `ready-for-agent` | spec + 约定 seam |
| 　分支：多会话工程 | 是 → `/to-tickets` 拆 tracer-bullet 票据（带阻塞边），每票跑③且票间 `/clear`；否 → 同窗口直接③ | — | 自包含票据组 |
| ③ 实现 | `/implement` | 驱动 `tdd`（红绿循环，一次一个垂直切片）→ 完工跑 `code-review`（双并行 sub-agent：Standards 轴 + Spec 轴）→ 提交 | 代码 + 双轴评审 |

上下文纪律：步骤①–②（含 to-tickets）在**同一个不中断的窗口**完成；`/implement` 每票据开新上下文。逼近 smart zone（约 150k token）时在最近的阶段边界 `/compact`。

## 三个汇入点（on-ramp）

- **堆积 issue** → `/triage`（状态机式分诊 → agent-ready 票据）→ `/implement`。`to-tickets` 产出的票据已 agent-ready，**不要**再 triage。
- **难查的 bug** → `diagnosing-bugs`（model-invoked，自动触发）：先造「能变红」的紧反馈回路（列了 10 种造法：失败测试 / curl 脚本 / trace 回放 / 二分 harness 等）→ 最小化 → 假设 → 插桩 → 修 + 回归测试；复盘发现缺 seam 时移交 `/improve-codebase-architecture`。
- **巨大且看不清的工程** → `/wayfinder`（最重度）：`grilling` + `domain-modeling` 定目的地 → 铺「决策票据地图」（`wayfinder:map` 标签）→ 并行派 `research` sub-agent → 每会话只解一张票 → **只交决策不交代码**，雾散后汇入 `/to-spec`。

## 底层词汇层与日常习惯

- `grilling` 是可复用盘问原语：`grill-me`、`grill-with-docs`、`triage`、`wayfinder`、`improve-codebase-architecture` 都是它的外壳；规定「查事实是 agent 的活（派 sub-agent），做决策是用户的活」。
- `domain-modeling`（领域语言）与 `codebase-design`（深模块词汇：module / interface / depth / seam / adapter，源自 Ousterhout）是被所有技能拉取的单一词汇源。
- 日常习惯：每隔几天跑 `/improve-codebase-architecture` 扫描「深模块化机会」，选中项生成想法进入主流程①。

## 主流程图

```
                        ┌─ /triage ──────────────┐
堆积 issue ────────────→│  agent-ready 票据       │──→ /implement
                        └────────────────────────┘
想法 ─→ /grill-with-docs ─→ /to-spec ─→ /to-tickets? ─┬─是→ 每票 /implement
        (grilling +        (综合,不发问,    (拆票据)    └─否→ /implement(同窗口)
         domain-modeling)   定 seam,发tracker)        │
                                                       ▼
                                              内部: tdd → code-review → 提交
巨大迷雾 ─→ /wayfinder (grilling+domain-modeling+research) ─雾散→ /to-spec ─→ 主线
坏了 ─→ diagnosing-bugs ─复盘─→ /improve-codebase-architecture ─→ 想法 → 主线
```

## 双宿主安装对照（本机已验证）

| 宿主 | 项目级位置 | 说明 |
| --- | --- | --- |
| Claude Code | `.claude/skills/`（平铺） | 或 `claude plugins install mattpocock-skills`（官方插件，自动更新、只读） |
| Codex | `.agents/skills/`（整目录，保留各技能的 `agents/openai.yaml`） | Codex 从 `$CWD/.agents/skills` 向上扫到仓库根；技能名带 `mattpocock-skills:` 前缀（取自 package.json 的 name） |
| 其他 agent | `npx skills@latest add mattpocock/skills` | 复制为可编辑文件，`npx skills update` 跟进上游 |

插件与 skills.sh 二选一，同时装会出现每个技能两份。扩展自己的技能：直接在两个安装目录新建文件夹即可，无注册机制；建议遵守上述分层约定与显式调用写法。

## 与 Comet 的对比（同为流程编排类）

- Comet 是「状态机 + 阶段门禁 + 评测」的重框架路线，机器门禁替代口头断言；Matt Pocock Skills 是「小技能组合 + 用户保留控制」的轻路线，无状态、无门禁脚本。
- 两者都强调 TDD 与 review 环节；选型时按「要强约束/可恢复/可评测」选 Comet，「要轻量可魔改/跨宿主一致」选 Matt Pocock Skills。

## 结论

1. 框架本质是「一堆普通 Markdown 文件夹」，无注册机制、无构建步骤；价值在分层调用模型、显式依赖写法与上下文纪律，而非工具代码。
2. 主流程的骨架是「盘问对齐 → 规格化 → 票据化 → 每票独立 TDD 实现 + 双轴评审」，汇入点覆盖 issue 分诊、bug 诊断、迷雾型大工程三类入口。
3. 可借鉴的最小集：`grilling` 盘问原语（设计树 + 每轮推荐答案 + 事实/决策分工）、`tdd` 的 seam 预约定与反模式清单、`code-review` 的双轴并行 sub-agent。
