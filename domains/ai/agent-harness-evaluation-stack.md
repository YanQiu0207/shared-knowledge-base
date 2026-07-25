---
status: verified-small-sample
source: local controlled trial plus official SWE-bench Verified evaluator
source_version: accessed 2026-07-25
applies_to: 需要评估 Coding Agent 能力、默认编排策略和高风险升级条件的跨项目开发框架
excludes: 完整 SWE-bench 排名、生产合规审计、模型间能力排名，以及特定项目的内部实现
---

# Agent Harness 的分层评测：能力、路由与交付证据

## 结论

评估 Agent 编程框架时，应把「模型是否能修好真实 Issue」与「框架是否在正确风险下升级控制」拆成不同信号。一个可重复的最小组合是：

1. 用离线、数据驱动的路由 Fixture 验证默认路径和升级条件。
2. 用项目自身回归测试验证合同和兼容性没有被破坏。
3. 用公开基准的官方 Harness 验证 Agent 生成补丁的端到端修复结果。
4. 用独立 Review 和结构化 Verify 约束交付声明；进程退出码不是评测成功的充分条件。

这套组合支持「Native-first，按风险升级 Runtime」的决策，但不能据少量公开样本删除 Runtime、宣称完整基准分数，或替代生产审计。

## 底层原理

### 1. 分离被测对象

| 信号 | 被测对象 | 不能推出的结论 |
| --- | --- | --- |
| 路由 Fixture | 框架的策略函数和失败关闭条件 | Agent 能否修复真实代码 |
| 项目回归 | 框架实现与既有合同 | 新模型的通用编码能力 |
| SWE-bench Verified | Agent 对公开真实 Issue 的补丁结果 | 框架的 Trust Gate 或生产审计有效性 |
| 独立 Review／Verify | 本次交付声明是否有机器与审查证据 | 公开基准的整体得分 |

混合这些信号会产生两种错误：把单元测试当成真实能力证据，或把公开基准 resolved 当成框架控制面正确性的证据。

### 2. 以失败关闭保护结论

评测包装器至少应验证：

- prediction JSONL 只包含本轮选中的实例，且使用单一模型标识；
- 预测内容以 SHA-256 固定，防止计划与执行间替换；
- 输出 Artifact 不覆盖已有证据；
- 官方评测结束后解析官方报告，而非只看子进程退出码；
- 每个选中实例同时出现在 completed 和 resolved 集合中，且不在 error 或 incomplete 集合中；
- 无 Run 的交付只声明独立 Verify 与 integration Review，不能伪造 Trust Gate、Harness 能力或严格独立 Judge。

### 3. 运行隔离是评测的一部分

公开基准常需要容器、数据集和镜像构建，不能进入每次默认回归。Windows 上若官方评测器依赖 POSIX 模块，可经 WSL 启动隔离 Linux 容器，再由该容器调用官方 Harness。

Docker Socket 是 Docker 主机的高权限控制面。启用此模式必须使用显式开关，并优先在专用评测机或隔离 Docker Daemon 上运行；不应对不可信 prediction、镜像或网络环境授权。

## 最小方案

```text
代码或策略变更
    │
    ├── 每次：离线路由 Fixture + 项目回归 + 独立 Verify／Review
    │
    └── 定期或发版前：固定、版本化的小样本 SWE-bench Verified
            │
            ├── Agent 在隔离基线仓库生成未提交 diff
            ├── 生成严格选择的 prediction JSONL
            ├── 显式启动官方 Harness
            └── 解析官方报告并写入结构化结论
```

建议把小样本的实例列表、模型标识、运行环境、prediction 哈希、官方报告路径和评测日期一并保存。这样才能比较模型或框架版本，而不是比较不可复现的聊天过程。

## 小样本效果与解释

一次 3 个公开 SWE-bench Verified 实例的小样本中，官方评测报告显示 `completed=3`、`resolved=3`、`errors=0`；同轮路由 Fixture 覆盖 8 类 Native／Runtime 选择，全部通过。该结果说明：

- 小样本中的 Agent 补丁被官方评测器接受；
- 默认 Native 路径与已声明的 Runtime 升级条件可以同时被机器检查；
- 评测包装器可以自动产生证据，无需人工手工判题。

它**不**说明模型在完整数据集上的得分为 100%，不说明所有项目都应禁用 Runtime，也不说明公开评测已覆盖私有仓库的安全、数据迁移、并发或合规风险。

## 适用节奏

| 时机 | 最小检查 | 目的 |
| --- | --- | --- |
| 每次修改路由或交付门 | 路由 Fixture、项目回归、Verify、Review | 防止控制面退化 |
| 每次修改 Agent Adapter 或评测包装器 | 上述检查加 prediction／报告解析负例 | 防止「假成功」 |
| 发版前或固定周期 | 固定公开小样本 | 观察真实修复能力漂移 |
| 高风险任务 | 完整 Runtime Run 与风险专用验证 | 保留审计、恢复与能力边界 |

## 来源与限制

- [SWE-bench 官方仓库](https://github.com/SWE-bench/SWE-bench)提供官方 Harness、数据集和容器化评测入口。
- [OpenAI：Harness engineering](https://openai.com/index/harness-engineering/)支持将环境、验证与反馈设计为 Agent 系统的一部分，但不提供上述小样本的统计外推。
- 本条目中的 `3/3` 仅是一次受控小样本的运行证据；实例选择、模型版本、运行环境和时间变化都会影响结果。
