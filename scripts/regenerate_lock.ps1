Write-Host "Regenerating poetry.lock file..." -ForegroundColor Cyan

# Remove the old lock file
if (Test-Path poetry.lock) {
    Remove-Item poetry.lock
}

# Generate a new lock file
poetry lock

Write-Host "Lock file regenerated successfully!" -ForegroundColor Green
