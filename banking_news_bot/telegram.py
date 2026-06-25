from __future__ import annotations

import json
import urllib.parse
import urllib.request


class TelegramError(RuntimeError):
    pass


def send_message(
    bot_token: str,
    chat_id: str,
    text: str,
    disable_web_page_preview: bool = True,
) -> dict:
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = urllib.parse.urlencode(
        {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": str(disable_web_page_preview).lower(),
        }
    ).encode("utf-8")
    request = urllib.request.Request(url, data=data, method="POST")
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not payload.get("ok"):
        raise TelegramError(payload.get("description", "Telegram sendMessage failed"))
    return payload
