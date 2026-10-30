#!/usr/bin/env python3
"""Шаги 2-3: описание + 3 названия + хэштеги. Выборка равномерно по всему видео,
её размер (SAMPLE_WORDS) подстраивается под контекст бэкенда."""
import sys, os, json, time
sys.path.insert(0, os.path.expanduser("~/VideoAutomation"))
import llm_client as L

stem = sys.argv[1]
B = L.BASE
words = open(f"{B}/transcripts/{stem}.txt", encoding="utf-8").read().split()
n = len(words)
# русский ≈ 3.5 токена/слово; оставляем ~40% контекста под инструкцию и ответ
auto = int(L.CTX * 0.6 / 3.5)
SAMPLE = int(L.ENV.get("SAMPLE_WORDS", min(auto, 6000)))

def sample(total, parts=8):
    if n <= total: return " ".join(words)
    step, chunk = n // parts, total // parts
    return " [...] ".join(" ".join(words[i*step:i*step+chunk]) for i in range(parts))

gp = f"{B}/glossary.txt"
TERMS = [l.strip() for l in open(gp, encoding="utf-8")] if os.path.exists(gp) else []
TERMS = [t for t in TERMS if t and not t.startswith("#")]
GLOSS = ("Точное написание имён и терминов (не искажай, не склоняй фамилии): "
         + "; ".join(TERMS) + ".\n") if TERMS else ""

PROMPT = ("Ты редактор видео школы йоги. По фрагментам транскрипта (они взяты равномерно "
          "по всему видео) заполни JSON на русском языке:\n"
          '"description": описание видео 120-180 слов, только факты из текста;\n'
          '"titles": три варианта названия, каждое до 55 символов;\n'
          '"hashtags": 5-8 хэштегов.\nПиши только по-русски.\n' + GLOSS + '\nФрагменты:\n')

L.warmup()
data = None
TIMEOUT = int(L.ENV.get("META_TIMEOUT", "180"))
sizes = sorted({s for s in (min(SAMPLE, 3000), 1200, 600, 300) if s <= SAMPLE}, reverse=True)
used = 0
for size in sizes:
    t0 = time.time(); body = PROMPT + sample(size)
    try:
        data = L.parse_json(L.ask(body, as_json=True, timeout=TIMEOUT))
        print(f"  выборка {size} слов ({len(body.encode())//1024} КБ): {time.time()-t0:.0f} с OK")
        if isinstance(data.get("titles"), list) and data["titles"]: used = min(n, size); break
    except Exception as e:
        print(f"  ⚠ выборка {size} слов ({len(body.encode())//1024} КБ): {time.time()-t0:.0f} с — {e}")
    data = None
if not data:
    data = {"description": "", "titles": [stem], "hashtags": []}

json.dump(data, open(f"{B}/descriptions/{stem}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
os.makedirs(f"{B}/articles", exist_ok=True)
open(f"{B}/articles/{stem}.md", "w", encoding="utf-8").write(
    f"# {data['titles'][0]}\n\n{data.get('description','')}\n\n{' '.join(map(str, data.get('hashtags', [])))}\n")
print(f"META_OK [{L.BACKEND}, выборка {used} из {n} слов]:", " | ".join(map(str, data["titles"])))
