#!/usr/bin/env python3
"""Чистит уже готовые транскрипты: python3 clean_transcript.py [файл.txt ...] (без аргументов — все)."""
import sys, os, glob
sys.path.insert(0, os.path.expanduser("~/VideoAutomation"))
from clean_lib import clean, BASE
files = sys.argv[1:] or [f for f in glob.glob(f"{BASE}/transcripts/*.txt")
                         if not f.endswith((".raw.txt", ".clean.txt"))]
for f in files:
    t = open(f, encoding="utf-8").read(); c = clean(t)
    if c != t:
        raw = f[:-4] + ".raw.txt"
        if not os.path.exists(raw): open(raw, "w", encoding="utf-8").write(t)
        open(f, "w", encoding="utf-8").write(c)
        print(f"✓ {os.path.basename(f)}: {len(t.split())} → {len(c.split())} слов")
