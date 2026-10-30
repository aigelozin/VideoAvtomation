#!/bin/bash
# Починка обработанных видео. --upload — заодно догрузить на площадки то, чего там нет.
"$HOME/VideoAutomation/.venv/bin/python3" "$HOME/VideoAutomation/repair.py" "$@"
