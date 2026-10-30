# Частые проблемы

| Симптом | Причина | Решение |
|---|---|---|
| Запросы к модели зависают, маленькие проходят | zapret перехватывает локальный трафик | `interface=enp5s0` в `conf.env` zapret, перезапуск zapret |
| В транскрипте повторяется список терминов, «Субтитры создавал DimaTorzok» | Whisper «эхом» повторял подсказку на тишине (до v5) | v5 убрал подсказку; почистить старые: `clean_transcript.py` |
| Видео не переименовано, на archive.org исходное имя | не выбрано название (сбой шага 2/4) | `bash ~/VideoAutomation/repair.sh`; с v5 без названия выгрузки нет |
| Статья = сплошной транскрипт | модель продолжала текст (до v7) | v7: план → разделы, проверка на копирование; `make_article.py ИМЯ` |
| `403 access_denied` при входе в YouTube | приложение Google в режиме Testing | Audience → Publish app или добавить себя в Test users |
| Publish app неактивна | не заполнен Branding | заполнить App name, support email, developer contact |
| «Домен не авторизован» в Branding | адрес в App domain без Authorized domains | очистить поля App domain |
| Видео на YouTube «Закрытый», не открывается | непроверенный проект Google | пройти YouTube API Audit |
| Rutube: «пропуск — выгрузки на archive.org нет» | Rutube берёт видео только по ссылке | сначала настроить archive.org |
| Команда из инструкции не работает, в ней «ёлочки» | автозамена кавычек на телефоне | выключить «Умную пунктуацию» или запускать готовые .sh-файлы |
| Скачанный файл не находится | браузер добавил `(1)` к имени | запускать по маске: `bash ~/Загрузки/имя*.sh` |
| Нет места/памяти GPU | обе модели не помещаются | проверить `nvidia-smi`; Whisper сам переходит на int8 или CPU |

## Где смотреть
- Лог конвейера: `~/VideoAutomation/logs/process.log`
- Лог модели: `journalctl -u llama-server -n 50`
- Лог сервисов: `journalctl --user -u video-pipeline -n 50`, `journalctl --user -u video-publish -n 50`
- Диагностика модели: `~/VideoAutomation/.venv/bin/python3 ~/VideoAutomation/diag_llm.py`
