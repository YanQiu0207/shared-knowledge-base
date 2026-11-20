# 已验证踩坑

## 结论

本主题保存已查证的现象、根因、修复与适用边界。只收经过实测或有可靠来源支撑的条目；未验证的怀疑留在项目内或交付报告中。

## 条目格式

- frontmatter 除根索引要求的必填字段外，新条目增加：
    - `triggers`：会踩到此坑的命令、文件、配置项或报错关键词，供动作前预警匹配。
    - `superseded_by`：仅在条目被新结论取代时填写新条目路径，同时把 `status` 改为 `superseded`；旧条目保留，不删除。
- 正文至少包含：结论（现象与根因）、错误做法 → 后果、修复或正确做法、适用边界。
- 「条目」列表的一句话摘要须写出主要触发词，使动作前预警只读本索引即可判断是否命中。

## 条目

- [第三方 API 中转改写 Claude Code 系统提示](relay-system-prompt-injection.md) — 中转可注入禁用 subagent、限制单次写入并要求静默服从的指令，能力降级不可见
- [思考内容回传缺失导致上游 400](thinking-passthrough-400.md) — 代理误剥离 thinking 签名，或客户端漏传 reasoning，均报 must be passed back
- [concord 在 Windows 误判 Codex 版本](concord-codex-win-adapter.md) — spawnSync 裸调 npm .cmd 垫片报 EINVAL（`undefinedundefined` 信号）；Codex daemon 仅认 standalone 安装
- [Windows Codex managed daemon 弹出控制台窗口](codex-windows-managed-daemon-console-windows.md) — 区分常驻 runtime／MCP 窗口与逐轮工具窗口；`--no-daemon` 可用于 CLI 对照与临时绕过
- [Devin 代理下 Opus 遇到 ScheduleWakeup 返回 400](devin-proxy-opus-schedule-wakeup-invalid-argument.md) — 禁用该工具后本次 Opus 文本请求成功；底层拒绝规则未确认
- [Clash fake-ip 下 ollama pull 卡住](ollama-pull-clash-fake-ip-non-public-redirect.md) — `ollama pull` 进度为 0、报 `redirect target not allowed ... non-public 198.18`；用走代理的临时实例拉取
- [Devin 代理下模型目录随代理出口地区缩水](devin-proxy-model-catalog-exit-region.md) — devin-2api 报 `absent from upstream catalog`、`permission_denied`，`/v1/models` 只剩 swe／kimi／glm 等；把上游域名命中的代理组切到可用地区并重启
