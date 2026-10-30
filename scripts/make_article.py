#!/usr/bin/env python3
"""Статья для блога (WordPress), 600–1000 слов, в два этапа:
 1) план по транскрипту (JSON): разделы, ключевые мысли, реплики диалогов с именами;
 2) текст каждого раздела — отдельным коротким запросом по плану (модель не видит сырой текст → не копирует его).
Структуру (заголовки, диалоги, итог) собирает код. Результат: articles/<stem>.md, .html, .plan.json.
.env: ARTICLE_MIN=600, ARTICLE_MAX=1000, ARTICLE_SAMPLE=6000."""
import sys, os, re, json, time, html
BASE = os.path.expanduser("~/VideoAutomation"); sys.path.insert(0, BASE)
import llm_client as L

stem = sys.argv[1]
words = open(f"{BASE}/transcripts/{stem}.txt", encoding="utf-8").read().split(); n = len(words)
WMIN, WMAX = int(L.ENV.get("ARTICLE_MIN", "600")), int(L.ENV.get("ARTICLE_MAX", "1000"))
SAMPLE = int(L.ENV.get("ARTICLE_SAMPLE", "6000")); TIMEOUT = int(L.ENV.get("ARTICLE_TIMEOUT", "900"))
try: d = json.load(open(f"{BASE}/descriptions/{stem}.json", encoding="utf-8"))
except Exception: d = {}
title = d.get("chosen_title") or (d.get("titles") or [stem])[0]
gp = f"{BASE}/glossary.txt"
terms = [l.strip() for l in open(gp, encoding="utf-8") if l.strip() and not l.startswith("#")] if os.path.exists(gp) else []
GLOSS = ("Точное написание имён и терминов: " + "; ".join(terms) + ".\n") if terms else ""

def sample(k, parts=12):
    if n <= k: return " ".join(words)
    step, chunk = n // parts, k // parts
    return "\n…\n".join(" ".join(words[i * step:i * step + chunk]) for i in range(parts))

def shingles(t, k=6):
    w = re.findall(r"\w+", t.lower()); return {" ".join(w[i:i + k]) for i in range(max(0, len(w) - k + 1))}
SRC = shingles(" ".join(words))
def copied(t):                                   # доля текста, дословно взятая из транскрипта
    s = shingles(t); return len(s & SRC) / len(s) if s else 1.0

# ── 1. План ──
PLAN_TASK = (
    "ЗАДАНИЕ. Выше — транскрипт занятия школы йоги (фрагменты взяты равномерно по всему видео, "
    "речь распознана автоматически, возможны ошибки). НЕ пересказывай его подряд и НЕ копируй. "
    f"Составь план статьи для блога на тему «{title}». Ответь JSON:\n"
    '{"intro": "2–3 предложения: что за занятие, кто ведёт, о чём",\n'
    ' "sections": [{"title": "короткий подзаголовок", "points": ["конкретная мысль, факт или практика из занятия", "..."],\n'
    '               "dialogue": [{"who": "имя говорящего", "text": "реплика, близко к сказанному"}]}],\n'
    ' "takeaways": ["главная мысль занятия", "..."]}\n'
    "Правила: 4–6 разделов в порядке хода занятия; в каждом 4–7 points своими словами; "
    "dialogue заполняй ТОЛЬКО там, где был живой обмен репликами (вопрос — ответ, обсуждение, приветствия участников), "
    "2–6 реплик, исправь оговорки и слова-паразиты; если имя неясно — «Ведущий», «Участница», «Участник»; "
    "иначе dialogue = []. takeaways — 3–5 пунктов. Только факты из транскрипта, по-русски.\n" + GLOSS)

plan = None
for k in sorted({min(SAMPLE, n), min(3000, n), min(1500, n)}, reverse=True):
    t0 = time.time()
    try:
        p = L.parse_json(L.ask("=== ТРАНСКРИПТ ===\n" + sample(k) + "\n=== КОНЕЦ ТРАНСКРИПТА ===\n\n" + PLAN_TASK,
                               as_json=True, timeout=TIMEOUT, max_tokens=3500))
        secs = [s for s in p.get("sections", []) if isinstance(s, dict) and s.get("title") and s.get("points")]
        print(f"  план по {k} словам: {time.time()-t0:.0f} с, разделов {len(secs)}")
        if len(secs) >= 3: p["sections"] = secs[:6]; plan = p; break
    except Exception as e:
        print(f"  ⚠ план по {k} словам: {time.time()-t0:.0f} с — {e}")
if not plan: print("СТАТЬЯ НЕ СОЗДАНА: план не получился"); sys.exit(1)
os.makedirs(f"{BASE}/articles", exist_ok=True)
json.dump(plan, open(f"{BASE}/articles/{stem}.plan.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)

# ── 2. Текст разделов ──
secs = plan["sections"]
per = max(90, int(((WMIN + WMAX) / 2 - 60 - 50) / len(secs)))      # слов на раздел без учёта диалогов
outline = "; ".join(s["title"] for s in secs)

def clean_par(t):
    t = re.sub(r"(?m)^\s*#+.*$", "", t); t = re.sub(r"\*\*|__", "", t)
    return [p.strip() for p in re.split(r"\n\s*\n", t) if len(p.strip()) > 20]

def write(task, size):
    for attempt in range(2):
        try:
            txt = L.ask(task, timeout=300, max_tokens=size * 4).strip()
            pars = clean_par(txt)
            if pars and copied(" ".join(pars)) < 0.35: return pars
            print(f"    ⚠ ответ похож на копию транскрипта — повтор")
        except Exception as e: print(f"    ⚠ {e}")
    return []

STYLE = ("Пиши по-русски, живым понятным языком для читателя, который не был на занятии, от третьего лица "
         "(«на занятии разбирали…», «ведущий объясняет…»). Без заголовков, списков и markdown — только абзацы "
         "через пустую строку. Ничего не выдумывай сверх данных пунктов.\n" + GLOSS)
intro = write(f"Статья для блога Международного Открытого Йога Университета «{title}». Разделы статьи: {outline}.\n"
              f"Напиши вступление 50–70 слов, один абзац, на основе: {plan.get('intro','')}\n" + STYLE, 70)
bodies = []
for s in secs:
    t0 = time.time()
    pars = write(f"Статья «{title}». Напиши текст раздела «{s['title']}» объёмом {per}–{per + 40} слов, 2–3 абзаца, "
                 f"раскрой эти мысли из занятия:\n- " + "\n- ".join(map(str, s["points"])) + "\n" + STYLE, per + 40)
    bodies.append(pars or [" ".join(map(str, s["points"]))])
    print(f"  раздел «{s['title']}»: {time.time()-t0:.0f} с")
take = [str(t).strip() for t in plan.get("takeaways", []) if str(t).strip()]

# ── 3. Сборка ──
def dlg(s): return [(str(r.get("who", "")).strip() or "Участник", str(r.get("text", "")).strip())
                    for r in (s.get("dialogue") or []) if isinstance(r, dict) and str(r.get("text", "")).strip()]
md = [f"# {title}", ""] + [p + "\n" for p in intro]
H = [f"<p>{html.escape(p)}</p>" for p in intro]
for s, pars in zip(secs, bodies):
    md += [f"## {s['title']}", ""] + [p + "\n" for p in pars]
    H += [f"<h2>{html.escape(s['title'])}</h2>"] + [f"<p>{html.escape(p)}</p>" for p in pars]
    rep = dlg(s)
    if rep:
        md += ["Из разговора на занятии:", ""] + [f"> **{w}:** {t}\n>" for w, t in rep] + [""]
        H += ['<p><em>Из разговора на занятии:</em></p>', '<blockquote class="dialogue">'] + \
             [f"<p><strong>{html.escape(w)}:</strong> {html.escape(t)}</p>" for w, t in rep] + ["</blockquote>"]
if take:
    md += ["## Главное", ""] + [f"- {t}" for t in take] + [""]
    H += ["<h2>Главное</h2>", "<ul>"] + [f"<li>{html.escape(t)}</li>" for t in take] + ["</ul>"]
md_text = "\n".join(md)
open(f"{BASE}/articles/{stem}.md", "w", encoding="utf-8").write(md_text)
open(f"{BASE}/articles/{stem}.html", "w", encoding="utf-8").write("\n".join(H) + "\n")
CSS = ("body{max-width:760px;margin:40px auto;padding:0 16px;font:18px/1.6 Georgia,serif;color:#222}"
       "h1,h2{font-family:sans-serif}h2{margin-top:1.8em}blockquote.dialogue{border-left:4px solid #c9a46b;"
       "background:#faf6ef;margin:1em 0;padding:.6em 1em}blockquote.dialogue p{margin:.4em 0}")
open(f"{BASE}/articles/{stem}.preview.html", "w", encoding="utf-8").write(
    f"<!doctype html><meta charset=utf-8><title>{html.escape(title)}</title><style>{CSS}</style>"
    f"<h1>{html.escape(title)}</h1>\n" + "\n".join(H))
wc = len(re.findall(r"\w+", re.sub(r"[#>*\-]", " ", md_text)))
print(f"ARTICLE_OK: {wc} слов, разделов {len(secs)}, диалогов {sum(1 for s in secs if dlg(s))}: "
      + " | ".join(s["title"] for s in secs))
