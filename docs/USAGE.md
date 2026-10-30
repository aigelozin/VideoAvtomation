# Ежедневная работа

## Обработать видео
Положи файл (mp4, mkv, mov, avi, webm) в **`~/VideoAutomation/inbox`**. Видео обрабатываются по очереди.
Длительность на 100-минутное занятие: транскрибация ~10–15 мин, тексты ~5–10 мин.

## Где результат
```
~/VideoAutomation/done/<Название_видео_2026-07-11>/
├── <Название_видео_2026-07-11>.mp4   видео
├── <Название_видео_2026-07-11>.jpg   превью
├── статья_просмотр.html              статья для чтения в браузере
├── статья_для_WordPress.html         HTML для вставки в блог
├── статья.md                         статья для правки
├── описание.txt                      название, описание, хэштеги, варианты, английская версия, ссылки
└── транскрипт.txt
```
Рабочие копии лежат в служебных папках (`transcripts/`, `descriptions/`, `articles/`, `thumbnails/`) — они нужны
скриптам, их не удалять.

## Смотреть, что происходит
```bash
tail -f ~/VideoAutomation/logs/process.log           # ход обработки (Ctrl+C — выйти)
systemctl --user status video-pipeline                # работает ли конвейер
systemctl --user list-timers | grep video             # таймеры расписания и Telegram
```

## Команды
| Команда | Что делает |
|---|---|
| `bash ~/VideoAutomation/schedule.sh list` | что и когда выйдет, что уже вышло |
| `bash ~/VideoAutomation/schedule.sh set ИМЯ 2026-11-05 19:00` | назначить своё время (ИМЯ — исходное имя файла, из `list`) |
| `bash ~/VideoAutomation/schedule.sh now ИМЯ` | опубликовать в ближайшие 5 минут |
| `bash ~/VideoAutomation/schedule.sh unset ИМЯ` | убрать из расписания |
| `bash ~/VideoAutomation/repair.sh` | починить обработанные видео: название, папка, превью, метаданные archive.org |
| `bash ~/VideoAutomation/repair.sh --upload` | то же + догрузить на площадки то, чего там нет |
| `bash ~/VideoAutomation/telegram.sh test` | пробное сообщение в канал |
| `bash ~/VideoAutomation/telegram.sh resend 123` | отправить запись блога №123 в канал ещё раз |
| `~/VideoAutomation/.venv/bin/python3 ~/VideoAutomation/make_article.py ИМЯ` | переписать статью |
| `~/VideoAutomation/.venv/bin/python3 ~/VideoAutomation/clean_transcript.py` | почистить транскрипты |
| `~/VideoAutomation/.venv/bin/python3 ~/VideoAutomation/upload_check.py` | проверить ключи площадок |

Повторно обработать видео целиком: перенести его из `done/<папка>/` в `inbox/` (уже выполненные выгрузки
не дублируются только если имя исходника не менялось — лучше использовать `repair.sh`).

## Словари (правятся в любой момент, одна строка — одно правило)
| Файл | Для чего | Формат |
|---|---|---|
| `glossary.txt` | точное написание имён и терминов в описаниях и статьях | `Гаятри 24` |
| `replacements.txt` | исправление ошибок распознавания речи | `ГАЯ-324 => Гаятри 24` |
| `en_glossary.txt` | английские варианты для archive.org | `Олег Атма => Oleg Atma` |

## Настройки текстов (`.env`)
- `ARTICLE_MIN` / `ARTICLE_MAX` — объём статьи в словах (600 / 1000).
- `SAMPLE_WORDS` — сколько слов транскрипта читать для описания и названий (3000).
- Промпты: описание и названия — `make_meta.py` (переменная `PROMPT`), статья — `make_article.py`
  (`PLAN_TASK` — план, `STYLE` — стиль текста), английский перевод — `en_meta.py`.
