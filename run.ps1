$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot
if (-not (Test-Path -LiteralPath ".venv\Scripts\python.exe")) {
    & "$PSScriptRoot\setup.ps1"
}
& "$PSScriptRoot\.venv\Scripts\python.exe" "$PSScriptRoot\launcher.py"
