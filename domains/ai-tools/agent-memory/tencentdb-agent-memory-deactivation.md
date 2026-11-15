---
scope: cross-project
status: verified
source: 本机 TencentDB Agent Memory 部署的配置、日志、计划任务与容器状态实测
source_version: 本地镜像构建于 2026-09-07，部署脚本基于源码 51264f5（2026-09-13）；停用日期 2026-11-15
applies_to: 停用以 Docker 部署、并由计划任务守护的 TencentDB Agent Memory，且需要可回滚
excludes: 删除数据或镜像、升级到新版本、团队共享部署
---

# TencentDB Agent Memory 停用记录

## 结论

- 停用原因：proxy 模式逐轮记录对话并调用独立 LLM 提炼，成本随对话量增长，而产出的记忆大多无用；提炼模型的 DeepSeek 余额耗尽后，系统处于「只记录不产出」的状态。成本数据见 [工具调研与选型](comparison.md#tencentdb-agent-memory-的成本实测)。
- **只停容器不够**：一个每 5 分钟运行的守护计划任务会把三件套重新拉起。必须先从托管配置里移除守护任务，再停容器。
- 采用「停用、保留数据」：容器、镜像、数据卷均保留，可随时恢复。记忆层改用 [causal-memory](causal-memory-setup.md)。

## 自动拉起的来源

| 机制 | 说明 | 处理 |
| --- | --- | --- |
| 计划任务 `CustomTask-memory-guard` | 每 5 分钟运行 `mymemory.py`，发现三件套未全部 healthy 就按 core → hub → proxy 重建拉起 | 在 `mytasks.toml` 中注释该任务，再注销计划任务。只注销不改配置的话，下次 `mytasks.py refresh` 会把它建回来 |
| 容器重启策略 | `tdai-proxy-shared` 为 `unless-stopped` | 全部改为 `docker update --restart=no` |
| Docker Desktop 登录自启 | 只会拉起重启策略非 `no` 的容器 | 不需要处理 |

实测：守护任务注销前的最后一次运行，在停容器后约 2 分钟把三个容器全部拉起，说明必须先处理守护任务。

## 停用步骤

1. 导出数据：`docker cp tdai-memory-core:/data/tdai-memory/<records|profiles|skills> <导出目录>`。
2. 注释 `mytasks.toml` 中的 `memory-guard` 段，并执行 `Unregister-ScheduledTask -TaskName CustomTask-memory-guard`。
3. 停容器并关闭自动重启：`tdai-memory-core`、`tdai-memory-hub`、`tdai-proxy`（8096）、`tdai-proxy-shared`（8097，Codex 实际使用的 proxy）。
4. Codex：注释 `~/.codex/config.toml` 中的 `model_provider = "team-proxy"`，回到 ChatGPT 登录直连，并实测 `codex exec` 可用。
5. Claude Code：移除 tdai-memory MCP 与召回 hook。
6. 验证：8096、8097、8420 端口的 `/health` 均无响应，`docker ps --filter name=tdai` 为空，计划任务列表中不再有 memory-guard。

## 回滚

1. 取消 `mytasks.toml` 中 `memory-guard` 段的注释，执行 `python mytasks.py refresh`。
2. `docker start tdai-memory-core tdai-memory-hub tdai-proxy tdai-proxy-shared`；守护任务也会自动拉起三件套，但不包括 `tdai-proxy-shared`。
3. 取消 Codex `model_provider` 一行的注释。
4. 提炼前先确认 DeepSeek 余额，否则仍会持续报 `Insufficient Balance`。

## 相关经验

- Codex 接 proxy 时若使用 ChatGPT 订阅，需关闭 proxy 鉴权才能透传订阅 token，此时会话初始化也随之关闭；历史记忆记录显示此配置下记忆注入不生效。本条未在停用前复核。
- 官方至 v2.0.3 仍只为 Claude Code 与 Codex 提供 proxy 接入；改走 hook + MCP 需要自建桥接。
