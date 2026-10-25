/* map-ui: מסך מפה משותף לתוספי אוצריא (מקוואות, גבולות עירוב). נשען על map-core.js.
   סטטוס: בפיתוח. מה שעובד היום: מפת נקודות עם זום וגרירה, חיפוש לפי שם, טעינת רחובות מקובץ
   (חיפוש רחוב ופינה, הנקודות הקרובות, בתי כנסת), הצגת "המיקום שלי".
   מה שעדיין "בקרוב" (מוצג כפתור שלא פעיל, כדי שיהיה ברור איפה זה יהיה): מסלול הגעה, קווי עירוב, בדיקת כתובת.
   online:false (מצב מנותק באוצריא) מסתיר כל קישור החוצה: הורדת רחובות, Waze/Google, הצטרפות.

   שימוש: MapUI.mount(element, {
     points: [{id, name, sub, lat, lon}], layerId, glyph, layerName, selectedId, me: [lat, lon],
     call(method, params), openLink(url), onPick(id), pickLabel, nearby: true, nearbyLabel,
     repo, forumUrl, future: ['מסלול הליכה...'] }) */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory(require('./map-core.js'));
  else root.MapUI = factory(root.MapCore);
})(this, function (MC) {
  'use strict';
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const W = 400, H = 300;

  // מחרוזות לתרגום: המארחים ממזגים את MapUI.EN למילון שלהם
  const EN = {
    'זום פנימה': 'Zoom in', 'זום החוצה': 'Zoom out', 'מרכוז': 'Center', 'מקור נתוני הרחובות': 'Street data source',
    'טעינת רחובות מקובץ': 'Load streets from a file', 'הורדת רחובות לעיר': 'Download city streets', 'הורדת רחובות (מתקרבים לעיר בזום)': 'Download streets (zoom in to a city)', 'מקור חלופי 1': 'Alternative source 1', 'מקור חלופי 2': 'Alternative source 2',
    'חיפוש רחוב או פינה, למשל: הרצל פינת בן יהודה': 'Search a street or corner, e.g. Herzl corner Ben Yehuda', 'חיפוש': 'Search',
    'שכבות': 'Layers', 'רחובות': 'Streets', 'בתי כנסת': 'Synagogues', 'מסלול הליכה או נסיעה (בקרוב)': 'Walking or driving route (coming soon)',
    'קווי עירוב (בקרוב)': 'Eruv lines (coming soon)', 'בדיקת כתובת בתוך העירוב (בקרוב)': 'Check an address inside the eruv (coming soon)',
    'בפיתוח': 'In development', 'מחכה לעזרה': 'Looking for help', 'הצטרפות': 'Join', 'הבקשה בגיטהאב': 'Request on GitHub', 'השרשור בפורום': 'Forum thread',
    'חזרה': 'Back', 'קרוב לכתובת': 'Near this address', 'נמצא:': 'Found:', 'לא נמצא רחוב בשם': 'No street found named', 'הרחובות לא נפגשים באזור הזה': 'The streets do not meet in this area',
    'הקובץ לא נקרא': 'The file could not be read', 'בקובץ אין רחובות': 'The file has no streets', 'כדי לחפש רחוב צריך לטעון קובץ רחובות': 'To search a street, load a streets file first',
    'הקובץ נטען': 'File loaded', 'רחובות': 'streets', 'נבחר': 'Selected', 'פתיחה ברשימה': 'Open in the list', 'פתיחה בדפדפן': 'Open in browser',
    'ניווט ב-Waze': 'Navigate with Waze', 'פתיחה ב-Google Maps': 'Open in Google Maps', 'מעבירים עכבר על נקודה, ולוחצים לפרטים': 'Hover a point, click for details',
    'אין נקודות עם מיקום להצגה': 'No points with a location to show', 'זו תצוגה ראשונית, ויש בה שגיאות אפשריות': 'This is an early view and may contain errors',
    'הקובץ נטען רק לזמן הפתיחה של המסך': 'The file is loaded for this session only', 'המיקום שלי': 'My location'
  };

  const CSS = `
.mapui .bar { display: flex; flex-wrap: wrap; gap: .4em; align-items: center; margin: .4em 0; }
.mapui .bar .grow { flex: 1 1 12em; min-width: 0; }
.mapui button.mu { font: inherit; cursor: pointer; padding: .35em .8em; border-radius: var(--radius-pill, 2em); border: 1px solid var(--color-outline-variant, #888); background: var(--color-surface, transparent); color: var(--color-on-surface, inherit); }
.mapui button.mu:hover { background: var(--color-secondary-container, rgba(128,128,128,.15)); }
.mapui button.mu[aria-disabled="true"] { opacity: .55; cursor: help; border-style: dashed; }
.mapui .view { touch-action: none; user-select: none; }
.mapui .view svg { display: block; width: 100%; height: auto; max-height: 55vh; background: var(--color-surface-container, transparent); border-radius: var(--radius-md, .75em); cursor: grab; }
.mapui .view svg g[data-id] { cursor: pointer; }
.mapui input[type="search"] { font: inherit; padding: .4em .8em; border-radius: var(--radius-pill, 2em); border: 1px solid var(--color-outline-variant, #888); background: var(--color-surface, transparent); color: var(--color-on-surface, inherit); width: 100%; box-sizing: border-box; }
.mapui .msg { margin: .3em 0; font-size: .9em; color: var(--color-on-surface-variant, inherit); }
.mapui .sel { margin: .5em 0; padding: .5em .8em; border-radius: var(--radius-md, .75em); background: var(--color-secondary-container, rgba(128,128,128,.12)); }
.mapui .layers { display: flex; flex-wrap: wrap; gap: .3em 1em; margin: .4em 0; font-size: .9em; }
.mapui .layers label.off { opacity: .55; }
.mapui h4 { margin: .8em 0 .2em; }
.mapui.mapui-tab .view svg { max-height: calc(100vh - 16em); min-height: 18em; }
`;

  function mount(el, o) {
    if (!MC) { el.innerHTML = '<p>רכיב המפה לא נטען.</p>'; return; }
    if (!document.getElementById('mapui-css')) { const st = document.createElement('style'); st.id = 'mapui-css'; st.textContent = CSS; document.head.append(st); }
    const pts = (o.points || []).filter(p => p.lat != null && p.lon != null);
    const S = { lat: 0, lon: 0, zoom: 1, area: null, areaName: '', sel: o.selectedId != null ? String(o.selectedId) : null, street: null,
      show: { pts: true, streets: true, syn: true } };
    const byId = new Map(pts.map(p => [String(p.id), p]));
    const layer = () => MC.toLayer({ type: 'FeatureCollection', features: pts.map(p => ({ type: 'Feature', geometry: { type: 'Point', coordinates: [p.lon, p.lat] }, properties: { id: p.id, name: p.name } })) }, o.layerId || 'pts', o.glyph || '•');

    function fit(list) {
      list = list && list.length ? list : pts;
      if (!list.length) { S.lat = 31.78; S.lon = 35.2; S.zoom = 0.1; return; }
      const lat = list.reduce((a, i) => a + i.lat, 0) / list.length, lon = list.reduce((a, i) => a + i.lon, 0) / list.length;
      const far = Math.max(150, ...list.map(i => MC.distM([lat, lon], [i.lat, i.lon])));
      S.lat = lat; S.lon = lon; S.zoom = Math.max(0.0005, Math.min(4, 300 / (far * 1.2)));
    }
    const selPt = () => (S.sel != null ? byId.get(S.sel) : null);
    if (selPt()) { S.lat = selPt().lat; S.lon = selPt().lon; S.zoom = 3; } else fit();

    const future = (o.future || ['מסלול הליכה או נסיעה (בקרוב)', 'קווי עירוב (בקרוב)']);
    const off = o.online === false;
    const join = off ? '' : [o.repo ? `<button class="mu" data-mu-open="${esc(o.repo + '/issues/new')}">הצטרפות</button>` : '', o.issueUrl ? `<button class="mu" data-mu-open="${esc(o.issueUrl)}">הבקשה בגיטהאב</button>` : '', o.forumUrl ? `<button class="mu" data-mu-open="${esc(o.forumUrl)}">השרשור בפורום</button>` : ''].join(' ');

    el.classList.add('mapui'); el.classList.toggle('mapui-tab', !!o.tab);
    el.innerHTML = `
      <div class="bar"><button class="mu" data-mu="in" title="זום פנימה" aria-label="זום פנימה">+</button><button class="mu" data-mu="out" title="זום החוצה" aria-label="זום החוצה">−</button><button class="mu" data-mu="fit">מרכוז</button>
        <span class="msg" id="mu-hint">${pts.length ? 'מעבירים עכבר על נקודה, ולוחצים לפרטים' : 'אין נקודות עם מיקום להצגה'}</span></div>
      <div class="view" id="mu-view"></div>
      <div class="sel" id="mu-sel" hidden></div>
      <div class="layers" id="mu-layers">
        <strong>שכבות</strong>
        <label><input type="checkbox" data-mu-layer="pts" checked> ${esc(o.layerName || 'נקודות')}</label>
        <label class="off"><input type="checkbox" data-mu-layer="streets" checked disabled> רחובות</label>
        <label class="off"><input type="checkbox" data-mu-layer="syn" checked disabled> בתי כנסת</label>
        ${future.map(f => `<label class="off" title="בפיתוח: מחכה לעזרה"><input type="checkbox" disabled> ${esc(f)}</label>`).join('')}
      </div>
      <h4>רחובות וחיפוש</h4>
      <div class="bar">${off ? '' : '<button class="mu" data-mu="dl" id="mu-dl">הורדת רחובות לעיר</button>'}<button class="mu" data-mu="load">טעינת רחובות מקובץ</button></div>
      ${off ? '<p class="msg">אוצריא במצב מנותק: אפשר לטעון קובץ רחובות שכבר שמור במחשב.</p>' : `<p class="msg">מורידים את קובץ העיר (נפתח בדפדפן וההורדה מתחילה לבד), ואז "טעינת רחובות מקובץ" ובוחרים אותו. <button class="mu" data-mu="url">מקור חלופי 1</button> <button class="mu" data-mu="url2">מקור חלופי 2</button> לעיר שאינה ברשימה. הקווים בלי רחובות הם קו מתאר מקורב של הארץ, לרקע בלבד.</p>`}
      <div class="bar"><div class="grow"><input type="search" id="mu-q" placeholder="חיפוש רחוב או פינה, למשל: הרצל פינת בן יהודה" aria-label="חיפוש"></div><button class="mu" data-mu="search">חיפוש</button></div>
      <div class="msg" id="mu-msg"></div><div id="mu-near"></div>
      <h4>בפיתוח</h4>
      <div class="bar">${future.map(f => `<button class="mu" aria-disabled="true" data-mu="soon" title="בפיתוח: מחכה לעזרה">${esc(f)}</button>`).join('')}</div>
      <p class="msg">זו תצוגה ראשונית, ויש בה שגיאות אפשריות. הקובץ נטען רק לזמן הפתיחה של המסך.${join ? ' מחכה לעזרה: ' + join : ''}</p>`;
    const $ = id => el.querySelector('#' + id);
    const nearCity = () => {
      const C = window.STREET_CITIES || {}; let best = null;
      for (const [n, c] of Object.entries(C)) { const d = MC.distM([S.lat, S.lon], [c.lat, c.lon]); if (!best || d < best.d) best = { n, c, d }; }
      return best && best.d < 30000 && S.zoom >= 0.5 ? best : null;
    };
    const updDl = () => { const b = $('mu-dl'); if (!b) return; const c = nearCity(); b.dataset.slug = c ? c.c.slug : ''; b.textContent = c ? 'הורדת רחובות: ' + c.n : 'הורדת רחובות (מתקרבים לעיר בזום)'; b.setAttribute('aria-disabled', c ? 'false' : 'true'); };
    const say = t => { $('mu-msg').textContent = t || ''; };

    function draw() { setTimeout(updDl, 0);
      const v = MC.createView({ lat: S.lat, lon: S.lon, zoom: S.zoom, width: W, height: H });
      const svg = MC.renderSVG({ area: S.area, view: v, layers: S.show.pts ? [layer()] : [], streets: S.show.streets, syn: S.show.syn, me: o.me, hl: S.sel, selected: S.street, labels: S.zoom >= 2, outline: !S.area });
      $('mu-view').innerHTML = svg; $('mu-view')._v = v;
    }
    function showSel() {
      const p = selPt(), b = $('mu-sel');
      if (!p) { b.hidden = true; return; }
      b.hidden = false;
      b.innerHTML = `<strong>${esc(p.name)}</strong>${p.sub ? '<br>' + esc(p.sub) : ''}<div class="bar">`
        + (o.onPick ? `<button class="mu" data-mu="pick">${esc(o.pickLabel || 'פתיחה ברשימה')}</button>` : '')
        + (off ? '' : `<button class="mu" data-mu-open="https://waze.com/ul?ll=${p.lat},${p.lon}&navigate=yes">ניווט ב-Waze</button>`
        + `<button class="mu" data-mu-open="https://www.google.com/maps/search/?api=1&query=${p.lat},${p.lon}">פתיחה ב-Google Maps</button>`)
        + `<button class="mu" aria-disabled="true" data-mu="soon" title="בפיתוח: מחכה לעזרה">${esc(future[0])}</button></div>`;
    }
    function nearList(center) {
      if (o.nearby === false || !center) { $('mu-near').innerHTML = ''; return; }
      const L = pts.map(p => [p, MC.distM(center, [p.lat, p.lon])]).sort((a, b) => a[1] - b[1]).slice(0, 5);
      $('mu-near').innerHTML = L.length ? `<div class="msg"><strong>${esc(o.nearbyLabel || 'קרוב לכתובת')}</strong></div><div class="bar">` + L.map(([p, d]) => `<button class="mu" data-mu-sel="${esc(p.id)}">${esc(p.name)} · ${d >= 1000 ? (d / 1000).toFixed(1) + " ק\"מ" : Math.round(d) + " מ'"}</button>`).join('') + '</div>' : '';
    }
    function refresh() { draw(); showSel(); updDl(); }
    function selectPt(id) { S.sel = String(id); const p = selPt(); if (p) { S.lat = p.lat; S.lon = p.lon; S.zoom = Math.max(S.zoom, 3); } S.street = null; refresh(); }

    async function loadFile() {
      if (!o.call) return say('טעינה מקובץ זמינה בתוך אוצריא.');
      try {
        const r = await o.call('fs.pickUserFile', { title: 'בחירת קובץ רחובות (JSON מ-Overpass או קובץ אזור)', extensions: ['json'] });
        if (!r || !r.success || !r.data || r.data.cancelled) return;
        const t = await o.call('fs.readTextFile', { token: r.data.token });
        let j = null; try { j = JSON.parse(t.data); } catch (e) { return say('הקובץ לא נקרא'); }
        let a;
        try { a = MC.decodeArea(MC.compactOverpass(j)); } catch (e) { return say(e.message || 'בקובץ אין רחובות'); }
        S.area = a; S.areaName = a.name || '';
        el.querySelectorAll('[data-mu-layer="streets"],[data-mu-layer="syn"]').forEach(c => { c.disabled = false; c.parentElement.classList.remove('off'); });
        if (!selPt()) { S.lat = a.lat; S.lon = a.lon; S.zoom = 1.2; }
        say(`הקובץ נטען: ${a.w.length} רחובות${(a.s || []).length ? ' ו-' + a.s.length + ' בתי כנסת' : ''}.`);
        refresh();
      } catch (e) { say('הקובץ לא נקרא'); }
    }
    function search() {
      const q = ($('mu-q').value || '').trim(); if (!q) return;
      const qa = MC.expandAliases(q);
      if (S.area) {
        const c = qa.split(/\s+פינת\s+|\s+פינה\s+|\s*[\/&]\s*/).filter(Boolean);
        if (c.length === 2) {
          const r = MC.findCorner(S.area, c[0], c[1]);
          if (!r) return say(`לא נמצא רחוב בשם "${MC.findWays(S.area, c[0]).length ? c[1] : c[0]}"`);
          if (!r.ok) return say('הרחובות לא נפגשים באזור הזה');
          S.lat = r.lat; S.lon = r.lon; S.zoom = 3; S.street = { i: r.i, k: r.k }; S.sel = null; say(`נמצא: ${c[0]} פינת ${c[1]}`); refresh(); return nearList([r.lat, r.lon]);
        }
        const r = MC.searchStreet(S.area, qa);
        if (r) { S.lat = r.lat; S.lon = r.lon; S.zoom = 3; S.street = { i: r.i, k: r.k }; S.sel = null; say(`נמצא: ${r.name}`); refresh(); return nearList([r.lat, r.lon]); }
      }
      // לפי שם הנקודה (גם בלי קובץ רחובות)
      const nq = MC.normHe(qa), hit = pts.find(p => MC.normHe(p.name + ' ' + (p.sub || '')).includes(nq));
      if (hit) { say('נמצא: ' + hit.name); return selectPt(hit.id); }
      say(S.area ? `לא נמצא רחוב בשם "${q}"` : 'כדי לחפש רחוב צריך לטעון קובץ רחובות');
    }

    // גרירה וזום
    let drag = null;
    const view = $('mu-view');
    view.addEventListener('pointerdown', e => { drag = { x: e.clientX, y: e.clientY, lat: S.lat, lon: S.lon, moved: false }; });
    view.addEventListener('pointermove', e => {
      if (!drag) return; const svg = view.querySelector('svg'); if (!svg) return;
      const k = svg.getBoundingClientRect().width / W, dx = (e.clientX - drag.x) / k, dy = (e.clientY - drag.y) / k;
      if (!drag.moved && Math.hypot(dx, dy) < 4) return; drag.moved = true;
      const v = view._v; S.lon = drag.lon - dx / v.scale / v.kx; S.lat = drag.lat + dy / v.scale / 110540; draw();
    });
    const end = () => { if (drag) setTimeout(() => { drag = null; }, 0); };
    view.addEventListener('pointerup', end); view.addEventListener('pointerleave', end); view.addEventListener('pointercancel', end);
    view.addEventListener('wheel', e => { e.preventDefault(); S.zoom = Math.max(0.0005, Math.min(8, S.zoom * (e.deltaY < 0 ? 1.25 : 0.8))); draw(); }, { passive: false });

    el.addEventListener('click', e => {
      const t = e.target;
      const g = t.closest && t.closest('#mu-view g[data-id]');
      if (g && !(drag && drag.moved)) return selectPt(g.dataset.id);
      const open = t.closest && t.closest('[data-mu-open]'); if (open) { if (o.openLink) o.openLink(open.dataset.muOpen); return; }
      const sp = t.closest && t.closest('[data-mu-sel]'); if (sp) return selectPt(sp.dataset.muSel);
      const lay = t.closest && t.closest('[data-mu-layer]'); if (lay) { S.show[lay.dataset.muLayer] = lay.checked; return draw(); }
      const b = t.closest && t.closest('[data-mu]'); if (!b) return;
      const a = b.dataset.mu;
      if (a === 'in') { S.zoom = Math.min(8, S.zoom * 1.5); draw(); }
      else if (a === 'out') { S.zoom = Math.max(0.0005, S.zoom / 1.5); draw(); }
      else if (a === 'fit') { S.sel = null; S.street = null; fit(); refresh(); }
      else if (a === 'load') loadFile();
      else if (a === 'dl') { const sl = b.dataset.slug; if (!sl) return say('אין קובץ רחובות מוכן לעיר הזו. אפשר לנסות מקור חלופי.'); say('ההורדה נפתחה בדפדפן. אחריה: "טעינת רחובות מקובץ".'); if (o.openLink) o.openLink((window.STREETS_BASE || '') + sl + '.json'); }
      else if (a === 'url' || a === 'url2') { const u = MC.overpassUrl(S.lat, S.lon, 1500, a === 'url2' ? 1 : 0); say('נפתח בדפדפן. שומרים את הקובץ שמתקבל (Ctrl+S) ואז "טעינת רחובות מקובץ".'); if (o.openLink) o.openLink(u); }
      else if (a === 'search') search();
      else if (a === 'pick') { const p = selPt(); if (p && o.onPick) o.onPick(p.id); }
      else if (a === 'soon') say('בפיתוח: הפעולה הזו עדיין לא קיימת. מחכה לעזרה, ראו את הקישורים למטה.');
    });
    $('mu-q').addEventListener('keydown', e => { if (e.key === 'Enter') search(); });
    refresh();
    return { state: S, refresh, select: selectPt };
  }

  return { mount, EN, CSS };
});
