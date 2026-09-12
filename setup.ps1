$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot

function Find-Python {
    $command = Get-Command python -ErrorAction SilentlyContinue
    if ($command) {
        & $command.Source -c "import sys; raise SystemExit(not ((3,11) <= sys.version_info[:2] < (3,14)))" 2>$null
        if ($LASTEXITCODE -eq 0) { return $command.Source }
    }
    try {
        $candidate = (& py -3.12 -c "import sys; print(sys.executable)" 2>$null)
        if ($LASTEXITCODE -eq 0 -and $candidate) { return $candidate.Trim() }
    } catch {}
    $localCandidate = Join-Path $env:LOCALAPPDATA "Programs\Python\Python312\python.exe"
    if (Test-Path -LiteralPath $localCandidate) { return $localCandidate }
    return $null
}

$pythonExe = Find-Python
if (-not $pythonExe) {
    $winget = Get-Command winget -ErrorAction SilentlyContinue
    if (-not $winget) {
        throw "Python 3.11-3.13 bulunamadı ve winget kullanılamıyor. https://python.org adresinden Python 3.12 kurun."
    }
    Write-Host "Python 3.12 kuruluyor..."
    & winget install --id Python.Python.3.12 --exact --silent --accept-package-agreements --accept-source-agreements
    if ($LASTEXITCODE -ne 0) { throw "Python kurulumu başarısız oldu." }
    $pythonExe = Find-Python
    if (-not $pythonExe) { throw "Python kuruldu ancak bu oturumda bulunamadı. Terminali yeniden açıp setup.ps1 çalıştırın." }
}

if (-not (Test-Path -LiteralPath ".venv\Scripts\python.exe")) {
    Write-Host "Sanal ortam oluşturuluyor..."
    & $pythonExe -m venv .venv
}

$venvPython = Resolve-Path ".venv\Scripts\python.exe"
& $venvPython -m pip install --upgrade pip wheel
& $venvPython -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw "Python bağımlılıkları kurulamadı." }
& $venvPython -m scripts.prepare_ocr
if ($LASTEXITCODE -ne 0) { throw "OCR modelleri indirilemedi." }
New-Item -ItemType File -Path ".venv\.belgeiz-ready" -Force | Out-Null

Write-Host "Kurulum tamamlandı. Bundan sonra BelgeIz.cmd dosyasına çift tıklayabilirsiniz."
