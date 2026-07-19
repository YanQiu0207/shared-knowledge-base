---
source: agentic-engineering-framework feat/cross-agent-shared-memory（lint_kb.py code review 修复轮）
status: pending
---

# Windows 下 Markdown lint 的两个高频误报源

## 结论

1. **UTF-8 BOM**：记事本等 Windows 工具写出的 Markdown 文件首行是 `﻿---`，用 `utf-8` 读取会把 frontmatter 误判为缺失；统一用 `encoding="utf-8-sig"` 读取（无 BOM 时与 `utf-8` 行为等价，无副作用）。
2. **站内锚点链接**：`[x](file.md#节名)` 直接对整串做存在性检查恒为 False；判存在性前先 `target.split("#", 1)[0]` 剥离锚点，剥离后为空的纯锚点链接（`#节名`）跳过。

## 证据

- 2026-07-19 lint_kb.py 首版 code review 中被指出这两处误报（comprehensive-reviewer F2 / F3）；修复实现见本仓库 commit `bd359aa` 的 `scripts/lint_kb.py`（`_read_lines` 与 `_link_targets`）。
