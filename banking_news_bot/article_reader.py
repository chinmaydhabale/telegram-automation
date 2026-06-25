from __future__ import annotations

import html
import re
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

from .models import NewsItem

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

SCRIPT_RE = re.compile(r"<(script|style|noscript|svg).*?</\1>", re.I | re.S)
TAG_RE = re.compile(r"<[^>]+>")
SPACE_RE = re.compile(r"\s+")


def clean_html(value: str) -> str:
    value = SCRIPT_RE.sub(" ", value)
    value = TAG_RE.sub(" ", value)
    value = html.unescape(value)
    return SPACE_RE.sub(" ", value).strip()


def decode_payload(payload: bytes, content_type: str) -> str:
    charset = "utf-8"
    for part in content_type.split(";"):
        part = part.strip().lower()
        if part.startswith("charset="):
            charset = part.split("=", 1)[1]
            break
    return payload.decode(charset, errors="replace")


def fetch_article_text(url: str, timeout: int = 15, max_chars: int = 2200) -> str:
    if not url:
        return ""
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-IN,en;q=0.9",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        content_type = response.headers.get("Content-Type", "")
        payload = response.read(450_000)
    if "text/html" not in content_type and "application/xhtml+xml" not in content_type:
        return ""
    text = clean_html(decode_payload(payload, content_type))
    return text[:max_chars]


def decode_link(link: str) -> str:
    link = (link or "").strip()
    if not link:
        return ""
    if link.startswith("https://news.google.com/"):
        try:
            import googlenewsdecoder
            decoded = googlenewsdecoder.gnewsdecoder(link)
            if isinstance(decoded, dict) and decoded.get("status"):
                return decoded.get("decoded_url", link)
        except Exception:
            pass
    return link


def enrich_item(item: NewsItem) -> tuple[NewsItem, str | None]:
    try:
        item.link = decode_link(item.link)
        item.source_excerpt = fetch_article_text(item.link)
        return item, None
    except Exception as exc:  # noqa: BLE001 - article extraction is best effort.
        return item, f"{item.title[:80]}: {exc}"


def enrich_articles(items: list[NewsItem], max_workers: int = 6) -> list[str]:
    errors: list[str] = []
    if not items:
        return errors
    with ThreadPoolExecutor(max_workers=min(max_workers, len(items))) as executor:
        future_map = {executor.submit(enrich_item, item): item for item in items}
        for future in as_completed(future_map):
            _item, error = future.result()
            if error:
                errors.append(error)
    return errors
