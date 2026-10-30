#!/usr/bin/env python3
"""Запускается таймером каждые 5 минут: публикует видео, чьё время пришло:
archive.org → Rutube → (YouTube, если ещё не загружен) → запись в блоге. Повторяет недоделанное до 24 ч."""
import os, sys, json, glob, subprocess, datetime as dt
BASE = os.path.expanduser("~/VideoAutomation"); PY = f"{BASE}/.venv/bin/python3"
LOG = f"{BASE}/logs/process.log"
env = {}
for line in open(f"{BASE}/.env", encoding="utf-8"):
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1); env[k.strip()] = v.strip()
def log(m):
    line = f"[{dt.datetime.now():%H:%M:%S}] 🗓 {m}"; print(line, flush=True)
    open(LOG, "a", encoding="utf-8").write(line + "\n")
need = [k for k, on in (("archive", env.get("ARCHIVE_ACCESS_KEY")),
                        ("rutube", env.get("RUTUBE_TOKEN") or env.get("RUTUBE_LOGIN")),
                        ("youtube", os.path.exists(f"{BASE}/yt_token.json")),
                        ("wordpress", env.get("WP_URL"))) if on]
now = dt.datetime.now(dt.timezone.utc)
for p in sorted(glob.glob(f"{BASE}/descriptions/*.json")):
    stem = os.path.basename(p)[:-5]
    try: d = json.load(open(p, encoding="utf-8"))
    except Exception: continue
    if not d.get("publish_at") or d.get("published"): continue
    at = dt.datetime.fromisoformat(d["publish_at"])
    if at > now: continue
    ft = d.get("file_title") or stem
    vids = [v for v in glob.glob(f"{BASE}/done/{glob.escape(ft)}/{glob.escape(ft)}.*") if not v.endswith((".jpg", ".txt"))]
    if not vids: log(f"{ft}: видео не найдено в done/ — пропуск"); continue
    log(f"ПУБЛИКАЦИЯ: {d.get('full_title', stem)}")
    e = dict(os.environ, WP_FORCE_STATUS=env.get("WP_SCHEDULED_STATUS", "publish"))
    for script, args in (("upload_all.py", [stem, vids[0]]), ("wp_publish.py", [stem]), ("collect.py", [stem])):
        if not os.path.exists(f"{BASE}/{script}"): continue
        r = subprocess.run([PY, f"{BASE}/{script}", *args], capture_output=True, text=True, env=e)
        for line in (r.stdout + r.stderr[-400:]).splitlines():
            if line.strip(): log("  " + line)
    d = json.load(open(p, encoding="utf-8")); up = d.get("uploads", {})
    missing = [k for k in need if not up.get(k)]
    if not missing or now - at > dt.timedelta(hours=24):
        d["published"] = now.isoformat(); json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        log("✓ опубликовано" + (f" (не удалось: {', '.join(missing)})" if missing else ""))
    else:
        log(f"ещё не готово: {', '.join(missing)} — повтор через 5 минут")
