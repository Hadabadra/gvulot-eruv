#!/usr/bin/env python3
"""ממשק האתר (2.3.0): מעתיק את עמודי האתר של מקור החומר לתוך התוסף, כדי שמי שרגיל לאתר יראה אותו בתוך אוצריא בלי אינטרנט.
משותף לשני התוספים (כמו הממשק). הפלט: <plugin>/web.js (window.SITE_WEB) ו-<plugin>/web/img/*.webp.

- עמודים: עמוד הבית, התפריט, וכל קישור פנימי עד עומק --depth. תוכן העמוד בלבד (בלי כותרת/תחתית של וורדפרס), בלי סקריפטים,
  בלי עיצוב ובלי מאפייני style/class — העיצוב הוא של התוסף (צבעי אוצריא בלבד, כדי לעמוד בכללי החנות).
- החומר פעם אחת: קישור או תמונה של מפה/חוברת שכבר בתוסף (לפי pageUrl/imageUrl/url ב-data.js/docs.js) נפתחים במציג של התוסף.
- שאר התמונות נדחסות (‏--img-width, ‏webp) עד --budget-mb; מעבר לתקציב — קישור במקום תמונה. קבצים אחרים וסרטונים — קישור חיצוני (רק עם אינטרנט).
שימוש: python3 tools/build_web.py gvulot-eruv http://hiruv.com/ --name "מוקד העירוב" [--depth 2] [--budget-mb 3]
"""
import argparse, hashlib, html, io, json, os, re, sys, time, urllib.parse, urllib.request
from html.parser import HTMLParser
from PIL import Image

UA = {"User-Agent": "Mozilla/5.0"}
KEEP = {"h1", "h2", "h3", "h4", "h5", "h6", "p", "br", "ul", "ol", "li", "a", "img", "strong", "b", "em", "i", "u", "table", "thead", "tbody", "tr",
        "td", "th", "blockquote", "figure", "figcaption", "hr", "div", "section", "span", "small", "sup", "sub"}
DROP = {"script", "style", "noscript", "svg", "form", "button", "input", "select", "textarea", "nav", "iframe", "video", "audio", "object", "template", "head"}
SKIP_URL = re.compile(r"/(feed|wp-json|wp-admin|wp-login|xmlrpc|comments|tag|category|author|page/\d+|cart|checkout|my-account)(/|$)|\?|#", re.I)
FILE_EXT = re.compile(r"\.(pdf|jpe?g|png|gif|webp|docx?|xlsx?|zip|mp4|mp3|mov)$", re.I)

def get(u, tries=3):
    u = urllib.parse.quote(u, safe=":/?&=%#,+;@!$*'()~")   # כתובות בעברית/עם רווחים
    for i in range(tries):
        try: return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60).read()
        except Exception as e:
            if i == tries - 1: raise
            time.sleep(4 * (i + 1))

def unwrap(u):
    """תמונות שעוברות דרך שירות דחיסה (shortpixel וכד') — הכתובת המקורית."""
    return re.sub(r"^https?://sp-ao\.shortpixel\.ai/client/[^/]*/", "", u or "")

def norm(u):
    """כתובת להשוואה: בלי פרוטוקול/www/סלאש בסוף, מפוענחת."""
    u = urllib.parse.unquote(html.unescape(u or "")).strip().replace("‏", "").replace("‎", "")
    m = re.search(r"drive\.google\.com/(?:file/d/|open\?id=|uc\?(?:export=\w+&)?id=)([\w-]{20,})", u)
    if m: return "drive:" + m.group(1)   # קבצי Google Drive — לפי המזהה, בלי פרמטרים
    u = re.sub(r"^https?://(www\.)?", "", u, flags=re.I).split("#")[0]
    return u.rstrip("/").lower()

def content_of(s):
    """תוכן העמוד: Elementor (wp-page/wp-post/single) או <main>/<article>, אחרת <body>."""
    for t in ("wp-page", "wp-post", "single-post", "single-page", "single"):
        i = s.find(f'data-elementor-type="{t}"')
        if i >= 0:
            j = s.find('data-elementor-type="footer"', i)
            return s[s.rfind("<", 0, i):j if j > 0 else len(s)]
    for tag in ("main", "article"):
        m = re.search(rf"<{tag}\b.*?</{tag}>", s, re.S | re.I)
        if m: return m.group(0)
    m = re.search(r"<body\b.*?</body>", s, re.S | re.I)
    return m.group(0) if m else s

class Clean(HTMLParser):
    def __init__(self, on_a, on_img):
        super().__init__(convert_charrefs=True); self.out = []; self.skip = 0; self.on_a, self.on_img = on_a, on_img
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in DROP:
            if tag == "iframe" and a.get("src") and not self.skip:   # סרטון/תוכן מוטמע → קישור חיצוני
                self.out.append(f'<p><a data-url="{html.escape(a["src"])}">תוכן מוטמע מהאתר (נפתח בדפדפן כשיש אינטרנט)</a></p>')
            if tag not in ("br", "input", "img"): self.skip += 1
            return
        if self.skip or tag not in KEEP: return
        if tag == "img":
            src = a.get("data-lazy-src") or a.get("data-src") or a.get("src") or ""
            if src and not src.startswith("data:"): self.out.append(self.on_img(src, a.get("alt") or ""))
            return
        if tag == "a":
            self.out.append(self.on_a(a.get("href") or "")); return
        if tag == "br" or tag == "hr": self.out.append(f"<{tag}>"); return
        keep = " ".join(f'{k}="{html.escape(v)}"' for k, v in attrs if k in ("colspan", "rowspan") and v)
        self.out.append(f"<{'div' if tag in ('section',) else tag}{' ' + keep if keep else ''}>")
    def handle_endtag(self, tag):
        if tag in DROP:
            if tag not in ("br", "input", "img"): self.skip = max(0, self.skip - 1)
            return
        if self.skip or tag not in KEEP or tag in ("img", "br", "hr"): return
        self.out.append("</a>" if tag == "a" else f"</{'div' if tag == 'section' else tag}>")
    def handle_data(self, d):
        if not self.skip: self.out.append(html.escape(d, quote=False))

def tidy(h):
    h = re.sub(r"[ \t\r\n]+", " ", h)
    for _ in range(6):
        h = re.sub(r"<(div|span|p|strong|b|em|i|li|ul|figure|h\d)>\s*</\1>", "", h)
        h = re.sub(r"<div>\s*(<div>.*?</div>)\s*</div>", r"\1", h)
        h = re.sub(r"<span>(.*?)</span>", r"\1", h)
    return h.strip()

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("plugin"); ap.add_argument("start"); ap.add_argument("--name", required=True)
    ap.add_argument("--depth", type=int, default=2); ap.add_argument("--max-pages", type=int, default=80)
    ap.add_argument("--route", action="append", default=[], help='קישור לכלי שכבר בתוסף: "תחילת-כתובת=מאפיין:ערך", למשל "flights.hakohanim.org=view:abroad"')
    ap.add_argument("--budget-mb", type=float, default=3.0); ap.add_argument("--img-width", type=int, default=900)
    o = ap.parse_args()
    plug = o.plugin; host = urllib.parse.urlparse(o.start).netloc.replace("www.", "")
    def load(f):
        p = os.path.join(plug, f)
        if not os.path.exists(p): return None
        t = open(p, encoding="utf8").read(); return json.loads(t[t.index("=", t.index("window.")) + 1:].strip().rstrip(";"))
    D, DOCS = load("data.js") or {}, load("docs.js") or []
    local = {}   # כתובת באתר ← חומר שכבר בתוסף
    for m in D.get("maps", []):
        for k in ("imageUrl", "pageUrl"):
            if m.get(k): local[norm(m[k])] = ("map", m["id"])
        if m.get("imageUrl"): local.setdefault("file:" + os.path.basename(norm(m["imageUrl"])), ("map", m["id"]))
    for d in DOCS:
        if d.get("url"): local[norm(d["url"])] = ("doc", d["id"]); local.setdefault("file:" + os.path.basename(norm(d["url"])), ("doc", d["id"]))
    def is_page(u):
        p = urllib.parse.urlparse(u)
        return p.netloc.replace("www.", "") == host and not FILE_EXT.search(p.path) and not SKIP_URL.search(u)
    pid = lambda u: "p" + hashlib.sha1(norm(u).encode()).hexdigest()[:7]
    # ── סריקה ──
    raw, queue, seen, nav = {}, [(o.start, 0)], set(), []
    while queue and len(raw) < o.max_pages:
        u, dep = queue.pop(0)
        if norm(u) in seen: continue
        seen.add(norm(u))
        try: s = get(u if u.endswith("/") else u + "/").decode("utf8", "replace")
        except Exception as e: print("לא ירד:", urllib.parse.unquote(u), e, file=sys.stderr); continue
        raw[pid(u)] = (u, s)
        if not nav:   # התפריט הראשי — מהעמוד הראשון
            hd = s[:s.find('data-elementor-type="wp-page"')] if 'data-elementor-type="wp-page"' in s else s[:s.find("<main")]
            for href, t in re.findall(r'<a[^>]+href="([^"]+)"[^>]*class="[^"]*(?:elementor-item|menu-link|nav-link)[^"]*"[^>]*>(.*?)</a>', hd, re.S):
                t = html.unescape(re.sub(r"<[^>]+>", "", t)).strip(); href = urllib.parse.urljoin(u, html.unescape(href))
                if t and is_page(href) and all(n[1] != t for n in nav): nav.append((href, t))
            for href, _ in nav: queue.append((href, 1))
        if dep < o.depth:
            for href in re.findall(r'href="([^"]+)"', content_of(s)):
                href = urllib.parse.urljoin(u, html.unescape(href))
                if is_page(href) and norm(href) not in seen: queue.append((href, dep + 1))
    ids = {norm(u): k for k, (u, _) in raw.items()}
    # ── ניקוי ותמונות ──
    imgdir = os.path.join(plug, "web", "img"); os.makedirs(imgdir, exist_ok=True)
    for f in os.listdir(imgdir): os.remove(os.path.join(imgdir, f))
    used = [0]; cache = {}; stats = {"local": 0, "img": 0, "noimg": 0, "ext": 0}
    def find_local(u):
        n = norm(u); return local.get(n) or local.get("file:" + os.path.basename(n))
    def on_a(href):
        href = html.unescape(href).strip()
        if not href or href.startswith(("#", "javascript:")): return "<a>"
        if href.startswith("tel:"): return f'<a data-phone="{html.escape(href[4:])}">'
        if href.startswith("mailto:"): return f'<a data-url="{html.escape(href)}">'
        u = unwrap(urllib.parse.urljoin(base[0], href))
        for r in o.route:
            k, v = r.split("=", 1); a, val = v.split(":", 1)
            if norm(u).startswith(norm(k)): stats["local"] += 1; return f'<a data-{a}="{html.escape(val)}">'
        L = find_local(re.sub(r"-\d+x\d+(\.\w+)$", r"\1", u))
        if L: stats["local"] += 1; return f'<a data-{"open-map" if L[0] == "map" else "doc"}="{L[1]}">'
        if norm(u) in ids: return f'<a data-webpage="{ids[norm(u)]}">'
        stats["ext"] += 1; return f'<a data-url="{html.escape(u)}" title="נפתח בדפדפן כשיש אינטרנט">'
    def on_img(src, alt):
        u = unwrap(urllib.parse.urljoin(base[0], html.unescape(src))); L = find_local(re.sub(r"-\d+x\d+(\.\w+)$", r"\1", u))
        if L and L[0] == "map": stats["local"] += 1; return f'<img src="maps/{L[1]}.t.webp" alt="{html.escape(alt)}" data-open-map="{L[1]}">'
        if L and L[0] == "doc": stats["local"] += 1; return f'<img src="docs/{L[1]}/001.t.webp" alt="{html.escape(alt)}" data-doc="{L[1]}">'
        if u in cache: return cache[u]
        try:
            im = Image.open(io.BytesIO(get(u))); im = im.convert("RGBA" if im.mode in ("RGBA", "LA", "P") else "RGB")
            if im.width < 40 or im.height < 40: cache[u] = ""; return ""   # אייקונים קטנטנים
            if im.width > o.img_width: im = im.resize((o.img_width, round(im.height * o.img_width / im.width)), Image.LANCZOS)
            b = io.BytesIO(); im.save(b, "WEBP", quality=50, method=6); b = b.getvalue()
            if used[0] + len(b) > o.budget_mb * 1048576: raise RuntimeError("תקציב")
            name = hashlib.sha1(u.encode()).hexdigest()[:10] + ".webp"; open(os.path.join(imgdir, name), "wb").write(b); used[0] += len(b)
            stats["img"] += 1; cache[u] = f'<img src="web/img/{name}" alt="{html.escape(alt)}" loading="lazy">'
        except Exception:
            stats["noimg"] += 1; cache[u] = f'<a data-url="{html.escape(u)}" class="web-noimg">🖼 {html.escape(alt or "תמונה מהאתר")} (כשיש אינטרנט)</a>'
        return cache[u]
    pages, base = {}, [""]
    for k, (u, s) in raw.items():
        base[0] = u; c = Clean(on_a, on_img); c.feed(content_of(s)); c.close()
        t = re.findall(r"<title>(.*?)</title>", s, re.S); t = html.unescape(t[0]).strip() if t else ""
        t = re.split(r"\s+[–|-]\s+", t)[0].strip() if " – " in t or " | " in t else t
        h = tidy("".join(c.out))
        # גלריות (תמונה כרקע): קישור ריק לקובץ תמונה ← התמונה עצמה
        h = re.sub(r'<a data-url="([^"]+\.(?:jpe?g|png|gif|webp))"[^>]*>\s*</a>', lambda m: on_img(html.unescape(m.group(1)), ""), h, flags=re.I)
        pages[k] = {"t": t, "u": u, "h": h}
    logo = ""
    m = re.search(r'data-elementor-type="header".*?<img[^>]+src="([^"]+)"', raw[pid(o.start)][1], re.S)
    if m:
        base[0] = o.start; x = on_img(m.group(1), o.name); mm = re.search(r'src="([^"]+)"', x); logo = mm.group(1) if mm else ""
    out = {"name": o.name, "url": o.start, "built": time.strftime("%Y-%m-%d"), "home": pid(o.start), "logo": logo,
           "nav": [[ids[norm(u)], t] for u, t in nav if norm(u) in ids], "pages": pages}
    with open(os.path.join(plug, "web.js"), "w", encoding="utf8") as f:   # כותרת: הערת בלוק בלי גרשיים (בודק החנות)
        f.write("/* ממשק האתר: עותק של עמודי " + o.start + " בתוך התוסף. נוצר על ידי tools/build_web.py — לא לערוך ידנית */\nwindow.SITE_WEB = " +
                json.dumps(out, ensure_ascii=False, separators=(",", ":")) + ";\n")
    print(f"{len(pages)} עמודים · תמונות {stats['img']} ({used[0] / 1048576:.1f}MB) · חומר מהתוסף {stats['local']} · קישורים חיצוניים {stats['ext']} · תמונות שלא נכנסו {stats['noimg']}", file=sys.stderr)

if __name__ == "__main__":
    main()
