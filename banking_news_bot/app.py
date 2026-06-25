from __future__ import annotations

import argparse
import sys

from .feed_reader import fetch_all
from .filtering import select_items
from .formatter import build_messages
from .settings import load_settings, load_sources
from .state import BotState, item_id
from .telegram import send_message


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Collect banking current affairs and post a Telegram digest."
    )
    parser.add_argument("--dry-run", action="store_true", help="Print Telegram message only.")
    parser.add_argument("--max-items", type=int, help="Maximum news items to include.")
    parser.add_argument("--lookback-hours", type=int, help="Only include recent items.")
    parser.add_argument("--min-score", type=int, help="Minimum relevance score.")
    parser.add_argument("--check-config", action="store_true", help="Print enabled sources.")
    return parser.parse_args(argv)


def print_dry_run(messages: list[str]) -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    for index, message in enumerate(messages, start=1):
        print(f"\n--- TELEGRAM MESSAGE {index} ---\n")
        print(message)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    settings = load_settings()
    dry_run = settings.dry_run or args.dry_run
    max_items = args.max_items or settings.max_items
    lookback_hours = args.lookback_hours or settings.lookback_hours
    min_score = args.min_score or settings.min_score

    sources = load_sources(settings.sources_file)
    if args.check_config:
        print(f"Enabled sources: {len(sources)}")
        for source in sources:
            print(f"- {source.name} [{source.category}] weight={source.weight}")
        return 0

    print(f"Fetching {len(sources)} sources...")
    fetched_items, errors = fetch_all(sources)
    for error in errors:
        print(f"Warning: {error}", file=sys.stderr)

    state = BotState.load(settings.state_file)
    selected_items = select_items(
        fetched_items,
        sources,
        state.seen_ids(),
        item_id,
        max_items=max_items,
        min_score=min_score,
        lookback_hours=lookback_hours,
    )

    if not selected_items:
        print("No new banking current-affairs items matched the filters.")
        return 0

    messages = build_messages(selected_items)
    if dry_run:
        print_dry_run(messages)
        return 0

    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        print(
            "TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID are required. "
            "Set them in .env or run with --dry-run.",
            file=sys.stderr,
        )
        return 2

    for message in messages:
        send_message(
            settings.telegram_bot_token,
            settings.telegram_chat_id,
            message,
            disable_web_page_preview=settings.disable_web_page_preview,
        )

    state.mark_posted(selected_items)
    print(f"Posted {len(selected_items)} items in {len(messages)} Telegram message(s).")
    return 0
