# Agent 记忆

## 结论

Coding Agent 的跨会话记忆层与共享知识库选型。自动提炼每轮对话的方案成本随对话量增长，重视额度时优先选择由 Agent 显式写入的工具；工具不解决「什么时候读写」，触发时机须写进 Agent 规则。

## 条目

- [Agent 记忆与知识管理工具：调研与选型](comparison.md) — 腾讯、字节、阿里、美团及社区项目对比；可吸收的设计思想；TencentDB Agent Memory 成本实测
- [causal-memory：安装、配置与使用](causal-memory-setup.md) — Windows wheel 安装，Claude Code 与 Codex 共用一个库，LLM 可选；端到端实测
- [TencentDB Agent Memory 停用记录](tencentdb-agent-memory-deactivation.md) — 守护计划任务会把容器重新拉起，须先移除；保留数据、可回滚
