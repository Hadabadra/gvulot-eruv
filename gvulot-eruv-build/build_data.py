#!/usr/bin/env python3
"""בונה את נתוני התוסף מתוך raw/: תמונות מפה דחוסות (webp) + ממוזערות, ו-data.js עם ערים, מפות ואחראים.
שימוש: python3 build_data.py <תיקיית-התוסף>"""
import json, os, re, sys, hashlib, urllib.parse, datetime
from concurrent.futures import ProcessPoolExecutor
from PIL import Image

PLUG = sys.argv[1]
os.makedirs(f"{PLUG}/maps", exist_ok=True)
MAX, Q, TH = 2000, 52, 420
# מפות שצריכות רזולוציה גבוהה במיוחד (#14 — מפת כל ירושלים מטושטשת ב-2000): מזהה → (צד ארוך, איכות).
# המקור: הקובץ המקורי באתר המוקד (בלי "-scaled" של וורדפרס).
HIRES = {"8d4561e9": (3600, 58)}

ALIAS = {"גני תקווה": "גני תקוה", "פתח תקווה": "פתח תקוה", "קריית אתא": "קרית אתא",
         "קרית יערים": "קריית יערים - טלזסטון", "לוד": "לוד - אחיסמך"}
PRETTY = {"קריית יערים - טלזסטון": "קרית יערים (טלזסטון)", "לוד - אחיסמך": "לוד (אחיסמך)"}


def norm_city(c):
    c = ALIAS.get(c.strip(), c.strip())
    return PRETTY.get(c, c)


def mid(url):
    return hashlib.sha1(url.encode()).hexdigest()[:8]


def hires_src(i, url, fallback):
    """מוריד את המקור המלא של מפה ב-HIRES (בלי -scaled). אם נכשל — הקובץ הרגיל."""
    if i not in HIRES:
        return fallback
    import urllib.request
    os.makedirs("raw/hires", exist_ok=True)
    dst = f"raw/hires/{i}{os.path.splitext(url)[1] or '.jpg'}"
    if not os.path.exists(dst):
        try:
            u = urllib.parse.quote(url.replace("-scaled.", "."), safe=":/")
            urllib.request.urlretrieve(u, dst)
        except Exception as e:
            print("hires נכשל", i, e, file=sys.stderr)
            return fallback
    return dst


def enc(job):
    src, out, th = job
    mx, q = HIRES.get(os.path.basename(out)[:-5], (MAX, Q))
    im = Image.open(src).convert("RGB")
    big = im.copy(); big.thumbnail((mx, mx), Image.LANCZOS)
    big.save(out, "WEBP", quality=q, method=5)
    t = im.copy(); t.thumbnail((TH, TH), Image.LANCZOS)
    t.save(th, "WEBP", quality=60, method=5)
    return out, big.size


pages = json.load(open("raw/index.json"))
resp = json.load(open("raw/responsible.json"))
maps, jobs = [], []
for p in pages:
    t = p["title"].replace("’", "'")
    city, _, sub = [s.strip() for s in t.partition("–")]
    for n, s in enumerate(p.get("sources", [])):
        i = mid(p["url"]) + (f"-{n}" if n else "")
        jobs.append((hires_src(i, s["url"], s["file"]), f"{PLUG}/maps/{i}.webp", f"{PLUG}/maps/{i}.t.webp"))
        maps.append({"id": i, "city": norm_city(city), "title": sub or "מפת העירוב",
                     "pageUrl": urllib.parse.unquote(p["url"]), "imageUrl": s["url"]})

with ProcessPoolExecutor() as ex:
    sizes = dict(ex.map(enc, jobs))
for m in maps:
    m["w"], m["h"] = sizes[f"{PLUG}/maps/{m['id']}.webp"]

bypage = {}
for m in maps:
    bypage.setdefault(m["pageUrl"].rstrip("/"), []).append(m["id"])

areas = []
for r in resp:
    if not r["city"]:
        continue
    areas.append({"city": norm_city(r["city"]), "n": r["num"], "area": r["area"], "names": r["names"],
                  "phones": [p for p in r["phones"] if len(re.sub(r"\D", "", p)) >= 9],
                  "maps": bypage.get((r["mapUrl"] or "").rstrip("/"), [])})

cities = sorted({m["city"] for m in maps} | {a["city"] for a in areas})
data = {"source": {"name": "מוקד העירוב", "site": "http://hiruv.com", "phone": "054-8483320",
                   "note": "אחריות הכשרות בכל מקום היא על האחראי המקומי, ולא על המוקד הארצי."},
        "built": datetime.date.today().isoformat(),
        "cities": cities, "maps": maps, "areas": areas}
open(f"{PLUG}/data.js", "w").write(
    "window.ERUV_DATA = " + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n")
tot = sum(os.path.getsize(f"{PLUG}/maps/{f}") for f in os.listdir(f"{PLUG}/maps"))
print(len(cities), "cities,", len(maps), "maps,", len(areas), "areas,", round(tot / 1e6, 1), "MB images")
