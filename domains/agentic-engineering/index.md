# Agentic Engineering

## 结论

本主题保存可跨项目复用的 Coding Agent 工程机制。项目专属规则和正文必须留在对应项目中。

## 条目

- [知识与代码冲突处理](knowledge-code-conflict-handling.md)
- [TencentDB Agent Memory 接入 Claude Code 与 Codex](tencentdb-agent-memory-claude-codex.md) — MCP Bridge 方案：显式调用工具，手动控制写入
- [TencentDB Agent Memory 的 Proxy 透明接入与模型绑定](tencentdb-agent-memory-proxy-mode.md) — 劫持 LLM 链路自动注入；模型名由上游决定且需带 [1M] 窗口标记；订阅制账号不适用
- [TencentDB Agent Memory 记忆层工作机制（注入 · 记录 · 检索）](tencentdb-agent-memory-mechanics.md) — 代理链路三动作；L0–L3 分层与注入块；会话归属与 mem:session-reset
- [TencentDB Agent Memory 的 Hook 接入（免 Proxy）](tencentdb-agent-memory-hook-mode.md) — 客户端生命周期事件接入；订阅制可用、无逐会话交互；资产上下文需自行补齐
- [AgentMemory：跨 Coding Agent 的本地持久化记忆层](agentmemory.md)
- [多 Agent 协作工程协议设计（AWS sample-codex-agent-team 样例）](multi-agent-collaboration-protocol.md)
