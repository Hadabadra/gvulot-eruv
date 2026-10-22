#!/usr/bin/env python3
"""עדכון אוטומטי (מופעל מ-.github/workflows/eruv-auto-update.yml, אפשר גם ידנית).
1. סורק מחדש את מקורות הנתונים: hiruv.com (מפות, אחראים, ספרייה) וויקיפדיה (עירובין בחו"ל).
2. מחשב טביעת אצבע של המקורות ומשווה ל-sources.lock.json.
3. אם משהו השתנה: מוריד תמונות, בונה data.js / extra.js, מעלה גרסת patch (manifest, VERSION, CHANGELOG, README)
   ומדפיס changed=true ל-$GITHUB_OUTPUT. אחרת changed=false ושום קובץ לא משתנה.
שימוש: cd gvulot-eruv-build && python3 auto_update.py ../gvulot-eruv
"""
import hashlib, html, json, os, re, subprocess, sys, datetime, urllib.parse

PLUG = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "../gvulot-eruv")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LOCK = os.path.join(HERE, "sources.lock.json")
RAW = os.path.join(HERE, "raw")
WIKI = "https://en.wikipedia.org/w/index.php?title=List_of_places_with_eruvin&action=raw"
# דפי הספרייה באתר המוקד מזוהים לפי טקסט הקישור בדף הבית
BOOK_PAGES = (("books1.html", "מאגר ספרים"), ("books2.html", "חוברות וספרים"))


def run(*cmd):
    print("$", " ".join(cmd), file=sys.stderr)
    subprocess.run(cmd, cwd=HERE, check=True)


def get(url):
    return subprocess.run(["curl", "-sSL", "--max-time", "90", url], capture_output=True).stdout.decode("utf-8", "replace")


def sha(x):
    return hashlib.sha256(json.dumps(x, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:16]


def output(k, v):
    print(f"{k}={v}")
    if os.environ.get("GITHUB_OUTPUT"):
        open(os.environ["GITHUB_OUTPUT"], "a").write(f"{k}={v}\n")


def fetch_sources():
    os.makedirs(RAW, exist_ok=True)
    run("python3", "scrape.py", "raw")
    run("python3", "parse_resp.py")
    home = get("http://hiruv.com/")
    have_books = True
    for fn, label in BOOK_PAGES:
        m = re.search(r'<a[^>]+href="(http://hiruv\.com/[^"]+)"[^>]*>\s*(?:<[^>]+>\s*)*' + re.escape(label), home)
        if m:
            open(os.path.join(RAW, fn), "w").write(get(m.group(1)))
        else:
            have_books = False
            print("לא נמצא דף", label, "— הספרייה לא תתעדכן", file=sys.stderr)
    wiki = get(WIKI)
    if len(wiki) > 5000:
        open(os.path.join(RAW, "wiki-eruvin.txt"), "w").write(wiki)
    return have_books and len(wiki) > 5000


def fingerprint(with_extra):
    idx = json.load(open(os.path.join(RAW, "index.json")))
    resp = json.load(open(os.path.join(RAW, "responsible.json")))
    fp = {"maps": sha([[p["url"], p["title"], sorted(p["images"])] for p in idx]), "areas": sha(resp),
          "n_pages": len(idx), "n_areas": len(resp)}
    if with_extra:
        books = "".join(sorted(re.findall(r'href="([^"]+\.pdf)"', open(os.path.join(RAW, "books1.html")).read()
                                          + open(os.path.join(RAW, "books2.html")).read())))
        fp["library"] = sha(books)
        fp["abroad"] = sha(open(os.path.join(RAW, "wiki-eruvin.txt")).read())
    return fp


def bump(changed_parts):
    mf = os.path.join(PLUG, "manifest.json")
    m = json.load(open(mf))
    a, b, c = map(int, m["version"].split("."))
    v = f"{a}.{b}.{c + 1}"
    m["version"] = v
    json.dump(m, open(mf, "w"), ensure_ascii=False, indent=2)
    open(mf, "a").write("\n")
    he = {"maps": "מפות", "areas": "רשימת האחראים", "library": "ספריית העירובין", "abroad": 'עירובין בחו"ל'}
    what = ", ".join(he[k] for k in changed_parts if k in he)
    line = f"עדכון אוטומטי מהמקורות ({datetime.date.today().isoformat()}): {what}"
    app = os.path.join(PLUG, "app.js")
    s = open(app).read()
    s = re.sub(r"const VERSION = '[^']+';", f"const VERSION = '{v}';", s)
    s = s.replace("  const CHANGELOG = [\n", f"  const CHANGELOG = [\n    ['{v}', ['{line}']],\n", 1)
    open(app, "w").write(s)
    rd = os.path.join(ROOT, "README.md")
    r = open(rd).read()
    i = r.index("## מה חדש ב-")
    r = r[:i] + f"## מה חדש ב-{v}\n- {line}.\n\n" + r[i:]
    open(rd, "w").write(r)
    return v


def main():
    full = fetch_sources()
    idx = json.load(open(os.path.join(RAW, "index.json")))
    if len(idx) < 30:
        sys.exit(f"נמצאו רק {len(idx)} דפי מפות — כנראה האתר לא זמין. עוצרים בלי לשנות.")
    new = fingerprint(full)
    old = json.load(open(LOCK)) if os.path.exists(LOCK) else {}
    changed = [k for k in ("maps", "areas", "library", "abroad") if k in new and new[k] != old.get(k)]
    if not old:
        # ריצה ראשונה: רק רושמים את המצב הקיים, בלי גרסה
        json.dump(new, open(LOCK, "w"), ensure_ascii=False, indent=1)
        output("changed", "baseline")
        return
    if not changed:
        output("changed", "false")
        return
    if "maps" in changed or "areas" in changed:
        run("python3", "fetch_images.py")
        run("python3", "build_data.py", PLUG)
    if "library" in changed or "abroad" in changed:
        run("python3", "build_extra.py", PLUG)
    json.dump({**old, **new}, open(LOCK, "w"), ensure_ascii=False, indent=1)
    v = bump(changed)
    output("changed", "true")
    output("version", v)


if __name__ == "__main__":
    main()
