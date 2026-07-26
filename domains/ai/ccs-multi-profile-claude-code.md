---
scope: cross-project
status: provisional
source: CCS 官方 GitHub README、OpenAI-compatible Provider Routing 文档与 Windows 本机最小调用验证
source_version: 2026-07-25
applies_to: 希望保留 Claude Code 使用习惯，同时按供应商或模型并行运行独立 Coding Agent 会话的个人与小团队
excludes: CCS 的账号合规性、供应商模型能力评测、企业级多租户网关治理，以及任意第三方协议转译服务的安全审计
---

# CCS：保留 Claude Code 的多供应商并行 Profile

## 结论

`kaitranntt/ccs` 是一个开源 Profile 与运行时管理器：它启动的仍是 Claude Code，而不是替换为另一套 Coding Agent。不同 Profile 在启动时各自注入端点、凭据和模型配置；对于 OpenAI 兼容 API，CCS 会为每个 Profile 启动独立的本地 Anthropic 兼容代理与端口。因此可用 `ccs <profile>` 分别启动多个会话，避免像共享全局配置那样在切换时影响已运行的会话。

实际使用中，把「选择 Profile」放在**启动会话时**，不要在会话运行期间改写全局 Claude 配置。写代码的并发会话仍应位于不同 Git worktree，避免模型隔离正确但文件修改互相覆盖。

## 适用边界

| 需求 | CCS 是否适合 | 说明 |
| --- | --- | --- |
| 保留 Claude Code 终端交互与工具链 | ✅ | CCS 作为启动器，后端进程仍为 Claude Code。 |
| GLM、Kimi 等不同 API 同时运行 | ✅，需实测 | 每个供应商建独立 Profile，再在不同终端启动。 |
| OpenAI 兼容 API 接入 Claude Code | ✅，需本地代理 | CCS 将 Claude Messages 请求转成 OpenAI Chat Completions，并把流式响应转回 Anthropic SSE。 |
| 已运行会话不受另一个 Profile 切换影响 | ✅，按设计 | 不同兼容 Profile 使用不同本地端口；应以本机双会话验证为准。 |
| 多会话同时改同一工作目录 | ❌ | 工具隔离不等于文件隔离，仍需 Git worktree。 |
| 让第三方模型获得官方 Claude Code 支持 | ❌ | 这是第三方协议转译，不能视为 Anthropic 官方支持。 |

## 最小操作流程

### 1. 安装并打开本地配置界面

```powershell
npm install -g @kaitranntt/ccs
ccs config
```

`ccs config` 会打开本机 Web 配置面板；供应商、API Key 和模型可在面板中维护，无需手写 `~/.claude/settings.json`。

### 2. 创建 Profile

为每个供应商创建独立 Profile，例如 `glm`、`kimi`。配置时应核对：

- API 协议类型：Anthropic Messages 或 OpenAI Chat Completions；
- Base URL 与模型 ID：以供应商当前官方控制台为准；
- API Key：只保存到本机 CCS 配置，不提交仓库、不粘贴到聊天或日志；
- 模型的上下文与工具调用限制：先跑只读小任务确认。

Kimi 的标准 API 是 OpenAI 兼容接口；若将它接到 Claude Code，CCS 需要启用其本地 Anthropic 兼容转译路径。GLM 若购买入口提供 Anthropic Messages 端点，则可作为原生 Anthropic 兼容 Profile 使用。

### 3. 启动独立会话

```powershell
# 终端 A
ccs glm

# 终端 B
ccs kimi
```

在每个 Claude Code 会话执行 `/status`，检查 Base URL、认证方式和模型是否符合预期。对于 OpenAI 兼容 Profile，Base URL 应为 CCS 的本机 `127.0.0.1:<port>` 代理地址，而不是直接显示供应商 URL。

### 4. 并行写代码时使用 worktree

```powershell
git worktree add ..\project-glm -b local/ccs-glm
git worktree add ..\project-kimi -b local/ccs-kimi
```

再分别进入两个 worktree 运行 `ccs glm` 与 `ccs kimi`。完成后以常规 Git diff、测试和 Review 收口。

## 不要这样用

- 不要使用 `ccs persist` 把某个 Profile 持久写入全局 `~/.claude/settings.json`；这会重新引入跨会话配置干扰。
- 不要在 CCR 等共享路由器中改「当前全局 Profile」后期待旧会话保持原路由。
- 不要因为同名模型或接口都宣称「兼容」就跳过验证；必须核对协议、工具调用、流式输出和上下文限制。

## Windows 注意事项

在一次 Windows 本机验证中，CCS `v8.8.1` 的 `ccs <profile> -p` 路径可能错误调用 Unix 的 `command -v`，导致找不到已安装的 Claude Code。可将 Claude 二进制路径配置给 CCS 后重新打开终端：

```powershell
[Environment]::SetEnvironmentVariable(
    "CCS_CLAUDE_PATH",
    "$HOME\.local\bin\claude.exe",
    "User"
)
```

这是一条版本相关的本机观察，不代表所有 Windows 安装都会复现；升级 CCS 后应重新验证。

## 验收清单

1. `ccs api list` 显示目标 Profile。
2. 各 Profile 的只读最小请求成功。
3. 两个终端同时运行时，`/status` 显示不同预期端点或模型。
4. 关闭、重配或切换其中一个 Profile 后，另一个会话仍能继续响应。
5. 并行写入时，两个会话位于不同 worktree。

## 证据与限制

- [CCS README](https://github.com/kaitranntt/ccs)
- [CCS OpenAI-compatible Provider Routing](https://github.com/kaitranntt/ccs/blob/main/docs/openai-compatible-providers.md)
- [Kimi OpenAI API 协议兼容性说明](https://platform.moonshot.cn/docs/guide/migrating-from-openai-to-kimi)
- [Claude Code 网关边界](https://code.claude.com/docs/en/llm-gateway)

本条目状态为 `provisional`：CCS 的多 Profile 与本地端口设计有项目文档和最小实测支持，但不同供应商的工具调用、长上下文、流式输出与费用统计仍可能存在协议差异。接入新供应商前，应先在隔离 worktree 中跑只读任务，再允许写入。
