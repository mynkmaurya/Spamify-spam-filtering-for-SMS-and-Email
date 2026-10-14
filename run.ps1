# Spamify AI - PowerShell Launcher
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Spamify AI - High-Accuracy Spam & Phishing Detection" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$candidates = @(
    "$env:LOCALAPPDATA\Python\bin\python.exe",
    "$env:LOCALAPPDATA\Python\pythoncore-3.14-64\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe"
)

$pyExe = $null

foreach ($c in $candidates) {
    if (Test-Path $c) {
        $pyExe = $c
        break
    }
}

if (-not $pyExe) {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        $pyExe = "py"
    } else {
        $pyExe = "python"
    }
}

Write-Host "[*] Detected Python: $pyExe" -ForegroundColor Green
& $pyExe --version
Write-Host ""

if (-not (Test-Path "models\spam_model.joblib")) {
    Write-Host "[*] Training model..." -ForegroundColor Yellow
    & $pyExe train.py
}

Write-Host "[*] Launching Spamify Web Application..." -ForegroundColor Green
Write-Host "[*] Open your browser at: http://127.0.0.1:5000" -ForegroundColor Cyan
Write-Host "[*] Press Ctrl+C in this terminal to stop the server." -ForegroundColor Gray
Write-Host ""

& $pyExe app.py
