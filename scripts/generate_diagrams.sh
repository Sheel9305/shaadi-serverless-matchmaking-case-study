#!/usr/bin/env bash
# Render every docs/diagrams/*.mmd file to SVG and PNG with mermaid-cli.
# Requires Node.js 18+. The first run downloads @mermaid-js/mermaid-cli and a headless Chromium.
#
#   bash scripts/generate_diagrams.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$ROOT/docs/diagrams"
OUT="$SRC/rendered"
MMDC_VERSION="${MMDC_VERSION:-11.4.2}"
mkdir -p "$OUT"

# Optional overrides:
#   MMDC=/path/to/mmdc                      use a specific mermaid-cli binary
#   PUPPETEER_CONFIG=/path/puppeteer.json   e.g. {"executablePath": "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"}
#                                           to reuse an installed Chrome instead of downloading Chromium
#                                           (install with: PUPPETEER_SKIP_DOWNLOAD=true npm i -g @mermaid-js/mermaid-cli)
if [ -n "${MMDC:-}" ]; then MMDC=("$MMDC");
elif command -v mmdc >/dev/null 2>&1; then MMDC=(mmdc);
else MMDC=(npx -y "@mermaid-js/mermaid-cli@${MMDC_VERSION}"); fi
if [ -n "${PUPPETEER_CONFIG:-}" ]; then MMDC+=(-p "$PUPPETEER_CONFIG"); fi

status=0
for f in "$SRC"/*.mmd; do
  name="$(basename "$f" .mmd)"
  for ext in svg png; do
    extra=()
    [ "$ext" = png ] && extra=(--scale 2)
    # ${extra[@]+...} keeps macOS bash 3.2 happy when the array is empty under `set -u`.
    if "${MMDC[@]}" -i "$f" -o "$OUT/$name.$ext" -b white ${extra[@]+"${extra[@]}"} >/dev/null 2>&1 && [ -s "$OUT/$name.$ext" ]; then
      echo "OK    $name.$ext ($(wc -c < "$OUT/$name.$ext" | tr -d ' ') bytes)"
    else
      echo "FAIL  $name.$ext"; status=1
    fi
  done
done
exit $status
