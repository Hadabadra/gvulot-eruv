# גבולות עירוב — מצב (12.11.2026)

**הגרסה: 2.2.0 יציבה (stable). מושהה עד ~מאי 2027.** אין issues או PRs פתוחים.

## מ-2.2.0: שני תוספים, ממשק אחד
- במאגר גם **טהרת כהנים** (`kohanim/`, id `com.hadabadra.tahorat-kohanim`) — מצב ותכנון ב-`kohanim-docs/STATUS.md`.
- **הממשק נכתב פעם אחת ב-`gvulot-eruv/`** (index.html, app.js, app.css, bridge, i18n, המפה, pdfjs, shared). `tools/sync-ui.sh` מעתיק אותו ל-`kohanim/` (ב-CI, ואפשר ידנית); שם הוא ב-.gitignore. **לא עורכים ממשק בתוך kohanim/.**
- מה שונה בין התוספים נמצא ב-`site.js` של כל תוסף (`window.SITE`): שם, טקסטים (`text`), טקסטים ב-HTML (`dom`), רשימות (hospitals/orgs/sources/openTasks/changelog), שכבות מפה (`layers`), בדיקת כתובת (`insideMsg`), תצוגות (`views`, `rail`), אודות ומידע הלכתי. בלי הגדרה — ברירת המחדל ב-app.js היא של העירוב.
- **כל גרסה לשניהם:** version זהה בשני ה-manifest (CI נכשל אחרת) וב-`version` של שני ה-site.js. `eruv-release.yml` אורז את שניהם, Release אחד עם שני הקבצים, ופרסום לחנות של שניהם (matrix). העדכון השבועי (`auto_update.py`) מעלה גרסה לשניהם.
- רכיב משותף חדש: `SIBLINGS` ב-app.js מוסיף כל תוסף לתפריט השכבות של המפה של השני (`MapUI.PLUGINS`), וכפתור `data-plugin` פותח אותו (`plugin.openOther`, ואם אינו מותקן — דף החנות).

- מאגר: Hadabadra/gvulot-eruv, ענף main. דחיפה ל-main עם גרסה חדשה ב-`gvulot-eruv/manifest.json` → CI אורז (`gvulot-eruv-build/pack.py`), יוצר Release ומפרסם לחנות (`.github/workflows/eruv-release.yml`, סודות OTZARIA_USER/PASSWORD).
- הקוד המשותף (מפה, רחובות, דיווח קריסה, המלצה) מגיע מ-Hadabadra/Mikvaot `shared/` — ה-CI מוריד אותו לפני האריזה (`tools/sync-shared.sh`). מתקנים שם בלבד.
- עדכון שבועי אוטומטי של המפות מהמוקד: `.github/workflows/eruv-auto-update.yml`.
- גודל החבילה כ-45MB (המגבלה בחנות 50MB) — לבדוק לפני הוספת תוכן כבד.

## מה נכנס ב-2.1.0 (12.11.2026)
- #16 טהרת כהנים: `KOHANIM` ב-app.js (קישורי התאחדות טהרת הכהנים) + הארגון ב-ORGS. **המפות עצמן לא בתוסף** — נשלחות רק במייל (a083132020@gmail.com) ואין הצהרת רשות להפצה; נוצרה טיוטת מייל בקשה בחשבון Gmail שלה (לשליחה על ידה). כשיגיעו + אישור — להוסיף כחוברות (DOCS).
- `COUNCIL_ERUV`: מחלקות עירוב של מועצות דתיות בערים בלי מפת מוקד (אשקלון, ת"א, מבשרת, אזור, נס ציונה, חריש) — מאתרי המועצות, בסעיף נפרד "לא מטעם מוקד העירוב".
- ערבתם (מאומת מעלון הארגון), עירוב כהלכה (eruv.org.il), אתרים שומרי שבת (#13).
- מיקום לפי העיר בלוח השנה של אוצריא (`settings.get key-selected-city` + `calendar.getCities`; הרשאות settings.read, calendar.read).
- סמלי סרגל עם תוויות (`.icon-btn > .lbl`).
- אימות מקורות: מוקד העירוב (מפות + אחראים) ללא שינוי. דף "חוברות וספרים" **הוסר מאתר המוקד** — build_extra.py שומר את הרשימה הקודמת (הקבצים עדיין זמינים), auto_update.py לא נכשל עליו. eruv.org רוענן (291 דפים; האתר איטי — להוריד בהדרגה, `build_eruvorg.py --parse` מדלג על דף חסר). sources.lock.json עודכן.

## מה נכנס ב-2.0.0
- #15 חזון יחזקאל = אלומה (סמוך לקוממיות) בחיפוש, בכותרת ובמפה (`CITY_AKA`, `CITY_POS` ב-app.js).
- #14 מפת כל ירושלים ברזולוציה גבוהה: `HIRES` ב-`gvulot-eruv-build/build_data.py` מוריד את המקור בלי "-scaled" (3600px). מפה מטושטשת נוספת — מוסיפים את המזהה שלה ל-HIRES.
- #13 "ערבתם" בארגונים (לפי דיווח משתמש), סמל מסמך לכפתור החוברות.
- דיווח קריסה 1.1.0 + מתג באודות; הדפסת PDF שנשמר (`ui.printFile`).

## בדיקת SDK (Otzaria/otzaria dev, docs/plugin-sdk, 11.11.2026)
- כבר בשימוש: `plugin.setRestoreState`, `searchFieldActions` (visibleWhen), `app.getConnectivity`, `fs.beginBinaryWrite`/`commitUserFileWrite`, `reader.openBookAtRef`, קיצור מקשים, כפתור בסרגל הקורא.
- נוסף: `ui.printFile` (0.9.98.1) להדפסת חוברת שנשמרה כ-PDF.
- לא מתאים כרגע: `app.getDivineNamesDisplay` / `events.setOptions` (אין טקסט עם שמות קודש מהקורא), `network.fetchFile` (הכל ארוז בתוסף). פיצ'רים של 0.9.99 (`pluginOnlyLabel`, `when` ב-searchFieldActions, `newTab`) — רק אחרי שאוצריא 0.9.99 תצא, כי הם מחייבים minAppVersion 0.9.99.

## נשאר פתוח (לאחר ההשהיה)
- קווי עירוב אמיתיים מעבר לפיילוט (קרית אתא, חדרה): אין מקור וקטורי; שכבת GovMap דורשת הרצה מישראל.
- מפות בית שמש (#4, #8 ישנים) ודירוג רמות העירוב — ממתינים למוקד (`MOKED-REQUEST.md`).
- בקשת allowlist ל-hiruv.com באוצריא — הטקסט ב-`OTZARIA-ALLOWLIST-ISSUE.md`, להגשה על ידה.
- (נסגר ב-2.2.0) מפות טהרת כהנים — עברו לתוסף נפרד "טהרת כהנים".
- ערים נוספות מהמועצות הדתיות — רק טלפונים/קישורים; מפות בתוך התוסף רק באישור המועצה.
- מספרי בתים במצב לא מקוון; מפות לא מקוונות מלאות (PLAN §6); שאלת קישור ל-MapsOffline; האם לאחד עם מקוואות (ההחלטה שלה).
