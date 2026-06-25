from __future__ import annotations

import json
import urllib.parse
import urllib.request

from .models import NewsItem


class GeminiError(RuntimeError):
    pass


def item_payload(item: NewsItem, index: int) -> dict:
    return {
        "id": index,
        "title": item.title,
        "summary": item.summary,
        "category": item.category,
        "tags": item.tags,
        "source": item.source,
        "published_at": item.published_at.isoformat() if item.published_at else "",
    }


def build_prompt(items: list[NewsItem]) -> str:
    payload = [item_payload(item, index) for index, item in enumerate(items)]
    return (
        "You rewrite current-affairs news for an Indian banking/exam Telegram channel.\n"
        "Return ONLY valid JSON. Do not wrap in markdown.\n"
        "Rules:\n"
        "- Use simple Hinglish/Hindi, professional exam-prep tone.\n"
        "- Do not add facts that are not present in title/summary/source.\n"
        "- If details are missing, keep it generic instead of guessing.\n"
        "- Keep each field short and Telegram friendly.\n"
        "- Avoid hype, clickbait, stock tips, and unnecessary adjectives.\n"
        "- Output schema: {\"items\":[{\"id\":0,\"summary\":\"...\",\"exam_point\":\"...\",\"remember\":\"...\"}]}\n"
        "Field meanings:\n"
        "- summary: 1-2 lines explaining kya hua.\n"
        "- exam_point: exam me kis angle se pucha ja sakta hai.\n"
        "- remember: one crisp fact/keyword to remember.\n\n"
        "Items:\n"
        f"{json.dumps(payload, ensure_ascii=False)}"
    )


def extract_text(response: dict) -> str:
    try:
        parts = response["candidates"][0]["content"]["parts"]
    except (KeyError, IndexError, TypeError) as exc:
        raise GeminiError("Gemini response did not include text content") from exc
    text = "".join(part.get("text", "") for part in parts if isinstance(part, dict))
    if not text.strip():
        raise GeminiError("Gemini response text was empty")
    return text.strip()


def parse_json_text(text: str) -> dict:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise GeminiError("Gemini returned invalid JSON") from exc


def polish_items(items: list[NewsItem], api_key: str, model: str) -> None:
    if not items or not api_key:
        return

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{urllib.parse.quote(model)}:generateContent"
        f"?key={urllib.parse.quote(api_key)}"
    )
    body = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": build_prompt(items)}],
            }
        ],
        "generationConfig": {
            "temperature": 0.25,
            "responseMimeType": "application/json",
        },
    }
    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            result = json.loads(response.read().decode("utf-8"))
    except Exception as exc:  # noqa: BLE001 - keep posting alive when Gemini fails.
        raise GeminiError(f"Gemini request failed: {exc}") from exc

    parsed = parse_json_text(extract_text(result))
    polished_by_id = {
        int(item.get("id")): item for item in parsed.get("items", []) if "id" in item
    }

    for index, item in enumerate(items):
        polished = polished_by_id.get(index)
        if not polished:
            continue
        item.ai_summary = str(polished.get("summary", "")).strip()
        item.ai_exam_point = str(polished.get("exam_point", "")).strip()
        item.ai_remember = str(polished.get("remember", "")).strip()
