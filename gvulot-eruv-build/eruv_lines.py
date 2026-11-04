#!/usr/bin/env python3
"""קווי עירוב בקירוב מתוך מפות מוקד העירוב (משימה ו׳, 1.9.0).

השיטה (שקופה וניתנת לשחזור):
1. מהתמונה של המוקד מוציאים שתי מסכות: הכבישים (פיקסלים לבנים) והקו של העירוב (כתום/אדום).
2. מציירים את רחובות OpenStreetMap של אותה עיר (הקבצים המובנים ב-streets/) כמסכה באותה רשת.
3. מנחוש התחלתי של 2 נקודות עיגון (צומת בתמונה ↔ צומת במפה) מחשבים התאמה, ומעדנים אותה אוטומטית
   (OpenCV ECC, טרנספורמציה אפינית) כך שהכבישים בתמונה יתלכדו עם הכבישים במפה.
4. את קו העירוב מהתמונה ממירים לקואורדינטות, מפשטים (כ-3 מ') ושומרים ב-gvulot-eruv/eruv-lines.js.

התוצאה היא *קירוב* בלבד: דיוק של עשרות מטרים, תלוי באיכות המפה. בתוסף מוצג תמיד "בקירוב — לפי מפת המוקד",
עם קישור למפה המקורית ולאחראי. הקובע הוא המפה המקורית והאחראי המקומי — לא הקו.

הרצה:  python3 gvulot-eruv-build/eruv_lines.py [--debug DIR]
עיר חדשה: מוסיפים רשומה ל-PILOTS (מזהה המפה, קובץ הרחובות, מסגרת המפה בתמונה, צבע הקו, 2 נקודות עיגון). """
import json, math, os, re, subprocess, sys
import numpy as np, cv2
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.path.join(HERE, '..', 'gvulot-eruv')
CORE = os.path.join(HERE, '..', 'shared', 'map-core', 'map-core.js')   # ה-CI מוריד את shared לפני האריזה
if not os.path.exists(CORE): CORE = os.path.join(APP, 'map-core.js')

# frame = [x0, y0, x1, y1] של אזור המפה בתמונה המלאה; anchors = [((x, y), (lat, lon)), ...]
# line = 'orange' או 'red'; inner = ריבועים להסתרה (מקרא, חותמת) בתוך המסגרת
PILOTS = [
    {'map': '02443b14', 'city': 'קרית אתא', 'name': 'שכונת שביט', 'streets': 'kiryat-ata', 'line': 'orange', 'resp': 'הרב משה ערערא · 053-316-0985',
     'frame': [114, 576, 1580, 1822], 'hide': [[180, 1690, 570, 1822]],
     'anchors': [((750, 1806), (32.80772, 35.11668)), ((262, 600), (32.81395, 35.11415))]},
    {'map': '947bcab2', 'city': 'חדרה', 'name': 'שכונות שלמה, קלרין ופאר (העירוב השכונתי)', 'streets': 'hadera', 'line': 'orange',
     'frame': [50, 25, 1590, 1383], 'hide': [],
     'anchors': [((370, 908), (32.42883, 34.91573)), ((1358, 928), (32.43300, 34.91572))]},
]

def area(slug):
    js = ("global.window={};require(%r);const MC=require(%r);const A=MC.decodeArea(window.STREETS[%r]);"
          "process.stdout.write(JSON.stringify(A.w.filter(w=>!/building/.test(w[1]||''))))") % (os.path.join(APP, 'streets', slug + '.js'), CORE, slug)
    return json.loads(subprocess.check_output(['node', '-e', js]))

def masks(img, P):
    a = img.astype(int); r, g, b = a[..., 0], a[..., 1], a[..., 2]
    road = (r > 241) & (g > 241) & (b > 241)
    if P['line'] == 'orange': line = (r > 190) & (g > 70) & (g < 160) & (b < 120) & (r - b > 110)
    else: line = (r > 170) & (g < 90) & (b < 90)
    keep = np.zeros(road.shape, bool); x0, y0, x1, y1 = P['frame']; keep[y0:y1, x0:x1] = True
    for x0, y0, x1, y1 in P.get('hide', []): keep[y0:y1, x0:x1] = False
    return (road & keep).astype(np.uint8) * 255, (line & keep).astype(np.uint8) * 255

def georef(P, img, road, ways, dbg=None):
    (p1, g1), (p2, g2) = P['anchors'][:2]
    lat0 = (g1[0] + g2[0]) / 2; mx = 111320 * math.cos(math.radians(lat0)); my = 110540
    m = lambda la, lo: np.array([(lo - g1[1]) * mx, -(la - g1[0]) * my])      # מטרים (x מזרחה, y דרומה) ביחס לעוגן 1
    # התאמה ראשונית (קנה מידה + סיבוב) מפיקסלים למטרים
    v_img = np.array(p2, float) - p1; v_m = m(*g2)
    s = np.linalg.norm(v_m) / np.linalg.norm(v_img); th = math.atan2(v_m[1], v_m[0]) - math.atan2(v_img[1], v_img[0])
    R = s * np.array([[math.cos(th), -math.sin(th)], [math.sin(th), math.cos(th)]])
    A0 = np.hstack([R, (-R @ np.array(p1, float)).reshape(2, 1)])                # פיקסל ← מטרים
    # מסכת OSM ברשת של התמונה: מטרים ← פיקסל (ההפכי של A0)
    Ainv = cv2.invertAffineTransform(A0.astype(np.float32))
    osm = np.zeros(road.shape, np.uint8)
    for n, h, g in ways:
        pts = np.array([m(g[i], g[i + 1]) for i in range(0, len(g), 2)], np.float32)
        px = (Ainv[:, :2] @ pts.T).T + Ainv[:, 2]
        w = 9 if re.search('primary|secondary|trunk', h or '') else 6
        cv2.polylines(osm, [px.astype(np.int32)], False, 255, w)
    # עידון: ECC מיישר את מסכת הכבישים בתמונה אל מסכת OSM
    blur = lambda a: cv2.GaussianBlur(a.astype(np.float32) / 255, (0, 0), 6)
    warp = np.eye(2, 3, dtype=np.float32)
    try:
        cc, warp = cv2.findTransformECC(blur(osm), blur(road), warp, cv2.MOTION_AFFINE, (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 300, 1e-6), None, 5)
    except cv2.error as e:
        cc = None; print('  ECC נכשל, נשארת ההתאמה הראשונית:', e)
    if dbg:
        al = cv2.warpAffine(road, warp, road.shape[::-1], flags=cv2.INTER_LINEAR + cv2.WARP_INVERSE_MAP)
        ov = np.dstack([osm, al, np.zeros_like(osm)]); cv2.imwrite(os.path.join(dbg, P['map'] + '-fit.png'), cv2.resize(ov, None, fx=.5, fy=.5))
    # פיקסל בתמונה ← פיקסל ברשת OSM (warp הוא osm→img; ההפכי) ← מטרים ← lat/lon
    W3 = np.vstack([warp, [0, 0, 1]]); W3i = np.linalg.inv(W3); A3 = np.vstack([A0, [0, 0, 1]])
    T = A3 @ W3i
    def to_ll(xy):
        q = (T[:2, :2] @ np.asarray(xy, float).T).T + T[:2, 2]
        return np.column_stack([g1[0] - q[:, 1] / my, g1[1] + q[:, 0] / mx])
    return to_ll, cc

def trace(line):
    k = cv2.morphologyEx(line, cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8))
    # פער קצר (חותמת או מספר שמכסים את הקו): מחברים בין שני הקצוות הקרובים של השלד
    from skimage.morphology import skeletonize
    sk = skeletonize(k > 0).astype(np.uint8)
    nb = cv2.filter2D(sk, -1, np.ones((3, 3), np.float32)) - 1
    ends = np.argwhere((sk == 1) & (nb == 1))
    def hole_area(m):
        cs, hier = cv2.findContours(m, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
        return max([cv2.contourArea(c) for c, h in zip(cs, hier[0]) if h[3] >= 0] or [0]) if hier is not None else 0
    if hole_area(k) == 0 and len(ends) <= 40:
        best = (0, None)
        for a in range(len(ends)):
            for b in range(a + 1, len(ends)):
                if np.linalg.norm(ends[a] - ends[b]) > 220: continue
                t = k.copy(); (y1, x1), (y2, x2) = ends[a], ends[b]; cv2.line(t, (int(x1), int(y1)), (int(x2), int(y2)), 255, 9)
                ha = hole_area(t)
                if ha > best[0]: best = (ha, t)
        if best[1] is not None: k = best[1]
    n, lab, st, _ = cv2.connectedComponentsWithStats(k)
    big = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA])); comp = (lab == big).astype(np.uint8) * 255
    cs, hier = cv2.findContours(comp, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    # קו סגור: יש חור — לוקחים את האמצע בין המתאר החיצוני לפנימי (בקירוב: הפנימי מורחב בחצי עובי)
    holes = [c for c, h in zip(cs, hier[0]) if h[3] >= 0]
    if holes:
        c = max(holes, key=cv2.contourArea)
        return c.reshape(-1, 2).astype(float), True
    c = max(cs, key=cv2.contourArea)
    return c.reshape(-1, 2).astype(float), False

def simplify(ll, tol_m=3):
    lat0 = ll[:, 0].mean(); xy = np.column_stack([ll[:, 1] * 111320 * math.cos(math.radians(lat0)), ll[:, 0] * 110540]).astype(np.float32)
    ap = cv2.approxPolyDP(xy.reshape(-1, 1, 2), tol_m, True).reshape(-1, 2)
    idx = [int(np.argmin(((xy - p) ** 2).sum(1))) for p in ap]
    return ll[sorted(set(idx))]

def main():
    dbg = sys.argv[sys.argv.index('--debug') + 1] if '--debug' in sys.argv else None
    if dbg: os.makedirs(dbg, exist_ok=True)
    data = {}
    for P in PILOTS:
        img = np.array(Image.open(os.path.join(APP, 'maps', P['map'] + '.webp')).convert('RGB'))
        road, line = masks(img, P)
        to_ll, cc = georef(P, img, road, area(P['streets']), dbg)
        px, closed = trace(line)
        ll = simplify(to_ll(px))
        print(f"{P['city']} — {P['name']}: {len(ll)} נקודות, סגור={closed}, התאמת ECC={cc if cc is None else round(cc, 3)}")
        data[P['map']] = {'city': P['city'], 'name': P['name'], 'resp': P.get('resp', ''), 'closed': closed, 'fit': None if cc is None else round(float(cc), 3),
                          'coords': [[round(a, 6), round(b, 6)] for a, b in ll]}
    out = os.path.join(APP, 'eruv-lines.js')
    with open(out, 'w', encoding='utf-8') as f:
        f.write('/* קווי עירוב בקירוב — נוצר ע"י gvulot-eruv-build/eruv_lines.py מתוך מפות מוקד העירוב. לא לערוך ידנית.\n'
                '   הקובע הוא המפה המקורית והאחראי המקומי; הקו הוא קירוב בלבד. */\n')
        f.write('window.ERUV_LINES = ' + json.dumps(data, ensure_ascii=False, separators=(',', ':')) + ';\n')
    print('נכתב', out)

if __name__ == '__main__':
    main()
