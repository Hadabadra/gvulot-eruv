/* טהרת כהנים — הגדרות התוסף לממשק המשותף (2.2.0).
   הממשק עצמו (index.html, app.js, app.css, המציג, המפה) מגיע מ-gvulot-eruv/ דרך tools/sync-ui.sh — לא עורכים אותו כאן.
   כאן: השם, הטקסטים, הארגונים, שכבות המפה (אזורים אסורים), ותצוגות שאין בעירוב (טיסות). התוכן ב-data.js / docs.js / extra.js / eruv-lines.js
   נבנה ע"י kohanim-build/build.py מחומרי התאחדות טהרת הכהנים, באישורם. */
(function () {
  'use strict';
  const D = window.ERUV_DATA || {}, X = window.ERUV_EXTRA || {}, LINES = window.ERUV_LINES || {};
  const PHONE = '08-3132020', EMAIL = 'a083132020@gmail.com', ID = 'com.hadabadra.tahorat-kohanim';
  const LV = { 'א': ['רמה א', 'var(--color-error, #c62828)'], 'ב': ['רמה ב', 'var(--color-tertiary, #ef6c00)'], 'ג': ['רמה ג', 'var(--color-secondary, #6d4c41)'] };
  const GROUPS = [['guide', 'מדריכים ומידע'], ['maps', 'מפות, הדרכות ומצגות הדרכה'], ['marot', 'מראות כהונה — חוברות הלכתיות'], ['emor', 'אמור ואמרת — עלונים הלכתיים'], ['pres', 'מצגות הלכתיות']];
  const DAYS = ['ראשון', 'שני', 'שלישי', 'רביעי', 'חמישי', 'שישי', 'שבת'];
  // מפות בית חולים לפי מזהה בית החולים (רשימת בתי החולים ורבניהם — מהממשק המשותף)
  const HOSP_MAPS = { hadassah: ['hadassah'], ichilov: ['ichilov', 'ichilov-orient'], sheba: ['tel-hashomer'], assaf: ['assaf'] };
  let C = null;   // ההקשר האחרון מ-app.js (לאירועים של לוח הטיסות)
  const fl = { day: new Date().getDay(), mode: 'land', time: '' };

  const levelCount = l => Object.values(LINES).filter(x => x.level === l).length;
  const cityHas = (c, ctx) => { const n = ctx.byCity.get(c); return n ? n.maps.length + n.areas.filter(a => a.group === 'areas').length : 0; };

  // ── טיסות: הלוח הקבוע (משוער) מתוך flights.hakohanim.org ──
  const F = X.flights || { days: {}, windows: { red: 20, orange: 80 } };
  const toMin = t => { const m = /^(\d{1,2}):(\d{2})/.exec(t || ''); return m ? +m[1] * 60 + +m[2] : null; };
  const fmt = m => { m = ((m % 1440) + 1440) % 1440; return String(Math.floor(m / 60)).padStart(2, '0') + ':' + String(m % 60).padStart(2, '0'); };
  function dayList(d) { return (F.days[String(d)] || []).map(x => ({ ...x, m: toMin(x.t) })).filter(x => x.m != null).sort((a, b) => a.m - b.m); }
  function checkHTML(ctx) {
    const t = toMin(fl.time); if (t == null) return '';
    const esc = ctx.esc, land = fl.mode === 'land';
    // לפי ההסבר באתר הטיסות: נוחתים — טיסה טמאה שנוחתת עד שעה אחריכם; ממריאים — טיסה טמאה שנוחתת בשלוש השעות שלפני ההמראה
    const from = land ? t : t - 180, to = land ? t + 60 : t;
    const all = [...dayList((fl.day + 6) % 7).map(x => ({ ...x, m: x.m - 1440 })), ...dayList(fl.day), ...dayList((fl.day + 1) % 7).map(x => ({ ...x, m: x.m + 1440 }))];
    const hit = all.filter(x => x.m >= from && x.m <= to);
    if (!hit.length) return `<div class="fl-res">לפי הלוח הקבוע לא נמצאה נחיתה של טיסה טמאה ${land ? 'בשעה שאחרי הנחיתה שלכם' : 'בשלוש השעות שלפני ההמראה'}. הלוח משוער — ביום הטיסה יש לבדוק שוב באתר או בקו המידע.</div>`;
    return `<div class="fl-res warn"><b>לפי הלוח הקבוע נוחתות ${land ? 'בשעה שאחרי הנחיתה שלכם' : 'בשלוש השעות שלפני ההמראה'}:</b> ${hit.map(x => `${esc(x.f)} (${esc(x.o)}) ב-${fmt(x.m)}`).join(' · ')}.
      ${land ? 'לפי אתר הטיסות: מומלץ להזדרז לצאת מהטרמינל ולבדוק שוב.' : 'לפי אתר הטיסות יש הוראות מתאימות (המתנה מחוץ לטרמינל או בחדר טיפול בחיות) — לבדוק באתר או בקו המידע.'}
      הלוח משוער ועלול להשתנות; בכל ספק — לשאול רב או להתקשר ${ctx.telChip(PHONE)}</div>`;
  }
  function flightsView(ctx) {
    C = ctx; const esc = ctx.esc, ICON = ctx.ICON;
    const L = dayList(fl.day), w = F.windows || { red: 20, orange: 80 };
    const bars = L.map(x => `<i class="o" style="right:${(x.m / 1440 * 100).toFixed(2)}%;width:${(w.orange / 1440 * 100).toFixed(2)}%"></i><i class="r" style="right:${(x.m / 1440 * 100).toFixed(2)}%;width:${(w.red / 1440 * 100).toFixed(2)}%"></i>`).join('');
    return `<div class="wrap">
      <div class="hero"><div class="grow"><h2>טיסות — נחיתות טמאות בנתב"ג טרמינל 3</h2>
      <p>הלוח הקבוע לפי ימי השבוע, מתוך אתר הטיסות של התאחדות טהרת הכהנים (נאסף ${esc(F.built || '')}). משוער בלבד: איחורים והקדמות מופיעים רק באתר עצמו, בזמן אמת.</p></div>
      <button class="btn tonal ext-only" data-url="${esc(F.src || 'https://flights.hakohanim.org/')}">${ICON.ext} בדיקה בזמן אמת</button></div>
      <div class="tabs">${DAYS.map((d, i) => `<button class="tab${i === fl.day ? ' on' : ''}" data-fl-day="${i}">${d}<span class="badge">${dayList(i).length}</span></button>`).join('')}</div>
      <div class="section-title">בדיקת טיסה שלי — יום ${DAYS[fl.day]}</div>
      <div class="fl-check"><select id="flMode"><option value="land"${fl.mode === 'land' ? ' selected' : ''}>נוחתים בנתב"ג בשעה</option><option value="dep"${fl.mode === 'dep' ? ' selected' : ''}>ממריאים מנתב"ג בשעה</option></select>
        <input id="flTime" type="time" value="${esc(fl.time)}"></div>
      <div id="flRes">${checkHTML(ctx)}</div>
      <div class="section-title">לוח הטומאה — יום ${DAYS[fl.day]} (${L.length} נחיתות)</div>
      <div class="fl-tl" title="אדום: ${w.red} הדקות הראשונות מהנחיתה · כתום: השעה שאחריהן">${bars}</div>
      <div class="fl-ticks">${[0, 3, 6, 9, 12, 15, 18, 21, 24].map(h => `<span>${String(h).padStart(2, '0')}</span>`).join('')}</div>
      <div class="fl-list">${L.map(x => `<div class="fl-item"><b>${esc(x.t)}</b><span>${esc(x.f)}</span><small>מ-${esc(x.o)}</small></div>`).join('') || '<p class="fine">אין נחיתות טמאות בלוח הקבוע ליום זה.</p>'}</div>
      <p class="fine">אדום — ${w.red} הדקות הראשונות מהנחיתה; כתום — השעה שאחריהן. הצבעים להתמצאות בלבד, למי שמגיע לטרמינל או לתחנת הרכבת (כמו באתר).
      ${(F.notices || []).map(esc).join(' · ')}</p>
      ${docCards(ctx, ['mk-flights', 'pres-flights', 'madrich'])}
      <p class="fine">מקור: flights.hakohanim.org — התאחדות טהרת הכהנים (הנתונים שם מ-aviationstack). שכבת המידע לכהנים מבוססת על כללים של המערכת ואינה פסק הלכה. בכל ספק יש להיוועץ ברב.</p>
      ${ctx.sourceCard()}</div>`;
  }
  const docCards = (ctx, ids) => { const ds = ids.map(i => ctx.docById.get(i)).filter(Boolean); return ds.length ? `<div class="doc-grid">${ds.map(d => ctx.docCardHTML(d)).join('')}</div>` : ''; };
  const mapCards = (ctx, ids) => { const ms = ids.map(i => ctx.mapById.get(i)).filter(Boolean); return ms.length ? `<div class="map-grid">${ms.map(ctx.mapCardHTML).join('')}</div>` : ''; };
  // אירועים של לוח הטיסות (app.js לא מכיר אותם)
  document.addEventListener('click', e => { const b = e.target.closest && e.target.closest('[data-fl-day]'); if (!b || !C) return; fl.day = +b.dataset.flDay; C.render(); });
  document.addEventListener('input', e => {
    if (!C || !(e.target.id === 'flTime' || e.target.id === 'flMode')) return;
    if (e.target.id === 'flTime') fl.time = e.target.value; else fl.mode = e.target.value;
    const r = document.getElementById('flRes'); if (r) r.innerHTML = checkHTML(C);
  });

  // ── תצוגות ──
  function cityCard(ctx, c) {
    const n = ctx.byCity.get(c), m = n.maps[0], esc = ctx.esc, ar = n.areas.filter(a => a.group === 'areas').length, ds = ctx.docsOfCity(c).length;
    return `<button class="city-card" data-city="${esc(c)}">${m ? `<div class="city-thumb" style="background-image:url('${esc(ctx.srcOf(m, true))}')"></div>` : `<div class="city-thumb empty">${ctx.ICON.pin}</div>`}
      <div class="city-meta"><strong>${esc(c)}</strong><span>${[n.maps.length ? n.maps.length + ' מפות' : '', ar ? ar + ' אזורים' : '', ds ? ds + ' חוברות' : ''].filter(Boolean).join(' · ') || 'נקודות הפצה'}</span></div></button>`;
  }
  function homeView(ctx) {
    const esc = ctx.esc, ICON = ctx.ICON, nAreas = D.areas.filter(a => a.group === 'areas').length;
    const main = D.cities.filter(c => cityHas(c, ctx));
    return `<div class="wrap">
      <div class="hero"><div class="grow"><h2>טהרת כהנים — מידע מעודכן</h2>
      <p>${D.maps.length} מפות, ${ctx.DOCS.length} חוברות ומצגות, ${nAreas} אזורים אסורים על המפה ולוח טיסות — מאת התאחדות טהרת הכהנים, באישורם, בלי צורך באינטרנט.</p></div>
      <button class="btn tonal" data-mapdev="">${ICON.map} מפת האזורים</button></div>
      <div class="section-title">המדריך והמידע העיקרי</div>${docCards(ctx, ['madrich', 'medical', 'bein-hazmanim', 'updates'])}
      <div class="row-links"><button class="btn text" data-view="docs">${ICON.book} כל החוברות, העלונים והמצגות</button>
        <button class="btn text" data-view="abroad">${ICON.globe} טיסות</button>
        <button class="btn text" data-view="hosps">${ICON.hospital} בתי חולים</button></div>
      <div class="section-title">ערים ואתרים</div>
      <div class="city-grid">${main.map(c => cityCard(ctx, c)).join('')}</div>
      <p class="fine">בעוד ${D.cities.length - main.length} ערים יש נקודות להשגת המדריך והמפות — בחיפוש או ברשימת הערים בצד.</p>
      ${ctx.sourceCard()}</div>`;
  }
  function docsView(ctx) {
    const esc = ctx.esc, ICON = ctx.ICON, groups = [...new Set((X.library || []).map(b => b.g))];
    return `<div class="wrap">
      <div class="hero"><div class="grow"><h2>חוברות, עלונים ומצגות</h2>
      <p>כל החוברות של התאחדות טהרת הכהנים בתוך התוסף ובלי אינטרנט: דפדוף, הגדלה, הדפסה ושמירה של עמוד. (התמונות דחוסות כדי שהכל ייכנס לתוסף.)</p></div></div>
      ${GROUPS.map(([g, t]) => { const ds = ctx.DOCS.filter(d => d.group === g); return ds.length ? `<div class="section-title">${esc(t)}</div><div class="doc-grid">${ds.map(d => ctx.docCardHTML(d)).join('')}</div>` : ''; }).join('')}
      ${groups.map(g => `<div class="section-title">${esc(g)}</div><div class="lib">${X.library.filter(b => b.g === g).map(b => `<button class="chip" data-url="${esc(b.u)}" title="פתיחה בדפדפן">${ICON.link}${esc(b.t)}</button>`).join('')}</div>`).join('')}
      <p class="fine">הסרטונים (כ-1.2GB) גדולים מדי לתוסף, ולכן הם קישורים לתיקיית ההתאחדות ב-Google Drive — נפתחים בדפדפן כשיש אינטרנט.</p>
      ${ctx.sourceCard()}</div>`;
  }
  function hospsView(ctx) {
    const esc = ctx.esc, ICON = ctx.ICON;
    return `<div class="wrap">
      <div class="hero"><div class="grow"><h2>בתי חולים ומרכזים רפואיים</h2><p>חוברת המרכזים הרפואיים והלכות פיקוח נפש, מפות לכהנים של בתי החולים, ורב בית החולים — רק ממקורות רשמיים.</p></div></div>
      ${docCards(ctx, ['medical', 'mk-pikuach', 'mk-hospitals', 'pres-buildings'])}
      <div class="section-title">מפות בתי חולים לכהנים</div>${mapCards(ctx, ['hadassah', 'ichilov', 'ichilov-orient', 'tel-hashomer', 'assaf'])}
      <div class="section-title">רב בית החולים ושירותי הדת</div>
      <div class="row-links">${ctx.HOSPITALS.filter(h => !h.abroad && h.contacts && h.contacts.length).map(h => `<button class="btn tonal" data-hosp="${h.id}">${ICON.hospital} ${esc(h.name)} · ${esc(h.city)}</button>`).join('')}</div>
      <p class="fine">מספרי רבני בתי החולים מעמודי שירותי הדת הרשמיים (כמו בתוסף גבולות עירוב). שאלות טהרה לכהנים — קו המידע של ההתאחדות ${ctx.telChip(PHONE)}</p></div>`;
  }
  function hospView(ctx, h) {
    const esc = ctx.esc;
    return `<div class="wrap">
      <div class="hero"><div class="grow"><h2>${esc(h.name)}</h2><p>${esc(h.city)}</p></div></div>
      ${mapCards(ctx, HOSP_MAPS[h.id] || [])}
      <div class="section-title">רב בית החולים ושירותי הדת</div>
      ${h.contacts && h.contacts.length ? `<div class="contacts">${h.contacts.map(ctx.contactHTML).join('')}</div>` : '<p class="fine">לא נמצאו טלפונים ממקור רשמי של בית החולים.</p>'}
      ${docCards(ctx, ['medical', 'mk-pikuach'])}
      ${h.src ? `<p class="fine">מקור הטלפונים: <button class="btn text" data-url="${esc(h.src)}">${esc(h.srcName)}</button></p>` : ''}
      <p class="fine">התוסף אינו פוסק הלכה. לשאלות טהרה: קו המידע של התאחדות טהרת הכהנים ${ctx.telChip(PHONE)}</p></div>`;
  }
  function railAbroad(ctx) {
    return { title: 'טיסות — ימי השבוע', count: 7, html: DAYS.map((d, i) => `<button class="rail-item${ctx.state.view === 'abroad' && fl.day === i ? ' on' : ''}" data-fl-day="${i}" data-view="abroad"><span class="name">יום ${d}</span><span class="badge">${dayList(i).length}</span></button>`).join('') };
  }
  function railHosp(ctx) {
    const H = ctx.HOSPITALS.filter(h => !h.abroad);
    return { title: 'בתי חולים', count: H.length, html: H.map(h => `<button class="rail-item${ctx.state.view === 'hosp' && ctx.state.hosp === h.id ? ' on' : ''}" data-hosp="${h.id}"><span class="name">${ctx.esc(h.name)}</span><span class="badge">${(HOSP_MAPS[h.id] || []).length ? '🗺' : ''}</span></button>`).join('') };
  }

  // ── מפה: שכבות האזורים האסורים לפי רמה, ובדיקת כתובת ──
  const center = L => [L.coords.reduce((s, p) => s + p[0], 0) / L.coords.length, L.coords.reduce((s, p) => s + p[1], 0) / L.coords.length];
  function layers() {
    const mk = (lvl, name, color, glyph) => {
      const ids = Object.keys(LINES).filter(i => LINES[i].level === lvl); if (!ids.length) return null;
      return { id: 'kh-' + ({ 'א': 'a1', 'ב': 'b2', 'ג': 'c3', A: 'oslo' })[lvl], name, glyph, sub: ids.length + ' אזורים',
        points: lvl === 'A' ? [] : ids.map(i => { const c = center(LINES[i]); return { lat: c[0], lon: c[1], id: '__line-' + i, label: LINES[i].name }; }),
        lines: ids.map(i => ({ coords: LINES[i].coords, closed: true, solid: true, color, label: `${lvl === 'A' ? 'שטח A' : 'אזור אסור לכהנים — ' + LV[lvl][0]} · ${LINES[i].city ? LINES[i].city + ' · ' : ''}${LINES[i].name}${LINES[i].resp ? ' — ' + LINES[i].resp : ''} · מקור: תוכנת הניווט של התאחדות טהרת הכהנים` })) };
    };
    return [mk('א', 'אזורים אסורים — רמה א', LV['א'][1], 'א'), mk('ב', 'אזורים אסורים — רמה ב', LV['ב'][1], 'ב'), mk('ג', 'אזורים אסורים — רמה ג', LV['ג'][1], 'ג'),
      mk('A', 'שטחי A (מתוכנת הניווט)', 'var(--color-outline, #757575)', 'A')].filter(Boolean);
  }
  function insideMsg(lat, lon) {
    const MC = window.MapCore; let near = null;
    for (const L of Object.values(LINES)) {
      const d = MC.distToRing([lat, lon], L.coords), inn = MC.inPoly([lat, lon], L.coords);
      const what = L.level === 'A' ? 'שטח A' : 'אזור אסור לכהנים (' + LV[L.level][0] + ')';
      if (inn) return `בתוך ${what}: ${L.city ? L.city + ' · ' : ''}${L.name}${L.resp ? ' — ' + L.resp : ''}. לפי תוכנת הניווט של ההתאחדות; לבירור: ${PHONE}`;
      if (d < 150 && (!near || d < near.d)) near = { d, L, what };
    }
    return near ? `כ-${Math.round(near.d)} מ' מ${near.what}: ${near.L.name}${near.L.city ? ' (' + near.L.city + ')' : ''}. לבירור: ${PHONE}` : 'לא נמצא אזור אסור במאגר בנקודה זו (המאגר אינו מלא — בכל ספק לשאול).';
  }

  window.SITE = {
    id: ID, title: 'טהרת כהנים', version: '2.2.0', lineZoom: 4,
    store: 'https://otzaria.org/plugins/6af5c07506096e8fb9b1aaa1',   // דף התוסף בחנות (נוצר 12.11.2026, ממתין לאישור מנהל)
    planPath: 'kohanim-docs/STATUS.md', forumUrl: '', fieldActionId: 'find-kohanim', email: EMAIL, contactUrl: 'https://hakohanim.org/',
    bookRegex: /אהלות|טומאת מת|טומאת כהנים|הלכות אבל|שסט|שע|אמור/,
    cityPos: D.cityPos || {}, cityAka: {},
    text: {
      name: 'טהרת כהנים', home: 'כל הארץ', mapsWord: 'מפות', mapsWordCity: 'מפות לכהנים', areasWord: 'אזורים ונקודות', areasOnly: 'נקודות הפצה',
      noMapCity: 'אין מפה לעיר זו במאגר', areasCityWord: 'אזורים ונקודות הפצה', areasTitle: 'אזורים', areasSearch: 'אזורים ונקודות הפצה', areaCount: 'אזורים',
      areaWhole: 'אזור', areaNoNames: '', docsTitle: 'חוברות ומצגות', docsAll: 'כל החוברות', abroadBtn: 'טיסות', abroadCrumb: 'טיסות', hospsBtn: 'בתי חולים',
      docTag: 'חוברת', docTagTitle: 'יש חוברת או מצגת לעיר זו', railCities: 'ערים', railAbroad: 'טיסות', railHosp: 'בתי חולים',
      techumTitle: 'חוברות ומצגות לעיר', techumEmptyHTML: 'אין חוברת מיוחדת לעיר זו. המדריך הכללי — בכפתור "חוברות". לשאלות: קו המידע של ההתאחדות',
      techumFine: 'חוברות התאחדות טהרת הכהנים. אינן פסק הלכה — בכל ספק יש לשאול רב או להתקשר לקו המידע.',
      searchEmpty: 'אפשר לחפש עיר, רחוב, אתר, בית חולים או חוברת. למקום שאינו במאגר: קו המידע של התאחדות טהרת הכהנים, 08-3132020.',
      libTitle: 'קישורים וסרטונים', sourceSite: 'לאתר המדריך לכהנים', sourceContact: '', sourcePhone: 'קו המידע',
      noNear: 'אין מידע במאגר בקרבת המיקום', lineLayer: 'אזורים אסורים לכהנים', addMap: 'הוספת מפה משלי',
      fbPlaceholder: 'הערה, תיקון או מקום חסר — נשלח דרך אוצריא למפתחת (תיקון במידע עצמו — לקו המידע של ההתאחדות)',
      guideNote: 'להתמצאות בלבד ואינו פסק הלכה.',
      readmeNote: 'להתמצאות בלבד ואינו פסק הלכה — בכל ספק לשאול רב או את קו המידע 08-3132020.',
      mapFine: 'מיקומי הערים בקירוב. האזורים האסורים — מתוך תוכנת הניווט של התאחדות טהרת הכהנים (רמה א אדום, ב כתום, ג חום; שטחי A אפור). המאגר אינו מלא והמצב בשטח משתנה — אין לסמוך עליו להלכה; בכל ספק לשאול. המפות עצמן — בלשונית "רשימה".'
    },
    dom: {
      '.topbar-title': { text: 'טהרת כהנים' }, '#crumb': { text: 'כל הארץ' },
      '#q': { placeholder: 'עיר, רחוב, אתר, בית חולים או חוברת' },
      '#notice > span:nth-of-type(2)': { text: 'המידע להתמצאות בלבד ואינו פסק הלכה. המצב בשטח משתנה — בכל ספק יש לשאול רב או להתקשר לקו המידע.' },
      '#notice .notice-call': { text: 'קו המידע לכהנים · 08-313-2020', data: { phone: PHONE } },
      '#btnDocs': { title: 'חוברות, עלונים ומצגות' }, '#btnDocs .lbl': { text: 'חוברות' },
      '#btnLoc': { title: 'המיקום שלי — פתיחת העיר הקרובה' },
      '[data-sec="abroad"]': { text: 'טיסות' }, '#btnLang': { hidden: true }
    },
    areaGroups: [['areas', 'אזורים אסורים לכהנים (מתוכנת הניווט של ההתאחדות)'], ['dist', 'נקודות להשגת המדריך לכהנים והמפות']],
    orgs: [
      { name: 'התאחדות טהרת הכהנים — קו המידע', what: 'מידע אוטומטי ומענה אנושי (שלוחה * מענה אנושי, שלוחה 9 עדכונים) · ' + EMAIL, phone: PHONE, url: 'https://hakohanim.org/', src: 'חתימת ההתאחדות ואתר hakohanim.org' },
      { name: 'קו השיעורים — קורס טלפוני בטומאת כהנים', what: 'קורס מקיף: התפשטות הטומאה, חיבור אהלים, בדיקת בתי חולים, פיקוח נפש', phone: '08-3024364', url: '', src: 'אתר hakohanim.org' },
      { name: 'שירות לקוחות — תוכנת הניווט לכהנים', what: 'במייל בלבד: M083132020@gmail.com', phone: 'M083132020@gmail.com', url: 'https://gps.hakohanim.org/', src: 'מייל ההתאחדות' }],
    hospitalsExtra: [{ id: 'assaf', name: 'אסף הרופא (שמיר)', city: 'באר יעקב', contacts: [] }],
    sources: [
      ['ויקרא כא — "אמור אל הכהנים"', 'ויקרא', 'כא א'],
      ['רמב"ם — הלכות אבל, פרק ג', 'הלכות אבל|משנה תורה אבל', 'ג'],
      ['רמב"ם — הלכות טומאת מת', 'הלכות טומאת מת|משנה תורה טומאת מת', 'א'],
      ['שולחן ערוך יורה דעה — הלכות טומאת כהן (שסט)', 'שולחן ערוך יורה דעה', 'שסט']],
    openTasks: [
      'הסרטונים של ההתאחדות (כ-1.2GB) — כרגע קישורים בלבד; גדולים מדי לתוסף (מגבלת 50MB)',
      'ניווט במסלול שעוקף אזורים אסורים — כרגע באתר gps.hakohanim.org בלבד (דורש שרת ניתוב)',
      'לוח טיסות בזמן אמת — כרגע הלוח הקבוע; זמן אמת רק באתר flights.hakohanim.org',
      'עדכון אוטומטי של האזורים והלוח מהאתרים של ההתאחדות (כמו העדכון השבועי בגבולות עירוב)',
      'קישור כל עיר לעמודים הרלוונטיים בתוך המדריך לכהנים'],
    changelog: [['2.2.0', ['תוסף חדש, באותו ממשק של "גבולות עירוב": כל החומר של התאחדות טהרת הכהנים, באישורם — המדריך לכהנים, חוברת המרכזים הרפואיים, מידע לבין הזמנים, מראות כהונה, אמור ואמרת והמצגות, בלי אינטרנט מלבד ההורדה.',
      'מפות לכהנים: מירון, צפת, טבריה, חיפה, הר הזיתים, הר הרצל, קבר דוד והר ציון, קבר שמואל הנביא, הדסה, איכילוב, תל השומר, אסף הרופא, כביש 444, נחל השופט ואומן — עם הגדלה, סיבוב, ייצוא והדפסה.',
      'מפת האזורים האסורים מתוכנת הניווט של ההתאחדות (רמות א/ב/ג, ושטחי A), וחיפוש כתובת שמראה אם היא בתוך אזור אסור.',
      'טיסות: לוח הנחיתות הטמאות בטרמינל 3 לפי ימי השבוע, ובדיקת "נוחתים / ממריאים בשעה…" (משוער — זמן אמת באתר).',
      'נקודות להשגת המדריך והמפות בכל עיר, רבני בתי החולים, ומקורות ללימוד בספריית אוצריא.',
      'דיווח קריסה (מתג באודות), קישורי הורדה מ-GitHub ומהחנות בכל ייצוא, כפתור בשדה החיפוש של אוצריא.']]],
    views: { home: homeView, docs: docsView, abroad: flightsView, hosps: hospsView, hosp: hospView },
    rail: { abroad: railAbroad, hosp: railHosp },
    layers, insideMsg,
    map: () => ({ layerId: 'kohanim', glyph: 'כ', layerName: 'ערים עם מידע לכהנים', self: ID, forumUrl: '', issueUrl: 'https://github.com/Hadabadra/gvulot-eruv/issues',
      pickLabel: 'פתיחת העיר', nearbyLabel: 'ערים קרובות', future: ['ניווט שעוקף אזורים אסורים (כרגע באתר ההתאחדות)', 'עדכון אוטומטי של האזורים מתוכנת הניווט'],
      guide: [{ t: 'אזורים אסורים לכהנים', d: `${levelCount('א')} אזורים ברמה א, ${levelCount('ב')} ברמה ב ו-${levelCount('ג')} ברמה ג, מתוך תוכנת הניווט של התאחדות טהרת הכהנים. חיפוש כתובת עם מספר בית מראה אם היא בתוך אזור. להתמצאות בלבד — המאגר אינו מלא.` },
        { t: 'ערים', d: 'כל נקודה היא עיר עם מפות או אזורים. "פתיחת העיר" מציגה את המפות, החוברות, האזורים ונקודות ההפצה.' }] }),
    halachaHTML: ctx => `<p>החומר בתוסף הוא של <b>התאחדות טהרת הכהנים</b> (בראשות הגר"ד מונק, הגר"א בייפוס והגר"י לומברד), באישורם.
      התוסף אינו פוסק הלכה ואינו קובע אם מקום מותר או אסור — הוא מרכז את המידע כדי להקל על הבירור.</p>
      <p>המצב בשטח משתנה (קברים שנמצאו, מנופים, נפטרים בבתי חולים ובטיסות). בכל ספק: קו המידע ${ctx.telChip(PHONE)} (מידע אוטומטי ומענה אנושי) או רב.</p>
      ${docCards(ctx, ['madrich', 'mk-summary', 'chevra-kadisha'])}`,
    aboutHTML: ctx => `<p>טהרת כהנים ${ctx.VERSION} · מאת לזש"ק לרמב"ר ומבק"י. כל החומר — המדריך, החוברות, המפות, האזורים ולוח הטיסות — מאת <b>התאחדות טהרת הכהנים</b> (hakohanim.org), באישורם, בתוך התוסף ובלי צורך באינטרנט.</p>
      <p>הממשק משותף עם התוסף "גבולות עירוב" (אותו קוד, באותו מאגר): כל שיפור בממשק מגיע לשניהם, ושניהם יוצאים באותה גרסה.
      <button class="btn text" data-plugin="com.hadabadra.gvulot-eruv">פתיחת גבולות עירוב</button></p>
      <div class="levels">
        <div class="level done"><span class="dot">1</span><div><b>החומר בתוך התוסף</b>${ctx.DOCS.length} חוברות ומצגות ו-${D.maps.length} מפות; הסרטונים — קישורים בלבד (גדולים מדי).</div></div>
        <div class="level done"><span class="dot">2</span><div><b>אזורים על המפה</b>${Object.keys(LINES).length} מצולעים מתוכנת הניווט, ובדיקת כתובת.</div></div>
        <div class="level part"><span class="dot">3</span><div><b>טיסות</b>לוח קבוע ובדיקת שעה; זמן אמת — באתר ההתאחדות.</div></div>
        <div class="level"><span class="dot">4</span><div><b>ניווט שעוקף אזורים</b>כרגע רק באתר gps.hakohanim.org.</div></div>
      </div><p>הנתונים נאספו ב-${ctx.esc(D.built)}.</p>`
  };
})();
