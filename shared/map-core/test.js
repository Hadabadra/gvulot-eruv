/* בדיקות ל-map-core. הרצה: node shared/map-core/test.js
   אם מוגדר KIVUN_ST (נתיב לקובץ st-NN.js מכיוון תפילה), רצות גם בדיקות על נתונים אמיתיים. */
'use strict';
const assert = require('assert');
const M = require('./map-core.js');

let n = 0;
const t = (name, fn) => { fn(); n++; console.log('ok  ' + name); };

// אזור סינתטי סביב (31.78, 35.2): רחוב א' מזרח-מערב, רחוב ב' צפון-דרום, נפגשים ב-(31.78, 35.2)
const kx = 111320 * Math.cos(31.78 * Math.PI / 180), ky = 110540;
const dLon = 100 / kx, dLat = 100 / ky;   // 100 מטר
const area = {
  k: 'test', lat: 31.78, lon: 35.2, r: 1500, d: '2026-10-23', name: 'בדיקה',
  w: [
    // כמו ב-OSM: שני הרחובות נפגשים בצומת משותף (31.78, 35.2)
    ['רחוב אלון', 'residential', [31.78, 35.2 - dLon, 31.78, 35.2, 31.78, 35.2 + dLon]],
    ["ז'בוטינסקי", 'secondary', [31.78 - dLat, 35.2, 31.78, 35.2, 31.78 + dLat, 35.2]],
    ['רחוב רחוק', 'residential', [31.79, 35.21, 31.791, 35.211]],
    ['', 'building', [31.7801, 35.2001, 31.7802, 35.2001, 31.7802, 35.2002, 31.7801, 35.2002]]
  ],
  s: [['בית כנסת', 31.7803, 35.2003]]
};

t('distM: 100 מטר צפונה', () => assert.ok(Math.abs(M.distM([31.78, 35.2], [31.78 + dLat, 35.2]) - 100) < 0.5));

t('decodeArea: פירוק הפרשים', () => {
  const enc = { k: 'e', lat: 31.78, lon: 35.2, r: 100, z: 2, w: [['א', 'residential', [-10, 20, 5, 5]]], s: [['ב', 1, 2]] };
  const d = M.decodeArea(JSON.parse(JSON.stringify(enc)));
  assert.strictEqual(d.z, 0);
  // ההפרשים מצטברים: x = 3178000-10, אחר כך +5; y = 3520000+20, אחר כך +5
  assert.deepStrictEqual(d.w[0][2], [31.7799, 35.2002, 31.77995, 35.20025]);
  assert.deepStrictEqual(d.s[0], ['ב', 31.78001, 35.20002]);
  assert.strictEqual(M.decodeArea(area), area, 'אזור שכבר מפורק מוחזר כמו שהוא');
});

t('compactOverpass: רחובות ובתי כנסת, מרכז לפי הנתונים', () => {
  const j = { elements: [
    { type: 'way', tags: { highway: 'residential', name: 'אלון' }, geometry: [{ lat: 31.78, lon: 35.2 }, { lat: 31.781, lon: 35.2 }] },
    { type: 'way', tags: { highway: 'residential' }, geometry: [{ lat: 31.78, lon: 35.2 }] },   // קצר מדי, מדלגים
    { type: 'node', lat: 31.7805, lon: 35.2005, tags: { amenity: 'place_of_worship', religion: 'jewish', name: 'בית כנסת' } }
  ] };
  const a = M.compactOverpass(j);
  assert.strictEqual(a.w.length, 1);
  assert.strictEqual(a.w[0][0], 'אלון');
  assert.strictEqual(a.s.length, 1);
  assert.ok(a.r > 0 && a.k.includes('_'));
  assert.throws(() => M.compactOverpass({ elements: [] }), /אין רחובות/);
});

t('findCover: בפנים, בשוליים, ומחוץ', () => {
  const areas = [{ k: 'a', lat: 31.78, lon: 35.2, r: 1500 }];
  assert.strictEqual(M.findCover(areas, [31.78, 35.2]).area.k, 'a');
  assert.strictEqual(M.findCover(areas, [31.78, 35.2]).partial, false);
  const edge = [31.78 + 1450 / ky, 35.2];                    // בתוך הרדיוס אבל בשולי 150 מ'
  assert.strictEqual(M.findCover(areas, edge).partial, true);
  assert.strictEqual(M.findCover(areas, [32.5, 35.2]), null);
});

t('חיפוש: נרמול וגרשיים', () => {
  assert.strictEqual(M.normName("ז'בוטינסקי"), 'זבוטינסקי');
  assert.strictEqual(M.normHe('קריית שמונה'), 'קרית שמונה');
  assert.strictEqual(M.normHe('ת"א'), 'ת א');
});

t('expandAliases: קיצורי ערים', () => {
  const E = M.expandAliases;
  assert.strictEqual(E('ב"ב'), 'בני ברק');
  assert.strictEqual(E('י-ם'), 'ירושלים');
  assert.strictEqual(E('ת"א'), 'תל אביב');
  assert.strictEqual(E('פ"ת'), 'פתח תקווה');
  assert.strictEqual(E('רח׳ הרב ב״ב'), 'רח׳ הרב בני ברק');
  assert.strictEqual(E('בבית'), 'בבית', 'מילה רגילה לא משתנה');
  assert.strictEqual(E('ב ב'), 'ב ב');
});

t('searchStreet: רחוב לפי שם מדויק ומכיל', () => {
  const r = M.searchStreet(area, 'רחוב אלון');
  assert.strictEqual(r.name, 'רחוב אלון');
  assert.ok(Math.abs(M.distM([r.lat, r.lon], [31.78, 35.2]) - 50) < 1, 'אמצע הקטע הארוך הראשון, 50 מ\' מהצומת');
  assert.strictEqual(M.searchStreet(area, 'זבוטינסקי').name, "ז'בוטינסקי");
  assert.strictEqual(M.searchStreet(area, 'אלון').name, 'רחוב אלון', 'התאמה חלקית');
  assert.strictEqual(M.searchStreet(area, 'לא קיים'), null);
});

t('findCorner: פינה, ופינה שלא נפגשת', () => {
  const c = M.findCorner(area, 'אלון', 'זבוטינסקי');
  assert.ok(c.ok && c.gapM < 2, 'הרחובות נפגשים');
  assert.ok(M.distM([c.lat, c.lon], [31.78, 35.2]) < 2);
  const far = M.findCorner(area, 'אלון', 'רחוק');
  assert.ok(far && !far.ok, 'רחוק מדי');
  assert.strictEqual(M.findCorner(area, 'אלון', 'לא קיים'), null);
});

t('nearestStreets ו-placeLabel', () => {
  const L = M.nearestStreets(area, [31.78, 35.2], 2).map(x => x.name).sort();
  assert.deepStrictEqual(L, ["ז'בוטינסקי", 'רחוב אלון']);
  assert.ok(M.placeLabel(area, [31.78, 35.2]).includes('פינת'));
  assert.strictEqual(M.placeLabel(area, [31.9, 35.4]), '');
});

t('הטלה: project/unproject הפיכות, כולל סיבוב', () => {
  for (const rot of [0, 33, 180, -90]) {
    const v = M.createView({ lat: 31.78, lon: 35.2, zoom: 2, rot });
    const p = M.project(v, 31.7811, 35.2023);
    const q = M.unproject(v, p[0], p[1]);
    assert.ok(Math.abs(q[0] - 31.7811) < 2e-6 && Math.abs(q[1] - 35.2023) < 2e-6, 'rot=' + rot);
  }
  const v = M.createView({ lat: 31.78, lon: 35.2 });
  const c = M.project(v, 31.78, 35.2);
  assert.deepStrictEqual(c, [200, 160], 'המרכז במרכז התצוגה');
  assert.ok(M.project(v, 31.78 + dLat, 35.2)[1] < 160, 'צפון למעלה');
});

t('שכבות: GeoJSON הלוך ושוב', () => {
  const items = [{ id: 'a', name: 'מקווה א', lat: 31.78, lon: 35.2 }, { id: 'b', name: 'בלי קואורדינטות' }];
  const fc = M.toGeoJSON(items, 'mikvaot');
  assert.strictEqual(fc.features.length, 1);
  assert.deepStrictEqual(fc.features[0].geometry.coordinates, [35.2, 31.78]);
  const L = M.toLayer(fc, 'mikvaot', 'מ');
  assert.deepStrictEqual(L.points[0], { lat: 31.78, lon: 35.2, label: 'מקווה א', id: 'a' });
  const poly = { type: 'FeatureCollection', features: [{ type: 'Feature', properties: { name: 'עירוב' }, geometry: { type: 'Polygon', coordinates: [[[35.2, 31.78], [35.21, 31.78], [35.21, 31.79], [35.2, 31.78]]] } }] };
  const P = M.toLayer(poly, 'eruv', 'ע');
  assert.strictEqual(P.lines.length, 1);
  assert.ok(P.lines[0].closed);
  assert.deepStrictEqual(P.lines[0].coords[0], [31.78, 35.2]);
});

t('renderSVG: רחובות, שכבות, חץ צפון ושורת מקור', () => {
  const v = M.createView({ lat: 31.78, lon: 35.2, zoom: 2 });
  const layer = M.toLayer(M.toGeoJSON([{ id: 'x', name: 'מקווה <בדיקה>', lat: 31.7801, lon: 35.2001 }], 'mikvaot'), 'mikvaot', 'מ');
  const svg = M.renderSVG({ area, view: v, layers: [layer], selected: { i: 0, k: 0 } });
  assert.ok(svg.startsWith('<svg') && svg.endsWith('</svg>'));
  assert.ok((svg.match(/<path /g) || []).length >= 3, 'שלושה רחובות ומבנה');
  assert.ok(svg.includes('data-layer="mikvaot"') && svg.includes('data-id="x"'));
  assert.ok(svg.includes('מקווה &lt;בדיקה&gt;') && !svg.includes('<בדיקה>'), 'בריחה מ-HTML');
  assert.ok(svg.includes('OpenStreetMap contributors'));
  assert.ok(/direction="rtl" text-anchor="start"[^>]*>\d+ מ' לרוחב/.test(svg), 'תווית קנה המידה מעוגנת rtl ולא נחתכת');
  assert.ok(svg.includes('stroke-width="7"'), 'רחוב נבחר מודגש');
  const wide = M.renderSVG({ area: null, view: M.createView({ lat: 31.78, lon: 35.2, zoom: 0.001 }), layers: [] });
  assert.ok(wide.includes('600 ק"מ לרוחב'), 'רוחב גדול מוצג בק"מ');
  assert.ok(M.renderSVG({ area: null, view: M.createView({ lat: 31.78, lon: 35.2, zoom: 0.1 }), layers: [] }).includes('6.0 ק"מ לרוחב'));
  const noArea = M.renderSVG({ area: null, view: v, layers: [layer] });
  assert.ok(!noArea.includes('OpenStreetMap'), 'בלי אזור אין שורת מקור');
  assert.ok(noArea.includes('data-layer="mikvaot"'), 'שכבת נקודות עובדת בלי מפת רחובות');
});

// בדיקות על נתונים אמיתיים מכיוון תפילה (אופציונלי)
if (process.env.KIVUN_ST) {
  const vm = require('vm'), fs = require('fs');
  let got = null;
  vm.runInNewContext(fs.readFileSync(process.env.KIVUN_ST, 'utf8'), { EMB_PUT: a => { got = a; } });
  t('נתונים אמיתיים: פירוק, חיפוש, הטלה וציור', () => {
    const a = M.decodeArea(got);
    assert.ok(a.w.length > 10, 'יש רחובות');
    const name = a.w.find(x => x[0] && x[2].length > 4)[0];
    const r = M.searchStreet(a, name);
    assert.ok(r && M.distM([r.lat, r.lon], [a.lat, a.lon]) < a.r * 2, 'הרחוב נמצא בתוך האזור');
    const v = M.createView({ lat: r.lat, lon: r.lon, zoom: 1.5 });
    const svg = M.renderSVG({ area: a, view: v, layers: [] });
    assert.ok(svg.length > 1000 && svg.includes('<path'));
    console.log('    ' + a.name + ': ' + a.w.length + ' רחובות, חיפוש "' + name + '" ← ' + r.lat + ',' + r.lon + ', SVG ' + svg.length + ' תווים');
  });
}

t('overpassUrl, ציור שכבת בתי כנסת, מיקום שלי והדגשה', () => {
  const u = M.overpassUrl(31.78, 35.2, 1200);
  assert.ok(u.startsWith('https://overpass-api.de/api/interpreter?data=') && decodeURIComponent(u).includes('around:1200,31.78000,35.20000'));
  const v = M.createView({ lat: 31.78, lon: 35.2, zoom: 2 });
  const layer = M.toLayer(M.toGeoJSON([{ id: 'x', name: 'א', lat: 31.7801, lon: 35.2001 }], 'm'), 'm', 'מ');
  const svg = M.renderSVG({ area, view: v, layers: [layer], syn: true, me: [31.78, 35.2], hl: 'x', streets: false });
  assert.ok(svg.includes('✡') && svg.includes('המיקום שלי') && svg.includes('r="15"'));
  assert.ok(!svg.includes('stroke-opacity=".75"'), 'streets:false מסתיר רחובות');
  assert.ok(!M.renderSVG({ area, view: v, layers: [], syn: false, streets: true }).includes('✡'));
});

console.log('\n' + n + ' בדיקות עברו');
