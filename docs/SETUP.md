# Установка с нуля и подключение площадок

> Команды удобнее копировать с компьютера. Если копируешь с телефона — выключи «Умную пунктуацию»
> (Настройки → Основные → Клавиатура), иначе кавычки превращаются в «ёлочки» и команды ломаются.

## 1. Драйвер NVIDIA и базовая установка
```bash
sudo ubuntu-drivers install      # драйвер NVIDIA, затем перезагрузка
nvidia-smi                       # должна показаться RTX 4070
git clone https://github.com/aigelozin/VideoAvtomation.git && cd VideoAvtomation
bash install.sh
```
`install.sh` ставит ffmpeg, inotify-tools, Python-окружение `~/VideoAutomation/.venv` с faster-whisper и
CUDA-библиотеками, копирует скрипты, создаёт `.env` и включает сервисы.

## 2. Локальная модель (llama.cpp + Qwen3.6)
```bash
sudo apt install -y build-essential cmake git libcurl4-openssl-dev
git clone https://github.com/ggml-org/llama.cpp ~/llama.cpp
cd ~/llama.cpp && cmake -B build -DGGML_CUDA=ON && cmake --build build -j 16 --target llama-server
```
- Модель: `~/models/Qwen3.6-35B-A3B-MTP/Qwen3.6-35B-A3B-UD-Q4_K_S.gguf`.
- Пресеты: скопировать `config/presets.ini.example` в `~/models/presets.ini` (поправить пути, если пользователь не `obeme`).
- Сервис: `systemd/llama-server.service.example` → `/etc/systemd/system/llama-server.service`, затем
  `sudo systemctl daemon-reload && sudo systemctl enable --now llama-server`.
- Проверка: `curl --noproxy '*' http://127.0.0.1:8080/health` и `~/VideoAutomation/.venv/bin/python3 ~/VideoAutomation/diag_llm.py`.

**Важно про zapret.** Если стоит `zapret_discord_youtube`, он по умолчанию перехватывает и локальный трафик —
запросы к модели больше ~16 КБ зависают. В его `conf.env` нужно указать внешний интерфейс: `interface=enp5s0`
(имя — из `ip -br link`), затем перезапустить сервис zapret.

## 3. Настройки `.env`
```bash
nano ~/VideoAutomation/.env       # Ctrl+O, Enter — сохранить; Ctrl+X — выйти
```
Пустой ключ = площадка выключена (конвейер её пропускает, это не ошибка). Шаблон с пояснениями — `config/env.example`.
Проверить ключи площадок без загрузки видео: `~/VideoAutomation/.venv/bin/python3 ~/VideoAutomation/upload_check.py`.

## 4. archive.org
1. Войти на archive.org → [archive.org/account/s3.php](https://archive.org/account/s3.php).
2. Скопировать ключи в `.env`: `ARCHIVE_ACCESS_KEY=`, `ARCHIVE_SECRET_KEY=`.

На archive.org всё публикуется **на английском**: название, описание, темы (subjects), имя файла
(`oleg-atma-bhakti-yoga_2026-06-22.mp4`). Переводит локальная модель; имена и термины — по словарю
`~/VideoAutomation/en_glossary.txt` (`русский => английский`).

## 5. YouTube
1. [console.cloud.google.com](https://console.cloud.google.com) → создать проект (например, VideoAutomation).
2. APIs & Services → Library → **YouTube Data API v3** → Enable.
3. **Google Auth Platform**:
   - **Branding:** App name, User support email, Developer contact — свою почту. Логотип не загружать.
     Поля App domain можно оставить пустыми (иначе нужен подтверждённый домен в Authorized domains).
   - **Audience:** User type = External → **Publish app** (статус *In production*). Пока статус *Testing* —
     добавить свою почту в **Test users**, но тогда вход действует только 7 дней.
   - **Clients:** Create client → тип **Desktop app** → скачать JSON.
4. Положить ключ и войти:
   ```bash
   mv ~/Загрузки/client_secret_*.json ~/VideoAutomation/yt_client_secret.json
   cd ~/VideoAutomation && .venv/bin/python3 yt_auth.py
   ```
   В браузере выбрать аккаунт **канала** → «Дополнительно» → «Перейти» → разрешить оба доступа.
   Появится `yt_token.json`.

**Ограничение YouTube:** видео, загруженные через непроверенный проект Google, блокируются в статусе «Закрытый».
Чтобы они становились публичными, один раз пройти аудит:
[YouTube API Services Audit](https://support.google.com/youtube/contact/yt_api_form) (бесплатно, от нескольких дней).
Ошибка `403 access_denied` при входе = приложение в режиме Testing, а аккаунт не в Test users.

## 6. Rutube
Rutube принимает видео **по ссылке**, поэтому сначала видео уходит на archive.org, а Rutube забирает его оттуда.
- Если вход по логину и паролю — `RUTUBE_LOGIN=`, `RUTUBE_PASSWORD=`.
- Если вход только по SMS — токен из браузера: studio.rutube.ru → F12 → вкладка Network → любой запрос к
  `rutube.ru/api` → заголовок `Authorization: Token …` → значение после `Token ` в `RUTUBE_TOKEN=` (неофициально).
- Альтернативы: перенос с YouTube в Rutube Студии (вручную) или запрос официального доступа к API в поддержке Rutube.
- `RUTUBE_HIDDEN=1` — загружать скрытым (тест), `0` — открыто.

## 7. WordPress (блог)
1. Админка → Пользователи → Профиль → **Пароли приложений** → имя `VideoAutomation` → Добавить.
2. В `.env`: `WP_URL=https://адрес-блога`, `WP_USER=логин`, `WP_APP_PASSWORD=пароль приложения`.
3. Номер рубрики: Записи → Рубрики → «Изменить» у нужной → число после `tag_ID=` в адресе → `WP_CATEGORY=`.
4. `WP_STATUS=draft` — без расписания создаются черновики; с расписанием записи публикуются в слот
   (`WP_SCHEDULED_STATUS=publish`).

Запись в блоге: статья, обложка-превью, встроенное видео YouTube, ссылки на Rutube и archive.org.

## 8. Telegram-канал
1. @BotFather → `/newbot` → получить токен → `TG_BOT_TOKEN=`.
2. Канал → Администраторы → добавить бота с правом «Публикация сообщений».
3. `TG_CHANNEL=@имя_канала`; для закрытого канала — опубликовать в нём сообщение и выполнить
   `bash ~/VideoAutomation/telegram.sh find`.
4. `TG_WP_CATEGORY=` — рубрика, из которой брать записи (пусто = `WP_CATEGORY`).
5. Проверка: `bash ~/VideoAutomation/telegram.sh test`.

Каждые 5 минут новые опубликованные записи рубрики (из конвейера и ручные) уходят в канал: обложка,
заголовок, анонс, кнопка «Читать в блоге». При первом запуске старые записи не рассылаются (кроме самой свежей).

## 9. Расписание публикаций
`PUBLISH_SLOTS=пн 19:00, ср 19:00, пт 19:00` (или `ежедневно 19:00`). Каждое новое видео занимает ближайший
свободный слот не раньше чем через `PUBLISH_MIN_LEAD_HOURS` (3 ч). Пустое значение — публиковать сразу.
- YouTube: загружается сразу, публикуется самим YouTube в слот.
- archive.org → Rutube и блог: выгружаются таймером `video-publish` в момент слота.
- Если компьютер был выключен — публикация пройдёт после включения; недоделанное повторяется до 24 часов.
