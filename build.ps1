param(
    [string]$Name = "tiktodv3"
)

$ErrorActionPreference = "Stop"

function Assert-LastExitCode {
    param([string]$Step)

    if ($LASTEXITCODE -ne 0) {
        throw "$Step failed with exit code $LASTEXITCODE"
    }
}

$outputPath = Join-Path $PSScriptRoot "dist\$Name.exe"
$runningOutput = Get-Process -ErrorAction SilentlyContinue | Where-Object {
    $_.Path -eq $outputPath
}
if ($runningOutput) {
    $processIds = ($runningOutput.Id -join ", ")
    throw "Close the running $Name.exe process(es) first (PID: $processIds)."
}

python -m pip install -r requirements-lock.txt -r requirements-dev.txt
Assert-LastExitCode "Dependency installation"
python verify.py
Assert-LastExitCode "Project verification"
python verify_gui.py
Assert-LastExitCode "GUI verification"
python -m compileall -q .
Assert-LastExitCode "Python compilation"
ruff check .
Assert-LastExitCode "Ruff lint"
ruff format --check .
Assert-LastExitCode "Ruff format check"
mypy .
Assert-LastExitCode "Mypy"
python -m PyInstaller `
    --noconfirm `
    --clean `
    --onefile `
    --windowed `
    --name $Name `
    --icon assets/logo.ico `
    --add-data "assets;assets" `
    --collect-all customtkinter `
    --collect-all cloakbrowser `
    app.py
Assert-LastExitCode "PyInstaller build for $Name.exe"

Write-Host "Executable created at dist/$Name.exe"
