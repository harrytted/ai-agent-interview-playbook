"""Reading-page navigation and accessible, correctly sized local diagrams."""
from html import escape
from html.parser import HTMLParser
from pathlib import Path
import posixpath
import re
import struct
from urllib.parse import unquote, urlsplit


class _Image(HTMLParser):
    def handle_starttag(self, tag, attrs):
        self.attrs = dict(attrs)


class _ChapterLinks(HTMLParser):
    """Recognize a standalone Markdown chapter-switching paragraph."""

    def __init__(self, html):
        super().__init__()
        self.labels = []
        self.outside = []
        self.in_link = False
        self.only_links = True
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.labels.append("")
            self.in_link = True
        else:
            self.only_links = False

    def handle_endtag(self, tag):
        if tag == "a":
            self.in_link = False

    def handle_data(self, data):
        if self.in_link:
            self.labels[-1] += data
        else:
            self.outside.append(data)

    @property
    def is_navigation(self):
        return (self.only_links and bool(self.labels)
                and all(re.match(r"^(上一章|下一章|学习目录|阅读目录|基础原理目录|工程进阶目录)", label)
                        for label in self.labels)
                and not re.sub(r"[\s·|：:]+", "", "".join(self.outside)))


def _chapter_navigation(html, page, config, files):
    if 'class="chapter-pagination"' in html or files is None:
        return html
    source = getattr(page.file, "src_uri", "")
    if not re.fullmatch(r"(?:learning|advanced)/\d{2}-[^/]+\.md", source):
        return html

    def pages(entries):
        for entry in entries:
            if isinstance(entry, str):
                continue
            for title, target in entry.items():
                if isinstance(target, str):
                    yield title, target
                elif isinstance(target, list):
                    yield from pages(target)

    section = source.split("/", 1)[0]
    section_title = "基础原理" if section == "learning" else "工程进阶"
    section_pages = next((entry[section_title] for entry in config.get("nav") or []
                          if isinstance(entry, dict) and section_title in entry), [])
    chapters = [(title, path) for title, path in pages(section_pages)
                if re.fullmatch(rf"{section}/\d{{2}}-[^/]+\.md", path)]
    current = next((i for i, (_, path) in enumerate(chapters) if path == source), None)
    if current is None:
        return html

    def link(label, title, path, kind):
        target = files.get_file_from_path(path)
        if target is None:
            raise ValueError(f"Chapter navigation target does not exist: {path}")
        url = target.url
        relative = posixpath.relpath(url, posixpath.dirname(page.file.dest_uri))
        if url.endswith("/"):
            relative = "./" if relative == "." else relative + "/"
        text = (f'<span class="chapter-pagination__text">'
                f'<span class="chapter-pagination__label">{escape(label)}</span>'
                f'<span class="chapter-pagination__title">{escape(title)}</span></span>')
        arrow = '<span class="chapter-pagination__arrow" aria-hidden="true">{}</span>'
        contents = arrow.format("←") + text if kind == "prev" else text
        if kind == "next":
            contents += arrow.format("→")
        return (f'<a class="chapter-pagination__{kind}" href="{escape(relative, quote=True)}" '
                f'aria-label="{escape(label + "：" + title, quote=True)}">{contents}</a>')

    links = []
    if current:
        title, path = chapters[current - 1]
        links.append(link("上一章", title, path, "prev"))
    links.append(link("章节目录", section_title, f"{section}/index.md", "index"))
    if current + 1 < len(chapters):
        title, path = chapters[current + 1]
        links.append(link("下一章", title, path, "next"))

    # Keep one chapter switcher, after the article and its related exercises.
    html = re.sub(r"<p>(.*?)</p>",
                  lambda match: "" if _ChapterLinks(match[1]).is_navigation else match[0],
                  html, flags=re.S)
    if not isinstance(getattr(page, "meta", None), dict):
        page.meta = {}
    hidden = page.meta.setdefault("hide", [])
    if "footer" not in hidden:
        hidden.append("footer")
    return html + '<nav class="chapter-pagination" aria-label="章节切换">' + "".join(links) + '</nav>'


def on_page_content(html, *, page, config, files):
    first_image = True
    local_pngs = {}
    docs = Path(config["docs_dir"]).resolve()

    def enrich(match):
        nonlocal first_image
        parser = _Image()
        parser.feed(match[0])
        attrs = parser.attrs
        src = urlsplit(attrs.get("src", ""))
        if src.scheme or src.netloc or not src.path.lower().endswith(".png"):
            return match[0]
        # The HTML src is relative to the output page, not the Markdown source.
        path = (docs / Path(page.file.dest_uri).parent / unquote(src.path)).resolve()
        if not path.is_relative_to(docs) or not path.is_file():
            return match[0]
        with path.open("rb") as image:
            header = image.read(24)
        if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n":
            return match[0]
        width, height = struct.unpack(">II", header[16:24])
        local_pngs[attrs["src"]] = width
        defaults = {"width": str(width), "height": str(height),
                    "loading": "eager" if first_image else "lazy", "decoding": "async"}
        first_image = False
        additions = "".join(f' {name}="{value}"' for name, value in defaults.items() if name not in attrs)
        return re.sub(r"\s*/?>$", lambda ending: additions + ending[0], match[0])

    html = re.sub(r"<img\b[^>]*>", enrich, html, flags=re.I)

    def readable_diagram(match):
        image = _Image()
        image.feed(match["image"])
        link = _Image()
        link.feed(match["open"])
        src = image.attrs.get("src", "")
        if src not in local_pngs or link.attrs.get("href") != src:
            return match[0]
        # Only standalone links to their own local PNG become figures. Inline
        # illustrations and images that navigate elsewhere retain their meaning.
        width = min(720, local_pngs[src])
        return (
            f'<figure class="diagram-figure" style="--diagram-mobile-width: {width}px">'
            '<div class="diagram-scroll" tabindex="0" role="region" '
            'aria-label="图表，可左右滚动查看">'
            + match["link"] + '</div>'
            '<figcaption class="diagram-hint">左右滑动查看全图，也可点击图片放大。</figcaption>'
            '</figure>'
        )

    html = re.sub(
        r'<p>\s*(?P<link>(?P<open><a\b[^>]*>)\s*(?P<image><img\b[^>]*>)\s*</a>)\s*</p>',
        readable_diagram, html, flags=re.I,
    )
    return _chapter_navigation(html, page, config, files)
