# רכיב משותף: המלצה על "אחת שאלתי" (גרסה 1.1.0)

מקור יחיד (מ-03.11.2026): `Hadabadra/Mikvaot` → `shared/promo/` — יחד עם המפה המשותפת (`shared/map-core`), מפת העולם (`shared/basemap`) ודיווח התקלות (`shared/report`). העותק ב-KLI-MULON הוא העתק בלבד. כל תוסף **מעתיק את שני הקבצים כמו שהם** (`achat-promo.js`, `achat-promo.css`) — לא עורכים אותם בתוך תוסף. שינוי נעשה כאן ומועתק מחדש לכל התוספים (כמו המפה המשותפת).

## מה הרכיב עושה
- **פופאפ קטן** בפינת המסך: טקסט ההמלצה, כפתורי "להורדה" ו"להסבר בפורום", "אל תציג שוב" ו-✕.
- **תדירות:** לכל היותר פעם בשבוע; לא ביום הפתיחה הראשונה (יום אחד לפחות מהפתיחה הראשונה, ופתיחה שנייה לפחות).
- **"אל תציג שוב"** ומתג **"הצג המלצות"** בהגדרות — נשמרים ב-storage של התוסף במפתח `achatPromo`.
- **שורה קבועה ב"אודות"** — מוצגת תמיד, בלי פופאפ ובלי תלות במתג.
- **ללא אינטרנט** (מצב "ללא גישה לאינטרנט" של אוצריא, `app.getConnectivity().isOfflineMode`): במקום הקישורים — כפתור "שמור דף הסבר וקישורים", ששומר `אחת שאלתי - הסבר וקישורים להורדה.html` — דף מעוצב עם הסבר, הוראות התקנה וקישורים לחיצים, וקישורי ההורדה של התוסף עצמו (GitHub + חנות).

## שילוב בתוסף
1. העתיקו את `achat-promo.js` ו-`achat-promo.css` לתיקייה `shared/promo/` שבתוסף, וטענו:
   ```html
   <link rel="stylesheet" href="shared/promo/achat-promo.css">
   <script src="shared/promo/achat-promo.js"></script>
   ```
2. אתחול (פעם אחת, אחרי שיש עטיפת `call` ל-SDK):
   ```js
   AchatPromo.init({ call, plugin: "שם התוסף", links: { gh: "https://github.com/…/releases/latest", store: "https://otzaria.org/plugins/…" } });
   ```
   אופציונלי: `isOnline: async () => bool` (אם לתוסף יש בדיקה משלו), `forumUrl`, `downloadUrl`.
3. בפתיחה **מתפריט הכלים בלבד** (לא בפתיחה מבחירת מילה/הודעה): `AchatPromo.maybeShow()`.
4. הגדרות: להוסיף `AchatPromo.settingsHtml()` לכרטיס, ואחרי הצבת ה-HTML — `AchatPromo.bind(container)`.
5. אודות: להוסיף `AchatPromo.aboutHtml()`, ואחרי הצבה — `AchatPromo.bind(container)`.

## דרישות
- הרשאות: `plugin.storage.read`, `plugin.storage.write`, `app.open_url`, `app.info.read` (ל-`app.getConnectivity`).
- אסימוני `:root`: `--color-primary`, `--color-on-primary`, `--color-primary-subtle`, `--color-surface`, `--color-surface-container-low`, `--color-surface-container-high`, `--color-on-surface`, `--color-on-surface-variant`, `--color-outline-variant`, `--color-shadow`, `--font-ui`, `--radius-lg`, `--radius-pill`. אין צבע קבוע מחוץ ל-`:root` (תגית "מראה תואם"), כל המידות ב-em.

## קישורים
- הסבר בפורום: נושא 2777 בפורום אוצריא ("להורדה אחת שאלתי - תוכנת חסימה (קיוסק) למחשב - ללימוד בלבד!") — `DEF.forumUrl`.
- הורדה: https://github.com/achat-shaalti/achat-shaalti/releases — `DEF.downloadUrl`.

## שינויים
- 1.1.0: במצב מנותק נשמר דף HTML עם קישורים לחיצים והוראות (במקום קובץ טקסט); שורת "מאת רובע היהודי" (`author`).
