#!/usr/bin/env bash
# Генерация PDF-версий документации из HTML через headless Chrome.
# Требует: локальный HTTP-сервер не нужен — используются file:// ссылки.
# Запуск: scripts/build-pdf.sh
set -euo pipefail
cd "$(dirname "$0")/.."

CHROME="${CHROME:-}"
for c in "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
         "/Applications/Chromium.app/Contents/MacOS/Chromium" \
         "$(command -v google-chrome || true)" "$(command -v chromium || true)"; do
  [ -n "$CHROME" ] && break
  [ -x "$c" ] && CHROME="$c"
done
[ -n "$CHROME" ] || { echo "Chrome/Chromium не найден; задайте CHROME=/path/to/chrome" >&2; exit 1; }

mkdir -p docs/pdf
for name in functional requirements install user-guide admin-guide lifecycle; do
  src="$PWD/docs/$name.html"
  out="$PWD/docs/pdf/xmark-$name.pdf"
  "$CHROME" --headless=new --disable-gpu --no-pdf-header-footer \
    --run-all-compositor-stages-before-draw --virtual-time-budget=5000 \
    --print-to-pdf="$out" "file://$src" 2>/dev/null
  printf '%-14s %6s KB\n' "$name" "$(( $(stat -c%s "$out" 2>/dev/null || stat -f%z "$out") / 1024 ))"
done
echo "PDF: docs/pdf/"
