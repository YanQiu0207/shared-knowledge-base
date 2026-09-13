---
status: verified
source: 本地实测（memory-hub 8125 的 HTTP 探测与前端 bundle 检查）+ Claude Code Hook 源码（~/.claude/hooks/tdai_memory_hook.py）与 .admin-key 文件存在性核查
source_version: 2026-09-12
applies_to: TencentDB Agent Memory 三容器栈（memory-core 8420 / memory-hub 8125 / tdai-proxy 8096）的本机部署
excludes: 代理链路注入与检索机制（见 tencentdb-agent-memory-mechanics.md）；模型绑定与接入方式（见 tencentdb-agent-memory-proxy-mode.md、tencentdb-agent-memory-hook-mode.md）
---

# TencentDB Agent Memory 的面板 UI 与 user_key 位置

## 结论

- 管理面板就是三容器栈里的 memory-hub，本机地址 `http://127.0.0.1:8125`（页面标题「Memory Hub」）。记忆和技能都有管理界面，不止查看。
- 本机生效的 user_key 默认来自文件 `E:\github\TencentDB-Agent-Memory\deploy\global-images\.admin-key`，而非环境变量——`TDAI_MEMORY_USER_KEY` 未设时，Hook 回退读该文件。

## 面板能力（实测）

从前端 bundle 确认的接口与文案：

| 能力 | 接口 / 文案证据 |
| --- | --- |
| 记忆 | 记忆块、记忆池、场景记忆、会话数（`/api/v1/chat-memory`） |
| 技能 | 独立技能管理页；支持「共享 / 私密」切换、导入、绑定到 Agent（`/api/v1/skill`） |
| 知识库 | Wiki 创建与导入（`/api/v1/knowledge`） |
| Agent | 创建与级联删除（`/api/v1/agent/delete-cascade`）、总览（`/api/v1/agent-overview/bootstrap`） |
| 任务 | 任务与 Agent 关联列表（`/api/v1/task/list-with-agents`） |
| 鉴权 | `/api/v1/auth/*`，含 `preview-key` |

技能资产商店（`/v3/skill/*` API 背后的数据）在面板里有对应管理界面，不需要纯 curl 操作。

## user_key 解析链

`~/.claude/hooks/tdai_memory_hook.py` 的读取顺序：

1. 先读环境变量 `TDAI_MEMORY_USER_KEY`（`load_user_key()`，行 133）。
2. 未设时回退读 `TDAI_MEMORY_KEY_FILE` 指向的文件，默认 `E:\github\TencentDB-Agent-Memory\deploy\global-images\.admin-key`（行 38-41）。

实测（2026-09-12）：本机环境变量未设（`~/.claude/settings.json` 中也无），`.admin-key` 文件存在（39 字节），即生效凭据就是该文件内容。curl 调用 `/v3/skill/*` 等接口时，`x-tdai-user-key` 头填该文件内容。

## 边界与注意

- 面板含 `preview-key` 接口，大概率能在页面上直接看到这把 key（推断，未实测）。
- `.admin-key` 是凭据：任何文档、会话、知识库都只记文件路径，不得记录内容。
- 文件路径为 Windows 本机部署路径，其他机器按实际部署目录对应。

## 证据

- HTTP 探测：`GET http://127.0.0.1:8125/` 返回 200，HTML 标题「Memory Hub」。
- 前端 bundle（`/assets/main-CdwHEhgx.js`）：上表接口路径与「技能管理页」「共享 / 私密」等文案。
- Hook 源码：`tdai_memory_hook.py` 行 38-41（`KEY_FILE` 默认值）与行 133-142（`load_user_key()` 回退逻辑）；`.admin-key` 存在性以 `wc -c` 核实。

## 相关条目

- [记忆层工作机制（注入 · 记录 · 检索）](tencentdb-agent-memory-mechanics.md)——同一系统的运行机制；其「验证方法」提到的面板即本条目的 memory-hub。
- [Proxy 透明接入与模型绑定](tencentdb-agent-memory-proxy-mode.md)——三容器栈与端口分工。
