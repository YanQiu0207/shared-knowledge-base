---
scope: cross-project
status: provisional
source: user-approved-agentic-engineering-framework-knowledge-management-change
source_version: 2026-07-19
applies_to: coding agents using project or cross-project knowledge alongside source code
excludes: systems where the knowledge artifact is itself an explicitly approved executable contract
---

# 知识与代码冲突处理

## 结论

项目知识和跨项目公共知识只用于辅助理解。它们与代码、Schema、配置、测试或运行证据冲突时，Agent 必须显式展示双方证据和不确定性，不能静默采用或覆盖任意一方。

## 操作

冲突报告至少包含：

- 知识文件与知识结论。
- 代码、Schema、配置、测试或运行证据。
- 知识记录的来源版本与当前版本。
- 尚不能确定的冲突原因。
- 下一步选择：更新知识、修正代码、更新当前变更契约或继续调查。

活跃 Change 是当前任务契约，不属于普通辅助知识。交付前必须验证实现是否满足 Change；不满足时不能宣布完成。

## 适用边界

- 本条目不判断冲突双方谁必然正确。
- 自动生成知识通常更可能过期，但仍应先比较来源路径和版本。
- 人工业务知识与代码冲突时，可能是代码缺陷、知识过期、目标尚未实现或适用范围不完整，必须保留不确定性。
- 公共知识只提供通用参考，不能仅凭「最佳实践」覆盖项目特殊约束。

## 证据等级

当前状态为 `provisional`：该机制已在 Agentic Engineering Framework 的真实知识管理改造和 Archive 冲突门禁中验证，但尚未积累多个独立项目案例。
