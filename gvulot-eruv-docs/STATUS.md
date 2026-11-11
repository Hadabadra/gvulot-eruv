# גבולות עירוב — מצב (11.11.2026)

**הגרסה: 2.0.0 יציבה (stable). מושהה עד ~מאי 2027.** אין issues או PRs פתוחים.

- מאגר: Hadabadra/gvulot-eruv, ענף main. דחיפה ל-main עם גרסה חדשה ב-`gvulot-eruv/manifest.json` → CI אורז (`gvulot-eruv-build/pack.py`), יוצר Release ומפרסם לחנות (`.github/workflows/eruv-release.yml`, סודות OTZARIA_USER/PASSWORD).
- הקוד המשותף (מפה, רחובות, דיווח קריסה, המלצה) מגיע מ-Hadabadra/Mikvaot `shared/` — ה-CI מוריד אותו לפני האריזה (`tools/sync-shared.sh`). מתקנים שם בלבד.
- עדכון שבועי אוטומטי של המפות מהמוקד: `.github/workflows/eruv-auto-update.yml`.
- גודל החבילה כ-45MB (המגבלה בחנות 50MB) — לבדוק לפני הוספת תוכן כבד.

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
- #16 רעיון: מפות טומאת כהנים (מקור שהוצע: כתובת מייל) — תוכן חדש, צריך מקור מאושר ובדיקה. ב-PLAN.md.
- #13 "אתרים שומרי שבת" — לא קשור לעירובין, לא נוסף.
- מספרי בתים במצב לא מקוון; מפות לא מקוונות מלאות (PLAN §6); שאלת קישור ל-MapsOffline; האם לאחד עם מקוואות (ההחלטה שלה).
