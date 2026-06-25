from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class Source:
    name: str
    url: str
    category: str = "News"
    weight: int = 0
    enabled: bool = True


@dataclass
class NewsItem:
    title: str
    link: str
    source: str
    feed_name: str
    category: str
    summary: str = ""
    source_excerpt: str = ""
    published_at: datetime | None = None
    score: int = 0
    tags: list[str] = field(default_factory=list)
    ai_summary: str = ""
    ai_exam_point: str = ""
    ai_remember: str = ""
