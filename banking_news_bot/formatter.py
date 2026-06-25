from __future__ import annotations

import html
from datetime import datetime, timedelta, timezone

from .models import NewsItem

UTC = timezone.utc
MAX_TELEGRAM_LENGTH = 4096
SAFE_TELEGRAM_LENGTH = 3750
IST = timezone(timedelta(hours=5, minutes=30), "IST")

CATEGORY_BADGES: dict[str, str] = {
    "Banking": "\U0001f3e6 Banking",
    "Economy": "\U0001f4b0 Economy",
    "Budget": "\U0001f4c8 Budget",
    "RBI Monetary Policy": "\U0001f4ca RBI Monetary Policy",
    "Government Schemes": "\U0001f1ee\U0001f1f3 Government Schemes",
    "Sports": "\U0001f3c6 Sports",
    "Awards": "\U0001f947 Awards",
    "Appointments": "\U0001f464 Appointments",
    "International Organizations": "\U0001f30d International Organizations",
    "Science & Technology": "\U0001f680 Science & Technology",
    "Defence Exercises": "\U0001f6e1 Defence Exercises",
    "Books & Authors": "\U0001f4da Books & Authors",
    "National & International News": "\U0001f4f0 National & International News",
}


def escape(value: str) -> str:
    return html.escape(value or "", quote=True)


def format_datetime(value: datetime | None) -> str:
    if value is None:
        return "Latest"
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(IST).strftime("%d %b %Y, %I:%M %p IST")


def shorten(value: str, limit: int) -> str:
    text = " ".join((value or "").split())
    if len(text) <= limit:
        return text
    return text[: limit - 3].rsplit(" ", 1)[0] + "..."


def summary_for(item: NewsItem) -> str:
    if item.ai_summary:
        return shorten(item.ai_summary, 320)
    summary = shorten(item.summary, 260)
    if summary:
        return summary
    return "Short official/news update. Detail source link par available hai."


def exam_point_for(item: NewsItem) -> str:
    if item.ai_exam_point:
        return shorten(item.ai_exam_point, 220)
    if item.tags:
        return ", ".join(CATEGORY_BADGES.get(tag, tag) for tag in item.tags)
    if item.category:
        return CATEGORY_BADGES.get(item.category, item.category)
    return CATEGORY_BADGES["National & International News"]


def remember_for(item: NewsItem) -> str:
    if item.ai_remember:
        return shorten(item.ai_remember, 180)
    if item.tags:
        return ", ".join(item.tags[:3])
    return item.category or "Current Affairs"


def primary_badge(item: NewsItem) -> str:
    for tag in item.tags:
        if tag in CATEGORY_BADGES:
            return CATEGORY_BADGES[tag]
    return CATEGORY_BADGES.get(item.category, CATEGORY_BADGES["National & International News"])


def render_item(index: int, item: NewsItem) -> str:
    source_line = f"{escape(item.source)} | {format_datetime(item.published_at)}"
    read_link = escape(item.link)
    link_line = f'<a href="{read_link}">Read full update</a>' if item.link else ""
    lines = [
        f"<b>{index}. {escape(shorten(item.title, 180))}</b>",
        f"<b>Category:</b> {escape(primary_badge(item))}",
        f"<b>Kya hua:</b> {escape(summary_for(item))}",
        f"<b>Exam angle:</b> {escape(exam_point_for(item))}",
        f"<b>Yaad rakhein:</b> {escape(remember_for(item))}",
        f"<b>Source:</b> {source_line}",
    ]
    if link_line:
        lines.append(link_line)
    return "\n".join(lines)


def header(now: datetime, part: int, total_parts: int) -> str:
    date_text = now.astimezone(IST).strftime("%d %b %Y")
    suffix = f" | Part {part}/{total_parts}" if total_parts > 1 else ""
    return (
        f"<b>Exam Current Affairs Digest</b>\n"
        f"Date: {date_text}{suffix}\n"
        f"Focus: Banking, Economy, RBI, Schemes, Sports, Awards, Defence, Science\n"
    )


def footer() -> str:
    return "\n#CurrentAffairs #BankingAwareness #ExamPrep #RBI #GK"


def build_messages(items: list[NewsItem]) -> list[str]:
    if not items:
        return []

    blocks = [render_item(index, item) for index, item in enumerate(items, start=1)]
    chunks: list[list[str]] = [[]]
    current_len = 0
    for block in blocks:
        extra_len = len(block) + 2
        if chunks[-1] and current_len + extra_len > SAFE_TELEGRAM_LENGTH:
            chunks.append([])
            current_len = 0
        chunks[-1].append(block)
        current_len += extra_len

    now = datetime.now(IST)
    messages: list[str] = []
    total_parts = len(chunks)
    for part, chunk in enumerate(chunks, start=1):
        message = header(now, part, total_parts) + "\n" + "\n\n".join(chunk) + footer()
        if len(message) > MAX_TELEGRAM_LENGTH:
            message = message[: MAX_TELEGRAM_LENGTH - 3] + "..."
        messages.append(message)
    return messages
