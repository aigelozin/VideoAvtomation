"""Чистка транскрипта: выбрасывает «эхо» глоссария и типовые выдумки Whisper на тишине,
затем исправляет термины по словарю replacements.txt («как распознано => как правильно»)."""
import os, re
BASE = os.path.expanduser("~/VideoAutomation")

def _lines(name):
    p = f"{BASE}/{name}"
    if not os.path.exists(p): return []
    return [l.strip() for l in open(p, encoding="utf-8") if l.strip() and not l.lstrip().startswith("#")]

HALLU = [r"Субтитры (?:создавал|сделал|делал|подготовил)[а-я]*\s+[\w.\-]+\.?",
         r"Редактор субтитров[^.!?]*(?:Корректор\s+[\w.\-]+(?:\s+[\w.\-]+)?)?\.?",
         r"Продолжение следует\.{0,3}",
         r"Занятие Международного Открытого Йога Университета\."]

def clean(text):
    terms = {t.lower() for t in _lines("glossary.txt")}
    for h in HALLU:
        text = re.sub(h, " ", text, flags=re.IGNORECASE)
    # предложения, состоящие в основном из терминов глоссария через запятую = эхо подсказки
    parts = re.split(r"(?<=[.!?])\s+", text)
    keep = []
    for p in parts:
        items = [i.strip(" .!?").lower() for i in p.split(",") if i.strip(" .!?")]
        if terms and len(items) >= 3 and sum(i in terms for i in items) / len(items) >= 0.6:
            continue
        keep.append(p)
    text = " ".join(keep)
    for line in _lines("replacements.txt"):
        if "=>" in line:
            wrong, right = (x.strip() for x in line.split("=>", 1))
            if wrong: text = re.sub(re.escape(wrong), right, text, flags=re.IGNORECASE)
    return re.sub(r"\s{2,}", " ", text).strip()
