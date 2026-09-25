---
status: verified-with-limits
source: agmsg v1.4.2 源码与文档、本地 Windows CLI 诊断、用户收发验证
source_version: v1.4.2；2026-09-25
applies_to: 同一台 Windows 机器上，通过 Git Bash 与本地 SQLite 通信的 Claude Code 和 Codex CLI
excludes: Codex 桌面会话自动接入、跨机器同步、所有 Windows 版本均无黑框、把消息传输当作任务编排或验收
---

# agmsg：Claude Code 与 Codex CLI 的本机通信

## 结论

[agmsg](https://github.com/fujibee/agmsg/tree/v1.4.2) 用本地 SQLite 保存跨产品 Agent 消息；消息传输、会话身份绑定和实时投递是三件不同的事。Claude Code 可通过 Monitor watcher 接收消息；Codex CLI 的 Monitor 则需要经过 agmsg shim 启动、连接专用 app-server，并把当前 Codex thread 绑定到团队身份。仅加入团队或把项目模式设为 `monitor`，不能证明 Codex 已可实时接收。[来源：Codex Monitor 说明](https://github.com/fujibee/agmsg/blob/v1.4.2/docs/codex-monitor-beta.md)

本次 Windows 验证中，Codex 已以 `--remote` 启动、app-server 和 launcher 均在运行，但 `delivery.sh status` 报「有 thread 加载、没有记录会话」，消息仍未读。在**目标 Codex 会话**执行 `$agmsg actas <agent>` 后，用户确认实时收发成功。这里的成功是用户回报；未独立完成长期稳定性、恢复和跨机器测试。

## 最小接入路径

1. 安装 agmsg，并保证 Claude Code 与 Codex CLI 使用**同一 Git Bash `HOME` 和 SQLite 存储**。Windows 上不要让 `bash` 意外解析到 WSL；agmsg 的 Bash 脚本还要求 `sqlite3` 在其实际执行环境的 `PATH` 上。[来源：Windows 说明](https://github.com/fujibee/agmsg/tree/v1.4.2#windows-git-bash)
2. 在同一项目中分别通过 `/agmsg` 和 `$agmsg` 加入同一个 team，使用不同的 agent name。将需要实时接收的 Codex 项目设为 `monitor`。[来源：Quick Start](https://github.com/fujibee/agmsg/tree/v1.4.2#quick-start)
3. 从 PowerShell 启动 Codex CLI 时，让交互式 `codex` 经过 agmsg 的 [`codex-shim.sh`](https://github.com/fujibee/agmsg/blob/v1.4.2/scripts/drivers/types/codex/codex-shim.sh)。shim 只在 Monitor 项目中将交互式会话转到 [`codex-monitor.sh`](https://github.com/fujibee/agmsg/blob/v1.4.2/scripts/drivers/types/codex/codex-monitor.sh)；`codex exec` 等非交互命令仍透传。修改 PowerShell Profile 后必须新开终端，或在当前终端重新加载 Profile；已经运行的 Codex 会话不会自动切换启动方式。
4. 新 Codex 会话发送首轮消息后，检查 `delivery.sh status codex "$(pwd)"`。如果已有 `--remote` 会话和 app-server，但团队身份没有记录到该 thread，在**该会话内**执行 `$agmsg actas <agent>`，再做新的消息收发测试。[来源：会话记录脚本](https://github.com/fujibee/agmsg/blob/v1.4.2/scripts/drivers/types/codex/codex-record-session.sh)

## Windows 兼容边界

- `npx agmsg@1.4.2` 的引导器用 `spawnSync('bash', ...)` 执行临时 `setup.sh`。若 PowerShell 的 `PATH` 先命中 WSL `bash.exe`，WSL 不能按 Git Bash 的方式打开 `C:/.../setup.sh`；应先核对 `Get-Command bash -All`。PowerShell `Set-Alias bash` 不会改变 Node 子进程的可执行文件查找。[来源：npm 引导代码](https://github.com/fujibee/agmsg/blob/v1.4.2/bin/agmsg.js)
- Codex CLI 的 `--no-daemon` 与 Monitor 所需的 `--remote` 互斥。若个人启动脚本自动添加 `--no-daemon`，Monitor 会报 `--no-daemon cannot be used with --remote`。本次验证在启动脚本中移除此参数后可建立桥接；用户当时观察到未再出现黑框，但这**不保证**后续工具、MCP 或其他会话不弹窗。黑框问题的独立证据与边界见[已验证踩坑](../../issues/codex-windows-managed-daemon-console-windows.md)。[来源：Monitor 拼参](https://github.com/fujibee/agmsg/blob/v1.4.2/scripts/drivers/types/codex/codex-monitor.sh#L302-L311)
- PowerShell 的 `codex` 函数只拦截从该 Shell 发起的 CLI 命令；点击图标打开的 Codex 桌面会话不会经过它。agmsg v1.4.2 的这条 Monitor 桥接面向 CLI TUI，不能据此声称桌面会话也已实时接入。[来源：Codex Monitor 说明](https://github.com/fujibee/agmsg/blob/v1.4.2/docs/codex-monitor-beta.md)

## 不改变消息状态的诊断顺序

1. `history.sh <team>`：确认消息已写入以及未读标记；不要先用会标记已读的 `inbox.sh` 做诊断。
2. `delivery.sh status codex "$(pwd)"`：区分「仅配置 `monitor`」与「已经记录当前 Codex 会话」。
3. 只读查看进程：确认交互式 `codex` 带 `--remote ws://...`，并有 agmsg 专用 `codex app-server --listen ws://...`。缺少 `--remote` 时先查实际启动入口；有 `--remote` 却无会话记录时，优先检查目标会话的身份绑定。
4. `scripts/drivers/types/codex/watch-once.sh "$(pwd)" codex --team <team> --name <agent> --timeout 0`：`status=pending` 表示存在未读消息，不能单凭它判断桥接已工作。[来源：只读 pending 检查](https://github.com/fujibee/agmsg/blob/v1.4.2/scripts/drivers/types/codex/watch-once.sh)

agmsg 只传文本和引用，不替代任务认领、停止条件、代码隔离或最终验收；跨 Agent 的结果仍须回到代码、测试和运行证据核实。[来源：项目 FAQ](https://github.com/fujibee/agmsg/tree/v1.4.2#faq--design-notes)
