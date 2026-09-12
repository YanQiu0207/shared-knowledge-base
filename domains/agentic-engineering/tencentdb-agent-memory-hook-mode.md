---
status: verified-local
source: 本地实测（TencentDB Agent Memory feat/server_team @0468a2a 的 memory-core 8420）+ Claude Code hooks 官方文档（code.claude.com/docs/en/hooks）+ cc-switch 覆写实测
source_version: 2026-09-12
applies_to: 用客户端 Hook 接入 TencentDB Agent Memory 的本地 workstream（Claude Code / Codex），尤其是订阅制账号或需要免除逐会话交互的场景
excludes: Proxy 透明劫持方案（见同目录 tencentdb-agent-memory-proxy-mode.md）；MCP Bridge 显式调用方案（见同目录 tencentdb-agent-memory-claude-codex.md）；远程 Gateway 暴露与凭据托管
---

# TencentDB Agent Memory 的 Hook 接入（免 Proxy）

## 结论

Hook 是三条接入路径里唯一不占用模型链路的一条：它跑在客户端生命周期事件上，直接读写 memory-core。因此**订阅制账号天然可用**，也不会触发 proxy 的 session-init 交互。

代价是 Hook 只拿到客户端给出的东西：默认只有记忆召回与归档。`<session_context>`、`<available_skills>` 这类资产上下文需要自己按 memory-core 的原生接口补。

| 维度 | Hook（本篇） | Proxy | MCP Bridge |
| --- | --- | --- | --- |
| 接入位置 | 客户端生命周期事件 | 模型 API 链路 | MCP 工具 |
| 订阅制账号 | 可用 | 不可用（凭据争用 `Authorization`） | 可用 |
| 逐会话交互 | 无 | 新会话弹 team/agent/task 表单 | 无 |
| 记忆写入 | 自动（会话结束归档） | 自动（逐轮） | 手动 |
| 资产上下文 | 需自行补齐 | 内置 | 无 |

## 客户端契约

### Claude Code

配置位于 `~/.claude/settings.json` 的 `hooks`：

```json
{
  "hooks": {
    "UserPromptSubmit": [
      { "hooks": [ {
        "type": "command",
        "command": "C:\\Program Files\\Python311\\python.exe",
        "args": ["C:\\Users\\<user>\\.claude\\hooks\\tdai_memory_hook.py"],
        "timeout": 30,
        "statusMessage": "Recalling TencentDB memory"
      } ] }
    ],
    "SessionEnd": [
      { "hooks": [ {
        "type": "command",
        "command": "C:\\Program Files\\Python311\\python.exe",
        "args": ["C:\\Users\\<user>\\.claude\\hooks\\tdai_memory_hook.py"],
        "timeout": 20
      } ] }
    ]
  }
}
```

关键契约：

- 命令 hook 从 stdin 收 JSON：`session_id`、`transcript_path`、`cwd`、`permission_mode`、`hook_event_name`，以及 `UserPromptSubmit` 专有的 `prompt`。
- `UserPromptSubmit`、`SessionStart`、`UserPromptExpansion`、`PostModelSwitch` 的**纯文本 stdout 会作为上下文注入**；其它事件的 stdout 只进 debug 日志。
- stdout 若以 `{` 开头且以 `}` 结尾，会被当作 JSON 解析。注入内容不要长成 JSON 的形状。
- `timeout` 单位是秒：command 默认 600，`UserPromptSubmit` 被降到 30；`SessionEnd` 默认只有 1.5 秒预算，但**在配置里写更长的 timeout 可把预算提到最多 60 秒**。

### Codex

配置位于 `~/.codex/hooks.json`，事件名与 JSON 字段大体同构。两个差异必须记住：

- `SessionEnd` 的超时被硬限制在 1–3 秒，配置更大的值会被收窄，归档必须压缩成一次短请求。
- hook 需要先在交互模式用 `/hooks` 信任一次，否则配置了也不会执行。

## 客户端侧资产注入

Hook 默认没有 team/agent/task 身份，那是 proxy 的 session-init 交互选出来的。要在 Hook 侧补齐，需要自己确定身份并调用 memory-core 原生接口：

| 目的 | 接口 | 备注 |
| --- | --- | --- |
| 取 team | `POST /v3/meta/team/list` | header 需 `x-tdai-user-key`，body 需 `user_key` 或 `user_id`；两者缺一即 401/400 |
| 取 agent | `POST /v3/meta/agent/list` | 只需 `team_id` |
| agent/task 详情 | `POST /v3/meta/agent/get`、`POST /v3/meta/task/get` | 用于拼 `<session_context>` |
| skill 目录 | `POST /v3/skill/listing` | 传 `team_id` + `agent_id` + `query`，**直接返回渲染好的 `<available_skills>` 文本** |
| skill 正文 | `POST /v3/skill/get` | `skill_id` + `include_content` + `include_manifest` |
| 记忆召回 | `POST /v2/atomic/search`、`POST /v2/core/read` | 原子记忆与 core profile |
| 会话归档 | `POST /v2/conversation/add` | `session_id` + `messages[]` |

注意 proxy 注入的 `<skill_tools>` 配方指向 `/{proxy}/skill-bridge/*` 与 `/{proxy}/memory-bridge/*`，这两个桥接端点是 proxy 自己提供的。脱离 proxy 后必须把配方改写成 memory-core 原生端点，否则模型看得到 skill 目录却没有调用手段。

身份可以来自环境变量（显式指定），也可以自动发现（取用户可见的第一个 team/agent）。自动发现建议落一个带 TTL 的临时文件缓存，避免每轮都打三次元数据请求。

## 持久化：别被配置管理器冲掉

Windows 上常见的 provider 切换工具（如 cc-switch）在**切换 provider 时整份覆写** `~/.claude/settings.json` / `~/.codex/config.toml`。判定与做法：

- 判定：手工加的配置在这类工具的 provider 快照或公共配置里**没有对应条目**时，切换即丢。
- Claude Code：把 `hooks` 段写进它的**公共配置**（cc-switch 对应 `settings` 表的 `common_config_claude`），这样切换任意 provider 都会带上。
- Codex：`~/.codex/hooks.json` 是独立文件，天然不受 `config.toml` 覆写影响；但写在 `config.toml` 里的 MCP 注册会丢，需要同等对待。
- 改这类工具的数据库前先退出应用进程，并备份数据库文件。

## 坑

- **Windows 上的 shell 解析**：Claude Code 的 command hook 在 `args` 缺省时走 shell form，Windows 默认交给 Git Bash；本机 PATH 上的 `bash` 可能是 WSL 的，`.cmd` 包装会被静默吃掉。用 `args` 走 exec form（直接 spawn 可执行文件加参数）最稳。
- **静默失效最难查**：hook 不执行时不会报错。验证时先挂一个并行探针 handler（把收到的 payload 写一行到固定文件），可立刻区分「hooks 段没被加载」与「单个 handler 有问题」。
- **上层残留会互相打架**：公共配置里指向已卸载插件的 hooks 会持续报错，并长期占据事件段位，把新配置挤掉。
- **注入体积**：skill 目录应按 query 匹配，不要每轮灌全量清单。
- **`.cmd` 与解释器路径**：Windows 下不要依赖 `py.exe` 或 PATH 上的 `python`，用解释器绝对路径。

## 验证

```powershell
# 1. 注入：跑一轮真实会话，检查 transcript 是否出现注入块
#    关键词：TencentDB Agent Memory context / <session_context> / <available_skills>
# 2. 归档：memory-core 日志应出现
#    POST /v2/conversation/add status=200
# 3. 耗时：召回加资产注入实测约 0.2s（本地 memory-core）
```

本机实测（2026-09-12）：注入块出现在新会话 transcript；归档 `status=200`、耗时 54ms；hook 端到端约 0.22s。

## 边界

- Hook 路径**没有**交互式 team/agent/task 选择：身份要么固定，要么自动取用户可见的第一个。
- 本条目实测覆盖 Claude Code 侧；Codex 侧当时只做了记忆召回与归档，资产注入尚未补齐。
- proxy 的 `/skill-bridge/*`、`/memory-bridge/*` 不在 Hook 路径内，相关配方需要改写为原生端点。