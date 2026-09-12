---
scope: cross-project
status: verified
source: 本地实测（TencentDB Agent Memory proxy v0468a2a + DeepSeek /anthropic 端点），源码定位 MemoryProxy/src/anthropicHandler.ts:272
source_version: 2026-09-12
applies_to: 任何在客户端与第三方 Anthropic 兼容端点之间插入代理层、且该代理会校验或改写 thinking 块的工作流
excludes: Anthropic 官方端点的签名行为、非 Anthropic 协议的模型调用（如 OpenAI Responses）、代理层其它功能（记忆注入、鉴权）
---

# 思考内容回传缺失导致上游 400（Anthropic thinking / OpenAI reasoning）

## 结论

在 Claude Code 与 DeepSeek 的 Anthropic 兼容端点之间插入 TencentDB Agent Memory 的 proxy 后，请求会间歇性 400：

```
The `content[].thinking` in the thinking mode must be passed back to the API.
```

根因是 **proxy 按 Anthropic 官方签名格式做的启发式校验，误判了 DeepSeek 签发的签名**：DeepSeek 的签名是 UUID（36 字符），而 proxy 的规则既要求签名长度 ≥ 40，又把 UUID 格式显式判为无效，于是每个 thinking 块都被剥离。带 `tool_use` 的助手轮一旦失去 thinking 块，上游即拒绝整条请求。

直连 DeepSeek 不会触发，因为该校验只存在于代理层。

## 判定规则与冲突点

`MemoryProxy/src/anthropicHandler.ts:272` 的 `hasValidThinkingSignature`：

```js
if (typeof sig !== "string" || sig.length < 40) return false;              // 长度下限 40
if (/^[0-9a-f]{8}-[0-9a-f]{4}-...-[0-9a-f]{12}$/i.test(sig)) return false; // UUID 判为无效
return /^[A-Za-z0-9+/=]+$/.test(sig);                                      // 必须 base64
```

DeepSeek 的 Anthropic 端点返回的签名形如 `8d132a5d-c8aa-4e9f-885d-be94e828181d`，两条规则都不满足，因此被判无效并进入剥离分支（日志：`stripped N invalid thinking block(s) from history`）。

## 实测对照

| 请求 | 结果 |
| --- | --- |
| 直连 DeepSeek，UUID 签名原样带上 | 200 |
| 经 proxy，UUID 签名 | 400（日志先 `stripped 1` 再 `status=400`）|
| 经 proxy，替换为 60 字符 base64 签名 | 200 |

第三行是关键：**DeepSeek 不校验签名的真伪，只要求 thinking 块存在**。这决定了修复方向是「不要剥离」，而非「修复签名」。

按 30 分钟窗口统计，失败率约 27%（8 个 400 / 22 个 200），表现为间歇性报错后由客户端自动重试。

## 修复

放行 UUID 形式签名（本地位于 `MemoryProxy/src/anthropicHandler.ts`）：

```js
function hasValidThinkingSignature(block: Record<string, unknown>): boolean {
  const sig = block.signature;
  if (typeof sig !== "string" || sig.length === 0) return false;
  if (/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(sig)) {
    return true;   // 部分兼容端点（如 DeepSeek）签发 UUID 签名，须放行
  }
  if (sig.length < 40) return false;
  return /^[A-Za-z0-9+/=]+$/.test(sig);
}
```

proxy 镜像以 tsx 直接执行 TypeScript，改源码后重建镜像即生效：

```bash
cd MemoryProxy && DOCKER_BUILDKIT=1 docker build -t tdai-memory-proxy:patched .
```

## 同类问题的 Codex 变体

Codex 走 OpenAI Responses 协议，思考内容在 `reasoning_text`，不经过上面的签名校验，但有一条**同源**的报错路径：

```
The `reasoning_text` in the thinking mode must be passed back to the API.
```

成因与 Anthropic 侧不同——是 **Codex 配置项作用域写错**：`disable_response_storage = true` 必须写在 `~/.codex/config.toml` 的**顶层**，写进 `[model_providers.<name>]` 段内不生效。该开关不生效时，Codex 认为上游已存储上下文而省略 reasoning 内容，DeepSeek 随即拒绝请求。

对照官方文档 `agents/codex/README.md`，顶层写法为：

```toml
model_provider = "team-proxy"
model = "<上游模型名>"
disable_response_storage = true      # ← 顶层

[model_providers.team-proxy]
wire_api = "responses"
base_url = "http://127.0.0.1:8096/codex/default"
experimental_bearer_token = "<user_key>"
```

用 `codex -c` 临时覆盖时同理：`-c 'disable_response_storage=true'` 是顶层键，不能写成 `-c 'model_providers.x.disable_response_storage=true'`。

## 适用边界与排查顺序

- **两个协议族各有一条「思考内容必须回传」的报错**：Anthropic 侧是 `content[].thinking`（代理剥离导致），OpenAI 侧是 `reasoning_text`（客户端省略导致）。看到其中任一条，先确认自己处在哪条路径上。
- **通用信号**：凡代理层出现「上游报缺少 thinking / 签名无效」而客户端直连正常，应优先怀疑代理的签名启发式，而不是模型或客户端。
- **排查顺序**：先看代理日志有无 `stripped ... thinking block(s)`，再用「直连 vs 经代理」构造同一请求对照，必要时替换签名格式做二分。
