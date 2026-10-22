#!/usr/bin/env python3
"""אורז את החוברות והמאמרים של מוקד העירוב (באישורם) בתוך התוסף: קובץ ה-PDF המקורי (מוצג ב-pdf.js),
ותמונה ממוזערת קטנה לכל עמוד (לרשימת העמודים ולכרטיסים).
קלט: raw/docs/*.pdf (מורדים לפי DOCS למטה)
פלט: <plugin>/docs/<id>.pdf, <plugin>/docs/<id>/NNN.t.webp, ו-<plugin>/docs.js (window.ERUV_DOCS)
שימוש: python3 build_docs.py ../gvulot-eruv
"""
import json, os, subprocess, sys, glob, tempfile, shutil
from PIL import Image

TW = 120
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
        [os.remove(x) for x in (dst + ".pdf", dst + ".pdf.js") if os.path.exists(x)]
        tmp = tempfile.mkdtemp()
        subprocess.run(["pdftoppm", "-r", "30", "-png", pdf, f"{tmp}/p"], check=True)
        pages = sorted(glob.glob(f"{tmp}/p-*.png"))
        dims = []
        for i, p in enumerate(pages, 1):
            im = Image.open(p).convert("RGB")
            dims.append([1000, round(1000 * im.height / im.width)])
            im.thumbnail((TW, TW * 2), Image.LANCZOS)
            im.save(f"{dst}/{i:03d}.t.webp", "WEBP", quality=45, method=6)
        # באוצריא pdf.js לא יכול לקרוא קובץ file:// (MissingPDFException), ולכן ה-PDF נארז כ-base64 בקובץ js שנטען בתג script
        import base64
        with open(os.path.join(out, "docs", did + ".pdf.js"), "w") as f:
            # שורות קצרות (4000 תווים) — מחרוזת אחת ענקית גרמה ל-"Stack Overflow" בהתקנה באוצריא
            b = base64.b64encode(open(pdf, "rb").read()).decode()
            f.write("(window.ERUV_PDF=window.ERUV_PDF||{})[" + json.dumps(did) + "]=[\n")
            f.write(",\n".join('"' + b[i:i + 4000] + '"' for i in range(0, len(b), 4000)))
            f.write("\n].join('');\n")
        shutil.rmtree(tmp)
        res.append({"id": did, "title": title, "kind": kind, "cities": cities, "url": url,
                    "pages": len(pages), "dims": dims, **({"summary": SUMMARY[did]} if did in SUMMARY else {})})
        print(title, len(pages), file=sys.stderr)
    with open(os.path.join(out, "docs.js"), "w") as f:
        f.write("window.ERUV_DOCS = " + json.dumps(res, ensure_ascii=False, separators=(",", ":")) + ";\n")

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "../gvulot-eruv")
