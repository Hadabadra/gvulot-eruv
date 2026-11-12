#!/usr/bin/env bash
# ממשק אחד לשני תוספים (2.2.0): המקור של הממשק הוא gvulot-eruv/. הסקריפט מעתיק אותו לתוסף טהרת כהנים (kohanim/).
# בתוך kohanim/ נשמרים ב-git רק התוכן וההגדרות (manifest.json, icon.png, site.js, data.js, docs.js, extra.js, eruv-lines.js, flights.js, maps/, docs/).
# קבצי הממשק המועתקים מופיעים ב-kohanim/.gitignore. רץ ב-CI לפני האריזה (אחרי sync-shared.sh), ואפשר גם ידנית.
# לא עורכים את קבצי הממשק בתוך kohanim/ — רק ב-gvulot-eruv/.
set -e
cd "$(dirname "$0")/.."
UI="index.html app.css app.js bridge.js i18n.js map-core.js map-ui.js world-basemap.js streets-cities.js streets pdfjs shared"
for f in $UI; do rm -rf "kohanim/$f"; cp -r "gvulot-eruv/$f" "kohanim/$f"; done
echo "הממשק הועתק מ-gvulot-eruv/ ל-kohanim/"
