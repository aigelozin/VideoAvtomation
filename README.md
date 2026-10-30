# VideoAutomation — автоматическая обработка и публикация видео МОЙУ

Локальный бесплатный конвейер для записей занятий Международного Открытого Йога Университета
([openyogaclass.com](https://openyogaclass.com)). Кладёшь видео (100+ минут) в папку `~/VideoAutomation/inbox` —
дальше всё происходит само:

| Шаг | Что делает | Скрипт |
|---|---|---|
| 1 | Транскрибация речи (Whisper large-v3 на GPU) + чистка «эха» и исправление терминов | `transcribe_gpu.py`, `clean_lib.py` |
| 2 | Короткое описание (120–180 слов), 3 варианта названия, хэштеги | `make_meta.py` |
| 3 | Статья для блога 600–1000 слов: разделы, подзаголовки, диалоги, «Главное» | `make_article.py` |
| 4 | Выбор лучшего названия + дата занятия | `sel_title.py` |
| 5 | Превью 1280×720 с названием | `make_thumb.sh` |
| 6 | Своя папка видео `done/<название>/` со всеми файлами | `rename_video.py`, `collect.py` |
| 7 | Публикация по расписанию: YouTube, archive.org (на английском), Rutube, блог WordPress → Telegram-канал | `upload_all.py`, `wp_publish.py`, `publish_due.py`, `tg_publish.py` |

Всё работает на своём компьютере: модели локальные, платных API нет.

## Оборудование и стек
- Ubuntu 24.04, NVIDIA RTX 4070 12 ГБ, i7-12700, 32 ГБ ОЗУ.
- **Распознавание речи:** faster-whisper `large-v3` (float16 на GPU, ~5 ГБ видеопамяти).
- **Тексты:** Qwen3.6-35B-A3B-MTP через `llama-server` (llama.cpp, порт 8080), ~4.5 ГБ видеопамяти — обе модели помещаются одновременно.
- **Автозапуск:** пользовательские сервисы systemd (`video-pipeline`, таймеры `video-publish`, `video-telegram`).

## Быстрый старт
```bash
git clone https://github.com/aigelozin/VideoAvtomation.git
cd VideoAvtomation
bash install.sh            # первая установка
bash install.sh --update   # обновление скриптов (настройки не трогаются)
```
Затем: заполнить `~/VideoAutomation/.env` и подключить площадки — **[docs/SETUP.md](docs/SETUP.md)**.

## Документация
- **[docs/SETUP.md](docs/SETUP.md)** — установка с нуля: модель, archive.org, YouTube, Rutube, WordPress, Telegram, расписание.
- **[docs/USAGE.md](docs/USAGE.md)** — ежедневная работа: куда класть видео, где результат, команды, словари.
- **[docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)** — частые проблемы и их решения.
- **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** — как устроен конвейер, файлы данных, почему так.
- **[docs/CHANGELOG.md](docs/CHANGELOG.md)** — история версий.

## Структура репозитория
```
install.sh            установка/обновление
scripts/              всё, что копируется в ~/VideoAutomation
config/               шаблон .env, словари терминов, пример presets.ini
systemd/              сервисы и таймеры
docs/                 инструкции
```
Секреты (`.env`, `yt_token.json`, `yt_client_secret.json`) и видео в репозиторий не попадают — см. `.gitignore`.
