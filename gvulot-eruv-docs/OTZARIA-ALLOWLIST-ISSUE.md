# בקשה לאוצריא: הוספת hiruv.com לרשימת האתרים המותרים לתוספים

להגשה כ-issue במאגר Otzaria/otzaria: https://github.com/Otzaria/otzaria/issues/new
(בקשות דומות הוגשו שם כ-PR בשם "allowlist: ..." לקובץ `plugin_network_allowlist.txt`, למשל #2726.)
הכתובת `raw.githubusercontent.com/Hadabadra` כבר התבקשה ב-issue #2185, ולכן כאן מבוקש רק hiruv.com.

---

**כותרת:**
allowlist: hiruv.com לתוסף גבולות עירוב (com.hadabadra.gvulot-eruv)

**גוף:**

התוסף "גבולות עירוב" (`com.hadabadra.gvulot-eruv`, https://github.com/Hadabadra/gvulot-eruv) מציג את מפות העירובים השכונתיים ואת רשימת האחראים של מוקד העירוב (hiruv.com), באישור המוקד.

כיום כל הנתונים ארוזים בתוך התוסף, ועדכון של מפה או של טלפון של אחראי מגיע למשתמשים רק בגרסה חדשה. העירובים משתנים לעתים קרובות, ולכן חשוב שהמידע יהיה עדכני.

מבוקש להוסיף ל-`plugin_network_allowlist.txt`:

```
hiruv.com
```

- שימוש: קריאה בלבד (GET), לכל היותר פעם אחת בפתיחת התוסף, כדי לבדוק אם יש עדכון.
- התוסף ממשיך לעבוד בלי אינטרנט, עם הנתונים הארוזים בו.
- לא נשלח שום מידע מהמשתמש.
- האתר של המוקד זמין רק ב-http (ב-https מתקבלת שגיאת TLS). אם נדרש https בלבד, יספיק `raw.githubusercontent.com/Hadabadra` שכבר התבקש ב-#2185: במאגר רץ כל שבוע workflow שמושך מהמוקד ומפרסם קובץ נתונים מעודכן.

תודה.
