# 已验证踩坑

## 结论

本主题保存已查证的现象、根因、修复与适用边界。只收经过实测或有可靠来源支撑的条目；未验证的怀疑留在项目内或交付报告中。

## 条目

- [第三方 API 中转改写 Claude Code 系统提示](relay-system-prompt-injection.md) — 中转可注入禁用 subagent、限制单次写入并要求静默服从的指令，能力降级不可见
- [思考内容回传缺失导致上游 400](thinking-passthrough-400.md) — 代理误剥离 thinking 签名，或客户端漏传 reasoning，均报 must be passed back
