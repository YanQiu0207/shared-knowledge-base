---
status: verified-with-limits
source: 本地进程与窗口观察、Codex CLI --help、用户重启后观察；openai/codex Issue #46949、#48029
source_version: 2026-09-25
applies_to: Windows 上 Codex 使用共享 managed app-server daemon，且启动本地工具、内置 runtime 或 stdio MCP 子进程的场景
excludes: 所有 MCP 启动都必定弹窗、所有 Codex 运行方式、上游代码根因已经得到本机验证、无 daemon 模式保留共享会话能力
---

# Windows Codex managed daemon 启动子进程时出现黑框

## 结论

Windows 上出现多个持续可见的控制台窗口时，先检查它们是否由 Codex 的 managed app-server daemon 启动，不要仅凭窗口数量归因于 MCP、Hook 或通知。可见窗口可能分别属于内置 runtime、stdio MCP 和工具进程；每轮短暂闪现的 `git.exe` 窗口还可能属于另一条启动路径。

在一台受影响的机器上，给 CLI 启动命令加入 `--no-daemon`，重新启动后用户观察到「看起来不会弹黑框」。另有 [#46949 的报告者](https://github.com/openai/codex/issues/46949)给出普通启动弹窗、`--no-daemon` 不弹的对照。**这是绕过办法，不是上游修复，也不能证明所有窗口的根因相同。**

## 证据与边界

- [openai/codex #46949](https://github.com/openai/codex/issues/46949)记录了 Windows managed daemon 启动 `node_repl.exe`、`node.exe`、Code Mode Host 和 stdio MCP 时出现可见窗口；截至 2026-09-25，该 Issue 仍为 open。Issue 中的进程链和复现结论属于报告者证据，不等同于每台机器都已复现。
- 本地窗口与进程检查曾观察到 `node_repl.exe`、`node.exe`、`cmd.exe` 等持续窗口，并看到工具调用时新建的 `pwsh.exe` 可见窗口。会话启动时的 MCP 窗口和逐轮工具窗口应分开定位。
- 本地 `codex --help` 将 `--no-daemon` 描述为「即使共享后台服务已运行，也不使用它」。重启后的无黑框现象是用户观察，未对 Desktop App、所有 MCP 和长期运行做完整回归。
- [openai/codex #48029](https://github.com/openai/codex/issues/48029)单独分析每轮开始的 Git 检查短暂弹窗，指向 Windows 子进程创建标志；它不能直接证明 #46949 所有常驻窗口共用同一代码缺陷。

## 排查与临时处理

1. 记录窗口出现时机：打开会话、每次提交消息，还是实际执行工具命令时。
2. 抓取可见窗口对应的进程、父进程、命令行和创建时间；确认是否由 managed app-server daemon 启动，再区分内置 runtime、MCP 和工具命令。
3. 若使用 CLI，可在**新会话**运行 `codex --no-daemon` 做对照。若窗口消失，可临时保留此参数并继续关注上游修复；若仍弹窗，重新抓父进程链，不要继续按 daemon 路径盲修。
4. `--no-daemon` 绕过共享后台服务；依赖共享 daemon 的会话或远程控制能力可能受影响，使用前按当前 Codex 版本实测。不要靠关闭窗口、杀死活跃 MCP 或替换各个发行版二进制来假装修复。

## 长期修复方向

由 Codex 上游在 Windows 的非交互式子进程启动路径中抑制可见控制台窗口，同时保留 stdio 管道和进程生命周期。当前条目不声称 #46949 已有合并或发布的修复；升级后须重新做有 daemon／无 daemon 对照。
