// תרגום בסיסי לאנגלית: כפתורים, כותרות, ניווט, שמות ערים ובתי חולים.
// עובד בהחלפת טקסט מדויק אחרי כל ציור (MutationObserver), בלי לגעת בלוגיקה של app.js.
// תוכן (שכונות, אחראים, חוברות, הסברים ארוכים) נשאר בעברית.
(function () {
  const W = {
    // מסגרת וכפתורים
    'גבולות עירוב': 'Eruv Borders', 'כל הארץ': 'All Israel', 'ישראל': 'Israel', 'חו"ל': 'Abroad', 'בתי חולים': 'Hospitals',
    'ערים': 'Cities', 'ארצות': 'Countries', 'חיפוש': 'Search', 'כל הערים': 'All cities', 'המיקום שלי': 'My location',
    'אודות': 'About', 'מידע הלכתי': 'Halachic info', 'תחום שבת וחוברות': 'Techum & booklets', 'ניווט ראשי': 'Main navigation',
    'סגירה': 'Close', 'הגדלה': 'Zoom in', 'הקטנה': 'Zoom out', 'התאמה למסך': 'Fit', 'סיבוב': 'Rotate', 'ייצוא': 'Export',
    'אחראים': 'Contacts', 'העמוד הבא': 'Next page', 'העמוד הקודם': 'Previous page', 'מספר עמוד': 'Page number',
    'אודות גבולות עירוב': 'About Eruv Borders', 'אודות התוסף': 'About', 'הדפסה / שמירה כ-PDF': 'Print / save as PDF',
    'שמירה כתמונה JPG': 'Save as JPG', 'שמירה כתמונה PNG': 'Save as PNG', 'שליחה': 'Send', 'שליחת תגובה': 'Send feedback',
    'עיר, שכונה, רחוב או שם האחראי': 'City, neighborhood, street or contact name',
    'כל הערים — דף הבית': 'All cities', 'אודות ומקור הנתונים': 'About and data source', 'מידע הלכתי ומקורות': 'Halachic info and sources',
    'תחום שבת, חוברות וספרייה': 'Techum, booklets and library', 'המיקום שלי — פתיחת העיר הקרובה': 'My location — open the nearest city',
    'ייצוא: תמונה או הדפסה': 'Export: image or print', 'אחראים במפה זו': 'Contacts for this map',
    'המפות להתמצאות בלבד. עירוב יכול להיפסל בכל שבוע, ולכן לפני שבת יש לוודא מול האחראי המקומי.':
      'Maps are for orientation only. An eruv can become invalid any week — before Shabbat, confirm with the local contact.',
    'מוקד העירוב · 054-8483320': 'Eruv Hotline · 054-8483320', 'מוקד העירוב': 'Eruv Hotline (hiruv.com)',
    'גלגלת או צביטה להגדלה · גרירה להזזה · לחיצה כפולה להגדלה מהירה': 'Scroll or pinch to zoom · drag to pan · double-click to zoom',
    // כותרות מקטעים
    'אחראים לפי שכונה': 'Contacts by neighborhood', 'ארגונים': 'Organizations', 'חוברות': 'Booklets', 'מפות': 'Maps',
    'נצפו לאחרונה': 'Recently viewed', 'ספריית העירובין': 'Eruv library', 'ספריית העירובין של המוקד': "The hotline's eruv library",
    'עירוב בתוך המתחם': 'Eruv on the campus', 'עירובין בחו"ל': 'Eruvin abroad', 'רב בית החולים ושירותי הדת': 'Hospital rabbi and religious services',
    'תחום שבת': 'Techum Shabbat', 'תחום שבת ועירוב תחומין': 'Techum Shabbat and eruv techumin', 'תחום שבת לפי עיר': 'Techum by city',
    'בתי חולים נוספים — עמודי שירותי הדת הרשמיים': 'More hospitals — official religious-services pages',
    'בתי חולים בשבת': 'Hospitals on Shabbat', 'בתי חולים בחו"ל': 'Hospitals abroad', 'גבולות העירובים השכונתיים': 'Neighborhood eruv borders',
    'תחום שבת וחוברות': 'Techum & booklets', 'בתכנון': 'Planned', 'יומן שינויים': 'Changelog', 'מידע לשבת': 'Shabbat info',
    'אתר העירוב': 'Eruv website', 'אתר': 'Website', 'הוספת מפה משלי': 'Add my own map', 'רב בית החולים': 'Hospital rabbi',
    'עוזר הרב': "Rabbi's assistant", 'לא פורסם טלפון ישיר': 'No direct phone published', 'אחראים בלבד': 'Contacts only',
    'רשימת אחראים': 'Contacts', 'מפה כללית': 'General map', 'כל החוברת': 'Whole booklet', 'מקור:': 'Source:',
    'עברית': 'עברית', 'English': 'English',
    // ערים
    'אופקים': 'Ofakim', 'אלעד': 'Elad', 'אשדוד': 'Ashdod', 'באר שבע': "Be'er Sheva", 'בית שמש': 'Beit Shemesh', 'ביתר': 'Beitar Illit',
    'בני ברק': 'Bnei Brak', 'בת ים': 'Bat Yam', 'גבעת זאב': "Giv'at Ze'ev", 'גני תקוה': 'Ganei Tikva', 'זכרון יעקב': "Zichron Ya'akov",
    'חדרה': 'Hadera', 'חזון יחזקאל': 'Chazon Yechezkel', 'חיפה': 'Haifa', 'חצור': 'Hatzor', 'טבריה': 'Tiberias', 'יסודות': 'Yesodot',
    'ירוחם': 'Yeruham', 'ירושלים': 'Jerusalem', 'כרמיאל': "Karmi'el", 'לוד (אחיסמך)': 'Lod (Achisamach)', 'מודיעין עילית': "Modi'in Illit",
    'מיצד': 'Meitzad', 'מירון': 'Meron', 'נוף הגליל': 'Nof HaGalil', 'נתיבות': 'Netivot', 'נתניה': 'Netanya', 'עמנואל': 'Emmanuel',
    'עפולה': 'Afula', 'פתח תקוה': 'Petah Tikva', 'צפת': 'Tzfat', 'קרית אתא': 'Kiryat Ata', 'קרית יערים (טלזסטון)': 'Kiryat Ye\'arim (Telz-Stone)',
    'קרית מלאכי': 'Kiryat Malachi', 'רחובות': 'Rehovot', 'רכסים': 'Rechasim', 'תל ציון': 'Tel Zion', 'תפרח': 'Tifrach',
    'תל אביב': 'Tel Aviv', 'ניו יורק': 'New York', 'ברוקלין': 'Brooklyn', 'בולטימור': 'Baltimore', 'תחום': 'Techum', 'רמת גן': 'Ramat Gan', 'חולון': 'Holon',
    // בתי חולים
    'שערי צדק': 'Shaare Zedek', 'הדסה עין כרם': 'Hadassah Ein Kerem', 'מעיני הישועה': "Ma'ayanei HaYeshua", 'לניאדו': 'Laniado',
    'בילינסון (רבין)': 'Beilinson (Rabin)', 'שניידר': 'Schneider', 'איכילוב': 'Ichilov', 'תל השומר (שיבא)': 'Tel HaShomer (Sheba)', 'וולפסון': 'Wolfson'
  };
  // ביטויים עם מספרים
  const P = [
    [/^(\d+) מפות$/, '$1 maps'], [/^(\d+) מפות · (\d+) שכונות$/, '$1 maps · $2 neighborhoods'], [/^אחראים בלבד · (\d+) שכונות$/, 'Contacts only · $1 neighborhoods'],
    [/^(\d+) אחראים$/, '$1 contacts'], [/^(.+) · מידע לשבת$/, (m, a) => (W[a] || a) + ' · Shabbat info']
  ];
  let lang = 'he';
  try { lang = localStorage.getItem('eruv-lang') || 'he'; } catch (e) {}
  const tr = s => {
    const t = s.trim(); if (!t || !/[א-ת]/.test(t)) return null;
    if (W[t]) return s.replace(t, W[t]);
    for (const [re, to] of P) if (re.test(t)) return s.replace(t, t.replace(re, to));
    return null;
  };
  const ATTRS = ['title', 'placeholder', 'aria-label'];
  function apply(root) {
    if (lang !== 'en' || !root) return;
    const tw = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    const nodes = []; while (tw.nextNode()) nodes.push(tw.currentNode);
    for (const n of nodes) { if (n.parentElement && n.parentElement.closest('textarea,script,style')) continue; const r = tr(n.nodeValue); if (r !== null && r !== n.nodeValue) n.nodeValue = r; }
    const els = root.querySelectorAll ? root.querySelectorAll('[title],[placeholder],[aria-label]') : [];
    for (const el of els) for (const a of ATTRS) { const v = el.getAttribute(a); if (v) { const r = tr(v); if (r !== null && r !== v) el.setAttribute(a, r); } }
  }
  function setLang(l) {
    lang = l; try { localStorage.setItem('eruv-lang', l); } catch (e) {}
    location.reload();
  }
  window.ERUV_I18N = { get lang() { return lang; }, setLang, t: s => (lang === 'en' && W[s]) || s };
  function init() {
    const b = document.getElementById('btnLang');
    if (b) { b.textContent = lang === 'en' ? 'עב' : 'EN'; b.title = lang === 'en' ? 'עברית' : 'English'; b.onclick = () => setLang(lang === 'en' ? 'he' : 'en'); }
    if (lang !== 'en') return;
    document.documentElement.lang = 'en'; document.documentElement.dir = 'ltr';
    document.title = 'Eruv Borders';
    apply(document.body);
    let busy = false;
    new MutationObserver(ms => { if (busy) return; busy = true; try { for (const m of ms) for (const n of m.addedNodes) n.nodeType === 1 ? apply(n) : n.nodeType === 3 && n.parentElement && apply(n.parentElement); if (ms.some(m => m.type === 'characterData' || m.type === 'attributes')) apply(document.body); } finally { busy = false; } })
      .observe(document.body, { childList: true, subtree: true, characterData: true, attributes: true, attributeFilter: ATTRS });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
