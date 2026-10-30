#!/bin/bash
# Расписание публикаций: list | set ИМЯ ГГГГ-ММ-ДД ЧЧ:ММ | now ИМЯ | unset ИМЯ
"$HOME/VideoAutomation/.venv/bin/python3" "$HOME/VideoAutomation/schedule.py" "$@"
