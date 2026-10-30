#!/usr/bin/env python3
"""Ищет потолок запроса к серверу модели: шлёт запросы растущего размера
через основной порт 8080 и напрямую в дочерний процесс модели (в обход роутера)."""
import os, sys, time, json, re, subprocess, urllib.request
sys.path.insert(0, os.path.expanduser("~/VideoAutomation"))
import llm_client as L

tr = sorted([f for f in os.listdir(f"{L.BASE}/transcripts") if f.endswith(".txt") and ".clean" not in f],
            key=lambda f: os.path.getmtime(f"{L.BASE}/transcripts/{f}"))[-1]
words = open(f"{L.BASE}/transcripts/{tr}", encoding="utf-8").read().split()

def post(url, n, t=90):
    body = json.dumps({"model": L.MODEL, "max_tokens": 40,
                       "messages": [{"role": "user", "content": "Перескажи одним предложением:\n" + " ".join(words[:n])}],
                       "chat_template_kwargs": {"enable_thinking": False}}, ensure_ascii=False).encode()
    t0 = time.time()
    try:
        req = urllib.request.Request(url + "/v1/chat/completions", data=body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=t) as r: json.loads(r.read())
        return f"{n:>5} слов, {len(body)//1024:>3} КБ: OK за {time.time()-t0:.0f} с"
    except Exception as e:
        return f"{n:>5} слов, {len(body)//1024:>3} КБ: СБОЙ за {time.time()-t0:.0f} с ({e})"

print(f"Транскрипт: {tr}, {len(words)} слов\n== через роутер {L.URL} ==")
for n in (300, 800, 1500, 3000):
    r = post(L.URL, n); print(r)
    if "СБОЙ" in r: break

ss = subprocess.run(["ss", "-ltnp"], capture_output=True, text=True).stdout
ports = sorted({p for p in re.findall(r"127\.0\.0\.1:(\d+)\s.*llama-server", ss) if p != L.URL.rsplit(":", 1)[-1]})
for p in ports:
    print(f"== напрямую в модель, порт {p} ==")
    for n in (1500, 3000):
        print(post(f"http://127.0.0.1:{p}", n))
if not ports: print("Дочерний порт модели не найден (ss -ltnp)")
