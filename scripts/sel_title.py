#!/usr/bin/env python3
"""Шаг 4: лучшее название + дата. Пишет chosen_title/full_title/file_title в json,
печатает TITLE=... и FTITLE=... . Если ИИ недоступен — берёт первый вариант из make_meta.
Код выхода 2 = нормальных названий нет (только имя файла)."""
import sys, os, json, re, datetime
BASE = os.path.expanduser("~/VideoAutomation")
sys.path.insert(0, BASE)
stem = sys.argv[1]; video = sys.argv[2] if len(sys.argv) > 2 else ""
p = f"{BASE}/descriptions/{stem}.json"
try: d = json.load(open(p, encoding="utf-8"))
except Exception: d = {"description": "", "titles": [], "hashtags": []}
titles = [str(t).strip() for t in d.get("titles", []) if str(t).strip() and str(t).strip() != stem]
if not titles:
    print(f"НЕТ НАЗВАНИЙ в descriptions/{stem}.json — шаг 2 не сработал", file=sys.stderr); sys.exit(2)

title = titles[0]
if len(titles) > 1:
    try:
        import llm_client as L
        t = L.ask("Выбери одно самое цепляющее название. Ответь только текстом названия, "
                  "без кавычек и номеров: " + " | ".join(titles), timeout=120, max_tokens=60)
        t = t.strip().splitlines()[0].strip().strip('"«»').lstrip("0123456789. )")
        if 5 < len(t) <= 70: title = t
    except Exception as e:
        print(f"ИИ не выбрал название ({e}) — беру первый вариант", file=sys.stderr)

m = re.search(r"(20\d{2})(\d{2})(\d{2})", stem); dt = None
if m:
    try: dt = datetime.date(*map(int, m.groups()))
    except ValueError: pass
if not dt and video and os.path.exists(video): dt = datetime.date.fromtimestamp(os.path.getmtime(video))
dt = dt or datetime.date.today()

safe = re.sub(r'[\\/:*?"<>|«»,;!]+', "", title).strip().rstrip(".")
ftitle = re.sub(r"\s+", "_", safe)[:80].strip("_") + "_" + dt.strftime("%Y-%m-%d")
d.update(chosen_title=title, full_title=f"{title} | {dt:%d.%m.%Y}", date=f"{dt:%d.%m.%Y}", file_title=ftitle)
json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(f"TITLE={d['full_title']}"); print(f"FTITLE={ftitle}")
