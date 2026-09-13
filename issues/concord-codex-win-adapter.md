---
scope: cross-project
status: verified
source: 本地实测（Windows 11 + Node 24 + Codex CLI 0.154.0 npm 版 + concord-mcp 0.10.4），源码定位 @concord-ai/concord-mcp/dist/install/adapters/index.js 的 run() 与 statusCodex()
source_version: 2026-09-13
applies_to: Windows 上用 npm 安装的 coding agent CLI 被 orchestration/adapter 工具探测与纳管的场景；任何用 Node spawnSync 直接调 npm .cmd 垫片的工具
excludes: macOS/Linux 上的 concord 行为、ChatGPT 桌面版与 Codex CLI 的功能冲突（实测无关）、concord 的消息协议与任务管理功能本身
---

# concord 在 Windows 误判 Codex 版本（npm 垫片 EINVAL）与 daemon 仅认 standalone 安装

## 结论

在 Windows 上 `concord setup` / `concord doctor` 把 Codex 适配器报为 `unsupported_version`，错误信息为 `Codex undefinedundefined lacks the verified app-server steering contract.`——其中 `undefinedundefined` 是决定性信号：**concord 从未读到过 codex 的版本号**。

根因是两层独立问题叠加：

1. **concord 的 Windows bug（主因）**：其 `run()` 用 Node `spawnSync` 裸调 PATH 里的 `codex.cmd`（npm 垫片）。Node ≥ 20.12 因 CVE-2024-27980 安全修复禁止无 `shell: true` 直接 spawn `.cmd/.bat`，返回 `EINVAL`，stdout/stderr 均为 `undefined`，被拼成字符串 `"undefinedundefined"`。已用最小脚本复现确认。
2. **Codex CLI 的设计限制（次因）**：绕过 bug 一后，`codex app-server daemon start/bootstrap` 硬编码只认 standalone 安装路径 `~\.codex\packages\standalone\current\bin\codex.exe`，npm 版直接报错拒绝启动 daemon；daemon 未启动时 `daemon version` 对缺失的控制 socket 报 os error 10050（误导性报错，不是网络问题）。

**ChatGPT 桌面版无关**：实测其使用 `\\.\pipe\codex-ipc` 等自己的管道，不占用 `~\.codex\app-server-control\` 控制位；安装 daemon 前后该目录均无冲突。

## 修复

安装 Codex 官方 standalone（与 npm 版并存，靠 PATH 定序）：

```powershell
irm https://chatgpt.com/codex/install.ps1 | iex
# PATH 新增 C:\Users\YanQi\AppData\Local\Programs\OpenAI\Codex\bin（用户级，排在 npm 前）
# 新开终端后 codex 解析到该目录下的 codex.exe（真 exe，非 .cmd 垫片）
codex app-server daemon bootstrap
codex app-server daemon start
codex app-server daemon version   # 应返回 {"status":"running",...}
```

真 exe 不触发 spawnSync EINVAL（bug 一顺带绕过）；daemon 起来后（bug 二消除）concord 状态变为 `installed`，能力从 `pull, busy` 恢复为 `pull, inject, steer, idle, busy`。

验证结果（concord doctor）：

```
claude-code  installed  native-monitor      pull, inject, steer, idle, busy
codex        installed  managed-controller  pull, inject, steer, idle, busy
```

## 适用边界与排查顺序

- **通用信号一**：Node 工具在 Windows 上对 npm 安装的 CLI 报「版本未知/undefined」，先怀疑 spawnSync 裸调 `.cmd` 垫片的 EINVAL（Node ≥ 20.12），而不是 CLI 本身没装或版本不满足。看错误信息里是否出现字面 `undefined` 拼接。
- **通用信号二**：工具报「socket 连接失败/已死的网络（os error 10050）」时，先确认对应 daemon 是否真的启动过，再怀疑环境冲突；10050 在这里是「控制文件存在但服务从未运行」的误导性翻译。
- **多份安装歧义**：standalone 与 npm 版并存靠 PATH 定序，旧终端不继承新 PATH（`where codex` 验证）；`daemon version` 返回的 `managedCodexPath` 可确认实际用的是哪份。
- concord 默认开遥测（存请求 IP + 国家、无自动过期），设 `CONCORD_TELEMETRY_DISABLED=1` 关闭。
