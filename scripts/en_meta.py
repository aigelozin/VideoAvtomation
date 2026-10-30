"""Английская версия метаданных для archive.org: название, описание, темы/теги.
Кэшируется в descriptions/<stem>.json → поле "en". Термины — из en_glossary.txt («рус => англ»)."""
import os, re, sys, json
BASE = os.path.expanduser("~/VideoAutomation"); sys.path.insert(0, BASE)

def _gloss():
    p = f"{BASE}/en_glossary.txt"
    if not os.path.exists(p): return ""
    pairs = [l.strip() for l in open(p, encoding="utf-8") if "=>" in l and not l.lstrip().startswith("#")]
    return ("Use exactly these English names/terms: " + "; ".join(x.replace("=>", "→") for x in pairs) + ".\n") if pairs else ""

def ensure_en(d):
    en = d.get("en") or {}
    if en.get("title") and en.get("description") and en.get("subjects"): return en
    import llm_client as L
    tags = [str(h).lstrip("#") for h in d.get("hashtags", [])]
    prompt = ("Translate and adapt this yoga class video metadata from Russian into natural, fluent English "
              "for archive.org. Return JSON:\n"
              '{"title": "English title, max 80 characters, no date",\n'
              ' "description": "English description, 120-200 words, same facts, no hashtags",\n'
              ' "subjects": ["8-12 English topic keywords/tags, lowercase, e.g. yoga, meditation, pranayama"]}\n'
              "Transliterate personal names (e.g. Олег Атма → Oleg Atma). Keep Sanskrit terms in standard "
              "English transliteration (пранаяма → pranayama, Сат Чит Ананда → Sat Chit Ananda). "
              "Do not invent facts.\n" + _gloss() +
              f"\nRussian title: {d.get('chosen_title') or (d.get('titles') or [''])[0]}\n"
              f"Russian description: {d.get('description', '')}\n"
              f"Russian tags: {', '.join(tags)}\n")
    last = None
    for _ in range(2):
        try:
            r = L.parse_json(L.ask(prompt, as_json=True, timeout=300, max_tokens=1200))
            t = str(r.get("title", "")).strip().strip('"')
            desc = str(r.get("description", "")).strip()
            subj = [str(s).strip().lstrip("#").lower() for s in r.get("subjects", []) if str(s).strip()]
            if t and desc and subj and not re.search(r"[А-Яа-яЁё]", t + desc):
                d["en"] = {"title": t[:100], "description": desc, "subjects": list(dict.fromkeys(subj))[:15]}
                return d["en"]
            last = "в ответе нет полей или остался русский текст"
        except Exception as e: last = e
    raise RuntimeError(f"не удалось получить английский перевод ({last})")
