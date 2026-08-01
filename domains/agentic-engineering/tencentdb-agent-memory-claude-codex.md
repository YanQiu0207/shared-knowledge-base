---
status: verified-local
source: https://github.com/TencentCloud/TencentDB-Agent-Memory
source_version: v1.0.0 (9b7dbdd)
applies_to: Windows, Node.js 22+, Claude Code, Codex, local standalone Memory Gateway
excludes: remote Gateway exposure, automatic per-turn capture, embedding service configuration, API keys and private model endpoints
---

# TencentDB Agent Memory 接入 Claude Code 与 Codex

## 结论

以源码启动 TencentDB Agent Memory 的 standalone Gateway，并通过一个本地 stdio MCP Bridge 同时接入 Claude Code 与 Codex。Gateway 默认使用本地 SQLite + BM25；Embedding 是可选增强，不是启动或使用记忆的前提。

这套模板包含可复制的 Bridge 源码、Gateway 启动脚本和 MCP 注册脚本。LLM 凭据保留在调用方指定的本地配置文件中，不写入仓库、脚本参数或 MCP 配置。

## 架构

```text
Claude Code ─┐
             ├─ stdio MCP Bridge ─ HTTP v2 ─ Memory Gateway (127.0.0.1:8420)
Codex ───────┘                                  └─ SQLite + BM25 + LLM Pipeline
```

Bridge 提供四个工具：

- `memory_status`：检查 Gateway 状态。
- `memory_recall`：BM25 取候选；可选使用已有聊天 LLM 重排候选。
- `memory_read_scenario`：按路径读取 L2 场景记忆。
- `memory_capture`：写入已确认的用户—助手对话到 L0。

## 前提

- Node.js 22 或更高版本。
- Python 3。
- 已安装 `codex` 与 `claude` CLI。
- 一个 OpenAI-compatible Chat Completions LLM，用于 L1/L2/L3 提取；不需要 Embedding 模型。

LLM 配置文件由用户自行保存在仓库外，格式如下：

```text
baseurl: https://example.com/v1
api-key: <secret>
model: <model-id>
```

不要提交该文件。

## 快速安装

1. 获取 TencentDB Agent Memory 源码并固定版本：

    ```powershell
    git clone --branch v1.0.0 --depth 1 https://github.com/TencentCloud/TencentDB-Agent-Memory.git E:\tools\TencentDB-Agent-Memory
    ```

2. 复制本条目同级的 [`tencentdb-agent-memory-bridge/`](tencentdb-agent-memory-bridge/) 到本机固定目录，例如 `C:\Users\<user>\tools\tdai-memory-bridge`。

3. 执行安装脚本。它会安装 Bridge 依赖、启动 Gateway，并将同一 stdio Bridge 注册到 Codex 与 Claude Code：

    ```powershell
    .\install.ps1 `
        -MemorySourcePath E:\tools\TencentDB-Agent-Memory `
        -LlmConfigPath E:\secrets\memory-llm.txt
    ```

4. 重启 Claude Code 和 Codex，再调用 `memory_status`。

## 记忆层与知识库的协调

- TencentDB Agent Memory 是「记忆层」：用于保存高频、简短、跨会话可用的偏好、约束和已确认结论；它不是项目事实或交付物的权威来源。
- 非简单任务先调用 `memory_recall` 恢复上下文，再按任务范围读取项目知识库或跨项目公共知识库。
- 代码、配置、测试和运行证据优先于记忆与知识库；发生冲突时必须展示冲突，不得静默覆盖。
- 只有已确认且可复用的结论才 `memory_capture`；项目专属或需追溯内容写入项目知识库，用户确认、脱敏且跨项目复用的内容写入公共知识库。
- 三类存储不做自动全量同步。Memory 只保存摘要或检索线索，不能替代正式文档。

## 使用策略

建议先采用可控写入：

1. 非简单任务开始前调用 `memory_recall`。
2. 命中场景路径时，按需调用 `memory_read_scenario`。
3. 只在用户确认或结论稳定且可复用时调用 `memory_capture`。
4. 不写入密钥、令牌、完整私密日志和未经确认的推断。

L1 原子记忆由 Gateway 异步提取；首次写入后立即检索为空是正常现象。

## LLM 重排

Bridge 默认仅在 BM25 返回至少 2 条候选时调用聊天 LLM 重排：

```text
BM25 前 15 条 → LLM 只返回相关候选 ID → 返回前 N 条
```

重排失败、超时、JSON 非法或返回未知 ID 时，Bridge 自动退回原 BM25 顺序。该机制复用已有聊天 LLM，不需要购买 Embedding 服务。

## 验证

```powershell
Set-Location C:\Users\<user>\tools\tdai-memory-bridge
npm test
```

预期测试覆盖：Gateway HTTP 请求头、LLM 重排顺序和异常回退。随后在 Claude Code 或 Codex 中调用 `memory_status` 与 `memory_recall` 做端到端验证。

## 边界

- Gateway 仅监听 `127.0.0.1` 时，可使用 standalone 默认的 `apiKey = "local"` 和 `serviceId = "default"`。
- 若改为局域网或公网监听，必须启用 `TDAI_GATEWAY_API_KEY`。
- 本模板不实现自动逐轮写入；需要先以真实任务验证记忆质量，避免长期记忆被临时推断污染。

## 证据

- TencentDB Agent Memory README 的 standalone Quick Start：本地 SQLite + BM25 默认可用，LLM 配置用于独立运行，`embedding.*` 属于远程可选配置。[README](https://github.com/TencentCloud/TencentDB-Agent-Memory/blob/feat/server/README.md)
- 本模板在 Windows 本机验证过 Gateway `health`、Claude Code MCP 连接、Codex MCP 注册，以及 Bridge 的 HTTP 与重排回退测试。
