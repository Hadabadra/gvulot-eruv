#!/usr/bin/env python3
"""עירובין בחו"ל מתוך המדריך של eruv.org (באישורם, 22.10.2026).
מוריד את רשימת העירובין (WP REST: wpbdp_listing + wpbdp_category) ואת דף כל עירוב, ומוציא:
שם, ארץ/מדינה, אתר, קישור למפה, טלפון, אימייל, ורב/הערות אם יש.
פלט: raw/eruvorg.json (מאגר גולמי לשימוש build_extra.py).
שימוש: python3 build_eruvorg.py            (מוריד מחדש)
       python3 build_eruvorg.py --parse    (רק מנתח את raw/eruvorg/*.html הקיימים)
"""
import html, json, os, re, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")
DIR = os.path.join(RAW, "eruvorg")
API = "https://www.eruv.org/wp-json/wp/v2/"


def get(url):
    r = subprocess.run(["curl", "-sSL", "--max-time", "60", "-A", "gvulot-eruv (Otzaria plugin; approved use)", url], capture_output=True)
    return r.stdout.decode("utf-8", "replace")


def fetch():
    os.makedirs(DIR, exist_ok=True)
    listings, page = [], 1
    while True:
        d = json.loads(get(f"{API}wpbdp_listing?per_page=100&page={page}&_fields=id,link,title,wpbdp_category"))
        if not isinstance(d, list) or not d: break
        listings += d; page += 1
        if len(d) < 100: break
    cats = json.loads(get(f"{API}wpbdp_category?per_page=100&_fields=id,name,parent"))
    json.dump({"listings": listings, "cats": cats}, open(os.path.join(DIR, "index.json"), "w"), ensure_ascii=False)
    for i, x in enumerate(listings):
        fn = os.path.join(DIR, f"{x['id']}.html")
        if not os.path.exists(fn):
            open(fn, "w").write(get(x["link"])); time.sleep(0.4)
        print(i + 1, len(listings), file=sys.stderr, end="\r")


FIELD = re.compile(r'field-display field-value wpbdp-field-([a-z_0-9]+) [^"]*"\s*>\s*<span class="field-label">(.*?)</span>\s*<div class="value">(.*?)</div>', re.S)


def text(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()


def parse():
    ix = json.load(open(os.path.join(DIR, "index.json")))
    cats = {c["id"]: c for c in ix["cats"]}
    out = []
    for x in ix["listings"]:
        p = open(os.path.join(DIR, f"{x['id']}.html"), encoding="utf-8", errors="replace").read()
        f = {}
        for m in FIELD.finditer(p):
            key, val = m.group(1), m.group(3)
            href = re.search(r'href="([^"]+)"', val)
            f[key] = (href.group(1) if href and not href.group(1).startswith("mailto:") else text(val))
            mail = re.search(r'mailto:([^"?]+)', val)
            if mail: f[key] = mail.group(1)
        # ארץ/מדינה מהקטגוריה: עלה = מדינה (או ארץ), ההורה = ארץ/יבשת
        path = []
        for cid in x.get("wpbdp_category", [])[:1]:
            c = cats.get(cid)
            while c: path.append(c["name"]); c = cats.get(c["parent"])
        out.append({"id": x["id"], "name": html.unescape(x["title"]["rendered"]), "link": x["link"], "cat": path, "f": f})
    json.dump(out, open(os.path.join(RAW, "eruvorg.json"), "w"), ensure_ascii=False, indent=1)
    keys = {}
    for o in out:
        for k in o["f"]: keys[k] = keys.get(k, 0) + 1
    print(len(out), "eruvin;", keys, file=sys.stderr)


if __name__ == "__main__":
    if "--parse" not in sys.argv: fetch()
    parse()
