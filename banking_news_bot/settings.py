from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

from .models import Source


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _parse_env_line(line: str) -> tuple[str, str] | None:
    stripped = line.strip()
    if not stripped or stripped.startswith("#") or "=" not in stripped:
        return None
    key, value = stripped.split("=", 1)
    key = key.strip()
    value = value.strip().strip('"').strip("'")
    return key, value


def load_dotenv(path: Path | None = None) -> None:
    env_path = path or PROJECT_ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        parsed = _parse_env_line(line)
        if parsed is None:
            continue
        key, value = parsed
        os.environ.setdefault(key, value)


def resolve_path(value: str, default: str) -> Path:
    raw = value or default
    path = Path(raw)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    try:
        return int(value)
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str
    telegram_chat_id: str
    max_items: int
    lookback_hours: int
    min_score: int
    dry_run: bool
    disable_web_page_preview: bool
    sources_file: Path
    state_file: Path


def load_settings() -> Settings:
    load_dotenv()
    return Settings(
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", "").strip(),
        telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID", "").strip(),
        max_items=env_int("MAX_ITEMS", 7),
        lookback_hours=env_int("LOOKBACK_HOURS", 168),
        min_score=env_int("MIN_SCORE", 4),
        dry_run=env_bool("DRY_RUN", False),
        disable_web_page_preview=env_bool("DISABLE_WEB_PAGE_PREVIEW", True),
        sources_file=resolve_path(os.getenv("SOURCES_FILE", ""), "config/sources.json"),
        state_file=resolve_path(os.getenv("STATE_FILE", ""), "data/posted_state.json"),
    )


def load_sources(path: Path) -> list[Source]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    sources: list[Source] = []
    for item in payload:
        sources.append(
            Source(
                name=item["name"],
                url=item["url"],
                category=item.get("category", "News"),
                weight=int(item.get("weight", 0)),
                enabled=bool(item.get("enabled", True)),
            )
        )
    return [source for source in sources if source.enabled]
