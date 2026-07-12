param(
    [switch]$SkipBuild
)

$ErrorActionPreference = "Stop"

$version = python -c "from config import APP_VERSION; print(APP_VERSION)"
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($version)) {
    throw "Could not read APP_VERSION from config.py"
}
$version = $version.Trim()
$artifactName = "tiktodv3-v$version-windows-x64.exe"
$artifactBaseName = [System.IO.Path]::GetFileNameWithoutExtension($artifactName)
$artifact = Join-Path $PSScriptRoot "dist\$artifactName"
$checksum = "$artifact.sha256"

if (-not $SkipBuild) {
    & "$PSScriptRoot\build.ps1" -Name $artifactBaseName
    if ($LASTEXITCODE -ne 0) {
        throw "The executable build failed"
    }
}

if (-not (Test-Path -LiteralPath $artifact -PathType Leaf)) {
    throw "Missing $artifact. Run without -SkipBuild to create it."
}

$hash = (Get-FileHash -LiteralPath $artifact -Algorithm SHA256).Hash.ToLowerInvariant()
Set-Content -LiteralPath $checksum -Value "$hash  $artifactName" -Encoding ascii

Write-Host "Release artifact: $artifact"
Write-Host "SHA-256 file:    $checksum"
Write-Host "SHA-256:         $hash"
