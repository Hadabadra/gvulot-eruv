#!/usr/bin/env bash
# מפה משותפת (Prayer-pointA#11): המקור הראשי של קוד המפה הוא shared/ במאגר Hadabadra/Mikvaot.
# מוריד את הקבצים המשותפים ל-shared/ ולתיקיית התוסף. רץ ב-CI לפני כל אריזה (eruv-release.yml) ואפשר גם ידנית.
# לא עורכים כאן את map-core.js / map-ui.js — מתקנים ב-Mikvaot/shared בלבד.
set -e
cd "$(dirname "$0")/.."
RAW="https://raw.githubusercontent.com/Hadabadra/Mikvaot/main/shared"
for f in map-core/map-core.js map-core/map-ui.js map-core/README.md map-core/SHARED-MAP.md map-core/test.js streets/streets-cities.js streets/cities.json basemap/world-basemap.js; do
  mkdir -p "shared/$(dirname "$f")"; curl -fsSL "$RAW/$f" -o "shared/$f.tmp" && mv "shared/$f.tmp" "shared/$f"
done
for f in map-core/map-core.js map-core/map-ui.js streets/streets-cities.js basemap/world-basemap.js; do cp "shared/$f" "gvulot-eruv/$(basename "$f")"; done
echo "סונכרן מ-Mikvaot/shared"
