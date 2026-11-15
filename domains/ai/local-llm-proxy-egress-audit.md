---
status: verified
source: 本机源码审计 WncFht/devin2api（Go），2026-11-15
source_version: devin-2api v0.18.x（HEAD e8547b6）；Windows 11；Go 1.27.1
applies_to: 审计本地 LLM 代理/转发工具是否隐蔽上传数据；第三方 API 中转网关的可信度评估
excludes: 二进制逆向审计；发布包与源码一致性的逐字节验证；上游服务端自身行为
---

# 本地 LLM 代理出网面审计：方法与 devin-2api 实例

## 结论

- 审计「本地代理是否偷传数据」的核心是清点出网面：硬编码 URL → 客户端构造点 → 后台出网 → 生成代码死存根，四层全过才算清完。
- devin-2api 实测通过：出网仅去 `devin.base_url`（默认 `server.codeium.com`）与 GitHub 自更新端点（仅面板手动触发），无遥测、无隐藏第三方端点。
- 「校验和通过」只证明下载包与发布一致，不等于二进制与源码同构；要严格可信，用源码自编译产物替换运行实例。

## 出网面清点法

按序执行，任何一层漏掉都可能藏住出口：

1. **硬编码 URL 全量 grep**（`https?://`）：先剔除测试文件与协议字面量（`json-schema.org`、`w3.org` 命名空间、错误文案里的文档链接），剩下的逐个点开看是不是真实拨号目标。
2. **客户端构造点**：`http.Client`、`RoundTripper`、RPC 客户端工厂（如 `connect.NewXxxClient`）。关键问题不是「有没有 client」，而是**每个 client 的 baseURL 从哪来**——配置文件、常量、还是拼接。全部绑在配置项上即收敛；出现第二个常量地址才是疑点。
3. **后台出网**：ticker、goroutine、启动流程里的定时或一次性调用（warm ping、配额采样、「检查更新」）。确认触发条件是自动还是手动——devin-2api 的 GitHub 检查只在 `/admin/update*` 面板端点被点时才发生，启动路径无任何更新探测。
4. **生成代码死存根**：proto/OpenAPI 生成的客户端可能带遥测服务存根（devin-2api 生成物里有 `AnalyticsServiceClient`），grep 调用点为零即死代码，不必误判为上报通道。
5. **用户输入驱动的出网**：消息体里的远程 URL（文档/图片/视频地址）会不会被服务端抓取转发——这是经用户输入的 SSRF 出口。devin-2api 的做法是把 URL 降级为文本标记显式注明「未抓取」，出口直接不存在。
6. **凭据与日志面**：token 是否只发往授权目的地、落库是否哈希化、上游错误体回显是否先 redact、debug 日志是否明文落盘。

## devin-2api 审计结果（v0.18.x）

| 面 | 结果 |
| --- | --- |
| 业务出网 | 全部 RPC 绑 `devin.base_url`，可配 `devin.proxy`（HTTP/SOCKS5），无硬编码备用端点 |
| 自更新 | 仅 `github.com` 与 `*.githubusercontent.com`，重定向白名单、checksums.txt sha256 校验、256MiB 上限；仅面板手动触发 |
| 遥测/分析 | 无；生成的 `AnalyticsServiceClient` 从未实例化 |
| 上游 metadata | 带协议伪装字段（随机 device fingerprint、伪造 os/client 名冒充官方客户端）——方向是代理→上游过鉴权，不是外传用户信息 |
| 指纹抹除 | sanitize 模块把 Claude Code/OpenClaw 等第三方客户端痕迹抹掉再发上游；隐私加分，但本质是规避上游第三方检测，属 TOS 灰区，账号被风控是使用者自己的风险 |
| 认证边界 | `dashboard.password` 为空时 `/admin` 零认证开放；`/v1` 在令牌仓为空时不校验；「匿名通道」令牌放行无凭据流量——回环绑定下风险有限，改 `0.0.0.0` 前必须先设密码 |
| 日志 | `debug.enabled` 开启时请求体未脱敏落本地 SQLite；token 落库是 SHA-256 |

## 编译备忘

- `go.mod` 要求 Go 1.27.1，本机 Go 1.20.4 低于 toolchain 自动切换的引入版本（Go 1.21），不会自动拉工具链；用 `go install golang.org/dl/go1.27.1@latest` 再 `go1.27.1 download` 补齐。

## 来源与证据

- 本机审计 2026-11-15：`E:\github\devin2api` @ `e8547b6`；关键文件 `internal/selfupdate/selfupdate.go`、`internal/ccpanel/upstream.go`、`internal/adapter/devin/{devin,demote,sanitize}.go`、`internal/ccpanel/auth.go`。
- [devin2api 项目仓库](https://github.com/WncFht/devin2api)；接入与认证实操见 [Devin 账号模型接入 Claude Code](devin-account-model-proxy-claude-code.md)。
