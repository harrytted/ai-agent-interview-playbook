"""Reserve diagram space and defer below-fold PNGs without modifying their pixels."""
from html.parser import HTMLParser
from pathlib import Path
import re
import struct
from urllib.parse import unquote, urlsplit


class _Image(HTMLParser):
    def handle_starttag(self, tag, attrs):
        self.attrs = dict(attrs)


def on_page_content(html, *, page, config, files):
    first_image = True
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
        defaults = {"width": str(width), "height": str(height),
                    "loading": "eager" if first_image else "lazy", "decoding": "async"}
        first_image = False
        additions = "".join(f' {name}="{value}"' for name, value in defaults.items() if name not in attrs)
        return re.sub(r"\s*/?>$", lambda ending: additions + ending[0], match[0])

    return re.sub(r"<img\b[^>]*>", enrich, html, flags=re.I)
