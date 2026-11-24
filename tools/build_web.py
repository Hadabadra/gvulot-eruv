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
    def __init__(self, on_a, on_img, keep_style=False):
        super().__init__(convert_charrefs=True); self.out = []; self.skip = 0; self.on_a, self.on_img, self.ks = on_a, on_img, keep_style
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
            if src and not src.startswith("data:"):
                x = self.on_img(src, a.get("alt") or "")
                if self.ks and a.get("class") and x.startswith("<img "): x = x.replace("<img ", f'<img class="{html.escape(a["class"])}" ', 1)
                self.out.append(x)
            return
        if tag == "a":
            self.out.append(self.on_a(a.get("href") or "")); return
        if tag == "br" or tag == "hr": self.out.append(f"<{tag}>"); return
        names = ("colspan", "rowspan", "class", "style", "id", "dir", "align") if self.ks else ("colspan", "rowspan")
        keep = " ".join(f'{k}="{html.escape(v)}"' for k, v in attrs if k in names and v and not (k == "style" and "url(" in v))
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

# ── עיצוב האתר (--site-style) ──
COLOR_RE = re.compile(r"#[0-9a-fA-F]{3,8}\b|\b(?:rgb|rgba|hsl|hsla)\s*\([^)]*\)", re.I)
NAMED = re.compile(r"\b(white|black|red|green|blue|gray|grey|silver|orange|yellow|purple|navy|maroon|teal|olive|lime|aqua|fuchsia|pink|brown|gold|beige|ivory|transparent)\b", re.I)
USED = set()   # מחלקות שמופיעות בעמודים — כלל שמחלקה שלו לא מופיעה בשום עמוד לא נשמר
def scope_sel(sel):
    out = []
    for part in split_top(sel, ","):
        p = part.strip()
        if not p: continue
        if USED and any(c not in USED for c in re.findall(r"\.(-?[_a-zA-Z][\w-]*)", re.sub(r":not\([^)]*\)", "", p))): continue
        p2 = re.sub(r"^(?::root|html)(\s+body)?\b|^body\b", ".site-raw", p)
        out.append(p2 if p2 != p else ".site-raw " + p)
    return ", ".join(out)
def split_top(s, ch):
    out, d, cur = [], 0, ""
    for c in s:
        if c in "([": d += 1
        if c in ")]": d -= 1
        if c == ch and d == 0: out.append(cur); cur = ""
        else: cur += c
    out.append(cur); return out
CNT = [0]; CSS_CTX = {"base": "", "img": "", "n": 0, "bytes": 0}
def css_img(m):
    """תמונת רקע מהאתר → web/img (webp), עד 4MB לכל התמונות של העיצוב."""
    u = m.group(1).strip("'\" ")
    if u.startswith("data:") or not re.search(r"\.(jpe?g|png|webp|gif)(\?|$)", u, re.I) or CSS_CTX["bytes"] > 4 * 1048576: return "none"
    try:
        im = Image.open(io.BytesIO(get(urllib.parse.urljoin(CSS_CTX["base"], unwrap(u)))))
        im = im.convert("RGBA" if im.mode in ("RGBA", "LA", "P") else "RGB")
        if im.width > 1400: im = im.resize((1400, round(im.height * 1400 / im.width)), Image.LANCZOS)
        b = io.BytesIO(); im.save(b, "WEBP", quality=55, method=6); b = b.getvalue()
        name = "css-" + hashlib.sha1(u.encode()).hexdigest()[:10] + ".webp"
        open(os.path.join(CSS_CTX["img"], name), "wb").write(b); CSS_CTX["bytes"] += len(b)
        return f'url("img/{name}")'
    except Exception:
        return "none"
def fix_decls(body):
    out = []
    for d in split_top(body, ";"):
        if ":" not in d: continue
        k, v = d.split(":", 1); k = k.strip(); v = v.strip()
        if not k or k.startswith("--"):
            if k: out.append(f"{k}:{v}")
            continue
        if "url(" in v and "data:" not in v:
            if not re.match(r"background(-image)?$", k.strip().lower()): continue
            v = re.sub(r"url\(([^)]*)\)", css_img, v)
        imp = ""
        if v.lower().endswith("!important"): v, imp = v[:-10].strip(), " !important"
        lk = k.lower()
        # בדיקת העיצוב בחנות: font-family חייב להיות var(--font-*) בלבד (גם var(--e-...),Sans-serif נדחה)
        if "var(" in v and not COLOR_RE.search(v) and not (lk == "font-family" and not re.fullmatch(r"var\(--font-[\w-]+\)", v)):
            out.append(f"{k}:{v}{imp}"); continue
        CNT[0] += 1; n = CNT[0]
        if lk == "font-family": out.append(f"--font-site-{n}:{v};{k}:var(--font-site-{n}){imp}")
        elif COLOR_RE.search(v) or (NAMED.search(v) and re.search(r"color|background|border|outline|fill|stroke|shadow", lk)) or (lk in ("font-size", "border-radius") and "px" in v):
            out.append(f"--color-site-{n}:{v};{k}:var(--color-site-{n}){imp}")
        else: out.append(f"{k}:{v}{imp}")
    return ";".join(out)
def scope_css(css):
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    out, i, n = [], 0, len(css)
    while i < n:
        j = css.find("{", i)
        if j < 0: break
        head = css[i:j].strip()
        d, k = 1, j + 1
        while k < n and d: d += {"{": 1, "}": -1}.get(css[k], 0); k += 1
        inner = css[j + 1:k - 1]
        if head.startswith("@"):
            at = head.split()[0].lower()
            if at in ("@media", "@supports", "@container", "@layer"): out.append(head + "{" + scope_css(inner) + "}")
            elif at in ("@keyframes", "@-webkit-keyframes"): out.append(head + "{" + re.sub(r"\{([^{}]*)\}", lambda m: "{" + fix_decls(m.group(1)) + "}", inner) + "}")
        else:
            if ";" in head: head = head.split(";")[-1].strip()
            sc = scope_sel(head) if head else ""
            if sc: out.append(sc + "{" + fix_decls(inner) + "}")
        i = k
    return "\n".join(out)
def site_css(raw, imgdir):
    seen, parts = set(), []; CSS_CTX["img"] = imgdir
    for u, s in raw.values():
        head = (re.search(r"<head\b.*?</head>", s, re.S | re.I) or re.search(r".*", s)).group(0)
        for m in re.finditer(r"<link\b[^>]*>|<style\b[^>]*>(.*?)</style>", head + s[len(head):][:0], re.S | re.I):
            t = m.group(0)
            if t.lower().startswith("<style"):
                c = m.group(1)
                if c and c not in seen: seen.add(c); parts.append((u, c))
                continue
            if not re.search(r"rel=[\"']?stylesheet", t, re.I): continue
            h = re.search(r"href=[\"']([^\"']+)", t)
            if not h: continue
            cu = urllib.parse.urljoin(u, html.unescape(h.group(1)))
            if cu in seen or re.search(r"fonts\.googleapis|font-awesome|dashicons|admin-bar", cu): continue
            seen.add(cu)
            try: parts.append((cu, get(cu).decode("utf8", "replace")))
            except Exception: print("css לא נטען:", cu, file=sys.stderr)
        for m in re.finditer(r"<style\b[^>]*>(.*?)</style>", s[len(head):], re.S | re.I):
            c = m.group(1)
            if c and c not in seen: seen.add(c); parts.append((u, c))
    body = []
    for base, c in parts: CSS_CTX["base"] = base; body.append(scope_css(c))
    body = "\n".join(body)
    return "/* עיצוב האתר, מוגבל ל-.site-raw. נוצר על ידי tools/build_web.py --site-style — לא לערוך ידנית */\n:root{--color-site-base:var(--color-on-surface)}\n" + body + "\n"

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("plugin"); ap.add_argument("start"); ap.add_argument("--name", required=True)
    ap.add_argument("--depth", type=int, default=2); ap.add_argument("--max-pages", type=int, default=80)
    ap.add_argument("--route", action="append", default=[], help='קישור לכלי שכבר בתוסף: "תחילת-כתובת=מאפיין:ערך", למשל "flights.hakohanim.org=view:abroad"')
    ap.add_argument("--budget-mb", type=float, default=3.0); ap.add_argument("--img-width", type=int, default=900)
    ap.add_argument("--site-style", action="store_true", help="כמו באתר: שומר class/style ומעתיק את עיצוב האתר ל-web/site.css (צבעים, גופנים וגדלים כמשתני CSS — תואם לבודק החנות)")
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
        base[0] = u; c = Clean(on_a, on_img, o.site_style); c.feed(content_of(s)); c.close()
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
    if o.site_style:
        for pg in pages.values():
            for cl in re.findall(r'class="([^"]+)"', pg["h"]): USED.update(cl.split())
        USED.update(["site-raw"])
        css = site_css(raw, imgdir)
        open(os.path.join(plug, "web", "site.css"), "w", encoding="utf8").write(css)
        print(f"עיצוב האתר: {len(css) // 1024}KB", file=sys.stderr)
    out = {"name": o.name, "siteStyle": bool(o.site_style), "url": o.start, "built": time.strftime("%Y-%m-%d"), "home": pid(o.start), "logo": logo,
           "nav": [[ids[norm(u)], t] for u, t in nav if norm(u) in ids], "pages": pages}
    with open(os.path.join(plug, "web.js"), "w", encoding="utf8") as f:   # כותרת: הערת בלוק בלי גרשיים (בודק החנות)
        f.write("/* ממשק האתר: עותק של עמודי " + o.start + " בתוך התוסף. נוצר על ידי tools/build_web.py — לא לערוך ידנית */\nwindow.SITE_WEB = " +
                json.dumps(out, ensure_ascii=False, separators=(",", ":")) + ";\n")
    print(f"{len(pages)} עמודים · תמונות {stats['img']} ({used[0] / 1048576:.1f}MB) · חומר מהתוסף {stats['local']} · קישורים חיצוניים {stats['ext']} · תמונות שלא נכנסו {stats['noimg']}", file=sys.stderr)

if __name__ == "__main__":
    main()
