#!/usr/bin/env python3
"""Черновик статьи в WordPress через REST API (пароль приложения). Включается, если в .env заданы
WP_URL, WP_USER, WP_APP_PASSWORD. WP_STATUS=draft (по умолчанию) | publish. WP_CATEGORY=id рубрики (необязательно).
В статью добавляются видео YouTube (встраивается само) и ссылки на Rutube и archive.org, обложка = превью."""
import sys, os, json, base64, urllib.request, urllib.error
BASE = os.path.expanduser("~/VideoAutomation"); stem = sys.argv[1]
env = {}
for line in open(f"{BASE}/.env", encoding="utf-8"):
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1); env[k.strip()] = v.strip()
url, user, pw = env.get("WP_URL", "").rstrip("/"), env.get("WP_USER"), env.get("WP_APP_PASSWORD", "").replace(" ", "")
if not (url and user and pw): print("WordPress: пропуск (нет WP_URL/WP_USER/WP_APP_PASSWORD в .env)"); sys.exit(0)
jp = f"{BASE}/descriptions/{stem}.json"; d = json.load(open(jp, encoding="utf-8")); up = d.setdefault("uploads", {})
if up.get("wordpress"): print(f"WordPress: уже есть → {up['wordpress']}"); sys.exit(0)
hp = f"{BASE}/articles/{stem}.html"
if not os.path.exists(hp): print("WordPress: пропуск — статьи нет"); sys.exit(0)
NP = urllib.request.build_opener(urllib.request.ProxyHandler({}))
AUTH = "Basic " + base64.b64encode(f"{user}:{pw}".encode()).decode()

def call(path, data, ctype="application/json", extra=None):
    h = {"Authorization": AUTH, "Content-Type": ctype, "User-Agent": "VideoAutomation/1.0"}; h.update(extra or {})
    req = urllib.request.Request(f"{url}/wp-json/wp/v2/{path}", data=data, method="POST", headers=h)
    with NP.open(req, timeout=120) as r: return json.loads(r.read().decode())

body = open(hp, encoding="utf-8").read()
if up.get("youtube"): body = f"{up['youtube']}\n\n" + body             # голая ссылка → WordPress встроит плеер
links = [f'<a href="{up[k]}">{n}</a>' for k, n in (("rutube", "Rutube"), ("youtube", "YouTube"), ("archive", "archive.org")) if up.get(k)]
if links: body += "\n<p>Смотреть запись занятия: " + " · ".join(links) + "</p>"
post = {"title": d.get("full_title") or d.get("chosen_title") or stem, "content": body,
        "status": os.environ.get("WP_FORCE_STATUS") or env.get("WP_STATUS", "draft"), "excerpt": d.get("description", "")[:600]}
if env.get("WP_CATEGORY", "").isdigit(): post["categories"] = [int(env["WP_CATEGORY"])]
try:
    thumb = f"{BASE}/thumbnails/{stem}.jpg"
    if os.path.exists(thumb):
        try:
            m = call("media", open(thumb, "rb").read(), "image/jpeg",
                     {"Content-Disposition": f'attachment; filename="{(d.get("date","") or stem).replace(".","-")}-preview.jpg"'})
            post["featured_media"] = m["id"]
        except Exception as e: print(f"WordPress: обложка не загрузилась ({e})")
    r = call("posts", json.dumps(post, ensure_ascii=False).encode())
    up["wordpress"] = r.get("link") or f"{url}/?p={r['id']}"
    json.dump(d, open(jp, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"WordPress: {'черновик' if post['status']=='draft' else 'запись'} создан(а) → {url}/wp-admin/post.php?post={r['id']}&action=edit")
except urllib.error.HTTPError as e:
    print(f"WordPress: ОШИБКА {e.code} {e.read().decode()[:300]}")
