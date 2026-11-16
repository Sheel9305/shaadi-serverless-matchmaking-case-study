#!/usr/bin/env bash
# Run every local check: project validation, lint, JS syntax, tests with coverage.
#   bash scripts/run_tests.sh          (activate the virtualenv first, or set PYTHON=.venv/bin/python)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
PY="${PYTHON:-python}"

echo "== 1/4 Project validation (compile, imports, JSON, YAML, links, secrets) =="
"$PY" scripts/validate_project.py

echo "== 2/4 Lint (ruff) =="
"$PY" -m ruff check .

echo "== 3/4 Frontend + k6 JavaScript syntax (node --check) =="
if command -v node >/dev/null 2>&1; then
  for f in frontend/*.js; do node --check "$f" && echo "OK  $f"; done
  for f in experiments/k6/*.js; do node --check --input-type=module < "$f" && echo "OK  $f (module syntax only)"; done
else
  echo "SKIP: node not installed"
fi

echo "== 4/4 pytest + coverage =="
"$PY" -m pytest --cov --cov-report=term-missing --cov-report=xml:test_reports/coverage.xml --junitxml=test_reports/junit.xml
