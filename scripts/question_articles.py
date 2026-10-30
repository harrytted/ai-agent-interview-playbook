"""Build one readable article per stable question from the canonical question bank.

The grouped docs remain the only editable answer source and retain their anchors.
Generated articles expose the main answer directly while preserving inner quizzes.
"""
from __future__ import annotations

from collections import OrderedDict
from os.path import relpath
from pathlib import Path, PurePosixPath
import posixpath
import re
import unicodedata
from urllib.parse import quote, unquote, urlsplit, urlunsplit

FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
INLINE_LINK = re.compile(
    r"(?P<open>!?\[[^\]\n]*\]\()"
    r"(?P<url><[^>\n]+>|[^ \t\r\n)]+)"
    r"(?P<title>[ \t]+(?:\"[^\"\n]*\"|'[^'\n]*'|\([^\n)]*\)))?\)"
)
DETAILS_TAG = re.compile(r"</?details\b[^>]*>", re.I)
MAIN_FOLD = re.compile(r"<details\b[^>]*>\s*<summary>[^<]*详细答案[^<]*</summary>", re.I)
GENERATED = "<!-- Generated question article; edit the canonical question in {source}, then run python3 scripts/check_repo.py --write-index. -->"


def article_path(question_id: str) -> Path:
    if not re.fullmatch(r"Q\d{3}", question_id):
        raise ValueError("question ID must use Q followed by three digits")
    return Path("questions") / (question_id + ".md")


def _slug(text: str) -> str:
    text = re.sub(r"\[([^]]+)\]\([^)]*\)", r"\1", text)
    text = text.replace("`", "").strip().lower()
    return "".join(c for c in text if c in "_- " or unicodedata.category(c)[0] in "LN").replace(" ", "-")


def _visible_mask(content: str) -> str:
    """Mask fenced examples without moving offsets used for HTML wrapper removal."""
    result = []
    character, length = "", 0
    for line in content.splitlines(keepends=True):
        match = FENCE.match(line)
        if character:
            result.append("".join("\n" if c == "\n" else " " for c in line))
            if match and match[1][0] == character and len(match[1]) >= length and not match[2].strip():
                character, length = "", 0
        elif match:
            character, length = match[1][0], len(match[1])
            result.append("".join("\n" if c == "\n" else " " for c in line))
        else:
            result.append(line)
    return "".join(result)


def _open_main_answer(content: str) -> str:
    """Remove only the main detailed-answer fold, never nested self-checks/code."""
    mask = _visible_mask(content)
    opening = MAIN_FOLD.search(mask)
    if opening is None:
        return content
    depth = 1
    for token in DETAILS_TAG.finditer(mask, opening.end()):
        depth += -1 if token.group().startswith("</") else 1
        if depth == 0:
            return content[:opening.start()] + content[opening.end():token.start()] + content[token.end():]
    raise ValueError("main question answer has an unclosed details wrapper")


def _relative_url(value: str, question, by_id: dict) -> str:
    parsed = urlsplit(value)
    if parsed.scheme or parsed.netloc or parsed.path.startswith("/"):
        return value
    target_question = re.match(r"q(\d{3})(?:-|$)", unquote(parsed.fragment), re.I)
    target_id = "Q" + target_question[1] if target_question else None
    if not parsed.path:
        if target_id and target_id != question.id and target_id in by_id and by_id[target_id].path == question.path:
            return urlunsplit(("", "", target_id + ".md", parsed.query, parsed.fragment))
        return value
    target = posixpath.normpath(posixpath.join(question.path.parent.as_posix(), unquote(parsed.path)))
    if target == ".." or target.startswith("../") or "\\" in target or "\x00" in target:
        raise ValueError(f"question link escapes repository: {value}")
    if target_id in by_id and by_id[target_id].path.as_posix() == target:
        target = article_path(target_id).as_posix()
    relative = posixpath.relpath(target, article_path(question.id).parent.as_posix())
    return urlunsplit(("", "", quote(relative, safe="/"), parsed.query, parsed.fragment))


def _body(question, by_id: dict) -> str:
    content = _open_main_answer(question.body)
    output = []
    character, length = "", 0

    def link(match):
        value = match["url"]
        angle = value.startswith("<") and value.endswith(">")
        rewritten = _relative_url(value[1:-1] if angle else value, question, by_id)
        return match["open"] + ("<" + rewritten + ">" if angle else rewritten) + (match["title"] or "") + ")"

    labels = {"详细答案": "详细解析", "常见追问": "常见追问", "实战案例": "实战案例",
              "常见误区": "常见误区", "微练习": "动手想一想", "学习与参考": "学习参考",
              "学习章与参考": "学习参考"}
    for line in content.splitlines(keepends=True):
        match = FENCE.match(line)
        if character:
            output.append(line)
            if match and match[1][0] == character and len(match[1]) >= length and not match[2].strip():
                character, length = "", 0
            continue
        if match:
            character, length = match[1][0], len(match[1])
            output.append(line)
            continue
        short_answer = re.match(r"^\*\*30[–—-]60\s*秒回答[：:]\*\*\s*(.*)$", line.rstrip("\r\n"))
        section = re.match(r"^\*\*([^*]+?)[：:]\*\*\s*(.*)$", line.rstrip("\r\n"))
        if short_answer:
            line = "## 简要回答\n" + ("\n" + short_answer[1] + "\n" if short_answer[1] else "")
        elif section and section[1] in labels:
            line = "## " + labels[section[1]] + "\n" + ("\n" + section[2] + "\n" if section[2] else "")
        else:
            heading = re.match(r"^(#{4,6}) (.+?)(\r?\n)?$", line)
            if heading:
                line = "#" * (len(heading[1]) - 1) + " " + heading[2] + (heading[3] or "")
        output.append(INLINE_LINK.sub(link, line))
    return "".join(output).strip() + "\n"


def _group_title(path: Path, root: Path) -> str:
    source = root / path
    if source.is_file():
        match = re.search(r"^# (.+)$", source.read_text(encoding="utf-8"), re.M)
        if match:
            return match[1]
    return path.stem


def article_pages(bank, root: Path) -> dict[Path, str]:
    """Return deterministic repository-relative paths and complete Markdown bytes."""
    bank = sorted(bank, key=lambda question: question.id)
    by_id = {question.id: question for question in bank}
    if len(by_id) != len(bank):
        raise ValueError("duplicate question IDs")
    result = {}
    groups = OrderedDict()
    for position, question in enumerate(bank):
        groups.setdefault(question.path, []).append(question)
        heading = f"{question.id} {question.title}"
        source_url = Path(relpath(question.path, article_path(question.id).parent)).as_posix()
        navigation = []
        if position:
            previous = bank[position - 1]
            navigation.append(f"[上一题：{previous.id}]({previous.id}.md)")
        navigation.append("[全部题目](README.md)")
        if position + 1 < len(bank):
            following = bank[position + 1]
            navigation.append(f"[下一题：{following.id}]({following.id}.md)")
        content = (GENERATED.format(source=question.path.as_posix()) + "\n\n# " + heading + "\n\n"
                   + _body(question, by_id) + "\n---\n\n" + " · ".join(navigation)
                   + f"\n\n[按模块阅读]({source_url}#{_slug(heading)})\n")
        result[article_path(question.id)] = content
    index = ["# 逐题阅读", "", "每道题是一篇独立文章：先读简要回答，再沿详细解析、图解、案例与追问理解知识。基础原理与工程进阶两部分另有完整的连续讲解，题目文章供复习、追问与查漏。", "",
             "[知识主线](../learning/knowledge-map.md) · [基础原理](../learning/README.md) · [工程进阶](../advanced/README.md)", ""]
    for folder, title in (("foundations", "基础原理"), ("engineering", "工程应用"), ("advanced", "进阶系统")):
        topics = [(source, items) for source, items in groups.items() if source.parent.name == folder]
        if not topics:
            continue
        index.extend(["## " + title, ""])
        for source, items in topics:
            index.extend(["### " + _group_title(source, root), ""])
            for question in items:
                index.append(f"- [{question.id} {question.title}]({question.id}.md)")
            index.append("")
    index.extend(["[带课程对应的总索引](../docs/question-index.md) · [返回首页](../README.md)", ""])
    result[Path("questions/README.md")] = "\n".join(index)
    return result


def write_articles(bank, root: Path) -> None:
    for relative, content in article_pages(bank, root).items():
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8")


def check_articles(bank, root: Path) -> list[str]:
    expected = article_pages(bank, root)
    failures = []
    for path, content in expected.items():
        actual = root / path
        if not actual.is_file() or actual.read_text(encoding="utf-8") != content:
            failures.append(f"{path.as_posix()} 独立文章需更新：python3 scripts/check_repo.py --write-index")
    extra = {p.relative_to(root) for p in (root / "questions").glob("Q[0-9][0-9][0-9].md")} - set(expected)
    failures.extend(f"多余独立题目：{p.as_posix()}" for p in sorted(extra))
    return failures
