# Exam Current Affairs Telegram Bot

Ye bot exam-oriented current affairs collect karta hai, duplicate posts rokta hai, aur Telegram channel me clean template ke sath digest post karta hai.

Default sources me RBI, SEBI, PIB aur Google News category search feeds configured hain. Sources editable hain: [config/sources.json](C:/Users/chinm/Documents/bankingcabot/config/sources.json).

Covered categories:

- 🏦 Banking
- 💰 Economy
- 📈 Budget
- 📊 RBI Monetary Policy
- 🇮🇳 Government Schemes
- 🏆 Sports
- 🥇 Awards
- 👤 Appointments
- 🌍 International Organizations
- 🚀 Science & Technology
- 🛡 Defence Exercises
- 📚 Books & Authors
- 📰 Important National & International News

## Setup

1. Telegram bot banao:
   - Telegram me `@BotFather` open karo.
   - `/newbot` se bot create karo.
   - Bot token copy karo.
   - Bot ko apne Telegram channel me admin banao with post permission.

2. Environment file banao:

```powershell
Copy-Item .env.example .env
notepad .env
```

3. `.env` me ye values set karo:

```env
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=@your_channel_username
GEMINI_API_KEY=optional_google_ai_studio_key
```

`GEMINI_API_KEY` optional hai. Empty rahe to normal template post hoga. Key set karoge to bot raw RSS items ko Gemini se exam-ready Hinglish me polish karega: `Kya hua`, `Exam angle`, aur `Yaad rakhein`.

4. Dry run karke template preview dekho:

```powershell
py -3 -B -m banking_news_bot --dry-run
```

5. Real Telegram post:

```powershell
py -3 -B -m banking_news_bot
```

## Windows Automation

Daily 8 AM IST run ke liye:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install_windows_task.ps1 -At 08:00
```

Task Scheduler me task name `ExamCurrentAffairsBot` hoga. Time change karna ho to:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install_windows_task.ps1 -TaskName ExamCurrentAffairsBot -At 18:30
```

## Useful Commands

Preview latest current affairs:

```powershell
py -3 -B -m banking_news_bot --dry-run --max-items 10
```

Fetch wider window:

```powershell
py -3 -B -m banking_news_bot --dry-run --lookback-hours 72
```

Default lookback 168 hours hai, taaki Budget, Books, Awards aur Defence Exercises jaise low-frequency exam topics miss na hon. Duplicate state same update ko dobara post nahi hone deta.

Show source list:

```powershell
py -3 -B -m banking_news_bot --check-config
```

## Customization

- Sources add/remove: [config/sources.json](C:/Users/chinm/Documents/bankingcabot/config/sources.json)
- Duplicate post state: `data/posted_state.json`
- Ranking keywords: [banking_news_bot/filtering.py](C:/Users/chinm/Documents/bankingcabot/banking_news_bot/filtering.py)
- Telegram template: [banking_news_bot/formatter.py](C:/Users/chinm/Documents/bankingcabot/banking_news_bot/formatter.py)
- Gemini polish prompt/API: [banking_news_bot/gemini.py](C:/Users/chinm/Documents/bankingcabot/banking_news_bot/gemini.py)

Note: "Pure internet" ko practical aur reliable banane ke liye bot official feeds plus Google News RSS search use karta hai. Isse scraping-heavy approach se better stability milti hai.
