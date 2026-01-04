<#
Starts Postgres via Docker Compose using values from .env.postgres
Usage: run from repository root or this script's folder:
  Set-Location n:\BERRIBOT\berribot-interview\backend
  .\.venv\Scripts\Activate.ps1
  .\start-postgres-clean.ps1
#>

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $scriptDir

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Error "Docker is not installed or not available in PATH. Start Docker Desktop first."
    exit 1
}

if (Test-Path .env.postgres) {
    Write-Host "Loading .env.postgres"
    Get-Content .env.postgres | ForEach-Object {
        if ($_ -match '^[\s#]') { return }
        $parts = $_ -split '=', 2
        if ($parts.Length -ge 2) {
            $name = $parts[0].Trim()
            $val = $parts[1].Trim()
            if ($name) { Set-Item -Path ("Env:\" + $name) -Value $val }
        }
    }
} else {
    Write-Host ".env.postgres not found — using environment variables if set"
}

Write-Host "Starting Postgres container (docker compose up -d)..."
docker compose up -d

Write-Host "Waiting for Postgres to initialize (10s) ..."
Start-Sleep -Seconds 10

Write-Host "Recent container logs (tail 100):"
docker logs --tail 100 berribot-postgres

Write-Host 'Run the connectivity test now or create tables with: python .\create_tables.py'
