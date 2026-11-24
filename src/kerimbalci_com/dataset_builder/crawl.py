"""Crawls the site via its sitemap and converts every page to plain text.

Output (under SITE_WORKDIR):
    text/<stem>.txt  first line is JSON metadata (og:title, published_time, tag), then the text
    manifest.json    {stem: url}
"""

import json
import logging
import re
import urllib.request
import xml.etree.ElementTree as ET
from collections.abc import Callable
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

from kerimbalci_com.config import Settings

logger = logging.getLogger(__name__)

Fetcher = Callable[[str], str]

_SITEMAP_NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
_SKIP_TAGS = {"script", "style", "nav", "header", "footer", "svg", "noscript", "form", "aside"}
_BLOCK_TAGS = {"p", "h1", "h2", "h3", "h4", "li", "br", "blockquote"}
_META_PROPERTIES = {"og:title", "article:published_time", "article:tag"}
_ASSET = re.compile(r"\.(jpe?g|png|webp|gif|svg)$", re.IGNORECASE)


def make_fetcher(settings: Settings) -> Fetcher:
    """Returns a function that downloads a URL as text using the configured User-Agent and timeout."""
    def fetch(url: str) -> str:
        request = urllib.request.Request(url, headers={"User-Agent": settings.crawl_user_agent})
        with urllib.request.urlopen(request, timeout=settings.http_timeout) as response:
            return response.read().decode("utf-8", errors="replace")
    return fetch


def parse_sitemap(xml_text: str) -> list[str]:
    """Returns the <loc> URLs of a sitemap (or sitemap index)."""
    root = ET.fromstring(xml_text)
    return [loc.text.strip() for loc in root.iter(f"{_SITEMAP_NS}loc") if loc.text]


def discover_urls(site_url: str, fetch: Fetcher) -> list[str]:
    """sitemap.xml -> child sitemaps -> page URLs (images excluded, deduplicated)."""
    index = parse_sitemap(fetch(site_url.rstrip("/") + "/sitemap.xml"))
    children = [u for u in index if u.endswith(".xml")] or [site_url.rstrip("/") + "/sitemap.xml"]
    urls: list[str] = []
    for child in children:
        for url in parse_sitemap(fetch(child)):
            if not _ASSET.search(url) and url not in urls:
                urls.append(url)
    return urls


def stem_for_url(url: str) -> str:
    """File name for a URL: / -> home, /tag/x/ -> tag_x, /post/ -> post."""
    path = urlparse(url).path.strip("/")
    return path.replace("/", "_") if path else "home"


class _TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self._skip_depth = 0
        self.parts: list[str] = []
        self.meta: dict[str, list[str]] = {}

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "meta":
            key = attrs.get("property") if attrs.get("property") in _META_PROPERTIES else None
            if key is None and attrs.get("name") == "description":
                key = "description"
            if key and attrs.get("content"):
                self.meta.setdefault(key, []).append(attrs["content"])
        if tag in _SKIP_TAGS:
            self._skip_depth += 1
        if tag in _BLOCK_TAGS:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in _SKIP_TAGS and self._skip_depth:
            self._skip_depth -= 1

    def handle_data(self, data):
        if not self._skip_depth:
            self.parts.append(data)


def extract_text(html: str) -> str:
    """Builds a metadata line + readable body text from HTML (nav/footer/script excluded)."""
    parser = _TextExtractor()
    parser.feed(html)
    body = re.sub(r"[ \t]+", " ", "".join(parser.parts))
    body = re.sub(r"\n\s*\n+", "\n\n", body).strip()
    return json.dumps(parser.meta, ensure_ascii=False) + "\n\n" + body


def crawl(settings: Settings, fetch: Fetcher | None = None) -> dict[str, str]:
    """Downloads the whole site into SITE_WORKDIR and returns the {stem: url} manifest."""
    fetch = fetch or make_fetcher(settings)
    text_dir = settings.site_workdir / "text"
    text_dir.mkdir(parents=True, exist_ok=True)

    manifest: dict[str, str] = {}
    urls = discover_urls(settings.site_url, fetch)
    logger.info("%d pages found", len(urls))
    for url in urls:
        stem = stem_for_url(url)
        try:
            (text_dir / f"{stem}.txt").write_text(extract_text(fetch(url)), encoding="utf-8")
            manifest[stem] = url
        except Exception as exc:  # noqa: BLE001 — one page must not stop the whole crawl
            logger.warning("Could not download %s: %s", url, exc)
    (settings.site_workdir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    logger.info("%d pages written: %s", len(manifest), text_dir)
    return manifest


def split_groups(text_dir: Path, count: int) -> list[list[str]]:
    """Splits the text files into `count` groups with balanced total word counts."""
    files = sorted(text_dir.glob("*.txt"), key=lambda f: -len(f.read_text(encoding="utf-8").split()))
    groups: list[list[str]] = [[] for _ in range(max(1, count))]
    weights = [0] * len(groups)
    for f in files:
        i = weights.index(min(weights))
        groups[i].append(f.name)
        weights[i] += len(f.read_text(encoding="utf-8").split())
    return groups
