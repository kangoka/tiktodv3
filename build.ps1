param(
    [string]$Name = "tiktodv3"
)

$ErrorActionPreference = "Stop"

& "$PSScriptRoot\scripts\build.ps1" -Name $Name
