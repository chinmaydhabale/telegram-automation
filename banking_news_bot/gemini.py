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
        "title": item.title[:300],
        "summary": item.summary[:1000],
        "source_excerpt": item.source_excerpt[:2200],
        "category": item.category,
        "tags": item.tags,
        "source": item.source,
        "published_at": item.published_at.isoformat() if item.published_at else "",
    }


def build_polish_prompt(items: list[NewsItem]) -> str:
    payload = [item_payload(item, index) for index, item in enumerate(items)]
    return (
        "You rewrite current-affairs news for an Indian banking/exam Telegram channel.\n"
        "Return ONLY valid JSON. Do not wrap in markdown.\n"
        "Rules:\n"
        "- Write everything in clear English only.\n"
        "- Use a professional exam-prep tone for Indian competitive exams.\n"
        "- Do not add facts that are not present in title/summary/source.\n"
        "- If details are missing, keep it generic instead of guessing.\n"
        "- Make the summary more useful than the raw feed, but still concise.\n"
        "- Keep each field Telegram friendly.\n"
        "- Avoid hype, clickbait, stock tips, and unnecessary adjectives.\n"
        "- Output schema: {\"items\":[{\"id\":0,\"summary\":\"...\",\"exam_point\":\"...\",\"remember\":\"...\"}]}\n"
        "Field meanings:\n"
        "- summary: 2-3 clear lines explaining what happened and why it matters. Include concrete numbers, rates, and percentages if present.\n"
        "- exam_point: what exam angle can be asked from this update (e.g. 'Which organization launched X?', 'Who is appointed as Y?').\n"
        "- remember: one crisp fact, key rate, percentage, or static GK details (like related organization headquarters, establishment year, or current chief/person) to memorize.\n\n"
        "Items:\n"
        f"{json.dumps(payload, ensure_ascii=False)}"
    )


def build_selection_prompt(items: list[NewsItem], max_items: int) -> str:
    payload = [item_payload(item, index) for index, item in enumerate(items)]
    return (
        "You are the editor of an Indian competitive-exam current affairs Telegram channel.\n"
        "You must decide which items are worth posting and then write the final post fields.\n"
        "Return ONLY valid JSON. Do not wrap in markdown.\n\n"
        "Selection rules:\n"
        "- Select only genuinely important current-affairs items from the provided candidates.\n"
        "- Focus heavily on banking/financial news, RBI guidelines/circulars, digital payment updates (NPCI/UPI), GDP forecasts, government schemes, and corporate/national appointments.\n"
        "- Reject old-looking, evergreen, generic listicle, entertainment gossip, stock-tip, routine local, or low-value items.\n"
        "- If no candidate is important enough, return {\"items\":[]}.\n"
        f"- Select at most {max_items} items.\n\n"
        "Writing rules:\n"
        "- Write everything in clear English only.\n"
        "- Use only the given title, feed summary, source, and source_excerpt. Do not invent details.\n"
        "- Use source_excerpt when available to make the post more detailed and useful.\n"
        "- Keep Telegram formatting concise, factual, and exam-focused.\n"
        "- Do not mention that you are using AI or that content is missing.\n\n"
        "Output schema:\n"
        "{\"items\":[{\"id\":0,\"summary\":\"...\",\"exam_point\":\"...\",\"remember\":\"...\"}]}\n\n"
        "Field requirements:\n"
        "- summary: 3-5 sentences explaining what happened, key details, and why it matters. Make sure to capture concrete numbers, rates, percentages, and committee names if present.\n"
        "- exam_point: 1-2 sentences on how this can be asked in exams (e.g. 'Which bank launched X?', 'What is the revised Repo Rate?').\n"
        "- remember: one crisp fact, key rate, percentage, or static GK details (such as related organization headquarters, establishment year, or current chief/person) to memorize.\n\n"
        "Candidates:\n"
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


def extract_json_block(text: str) -> str:
    start = text.find('{')
    if start == -1:
        return text
    brace_count = 0
    in_string = False
    escape = False
    for i in range(start, len(text)):
        char = text[i]
        if escape:
            escape = False
            continue
        if char == '\\':
            escape = True
            continue
        if char == '"':
            in_string = not in_string
            continue
        if not in_string:
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    return text[start:i+1]
    return text[start:]


def parse_json_text(text: str) -> dict:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()
    cleaned = extract_json_block(cleaned)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        import sys
        print(f"DEBUG: Gemini raw text was:\n{text}", file=sys.stderr)
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
            "parts": [{"text": build_polish_prompt(items)}],
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


def select_and_write_items(
    candidates: list[NewsItem],
    api_key: str,
    model: str,
    max_items: int,
) -> list[NewsItem]:
    if not candidates or not api_key:
        return []

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{urllib.parse.quote(model)}:generateContent"
        f"?key={urllib.parse.quote(api_key)}"
    )
    body = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": build_selection_prompt(candidates, max_items)}],
            }
        ],
        "generationConfig": {
            "temperature": 0.2,
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
        with urllib.request.urlopen(request, timeout=60) as response:
            result = json.loads(response.read().decode("utf-8"))
    except Exception as exc:  # noqa: BLE001
        raise GeminiError(f"Gemini request failed: {exc}") from exc

    parsed = parse_json_text(extract_text(result))
    selected: list[NewsItem] = []
    seen_indexes: set[int] = set()
    for polished in parsed.get("items", []):
        try:
            index = int(polished.get("id"))
        except (TypeError, ValueError):
            continue
        if index in seen_indexes or index < 0 or index >= len(candidates):
            continue
        item = candidates[index]
        item.ai_summary = str(polished.get("summary", "")).strip()
        item.ai_exam_point = str(polished.get("exam_point", "")).strip()
        item.ai_remember = str(polished.get("remember", "")).strip()
        if item.ai_summary:
            selected.append(item)
            seen_indexes.add(index)
        if len(selected) >= max_items:
            break
    return selected
