from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from .filtering import normalize_title
from .models import NewsItem


def canonical_link(link: str) -> str:
    if not link:
        return ""
    try:
        parts = urlsplit(link)
    except ValueError:
        return link.strip().lower()
    return urlunsplit((parts.scheme, parts.netloc.lower(), parts.path, "", ""))


def item_id(item: NewsItem) -> str:
    base = canonical_link(item.link) or normalize_title(item.title)
    title = normalize_title(item.title)
    digest = hashlib.sha256(f"{base}|{title}".encode("utf-8")).hexdigest()
    return digest[:24]


@dataclass
class BotState:
    path: Path
    posted_ids: dict[str, str] = field(default_factory=dict)
    last_run_at: str | None = None

    @classmethod
    def load(cls, path: Path) -> "BotState":
        if not path.exists():
            return cls(path=path)
        payload = json.loads(path.read_text(encoding="utf-8"))
        return cls(
            path=path,
            posted_ids=dict(payload.get("posted_ids", {})),
            last_run_at=payload.get("last_run_at"),
        )

    def seen_ids(self) -> set[str]:
        return set(self.posted_ids)

    def mark_posted(self, items: list[NewsItem]) -> None:
        now = datetime.now(UTC).isoformat()
        for item in items:
            self.posted_ids[item_id(item)] = now
        self.last_run_at = now
        self.trim()
        self.save()

    def trim(self, keep: int = 1500) -> None:
        if len(self.posted_ids) <= keep:
            return
        ordered = sorted(self.posted_ids.items(), key=lambda pair: pair[1], reverse=True)
        self.posted_ids = dict(ordered[:keep])

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "last_run_at": self.last_run_at,
            "posted_ids": self.posted_ids,
        }
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
