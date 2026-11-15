---
scope: cross-project
status: verified
source: causal-memory 官方 README、integrations/claude-code 与 integrations/codex 安装脚本、skills/causal-memory/SKILL.md；本机安装与端到端实测
source_version: causal-memory 0.10.0（PyPI win_amd64 wheel）；Codex CLI 0.169.0；验证日期 2026-11-15
applies_to: 在 Windows 上让 Claude Code 与 Codex 共用一个 causal-memory 记忆库，并按需接入 OpenAI 兼容的 LLM
excludes: macOS／Linux 安装细节、HTTP 多租户部署、本地向量模型（需源码编译 local-embed 特性）、评测数据复核
---

# causal-memory：安装、配置与使用（Claude Code + Codex 共享）

## 结论

- Windows 无需 Rust：PyPI 提供 `win_amd64` wheel，`uv tool install causal-memory` 即可得到 `causal-memory.exe`，裸跑就是 stdio MCP server。
- 两个 CLI 注册同一个 MCP，并用 `CAUSAL_MEMORY_DB` 显式指向同一个 SQLite 文件，即可共享记忆。官方文档里的默认库路径前后不一致（`~/.causal-memory/` 与 `~/.local/share/causal-memory/` 都出现过），必须显式指定。
- 只有 Agent 显式调用工具时才写入。不配 LLM 时写入与 BM25 检索可用；配了 LLM 后，提炼类功能才会调用模型，且 LLM 不可用（如余额不足返回 402）时写入与检索不受影响。

## 安装

```bash
uv tool install causal-memory        # 或 pip install causal-memory
causal-memory --help                 # 验证命令可用
```

官方 `integrations/*/install.sh` 假定使用源码编译出的 `target/release/causal-memory`，用 wheel 安装时改为手工注册。

## 注册 MCP

```bash
DB='C:/Users/<user>/.local/share/causal-memory/causal.db'
BIN='C:/Users/<user>/.local/bin/causal-memory.exe'

# Claude Code：服务名必须写在 -e 之前，否则 -e 会把服务名当作环境变量吞掉，
# 报错 missing required argument 'commandOrUrl'
claude mcp add causal-memory --scope user -e CAUSAL_MEMORY_DB=$DB -- $BIN

# Codex
codex mcp add --env CAUSAL_MEMORY_DB=$DB causal-memory -- $BIN
```

验证：`claude mcp list` 显示 Connected；`codex mcp get causal-memory` 显示 `enabled: true`。

## 配置 LLM（可选）

配置写入 `~/.local/share/causal-memory/config.json`，两个 CLI 启动的 MCP 进程共用：

```bash
causal-memory setconfig \
    CAUSAL_MEMORY_LLM_API=https://api.deepseek.com/v1 \
    CAUSAL_MEMORY_LLM_KEY=<key> \
    CAUSAL_MEMORY_LLM_MODEL=<model>
causal-memory getconfig              # 密钥会被遮蔽显示
```

- `CAUSAL_MEMORY_LLM_API` 填 OpenAI 兼容的 base URL。向量检索另用 `CAUSAL_MEMORY_EMBED_API/KEY/MODEL`；DeepSeek 不提供 embedding 接口，不配时只用 BM25。
- 用到 LLM 的是 `distill`、`judge`、`reasoning`、`resolve-updates` 等命令，以及 `remember`、`resolve_updates` 等工具；`record_decision`、`search_memory`、`intervention_query` 不依赖 LLM。
- 验证 LLM 是否接通：对一个临时库执行 `causal-memory distill <session.json> --dry-run`。输入须含 `date` 字段和 `turns` 数组，否则只报格式警告、不会发出请求。

## 使用规则

写进 `~/.claude/CLAUDE.md` 与 `~/.codex/AGENTS.md`：

| 时机 | 工具 |
| --- | --- |
| 非平凡决策前（架构、排查思路、选型、部署） | `search_memory` |
| 不可逆或高风险操作前 | `intervention_query`（返回 safe / warning / danger） |
| 意外失败时 | `trace_cause` / `trace_cause_chain` |
| 行动并验证结果后 | `record_decision`（必填 `decision`、`outcome`、`relation`、`task_tag`，建议补 `context`） |
| 稳定事实 | `record_fact`（`key` / `value`） |
| 教训被证伪 | `invalidate_decision`，不另记一条相反结论 |

## 端到端验证（2026-11-15）

1. Codex 调用 `record_decision` 写入一条：「Node 脚本在 fetch 句柄未关闭时调用 `process.exit()`」→（caused）→「Windows 上触发 libuv 断言崩溃」。
2. Claude Code 无头模式（`claude -p`）调用 `intervention_query`，查询「在 Windows 的 Node hook 脚本里调用 `process.exit()`」，返回 ⚠️ DANGER 并引用上一步的教训。
3. LLM 返回 402 时，经 stdio 直接调用 `record_decision` 与 `search_memory`，两者均返回 `isError: false`。
4. DeepSeek 续费后再跑 `distill --dry-run`，不再报 402；模型对一段两轮的测试对话给出「nothing worth remembering」，说明请求与结果解析正常，提炼环节本身也会过滤无价值内容。

## 适用边界

- 新注册的 MCP 要在客户端重启后才会出现在当前会话里。
- 没有自动召回，是否查询取决于 Agent 是否遵守规则；需要时可加 PreToolUse hook，在 Bash 命令前调用 `intervention_query`。
- 只用 BM25 时的中文检索效果尚待更多样本验证。
- 项目处于 alpha 阶段，README 中工具数量、测试数量有前后不一致之处，评测为项目方自报。
