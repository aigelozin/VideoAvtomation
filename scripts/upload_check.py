#!/usr/bin/env python3
"""Проверка ключей площадок без загрузки видео."""
import os, json, urllib.request
BASE = os.path.expanduser("~/VideoAutomation"); env = {}
for line in open(f"{BASE}/.env", encoding="utf-8"):
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1); env[k.strip()] = v.strip()
NP = urllib.request.build_opener(urllib.request.ProxyHandler({}))
# archive.org
if env.get("ARCHIVE_ACCESS_KEY"):
    try:
        import internetarchive as ia
        info = ia.get_user_info(env["ARCHIVE_ACCESS_KEY"], env.get("ARCHIVE_SECRET_KEY", ""))
        print("archive.org: ключи приняты, аккаунт", info.get("screenname") or info.get("username") or info)
    except Exception as e: print("archive.org: проверка не прошла —", e)
else: print("archive.org: ключей нет")
# Rutube
if env.get("RUTUBE_TOKEN") or env.get("RUTUBE_LOGIN"):
    try:
        if env.get("RUTUBE_TOKEN"): tok = env["RUTUBE_TOKEN"]
        else:
            req = urllib.request.Request("https://rutube.ru/api/accounts/token_auth/", method="POST",
                data=json.dumps({"username": env["RUTUBE_LOGIN"], "password": env.get("RUTUBE_PASSWORD","")}).encode(),
                headers={"Content-Type": "application/json"})
            tok = json.loads(NP.open(req, timeout=30).read())["token"]
        r = NP.open(urllib.request.Request("https://rutube.ru/api/video/person/?limit=1",
                    headers={"Authorization": f"Token {tok}"}), timeout=30)
        print("Rutube: вход выполнен, токен рабочий")
    except Exception as e: print("Rutube: вход не прошёл —", e)
else: print("Rutube: ключей нет")
print("YouTube:", "токен есть" if os.path.exists(f"{BASE}/yt_token.json") else
      ("есть client_secret, запусти yt_auth.py" if os.path.exists(f"{BASE}/yt_client_secret.json") else "не настроен"))
