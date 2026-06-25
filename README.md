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

`GEMINI_API_KEY` optional hai. Key set karoge to Gemini final editor ki tarah kaam karega: last 24 hours ke fresh candidates me se important items select karega, source/detail text dekh kar detailed English post banayega, aur low-value items skip karega. Agar important latest news nahi mili to bot kuch post nahi karega.

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

## Linux/VPS Automation

Oracle VPS par default automation din me 2 baar run hota hai:

- 08:00 AM IST
- 08:00 PM IST

Install:

```bash
cd ~/apps/telegram-automation
bash scripts/install_linux_cron.sh
```

Custom schedule, for example 3 baar daily:

```bash
bash scripts/install_linux_cron.sh 07:00 14:00 20:00
```

Cron har run me last 24 hours ki latest news fetch karega. Gemini enabled hai to wahi decide karega ki kaunsi news share karni hai aur kaunsi skip karni hai. Agar important latest news nahi mili to bot kuch post nahi karega. Duplicate protection `data/posted_state.json` me source IDs aur title fingerprints save karke repeat posts rokta hai.

Check automation:

```bash
crontab -l
tail -f ~/apps/telegram-automation/data/bot.log
```

## Useful Commands

Preview latest current affairs:

```powershell
py -3 -B -m banking_news_bot --dry-run --max-items 10
```

Fetch wider window for testing:

```powershell
py -3 -B -m banking_news_bot --dry-run --lookback-hours 72
```

Default lookback 24 hours hai. Production automation me ise 24 hi rakhna recommended hai, taaki week-old news post na ho.

Show source list:

```powershell
py -3 -B -m banking_news_bot --check-config
```

## Customization

- Sources add/remove: [config/sources.json](C:/Users/chinm/Documents/bankingcabot/config/sources.json)
- Duplicate post state: `data/posted_state.json`
- Ranking keywords: [banking_news_bot/filtering.py](C:/Users/chinm/Documents/bankingcabot/banking_news_bot/filtering.py)
- Telegram template: [banking_news_bot/formatter.py](C:/Users/chinm/Documents/bankingcabot/banking_news_bot/formatter.py)
- Gemini editor/selection prompt/API: [banking_news_bot/gemini.py](C:/Users/chinm/Documents/bankingcabot/banking_news_bot/gemini.py)

Duplicate protection: bot source link IDs ke saath title fingerprints bhi store karta hai in `data/posted_state.json`. Agar ek Telegram message send ho chuka ho aur later chunk fail ho jaye, sent items turant state me mark ho jaate hain so next run me repost nahi hote.

Note: "Pure internet" ko practical aur reliable banane ke liye bot official feeds plus Google News RSS search use karta hai. Isse scraping-heavy approach se better stability milti hai.
