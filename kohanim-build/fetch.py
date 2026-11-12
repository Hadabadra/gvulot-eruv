#!/usr/bin/env python3
"""מוריד את חומרי התאחדות טהרת הכהנים (באישורם) ל-kohanim-build/raw/ — לא נשמר ב-git.
  drive/   — כל תיקיית Google Drive הציבורית שלהם (כולל תתי-תיקיות), בלי סרטונים (גדולים מדי לתוסף)
  areas.json — האזורים האסורים לכהנים מתוכנת הניווט gps.hakohanim.org (/api/areas)
  flights/<weekday>.json — לוח הנחיתות הקבוע (tumah_day.php) לשבוע, מ-flights.hakohanim.org
  notices.json — הודעות אתר הטיסות
שימוש: python3 fetch.py [--videos]
"""
import datetime, html, http.cookiejar, json, os, re, sys, urllib.request

FOLDER = "1I4LBIeZRHuUfdAwT8WDYJa-24R5sF7Bs"
RAW = os.path.join(os.path.dirname(os.path.abspath(__file__)), "raw")
cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
op.addheaders = [("User-Agent", "Mozilla/5.0")]
get = lambda u, t=120: op.open(u, timeout=t).read()

def tree(fid, path, out, seen):
    if fid in seen: return
    seen.add(fid)
    h = get(f"https://drive.google.com/embeddedfolderview?id={fid}#list").decode("utf8", "replace")
    for m in re.finditer(r'<div class="flip-entry" id="entry-([\w-]+)".*?<div class="flip-entry-title">(.*?)</div>', h, re.S):
        i, t = m.group(1), html.unescape(m.group(2)).strip()
        if "folders/" + i in h: tree(i, path + [t], out, seen)
        else: out.append({"id": i, "path": "/".join(path + [t])})

def main():
    videos = "--videos" in sys.argv
    os.makedirs(os.path.join(RAW, "drive"), exist_ok=True)
    items = []; tree(FOLDER, [], items, set())
    json.dump(items, open(os.path.join(RAW, "drive-tree.json"), "w"), ensure_ascii=False, indent=1)
    for x in items:
        if not videos and re.search(r"\.(mp4|mov)$", x["path"], re.I): continue
        p = os.path.join(RAW, "drive", x["path"])
        if os.path.exists(p) and os.path.getsize(p): continue
        os.makedirs(os.path.dirname(p), exist_ok=True)
        d = get(f"https://drive.usercontent.google.com/download?id={x['id']}&export=download&confirm=t", 900)
        if d[:200].lower().lstrip().startswith((b"<!doctype html", b"<html")):
            print("לא ירד (HTML):", x["path"]); continue
        open(p, "wb").write(d); print(len(d), x["path"])
    a = json.loads(get("https://gps.hakohanim.org/api/areas"))
    json.dump(a, open(os.path.join(RAW, "areas.json"), "w"), ensure_ascii=False)
    print("אזורים:", len(a["data"]["features"]))
    os.makedirs(os.path.join(RAW, "flights"), exist_ok=True)
    base = datetime.date.today() + datetime.timedelta(days=14)   # רחוק מספיק: לוח קבוע בלבד, בלי נתוני זמן אמת
    for i in range(7):
        d = base + datetime.timedelta(days=i)
        j = json.loads(get(f"https://flights.hakohanim.org/tumah_day.php?date={d.isoformat()}"))
        json.dump(j, open(os.path.join(RAW, "flights", f"{j['weekday']}.json"), "w"), ensure_ascii=False)
    open(os.path.join(RAW, "notices.json"), "wb").write(get("https://flights.hakohanim.org/notices.json"))
    print("טיסות: 7 ימים")

if __name__ == "__main__":
    main()
