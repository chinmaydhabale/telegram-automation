from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from .filtering import normalize_title
from .models import NewsItem

UTC = timezone.utc


def canonical_link(link: str) -> str:
    if not link:
        return ""
    try:
        parts = urlsplit(link)
    except ValueError:
        return link.strip().lower()
    return urlunsplit((parts.scheme, parts.netloc.lower(), parts.path, "", ""))


def strip_source_suffix(title: str) -> str:
    if " - " not in title:
        return title
    head, tail = title.rsplit(" - ", 1)
    if len(tail.split()) <= 6:
        return head
    return title


def item_fingerprint(item: NewsItem) -> str:
    return normalize_title(strip_source_suffix(item.title))


def item_id(item: NewsItem) -> str:
    base = canonical_link(item.link) or normalize_title(item.title)
    title = normalize_title(item.title)
    digest = hashlib.sha256(f"{base}|{title}".encode("utf-8")).hexdigest()
    return digest[:24]


@dataclass
class BotState:
    path: Path
    posted_ids: dict[str, str] = field(default_factory=dict)
    posted_fingerprints: dict[str, str] = field(default_factory=dict)
    last_run_at: str | None = None

    @classmethod
    def load(cls, path: Path) -> "BotState":
        if not path.exists():
            return cls(path=path)
        payload = json.loads(path.read_text(encoding="utf-8"))
        return cls(
            path=path,
            posted_ids=dict(payload.get("posted_ids", {})),
            posted_fingerprints=dict(payload.get("posted_fingerprints", {})),
            last_run_at=payload.get("last_run_at"),
        )

    def seen_ids(self) -> set[str]:
        return set(self.posted_ids)

    def seen_fingerprints(self) -> set[str]:
        return set(self.posted_fingerprints)

    def mark_posted(self, items: list[NewsItem]) -> None:
        now = datetime.now(UTC).isoformat()
        for item in items:
            self.posted_ids[item_id(item)] = now
            self.posted_fingerprints[item_fingerprint(item)] = now
        self.last_run_at = now
        self.trim()
        self.save()

    def trim(self, keep: int = 1500) -> None:
        if len(self.posted_ids) > keep:
            ordered = sorted(self.posted_ids.items(), key=lambda pair: pair[1], reverse=True)
            self.posted_ids = dict(ordered[:keep])
        if len(self.posted_fingerprints) > keep:
            ordered = sorted(
                self.posted_fingerprints.items(),
                key=lambda pair: pair[1],
                reverse=True,
            )
            self.posted_fingerprints = dict(ordered[:keep])

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "last_run_at": self.last_run_at,
            "posted_ids": self.posted_ids,
            "posted_fingerprints": self.posted_fingerprints,
        }
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
