<#
.SYNOPSIS
  Create Windows Codex config files for manual editing.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File .\scripts\setup-windows-codex.ps1

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File .\scripts\setup-windows-codex.ps1 -Force
#>

[CmdletBinding()]
param(
  [string]$CodexHome = "$env:USERPROFILE\.codex",
  [switch]$Force
)

$ErrorActionPreference = "Stop"

function Write-Step {
  param([string]$Message)
  Write-Host ""
  Write-Host "==> $Message"
}

function Backup-IfNeeded {
  param([string]$Path)

  if ((Test-Path $Path) -and $Force) {
    $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $backupPath = "$Path.bak.$stamp"
    Copy-Item -Path $Path -Destination $backupPath -Force
    Write-Host "Backed up existing file to: $backupPath"
  }
}

function Write-FileIfMissing {
  param(
    [string]$Path,
    [string]$Content
  )

  if ((Test-Path $Path) -and -not $Force) {
    Write-Host "Exists, skipped: $Path"
    return
  }

  Backup-IfNeeded -Path $Path
  Set-Content -Path $Path -Value $Content -Encoding UTF8
  Write-Host "Created: $Path"
}

Write-Step "Creating Codex directory"
New-Item -ItemType Directory -Path $CodexHome -Force | Out-Null

$configPath = Join-Path $CodexHome "config.toml"
$authPath = Join-Path $CodexHome "auth.json"

$configTemplate = @'
# Edit this file manually.
# Example:
#
# model = "gpt-5.5"
# model_provider = "your-provider"
#
# [model_providers.your-provider]
# name = "your-provider"
# base_url = "https://your-base-url/v1"
# wire_api = "responses"
# approval_policy = "on-request"
# sandbox_mode = "workspace-write"
'@

$authTemplate = @'
{
  "OPENAI_API_KEY": ""
}
'@

Write-Step "Creating config.toml and auth.json"
Write-FileIfMissing -Path $configPath -Content $configTemplate
Write-FileIfMissing -Path $authPath -Content $authTemplate

Write-Step "Done"
Write-Host "Codex home: $CodexHome"
Write-Host "Config: $configPath"
Write-Host "Auth: $authPath"
Write-Host ""
Write-Host "Open these files and fill in your own config, key, and base_url."
