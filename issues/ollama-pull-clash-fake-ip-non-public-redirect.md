---
scope: cross-project
status: verified
source: 本机实测（Ollama 0.40.15，Clash Verge fake-ip 模式），Ollama server.log 原始报错
source_version: 2026-11-15
applies_to: 本机开着 Clash（或其他 fake-ip 模式的代理／TUN）时执行 ollama pull 拉取模型
excludes: 代理工作在 redir-host 等非 fake-ip 模式时、Ollama 官方源以外的模型仓库、Linux／macOS 上的表现
triggers: ollama pull；进度一直为 0；redirect target not allowed；resolves to non-public 198.18；r2.cloudflarestorage.com；max retries exceeded；Clash fake-ip
---

# Clash fake-ip 下 ollama pull 卡住：拒绝重定向到「非公网地址」

## 结论

现象：`ollama pull` 能拿到 manifest，但模型文件进度始终为 0，最终报 `max retries exceeded`。`%LOCALAPPDATA%\Ollama\server.log` 反复出现：

```
daec91ffb5dd part 7 attempt 5 failed: Get "https://<id>.r2.cloudflarestorage.com/...":
redirect target not allowed: <id>.r2.cloudflarestorage.com resolves to non-public 198.18.7.155, retrying in 32s
```

根因：Ollama 的模型文件先从 `registry.ollama.ai` 重定向到 Cloudflare R2 下载。Clash 的 fake-ip 模式把 R2 域名解析成 `198.18.0.0/16` 保留网段的假地址，Ollama 判定重定向目标是非公网地址，于是拒绝跟随。

同一时刻用 `curl` 从命令行直接下载同一个文件是正常的（1 MB 约 3 秒），所以这不是网络不通，而是 Ollama 自身的重定向安全检查。

## 错误做法 → 后果

- 反复重试 `ollama pull`，或等它自己重试 → 每个分片都按同样原因失败，最终 `max retries exceeded`，白等数分钟。
- 看到 registry 能访问（`curl https://registry.ollama.ai/...` 返回 200）就判定「网络正常、只是慢」 → 漏掉真正的报错。要看 `server.log`，不要只看 pull 的进度输出。

## 修复

另起一个走 HTTP 代理的临时 Ollama 实例来拉取。它和主实例共用模型目录，拉完结束即可，不改主实例和系统配置：

```bash
# Clash Verge 的混合端口见 clash-verge.yaml 中的 mixed-port
OLLAMA_HOST=127.0.0.1:11435 HTTPS_PROXY=http://127.0.0.1:<mixed-port> NO_PROXY=127.0.0.1,localhost ollama serve
OLLAMA_HOST=127.0.0.1:11435 ollama pull bge-m3      # 或 curl .../api/pull
# 完成后结束 11435 上的进程；主实例 ollama list 即可看到新模型
```

实测：走代理后 1.16 GB 的 bge-m3 正常下载完成，主实例（11434）无需重启就能列出并调用该模型。

注意：在 Git Bash 里结束后台的 `ollama serve` 时，只停掉外层 shell 不会结束子进程，要按端口找到进程再结束。

## 适用边界

- 走代理能解决问题，推测是因为改由代理解析域名，Ollama 不再在本地拿到 fake-ip 地址。这一机制未查源码确认。
- 以下替代方案**未验证**：在 Clash 的 `fake-ip-filter` 中加入 `*.r2.cloudflarestorage.com`；给主实例设置 `HTTPS_PROXY` 后重启 Ollama。
- 其他会对重定向目标做私网地址校验的下载工具，在 fake-ip 模式下可能出现同类问题。
