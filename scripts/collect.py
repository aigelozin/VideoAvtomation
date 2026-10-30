#!/usr/bin/env python3
"""Собирает всё по видео в его папку done/<название>/: превью, статью, описание, транскрипт.
Можно запускать повторно — файлы обновятся. Запуск: collect.py STEM"""
import sys, os, json, glob, shutil
BASE = os.path.expanduser("~/VideoAutomation"); stem = sys.argv[1]
d = json.load(open(f"{BASE}/descriptions/{stem}.json", encoding="utf-8"))
ft = d.get("file_title") or stem
vids = [p for p in glob.glob(f"{BASE}/done/{glob.escape(ft)}*/*") if os.path.splitext(p)[0].endswith(os.path.basename(os.path.dirname(p)))
        and p.lower().endswith((".mp4", ".mkv", ".mov", ".avi", ".webm", ".flv"))]
if not vids: print(f"Папка: видео {ft} не найдено в done/"); sys.exit(1)
folder = os.path.dirname(sorted(vids)[0]); name = os.path.basename(folder)
copies = {f"{BASE}/thumbnails/{stem}.jpg": f"{name}.jpg",
          f"{BASE}/articles/{stem}.md": "статья.md",
          f"{BASE}/articles/{stem}.html": "статья_для_WordPress.html",
          f"{BASE}/articles/{stem}.preview.html": "статья_просмотр.html",
          f"{BASE}/transcripts/{stem}.txt": "транскрипт.txt"}
got = []
for src, dst in copies.items():
    if os.path.exists(src): shutil.copy2(src, f"{folder}/{dst}"); got.append(dst)
up = d.get("uploads", {})
names = {"youtube": "YouTube", "rutube": "Rutube", "archive": "archive.org", "wordpress": "Блог"}
txt = [d.get("full_title", ""), "", d.get("description", ""), "",
       " ".join(str(h) for h in d.get("hashtags", [])), ""]
if d.get("titles"): txt += ["Варианты названия:"] + [f"- {t}" for t in d["titles"]] + [""]
en = d.get("en") or {}
if en: txt += ["English (archive.org):", en.get("title", ""), en.get("description", ""), "Subjects: " + ", ".join(en.get("subjects", [])), ""]
if up: txt += ["Ссылки:"] + [f"{names.get(k, k)}: {v}" for k, v in up.items() if k in names]
open(f"{folder}/описание.txt", "w", encoding="utf-8").write("\n".join(txt).strip() + "\n"); got.append("описание.txt")
print(f"Папка {name}/: " + ", ".join(got))
