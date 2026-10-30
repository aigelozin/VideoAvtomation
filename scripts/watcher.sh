#!/bin/bash
# Следит за inbox/ и по очереди отдаёт новые видео в process_one.sh (запускается сервисом video-pipeline).
set -uo pipefail
BASE="$HOME/VideoAutomation"
INBOX="$BASE/inbox"; PROC="$BASE/processing"
shopt -s nullglob nocaseglob
for f in "$INBOX"/*.{mp4,mkv,avi,mov,webm,flv}; do        # догоняем то, что лежало до запуска
  [ -e "$f" ] || continue
  mv "$f" "$PROC/" && "$BASE/process_one.sh" "$PROC/$(basename "$f")"
done
shopt -u nocaseglob
inotifywait -m -q -e close_write -e moved_to --format '%f' "$INBOX" | while read -r F; do
  case "${F,,}" in
    *.mp4|*.mkv|*.avi|*.mov|*.webm|*.flv)
      sleep 2; mv "$INBOX/$F" "$PROC/" 2>/dev/null && "$BASE/process_one.sh" "$PROC/$F" ;;
  esac
done
