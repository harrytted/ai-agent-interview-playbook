#!/usr/bin/env python3
"""Validate built HTML links, question anchors and rendered answer blocks."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

PROJECT_BASE = "/ai-agent-interview-playbook/"
SITE_HOST = "harrytted.github.io"
EXPECTED_QUESTIONS = frozenset(range(1, 93))
HTML_SUFFIXES = frozenset({".html", ".htm"})
REFERENCE_ATTRIBUTES = {"a": "href", "img": "src", "script": "src", "link": "href"}


@dataclass
class AnswerBlock:
    tags: Counter[str] = field(default_factory=Counter)
    text: list[str] = field(default_factory=list)
    prose: list[str] = field(default_factory=list)
    closed: bool = False


@dataclass
class Question:
    number: int
    anchor: str
    line: int
    answers: list[AnswerBlock] = field(default_factory=list)


class SiteHTML(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids: set[str] = set()
        self.element_id_lines: dict[str, int] = {}
        self.duplicate_ids: list[tuple[str, int, int]] = []
        self.references: list[tuple[str, str, str, int]] = []
        self.questions: list[Question] = []
        self.heading_errors: list[str] = []
        self._heading: list[str] | None = None
        self._heading_id = ""
        self._heading_line = 0
        self._question: Question | None = None
        self._answer: AnswerBlock | None = None
        self._details_depth = 0
        self._code_depth = 0
        self.h1_titles: list[str] = []
        self.section_titles: list[str] = []
        self._article_heading: list[str] | None = None
        self._article_heading_tag = ""

    def handle_starttag(self, tag: str, attrs):
        values = dict(attrs)
        if values.get("id"):
            identity = values["id"]
            line = self.getpos()[0]
            if identity in self.element_id_lines:
                self.duplicate_ids.append((identity, line, self.element_id_lines[identity]))
            else:
                self.element_id_lines[identity] = line
            self.ids.add(identity)
        if tag == "a" and values.get("name"):
            self.ids.add(values["name"])
        attr = REFERENCE_ATTRIBUTES.get(tag)
        if attr and values.get(attr) is not None:
            self.references.append((tag, attr, values[attr], self.getpos()[0]))

        if tag in {"h1", "h2", "h3"}:
            self._question = None
        if tag in {"h1", "h2"}:
            self._article_heading = []
            self._article_heading_tag = tag
        if tag == "h3":
            self._heading = []
            self._heading_id = values.get("id", "")
            self._heading_line = self.getpos()[0]

        if tag == "details":
            if self._details_depth:
                self._details_depth += 1
            elif self._question is not None:
                self._answer = AnswerBlock()
                self._question.answers.append(self._answer)
                self._details_depth = 1
        if self._answer is not None:
            self._answer.tags[tag] += 1
            if tag in {"pre", "code"}:
                self._code_depth += 1

    def handle_startendtag(self, tag: str, attrs):
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_data(self, data: str):
        if self._article_heading is not None:
            self._article_heading.append(data)
        if self._heading is not None:
            self._heading.append(data)
        if self._answer is not None:
            self._answer.text.append(data)
            if not self._code_depth:
                self._answer.prose.append(data)

    def handle_endtag(self, tag: str):
        if tag == self._article_heading_tag and self._article_heading is not None:
            text = " ".join("".join(self._article_heading).split()).rstrip(" ¶")
            (self.h1_titles if tag == "h1" else self.section_titles).append(text)
            self._article_heading = None
            self._article_heading_tag = ""
        if tag == "h3" and self._heading is not None:
            text = " ".join("".join(self._heading).split())
            title = re.match(r"Q(\d{3})(?:\s|$)", text)
            anchor = re.match(r"q(\d{3})(?:-|$)", self._heading_id, re.IGNORECASE)
            if title or anchor:
                if not title or not anchor or title[1] != anchor[1]:
                    self.heading_errors.append(
                        f"line {self._heading_line}: question title and h3 id disagree: {text!r} / {self._heading_id!r}"
                    )
                else:
                    self._question = Question(int(title[1]), self._heading_id, self._heading_line)
                    self.questions.append(self._question)
            self._heading = None
        if self._answer is not None and tag in {"pre", "code"}:
            self._code_depth = max(0, self._code_depth - 1)
        if tag == "details" and self._details_depth:
            self._details_depth -= 1
            if not self._details_depth:
                if self._answer is not None:
                    self._answer.closed = True
                self._answer = None
                self._code_depth = 0


@dataclass
class CheckResult:
    errors: list[str] = field(default_factory=list)
    pages: int = 0
    references: int = 0
    questions: int = 0
    articles: int = 0


def resolve_reference(root: Path, page: Path, value: str) -> tuple[Path, str] | None:
    """Resolve a browser reference without reading outside the site directory."""
    url = urlsplit(value.strip())
    if url.netloc or url.scheme:
        if url.scheme not in {"", "http", "https"} or url.hostname != SITE_HOST:
            return None
    path = unquote(url.path, errors="strict")
    fragment = unquote(url.fragment, errors="strict").split(":~:text=", 1)[0]
    if "\x00" in path:
        raise ValueError("NUL character in local URL")
    if path.startswith("/"):
        if path == PROJECT_BASE.rstrip("/"):
            path = ""
        elif path.startswith(PROJECT_BASE):
            path = path[len(PROJECT_BASE):]
        else:
            raise ValueError(f"URL is outside project base {PROJECT_BASE}")
        target = root / path
    elif not path:
        target = page
    else:
        # The generated root 404.html also resolves relative links at the site root.
        target = page.parent / path
    target = target.resolve()
    if not target.is_relative_to(root):
        raise ValueError("URL escapes site directory")
    if target.is_dir() or path.endswith("/"):
        target = (target / "index.html").resolve()
    if not target.is_relative_to(root):
        raise ValueError("URL escapes site directory")
    return target, fragment


def check_site(site_dir: Path) -> CheckResult:
    root = site_dir.resolve()
    result = CheckResult()
    if not root.is_dir():
        result.errors.append(f"Site directory does not exist: {root}")
        return result

    pages: dict[Path, SiteHTML] = {}
    for source in sorted(root.rglob("*")):
        if not source.is_file() or source.suffix.lower() not in HTML_SUFFIXES:
            continue
        page = source.resolve()
        if not page.is_relative_to(root):
            result.errors.append(f"{source.relative_to(root)}: HTML file escapes site directory")
            continue
        parser = SiteHTML()
        try:
            parser.feed(page.read_text(encoding="utf-8"))
            parser.close()
        except (OSError, UnicodeError) as error:
            result.errors.append(f"{source.relative_to(root)}: cannot read HTML: {error}")
            continue
        pages[page] = parser
    result.pages = len(pages)
    if not pages:
        result.errors.append("No built HTML pages found")

    for page, parser in pages.items():
        for identity, line, first_line in parser.duplicate_ids:
            result.errors.append(
                f"{page.relative_to(root)}:{line}: duplicate element id {identity!r} (first at line {first_line})"
            )
        seen: set[tuple[str, str, str]] = set()
        for tag, attr, value, line in parser.references:
            key = (tag, attr, value)
            if key in seen:
                continue
            seen.add(key)
            location = f"{page.relative_to(root)}:{line} {tag}[{attr}]={value!r}"
            try:
                resolved = resolve_reference(root, page, value)
            except (ValueError, UnicodeError) as error:
                result.errors.append(f"{location}: {error}")
                continue
            if resolved is None:
                continue
            result.references += 1
            target, fragment = resolved
            if not target.is_file():
                result.errors.append(f"{location}: missing file {target.relative_to(root)}")
                continue
            if not fragment or target.suffix.lower() not in HTML_SUFFIXES | {".svg"}:
                continue
            destination = pages.get(target)
            if destination is None:
                destination = SiteHTML()
                try:
                    destination.feed(target.read_text(encoding="utf-8"))
                    destination.close()
                except (OSError, UnicodeError) as error:
                    result.errors.append(f"{location}: cannot read fragment target: {error}")
                    continue
            if fragment not in destination.ids:
                result.errors.append(f"{location}: missing fragment {fragment!r} in {target.relative_to(root)}")

    inventory: dict[int, list[str]] = defaultdict(list)
    for page, parser in pages.items():
        if page.relative_to(root).parts[0] != "docs":
            continue
        result.errors.extend(f"{page.relative_to(root)}: {error}" for error in parser.heading_errors)
        for question in parser.questions:
            location = f"{page.relative_to(root)}:{question.line} Q{question.number:03}"
            inventory[question.number].append(location)
            if not question.answers:
                result.errors.append(f"{location}: missing details answer block")
                continue
            block = question.answers[0]
            text = "".join(block.text)
            prose = "\n".join(block.prose)
            structured = (
                (block.tags["p"] or block.tags["h4"])
                and (block.tags["ol"] or block.tags["ul"])
                and block.tags["li"] >= 3
            )
            labels = all(label in text for label in ("详细答案", "常见追问", "实战案例"))
            raw_markdown = re.search(
                r"(?m)^\s*(?:\*\*(?:详细答案|常见追问|实战案例)[：:]?\*\*|#{1,4}\s+)", prose
            )
            if not block.closed or not structured or not labels or raw_markdown:
                result.errors.append(f"{location}: details answer is not rendered as structured HTML")

    result.questions = sum(map(len, inventory.values()))
    missing = EXPECTED_QUESTIONS - inventory.keys()
    unexpected = inventory.keys() - EXPECTED_QUESTIONS
    if missing:
        result.errors.append("Missing question h3 IDs: " + ", ".join(f"Q{n:03}" for n in sorted(missing)))
    if unexpected:
        result.errors.append("Unexpected question h3 IDs: " + ", ".join(f"Q{n:03}" for n in sorted(unexpected)))
    for number, locations in inventory.items():
        if len(locations) > 1:
            result.errors.append(f"Duplicate Q{number:03} h3 IDs: " + "; ".join(locations))
    # Old grouped URLs retain their 92 anchors. The primary reading surface is
    # separately checked when standalone articles are present.
    if (root / "questions").is_dir():
        articles: dict[int, list[Path]] = defaultdict(list)
        for page, parser in pages.items():
            relative = page.relative_to(root)
            if len(relative.parts) < 2 or relative.parts[0] != "questions":
                continue
            match = re.fullmatch(r"Q(\d{3})", Path(relative.parts[1]).stem)
            if not match:
                continue
            number = int(match[1])
            articles[number].append(page)
            if len(parser.h1_titles) != 1 or not parser.h1_titles[0].startswith(f"Q{number:03} "):
                result.errors.append(f"{relative}: standalone question H1 disagrees with its filename")
            required_sections = {"简要回答", "详细解析", "常见追问", "实战案例", "常见误区", "动手想一想", "学习参考"}
            if not required_sections.issubset(parser.section_titles):
                result.errors.append(f"{relative}: standalone article sections are missing or not rendered")
        result.articles = sum(map(len, articles.values()))
        missing_articles = EXPECTED_QUESTIONS - articles.keys()
        unexpected_articles = articles.keys() - EXPECTED_QUESTIONS
        if missing_articles:
            result.errors.append("Missing standalone articles: " + ", ".join(f"Q{n:03}" for n in sorted(missing_articles)))
        if unexpected_articles:
            result.errors.append("Unexpected standalone articles: " + ", ".join(f"Q{n:03}" for n in sorted(unexpected_articles)))
        for number, locations in articles.items():
            if len(locations) != 1:
                result.errors.append(f"Duplicate standalone Q{number:03}")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("site_dir", nargs="?", type=Path, default=Path("site"))
    args = parser.parse_args(argv)
    result = check_site(args.site_dir)
    if result.errors:
        for error in result.errors:
            print(f"ERROR: {error}", file=sys.stderr)
        print(f"Site check failed: {len(result.errors)} errors", file=sys.stderr)
        return 1
    print(
        f"Site check passed: {result.pages} HTML pages, {result.references} local references, "
        f"{result.questions} rendered questions (Q001–Q092)."
        + (f" {result.articles} standalone articles." if result.articles else "")
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
