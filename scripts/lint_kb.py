"""跨项目共用知识库结构 lint。

对照根 index.md 的「查询规则」「写入规则」做机器检查：

1. 每个 domains/<topic>/ 有 index.md 且含「结论」章节。
2. 根索引分类表与顶层目录一一对应；索引表链接目标存在。
3. 行数预算：根索引 <= 60 行；主题索引 <= 100 行；条目 <= 400 行。
4. 条目（domains/、issues/ 下非 index 文件）frontmatter 必填
   status / source / source_version / applies_to / excludes，且禁止项目作用域。

用法：python scripts/lint_kb.py [--root <知识库根目录>]
退出码：0 全过；1 有违规；2 目录结构不可用。
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

MAX_ROOT_INDEX_LINES = 60
MAX_TOPIC_INDEX_LINES = 100
MAX_ENTRY_LINES = 400
REQUIRED_FRONTMATTER_KEYS = (
    "status",
    "source",
    "source_version",
    "applies_to",
    "excludes",
)
# 非知识内容的顶层目录：不要求出现在根索引分类表；点前缀目录一并忽略。
IGNORED_TOP_DIRS = {"projects", "scripts"}
# 条目检查（行数预算 + frontmatter）只覆盖知识条目所在目录。
ENTRY_DIRS = ("domains", "issues")
LINK_PATTERN = re.compile(r"\[[^\]]*\]\(([^)]+)\)")


def _read_lines(path: Path) -> list[str]:
    # utf-8-sig：兼容 Windows 工具写出的带 BOM 文件，避免 frontmatter 误报。
    return path.read_text(encoding="utf-8-sig").splitlines()


def _link_targets(line: str) -> list[str]:
    """提取行内站内链接目标，剥离锚点；跳过外链和纯锚点链接。"""
    targets = []
    for raw in LINK_PATTERN.findall(line):
        if raw.startswith(("http://", "https://")):
            continue
        target = raw.split("#", 1)[0]
        if target:
            targets.append(target)
    return targets


def _check_root_index(root: Path, problems: list[str]) -> None:
    """根索引：行数预算、分类表与顶层目录一一对应、链接目标存在。"""
    index = root / "index.md"
    if not index.is_file():
        problems.append("index.md：根索引不存在")
        return
    lines = _read_lines(index)
    if len(lines) > MAX_ROOT_INDEX_LINES:
        problems.append(
            f"index.md：{len(lines)} 行，超出根索引预算 {MAX_ROOT_INDEX_LINES} 行"
        )

    linked_dirs = set()
    for line in lines:
        for target in _link_targets(line):
            if not (root / target).exists():
                problems.append(f"index.md：链接目标不存在 -> {target}")
            linked_dirs.add(target.strip("/").split("/")[0])

    for child in sorted(p for p in root.iterdir() if p.is_dir()):
        if child.name.startswith(".") or child.name in IGNORED_TOP_DIRS:
            continue
        if child.name not in linked_dirs:
            problems.append(f"index.md：分类表缺少顶层目录 {child.name}/ 的入口")


def _check_topic_indexes(root: Path, problems: list[str]) -> None:
    """domains/ 每个主题必须有含「结论」章节的 index.md；主题索引限行数。"""
    domains = root / "domains"
    if not domains.is_dir():
        return
    for topic in sorted(p for p in domains.iterdir() if p.is_dir()):
        index = topic / "index.md"
        rel = index.relative_to(root).as_posix()
        if not index.is_file():
            problems.append(f"{rel}：主题缺少 index.md")
            continue
        if not any(line.strip() == "## 结论" for line in _read_lines(index)):
            problems.append(f"{rel}：缺少「结论」章节")

    for index in sorted(domains.rglob("index.md")):
        rel = index.relative_to(root).as_posix()
        lines = _read_lines(index)
        if len(lines) > MAX_TOPIC_INDEX_LINES:
            problems.append(
                f"{rel}：{len(lines)} 行，超出主题索引预算"
                f" {MAX_TOPIC_INDEX_LINES} 行"
            )
        for i, line in enumerate(lines, start=1):
            for target in _link_targets(line):
                if not (index.parent / target).exists():
                    problems.append(f"{rel}:{i}：链接目标不存在 -> {target}")


def _check_entries(root: Path, problems: list[str]) -> None:
    """条目：行数预算 + frontmatter 必填字段。"""
    for area in ENTRY_DIRS:
        base = root / area
        if not base.is_dir():
            continue
        for entry in sorted(base.rglob("*.md")):
            if entry.name == "index.md":
                continue
            rel = entry.relative_to(root).as_posix()
            lines = _read_lines(entry)
            if len(lines) > MAX_ENTRY_LINES:
                problems.append(
                    f"{rel}：{len(lines)} 行，超出条目预算 {MAX_ENTRY_LINES} 行，"
                    "应拆分为多条目并更新主题索引"
                )
            _check_frontmatter(rel, lines, problems)


def _check_frontmatter(rel: str, lines: list[str], problems: list[str]) -> None:
    if not lines or lines[0].strip() != "---":
        problems.append(f"{rel}：缺少 frontmatter")
        return
    body: list[str] = []
    for line in lines[1:]:
        if line.strip() == "---":
            break
        body.append(line)
    else:
        problems.append(f"{rel}：frontmatter 未闭合")
        return
    keys = {
        line.split(":", 1)[0].strip() for line in body if ":" in line
    }
    missing = [key for key in REQUIRED_FRONTMATTER_KEYS if key not in keys]
    if missing:
        problems.append(f"{rel}：frontmatter 缺少字段 {', '.join(missing)}")
    fields = {
        line.split(":", 1)[0].strip(): line.split(":", 1)[1].strip()
        for line in body
        if ":" in line
    }
    if fields.get("scope", "").lower() == "project":
        problems.append(f"{rel}：公共条目禁止 scope: project")


def main(argv: list[str]) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # Windows 控制台默认非 UTF-8

    parser = argparse.ArgumentParser(description="校验共用知识库的结构与预算")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="知识库根目录，默认取脚本所在仓库根。",
    )
    args = parser.parse_args(argv)
    root: Path = args.root.resolve()
    if not (root / "domains").is_dir():
        print(f"error: {root} 下没有 domains/ 目录", file=sys.stderr)
        return 2

    problems: list[str] = []
    _check_root_index(root, problems)
    _check_topic_indexes(root, problems)
    _check_entries(root, problems)

    for problem in problems:
        print(f"violation: {problem}")
    print(f"checked root={root} | violations={len(problems)}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
