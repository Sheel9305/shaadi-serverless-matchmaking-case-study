# Windows PowerShell equivalent of scripts/run_tests.sh
#   powershell -ExecutionPolicy Bypass -File scripts\run_tests.ps1
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
$py = if ($env:PYTHON) { $env:PYTHON } else { "python" }

Write-Host "== 1/4 Project validation =="
& $py scripts/validate_project.py; if ($LASTEXITCODE) { exit $LASTEXITCODE }

Write-Host "== 2/4 Lint (ruff) =="
& $py -m ruff check .; if ($LASTEXITCODE) { exit $LASTEXITCODE }

Write-Host "== 3/4 JavaScript syntax =="
if (Get-Command node -ErrorAction SilentlyContinue) {
  Get-ChildItem frontend\*.js | ForEach-Object { node --check $_.FullName; if ($LASTEXITCODE) { exit 1 }; Write-Host "OK  $($_.Name)" }
  Get-ChildItem experiments\k6\*.js | ForEach-Object { Get-Content $_.FullName -Raw | node --check --input-type=module; if ($LASTEXITCODE) { exit 1 }; Write-Host "OK  $($_.Name)" }
} else { Write-Host "SKIP: node not installed" }

Write-Host "== 4/4 pytest + coverage =="
& $py -m pytest --cov --cov-report=term-missing --cov-report=xml:test_reports/coverage.xml --junitxml=test_reports/junit.xml
exit $LASTEXITCODE
