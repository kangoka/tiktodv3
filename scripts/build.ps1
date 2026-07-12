param(
    [string]$Name = "tiktodv3"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot

function Assert-LastExitCode {
    param([string]$Step)

    if ($LASTEXITCODE -ne 0) {
        throw "$Step failed with exit code $LASTEXITCODE"
    }
}

$outputPath = Join-Path $ProjectRoot "dist\$Name.exe"
$runningOutput = Get-Process -ErrorAction SilentlyContinue | Where-Object {
    $_.Path -eq $outputPath
}
if ($runningOutput) {
    $processIds = ($runningOutput.Id -join ", ")
    throw "Close the running $Name.exe process(es) first (PID: $processIds)."
}

Push-Location $ProjectRoot
try {
    python -m pip install -r requirements-lock.txt -r requirements-dev.txt
    Assert-LastExitCode "Dependency installation"
    python -m verification.core
    Assert-LastExitCode "Project verification"
    python -m verification.gui
    Assert-LastExitCode "GUI verification"
    python -m compileall -q tiktodv3 verification app.py verify.py verify_gui.py
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
}
finally {
    Pop-Location
}

Write-Host "Executable created at dist/$Name.exe"
