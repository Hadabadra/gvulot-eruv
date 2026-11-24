# עדכון החומר של טהרת כהנים — מדריך קצר

מיועד למי שיעדכן את התוסף בשביל התאחדות טהרת הכהנים (טכנאי/ת או מתכנת/ת עם גישה לריפו). עדכון רגיל לוקח כחצי שעה ואינו בנייה מחדש — רק החלפת קבצים והרצת סקריפט.

## מה מתעדכן ומאיפה
| חומר | מקור | איך |
|---|---|---|
| חוברות, מפות, מצגות | תיקיית הדרייב של ההתאחדות (הקישור במייל שלהם) | מורידים את התיקייה כולה ל-`kohanim-build/raw/drive/` |
| אזורים אסורים | gps.hakohanim.org | `python3 kohanim-build/fetch.py` |
| לוח הטיסות הקבוע | flights.hakohanim.org | `python3 kohanim-build/fetch.py` |
| תאריך "מעודכן ל..." | ידני | `dataDate` ושורת הכותרת ב-`kohanim/site.js` (כרגע: כסליו תשפ"ז) |

## הצעדים
1. `git clone https://github.com/Hadabadra/gvulot-eruv` (צריך הרשאת כתיבה — בקשה דרך Issue בריפו).
2. מורידים את תיקיית הדרייב העדכנית ל-`kohanim-build/raw/drive/` (אותם שמות קבצים; קובץ חדש — מוסיפים שורה ל-`MAPS`/`DOCS` בראש `kohanim-build/build.py`).
3. `python3 kohanim-build/fetch.py` ואז `python3 kohanim-build/build.py kohanim` (דורש gs, pdftoppm, img2pdf, Pillow, openpyxl).
4. מעדכנים את `dataDate` ב-`kohanim/site.js` ומעלים גרסה ב-`kohanim/manifest.json` וב-`gvulot-eruv/manifest.json` (שני התוספים יוצאים יחד).
5. `bash tools/sync-ui.sh`, קומיט, Pull Request ל-`main`. אחרי המיזוג ה-CI אורז ומפרסם את שני התוספים לחנות אוצריא לבד.

## עם בינה מלאכותית
אפשר לתת לעוזר קוד (כמו Claude Code) את הריפו ואת ההוראה:
"עדכן את טהרת כהנים לפי kohanim-docs/UPDATE.md מהתיקייה המצורפת, העלה גרסה ופתח PR".

מגבלה: החבילה בחנות עד 50MB (היום כ-43MB). סרטונים לא נכנסים — רק קישורים.
