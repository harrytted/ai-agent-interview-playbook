#!/usr/bin/env python3
"""Check local documentation paths, stable question IDs and generated index."""
from __future__ import annotations

import argparse
import json
from os.path import relpath
from pathlib import Path
import re
import sys
import unicodedata
from urllib.parse import unquote, urlsplit

from study import ROOT, questions
from question_articles import article_path, check_articles, write_articles

EXPECTED_QUESTIONS = 92
EXCLUDED_DIRS = frozenset({".git", ".local", ".venv", ".venv-docs", ".site-src", "site", "node_modules"})
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
BASE_LESSONS = {
    "Q001": "learning/01-system-map.md",
    **{f"Q{i:03}": "learning/02-llm-primer.md" for i in range(2, 8)},
    "Q008": "learning/09-evaluation.md",
    "Q009": "learning/04-agent-loop.md",
    "Q010": "learning/08-planning-and-multi-agent.md",
    "Q011": "learning/07-memory-and-state.md",
    "Q012": "learning/04-agent-loop.md",
    "Q013": "learning/08-planning-and-multi-agent.md",
    "Q014": "learning/10-reliability-and-security.md",
    "Q015": "learning/08-planning-and-multi-agent.md",
    "Q016": "learning/08-planning-and-multi-agent.md",
    **{f"Q{i:03}": "learning/06-rag-and-retrieval.md" for i in range(17, 25)},
    **{f"Q{i:03}": "learning/05-tools-and-mcp.md" for i in range(25, 30)},
    "Q030": "learning/07-memory-and-state.md",
    "Q031": "learning/03-context-and-prompts.md",
    "Q032": "learning/07-memory-and-state.md",
    **{f"Q{i:03}": "learning/09-evaluation.md" for i in range(33, 41)},
    **{f"Q{i:03}": "learning/10-reliability-and-security.md" for i in range(41, 49)},
    "Q049": "learning/01-system-map.md",
    "Q050": "learning/06-rag-and-retrieval.md",
    "Q051": "learning/04-agent-loop.md",
    "Q052": "learning/01-system-map.md",
    "Q053": "docs/engineering/08-project-lab.md",
    "Q054": "learning/09-evaluation.md",
    "Q055": "docs/engineering/08-project-lab.md",
    "Q056": "learning/09-evaluation.md",
}
LINKS_START = "<!-- question-links:start -->"
LINKS_END = "<!-- question-links:end -->"


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


def local_url(source: Path, target: Path) -> str:
    return Path(relpath(target, source.parent)).as_posix()


def lesson_sections() -> dict[Path, str]:
    """Build lesson navigation from primary mappings and explicit related-lesson links."""
    grouped = {}
    for q in questions():
        if q.id not in BASE_LESSONS:
            continue
        targets = {ROOT / BASE_LESSONS[q.id]}
        for match in re.finditer(r"\[[^\]]*\]\(([^)\s]+)\)", q.body):
            parsed = urlsplit(match[1])
            if parsed.scheme or parsed.netloc:
                continue
            target = (ROOT / q.path.parent / unquote(parsed.path)).resolve()
            if (target.parent == ROOT / "learning" and re.match(r"\d{2}-", target.name)) or target == ROOT / "docs/engineering/08-project-lab.md":
                targets.add(target)
        for target in targets:
            grouped.setdefault(target, []).append(q)
    result = {}
    for lesson, bank in grouped.items():
        lines = [LINKS_START, "## 配套面试练习", "", "先合上正文讲一分钟，再用追问和案例检查理解。每题都可以跳回对应学习内容。", "",
                 "<details><summary>展开本章相关面试题</summary>", ""]
        for q in bank:
            target = local_url(lesson, ROOT / article_path(q.id))
            lines.append(f"- [{q.id} {q.title}]({target}#{slug(q.id + ' ' + q.title)})")
        lines.extend(["", "</details>", LINKS_END])
        result[lesson] = "\n".join(lines)
    return result


def write_navigation() -> None:
    write_articles(questions(), ROOT)
    (ROOT / "docs/question-index.md").write_text(question_index(), encoding="utf-8")
    for path, section in lesson_sections().items():
        content = path.read_text(encoding="utf-8")
        pattern = re.escape(LINKS_START) + r".*?" + re.escape(LINKS_END)
        if LINKS_START in content:
            content = re.sub(pattern, lambda _: section, content, flags=re.S)
        else:
            content = content.rstrip() + "\n\n" + section + "\n"
        path.write_text(content, encoding="utf-8")


def question_index() -> str:
    bank = questions()
    lines = [f"# {len(bank)} 题索引", "", "先找到问题，再回到机制。短答用于口述，详细答案用于理解，追问与案例用于检查能否迁移。", "",
             "[基础原理](../learning/README.md) · [工程进阶](../advanced/README.md) · [36 道进阶题与章节对照](advanced/README.md)", ""]
    for folder, title in (("foundations", "基础原理：Q001–Q032"),
                          ("engineering", "工程与项目：Q033–Q056"),
                          ("advanced", "进阶系统：Q057–Q092")):
        lines.extend([f"## {title}", "", "| 题号 | 问题 | 学习入口 |", "| --- | --- | --- |"])
        for q in (item for item in bank if item.path.parent.name == folder):
            path = local_url(ROOT / "docs/question-index.md", ROOT / article_path(q.id))
            if folder == "advanced":
                course = f"[{q.path.stem[:2]} 章](../advanced/{q.path.name})"
            else:
                lesson = ROOT / BASE_LESSONS[q.id]
                label = "项目实验" if lesson.name == "08-project-lab.md" else f"基础 {lesson.name[:2]} 章"
                course = f"[{label}]({local_url(ROOT / 'docs/question-index.md', lesson)})"
            lines.append(f"| {q.id} | [{q.title}]({path}#{slug(q.id + ' ' + q.title)}) | {course} |")
        lines.append("")
    lines.extend(["", "[学习路线](00-roadmap.md) · [复习工具](../practice/README.md) · [仓库首页](../README.md)", ""])
    return "\n".join(lines)


def check() -> list[str]:
    failures = []
    bank = questions()
    failures.extend(check_articles(bank, ROOT))
    expected = [f"Q{i:03}" for i in range(1, EXPECTED_QUESTIONS + 1)]
    if [q.id for q in bank] != expected:
        failures.append(f"题号应为 Q001–Q{EXPECTED_QUESTIONS:03} 且连续唯一。")
    for q in bank:
        for label in ("优先级", "回答", "误区", "微练习"):
            if label not in q.body:
                failures.append(f"{q.id} 缺少 {label}")
        if "追问" not in q.body:
            failures.append(f"{q.id} 缺少追问")
        for label in ("详细答案", "常见追问", "实战案例"):
            if label not in q.body:
                failures.append(f"{q.id} 缺少 {label}")
        if q.id in BASE_LESSONS:
            target = local_url(ROOT / q.path, ROOT / BASE_LESSONS[q.id])
            if target not in q.body:
                failures.append(f"{q.id} 缺少主要学习章链接：{target}")
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
    for path, section in lesson_sections().items():
        if not path.exists() or section not in path.read_text(encoding="utf-8"):
            failures.append(f"{path.relative_to(ROOT)} 面试题导航需更新：python3 scripts/check_repo.py --write-index")
    markdown = sorted(p for p in ROOT.rglob("*.md") if not EXCLUDED_DIRS.intersection(p.relative_to(ROOT).parts))
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
        if not EXCLUDED_DIRS.intersection(path.relative_to(ROOT).parts):
            try:
                json.loads(path.read_text(encoding="utf-8"))
            except (ValueError, OSError) as error:
                failures.append(f"{path.relative_to(ROOT)} JSON 无效：{error}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-index", action="store_true", help="更新独立文章、题目总索引与学习章题目导航")
    args = parser.parse_args()
    if args.write_index:
        write_navigation()
    failures = check()
    for item in failures:
        print(f"ERROR: {item}", file=sys.stderr)
    if not failures:
        print(f"PASS: {len(questions())} 题、字段、索引、本地文档链接与 JSON。外部 URL 可达性不在本检查范围。")
    return bool(failures)


if __name__ == "__main__":
    raise SystemExit(main())
