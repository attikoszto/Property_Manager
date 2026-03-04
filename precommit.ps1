$ErrorActionPreference = "Continue"
$failed = 0

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Ruff Lint" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
ruff check . --fix
if ($LASTEXITCODE -ne 0) {
    Write-Host "X Ruff Lint fehlgeschlagen" -ForegroundColor Red
    $failed = 1
} else {
    Write-Host "OK Ruff Lint" -ForegroundColor Green
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Black Format Check" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
black --check .
if ($LASTEXITCODE -ne 0) {
    Write-Host "X Black Format fehlgeschlagen" -ForegroundColor Red
    $failed = 1
} else {
    Write-Host "OK Black Format" -ForegroundColor Green
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Pytest" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
pytest tests/ -x -q
if ($LASTEXITCODE -ne 0) {
    Write-Host "X Pytest fehlgeschlagen" -ForegroundColor Red
    $failed = 1
} else {
    Write-Host "OK Pytest" -ForegroundColor Green
}

Write-Host "`n========================================" -ForegroundColor Cyan
if ($failed -ne 0) {
    Write-Host "X Checks fehlgeschlagen" -ForegroundColor Red
    exit 1
} else {
    Write-Host "Alle Checks bestanden!" -ForegroundColor Green
    exit 0
}
