#!/usr/bin/env bash
# רכיב משותף "אחת שאלתי" — המקור היחיד: Hadabadra/KLI-MULON shared/promo/. לא עורכים את העותק כאן; מתקנים שם ומריצים שוב.
set -e
cd "$(dirname "$0")/.."
P="$(basename "$PWD" | tr 'A-Z' 'a-z')"; [ -d "$P" ] || P=mikvaot
RAW="https://raw.githubusercontent.com/Hadabadra/KLI-MULON/main/shared/promo"
mkdir -p "$P/shared/promo"
for f in achat-promo.js achat-promo.css; do curl -fsSL "$RAW/$f" -o "$P/shared/promo/$f"; done
echo "סונכרן: shared/promo → $P/shared/promo"
