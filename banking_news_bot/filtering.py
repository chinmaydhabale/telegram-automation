from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

from .models import NewsItem, Source

UTC = timezone.utc
CATEGORY_ORDER: tuple[str, ...] = (
    "Banking",
    "Economy",
    "Budget",
    "RBI Monetary Policy",
    "Government Schemes",
    "Sports",
    "Awards",
    "Appointments",
    "International Organizations",
    "Science & Technology",
    "Defence Exercises",
    "Books & Authors",
    "National & International News",
)

CATEGORY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "Banking": (
        "rbi",
        "reserve bank",
        "banking",
        "bank",
        "upi",
        "nbfc",
        "npa",
        "deposit",
        "loan",
        "kyc",
        "digital payment",
        "payment aggregator",
        "small finance bank",
        "payments bank",
    ),
    "Economy": (
        "economy",
        "gdp",
        "inflation",
        "cpi",
        "wpi",
        "fiscal deficit",
        "current account",
        "exports",
        "imports",
        "gst collection",
        "iip",
        "unemployment",
    ),
    "Budget": (
        "budget",
        "union budget",
        "finance bill",
        "income tax",
        "direct tax",
        "indirect tax",
        "customs duty",
        "capital expenditure",
        "fiscal policy",
    ),
    "RBI Monetary Policy": (
        "monetary policy",
        "mpc",
        "repo rate",
        "reverse repo",
        "standing deposit facility",
        "crr",
        "slr",
        "liquidity",
        "policy rate",
    ),
    "Government Schemes": (
        "scheme",
        "yojana",
        "mission",
        "abhiyan",
        "pm-kisan",
        "jan dhan",
        "mudra",
        "ayushman",
        "launched",
        "portal",
    ),
    "Sports": (
        "sports",
        "cricket",
        "hockey",
        "football",
        "badminton",
        "tennis",
        "olympic",
        "paralympic",
        "world cup",
        "championship",
        "tournament",
        "medal",
        "grand slam",
    ),
    "Awards": (
        "award",
        "prize",
        "honour",
        "honor",
        "conferred",
        "padma",
        "nobel",
        "booker",
        "oscar",
        "grammy",
        "bharat ratna",
    ),
    "Appointments": (
        "appointed",
        "appointment",
        "named as",
        "takes charge",
        "chairman",
        "chairperson",
        "ceo",
        "governor",
        "ambassador",
        "chief justice",
        "president",
    ),
    "International Organizations": (
        "united nations",
        " un ",
        "imf",
        "world bank",
        "wto",
        "who",
        "adb",
        "g20",
        "brics",
        "sco",
        "asean",
        "fatf",
        "unesco",
    ),
    "Science & Technology": (
        "science",
        "technology",
        "isro",
        "space",
        "satellite",
        "mission",
        "artificial intelligence",
        " ai ",
        "quantum",
        "semiconductor",
        "supercomputer",
        "digital",
    ),
    "Defence Exercises": (
        "defence exercise",
        "defense exercise",
        "military exercise",
        "joint exercise",
        "army",
        "navy",
        "air force",
        "coast guard",
        "drdo",
        "missile",
        "operation",
        "warship",
    ),
    "Books & Authors": (
        "book",
        "author",
        "authored by",
        "written by",
        "memoir",
        "autobiography",
        "biography",
        "novel",
        "launched book",
    ),
    "National & International News": (
        "national",
        "international",
        "parliament",
        "supreme court",
        "cabinet",
        "bill",
        "act",
        "summit",
        "treaty",
        "agreement",
        "election",
    ),
}

DETECTION_ORDER: tuple[str, ...] = (
    "RBI Monetary Policy",
    "Budget",
    "Government Schemes",
    "Defence Exercises",
    "International Organizations",
    "Science & Technology",
    "Books & Authors",
    "Appointments",
    "Awards",
    "Sports",
    "Banking",
    "Economy",
    "National & International News",
)

KEYWORD_SCORES: dict[str, int] = {
    "rbi": 7,
    "reserve bank": 7,
    "monetary policy": 6,
    "repo rate": 6,
    "crr": 5,
    "slr": 5,
    "upi": 6,
    "npci": 5,
    "digital payment": 5,
    "payments bank": 5,
    "banking": 5,
    "bank": 4,
    "nbfc": 5,
    "npa": 5,
    "basel": 5,
    "financial inclusion": 4,
    "deposit": 4,
    "loan": 4,
    "credit card": 4,
    "debit card": 4,
    "cbdc": 5,
    "e-rupee": 5,
    "fintech": 4,
    "kyc": 5,
    "fraud": 4,
    "cyber": 3,
    "financial stability": 4,
    "inflation": 3,
    "liquidity": 4,
    "psb": 4,
    "public sector bank": 4,
    "co-operative bank": 5,
    "cooperative bank": 5,
    "small finance bank": 5,
    "payment aggregator": 5,
    "sebi": 3,
    "pib": 2,
    "ministry of finance": 4,
    "financial services": 4,
    "economy": 4,
    "gdp": 4,
    "cpi": 3,
    "wpi": 3,
    "fiscal deficit": 4,
    "budget": 5,
    "union budget": 6,
    "finance bill": 5,
    "income tax": 4,
    "gst": 3,
    "scheme": 4,
    "yojana": 4,
    "mission": 3,
    "sports": 3,
    "championship": 3,
    "tournament": 3,
    "medal": 3,
    "award": 4,
    "prize": 4,
    "appointed": 4,
    "appointment": 4,
    "chairman": 3,
    "ceo": 3,
    "governor": 3,
    "imf": 4,
    "world bank": 4,
    "g20": 4,
    "brics": 4,
    "sco": 3,
    "asean": 3,
    "isro": 4,
    "science": 3,
    "technology": 3,
    "satellite": 4,
    "defence": 4,
    "defense": 4,
    "military exercise": 5,
    "joint exercise": 5,
    "book": 3,
    "author": 3,
    "parliament": 3,
    "supreme court": 3,
}

TAG_KEYWORDS: list[tuple[str, tuple[str, ...]]] = [
    ("RBI", ("rbi", "reserve bank", "repo rate", "crr", "slr")),
    ("Monetary Policy", ("monetary policy", "repo rate", "liquidity", "inflation")),
    ("UPI", ("upi", "npci", "digital payment", "payment aggregator")),
    ("Banking Regulation", ("banking regulation", "kyc", "basel", "nbfc", "npa")),
    ("Banking Awareness", ("bank", "deposit", "loan", "credit card", "debit card")),
    ("Finance Ministry", ("ministry of finance", "financial services", "pib")),
    ("Fintech", ("fintech", "cbdc", "e-rupee")),
]

EXCLUDE_PATTERNS = (
    "stock picks",
    "intraday",
    "buy or sell",
    "share price target",
    "multibagger",
    "ipo allotment",
    "quarterly results",
)

NON_WORD_RE = re.compile(r"[^a-z0-9]+")
KEYWORD_RE_CACHE: dict[str, re.Pattern[str]] = {}


def normalize_title(title: str) -> str:
    value = NON_WORD_RE.sub(" ", title.lower())
    return " ".join(value.split())


def canonical_domain(link: str) -> str:
    try:
        return urlparse(link).netloc.lower().removeprefix("www.")
    except ValueError:
        return ""


def has_keyword(text: str, keyword: str) -> bool:
    keyword = keyword.strip().lower()
    if not keyword:
        return False
    if " " in keyword or "-" in keyword or "&" in keyword:
        return keyword in text
    pattern = KEYWORD_RE_CACHE.get(keyword)
    if pattern is None:
        pattern = re.compile(rf"(?<![a-z0-9]){re.escape(keyword)}(?![a-z0-9])")
        KEYWORD_RE_CACHE[keyword] = pattern
    return pattern.search(text) is not None


def detect_tags(text: str, source_category: str = "") -> list[str]:
    lowered = text.lower()
    category_matches: list[str] = []
    for tag in DETECTION_ORDER:
        keywords = CATEGORY_KEYWORDS[tag]
        if any(has_keyword(lowered, keyword) for keyword in keywords):
            category_matches.append(tag)

    primary: str | None = None
    if source_category in CATEGORY_ORDER:
        if source_category == "Banking" and "RBI Monetary Policy" in category_matches:
            primary = "RBI Monetary Policy"
        else:
            primary = source_category
    elif category_matches:
        primary = category_matches[0]

    tags: list[str] = [primary] if primary else []
    for tag, keywords in TAG_KEYWORDS:
        if tag not in tags and any(has_keyword(lowered, keyword) for keyword in keywords):
            tags.append(tag)
    return tags[:4]


def primary_category(item: NewsItem) -> str:
    for tag in item.tags:
        if tag in CATEGORY_ORDER:
            return tag
    if item.category in CATEGORY_ORDER:
        return item.category
    return "National & International News"


def category_bonus(source_category: str, tags: list[str]) -> int:
    bonus = 0
    if source_category in CATEGORY_ORDER:
        bonus += 3
    bonus += min(6, len([tag for tag in tags if tag in CATEGORY_ORDER]) * 2)
    return bonus


def score_item(item: NewsItem, source_lookup: dict[str, Source]) -> int:
    title_text = item.title.lower()
    full_text = f"{item.title} {item.summary} {item.source} {item.feed_name}".lower()
    if any(pattern in full_text for pattern in EXCLUDE_PATTERNS):
        return 0

    source = source_lookup.get(item.feed_name, Source(item.feed_name, ""))
    source_weight = source.weight
    score = source_weight
    for keyword, weight in KEYWORD_SCORES.items():
        if has_keyword(title_text, keyword):
            score += weight * 2
        elif has_keyword(full_text, keyword):
            score += weight

    domain = canonical_domain(item.link)
    if domain.endswith("rbi.org.in"):
        score += 8
    elif domain.endswith("pib.gov.in") or domain.endswith("sebi.gov.in"):
        score += 4
    elif "news.google.com" in domain:
        score += 1

    item.tags = detect_tags(full_text, item.category)
    score += category_bonus(item.category, item.tags)
    item.score = score
    return score


def is_recent(item: NewsItem, lookback_hours: int) -> bool:
    if item.published_at is None:
        return True
    cutoff = datetime.now(UTC) - timedelta(hours=lookback_hours)
    return item.published_at >= cutoff


def select_items(
    items: list[NewsItem],
    sources: list[Source],
    seen_ids: set[str],
    item_id,
    max_items: int,
    min_score: int,
    lookback_hours: int,
) -> list[NewsItem]:
    source_lookup = {source.name: source for source in sources}
    candidates: list[NewsItem] = []
    fingerprints: set[str] = set()

    for item in items:
        if not is_recent(item, lookback_hours):
            continue
        if item_id(item) in seen_ids:
            continue
        score = score_item(item, source_lookup)
        if score < min_score:
            continue
        fingerprint = normalize_title(item.title)
        if fingerprint in fingerprints:
            continue
        fingerprints.add(fingerprint)
        candidates.append(item)

    candidates.sort(
        key=lambda item: (
            item.score,
            item.published_at or datetime.min.replace(tzinfo=UTC),
        ),
        reverse=True,
    )

    selected: list[NewsItem] = []
    selected_ids: set[str] = set()
    by_category: dict[str, list[NewsItem]] = {category: [] for category in CATEGORY_ORDER}
    for item in candidates:
        by_category.setdefault(primary_category(item), []).append(item)

    for category in CATEGORY_ORDER:
        if len(selected) >= max_items:
            break
        for item in by_category.get(category, []):
            identifier = item_id(item)
            if identifier not in selected_ids:
                selected.append(item)
                selected_ids.add(identifier)
                break

    for item in candidates:
        if len(selected) >= max_items:
            break
        identifier = item_id(item)
        if identifier not in selected_ids:
            selected.append(item)
            selected_ids.add(identifier)

    return selected
