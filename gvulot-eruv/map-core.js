/* map-core: בסיס משותף למפה ולחיפוש בתוספי אוצריא (מקוואות, גבולות עירוב, כיוון תפילה).
   נגזר מ-streets.js של כיוון תפילה. סטטוס: בפיתוח, עדיין לא מחובר לממשק של התוספים.
   אין תלות ב-DOM: הפונקציות מקבלות נתונים ומחזירות נתונים או מחרוזת SVG, ולכן אפשר לבדוק אותן ב-Node.

   פורמט אזור (כמו בכיוון תפילה):
     { k, lat, lon, r, d, name,
       w: [[שם, סוג-כביש, [lat, lon, lat, lon, ...]], ...],   // רחובות ומבנים
       s: [[שם, lat, lon], ...] }                               // נקודות עניין (בתי כנסת)
   z === 2 = הקואורדינטות שמורות כהפרשים ב-1e-5 מעלה; decodeArea מפרק אותן. */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.MapCore = factory();
})(this, function () {
  'use strict';
  const R = Math.PI / 180;
  const M_LAT = 110540;                       // מטרים למעלת רוחב
  const mLon = lat => 111320 * Math.cos(lat * R);
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

  /* ── גאומטריה ── */
  function distM(a, b) {                      // מרחק במטרים בין [lat, lon] ל-[lat, lon] (קירוב מישורי, מספיק לעיר)
    const dx = (b[1] - a[1]) * mLon((a[0] + b[0]) / 2), dy = (b[0] - a[0]) * M_LAT;
    return Math.hypot(dx, dy);
  }
  function nearOnSegment(p, q1, q2) {         // הנקודה הקרובה ביותר ל-p על הקטע q1-q2 (מישור במטרים)
    const dx = q2[0] - q1[0], dy = q2[1] - q1[1];
    const u = Math.max(0, Math.min(1, ((p[0] - q1[0]) * dx + (p[1] - q1[1]) * dy) / (dx * dx + dy * dy || 1)));
    return [q1[0] + u * dx, q1[1] + u * dy];
  }

  /* ── נתוני אזור ── */
  function decodeArea(a) {
    if (!a || a.z !== 2) return a;
    const B = [Math.round(a.lat * 1e5), Math.round(a.lon * 1e5)];
    const out = Object.assign({}, a);
    out.w = a.w.map(([n, h, g]) => {
      const o = []; let x = B[0], y = B[1];
      for (let i = 0; i < g.length; i += 2) { x += g[i]; y += g[i + 1]; o.push(x / 1e5, y / 1e5); }
      return [n, h, o];
    });
    out.s = (a.s || []).map(([n, dx, dy]) => [n, (B[0] + dx) / 1e5, (B[1] + dy) / 1e5]);
    out.z = 0;
    return out;
  }

  /* קובץ Overpass גולמי (עם geometry) לפורמט האזור. אם כבר בפורמט האזור, מוחזר כמו שהוא. */
  function compactOverpass(j, lat, lon, r) {
    if (j && Array.isArray(j.w)) return j;
    const all = (j && j.elements) || [];
    const els = all.filter(e => e.type === 'way' && (e.tags || {}).highway && Array.isArray(e.geometry) && e.geometry.length > 1);
    if (!els.length) throw new Error('בקובץ אין רחובות');
    if (lat == null) {                         // מרכז ורדיוס מתוך הנתונים עצמם
      let s = 0, t = 0, c = 0;
      for (const e of els) for (const g of e.geometry) { s += g.lat; t += g.lon; c++; }
      lat = s / c; lon = t / c; r = 0;
      for (const e of els) for (const g of e.geometry) r = Math.max(r, distM([lat, lon], [g.lat, g.lon]));
      r = Math.round(r);
    }
    const w = els.map(e => {
      const t = e.tags || {};
      return [t['name:he'] || t.name || '', t.highway || '', e.geometry.flatMap(g => [+g.lat.toFixed(6), +g.lon.toFixed(6)])];
    });
    const s = [];
    for (const e of all) {
      const t = e.tags || {};
      if (t.amenity !== 'place_of_worship') continue;
      let p = null;
      if (e.lat != null) p = [e.lat, e.lon];
      else if (e.bounds) p = [(e.bounds.minlat + e.bounds.maxlat) / 2, (e.bounds.minlon + e.bounds.maxlon) / 2];
      else if (Array.isArray(e.geometry) && e.geometry.length) {
        let a = 0, b = 0; for (const g of e.geometry) { a += g.lat; b += g.lon; }
        p = [a / e.geometry.length, b / e.geometry.length];
      }
      if (p) s.push([t['name:he'] || t.name || '', +p[0].toFixed(5), +p[1].toFixed(5)]);
    }
    return { v: 1, s, k: lat.toFixed(3) + '_' + lon.toFixed(3) + '_' + r, lat: +lat.toFixed(5), lon: +lon.toFixed(5), r, d: new Date().toISOString().slice(0, 10), w };
  }

  /* האזור שמכסה את המיקום: קודם אזור שהמיקום בתוכו (בשוליים של edge מטרים מהקצה); אם אין, אזור שהמיקום בשוליו.
     מחזיר { area, partial } או null. areas: רשימת תיאורי אזורים { k, lat, lon, r }. */
  function findCover(areas, pos, opt) {
    const edge = (opt && opt.edgeM) || 150, outer = (opt && opt.outerM) || 1500;
    let inside = null, border = null;
    for (const a of areas) {
      const m = distM(pos, [a.lat, a.lon]);
      if (m <= a.r - edge) { if (!inside || m < inside[1]) inside = [a, m]; }
      else if (m <= a.r + outer) { if (!border || m - a.r < border[1]) border = [a, m - a.r]; }
    }
    if (inside) return { area: inside[0], partial: false };
    if (border) return { area: border[0], partial: true };
    return null;
  }

  /* ── חיפוש ── */
  // ניקוי לצורך השוואה: בלי גרשיים ומקפים, רווחים בודדים, אותיות קטנות
  const normName = s => String(s == null ? '' : s).replace(/["'״׳\-]/g, '').replace(/\s+/g, ' ').trim().toLowerCase();
  // נרמול חיפוש כללי בעברית (ניקוד, פיסוק, "קריית"="קרית", יי="י", וו="ו")
  const normHe = s => String(s || '').toLowerCase().replace(/[֑-ׇ"'׳״`’\-–—,.()]/g, ' ').replace(/קריית/g, 'קרית').replace(/יי/g, 'י').replace(/וו/g, 'ו').replace(/\s+/g, ' ').trim();

  // קיצורי ערים נפוצים. אותה רשימה כמו במקוואות. הנרמול מוחק גרשיים ומקפים, ולכן ההרחבה נעשית לפניו.
  const Q = '["״\'׳]';
  const ALIASES = [['י', 'ם', 'ירושלים', '[-־–"״\'׳]'], ['ב', 'ב', 'בני ברק'], ['ת', 'א', 'תל אביב'], ['פ', 'ת', 'פתח תקווה'], ['ב', 'ש', 'באר שבע'],
    ['ר', 'ג', 'רמת גן'], ['ר', 'ל', 'ראשון לציון'], ['ק', 'ש', 'קרית שמונה'], ['ק', 'ג', 'קרית גת']]
    .map(([a, b, full, sep]) => [new RegExp('(^|\\s)' + a + (sep || Q) + b + '(?=\\s|$)', 'g'), full]);
  const expandAliases = s => ALIASES.reduce((t, [re, full]) => t.replace(re, '$1' + full), String(s || ''));

  function findWays(area, q) {                 // התאמה מדויקת קודם, ואם אין: מכיל
    const Qn = normName(q);
    const idx = area.w.map((x, i) => [x, i]);
    let ws = idx.filter(([x]) => normName(x[0]) === Qn);
    if (!ws.length) ws = idx.filter(([x]) => normName(x[0]).includes(Qn));
    return ws;                                 // [[way, index], ...]
  }
  /* חיפוש רחוב: הקטע הארוך ביותר של הרחוב ומרכזו. */
  function searchStreet(area, q) {
    const ws = findWays(area, q); if (!ws.length) return null;
    const kx = mLon(area.lat); let best = null;
    for (const [[name, , g], i] of ws) {
      for (let k = 0; k + 3 < g.length; k += 2) {
        const L = Math.hypot((g[k + 2] - g[k]) * M_LAT, (g[k + 3] - g[k + 1]) * kx);
        if (!best || L > best.len) best = { len: L, i, k, name };
      }
    }
    const g = area.w[best.i][2], k = best.k;
    return { i: best.i, k, name: best.name, lat: +((g[k] + g[k + 2]) / 2).toFixed(6), lon: +((g[k + 1] + g[k + 3]) / 2).toFixed(6) };
  }
  /* חיפוש פינה: נקודת המפגש של שני רחובות. null אם אין, או אם הם רחוקים יותר מ-maxM. */
  function findCorner(area, a, b, maxM) {
    maxM = maxM || 150;
    const A = findWays(area, a), B = findWays(area, b);
    if (!A.length || !B.length) return null;
    const o = [area.lat, area.lon], kx = mLon(o[0]);
    const xy = (la, lo) => [(lo - o[1]) * kx, (la - o[0]) * M_LAT];
    let best = null;
    for (const [[, , g], i] of A) for (let k = 0; k + 3 < g.length; k += 2) {
      const a1 = xy(g[k], g[k + 1]), a2 = xy(g[k + 2], g[k + 3]);
      for (const [[, , h]] of B) for (let j = 0; j + 3 < h.length; j += 2) {
        const b1 = xy(h[j], h[j + 1]), b2 = xy(h[j + 2], h[j + 3]);
        for (const [p, q1, q2] of [[a1, b1, b2], [a2, b1, b2], [b1, a1, a2], [b2, a1, a2]]) {
          const n = nearOnSegment(p, q1, q2), d = Math.hypot(n[0] - p[0], n[1] - p[1]);
          if (!best || d < best[0]) best = [d, (p[0] + n[0]) / 2, (p[1] + n[1]) / 2, i, k];
        }
      }
    }
    if (!best) return null;
    return { gapM: Math.round(best[0]), ok: best[0] <= maxM, lat: +(o[0] + best[2] / M_LAT).toFixed(6), lon: +(o[1] + best[1] / kx).toFixed(6), i: best[3], k: best[4],
      names: [area.w[best[3]][0], B[0][0][0]] };
  }
  /* הרחובות הקרובים ביותר לנקודה (ללא כפילויות לפי שם), ממוינים לפי מרחק במטרים. */
  function nearestStreets(area, p, limit) {
    const kx = mLon(p[0]), B = new Map();
    for (const [n, , g] of area.w) {
      if (!n) continue;
      for (let k = 0; k + 3 < g.length; k += 2) {
        const ax = (g[k + 1] - p[1]) * kx, ay = (g[k] - p[0]) * M_LAT, bx = (g[k + 3] - p[1]) * kx, by = (g[k + 2] - p[0]) * M_LAT;
        const dx = bx - ax, dy = by - ay, u = Math.max(0, Math.min(1, -(ax * dx + ay * dy) / (dx * dx + dy * dy || 1)));
        const d = Math.hypot(ax + u * dx, ay + u * dy);
        if (!B.has(n) || d < B.get(n)) B.set(n, d);
      }
    }
    return [...B].sort((a, b) => a[1] - b[1]).slice(0, limit || 5).map(([name, d]) => ({ name, distM: Math.round(d) }));
  }
  /* שם למקום לפי הרחובות שלידו: "א פינת ב" / "ליד א" / "" */
  function placeLabel(area, p) {
    const L = nearestStreets(area, p, 2);
    if (!L.length || L[0].distM > 120) return '';
    return L[1] && L[1].distM < 60 ? `${L[0].name} פינת ${L[1].name}` : (L[0].distM < 25 ? L[0].name : 'ליד ' + L[0].name);
  }

  /* ── תצוגה והטלה ── */
  /* view: { lat, lon (מרכז), zoom (1 = חצי רוחב של 300 מ'), rot (מעלות בכיוון השעון), width, height } */
  function createView(o) {
    const v = Object.assign({ zoom: 1, rot: 0, width: 400, height: 320 }, o);
    v.kx = mLon(v.lat); v.hw = 300 / v.zoom; v.scale = (v.width / 2) / v.hw;
    return v;
  }
  function project(v, lat, lon) {
    const dx = (lon - v.lon) * v.kx, dy = (lat - v.lat) * M_LAT, c = Math.cos(v.rot * R), s = Math.sin(v.rot * R);
    const x = dx * c + dy * s, y = -dx * s + dy * c;
    return [v.width / 2 + x * v.scale, v.height / 2 - y * v.scale];
  }
  function unproject(v, px, py) {
    const x = (px - v.width / 2) / v.scale, y = (v.height / 2 - py) / v.scale, c = Math.cos(v.rot * R), s = Math.sin(v.rot * R);
    const dx = x * c - y * s, dy = x * s + y * c;
    return [+(v.lat + dy / M_LAT).toFixed(6), +(v.lon + dx / v.kx).toFixed(6)];
  }

  /* כתובת Overpass להורדת רחובות (ובתי כנסת) סביב נקודה. פותחים בדפדפן, שומרים את הקובץ וטוענים בתוסף. */
  const OVERPASS = 'https://overpass-api.de/api/interpreter';
  function overpassUrl(lat, lon, r) {
    const a = `(around:${r || 1500},${(+lat).toFixed(5)},${(+lon).toFixed(5)})`;
    return OVERPASS + '?data=' + encodeURIComponent(`[out:json][timeout:60];(way["highway"]["name"]${a};nwr["amenity"="place_of_worship"]["religion"="jewish"]${a};);out tags geom;`);
  }

  /* ── שכבות ──
     שכבה: { id, glyph, points: [{lat, lon, label, id}], lines: [{coords: [[lat, lon], ...], closed, label}] }
     glyph: תו קצר שמצויר על הנקודה (למשל "מ" למקווה, "ע" לעירוב). */
  function toLayer(fc, id, glyph) {            // GeoJSON (Point / LineString / Polygon) -> שכבה
    const L = { id, glyph: glyph || '•', points: [], lines: [] };
    for (const f of (fc && fc.features) || []) {
      const g = f.geometry || {}, p = f.properties || {}, label = p.name || p.label || '';
      if (g.type === 'Point') L.points.push({ lat: g.coordinates[1], lon: g.coordinates[0], label, id: p.id });
      else if (g.type === 'LineString') L.lines.push({ coords: g.coordinates.map(c => [c[1], c[0]]), closed: false, label });
      else if (g.type === 'Polygon') for (const ring of g.coordinates) L.lines.push({ coords: ring.map(c => [c[1], c[0]]), closed: true, label });
    }
    return L;
  }
  function toGeoJSON(items, layer, pick) {     // רשומות עם lat/lon -> FeatureCollection של נקודות
    return {
      type: 'FeatureCollection',
      features: items.filter(i => i.lat != null && i.lon != null).map(i => ({
        type: 'Feature', geometry: { type: 'Point', coordinates: [i.lon, i.lat] },
        properties: Object.assign({ layer }, pick ? pick(i) : { id: i.id, name: i.name || '' })
      }))
    };
  }

  /* ── ציור SVG (מחרוזת). צבעים כמשתני CSS של אוצריא, כמו בכיוון תפילה. ── */
  const widthLabel = m => m >= 2000 ? (m >= 20000 ? Math.round(m / 1000) : (m / 1000).toFixed(1)) + ' ק"מ' : Math.round(m) + " מ'";
  function renderSVG(o) {
    const v = o.view, area = o.area, f = n => n.toFixed(1), W = v.width, H = v.height;
    let lines = '', labels = '', pts = '';
    const inView = (x, y, m) => x > -m && x < W + m && y > -m && y < H + m;
    if (area && o.streets !== false) {
      for (const [name, hw, g] of area.w) {
        let d = '', best = null, any = false;
        for (let k = 0; k < g.length; k += 2) {
          const p = project(v, g[k], g[k + 1]);
          if (inView(p[0], p[1], 50)) any = true;
          d += (k ? 'L' : 'M') + f(p[0]) + ',' + f(p[1]);
          if (k) { const q = project(v, g[k - 2], g[k - 1]), len = Math.hypot(p[0] - q[0], p[1] - q[1]); if (!best || len > best[0]) best = [len, q, p]; }
        }
        if (!any) continue;
        const big = /^(motorway|trunk|primary|secondary)/.test(hw), bld = hw === 'building', pth = /^(path|footway|track|steps|cycleway|bridleway|service)$/.test(hw);
        lines += `<path d="${d}" fill="${bld ? 'var(--color-on-surface-dim)' : 'none'}" fill-opacity=".12" stroke="var(--color-on-surface-dim)" stroke-opacity=".75" stroke-width="${big ? 4 : bld ? 1 : pth ? 1.6 : 2.5}"${pth ? ' stroke-dasharray="5 3"' : ''} stroke-linecap="round" stroke-linejoin="round"/>`;
        if (o.labels !== false && best && best[0] > 70 && name) {
          let a = Math.atan2(best[2][1] - best[1][1], best[2][0] - best[1][0]) / R; if (a > 90) a -= 180; if (a < -90) a += 180;
          labels += `<text transform="translate(${f((best[1][0] + best[2][0]) / 2)},${f((best[1][1] + best[2][1]) / 2)}) rotate(${f(a)})" y="-5" text-anchor="middle" font-size="11" fill="var(--color-on-surface)" paint-order="stroke" stroke="var(--color-surface)" stroke-width="3">${esc(name)}</text>`;
        }
      }
    }
    for (const layer of o.layers || []) {
      for (const ln of layer.lines || []) {   // קווים ופוליגונים (למשל גבול עירוב)
        const d = ln.coords.map((c, i) => { const p = project(v, c[0], c[1]); return (i ? 'L' : 'M') + f(p[0]) + ',' + f(p[1]); }).join('') + (ln.closed ? 'Z' : '');
        lines += `<path d="${d}" fill="${ln.closed ? 'var(--color-primary)' : 'none'}" fill-opacity=".08" stroke="var(--color-primary)" stroke-width="2.5" stroke-dasharray="7 4" stroke-linejoin="round"><title>${esc(ln.label || layer.id)}</title></path>`;
      }
      for (const pt of layer.points || []) {
        const p = project(v, pt.lat, pt.lon); if (!inView(p[0], p[1], 20)) continue;
        const hl = o.hl != null && String(o.hl) === String(pt.id);
        pts += `<g data-layer="${esc(layer.id)}" data-id="${esc(pt.id || '')}"><title>${esc(pt.label || layer.id)}</title>${hl ? `<circle cx="${f(p[0])}" cy="${f(p[1])}" r="15" fill="none" stroke="var(--color-primary)" stroke-width="3"/>` : ''}<circle cx="${f(p[0])}" cy="${f(p[1])}" r="9" fill="var(--color-primary)" stroke="var(--color-surface)" stroke-width="2"/>`
          + `<text x="${f(p[0])}" y="${f(p[1] + 4)}" text-anchor="middle" font-size="11" font-weight="700" fill="var(--color-on-primary, #fff)">${esc(layer.glyph || '•')}</text></g>`;
        if (v.zoom >= 2 && pt.label) pts += `<text x="${f(p[0])}" y="${f(p[1] + 22)}" text-anchor="middle" font-size="10" fill="var(--color-primary)" paint-order="stroke" stroke="var(--color-surface)" stroke-width="3">${esc(pt.label)}</text>`;
      }
    }
    let syn = '', me = '';
    if (area && o.syn) for (const [sn, la, lo] of area.s || []) {
      const p = project(v, la, lo); if (!inView(p[0], p[1], 10)) continue;
      syn += `<g><title>${esc(sn || 'בית כנסת')}</title><text x="${f(p[0])}" y="${f(p[1] + 5)}" text-anchor="middle" font-size="14" fill="var(--color-primary)" paint-order="stroke" stroke="var(--color-surface)" stroke-width="3">✡</text></g>`;
    }
    if (o.me) { const p = project(v, o.me[0], o.me[1]); if (inView(p[0], p[1], 20)) me = `<circle cx="${f(p[0])}" cy="${f(p[1])}" r="7" fill="var(--color-on-surface)" stroke="var(--color-surface)" stroke-width="2.5"><title>המיקום שלי</title></circle>`; }
    let sel = '';
    if (o.selected && area && area.w[o.selected.i]) {
      const g = area.w[o.selected.i][2], k = o.selected.k, q = project(v, g[k], g[k + 1]), p = project(v, g[k + 2], g[k + 3]);
      sel = `<line x1="${f(q[0])}" y1="${f(q[1])}" x2="${f(p[0])}" y2="${f(p[1])}" stroke="var(--color-primary)" stroke-width="7" stroke-linecap="round"/>`;
    }
    const north = `<g transform="translate(${W - 20},30) rotate(${f(v.rot)})"><path d="M0,-12 L6,7 L0,3 L-6,7Z" fill="var(--color-on-surface)" stroke="var(--color-surface)" stroke-width="1.5"/><text y="-15" text-anchor="middle" font-size="11" fill="var(--color-on-surface)" paint-order="stroke" stroke="var(--color-surface)" stroke-width="3">צ N</text></g>`;
    // טקסט עברי מתיישר מימין: מעוגן ב-rtl ליד חץ הצפון, ומתפרש שמאלה (כמו בכיוון תפילה)
    const scale = `<text x="${W - 38}" y="18" direction="rtl" text-anchor="start" font-size="12" fill="var(--color-on-surface-dim)">${widthLabel(v.hw * 2)} לרוחב</text>`;
    const attr = area && o.streets !== false ? `<text x="8" y="${H - 8}" direction="ltr" font-size="10" fill="var(--color-on-surface-dim)">© OpenStreetMap contributors${area.d ? ' · ' + esc(area.d) : ''}</text>` : '';
    return `<svg viewBox="0 0 ${W} ${H}" xmlns="http://www.w3.org/2000/svg" role="img">${lines}${sel}${labels}${syn}${pts}${me}${north}${scale}${attr}</svg>`;
  }

  return { distM, decodeArea, compactOverpass, findCover, normName, normHe, expandAliases, findWays, searchStreet, findCorner, nearestStreets, placeLabel,
    createView, project, unproject, toLayer, toGeoJSON, renderSVG, overpassUrl };
});
