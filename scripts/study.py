#!/usr/bin/env python3
"""Offline question browser and transparent date-based review scheduling."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import date, datetime, timedelta
import json
import os
from pathlib import Path
import random
import re
import tempfile
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
HEADING = re.compile(r"^### (Q\d{3}) (.+)$", re.MULTILINE)
FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
BANK_FOLDERS = ("foundations", "engineering", "advanced")


@dataclass(frozen=True)
class Question:
    id: str
    title: str
    path: Path
    body: str


def _structural_text(content: str) -> str:
    """Hide fenced examples while retaining offsets into the original answer."""
    lines = []
    character, length = "", 0
    for line in content.splitlines(keepends=True):
        marker = FENCE.match(line)
        if character:
            lines.append("".join("\n" if char == "\n" else " " for char in line))
            if marker and marker[1][0] == character and len(marker[1]) >= length and not marker[2].strip():
                character, length = "", 0
        elif marker:
            character, length = marker[1][0], len(marker[1])
            lines.append("".join("\n" if char == "\n" else " " for char in line))
        else:
            lines.append(line)
    return "".join(lines)


def questions(root: Path = ROOT) -> list[Question]:
    found = []
    for folder in BANK_FOLDERS:
        for path in sorted((root / "docs" / folder).glob("*.md")):
            content = path.read_text(encoding="utf-8")
            structural = _structural_text(content)
            matches = list(HEADING.finditer(structural))
            for i, match in enumerate(matches):
                end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
                # Chapter navigation and reference sections are outside individual answers.
                section = re.search(r"\n## ", structural[match.end():end])
                if section:
                    end = match.end() + section.start()
                body = content[match.end():end].strip()
                found.append(Question(match[1], match[2], path.relative_to(root), body))
    ids = [q.id for q in found]
    if len(ids) != len(set(ids)):
        raise ValueError("题号重复，请先修正文档。")
    return sorted(found, key=lambda q: q.id)


def readable_answer(body: str) -> str:
    """Expand GitHub's answer folds for a terminal while retaining all answer text."""
    visible = _structural_text(body)
    output, position = [], 0
    for match in re.finditer(r"<summary>(.*?)</summary>|</?details\b[^>]*>", visible, re.S):
        output.append(body[position:match.start()])
        if match[1] is not None:
            output.append(body[match.start(1):match.end(1)] + "\n")
        position = match.end()
    output.append(body[position:])
    return "".join(output).strip()


def today() -> date:
    return datetime.now(ZoneInfo("Asia/Shanghai")).date()


def read_progress(path: Path) -> dict:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("进度文件应是 JSON 对象；请修复或备份后重建。")
    for qid, item in data.items():
        if not isinstance(item, dict) or not isinstance(item.get("stage"), int):
            raise ValueError(f"进度记录 {qid} 缺少有效 stage。")
        if not 0 <= item["stage"] <= 3:
            raise ValueError(f"进度记录 {qid} 的 stage 超出范围。")
        date.fromisoformat(item["due"])
    return data


def schedule(previous: dict, score: int, day: date) -> dict:
    if score not in range(4):
        raise ValueError("score 必须是 0、1、2 或 3。")
    stage = max(-1, min(3, int(previous.get("stage", -1))))
    if score in (0, 1):
        stage, interval = 0, score
    elif score == 2:
        stage, interval = max(1, stage), 3
    else:
        stage = min(3, stage + 1)
        interval = (1, 3, 7, 14)[stage]
    return {"score": score, "stage": stage,
            "reviews": previous.get("reviews", 0) + 1,
            "last_review": day.isoformat(),
            "due": (day + timedelta(days=interval)).isoformat()}


def save_progress(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # Atomic replacement prevents an interrupted write from truncating past reviews.
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                         prefix=".progress-", delete=False) as handle:
            tmp = handle.name
            json.dump(data, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        os.replace(tmp, path)
    finally:
        if tmp and os.path.exists(tmp):
            os.unlink(tmp)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="离线抽题、阅读与复习；日期按 Asia/Shanghai。")
    parser.add_argument("--progress", type=Path, default=ROOT / ".local/study-progress.json")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("list", "draw"):
        command = commands.add_parser(name)
        command.add_argument("--topic", default="")
        if name == "draw":
            command.add_argument("--count", type=int, default=5)
            command.add_argument("--seed", type=int)
    commands.add_parser("show").add_argument("id")
    review = commands.add_parser("review")
    review.add_argument("id")
    review.add_argument("--score", type=int, required=True, choices=range(4))
    commands.add_parser("due")
    commands.add_parser("stats")
    args = parser.parse_args(argv)
    try:
        bank = questions()
        if not bank:
            raise ValueError("未发现题目；请从完整仓库运行。")
        by_id = {q.id: q for q in bank}
        if args.command in ("list", "draw"):
            topic = args.topic.casefold()
            selected = [q for q in bank if topic in f"{q.title} {q.path} {q.body}".casefold()]
            if args.command == "draw":
                if args.count < 1:
                    parser.error("--count 必须大于 0")
                selected = random.Random(args.seed).sample(selected, min(args.count, len(selected)))
            for q in selected:
                print(f"{q.id} {q.title}  [{q.path}]")
            print(f"共 {len(selected)} 题。先口述，再用 show 查看答案。")
            return 0
        if args.command in ("show", "review"):
            qid = args.id.upper()
            if qid not in by_id:
                parser.error(f"未知题号：{qid}")
            question = by_id[qid]
            if args.command == "show":
                print(f"{question.id} {question.title}\n来源：{question.path}\n\n{readable_answer(question.body)}")
                return 0
        progress = read_progress(args.progress)
        day = today()
        if args.command == "review":
            progress[qid] = schedule(progress.get(qid, {}), args.score, day)
            save_progress(args.progress, progress)
            print(f"{qid} 已记录：{args.score} 分；下次复习 {progress[qid]['due']}。")
        else:
            seen = {qid: item for qid, item in progress.items() if qid in by_id}
            due = [q for q in bank if q.id in seen and date.fromisoformat(seen[q.id]["due"]) <= day]
            unseen = [q for q in bank if q.id not in seen]
            if args.command == "stats":
                print(f"题目 {len(bank)}；已自评 {len(seen)}；未学习 {len(unseen)}；到期 {len(due)}。")
                print("自评与复习间隔不代表客观掌握程度。")
            else:
                print(f"今天 {day}（Asia/Shanghai）\n到期复习：")
                for q in due:
                    print(f"  {q.id} {q.title}")
                if not due:
                    print("  暂无")
                print(f"未学习（{len(unseen)} 题）：")
                for q in unseen:
                    print(f"  {q.id} {q.title}")
        return 0
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, f"无法完成：{error}\n")


if __name__ == "__main__":
    raise SystemExit(main())
