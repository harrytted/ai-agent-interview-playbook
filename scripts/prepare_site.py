#!/usr/bin/env python3
"""Prepare an allowlisted Markdown tree for MkDocs without changing its sources."""
from __future__ import annotations

import argparse
from collections import defaultdict
import os
from pathlib import Path, PurePosixPath
import posixpath
import re
import shutil
import unicodedata
from urllib.parse import quote, unquote, urlsplit, urlunsplit


ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_URL = "https://github.com/harrytted/ai-agent-interview-playbook"
ROOT_PAGES = ("README.md", "CONTRIBUTING.md", "CHANGELOG.md")
PAGE_FOLDERS = ("learning", "advanced", "docs", "practice", "research")
ASSET_EXTENSIONS = {".css", ".js", ".svg", ".png", ".ico", ".woff2"}
PRIVATE_NAMES = {".git", ".local", "env", "venv", ".venv", "__pycache__",
                 "node_modules", "credentials", "credential", "secrets"}
MARKER = ".prepared-site-source"
MARKER_CONTENT = "agent-interview-playbook site sources v1\n"
FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
HEADING = re.compile(r"^(#{1,6})[ \t]+(.+?)\s*$")
EXPLICIT_ID = re.compile(r"\{[^{}]*#[^{}\s]+[^{}]*\}\s*$")
INLINE_LINK = re.compile(
    r"(?P<open>!?\[[^\]\n]*\]\()"
    r"(?P<url><[^>\n]+>|[^ \t\r\n)]+)"
    r"(?P<title>[ \t]+(?:\"[^\"\n]*\"|'[^'\n]*'|\([^\n)]*\)))?\)"
)


def slug(text: str) -> str:
    """Match check_repo.slug so existing GitHub question fragments stay valid."""
    text = re.sub(r"\[([^]]+)\]\([^)]*\)", r"\1", text)
    text = text.replace("`", "").strip().lower()
    text = "".join(c for c in text if c in "_- " or unicodedata.category(c)[0] in "LN")
    return text.replace(" ", "-")


def private_path(path: PurePosixPath) -> bool:
    return any(part.startswith(".") or part.casefold() in PRIVATE_NAMES
               or PurePosixPath(part).stem.casefold() in {"credentials", "credential", "secrets"}
               for part in path.parts)


def source_files(root: Path) -> list[Path]:
    """Walk only public content roots; never use a repository-wide glob."""
    root = root.resolve()
    result = [root / name for name in ROOT_PAGES if (root / name).is_file()
              and not (root / name).is_symlink()]
    for folder in (*PAGE_FOLDERS, "examples"):
        base = root / folder
        if not base.is_dir() or base.is_symlink():
            continue
        for current, directories, files in os.walk(base, followlinks=False):
            current_path = Path(current)
            directories[:] = sorted(name for name in directories
                                    if not private_path(PurePosixPath(name))
                                    and not (current_path / name).is_symlink())
            for name in sorted(files):
                path = current_path / name
                relative = path.relative_to(root)
                allowed = name == "README.md" if folder == "examples" else name.endswith(".md")
                if allowed and not private_path(PurePosixPath(relative.as_posix())) and not path.is_symlink():
                    result.append(path)
    return sorted(result)


def page_mapping(root: Path) -> dict[PurePosixPath, PurePosixPath]:
    mapping = {}
    destinations = set()
    for source in source_files(root):
        relative = PurePosixPath(source.relative_to(root).as_posix())
        target = relative.with_name("index.md") if relative.name == "README.md" else relative
        if target in destinations:
            raise ValueError(f"Two source pages map to the same destination: {target}")
        mapping[relative] = target
        destinations.add(target)
    return mapping


def asset_mapping(root: Path) -> dict[PurePosixPath, PurePosixPath]:
    """Publish only known static formats from the dedicated website/assets tree."""
    base = root / "website/assets"
    if not base.is_dir() or base.is_symlink() or (root / "website").is_symlink():
        return {}
    mapping = {}
    for current, directories, files in os.walk(base, followlinks=False):
        current_path = Path(current)
        directories[:] = sorted(name for name in directories
                                if not private_path(PurePosixPath(name))
                                and not (current_path / name).is_symlink())
        for name in sorted(files):
            path = current_path / name
            relative = PurePosixPath(path.relative_to(root).as_posix())
            if (path.suffix.casefold() in ASSET_EXTENSIONS and not path.is_symlink()
                    and not private_path(relative)):
                mapping[relative] = PurePosixPath("assets") / path.relative_to(base).as_posix()
    return mapping


def rewrite_url(url: str, source: PurePosixPath, mapping: dict[PurePosixPath, PurePosixPath],
                root: Path) -> str:
    parsed = urlsplit(url)
    if parsed.scheme or parsed.netloc or not parsed.path:
        return url
    # Only repository-relative links are rewritten; absolute web paths remain web paths.
    if parsed.path.startswith("/"):
        return url
    decoded = unquote(parsed.path)
    if "\\" in decoded or "\x00" in decoded:
        raise ValueError(f"Unsupported repository link in {source}: {url}")
    normalized = posixpath.normpath(posixpath.join(str(source.parent), decoded))
    if normalized == ".." or normalized.startswith("../"):
        raise ValueError(f"Repository link escapes its source root in {source}: {url}")
    relative = PurePosixPath(normalized)
    if private_path(relative):
        raise ValueError(f"Private path is not a publishable link in {source}: {url}")
    target = mapping.get(relative)
    actual = root / relative
    is_directory = decoded.endswith("/") or actual.is_dir()
    if target is None and is_directory:
        target = mapping.get(relative / "README.md") or mapping.get(relative / "index.md")
    if target is not None:
        path = posixpath.relpath(str(target), str(mapping[source].parent))
        return urlunsplit(("", "", quote(path, safe="/"), parsed.query, parsed.fragment))
    kind = "tree" if is_directory else "blob"
    repository_path = quote(relative.as_posix(), safe="/")
    repository = urlsplit(REPOSITORY_URL)
    return urlunsplit((repository.scheme, repository.netloc,
                       f"{repository.path}/{kind}/main/{repository_path}",
                       parsed.query, parsed.fragment))


def transform_markdown(content: str, source: PurePosixPath,
                       mapping: dict[PurePosixPath, PurePosixPath], root: Path) -> str:
    counts: dict[str, int] = defaultdict(int)
    output = []
    fence_character = ""
    fence_length = 0

    def link(match: re.Match) -> str:
        value = match["url"]
        angle = value.startswith("<") and value.endswith(">")
        rewritten = rewrite_url(value[1:-1] if angle else value, source, mapping, root)
        if angle:
            rewritten = "<" + rewritten + ">"
        return match["open"] + rewritten + (match["title"] or "") + ")"

    def details(match: re.Match) -> str:
        tag = match.group()
        if re.search(r"\bmarkdown\s*=", tag, flags=re.I):
            return tag
        return tag[:-1].rstrip() + ' markdown="1">'

    for line in content.splitlines(keepends=True):
        body = line.rstrip("\r\n")
        ending = line[len(body):]
        marker = FENCE.match(body)
        if fence_character:
            output.append(line)
            if marker and marker[1][0] == fence_character and len(marker[1]) >= fence_length and not marker[2].strip():
                fence_character, fence_length = "", 0
            continue
        if marker:
            fence_character, fence_length = marker[1][0], len(marker[1])
            output.append(line)
            continue
        heading = HEADING.match(body)
        if heading:
            base = slug(heading[2])
            count = counts[base]
            counts[base] += 1
            if not EXPLICIT_ID.search(heading[2]):
                identity = base if count == 0 else f"{base}-{count}"
                body += f" {{#{identity}}}"
        body = INLINE_LINK.sub(link, body)
        body = re.sub(r"<details\b[^>]*>", details, body, flags=re.I)
        output.append(body + ending)
    return "".join(output)


def output_directory(root: Path, requested: Path | None) -> Path:
    raw = Path(requested) if requested is not None else Path(".site-src")
    if ".." in raw.parts:
        raise ValueError("Output must not contain parent-directory traversal")
    candidate = raw if raw.is_absolute() else root / raw
    if candidate.is_symlink():
        raise ValueError("Output must not be a symlink")
    output = candidate.resolve()
    if candidate.absolute().is_relative_to(root) and not output.is_relative_to(root):
        raise ValueError("Relative output must stay inside the repository")
    if output == Path(output.anchor) or root == output or root.is_relative_to(output):
        raise ValueError("Output must not be the repository, filesystem root, or a source ancestor")
    if output.is_relative_to(root):
        relative = output.relative_to(root)
        blocked = {*PAGE_FOLDERS, "examples", "scripts", "tests", "website", *PRIVATE_NAMES}
        if not relative.parts or relative.parts[0].casefold() in blocked:
            raise ValueError("Output overlaps a source or private directory")
    if output.exists():
        if not output.is_dir():
            raise ValueError("Output already exists as a file")
        entries = list(output.iterdir())
        marker = output / MARKER
        owned = marker.is_file() and not marker.is_symlink() and marker.read_text(encoding="utf-8") == MARKER_CONTENT
        if entries and not owned:
            raise ValueError("Refusing to clear a nonempty output without this script's ownership marker")
    return output


def prepare_site(root: Path = ROOT, output: Path | None = None) -> int:
    root = Path(root).resolve()
    destination = output_directory(root, output)
    mapping = page_mapping(root)
    assets = asset_mapping(root)
    links = {**mapping, **assets}
    # Transform everything before replacing any previous generated output.
    pages = {target: transform_markdown((root / source).read_text(encoding="utf-8"), source, links, root)
             for source, target in mapping.items()}
    asset_contents = {target: (root / source).read_bytes() for source, target in assets.items()}
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)
    (destination / MARKER).write_text(MARKER_CONTENT, encoding="utf-8")
    for relative, content in pages.items():
        path = destination / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    for relative, content in asset_contents.items():
        path = destination / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    return len(pages)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Generated source directory (default: .site-src)")
    args = parser.parse_args(argv)
    try:
        count = prepare_site(output=args.output)
    except (OSError, ValueError) as error:
        parser.exit(1, f"Cannot prepare site: {error}\n")
    print(f"Prepared {count} pages.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
