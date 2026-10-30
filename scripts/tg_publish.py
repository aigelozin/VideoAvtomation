#!/usr/bin/env python3
"""Новые записи из рубрики WordPress → Telegram-канал (картинка + заголовок + анонс + кнопка «Читать в блоге»).
  tg_publish.py          — проверить рубрику и отправить новое (запускается таймером каждые 5 минут)
  tg_publish.py find     — показать id каналов, где бот админ (сначала опубликуй что-нибудь в канале)
  tg_publish.py test     — отправить в канал пробное сообщение
  tg_publish.py resend ID — отправить запись блога с номером ID ещё раз
.env: TG_BOT_TOKEN, TG_CHANNEL (@имя_канала или -100…), TG_WP_CATEGORY (по умолчанию = WP_CATEGORY)"""
import sys, os, json, re, html, urllib.request, urllib.parse, urllib.error
BASE = os.path.expanduser("~/VideoAutomation"); STATE = f"{BASE}/logs/telegram_sent.json"
env = {}
for line in open(f"{BASE}/.env", encoding="utf-8"):
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1); env[k.strip()] = v.strip()
TOKEN, CHAN = env.get("TG_BOT_TOKEN", ""), env.get("TG_CHANNEL", "")
API = env.get("TG_API_URL", "https://api.telegram.org").rstrip("/")
WP = env.get("WP_URL", "").rstrip("/"); CAT = env.get("TG_WP_CATEGORY") or env.get("WP_CATEGORY", "")
cmd = sys.argv[1] if len(sys.argv) > 1 else "run"

def tg(method, **params):
    data = json.dumps(params, ensure_ascii=False).encode()
    req = urllib.request.Request(f"{API}/bot{TOKEN}/{method}", data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r: return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return json.loads(e.read().decode() or "{}") or {"ok": False, "description": str(e)}

if not TOKEN: print("Telegram: пропуск (нет TG_BOT_TOKEN в .env)"); sys.exit(0)
if cmd == "find":
    seen = {}
    for u in tg("getUpdates").get("result", []):
        c = (u.get("channel_post") or u.get("my_chat_member") or u.get("message") or {}).get("chat", {})
        if c: seen[c["id"]] = f"{c.get('title') or c.get('username')} ({c.get('type')})"
    print("\n".join(f"TG_CHANNEL={k}   ← {v}" for k, v in seen.items()) or
          "Ничего не найдено: добавь бота админом в канал и опубликуй там любое сообщение, потом повтори")
    sys.exit(0)
if not CHAN: print("Telegram: пропуск (нет TG_CHANNEL в .env)"); sys.exit(0)
if cmd == "test":
    r = tg("sendMessage", chat_id=CHAN, text="✅ Бот VideoAutomation подключён к каналу")
    print("✓ отправлено" if r.get("ok") else f"✗ {r.get('description')}"); sys.exit(0)
if not (WP and CAT): print("Telegram: пропуск (нет WP_URL или номера рубрики TG_WP_CATEGORY/WP_CATEGORY)"); sys.exit(0)

def wp_posts(extra=""):
    url = f"{WP}/wp-json/wp/v2/posts?categories={CAT}&per_page=10&orderby=date&order=desc&_embed=1{extra}"
    req = urllib.request.Request(url, headers={"User-Agent": "VideoAutomation/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r: return json.loads(r.read().decode())

def text_of(h): return html.unescape(re.sub(r"<[^>]+>", " ", h or "")).replace("[…]", "").replace("[&hellip;]", "").strip()

def send(p):
    title = text_of(p["title"]["rendered"])
    teaser = re.sub(r"\s+", " ", text_of(p.get("excerpt", {}).get("rendered", "")))
    link = p["link"]
    head = f"<b>{html.escape(title)}</b>\n\n"; tail = f"\n\n<a href=\"{html.escape(link)}\">Читать статью →</a>"
    room = 1000 - len(head) - len(tail)
    if len(teaser) > room: teaser = teaser[:room].rsplit(" ", 1)[0] + "…"
    cap = head + html.escape(teaser) + tail
    kb = {"inline_keyboard": [[{"text": "📖 Читать в блоге", "url": link}]]}
    img = None
    try: img = p["_embedded"]["wp:featuredmedia"][0]["source_url"]
    except Exception: pass
    if img:
        r = tg("sendPhoto", chat_id=CHAN, photo=img, caption=cap, parse_mode="HTML", reply_markup=kb)
        if r.get("ok"): return r
    return tg("sendMessage", chat_id=CHAN, text=cap, parse_mode="HTML", reply_markup=kb,
              link_preview_options={"url": link, "prefer_large_media": True})

state = json.load(open(STATE)) if os.path.exists(STATE) else None
if cmd == "resend":
    p = json.loads(urllib.request.urlopen(urllib.request.Request(f"{WP}/wp-json/wp/v2/posts/{sys.argv[2]}?_embed=1",
        headers={"User-Agent": "VideoAutomation/1.0"}), timeout=60).read().decode())
    r = send(p); print("✓ отправлено" if r.get("ok") else f"✗ {r.get('description')}"); sys.exit(0)
posts = wp_posts()
if state is None:            # первый запуск: старые записи не рассылаем, запоминаем
    state = {"sent": [p["id"] for p in posts]}
    if env.get("TG_SEND_LAST", "1") == "1" and posts: state["sent"].remove(posts[0]["id"])   # самую свежую — отправим для проверки
    print(f"Telegram: первый запуск — {len(state['sent'])} старых записей пропущено")
os.makedirs(os.path.dirname(STATE), exist_ok=True)
for p in reversed(posts):    # от старых к новым
    if p["id"] in state["sent"] or p.get("status") != "publish": continue
    r = send(p)
    if r.get("ok"):
        state["sent"].append(p["id"]); print(f"Telegram: ✓ «{text_of(p['title']['rendered'])}» отправлено в канал")
    else:
        print(f"Telegram: ✗ запись {p['id']}: {r.get('description')}")
    json.dump(state, open(STATE, "w"), ensure_ascii=False)
json.dump(state, open(STATE, "w"), ensure_ascii=False)
