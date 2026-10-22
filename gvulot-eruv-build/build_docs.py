#!/usr/bin/env python3
"""ממיר את החוברות והמאמרים של מוקד העירוב (באישורם) לדפי תמונה בתוך התוסף.
קלט: raw/docs/*.pdf (מורדים ידנית — ראו DOCS למטה)
פלט: <plugin>/docs/<id>/NNN.webp + NNN.t.webp, ו-<plugin>/docs.js (window.ERUV_DOCS)
שימוש: python3 build_docs.py ../gvulot-eruv
"""
import json, os, subprocess, sys, glob, tempfile, shutil
from PIL import Image

W, Q, TW = 1500, 55, 150
# id, קובץ, כותרת, סוג, ערים (לשונית "תחום שבת" בעיר), מקור
DOCS = [
    ("derech-jlm", "derech-jlm.pdf", "דרך התחומין — ירושלים", "booklet", ["ירושלים"],
     "http://hiruv.com/wp-content/uploads/2018/11/דרך-התחומין-ירושלים-מהדורה-חדשה-1.pdf"),
    ("derech-ab", "derech-ab.pdf", "דרך התחומין א–ב — גוש דן, בתי החולים איכילוב ותל השומר, מודיעין עילית, מירון, חפץ חיים, אופקים", "booklet",
     ["בני ברק", "פתח תקוה", "אלעד", "תל אביב", "רמת גן", "מודיעין עילית", "אופקים", "חפץ חיים", "מירון"],
     "http://hiruv.com/wp-content/uploads/2018/11/דרך-התחומין-א-ב-1.pdf"),
    ("nofesh", "nofesh.pdf", "המדריך לנופש — עירובין בצימרים ובמושבים", "booklet", [],
     "http://hiruv.com/wp-content/uploads/2018/11/מדריך-לנופש.pdf"),
    ("techum-ashdod", "techum-ashdod.pdf", "אשדוד — תחום שבת", "techum", ["אשדוד"], "http://hiruv.com/אשדוד-תחום-שבת/"),
    ("techum-beit-shemesh", "techum-beit-shemesh.pdf", "בית שמש — תחום שבת", "techum", ["בית שמש"], "http://hiruv.com/בית-שמש-תחום-שבת/"),
    ("techum-beitar", "techum-beitar.pdf", "ביתר עילית — תחום שבת", "techum", ["ביתר"], "http://hiruv.com/ביתר-עילית-תחום-שבת/"),
    ("techum-elad", "techum-elad.pdf", "אלעד — תחום שבת", "techum", ["אלעד"], "http://hiruv.com/אלעד/"),
    ("techum-ofakim", "techum-ofakim.pdf", "אופקים — תחום שבת", "techum", ["אופקים"], "http://hiruv.com/אופקים/"),
    ("techum-beit-chilkiya", "techum-beit-chilkiya.pdf", "בית חלקיה — תחום שבת", "techum", ["בית חלקיה"], "http://hiruv.com/בית-חלקיה-תחום-שבת/"),
]
# תקציר מתוך דפי האתר (טקסט, לא תמונה) — רק היכן שהאתר פירט
SUMMARY = {
    "techum-elad": {"near": "נחשונים, הטיילת בכביש העוקף (כביש פרוש)", "eruv": "לא קיים", "far": "פתח תקווה, ראש העין, נחלים"},
    "techum-beit-chilkiya": {"intro": "בית חלקיה נמצאת בין יד בנימין לחפץ חיים ומחברת ביניהם: מי ששובת בה מותר בשניהם.",
                             "near": "יד בנימין, חפץ חיים, חלק מגני טל", "eruv": "החלק הנוסף של גני טל", "far": "יסודות, בני ראם"},
}

def main(out):
    src = os.path.join(os.path.dirname(__file__), "raw", "docs")
    res = []
    for did, fn, title, kind, cities, url in DOCS:
        pdf = os.path.join(src, fn)
        if not os.path.exists(pdf):
            print("חסר", pdf, file=sys.stderr); continue
        dst = os.path.join(out, "docs", did); shutil.rmtree(dst, ignore_errors=True); os.makedirs(dst)
        tmp = tempfile.mkdtemp()
        subprocess.run(["pdftoppm", "-r", "150", "-png", pdf, f"{tmp}/p"], check=True)
        pages = sorted(glob.glob(f"{tmp}/p-*.png"))
        dims = []
        for i, p in enumerate(pages, 1):
            im = Image.open(p).convert("RGB")
            if im.width > W: im = im.resize((W, round(im.height * W / im.width)), Image.LANCZOS)
            im.save(f"{dst}/{i:03d}.webp", "WEBP", quality=Q, method=5)
            t = im.copy(); t.thumbnail((TW, TW * 2)); t.save(f"{dst}/{i:03d}.t.webp", "WEBP", quality=50, method=5)
            dims.append([im.width, im.height])
        shutil.rmtree(tmp)
        res.append({"id": did, "title": title, "kind": kind, "cities": cities, "url": url,
                    "pages": len(pages), "dims": dims, **({"summary": SUMMARY[did]} if did in SUMMARY else {})})
        print(title, len(pages), file=sys.stderr)
    with open(os.path.join(out, "docs.js"), "w") as f:
        f.write("window.ERUV_DOCS = " + json.dumps(res, ensure_ascii=False, separators=(",", ":")) + ";\n")

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "../gvulot-eruv")
