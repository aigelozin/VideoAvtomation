#!/usr/bin/env python3
"""Чинит уже обработанные видео: дописывает название (если не было), переименовывает файл
в done/, переделывает превью, исправляет заголовок/описание на archive.org.
Запуск: repair.py [STEM ...] (без аргументов — все видео)."""
import sys, os, json, glob, subprocess, re
BASE = os.path.expanduser("~/VideoAutomation"); PY = f"{BASE}/.venv/bin/python3"
sys.path.insert(0, BASE)
env = {}
for line in open(f"{BASE}/.env", encoding="utf-8"):
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1); env[k.strip()] = v.strip()
UPLOAD = "--upload" in sys.argv; sys.argv = [a for a in sys.argv if a != "--upload"]
stems = sys.argv[1:] or [os.path.basename(p)[:-5] for p in sorted(glob.glob(f"{BASE}/descriptions/*.json"))]
VEXT = (".mp4", ".mkv", ".mov", ".avi", ".webm", ".flv")

def find_video(stem, d):
    ft = d.get("file_title")
    cands = []
    for folder in ("done", "processing", "inbox"):
        for e in VEXT:
            if ft: cands += [f"{BASE}/{folder}/{ft}/{ft}{e}", f"{BASE}/{folder}/{ft}{e}"]
            cands.append(f"{BASE}/{folder}/{stem}{e}")
    return next((c for c in cands if os.path.exists(c)), None)

for stem in stems:
    jp = f"{BASE}/descriptions/{stem}.json"
    d = json.load(open(jp, encoding="utf-8"))
    v = find_video(stem, d)
    print(f"\n▶ {stem}\n  видео: {v or 'НЕ НАЙДЕНО'}")
    fixed_title = False
    if not d.get("file_title"):
        r = subprocess.run([PY, f"{BASE}/sel_title.py", stem, v or ""], capture_output=True, text=True)
        print("  " + (r.stdout.strip().replace("\n", "\n  ") or r.stderr.strip()))
        if r.returncode != 0:
            print("  ✗ названий нет — сначала: python3 make_meta.py", stem); continue
        d = json.load(open(jp, encoding="utf-8")); fixed_title = True
    else:
        print(f"  название: {d.get('full_title')}")
    if not v: continue
    if fixed_title or not os.path.exists(f"{BASE}/thumbnails/{stem}.jpg"):
        subprocess.run(["bash", f"{BASE}/make_thumb.sh", stem, v, d["full_title"]]); print("  ✓ превью с названием")
    if os.path.abspath(v) != os.path.abspath(f"{BASE}/done/{d['file_title']}/{d['file_title']}{os.path.splitext(v)[1].lower()}"):
        v = subprocess.run([PY, f"{BASE}/rename_video.py", stem, v], capture_output=True, text=True).stdout.strip()
        print(f"  ✓ перенесено → done/{os.path.basename(os.path.dirname(v))}/{os.path.basename(v)}")
    else:
        print("  ✓ имя и папка верные")
    arch = d.get("uploads", {}).get("archive")
    if arch and env.get("ARCHIVE_ACCESS_KEY"):
        import internetarchive as ia
        from en_meta import ensure_en
        ident = arch.rstrip("/").split("/")[-1]
        try:
            en = ensure_en(d); json.dump(d, open(jp, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
            dd, mm, yy = d["date"].split("."); iso = f"{yy}-{mm}-{dd}"
            desc = en["description"] + "\n\n" + env.get("ARCHIVE_SIGNATURE", "International Open Yoga University · openyogaclass.com") + "\n\nLanguage of the video: Russian."
            md = {"title": f"{en['title']} | {iso}", "description": desc.replace("\n", "<br>"), "subject": en["subjects"],
                  "creator": env.get("ARCHIVE_CREATOR_EN", "International Open Yoga University")}
            r = ia.modify_metadata(ident, md, access_key=env["ARCHIVE_ACCESS_KEY"], secret_key=env["ARCHIVE_SECRET_KEY"])
            ok = getattr(r, "status_code", 0) == 200 or "no changes" in getattr(r, "text", "").lower()
            print(f"  {'✓' if ok else '✗'} archive.org по-английски: «{en['title']}» ({arch})")
        except Exception as e: print(f"  ✗ archive.org: {e}")
        thumb = f"{BASE}/thumbnails/{stem}.jpg"
        if fixed_title and os.path.exists(thumb):
            ia.upload(ident, files={"__ia_thumb.jpg": thumb}, access_key=env["ARCHIVE_ACCESS_KEY"],
                      secret_key=env["ARCHIVE_SECRET_KEY"], retries=3); print("  ✓ archive.org: обложка обновлена")
    if UPLOAD and d.get("full_title"):
        r = subprocess.run([PY, f"{BASE}/upload_all.py", stem, v], capture_output=True, text=True)
        print("  " + (r.stdout.strip() or r.stderr.strip()[-300:]).replace("\n", "\n  "))
        d = json.load(open(jp, encoding="utf-8"))
    r = subprocess.run([PY, f"{BASE}/collect.py", stem], capture_output=True, text=True)
    print("  ✓ " + (r.stdout.strip() or r.stderr.strip()[-300:]))
