# דיווח תקלות אוטומטי + מה חדש ב-SDK של אוצריא 0.9.98.3 (בדיקה 03.11.2026)

מקור: `Otzaria/otzaria` ענף `dev`, `docs/plugin-sdk/API_REFERENCE.md` (נבדק 03.11.2026).

## מערכת הדיווחים (feedback.report)
- `feedback.report({ details, reportType, reporterEmail })` — `reportType`: `bug` / `crash` / `content` / `other` (ערך אחר הופך ל-`other`; לכן תוקן בעירוב `'feedback'` ← `'other'`).
- **אין שליחה שקטה:** אוצריא מציגה תמיד דיאלוג אישור עם תצוגה מקדימה. אין דרך לעקוף. לכן "דיווח קריסה אוטומטי" = התוסף תופס את השגיאה ומציע למשתמש לשלוח, והדיאלוג של אוצריא מאשר.
- **בלי אינטרנט:** הדיווח נשמר בתור מקומי (`'queued'`) ונשלח לבד כל 5 דקות כשיש חיבור; המשתמש מנהל את התור בהגדרות.
- לא דורש הרשאה. הדיווח מגיע לאתר אוצריא ← למייל המפתחת ← הסקריפט של Google Apps Script פותח issue בגיטהאב עם התווית "דיווח-משתמש".
- `feedback.hasReporterEmail` — לבדוק אם צריך לבקש כתובת.

## הרכיב `crash-report.js`
- `CrashReport.init({ call, plugin, version })` — תופס `error` ו-`unhandledrejection`, מציג הודעה קטנה "אירעה תקלה" עם "שליחת דיווח למפתח" / "לא עכשיו" / "לא להציע שוב" (נשמר ב-storage במפתח `crashReportOff`).
- הדיווח כולל: שם התוסף וגרסתו, ההודעה, המחסנית (עד 1,800 תווים), גרסת אוצריא (`app.getInfo`). נתיבי משתמש (`C:\Users\<שם>`) מוסתרים.
- `CrashReport.report(msg, stack)` — דיווח ידני על שגיאה שהתוסף תפס בעצמו.
- כל תוסף מעתיק את הקובץ כמו שהוא: מקוואות `tools/sync-shared.sh`, גבולות עירוב — ה-CI מוריד לפני האריזה.

## חדש ב-0.9.98.3 (אין שיטות API חדשות — רק אפשרויות במניפסט)
- `searchDialogItems`: `type: "switch"`, `persist: false` (בחירה חד-פעמית), `resultsAction` (כפתור בטאב החיפוש שמעביר את החיפוש לתוסף).
- `searchFieldActions`: `visibleWhen: "nonEmptyText"`, `mode: "providerBooksFilter"` + `libraryOnlyIcon`, והקשר חיפוש מלא באירוע `search.fieldAction.invoked`.
- נתונים: לכל ערך ארמי יש `dictionary`; מאגר האישים הוחלף ב"תולדות גדולי ישראל" (`formatVersion: 2`).
- כל אלה דורשים `minAppVersion: "0.9.98.3"`. **למקוואות ולגבולות עירוב אין בהם צורך** (אין להם ספקי חיפוש). רלוונטי ללשון הקודש (חיפוש) ולאישים — לבחינה בשיחה שלהם.
- ב-0.9.98.1 (כבר קיים): `feedback.submitBookCorrection`, `reader.reportTextReaderLocation`.
