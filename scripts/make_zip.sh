#!/usr/bin/env bash
# Create a clean ZIP of the repository for submission (no venv, caches, secrets or build output).
#   bash scripts/make_zip.sh            -> dist/shaadi-cloud-case-study.zip
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
NAME="$(basename "$ROOT")"
mkdir -p "$ROOT/dist"
OUT="$ROOT/dist/${NAME}.zip"
rm -f "$OUT"
cd "$(dirname "$ROOT")"
zip -rq "$OUT" "$NAME" \
  -x "$NAME/.venv/*" "$NAME/venv/*" "$NAME/dist/*" "$NAME/.git/*" \
     "*/__pycache__/*" "*.pyc" "$NAME/.pytest_cache/*" "$NAME/.ruff_cache/*" \
     "$NAME/.coverage" "$NAME/test_reports/coverage.xml" "$NAME/test_reports/junit.xml" \
     "$NAME/infrastructure/.aws-sam/*" "*/.DS_Store" "$NAME/.env" "$NAME/.env.*" "*/node_modules/*"
echo "Created $OUT ($(du -h "$OUT" | cut -f1))"
unzip -l "$OUT" | tail -1
