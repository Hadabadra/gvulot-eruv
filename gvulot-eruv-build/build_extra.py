#!/usr/bin/env python3
"""נתונים נוספים לתוסף: ספריית העירובין של מוקד העירוב (קישורים), ועירובין בחו"ל (מתוך ויקיפדיה, CC BY-SA).
קלט: raw/books1.html, raw/books2.html (דפי "מאגר ספרים" ו"חוברות וספרים" באתר המוקד),
     raw/wiki-eruvin.txt (https://en.wikipedia.org/w/index.php?title=List_of_places_with_eruvin&action=raw)
פלט: <plugin>/extra.js  (window.ERUV_EXTRA = {library, abroad})
"""
import re, html, json, sys, os, urllib.parse

R = os.path.join(os.path.dirname(__file__), "raw")

def library():
    out, seen = [], set()
    for fn, group in (("books2.html", "חוברות בהלכות אקטואליות"), ("books1.html", "ספרים תורניים בעירובין")):
        p = open(os.path.join(R, fn), encoding="utf-8", errors="replace").read()
        for m in re.finditer(r'<a[^>]+href="([^"]+\.pdf)"[^>]*>(.*?)</a>', p, re.S):
            url = urllib.parse.unquote(m.group(1)).strip()
            if url in seen: continue
            seen.add(url)
            t = html.unescape(re.sub("<[^>]+>", "", m.group(2))).strip()
            if t in ("הורדה", "גליונות", "") or len(t) < 3:
                t = re.sub(r"[-_]+", " ", url.rsplit("/", 1)[1][:-4]).strip()
            t = re.sub(r"\s+", " ", t.replace("\t", " "))
            out.append({"g": group, "t": t, "u": url})
    return out

HE = {"Argentina": "ארגנטינה", "Australia": "אוסטרליה", "Austria": "אוסטריה", "Belarus": "בלארוס", "Belgium": "בלגיה",
      "Brazil": "ברזיל", "Canada": "קנדה", "Chile": "צ'ילה", "France": "צרפת", "Gibraltar": "גיברלטר", "Hong Kong": "הונג קונג",
      "Hungary": "הונגריה", "Italy": "איטליה", "Lithuania": "ליטא", "Mexico": "מקסיקו", "Netherlands": "הולנד", "Poland": "פולין",
      "Portugal": "פורטוגל", "Russia": "רוסיה", "Slovakia": "סלובקיה", "South Africa": "דרום אפריקה", "Spain": "ספרד",
      "Switzerland": "שווייץ", "Ukraine": "אוקראינה", "United Kingdom": "בריטניה", "United States": "ארצות הברית", "Uruguay": "אורוגוואי"}
# הוסרו לפי בקשת משתמש מחו"ל בפורום (shmuel, 22.10.2026): מקור שאינו חרדי
REMOVE_URLS = {"http://darcheinoammn.org/information_links/information_links.htm"}
# נוספו לפי אותו משתמש (מקורות עירובין בחו"ל)
ADD = [
    {"c": "United States", "ch": "ארצות הברית", "r": "New York", "p": "Monsey", "in": "", "u": "https://eiruvofmonsey.org/"},
    {"c": "United States", "ch": "ארצות הברית", "r": "New York", "p": "Rockland County", "in": "", "u": "https://www.rocklanderuv.org/copy-of-about-us"},
    {"c": "United States", "ch": "ארצות הברית", "r": "New Jersey", "p": "Lakewood (The Lakewood Luach)", "in": "", "u": "https://thelakewoodluach.com/eruv-info"},
    {"c": "United States", "ch": "ארצות הברית", "r": "New Jersey", "p": "Lakewood (new map, Sparks)", "in": "", "u": "https://sparksofanation.com/sparks/reader-submitted-a-new-eruv-map-for-a-prime-area-of-lakewood-not-just-a-geographic-depiction-but-a-sign-of-the-growth-and-flourishing-of-torah-neighborhoods-a-celebration-of-yiddishkeit-on-the-ris/"},
    {"c": "United States", "ch": "ארצות הברית", "r": "", "p": "Eruv Finder (US directory)", "in": "", "u": "https://eruvfinder.com/"},
]
# שיקגו: לפי מועצת הרבנים של שיקגו (cRc, crcweb.org/guide_chicago.php) — אתר וקו סטטוס לכל עירוב.
# מחליף את שורות ויקיפדיה של אילינוי (בהן קישורים מתים כמו geocities). נבדק 22.10.2026.
CRC = "https://crcweb.org/guide_chicago.php"
CHICAGO = [
    {"p": "West Rogers Park (Chicago)", "u": "http://chicagoeruv.tripod.com/", "ph": "773-743-7882"},
    {"p": "Lincolnwood – Peterson Park", "u": CRC, "ph": "847-677-3788"},
    {"p": "Skokie", "u": "http://www.skokieeruv.com/", "ph": "847-679-3788"},
    {"p": "Lakeview (Lakefront)", "u": "https://twitter.com/lakefronteruv", "ph": "773-248-9200"},
    {"p": "Glenbrook (Glenview/Northbrook)", "u": "http://www.glenbrookcommunityeruv.com", "ph": ""},
    {"p": "Buffalo Grove", "u": "http://www.bgeruv.com", "ph": "773-771-2613"},
    {"p": "Highland Park", "u": "http://www.hp-eruv.com/", "ph": "773-415-4940"},
    {"p": "Hyde Park / South Side", "u": "https://southsideeruv.org/", "ph": ""},
    {"p": "Evanston (בבנייה, צפי 2028)", "u": "https://evanstoneruv.org/", "ph": ""},
    {"p": "מפות העירובין של שיקגו (cRc)", "u": "https://www.crcweb.org/eruv%20maps.pdf", "ph": ""},
]
KEEP_IL = {"Champaign-Urbana"}

SKIP = {"Israel", "Palestine (Israeli settlements)", "Syria (Israeli settlements)", "References", "External links"}

def clean_name(s):
    s = re.sub(r"<ref[^>]*/>|<ref[^>]*>.*?</ref>", "", s, flags=re.S)
    s = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]+)\]\]", r"\1", s)
    s = re.sub(r"\{\{[^}]*\}\}", "", s)
    s = re.sub(r"'{2,}", "", s)
    return re.sub(r"\s+", " ", s).strip(" :;,-—")

def abroad():
    txt = open(os.path.join(R, "wiki-eruvin.txt"), encoding="utf-8").read()
    out, country, region = [], None, ""
    for line in txt.splitlines():
        h = re.match(r"^(=+)\s*(.*?)\s*\1\s*$", line)
        if h:
            lvl, name = len(h.group(1)), h.group(2)
            if lvl == 2: country, region = name, ""
            else: region = clean_name(name)
            continue
        if not country or country in SKIP: continue
        if not (line.startswith("*") or (line and line[0] != "{" and "<ref" in line and line.startswith("[["))): continue
        depth = len(line) - len(line.lstrip("*"))
        ref = re.search(r"\|\s*url\s*=\s*([^\s|}]+)", line) or re.search(r"\[(https?://[^\s\]]+)", line)
        name = clean_name(line.lstrip("*"))
        if not name or len(name) > 70: continue
        if depth >= 2 and out and out[-1]["c"] == country and not out[-1].get("sub"):
            parent = out[-1]["p"] if depth == 2 else out[-1]["p"]
        else:
            parent = ""
        out.append({"c": country, "ch": HE.get(country.strip(), country.strip()), "r": region,
                    "p": name, "in": parent if depth >= 2 else "", "u": ref.group(1) if ref else ""})
    return out

def patch_chicago(ab):
    il = [{"c": "United States", "ch": "ארצות הברית", "r": "Illinois", "in": "", **x} for x in CHICAGO]
    return [a for a in ab if a["r"] != "Illinois" or a["p"] in KEEP_IL] + il


def main(plugin):
    lib, ab = library(), abroad()
    ab = patch_chicago([a for a in ab if a["u"] not in REMOVE_URLS] + ADD)
    with open(os.path.join(plugin, "extra.js"), "w", encoding="utf-8") as f:
        f.write("window.ERUV_EXTRA = " + json.dumps({"library": lib, "abroad": ab}, ensure_ascii=False, separators=(",", ":")) + ";\n")
    print(len(lib), "books;", len(ab), "places abroad in", len({a['c'] for a in ab}), "countries", file=sys.stderr)

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "../gvulot-eruv")
