#!/usr/bin/env python3
"""Check local documentation paths, stable question IDs and generated index."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
import unicodedata
from urllib.parse import unquote, urlsplit

from study import ROOT, questions

EXPECTED_QUESTIONS = 92
ADVANCED_CHAPTERS = (
    "01-harness-and-deep-agents",
    "02-durable-execution",
    "03-context-engineering",
    "04-memory-and-skills",
    "05-tool-routing-and-mcp",
    "06-agentic-rag",
    "07-multi-agent-systems",
    "08-coding-and-computer-use",
    "09-evaluation-and-feedback",
    "10-performance-and-serving",
    "11-security-and-governance",
    "12-agent-training",
)


def slug(text: str) -> str:
    text = re.sub(r"\[([^]]+)\]\([^)]*\)", r"\1", text)
    text = text.replace("`", "").strip().lower()
    text = "".join(c for c in text if c in "_- " or unicodedata.category(c)[0] in "LN")
    return text.replace(" ", "-")


def anchors(content: str) -> set[str]:
    result: set[str] = set()
    counts: dict[str, int] = {}
    in_code = False
    for line in content.splitlines():
        if line.startswith("```"):
            in_code = not in_code
        if in_code:
            continue
        match = re.match(r"^#{1,6} (.+)$", line)
        if match:
            base = slug(match[1])
            count = counts.get(base, 0)
            result.add(base if count == 0 else f"{base}-{count}")
            counts[base] = count + 1
    return result


def question_index() -> str:
    bank = questions()
    lines = [f"# {len(bank)} 题索引", "", "先找到问题，再回到机制。短答用于口述，详细答案用于理解，追问与案例用于检查能否迁移。", "",
             "[基础课程](../learning/README.md) · [进阶课程](../advanced/README.md) · [36 道进阶题与章节对照](advanced/README.md)", ""]
    for folder, title in (("foundations", "基础原理：Q001–Q032"),
                          ("engineering", "工程与项目：Q033–Q056"),
                          ("advanced", "进阶系统：Q057–Q092")):
        lines.extend([f"## {title}", "", "| 题号 | 问题 | 学习入口 |", "| --- | --- | --- |"])
        for q in (item for item in bank if item.path.parent.name == folder):
            path = q.path.relative_to("docs").as_posix()
            if folder == "advanced":
                course = f"[{q.path.stem[:2]} 章](../advanced/{q.path.name})"
            else:
                course = "[基础课程](../learning/README.md)" if folder == "foundations" else "[工程学习路线](00-roadmap.md)"
            lines.append(f"| {q.id} | [{q.title}]({path}#{slug(q.id + ' ' + q.title)}) | {course} |")
        lines.append("")
    lines.extend(["", "[学习路线](00-roadmap.md) · [复习工具](../practice/README.md) · [仓库首页](../README.md)", ""])
    return "\n".join(lines)


def check() -> list[str]:
    failures = []
    bank = questions()
    expected = [f"Q{i:03}" for i in range(1, EXPECTED_QUESTIONS + 1)]
    if [q.id for q in bank] != expected:
        failures.append(f"题号应为 Q001–Q{EXPECTED_QUESTIONS:03} 且连续唯一。")
    for q in bank:
        for label in ("优先级", "回答", "误区", "微练习"):
            if label not in q.body:
                failures.append(f"{q.id} 缺少 {label}")
        if "追问" not in q.body:
            failures.append(f"{q.id} 缺少追问")
        if q.path.parent.name == "advanced":
            for label in ("详细答案", "常见追问", "实战案例"):
                if label not in q.body:
                    failures.append(f"{q.id} 缺少 {label}")
    # Each advanced lesson owns three stable questions and links back to its question chapter.
    for number, stem in enumerate(ADVANCED_CHAPTERS):
        lesson = ROOT / "advanced" / f"{stem}.md"
        interview = ROOT / "docs/advanced" / f"{stem}.md"
        expected_ids = [f"Q{i:03}" for i in range(57 + number * 3, 60 + number * 3)]
        actual_ids = [q.id for q in bank if q.path == interview.relative_to(ROOT)]
        if actual_ids != expected_ids:
            failures.append(f"{interview.relative_to(ROOT)} 应包含 {'、'.join(expected_ids)}")
        if lesson.exists() and f"../docs/advanced/{stem}.md" not in lesson.read_text(encoding="utf-8"):
            failures.append(f"{lesson.relative_to(ROOT)} 缺少对应面试章回链")
        if interview.exists() and f"../../advanced/{stem}.md" not in interview.read_text(encoding="utf-8"):
            failures.append(f"{interview.relative_to(ROOT)} 缺少对应学习章回链")
    index = ROOT / "docs/question-index.md"
    if not index.exists() or index.read_text(encoding="utf-8") != question_index():
        failures.append("题目索引需更新：python3 scripts/check_repo.py --write-index")
    markdown = sorted(p for p in ROOT.rglob("*.md") if not any(x in p.parts for x in (".git", ".local", ".venv")))
    for path in markdown:
        content = path.read_text(encoding="utf-8")
        # Remove fenced examples so instructional placeholder paths are not links.
        visible = re.sub(r"```.*?```", "", content, flags=re.S)
        for match in re.finditer(r"!?\[[^\]]*\]\(([^)\s]+)\)", visible):
            target = match[1].strip("<>")
            parsed = urlsplit(target)
            if parsed.scheme or parsed.netloc:
                continue
            dest = (path.parent / unquote(parsed.path)).resolve() if parsed.path else path
            try:
                dest.relative_to(ROOT)
            except ValueError:
                failures.append(f"{path.relative_to(ROOT)} 链接逃出仓库：{target}")
                continue
            if not dest.exists():
                failures.append(f"{path.relative_to(ROOT)} 目标不存在：{target}")
            elif parsed.fragment and dest.is_file() and dest.suffix == ".md":
                if unquote(parsed.fragment) not in anchors(dest.read_text(encoding="utf-8")):
                    failures.append(f"{path.relative_to(ROOT)} 锚点不存在：{target}")
    for path in ROOT.rglob("*.json"):
        if ".local" not in path.parts and ".git" not in path.parts:
            try:
                json.loads(path.read_text(encoding="utf-8"))
            except (ValueError, OSError) as error:
                failures.append(f"{path.relative_to(ROOT)} JSON 无效：{error}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-index", action="store_true")
    args = parser.parse_args()
    if args.write_index:
        (ROOT / "docs/question-index.md").write_text(question_index(), encoding="utf-8")
    failures = check()
    for item in failures:
        print(f"ERROR: {item}", file=sys.stderr)
    if not failures:
        print(f"PASS: {len(questions())} 题、字段、索引、本地文档链接与 JSON。外部 URL 可达性不在本检查范围。")
    return bool(failures)


if __name__ == "__main__":
    raise SystemExit(main())
