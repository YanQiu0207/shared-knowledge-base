---
status: verified-local
source: https://github.com/rohitg00/agentmemory
source_version: 0.9.28
applies_to: Windows 10/11、Node.js、Claude Code、Codex CLI/Codex Desktop、本地单机记忆服务
excludes: 远程部署、团队共享服务的鉴权与备份、LLM 供应商密钥配置、插件升级后的绝对路径维护
---

# AgentMemory：跨 Coding Agent 的本地持久化记忆层

## 结论

AgentMemory 是一个面向 Coding Agent 的本地持久化记忆服务。它通过 Hook 捕获会话与工具事件，并通过 MCP 向 Claude Code、Codex 等客户端提供检索、写入和会话查询能力。

在默认配置下，无需 API Key 即可运行 BM25 与本地嵌入检索；LLM 压缩与自动上下文注入需要显式启用，且会产生额外 Token 成本。

本地嵌入可通过 `EMBEDDING_PROVIDER=local` 启用。AgentMemory v0.9.28 在该配置下使用 on-device 的 `all-MiniLM-L6-v2`，输出 384 维向量，不经过 Ollama 或远程 Embedding API。

## 特点

- **跨客户端共享**：多个已接入的 Coding Agent 连接同一台本地服务时，可复用同一份记忆。
- **自动捕获**：Claude Code 插件注册 12 个生命周期 Hook；Codex 插件注册 6 个 Hook。
- **显式 MCP 操作**：可使用 `memory_smart_search`、`memory_save` 等 MCP 工具查询或写入记忆。
- **本地优先**：服务默认监听 `127.0.0.1`；REST、流和查看器默认端口分别为 `3111`、`3112`、`3113`。
- **分层原则**：记忆只作待核对的上下文，不替代代码、配置、测试、运行证据或受版本管理的知识库。

## Windows 安装

以下步骤适用于 Native Windows。`agentmemory connect` 在 Windows 上当前不支持自动接线，因此 Claude Code 与 Codex 应使用插件安装；Codex Desktop 还需配置全局 Hook workaround。

1. 安装 CLI：

    ```powershell
    npm install -g @agentmemory/agentmemory
    ```

2. 安装与 AgentMemory 兼容的 `iii-engine` v0.11.2：下载官方 Windows 发行包中的 `iii.exe`，放到 `%USERPROFILE%\.localin\iii.exe`，并验证版本。

    ```powershell
    & "$HOME/.local/bin/iii.exe" --version
    ```

3. 启动服务，并验证本地健康状态：

    ```powershell
    agentmemory
    Invoke-WebRequest http://127.0.0.1:3111/agentmemory/health
    ```

4. 安装 Claude Code 插件：

    ```powershell
    claude plugin marketplace add rohitg00/agentmemory
    claude plugin install agentmemory
    ```

5. 安装 Codex 插件：

    ```powershell
    codex plugin marketplace add rohitg00/agentmemory
    codex plugin add agentmemory@agentmemory
    ```

6. 重启 Claude Code 与 Codex，并确认 AgentMemory MCP 工具可用。

## Claude Code Hook 手动接线（Windows 兜底）

Windows 上 `agentmemory connect claude-code --with-hooks` 不被支持（`--dry-run` 报 "manual install required"）。若插件安装未自动接线 Hook，按以下手动配置（本机已验证）：

1. 定位插件目录（npm 全局）：`%APPDATA%\npm\node_modules\@agentmemory\agentmemory\plugin\`。其中 `hooks\hooks.json` 是 Hook 模板（含 12 个事件），`scripts\*.mjs` 是各事件脚本。

2. 把模板里所有 `${CLAUDE_PLUGIN_ROOT}` 替换为该 plugin 目录的绝对路径（建议用正斜杠，避免 JSON 反斜杠转义）。

3. 深合并进 `~/.claude/settings.json`（保留已有键）：
    - `hooks`：并入模板的 12 个事件，每个 command 形如 `node "<plugin 目录>/scripts/session-start.mjs"`。
    - 顶层 `env`：补 `AGENTMEMORY_URL`、`AGENTMEMORY_SECRET`、`AGENTMEMORY_INJECT_CONTEXT`。
    - `mcpServers.agentmemory`：`command` 为 `npx`，`args` 为 `["-y", "@agentmemory/mcp"]`，env 同上。

4. 重启 Claude Code 生效。agentmemory 升级后若脚本目录带新版本号路径，需重新展开 `${CLAUDE_PLUGIN_ROOT}`。

## Codex Hook 安装（plugin 自动，Windows 已验证）

与 Claude Code 不同，Codex 在 Windows 上 plugin marketplace 正常工作，无需手动接线 Hook：

1. 安装：`codex plugin marketplace add rohitg00/agentmemory`，再 `codex plugin add agentmemory@agentmemory`。

2. plugin 启用后自动注册 6 个 Hook（`SessionStart`、`UserPromptSubmit`、`PreToolUse`、`PostToolUse`、`PreCompact`、`Stop`）与 MCP 工具。Hook 定义来自插件 `hooks/hooks.codex.json`，脚本缓存在 `~/.codex/plugins/cache/agentmemory/agentmemory/<版本>/scripts/`；MCP 由插件 `.codex-plugin/plugin.json` 指向的 `.mcp.json` 自动提供，**不写入 `config.toml` 的 `[mcp_servers]`**（这是正常的，不是缺失）。

3. 验证（`~/.codex/config.toml`）：`[plugins."agentmemory@agentmemory"] enabled = true`、`[hooks.state."agentmemory@agentmemory:hooks/hooks.codex.json:..."]` 出现 6 条、`[features] hooks = true`。

4. 环境变量：Codex 不读 `~/.claude/settings.json`，Hook 进程靠 Windows 用户环境变量拿 `AGENTMEMORY_URL`、`AGENTMEMORY_SECRET`、`AGENTMEMORY_INJECT_CONTEXT`（见「Hook 环境变量（Windows 实证）」节的注册表写法）。设后重启 Codex 生效。

## Codex Desktop 注意事项

当前 Codex Desktop 不会派发插件目录中的 `hooks.json`。插件的 MCP 工具仍可用，但自动捕获不会生效。

在该限制修复前，将 Codex 插件提供的 6 个 Hook（`SessionStart`、`UserPromptSubmit`、`PreToolUse`、`PostToolUse`、`PreCompact`、`Stop`）镜像写入 `~/.codex/hooks.json`，并把 `${CLAUDE_PLUGIN_ROOT}` 替换为已安装插件的绝对路径。插件升级后必须重新检查这些绝对路径。

## Hook 环境变量（Windows 实证）

Hook 脚本（`session-start.mjs` 等）只读 `process.env`，不读 `~/.agentmemory/.env`。关键变量：

- `AGENTMEMORY_URL`（默认 `http://localhost:3111`）。
- `AGENTMEMORY_SECRET`（服务端设了 secret 就必填，否则 Hook 401）。
- `AGENTMEMORY_INJECT_CONTEXT`（`true`/`false`，控制是否把记忆注入回 prompt）。

Windows 下让 Hook 进程拿到这些变量的两条路径：

- **Claude Code**：写入 `~/.claude/settings.json` 顶层 `env` 字段，Claude Code 会注入到 Hook 子进程。
- **Codex 等不读 settings.json 的客户端**：写入 Windows 用户环境变量。避免用 `[Environment]::SetEnvironmentVariable(...,'User')`——它会同步广播 `WM_SETTINGCHANGE`，遇无响应窗口会阻塞挂起；改用直接写注册表 `HKCU:\Environment`（`New-ItemProperty -Force`），新进程从注册表继承。

设环境变量后必须重启对应客户端才生效。

## 本地 Ollama 备用 LLM（Windows 实证）

云 LLM 为主用时，可用本地 Ollama 作断网或限流的兜底，通过 OpenAI 兼容端点接入，无需改 hook 或环境变量结构。

1. 安装 Ollama（服务自启）；CLI 不在 PATH 时用全路径 `%LOCALAPPDATA%\Programs\Ollama\ollama.exe`。

2. 拉模型：`ollama pull <模型名>`（如 `qwen2.5:7b`）。

3. 在 `~/.agentmemory/.env` 切换 LLM provider（注释云 LLM 三行，启用 Ollama 三行）：

    ```ini
    OPENAI_BASE_URL=http://localhost:11434/v1
    OPENAI_API_KEY=ollama
    OPENAI_MODEL=qwen2.5:7b
    ```

4. 重启 `agentmemory` 生效。`AGENTMEMORY_SECRET`、hook 环境变量、`EMBEDDING_PROVIDER=local` 均不用改（与 LLM provider 无关）。

显存约束（8 GB 实测）：`qwen2.5:7b`（q4，约 4.7 GB）加载后占约 6.9 GB / 8 GB（86%），偏紧——Ollama 默认 `num_ctx=2048`，consolidation 一批 observations 拼成的长 prompt 可能被截断；调大 `num_ctx` 又可能显存 OOM。兜底：换更小模型（如 `qwen2.5:3b`，显存宽松可开大 context），或在 Modelfile 调整 `num_ctx`。

性能参考：首次加载模型约 70 s（一次性），暖推理约 2–3 s/次。

## 本地 Embedding（Windows 实证）

Embedding Provider 与用于摘要、压缩的 LLM Provider 相互独立。在 `~/.agentmemory/.env` 中配置：

```ini
EMBEDDING_PROVIDER=local
```

AgentMemory v0.9.28 此时使用本地 `all-MiniLM-L6-v2` 生成 384 维向量，无需 Ollama、远程 Embedding API 或对应的 API Key。修改配置后需重启 AgentMemory。

## 开机自启（Windows 实证）

服务进程不随开机常驻，需配置自启。两种方式：

1. **任务计划程序（推荐，支持崩溃自愈）**——触发器「用户登录时」，动作 `powershell.exe -WindowStyle Hidden -Command "agentmemory"`，设 `RestartCount` 与 `ExecutionTimeLimit = Zero`。但 `Register-ScheduledTask` 在部分机器（组策略或 UAC）会「拒绝访问」，需管理员权限。

2. **注册表 `HKCU:\Software\Microsoft\Windows\CurrentVersion\Run`（用户级兜底，无需管理员）**——任务计划拒访时使用：

    ```powershell
    $amCmd = "$env:APPDATA\npm\agentmemory.cmd"
    Set-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run" `
        -Name "AgentMemory" -Value "powershell.exe -WindowStyle Hidden -NoProfile -Command `"& '$amCmd'`""
    ```

    登录时 explorer 自动触发，隐藏窗口启动。**局限**：无 `RestartCount`，崩溃不自动重启。

无论哪种方式，用 `.cmd` 全路径而非 `.ps1`——避开 ExecutionPolicy 限制（`RemoteSigned` 下本地 `.ps1` 一般可执行，但 `.cmd` 无此风险）。验证：注销重登后执行 `agentmemory status`，或查看 `~/.agentmemory/server.stderr.log` 的 Provider 行。

## 使用方法

- **日常使用**：让 Hook 自动捕获会话事件；将自动注入的上下文视为候选信息，并以当前证据核实。
- **主动检索**：在需要历史决策、已验证故障或会话摘要时，调用 AgentMemory MCP 的检索工具。
- **主动写入**：仅记录已确认、可复用、已脱敏的偏好、约束、决策或经验；不要写入密钥、令牌、私人数据、完整日志和未经确认的推断。
- **配置增强**：在 `~/.agentmemory/.env` 配置 LLM Provider 后，可按需要启用 `AGENTMEMORY_AUTO_COMPRESS=true` 与 `AGENTMEMORY_INJECT_CONTEXT=true`。`AGENTMEMORY_INJECT_CONTEXT=true` 会让 PreToolUse、SessionStart Hook 每个 tool turn 注入约 4000 字符记忆上下文，按 tool-call 频率持续消耗 session token；启用前据自身调用频率评估成本，token 敏感场景建议先关闭、攒够记忆后再开。
- **停止服务**：运行 `agentmemory stop`；服务数据默认保存在用户目录下，由本机负责备份与清理。

## 边界

- 仅限本机个人或受控环境的接入经验，不覆盖远程部署、团队共享、鉴权、数据保留与备份策略。
- `AGENTMEMORY_SECRET` 一旦设置，连 127.0.0.1 loopback 也强制 Bearer 鉴权（实测不带 auth 返回 401）。因此本地多客户端接入时，每个 Hook 进程都必须能读到该 Secret，否则 Hook 调用全部 401；远程暴露前同样必须配置，并单独评估网络边界与数据安全。
- 公共知识库只保存通用方法；具体用户目录、插件缓存绝对路径、项目事实和本地密钥不得写入本条目。

## 证据

- [AgentMemory 官方 README](https://github.com/rohitg00/agentmemory)：安装、客户端插件、Windows 运行时与 Codex Desktop workaround。
- 本机已验证：AgentMemory v0.9.28、`iii-engine` v0.11.2、Claude Code 与 Codex 插件安装，以及 `http://127.0.0.1:3111/agentmemory/health` 健康检查。
- 本机实证补充：经源码 grep 确认 Hook 脚本只读 `process.env`、不读 `~/.agentmemory/.env`；不带 Bearer 调 `/agentmemory/health` 与 `/agentmemory/search` 均返回 401（loopback 也强制鉴权）；接入 OpenAI 兼容 LLM 后 `mem::summarize` 实际被调用并产出会话标题。
- 本机配置实证：AgentMemory v0.9.28 的 `~/.agentmemory/.env` 使用 `EMBEDDING_PROVIDER=local`，配置说明标注模型为 `all-MiniLM-L6-v2`、向量维度为 384，且不经过 Ollama。
