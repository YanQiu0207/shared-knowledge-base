---
scope: cross-project
status: provisional
source: openai/codex-plugin-cc 仓库（v1.0.4）插件内 command 文件 + 本机 Codex CLI 0.145.0 的 setup 验证
source_version: 2026-07-26（插件 1.0.4 / codex-cli 0.145.0）
applies_to: 在 Claude Code 中调用本机 Codex 做「第二意见」代码审查或任务委派的个人开发者
excludes: Codex CLI 本身的安装排障与登录合规、Codex 模型能力评测、以及非 Claude Code 宿主调用 Codex 的方式
---

# codex-plugin-cc：Claude Code 内调用 Codex 的官方插件

## 结论

`openai/codex-plugin-cc` 是 OpenAI 官方维护的 Claude Code 插件：在 Claude Code 中以 marketplace `openai-codex`、插件名 `codex` 注册，插件本身不含业务逻辑，只通过 `codex-companion.mjs` 调度本机已安装的 Codex CLI。用途是在 Claude Code 会话内获得「另一个模型家族」的独立审查或委派执行。

它是 [Codex 与 Claude Code 调用其他 Coding Agent](cross-coding-agent-orchestration.md) 中「Claude Code 调用 Codex」方向的官方落地，与第三方 `skills-directory/skill-codex` 或 `codex mcp-server` 是并列可选项，而非同一方案的变体。

## 前置条件

- 本机已全局安装 `@openai/codex` CLI 并完成登录（ChatGPT 登录或 API Key）。
- 安装插件后用 `/codex:setup` 验证：返回 `ready: true` 才算全链路就绪；`ready: false` 时按提示安装 CLI 或执行 `codex login`。

## 命令清单

7 个斜杠命令（命名空间 `/codex:`）：

| 命令 | 定位 | 是否改代码 |
| --- | --- | --- |
| `/codex:setup` | 环境检查、开关 stop-time 审查门禁 | 否 |
| `/codex:review` | 对 git 改动做 Codex 代码审查 | 否（只读） |
| `/codex:adversarial-review` | 对抗式审查，质疑设计与取舍，可带 focus 文本 | 否（只读） |
| `/codex:rescue` | 把任务委派给 Codex 执行 | 是（Codex 动手） |
| `/codex:status` | 查看本会话/本仓库的 Codex 任务进度 | — |
| `/codex:result` | 取回已完成任务的完整结果 | — |
| `/codex:cancel` | 取消后台任务 | — |

`review` 与 `adversarial-review` 都是 review-only：只输出 Codex 的发现，不改代码、不打补丁。要让 Codex 实际修改代码，用 `/codex:rescue`。

## 高频参数

第一档（几乎每次都用）：

| 参数 | 适用命令 | 作用 |
| --- | --- | --- |
| `--background` / `--wait` | review、adversarial-review、rescue | 后台跑 vs 前台等。不传时插件先估算改动量再问；≤1-2 文件建议 `--wait`，其余 `--background` |
| `--base <ref>` | review、adversarial-review | 审查基线。审整条分支最常用，如 `--base main` 表示「本分支相对 main 的全部改动」 |

第二档（按场景）：

| 参数 | 适用命令 | 作用 |
| --- | --- | --- |
| `<job-id>` | status、result、cancel | 定位具体后台任务；不传则列全部 |
| `--scope auto\|working-tree\|branch` | review、adversarial-review | 审查范围，默认 `auto`；仅审未提交改动用 `--scope working-tree`。两命令都不支持 staged/unstaged |
| `<focus 文本>` | adversarial-review 专属 | flags 后接自然语言焦点，如 `--base main 重点看并发安全` |

第三档（低频）：

- rescue 专属：`--resume` / `--fresh`（续上次 Codex 线程或开新的）、`--model spark`（映射 `gpt-5.3-codex-spark`）、`--effort none|minimal|low|medium|high|xhigh`。
- setup 专属：`--enable-review-gate` / `--disable-review-gate`（一次性配置「停止前强制审查」门禁）。

## 典型流程

审整条分支（前台等）：

```text
/codex:review --base main --wait
```

后台审查后取回：

```text
/codex:review --base main --background
/codex:status              # 列全部任务，拿到 job-id
/codex:status <job-id>     # 盯单个任务进度
/codex:result <job-id>     # 取完整结果
```

带焦点的对抗式审查：

```text
/codex:adversarial-review --base main --background 重点看资源释放与并发
```

## 不要这样用

- 不要期待 `/codex:review` 改代码；它是只读审查。要修代码用 `/codex:rescue`。
- 不要在 `/codex:review` 后追加 focus 文本，会被忽略；带焦点必须用 `/codex:adversarial-review`。
- 不要跳过 `/codex:setup` 直接用；CLI 未登录或未安装时命令会失败，且错误信息不一定直观。

## 与通用方法的关系

本条目是具体插件的命令参考。何时该用跨产品 Agent、安全约束与多方案选型对比见 [Codex 与 Claude Code 调用其他 Coding Agent](cross-coding-agent-orchestration.md)；该条目已点明 `openai/codex-plugin-cc` 的调用方向，本条目补全其命令与参数。

## 证据与限制

- [openai/codex-plugin-cc](https://github.com/openai/codex-plugin-cc)
- 插件内 `commands/*.md`（review / adversarial-review / rescue / status / result / cancel / setup 的 argument-hint 与执行规则）。
- 本机验证：codex-cli 0.145.0 + 插件 1.0.4，`/codex:setup --json` 返回 `ready: true`。

本条目状态为 `provisional`：命令与参数基于插件 1.0.4 的 command 文件和一次 setup 验证；不同插件版本或 codex-cli 版本的参数集合、默认行为（尤其后台执行与 review-gate）可能变化。升级后应重新核对命令定义。
