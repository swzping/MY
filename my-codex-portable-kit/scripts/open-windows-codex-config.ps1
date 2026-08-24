<#
.SYNOPSIS
  Open Windows Codex config files for manual editing.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File .\scripts\open-windows-codex-config.ps1
#>

[CmdletBinding()]
param(
  [string]$CodexHome = "$env:USERPROFILE\.codex"
)

$ErrorActionPreference = "Stop"

$configPath = Join-Path $CodexHome "config.toml"
$authPath = Join-Path $CodexHome "auth.json"

if (-not (Test-Path $CodexHome)) {
  New-Item -ItemType Directory -Path $CodexHome -Force | Out-Null
}

if (-not (Test-Path $configPath)) {
  New-Item -ItemType File -Path $configPath -Force | Out-Null
}

if (-not (Test-Path $authPath)) {
  Set-Content -Path $authPath -Value "{`r`n  `"OPENAI_API_KEY`": `"`"`r`n}`r`n" -Encoding UTF8
}

Write-Host "Config: $configPath"
Write-Host "Auth: $authPath"

Start-Process notepad.exe $configPath
Start-Process notepad.exe $authPath
