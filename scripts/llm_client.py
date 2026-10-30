#!/usr/bin/env python3
"""Единый клиент LLM: Ollama (/api/generate) или llama.cpp (OpenAI /v1/chat/completions).
Настройки в ~/VideoAutomation/.env: LLM_BACKEND, LLM_URL, LLM_MODEL."""
import os, json, re, urllib.request

BASE = os.path.expanduser("~/VideoAutomation")

def load_env():
    env = {}
    p = f"{BASE}/.env"
    if os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1); env[k.strip()] = v.strip()
    return env

ENV = load_env()
BACKEND = ENV.get("LLM_BACKEND", "ollama")            # ollama | llamacpp
URL     = ENV.get("LLM_URL", "http://127.0.0.1:11434" if BACKEND == "ollama" else "http://127.0.0.1:8080")
MODEL   = ENV.get("LLM_MODEL", "qwen2.5:7b")
CTX     = int(ENV.get("LLM_CTX", "4096" if BACKEND == "ollama" else "32768"))

def _post(path, payload, timeout):
    req = urllib.request.Request(URL + path, data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))

def ask(prompt, as_json=False, timeout=600, max_tokens=900):
    if BACKEND == "llamacpp":
        body = {"model": MODEL, "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.6, "max_tokens": max_tokens,
                # Qwen3.x: выключаем режим размышлений, иначе <think> ломает JSON
                "chat_template_kwargs": {"enable_thinking": False}}
        if as_json: body["response_format"] = {"type": "json_object"}
        txt = _post("/v1/chat/completions", body, timeout)["choices"][0]["message"]["content"]
    else:
        body = {"model": MODEL, "prompt": prompt, "stream": False, "keep_alive": "30m",
                "options": {"num_ctx": CTX, "num_gpu": 99, "num_predict": max_tokens}}
        if as_json: body["format"] = "json"
        txt = _post("/api/generate", body, timeout).get("response", "")
    return re.sub(r"<think>.*?</think>", "", txt, flags=re.DOTALL).strip()

def warmup():
    for _ in range(3):
        try: ask("ok", timeout=120, max_tokens=4); return True
        except Exception: pass
    return False

def parse_json(txt):
    txt = re.sub(r"^```(?:json)?\s*", "", txt.strip()); txt = re.sub(r"\s*```$", "", txt)
    m = re.search(r"\{.*\}", txt, re.DOTALL)
    return json.loads(m.group(0) if m else txt)
