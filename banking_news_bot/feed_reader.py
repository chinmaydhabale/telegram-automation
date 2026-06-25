from __future__ import annotations

import html
import re
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime

from .models import NewsItem, Source

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

TAG_RE = re.compile(r"<[^>]+>")
SPACE_RE = re.compile(r"\s+")


def fetch_url(url: str, timeout: int = 25) -> bytes:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/rss+xml, application/xml, text/xml, */*",
            "Accept-Language": "en-IN,en;q=0.9",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()


def child_text(element: ET.Element, *names: str) -> str:
    wanted = {name.lower() for name in names}
    for child in list(element):
        if local_name(child.tag) in wanted and child.text:
            return normalize_text(child.text)
    return ""


def child_attr(element: ET.Element, name: str, attr: str) -> str:
    for child in list(element):
        if local_name(child.tag) == name.lower():
            return child.attrib.get(attr, "").strip()
    return ""


def normalize_text(value: str) -> str:
    value = html.unescape(value or "")
    value = TAG_RE.sub(" ", value)
    return SPACE_RE.sub(" ", value).strip()


def parse_date(value: str) -> datetime | None:
    value = (value or "").strip()
    if not value:
        return None
    try:
        dt = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def parse_rss_item(source: Source, element: ET.Element) -> NewsItem | None:
    title = child_text(element, "title")
    link = child_text(element, "link")
    if not link:
        link = child_text(element, "guid", "id")
    summary = child_text(element, "description", "summary", "encoded")
    source_name = child_text(element, "source") or source.name
    published_at = parse_date(
        child_text(element, "pubDate", "published", "updated", "date")
    )
    if not title:
        return None
    return NewsItem(
        title=title,
        link=link,
        source=source_name,
        feed_name=source.name,
        category=source.category,
        summary=summary,
        published_at=published_at,
    )


def parse_atom_entry(source: Source, element: ET.Element) -> NewsItem | None:
    title = child_text(element, "title")
    link = child_attr(element, "link", "href") or child_text(element, "link")
    summary = child_text(element, "summary", "content")
    published_at = parse_date(child_text(element, "published", "updated"))
    source_name = child_text(element, "source") or source.name
    if not title:
        return None
    return NewsItem(
        title=title,
        link=link,
        source=source_name,
        feed_name=source.name,
        category=source.category,
        summary=summary,
        published_at=published_at,
    )


def parse_feed(source: Source, payload: bytes) -> list[NewsItem]:
    root = ET.fromstring(payload)
    items: list[NewsItem] = []
    for element in root.iter():
        name = local_name(element.tag)
        if name == "item":
            item = parse_rss_item(source, element)
        elif name == "entry":
            item = parse_atom_entry(source, element)
        else:
            continue
        if item is not None:
            items.append(item)
    return items


def fetch_source(source: Source) -> tuple[list[NewsItem], str | None]:
    try:
        return parse_feed(source, fetch_url(source.url)), None
    except Exception as exc:  # noqa: BLE001 - feed failures should not stop the digest.
        return [], f"{source.name}: {exc}"


def fetch_all(sources: list[Source]) -> tuple[list[NewsItem], list[str]]:
    items: list[NewsItem] = []
    errors: list[str] = []
    max_workers = min(8, max(1, len(sources)))
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {executor.submit(fetch_source, source): source for source in sources}
        for future in as_completed(future_map):
            fetched, error = future.result()
            items.extend(fetched)
            if error:
                errors.append(error)
    return items, errors
