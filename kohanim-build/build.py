#!/usr/bin/env python3
"""בונה את תוכן התוסף "טהרת כהנים" מתוך kohanim-build/raw (ראו fetch.py). החומר של התאחדות טהרת הכהנים, באישורם.
פלט בתיקיית התוסף (kohanim/):
  data.js        window.ERUV_DATA  — ערים, מפות (תמונות), אזורים אסורים ונקודות הפצה (אותו מבנה כמו בגבולות עירוב)
  eruv-lines.js  window.ERUV_LINES — מצולעי האזורים האסורים לשכבת המפה ולבדיקת כתובת
  docs.js + docs/<id>.pdf.js + docs/<id>/NNN.t.webp — חוברות, עלונים ומצגות (PDF דחוס, base64)
  maps/<id>.webp + .t.webp — מפות של עמוד אחד עד שלושה
  extra.js       window.ERUV_EXTRA — קישורים (סרטונים, אתרים) ולוח הטיסות הקבוע (flights)
שימוש: python3 build.py ../kohanim [--quick]   (‏--quick: רק נתונים, בלי מפות וחוברות. דורש gs, pdftoppm, img2pdf, Pillow, openpyxl)
"""
import base64, datetime, glob, hashlib, json, math, os, re, shutil, subprocess, sys, tempfile
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")
DRIVE = os.path.join(RAW, "drive")
TW = 120          # רוחב תמונה ממוזערת לעמוד חוברת
MAPW = 2400       # רוחב תמונת מפה (כמו מפות העירוב)
SRC = {"name": "התאחדות טהרת הכהנים", "site": "https://hakohanim.org/", "phone": "08-3132020",
       "note": "המידע להתמצאות בלבד ואינו פסק הלכה. בכל ספק — קו המידע של ההתאחדות או רב."}
DRIVE_URL = "https://drive.google.com/file/d/{}/view"

# מפות: (id, קובץ, כותרת, עיר, עמודים) — כל עמוד הוא מפה נפרדת במציג (הגדלה, סיבוב, ייצוא)
MAPS = [
    ("meron-new", "מפות והדרכות/מפה מירון חדש.pdf", "מפת מירון החדשה", "מירון", None),
    ("meron-ba", "מפות והדרכות/מירון בני עקיבא.png", "מירון — אזור בני עקיבא", "מירון", None),
    ("safed", "מפות והדרכות/מפת צפת.pdf", "מפת צפת", "צפת", None),
    ("tiberias", "מפות והדרכות/מפת טבריה כללי בלי ההדרכות.pdf", "מפת טבריה — כללי", "טבריה", None),
    ("haifa", "מפות והדרכות/מפת חיפה.pdf", "מפת חיפה", "חיפה", None),
    ("hadassah", "מפות והדרכות/מפת הדסה עין כרם לכהנים.pdf", "הדסה עין כרם", "ירושלים", None),
    ("har-hazeitim", "מפות והדרכות/מפת הר הזיתים.pdf", "הר הזיתים", "ירושלים", None),
    ("har-herzl", "מפות והדרכות/מפת הר הרצל לכהנים (משרד הביטחון).jpg", "הר הרצל (מפת משרד הביטחון)", "ירושלים", None),
    ("david-zion", "מפות והדרכות/מפת קבר דוד המלך והר ציון.pdf", "קבר דוד המלך והר ציון", "ירושלים", None),
    ("shmuel", "מפות והדרכות/קבר שמואל הנביא עם סימונים.png", "קבר שמואל הנביא", "ירושלים", None),
    ("ichilov", "מפות והדרכות/מפת איכילוב.pdf", "איכילוב — מפה לכהנים", "תל אביב", None),
    ("ichilov-orient", "מפות והדרכות/מפת התמצאות באיכילוב.png", "איכילוב — מפת התמצאות", "תל אביב", None),
    ("tel-hashomer", "מפות והדרכות/מפה חדשה של תל השומר עם סימונים.pdf", "תל השומר (שיבא) — מפה עם סימונים", "רמת גן", None),
    ("assaf", "מפות והדרכות/מפת התמצאות באסף הרופא.pdf", "אסף הרופא (שמיר) — מפת התמצאות", "באר יעקב", None),
    ("road-444", "מפות והדרכות/מפת כביש 444 צומת גמזו.pdf", "כביש 444 — צומת גמזו", "כבישים בין-עירוניים", None),
    ("nachal-hashofet", "מפות והדרכות/הדרכה בנחל השופט.pdf", "הדרכה בנחל השופט", "נחל השופט", None),
    ("uman", "מפות והדרכות/מפת אומן לכהנים.pdf", "מפת אומן לכהנים", "אומן (אוקראינה)", None),
]
# חוברות, עלונים ומצגות: (id, קובץ, כותרת, קבוצה, ערים, סוג דחיסה) ; סוג: book (טקסט) / pres (מצגת — רסטור) / map (מפה רב-עמודית)
DOCS = [
    ("madrich", "המדריך לכהנים המעודכן - רחובות ואתרים.pdf", "המדריך לכהנים המעודכן — רחובות, אתרים, טיסות וחו\"ל", "guide", [], "book"),
    ("medical", "מידע על מרכזים רפואיים לציבור הכהנים.pdf", "מרכזים רפואיים והלכות פיקוח נפש", "guide", ["ירושלים", "תל אביב", "רמת גן", "באר יעקב"], "book"),
    ("bein-hazmanim", "עלון מידע בין הזמנים תשפו.pdf", "מידע לבין הזמנים תשפ\"ו (כולל מפת טבריה)", "guide", ["טבריה", "צפת", "מירון"], "book"),
    ("updates", "עדכונים והוספות למידע תמוז תשפה.pdf", "עדכונים והוספות למידע — תמוז תשפ\"ה", "guide", [], "book"),
    ("gps-guide", "כל המידע על תוכנת הניווט.pdf", "תוכנת הניווט לכהנים — כל המידע", "guide", [], "book"),
    ("muslim-quarter", "מפות והדרכות/מפת הרובע המוסלמי עם סימונים לכהנים.pdf", "מפת הרובע המוסלמי עם סימונים לכהנים", "maps", ["ירושלים"], "map"),
    ("akko", "מפות והדרכות/הדרכה לנסיעה לעכו - ארץ העמים.pdf", "הדרכה לנסיעה לעכו — ארץ העמים", "maps", ["עכו"], "map"),
    ("north", "מצגות הדרכה/מצגת הדרכה בצפון.pdf", "מצגת הדרכה בצפון", "maps", ["צפת", "טבריה", "מירון", "חיפה", "עכו"], "pres"),
    ("meron-pres", "מצגות הדרכה/מצגת מירון.pdf", "מצגת מירון", "maps", ["מירון"], "pres"),
    ("mk-tiberias", "מראות כהונה - חוברות הלכתיות/מראות כהונה ביאור דעת גדולי הפוסקים על חששות טומאת כהנים בטבריה תחתית.pdf", "מראות כהונה — דעת גדולי הפוסקים על טבריה תחתית", "marot", ["טבריה"], "book"),
    ("mk-hospitals", "מראות כהונה - חוברות הלכתיות/מראות כהונה בתי חולים ונפלים למורי הוראה.pdf", "מראות כהונה — בתי חולים ונפלים (למורי הוראה)", "marot", [], "book"),
    ("mk-pikuach", "מראות כהונה - חוברות הלכתיות/מראות כהונה הלכות פיקוח נפש לכהנים בבתי חולים.pdf", "מראות כהונה — פיקוח נפש לכהנים בבתי חולים", "marot", [], "book"),
    ("mk-flights", "מראות כהונה - חוברות הלכתיות/מראות כהונה טומאת כהנים בטיסות ונמלי תעופה.pdf", "מראות כהונה — טומאת כהנים בטיסות ונמלי תעופה", "marot", [], "book"),
    ("mk-summary", "מראות כהונה - חוברות הלכתיות/מראות כהונה סיכום השיעורים צבעוני.pdf", "מראות כהונה — סיכום השיעורים (צבעוני)", "marot", [], "book"),
    ("teiva", "מראות כהונה - חוברות הלכתיות/קונטרס תיבה נזרקת.pdf", "קונטרס תיבה נזרקת", "marot", [], "book"),
    ("chevra-kadisha", "מראות כהונה - חוברות הלכתיות/קיצור הלכות טומאת מת לחברא קדישא.pdf", "קיצור הלכות טומאת מת לחברא קדישא", "marot", [], "book"),
    ("tahorat-yosef", "מראות כהונה - חוברות הלכתיות/אוסף גליונות טהרת יוסף בירורי סוגיות במסכת אהלות.pdf", "טהרת יוסף — בירורי סוגיות במסכת אהלות", "marot", [], "book"),
    ("emor-1-10", "אמור ואמרת - עלונים הלכתיים/אמור ואמרת מעודכן סופי 1-10.pdf", "אמור ואמרת — גליונות 1–10", "emor", [], "book"),
    ("emor-collection", "אמור ואמרת - עלונים הלכתיים/אמור ואמרת אוסף תשפב - תשפו.pdf", "אמור ואמרת — אוסף תשפ\"ב–תשפ\"ו", "emor", [], "book"),
    ("emor-shvat", "אמור ואמרת - עלונים הלכתיים/אמור ואמרת 26 שבט תשפו תוכנת ניווט לכהנים ותיקון בית העלמין שערי צדק.pdf", "אמור ואמרת — שבט תשפ\"ו: תוכנת הניווט ותיקון בית העלמין שערי צדק", "emor", ["ירושלים"], "book"),
    ("rimonim", "אמור ואמרת - עלונים הלכתיים/טהרת רימונים ח אב.pdf", "טהרת רימונים — ח' אב", "emor", [], "book"),
    ("pres-ohel", "מצגות הלכתיות/מצגת אהל חוצץ.pdf", "מצגת: אוהל חוצץ", "pres", [], "pres"),
    ("pres-buildings", "מצגות הלכתיות/מצגת העברת טומאת מת בבתי חולים ובבנינים.pdf", "מצגת: העברת טומאת מת בבתי חולים ובבניינים", "pres", [], "pres"),
    ("pres-flights", "מצגות הלכתיות/מצגת טומאת כהנים בטיסות וטרמינלים.pdf", "מצגת: טומאת כהנים בטיסות וטרמינלים", "pres", [], "pres"),
    ("pres-sof-tuma", "מצגות הלכתיות/מצגת סוף טומאה לצאת.pdf", "מצגת: סוף טומאה לצאת", "pres", [], "pres"),
    ("pres-cranes", "מצגות הלכתיות/מצגת על המנופים בירושלים.pdf", "מצגת: המנופים בירושלים", "pres", ["ירושלים"], "pres"),
]
# כפילויות בתיקייה (אותו קובץ בשתי תיקיות) — לא נארזות פעמיים
DUPS = {"אמור ואמרת - עלונים הלכתיים/מאמר טבריה.pdf": "mk-tiberias",
        "אמור ואמרת - עלונים הלכתיים/אוסף גליונות טהרת יוסף בירורי סוגיות במסכת אהלות.pdf": "tahorat-yosef",
        "מפות והדרכות/מצגת הדרכה בצפון.pdf": "north"}
CITY_POS = {"ירושלים": [31.780, 35.210], "טבריה": [32.790, 35.530], "צפת": [32.960, 35.500], "מירון": [32.980, 35.440], "חיפה": [32.800, 34.990],
            "תל אביב": [32.080, 34.780], "רמת גן": [32.070, 34.820], "באר שבע": [31.252, 34.791], "באר יעקב": [31.935, 34.840], "עכו": [32.927, 35.083],
            "גבעתיים": [32.071, 34.811], "נחשונים": [32.060, 34.950], "אלעד": [32.052, 34.951], "לוד": [31.951, 34.888], "בית שמש": [31.730, 34.990],
            "הרצליה": [32.166, 34.844], "חצור": [32.980, 35.540], "נתיבות": [31.420, 34.590], "אשקלון": [31.668, 34.574], "זכרון יעקב": [32.570, 34.950],
            "נחל השופט": [32.604, 35.100], "בני ברק": [32.084, 34.834], "פתח תקוה": [32.090, 34.880], "נתניה": [32.330, 34.860], "אשדוד": [31.801, 34.650],
            "מודיעין עילית": [31.930, 35.040], "ביתר": [31.700, 35.120], "רחובות": [31.890, 34.810], "חולון": [32.016, 34.779], "עפולה": [32.610, 35.290],
            "כרמיאל": [32.920, 35.300], "נוף הגליל": [32.710, 35.320], "קרית גת": [31.610, 34.770], "אופקים": [31.314, 34.620], "דימונה": [31.069, 35.033],
            "ערד": [31.259, 35.214], "קרית שמונה": [33.207, 35.571], "נהריה": [33.006, 35.094], "רמלה": [31.928, 34.866], "חדרה": [32.434, 34.919]}
CITY_FIX = {"ליד ירושלים": "ירושלים", "תל אביב כביש 5": "תל אביב", "אחיסמך": "לוד", "בית שמש ": "בית שמש"}
OPEN_ROADS = "כבישים ושטחים פתוחים"
LEVEL = {"א": "רמה א", "ב": "רמה ב", "ג": "רמה ג"}

def run(*a): subprocess.run(a, check=True, capture_output=True)
def km(a, b):
    r = math.pi / 180; x = (b[1] - a[1]) * r * math.cos((a[0] + b[0]) * r / 2); y = (b[0] - a[0]) * r
    return math.hypot(x, y) * 6371

def compress(src, kind, tmp):
    """מחזיר נתיב ל-PDF הקטן ביותר מבין כמה דחיסות (כל החומר נשאר; רק תמונות נדחסות)."""
    cand = [src]
    def gs(out, preset, dpi, q=None):
        a = ["gs", "-q", "-dNOPAUSE", "-dBATCH", "-sDEVICE=pdfwrite", "-dCompatibilityLevel=1.5", f"-dPDFSETTINGS=/{preset}",
             f"-dColorImageResolution={dpi}", f"-dGrayImageResolution={dpi}", "-dMonoImageResolution=200", "-dDetectDuplicateImages=true"]
        if q: a += ["-dColorImageDownsampleThreshold=1.0", "-dGrayImageDownsampleThreshold=1.0", f"-dJPEGQ={q}"]
        subprocess.run(a + ["-sOutputFile=" + out, src], capture_output=True)
        if os.path.exists(out) and os.path.getsize(out) > 1000: cand.append(out)
    gs(tmp + "/e.pdf", "ebook", 150)
    if kind == "map": raster(src, tmp + "/m.pdf", 2200, 62); cand.append(tmp + "/m.pdf")
    elif kind == "pres": raster(src, tmp + "/p.pdf", 1000, 45); cand.append(tmp + "/p.pdf")
    elif os.path.getsize(src) > 1_500_000: gs(tmp + "/s.pdf", "screen", 72, 45)
    if kind == "map": return tmp + "/m.pdf"   # מפה: חדות קבועה גם אם יוצא מעט גדול יותר
    return min(cand, key=os.path.getsize)

def raster(src, out, w, q):
    t = tempfile.mkdtemp()
    run("pdftoppm", "-r", "150", "-jpeg", "-jpegopt", "quality=95", src, t + "/p")
    js = sorted(glob.glob(t + "/p-*.jpg"))
    for p in js:
        im = Image.open(p).convert("RGB")
        if im.width > w: im = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
        im.save(p, "JPEG", quality=q, optimize=True, progressive=True)
    run("img2pdf", *js, "-o", out); shutil.rmtree(t)

def pages_of(path):
    """תמונות העמודים של מפה (PIL), ברוחב MAPW לכל היותר."""
    if not path.lower().endswith(".pdf"): return [Image.open(path).convert("RGB")]
    t = tempfile.mkdtemp(); run("pdftoppm", "-r", "220", "-png", path, t + "/p")
    ims = [Image.open(p).convert("RGB") for p in sorted(glob.glob(t + "/p-*.png"))]; shutil.rmtree(t)
    return ims

def load_js(path):
    t = open(path, encoding="utf8").read(); return json.loads(t[t.index("=", t.index("window.")) + 1:].strip().rstrip(";"))

def main(out, quick=False):
    """quick: בלי לצייר מחדש מפות וחוברות (לוקח דקות) — רק נתונים: אזורים, נקודות הפצה, טיסות, קישורים."""
    tree = {x["path"]: x["id"] for x in json.load(open(os.path.join(RAW, "drive-tree.json")))}
    used = set()
    if quick:
        maps = load_js(os.path.join(out, "data.js"))["maps"]; res = load_js(os.path.join(out, "docs.js"))
        used |= {m[1] for m in MAPS} | {d[1] for d in DOCS}
    # ── מפות ──
    if not quick: shutil.rmtree(os.path.join(out, "maps"), ignore_errors=True); os.makedirs(os.path.join(out, "maps"))
    if not quick: maps = []
    for mid, fn, title, city, _ in ([] if quick else MAPS):
        ims = pages_of(os.path.join(DRIVE, fn)); used.add(fn)
        for i, im in enumerate(ims, 1):
            iid = mid if len(ims) == 1 else f"{mid}-{i}"
            if im.width > MAPW: im = im.resize((MAPW, round(im.height * MAPW / im.width)), Image.LANCZOS)
            im.save(os.path.join(out, "maps", iid + ".webp"), "WEBP", quality=72, method=6)
            th = im.copy(); th.thumbnail((420, 420), Image.LANCZOS); th.save(os.path.join(out, "maps", iid + ".t.webp"), "WEBP", quality=60, method=6)
            maps.append({"id": iid, "city": city, "title": title + (f" ({i}/{len(ims)})" if len(ims) > 1 else ""),
                         "pageUrl": DRIVE_URL.format(tree.get(fn, "")), "w": im.width, "h": im.height})
        print("מפה", title, len(ims), file=sys.stderr)
    # ── חוברות ──
    if not quick: res = []
    for did, fn, title, group, cities, kind in ([] if quick else DOCS):
        src = os.path.join(DRIVE, fn); used.add(fn)
        dst = os.path.join(out, "docs", did); shutil.rmtree(dst, ignore_errors=True); os.makedirs(dst)
        tmp = tempfile.mkdtemp(); pdf = compress(src, kind, tmp)
        run("pdftoppm", "-r", "30", "-png", pdf, f"{tmp}/t")
        dims = []
        for i, p in enumerate(sorted(glob.glob(f"{tmp}/t-*.png")), 1):
            im = Image.open(p).convert("RGB"); dims.append([1000, round(1000 * im.height / im.width)])
            im.thumbnail((TW, TW * 2), Image.LANCZOS); im.save(f"{dst}/{i:03d}.t.webp", "WEBP", quality=45, method=6)
        b = base64.b64encode(open(pdf, "rb").read()).decode()
        with open(os.path.join(out, "docs", did + ".pdf.js"), "w") as f:   # שורות קצרות: מחרוזת ענקית אחת גורמת ל-Stack Overflow באוצריא
            f.write("(window.ERUV_PDF=window.ERUV_PDF||{})[" + json.dumps(did) + "]=[\n" + ",\n".join('"' + b[i:i + 4000] + '"' for i in range(0, len(b), 4000)) + "\n].join('');\n")
        res.append({"id": did, "title": title, "kind": "booklet", "group": group, "cities": cities, "url": DRIVE_URL.format(tree.get(fn, "")),
                    "pages": len(dims), "dims": dims, "bytes": os.path.getsize(pdf)})
        print("חוברת", title, len(dims), os.path.getsize(src), "→", os.path.getsize(pdf), file=sys.stderr)
        shutil.rmtree(tmp)
    with open(os.path.join(out, "docs.js"), "w") as f:
        f.write("/* נוצר על ידי kohanim-build/build.py — לא לערוך ידנית */\nwindow.ERUV_DOCS = " + json.dumps(res, ensure_ascii=False, separators=(",", ":")) + ";\n")
    # ── אזורים אסורים (תוכנת הניווט) ──
    feats = json.load(open(os.path.join(RAW, "areas.json")))["data"]["features"]
    lines, areas, cpos = {}, [], dict(CITY_POS)
    for f in feats:
        pr = f["properties"]; ring = f["geometry"]["coordinates"][0]
        coords = [[round(c[1], 6), round(c[0], 6)] for c in ring]
        cen = [sum(c[0] for c in coords) / len(coords), sum(c[1] for c in coords) / len(coords)]
        lid = hashlib.sha1(json.dumps(ring).encode()).hexdigest()[:8]
        lvl = pr.get("level") or ""
        raw_city = (pr.get("city") or "").strip()
        city, sub = raw_city, ""
        if " - " in city: city, sub = [x.strip() for x in city.split(" - ", 1)]
        city = CITY_FIX.get(raw_city, CITY_FIX.get(city, city)).strip().rstrip(" -–").strip()
        if lvl == "A":   # שטחי A (מתוכנת הניווט) — שכבה נפרדת במפה בלבד
            lines[lid] = {"city": "", "name": "שטח A", "resp": "", "closed": True, "level": "A", "coords": coords}; continue
        if not city or city == "בינעירוני":
            near = min(cpos.items(), key=lambda kv: km(cen, kv[1]))
            city = near[0] if km(cen, near[1]) < 6 else OPEN_ROADS
        name = (pr.get("name") or "").strip()
        if name in ("", "אזור") and pr.get("street"): name = pr["street"]
        title = " · ".join(x for x in [sub, name if name != "אזור" else "", ("רח' " + pr["street"]) if pr.get("street") and pr.get("street") != name else ""] if x) or "אזור"
        lines[lid] = {"city": city, "name": title, "resp": pr.get("description") or "", "closed": True, "level": lvl, "coords": coords}
        areas.append({"city": city, "n": "", "area": title, "names": [pr["description"]] if pr.get("description") else [], "noNames": "",
                      "phones": [], "maps": [], "badge": lvl, "badgeText": LEVEL.get(lvl, lvl), "group": "areas", "line": lid})
    # ── נקודות להשגת המדריך והמפות (גיליון ההתאחדות) ──
    import openpyxl
    ws = openpyxl.load_workbook(os.path.join(DRIVE, "כתובות להשגת המדריך לכהנים והמפות.xlsx"), read_only=True).worksheets[0]
    for r in list(ws.iter_rows(values_only=True))[1:]:
        if not r or not r[0]: continue
        city = CITY_FIX.get(str(r[0]).strip(), str(r[0]).strip())
        ph = [p.strip() for p in re.split(r"[,/]| ו-", str(r[3] or "")) if re.search(r"\d{6}", p)]
        note = re.sub(r"[,\s]+$", "", str(r[4] or "").strip())
        areas.append({"city": city, "n": "", "area": " · ".join(x for x in [str(r[1] or "").strip(), str(r[2] or "").strip()] if x),
                      "names": [note] if note else [], "noNames": "", "phones": ph, "maps": [], "group": "dist"})
    used.add("כתובות להשגת המדריך לכהנים והמפות.xlsx")
    order = ["ירושלים", "טבריה", "צפת", "מירון", "חיפה", "תל אביב", "רמת גן", "באר יעקב", "באר שבע", "עכו"]
    cities = sorted({m["city"] for m in maps} | {a["city"] for a in areas} | {c for d in res for c in d["cities"]},
                    key=lambda c: (c == OPEN_ROADS, c not in order, order.index(c) if c in order else 0, c))
    built = datetime.date.today().isoformat()
    with open(os.path.join(out, "data.js"), "w") as f:
        f.write("/* נוצר על ידי kohanim-build/build.py מחומרי התאחדות טהרת הכהנים, באישורם — לא לערוך ידנית */\nwindow.ERUV_DATA = " +
                json.dumps({"source": SRC, "built": built, "cities": cities, "maps": maps, "areas": areas, "cityPos": cpos},
                           ensure_ascii=False, separators=(",", ":")) + ";\n")
    with open(os.path.join(out, "eruv-lines.js"), "w") as f:
        f.write("/* אזורים אסורים לכהנים — מתוך תוכנת הניווט של התאחדות טהרת הכהנים (gps.hakohanim.org), באישורם. נוצר על ידי kohanim-build/build.py.\n"
                "   להתמצאות בלבד; הקובע הוא ההתאחדות והרב. */\nwindow.ERUV_LINES = " + json.dumps(lines, ensure_ascii=False, separators=(",", ":")) + ";\n")
    # ── טיסות: הלוח הקבוע לפי יום בשבוע ──
    days = {}
    for p in sorted(glob.glob(os.path.join(RAW, "flights", "*.json"))):
        j = json.load(open(p)); days[str(j["weekday"])] = [{"f": x["flight"], "o": x["origin"], "t": x["scheduled"]} for x in j["landings"]]
        win = j.get("windows", {"red": 20, "orange": 80})
    notices = json.load(open(os.path.join(RAW, "notices.json"))).get("messages", [])
    flights = {"built": built, "windows": win, "days": days, "notices": notices, "src": "https://flights.hakohanim.org/"}   # לוח קבוע, משוער בלבד
    # ── קישורים (כשיש אינטרנט): סרטונים ומה שלא נארז ──
    lib = []
    for path, fid in sorted(tree.items()):
        if path in used or path in DUPS: continue
        g = "סרטוני הדרכה והלכה (Google Drive — כשיש אינטרנט)" if re.search(r"\.(mp4|mov)$", path, re.I) else "קבצים נוספים"
        lib.append({"g": g, "t": re.sub(r"\.(mp4|mov|pdf)$", "", path.split("/")[-1], flags=re.I).replace(" - התאחדות טהרת הכהנים", "").strip(), "u": DRIVE_URL.format(fid)})
    lib += [{"g": "אתרים ויישומים של ההתאחדות", "t": t, "u": u} for t, u in [
        ("אתר המדריך לכהנים", "https://hakohanim.org/"), ("ניווט לכהנים — באתר (מסלול שעוקף אזורים אסורים)", "https://gps.hakohanim.org/"),
        ("ניווט לכהנים — אפליקציה לאנדרואיד", "https://play.google.com/store/apps/details?id=gps.hakohanim.org"),
        ("מידע טיסות לכהנים — זמן אמת", "https://flights.hakohanim.org/"),
        ("כל החומרים בתיקיית Google Drive של ההתאחדות", "https://drive.google.com/drive/folders/1I4LBIeZRHuUfdAwT8WDYJa-24R5sF7Bs")]]
    with open(os.path.join(out, "extra.js"), "w") as f:
        f.write("/* נוצר על ידי kohanim-build/build.py. הערה: בכותרות של קבצים שנוצרים — רק הערת בלוק, בלי גרשיים (בודק החנות נתקע אחרת) */\nwindow.ERUV_EXTRA = " + json.dumps({"library": lib, "abroad": [], "flights": flights}, ensure_ascii=False, separators=(",", ":")) + ";\n")
    missing = [p for p in tree if p not in used and p not in DUPS and not re.search(r"\.(mp4|mov)$", p, re.I)]
    print(f"ערים {len(cities)} · מפות {len(maps)} · חוברות {len(res)} · אזורים {sum(1 for a in areas if a['group']=='areas')} (+{sum(1 for l in lines.values() if l['level']=='A')} שטחי A) · נקודות הפצה {sum(1 for a in areas if a['group']=='dist')} · לא נארזו: {missing}", file=sys.stderr)

if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    main(a[0] if a else os.path.join(HERE, "..", "kohanim"), "--quick" in sys.argv)
