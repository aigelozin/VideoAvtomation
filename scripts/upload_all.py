#!/usr/bin/env python3
"""Шаг 7: выгрузка на archive.org → Rutube (по ссылке с archive.org) и YouTube.
Каждая площадка включается, только если заданы её ключи. Уже выполненные выгрузки
запоминаются в descriptions/<stem>.json → повторный прогон не создаёт дубликатов."""
import sys, os, json, re, time, uuid, urllib.request, urllib.error, urllib.parse

BASE = os.path.expanduser("~/VideoAutomation")
stem, video = sys.argv[1], sys.argv[2]
jpath = f"{BASE}/descriptions/{stem}.json"
try: d = json.load(open(jpath, encoding="utf-8"))
except Exception: d = {"titles": [stem], "description": "", "hashtags": []}
up = d.setdefault("uploads", {})
thumb = f"{BASE}/thumbnails/{stem}.jpg"

env = {}
if os.path.exists(f"{BASE}/.env"):
    for line in open(f"{BASE}/.env", encoding="utf-8"):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1); env[k.strip()] = v.strip()

if not d.get("full_title"):
    print("Выгрузка отложена: у видео нет выбранного названия (запусти repair.sh)", flush=True); sys.exit(0)
title = d["full_title"]
tags = [str(h).lstrip("#").strip() for h in d.get("hashtags", []) if str(h).strip()]
desc = (d.get("description", "") + "\n\n" + " ".join("#" + t.replace(" ", "_") for t in tags)).strip()
SCHOOL = env.get("CHANNEL_SIGNATURE", "Международный Открытый Йога Университет · openyogaclass.com")
desc_full = desc + "\n\n" + SCHOOL

def save():
    json.dump(d, open(jpath, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

def say(m): print(m, flush=True)

NOPROXY = urllib.request.build_opener(urllib.request.ProxyHandler({}))

# ───────────────────────── archive.org ─────────────────────────
TR = dict(zip("абвгдеёжзийклмнопрстуфхцчшщъыьэюя",
              ["a","b","v","g","d","e","e","zh","z","i","y","k","l","m","n","o","p","r","s","t",
               "u","f","h","ts","ch","sh","sch","","y","","e","yu","ya"]))
def slug(s):
    s = "".join(TR.get(c, c) for c in s.lower())
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")[:60]

def do_archive():
    if up.get("archive"): say(f"archive.org: уже выгружено → {up['archive']}"); return
    ak, sk = env.get("ARCHIVE_ACCESS_KEY"), env.get("ARCHIVE_SECRET_KEY")
    if not (ak and sk): say("archive.org: пропуск (нет ARCHIVE_ACCESS_KEY/SECRET_KEY в .env)"); return
    import internetarchive as ia
    sys.path.insert(0, BASE); from en_meta import ensure_en
    try: en = ensure_en(d); save()
    except Exception as e:
        say(f"archive.org: отложено — {e}. Повтор: bash ~/VideoAutomation/repair.sh --upload"); return
    if d.get("date"):
        dd, mm, yy = d["date"].split("."); iso = f"{yy}-{mm}-{dd}"
    else: iso = (d.get("file_title", "")[-10:] or time.strftime("%Y-%m-%d"))
    s_en = slug(en["title"]).strip("-") or "yoga-class"
    base = re.sub(r"-+", "-", f"{env.get('ARCHIVE_PREFIX', 'moyu')}-{iso}-{s_en}").strip("-")[:90]
    ident, n = base, 2
    while ia.get_item(ident).exists: ident, n = f"{base}-{n}", n + 1
    vname = f"{s_en}_{iso}{os.path.splitext(video)[1].lower()}"          # английское имя файла
    files = {vname: video}
    if os.path.exists(thumb): files["__ia_thumb.jpg"] = thumb
    desc_en = en["description"] + "\n\n" + env.get("ARCHIVE_SIGNATURE",
              "International Open Yoga University · openyogaclass.com") + "\n\nLanguage of the video: Russian."
    md = {"title": f"{en['title']} | {iso}", "description": desc_en.replace("\n", "<br>"), "mediatype": "movies",
          "collection": env.get("ARCHIVE_COLLECTION", "opensource_movies"), "language": "rus",
          "subject": en["subjects"], "date": iso,
          "creator": env.get("ARCHIVE_CREATOR_EN", "International Open Yoga University")}
    say(f"archive.org: загружаю как {ident} ({en['title']}) …")
    r = ia.upload(ident, files=files, metadata=md, access_key=ak, secret_key=sk, retries=5, retries_sleep=20)
    if all(x.status_code == 200 for x in r):
        up["archive"] = f"https://archive.org/details/{ident}"
        up["archive_file"] = f"https://archive.org/download/{ident}/{urllib.parse.quote(vname)}"
        save(); say(f"archive.org: OK → {up['archive']}")
    else:
        say(f"archive.org: ОШИБКА {[x.status_code for x in r]}")

# ───────────────────────── Rutube ─────────────────────────
def rt_call(method, path, token=None, payload=None, timeout=60):
    data = json.dumps(payload, ensure_ascii=False).encode() if payload is not None else None
    h = {"Content-Type": "application/json", "Accept": "application/json"}
    if token: h["Authorization"] = f"Token {token}"
    req = urllib.request.Request("https://rutube.ru/" + path, data=data, method=method, headers=h)
    with NOPROXY.open(req, timeout=timeout) as r:
        return json.loads(r.read().decode() or "{}")

def do_rutube():
    if up.get("rutube"): say(f"Rutube: уже выгружено → {up['rutube']}"); return
    token = env.get("RUTUBE_TOKEN")
    if not token and env.get("RUTUBE_LOGIN") and env.get("RUTUBE_PASSWORD"):
        try: token = rt_call("POST", "api/accounts/token_auth/",
                             payload={"username": env["RUTUBE_LOGIN"], "password": env["RUTUBE_PASSWORD"]})["token"]
        except Exception as e: say(f"Rutube: не удалось войти ({e})"); return
    if not token: say("Rutube: пропуск (нет RUTUBE_TOKEN или RUTUBE_LOGIN/PASSWORD в .env)"); return
    src = up.get("archive_file")
    if not src: say("Rutube: пропуск — Rutube принимает видео только по ссылке, а выгрузки на archive.org нет"); return
    # ждём, пока archive.org начнёт отдавать файл (обычно 1–10 минут)
    for i in range(30):
        try:
            with NOPROXY.open(urllib.request.Request(src, method="HEAD"), timeout=30) as r:
                if r.status == 200: break
        except Exception: pass
        time.sleep(30)
    else:
        say("Rutube: файл на archive.org ещё недоступен — повтор при следующем прогоне"); return
    try:
        res = rt_call("POST", "api/video/", token, {
            "url": src, "title": title[:100], "description": desc_full[:5000],
            "is_hidden": env.get("RUTUBE_HIDDEN", "1") in ("1", "true", "True"),
            "category_id": int(env.get("RUTUBE_CATEGORY", "13"))}, timeout=120)
    except urllib.error.HTTPError as e:
        say(f"Rutube: ОШИБКА {e.code} {e.read().decode()[:300]}"); return
    vid = res.get("video_id") or res.get("id")
    if not vid: say(f"Rutube: неожиданный ответ {str(res)[:300]}"); return
    up["rutube"] = f"https://rutube.ru/video/{vid}/"; save()
    say(f"Rutube: принято в обработку → {up['rutube']}")
    if os.path.exists(thumb):          # превью (multipart, поле file)
        try:
            b = uuid.uuid4().hex
            body = (f"--{b}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"thumb.jpg\"\r\n"
                    f"Content-Type: image/jpeg\r\n\r\n").encode() + open(thumb, "rb").read() + f"\r\n--{b}--\r\n".encode()
            req = urllib.request.Request(f"https://rutube.ru/api/video/{vid}/thumbnail/", data=body, method="POST",
                    headers={"Authorization": f"Token {token}", "Content-Type": f"multipart/form-data; boundary={b}"})
            NOPROXY.open(req, timeout=60); say("Rutube: превью загружено")
        except Exception as e: say(f"Rutube: превью не загрузилось ({e}) — можно добавить вручную")

# ───────────────────────── YouTube ─────────────────────────
def yt_status():
    st = {"privacyStatus": env.get("YT_PRIVACY", "private"), "selfDeclaredMadeForKids": False}
    pa = d.get("publish_at")
    if pa:
        import datetime as _dt
        t = _dt.datetime.fromisoformat(pa).astimezone(_dt.timezone.utc)
        if t > _dt.datetime.now(_dt.timezone.utc) + _dt.timedelta(minutes=20):   # YouTube опубликует сам
            st = {"privacyStatus": "private", "publishAt": t.strftime("%Y-%m-%dT%H:%M:%SZ"), "selfDeclaredMadeForKids": False}
        else:
            st["privacyStatus"] = env.get("YT_SCHEDULED_PRIVACY", "public")
    return st

def do_youtube():
    if up.get("youtube"): say(f"YouTube: уже выгружено → {up['youtube']}"); return
    tok = f"{BASE}/yt_token.json"
    if not os.path.exists(tok): say("YouTube: пропуск (нет yt_token.json — запусти один раз yt_auth.py)"); return
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    SC = ["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube"]
    creds = Credentials.from_authorized_user_file(tok, SC)
    if not creds.valid:
        creds.refresh(Request()); open(tok, "w").write(creds.to_json())
    yt = build("youtube", "v3", credentials=creds, cache_discovery=False)
    clean = lambda s: s.replace("<", "‹").replace(">", "›")      # YouTube не принимает < >
    body = {"snippet": {"title": clean(title)[:100], "description": clean(desc_full)[:4900],
                        "tags": tags[:15], "categoryId": env.get("YT_CATEGORY", "27"),   # 27 = Образование
                        "defaultLanguage": "ru", "defaultAudioLanguage": "ru"},
            "status": yt_status()}
    say("YouTube: загружаю …")
    req = yt.videos().insert(part="snippet,status", body=body,
                             media_body=MediaFileUpload(video, chunksize=16 * 1024 * 1024, resumable=True))
    resp, last = None, -1
    while resp is None:
        st, resp = req.next_chunk()
        if st and int(st.progress() * 10) != last:
            last = int(st.progress() * 10); say(f"YouTube: {last * 10}%")
    vid = resp["id"]; up["youtube"] = f"https://youtu.be/{vid}"; save()
    say(f"YouTube: OK → {up['youtube']} ({body['status']['privacyStatus']})")
    if os.path.exists(thumb):
        try: yt.thumbnails().set(videoId=vid, media_body=MediaFileUpload(thumb)).execute(); say("YouTube: превью загружено")
        except Exception as e: say(f"YouTube: превью не загрузилось ({str(e)[:150]}) — для своих превью канал должен быть подтверждён по телефону")

ONLY = [x.strip() for x in os.environ.get("UPLOAD_ONLY", "").split(",") if x.strip()]
for name, fn in (("archive.org", do_archive), ("Rutube", do_rutube), ("YouTube", do_youtube)):
    if ONLY and name not in ONLY: continue
    try: fn()
    except Exception as e: say(f"{name}: ОШИБКА {str(e)[:300]}")
