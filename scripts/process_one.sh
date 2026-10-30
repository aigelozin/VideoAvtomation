#!/bin/bash
# Обработка ОДНОГО видео: 7 шагов конвейера (v11). Аргумент: путь к видео в processing/.
set -uo pipefail
BASE="$HOME/VideoAutomation"; VENV="$BASE/.venv"; LOG="$BASE/logs/process.log"
VIDEO="$1"; NAME=$(basename "$VIDEO"); STEM="${NAME%.*}"
PY="$VENV/bin/python3"
say(){ echo "[$(date '+%H:%M:%S')] $1" | tee -a "$LOG"; }
say "════════ START: $NAME ════════"
export LD_LIBRARY_PATH=$(cat "$BASE/.cuda_path" 2>/dev/null):${LD_LIBRARY_PATH:-}

say "1/7 🎙 Транскрибация..."
if "$PY" "$BASE/transcribe_gpu.py" "$VIDEO" >>"$LOG" 2>&1; then say "1/7 🎙 OK"; TOK=1; else say "1/7 🎙 ОШИБКА"; TOK=0; fi

TITLE=""; HAVE_TITLE=0
if [ "$TOK" = "1" ]; then
  say "2/7 📝 Описание, статья, варианты названий..."
  "$PY" "$BASE/make_meta.py" "$STEM" >>"$LOG" 2>&1 && say "2/7 📝 OK" || say "2/7 📝 ОШИБКА"
  say "4/7 🏆 Выбор названия и дата..."
  OUT=$("$PY" "$BASE/sel_title.py" "$STEM" "$VIDEO" 2>>"$LOG") && HAVE_TITLE=1
  TITLE=$(echo "$OUT" | grep '^TITLE=' | cut -d= -f2-)
  [ "$HAVE_TITLE" = "1" ] && say "4/7 🏆 $TITLE" || say "4/7 🏆 ОШИБКА: названия нет (см. лог выше)"
  say "3/7 📰 Статья для блога (600–1000 слов)..."
  "$PY" "$BASE/make_article.py" "$STEM" 2>>"$LOG" | while read -r line; do say "3/7 📰 $line"; done
fi

say "5/7 📸 Превью..."
bash "$BASE/make_thumb.sh" "$STEM" "$VIDEO" "${TITLE:-$STEM}" 2>>"$LOG" && say "5/7 📸 OK" || say "5/7 📸 ОШИБКА"

NEW=$("$PY" "$BASE/rename_video.py" "$STEM" "$VIDEO" 2>>"$LOG")
if [ "$HAVE_TITLE" = "1" ] && [ -f "$NEW" ]; then
  say "6/7 📁 Папка → done/$(basename "$(dirname "$NEW")")/"
  say "7/7 ⬆️ Выгрузка на площадки..."
  if grep -q "^PUBLISH_SLOTS=..*" "$BASE/.env"; then
    SLOT=$("$PY" "$BASE/schedule.py" assign "$STEM" 2>>"$LOG")
    say "7/7 🗓 Публикация назначена: $SLOT"
    UPLOAD_ONLY=YouTube "$PY" "$BASE/upload_all.py" "$STEM" "$NEW" 2>>"$LOG" | while read -r line; do say "7/7 ⬆️ $line"; done
    say "7/7 🗓 archive.org, Rutube и блог выйдут автоматически: $SLOT"
  else
    "$PY" "$BASE/upload_all.py" "$STEM" "$NEW" 2>>"$LOG" | while read -r line; do say "7/7 ⬆️ $line"; done
    "$PY" "$BASE/wp_publish.py" "$STEM" 2>>"$LOG" | while read -r line; do say "7/7 📰 $line"; done
  fi
else
  say "6/7 📁 НЕ переименовано: $(basename "${NEW:-$VIDEO}") — выгрузка отложена."
  say "    Починка: bash ~/VideoAutomation/repair.sh"
fi
[ -f "${NEW:-}" ] && "$PY" "$BASE/collect.py" "$STEM" 2>>"$LOG" | while read -r line; do say "📦 $line"; done
say "════════ DONE: $(basename "${NEW:-$NAME}") ════════"
