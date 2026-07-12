param(
    [switch]$SkipBuild
)

$ErrorActionPreference = "Stop"

& "$PSScriptRoot\scripts\package-release.ps1" -SkipBuild:$SkipBuild
