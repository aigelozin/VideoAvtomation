#!/usr/bin/env python3
"""Шаг 6: кладёт видео в собственную папку done/<название>/<название>.<ext>. Печатает новый путь.
Код выхода 1 — названия нет (папка и файл называются по исходному имени)."""
import sys, os, json, shutil
BASE = os.path.expanduser("~/VideoAutomation")
stem, video = sys.argv[1], sys.argv[2]
ext = os.path.splitext(video)[1].lower()
try: ft = json.load(open(f"{BASE}/descriptions/{stem}.json", encoding="utf-8")).get("file_title", "")
except Exception: ft = ""
name = ft or stem
folder = f"{BASE}/done/{name}"; n = 2
while os.path.exists(f"{folder}/{os.path.basename(folder)}{ext}") and \
        os.path.abspath(f"{folder}/{os.path.basename(folder)}{ext}") != os.path.abspath(video):
    folder = f"{BASE}/done/{name}_{n}"; n += 1          # то же название у другого видео
os.makedirs(folder, exist_ok=True)
dst = f"{folder}/{os.path.basename(folder)}{ext}"
if os.path.abspath(dst) != os.path.abspath(video):
    shutil.move(video, dst)
print(dst)
sys.exit(0 if ft else 1)
