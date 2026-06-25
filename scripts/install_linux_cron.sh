#!/usr/bin/env bash
set -euo pipefail

MARKER_BEGIN="# BEGIN telegram-automation"
MARKER_END="# END telegram-automation"
DEFAULT_TIMES=("08:00" "20:00")

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-$(command -v python3)}"
TIMES=("$@")

if [ "${#TIMES[@]}" -eq 0 ]; then
  TIMES=("${DEFAULT_TIMES[@]}")
fi

if [ ! -f "$PROJECT_ROOT/.env" ]; then
  echo "Missing .env file at $PROJECT_ROOT/.env"
  echo "Create it first: cp .env.example .env && nano .env"
  exit 1
fi

mkdir -p "$PROJECT_ROOT/data"

if command -v timedatectl >/dev/null 2>&1; then
  current_tz="$(timedatectl show -p Timezone --value 2>/dev/null || true)"
  if [ "$current_tz" != "Asia/Kolkata" ]; then
    if command -v sudo >/dev/null 2>&1; then
      sudo timedatectl set-timezone Asia/Kolkata || {
        echo "Could not set timezone automatically. Cron times will use server timezone."
      }
    else
      echo "sudo not available. Cron times will use server timezone."
    fi
  fi
fi

quote() {
  printf "'%s'" "$(printf "%s" "$1" | sed "s/'/'\\\\''/g")"
}

validate_time() {
  case "$1" in
    [0-2][0-9]:[0-5][0-9])
      hour="${1%%:*}"
      [ "$hour" -le 23 ]
      ;;
    *)
      return 1
      ;;
  esac
}

RUN_CMD="cd $(quote "$PROJECT_ROOT") && /usr/bin/flock -n $(quote "$PROJECT_ROOT/data/bot.lock") $(quote "$PYTHON_BIN") -B -m banking_news_bot >> $(quote "$PROJECT_ROOT/data/bot.log") 2>&1"

tmp_file="$(mktemp)"
trap 'rm -f "$tmp_file"' EXIT

crontab -l 2>/dev/null | sed "/$MARKER_BEGIN/,/$MARKER_END/d" > "$tmp_file" || true

{
  echo "$MARKER_BEGIN"
  echo "# Runs the Telegram current-affairs bot. Times below are in the server timezone."
  for run_time in "${TIMES[@]}"; do
    if ! validate_time "$run_time"; then
      echo "Invalid time: $run_time. Use HH:MM, for example 08:00 or 20:00." >&2
      exit 1
    fi
    hour="${run_time%%:*}"
    minute="${run_time##*:}"
    hour=$((10#$hour))
    minute=$((10#$minute))
    echo "$minute $hour * * * $RUN_CMD"
  done
  echo "$MARKER_END"
} >> "$tmp_file"

crontab "$tmp_file"

echo "Cron installed for: ${TIMES[*]}"
echo "Project: $PROJECT_ROOT"
echo "Log file: $PROJECT_ROOT/data/bot.log"
echo "Check cron with: crontab -l"
echo "Check logs with: tail -f $PROJECT_ROOT/data/bot.log"
