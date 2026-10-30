# Как устроен конвейер

```
inbox/ ──watcher.sh──► processing/ ──process_one.sh──────────────────────────────────────────────┐
                                     1 transcribe_gpu.py  → transcripts/<stem>.txt (+ .raw.txt)  │
                                     2 make_meta.py       → descriptions/<stem>.json             │
                                     4 sel_title.py       → chosen_title, full_title, file_title │
                                     3 make_article.py    → articles/<stem>.md/.html/.plan.json  │
                                     5 make_thumb.sh      → thumbnails/<stem>.jpg                │
                                     6 rename_video.py    → done/<file_title>/<file_title>.mp4   │
                                     7 schedule.py assign → publish_at;  upload_all.py (YouTube) │
                                       collect.py         → done/<file_title>/ все файлы ◄───────┘
таймер video-publish (5 мин): publish_due.py → upload_all.py (archive.org → Rutube) → wp_publish.py → collect.py
таймер video-telegram (5 мин): tg_publish.py → новые записи рубрики WordPress → Telegram
```

## Главный файл данных: `descriptions/<stem>.json`
`<stem>` — исходное имя видео (например `GMT20260711-100158_Recording_640x360`); все служебные файлы
называются по нему, итоговая папка — по `file_title`.

| Поле | Кто пишет | Что это |
|---|---|---|
| `description`, `titles`, `hashtags` | make_meta | описание и варианты |
| `chosen_title`, `full_title`, `date`, `file_title` | sel_title | выбранное название, «название \| дд.мм.гггг», имя папки |
| `en` | en_meta | английские title, description, subjects для archive.org |
| `publish_at`, `published` | schedule / publish_due | время слота и факт публикации |
| `uploads` | upload_all, wp_publish | ссылки: archive, archive_file, rutube, youtube, wordpress |

`uploads` делает выгрузку идемпотентной: повторный запуск не создаёт дубликатов.

## Решения и причины
- **llama.cpp вместо Ollama:** MoE-модель Qwen3.6-35B-A3B с `cpu-moe` держит в видеопамяти ~4.5 ГБ —
  рядом помещается Whisper large-v3; MTP ускоряет генерацию.
- **Выборка транскрипта равными частями** по всему видео: охват всего занятия при ограниченном контексте.
- **Статья в два этапа** (план JSON → разделы по плану): модель не видит сырой текст на этапе письма и не
  копирует его; структуру собирает код; проверка доли дословных совпадений (< 35%).
- **Whisper без initial_prompt/hotwords** и с `condition_on_previous_text=False`: подсказка «эхом» вставлялась
  в тишину и зацикливалась. Термины исправляются после распознавания (`replacements.txt`).
- **Rutube через archive.org:** API Rutube принимает видео только по URL.
- **Без названия — без выгрузки:** защита от публикации под исходным именем файла.
- **Локальные запросы без прокси** (`ProxyHandler({})`): системный прокси/zapret не должны вмешиваться в 127.0.0.1.
