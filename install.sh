#!/bin/bash
# Установка / обновление VideoAutomation из репозитория.
#   bash install.sh           — полная установка (пакеты, Python-окружение, скрипты, сервисы)
#   bash install.sh --update  — только обновить скрипты и сервисы (настройки и словари не трогаются)
# llama.cpp и модель ставятся отдельно — см. docs/SETUP.md, раздел 2.
set -e
REPO="$(cd "$(dirname "$0")" && pwd)"; BASE="$HOME/VideoAutomation"; PY="$BASE/.venv/bin/python3"
UPDATE=0; [ "${1:-}" = "--update" ] && UPDATE=1
say(){ echo -e "\033[1;32m▶\033[0m $1"; }

mkdir -p "$BASE"/{inbox,processing,done,transcripts,descriptions,articles,thumbnails,logs}

if [ "$UPDATE" = "0" ]; then
  say "Системные пакеты (нужен пароль sudo)"
  sudo apt-get update -q && sudo apt-get install -y -q ffmpeg inotify-tools python3-venv python3-pip fonts-dejavu-core
  say "Python-окружение"
  [ -x "$PY" ] || python3 -m venv "$BASE/.venv"
  "$BASE/.venv/bin/pip" install -q --upgrade pip
  "$BASE/.venv/bin/pip" install -q faster-whisper nvidia-cublas-cu12 "nvidia-cudnn-cu12==9.*" \
      internetarchive google-api-python-client google-auth-oauthlib
  "$PY" -c "import nvidia.cublas.lib as a, nvidia.cudnn.lib as b; print(':'.join(list(m.__path__)[0] for m in (a, b)))" > "$BASE/.cuda_path"
  say "Путь к CUDA-библиотекам: $(cat "$BASE/.cuda_path")"
fi

say "Скрипты"
TS=$(date +%s)
for f in "$REPO"/scripts/*; do
  n=$(basename "$f")
  [ -f "$BASE/$n" ] && ! cmp -s "$f" "$BASE/$n" && cp "$BASE/$n" "$BASE/$n.bak.$TS"
  cp "$f" "$BASE/$n"
done
chmod +x "$BASE"/*.sh "$BASE"/*.py

say "Словари и настройки (существующие не перезаписываются)"
for f in glossary.txt replacements.txt en_glossary.txt; do [ -f "$BASE/$f" ] || cp "$REPO/config/$f" "$BASE/$f"; done
if [ ! -f "$BASE/.env" ]; then cp "$REPO/config/env.example" "$BASE/.env"; echo "  создан .env — заполни ключи: nano ~/VideoAutomation/.env"
else   # дописать новые ключи, которых ещё нет
  grep -E '^[A-Z_]+=' "$REPO/config/env.example" | while IFS= read -r l; do
    k="${l%%=*}"; grep -q "^$k=" "$BASE/.env" || { echo "$l" >> "$BASE/.env"; echo "  + $k"; }
  done
fi
chmod 600 "$BASE/.env"

say "Сервисы systemd (пользовательские)"
mkdir -p "$HOME/.config/systemd/user"
cp "$REPO"/systemd/video-*.service "$REPO"/systemd/video-*.timer "$HOME/.config/systemd/user/"
loginctl enable-linger "$USER" 2>/dev/null || true
systemctl --user daemon-reload
systemctl --user enable --now video-pipeline.service video-publish.timer video-telegram.timer
systemctl --user restart video-pipeline.service

say "Проверка"
for f in "$BASE"/*.py; do "$PY" -m py_compile "$f" || echo "✗ $f"; done
bash -n "$BASE/process_one.sh" && echo "✓ скрипты в порядке"
curl -s -m 5 --noproxy '*' http://127.0.0.1:8080/health >/dev/null && echo "✓ llama-server отвечает" || echo "⚠ llama-server не отвечает на :8080 — см. docs/SETUP.md, раздел 2"
echo; echo "Готово. Положи видео в ~/VideoAutomation/inbox — обработка начнётся сама."
