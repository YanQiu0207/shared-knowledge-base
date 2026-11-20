---
status: verified
source: Windows 本机实测（同一账号切换代理出口前后拉取模型目录并发起真实请求）；devin-2api 自带上游协议文档；Devin 官方模型文档
source_version: devin-2api v0.18.0；Claude Code 2.1.329；2026-11-21
applies_to: Claude Code 经 devin-2api 反代 Devin 订阅时，Claude／GPT／Gemini 系模型整批从目录消失并被拒绝
excludes: 仅单个模型不可用；套餐、试用期或组织白名单导致的收窄；香港、美国以外出口地区的表现；断言上游过滤的具体判定规则
triggers: devin-2api；absent from upstream catalog；already denied upstream；permission_denied；refusing locally until；fallbackModel 连续降级；/v1/models 只剩 swe、kimi、glm、deepseek、nemotron；Clash 兜底组；代理出口地区
---

# Devin 代理下模型目录随代理出口地区缩水

## 结论

现象：Claude Code 启动或切换模型时报 404，并沿 `fallbackModel` 逐级降级：

```
not_found: model "<claude 模型名>" is absent from the upstream catalog and was
already denied upstream (permission_denied); refusing locally until <时间>
```

此时代理的 `GET /v1/models` 只返回 46 个模型，全部是 `swe-*`、`kimi-*`、`glm-*`、`deepseek-*`、`nemotron-*`，Claude、GPT、Gemini 三系一个不剩。

根因：上游下发的账号模型目录与代理出口地区相关。实测出口为香港时目录是上述 46 个；把出口切到美国并重启代理后，同一账号的目录恢复为 303 个，`claude-fable-5-2-high` 的真实请求成功。本地配置、订阅套餐和代理版本均未改动。

报错中的 `refusing locally until` 只是代理对上游拒绝结果的本地缓存，到期后上游照样拒绝。

## 错误做法 → 后果

- 等本地拒绝缓存到期后重试 → 出口不变，上游继续返回 `permission_denied`。
- 把 `ANTHROPIC_DEFAULT_*_MODEL` 改指向剩余模型，或在代理里加别名把 Claude 模型名映射到 `swe-*` → 报错消失，但实际运行的不是所选模型，还掩盖了目录可以恢复这一事实。
- 看到整批消失就判定「平台下架」或「套餐降级」 → 先查官方模型文档；本次文档仍把这些模型列为正式可用，问题只在本账号拿到的目录。

## 排查与修复

1. 确认出口地区：`curl https://ipinfo.io/json`。开着 TUN 模式时，直连流量同样经代理出口，系统代理开关显示关闭不代表没走代理。
2. 确认目录规模：`curl http://127.0.0.1:<端口>/v1/models`，统计总数和 `claude`、`gpt`、`gemini` 的命中数。
3. 找到上游域名（`server.codeium.com`）命中的代理组。本次该域名没有专属规则，走的是 `MATCH` 兜底组，「海外 AI」之类的分组并不覆盖它。
4. 把该代理组切到目标地区的节点，重启 devin-2api，重新拉取目录。
5. 用最小请求做端到端验证，只看目录不算数：

```bash
curl -s -X POST http://127.0.0.1:<端口>/v1/messages \
    -H "Content-Type: application/json" -H "x-api-key: local" \
    -H "anthropic-version: 2023-06-01" \
    -d '{"model":"<模型名>","max_tokens":16,"messages":[{"role":"user","content":"reply with the single word: ok"}]}'
```

TUN 模式已接管直连流量，不需要再给 devin-2api 配置 `devin.proxy`。

与版本门的区分：devin-2api 的上游协议文档记录，版本门表现为 `failed_precondition` 加「please update your editor」文案；`permission_denied` 对应无权访问的模型，不必先去调 `client_version`。

## 适用边界

- 只对比了香港和美国两个出口。上游按什么判定（IP 归属地、是否另有账号侧条件）未确认；「与闭源模型厂商的地区限制相符」是推断，没有上游文档佐证。
- 切换出口与重启代理是同时做的，没有做「不换出口只重启」和「切回原出口」的对照。上游在原出口下对请求返回过 `permission_denied`，重启改变不了上游的判定，因此出口地区是最合理的解释，但严格的单变量验证尚缺。
- 切换兜底组会让所有未匹配规则的流量都走新节点。更精细的做法是为上游域名加专属规则，此方案**未验证**。
- 代理节点切换后是否必须重启 devin-2api 才刷新目录，未单独验证。
- 出口节点失效或被自动切换回原地区后，问题会复现；再次出现同样报错时先查出口。

## 来源

- [Devin 模型文档](https://docs.devin.ai/desktop/models)：2026-11-09 版本仍列出 Claude、GPT、Gemini 系模型，并说明账号实际可用模型以 List Models API 为准。
- [devin-2api 上游协议文档](https://github.com/WncFht/devin2api/blob/main/docs/upstream-protocol.md)：错误码分类，`permission_denied` 与版本门的区别。
- 本机同一账号、同一代理版本在两个出口下的目录对比与真实请求验证。
