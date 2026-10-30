#!/usr/bin/env python3
"""Расписание публикаций. Слоты в .env: PUBLISH_SLOTS=пн 19:00, ср 19:00, пт 19:00 (или: ежедневно 19:00)
  schedule.py list                         — что и когда выйдет
  schedule.py assign STEM                  — занять ближайший свободный слот (делает конвейер сам)
  schedule.py set STEM 2026-11-05 19:00    — назначить своё время
  schedule.py now STEM                     — опубликовать при следующей проверке (в течение 5 минут)
  schedule.py unset STEM                   — убрать из расписания"""
import sys, os, json, glob, re, datetime as dt
from zoneinfo import ZoneInfo
BASE = os.path.expanduser("~/VideoAutomation")
env = {}
for line in open(f"{BASE}/.env", encoding="utf-8"):
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1); env[k.strip()] = v.strip()
TZ = ZoneInfo(env.get("PUBLISH_TZ", "Europe/Moscow"))
LEAD = dt.timedelta(hours=float(env.get("PUBLISH_MIN_LEAD_HOURS", "3")))
DAYS = {"пн": 0, "вт": 1, "ср": 2, "чт": 3, "пт": 4, "сб": 5, "вс": 6,
        "mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}
WD = ["пн", "вт", "ср", "чт", "пт", "сб", "вс"]

def slots():
    out = []
    for part in re.split(r"[,;]", env.get("PUBLISH_SLOTS", "")):
        m = re.match(r"\s*([а-яa-z]+)\s+(\d{1,2})[:.](\d{2})\s*$", part.strip().lower())
        if not m: continue
        day, h, mi = m.group(1)[:3], int(m.group(2)), int(m.group(3))
        days = range(7) if day in ("еже", "каж", "dai", "все") else [DAYS[day]] if day in DAYS else []
        out += [(w, h, mi) for w in days]
    return sorted(set(out))

def load(stem):
    p = f"{BASE}/descriptions/{stem}.json"; return p, json.load(open(p, encoding="utf-8"))
def save(p, d): json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
def all_items():
    for p in sorted(glob.glob(f"{BASE}/descriptions/*.json")):
        try: yield os.path.basename(p)[:-5], json.load(open(p, encoding="utf-8"))
        except Exception: pass
def fmt(iso):
    t = dt.datetime.fromisoformat(iso).astimezone(TZ); return f"{WD[t.weekday()]} {t:%d.%m.%Y %H:%M}"

def next_free():
    sl = slots()
    if not sl: raise SystemExit("PUBLISH_SLOTS в .env пуст — расписание выключено")
    taken = {dt.datetime.fromisoformat(d["publish_at"]) for _, d in all_items() if d.get("publish_at")}
    start = dt.datetime.now(TZ) + LEAD
    for i in range(0, 400):
        day = (start + dt.timedelta(days=i)).date()
        for w, h, mi in sl:
            if day.weekday() != w: continue
            t = dt.datetime(day.year, day.month, day.day, h, mi, tzinfo=TZ)
            if t >= start and t not in taken: return t
    raise SystemExit("свободный слот не найден")

cmd = sys.argv[1] if len(sys.argv) > 1 else "list"
if cmd == "assign":
    p, d = load(sys.argv[2])
    if not d.get("publish_at"):
        d["publish_at"] = next_free().isoformat(); d.pop("published", None); save(p, d)
    print(fmt(d["publish_at"]))
elif cmd == "set":
    p, d = load(sys.argv[2])
    t = dt.datetime.strptime(" ".join(sys.argv[3:5]), "%Y-%m-%d %H:%M").replace(tzinfo=TZ)
    d["publish_at"] = t.isoformat(); d.pop("published", None); save(p, d); print("назначено:", fmt(d["publish_at"]))
elif cmd == "now":
    p, d = load(sys.argv[2]); d["publish_at"] = dt.datetime.now(TZ).replace(microsecond=0).isoformat()
    d.pop("published", None); save(p, d); print("опубликуется в течение 5 минут")
elif cmd == "unset":
    p, d = load(sys.argv[2]); d.pop("publish_at", None); save(p, d); print("убрано из расписания")
else:
    print("Слоты:", env.get("PUBLISH_SLOTS") or "не заданы", "| часовой пояс:", TZ)
    rows = sorted((d["publish_at"], s, d) for s, d in all_items() if d.get("publish_at"))
    if not rows: print("В расписании пусто")
    for iso, s, d in rows:
        st = "✓ вышло" if d.get("published") else "⏳ ждёт"
        print(f"{st}  {fmt(iso)}  {d.get('full_title') or s}")
