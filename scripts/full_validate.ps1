Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$Failures = New-Object System.Collections.Generic.List[string]
$Warnings = New-Object System.Collections.Generic.List[string]

function Step($Message) {
    Write-Host ""
    Write-Host "==> $Message"
}

function Fail($Message) {
    $Failures.Add($Message)
    Write-Host "FAIL: $Message" -ForegroundColor Red
}

function Warn($Message) {
    $Warnings.Add($Message)
    Write-Host "WARN: $Message" -ForegroundColor Yellow
}

function Require-Command($Name) {
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        Fail "$Name is not installed or not on PATH"
        return $false
    }
    return $true
}

Push-Location $Root
try {
    Step "Checking required tools"
    $hasDocker = Require-Command "docker"
    $hasPython = Require-Command "python"
    if (-not $hasDocker -or -not $hasPython) { throw "Missing required tools" }

    Step "Building and starting Docker stack"
    docker compose up --build -d

    Step "Compiling backend in production Python image"
    docker compose run --rm -v "${Root}:/workspace" -w /workspace backend python -X pycache_prefix=/tmp/pycache -m compileall backend/app scripts tests

    Step "Running database migration bootstrap"
    docker compose exec -T backend python -m scripts.migrate

    Step "Running idempotent seed"
    docker compose exec -T backend python -m scripts.seed

    Step "Running backend smoke tests"
    docker compose run --rm -v "${Root}:/workspace" -w /workspace backend pytest tests

    Step "Waiting for healthy containers"
    $deadline = (Get-Date).AddMinutes(5)
    do {
        $statusLines = docker compose ps --format json | ConvertFrom-Json
        $unhealthy = @($statusLines | Where-Object { $_.Health -and $_.Health -ne "healthy" })
        $starting = @($statusLines | Where-Object { $_.Health -eq "starting" })
        if ($unhealthy.Count -eq 0 -and $starting.Count -eq 0) { break }
        Start-Sleep -Seconds 5
    } while ((Get-Date) -lt $deadline)

    $containers = docker compose ps --format json | ConvertFrom-Json
    foreach ($container in $containers) {
        if ($container.Health -and $container.Health -ne "healthy") {
            Fail "$($container.Service) is $($container.Health)"
        }
    }

    Step "Checking API health"
    Invoke-RestMethod -Uri "http://localhost:8000/live" | Out-Null
    Invoke-RestMethod -Uri "http://localhost:8000/health" | Out-Null
    Invoke-RestMethod -Uri "http://localhost:8000/ready" | Out-Null
    Invoke-WebRequest -Uri "http://localhost:8000/metrics" -UseBasicParsing | Out-Null
    Invoke-WebRequest -Uri "http://localhost:8080/health" -UseBasicParsing | Out-Null

    Step "Checking login inside backend container"
    docker compose exec -T backend python -m scripts.seed
    $loginBody = @{ email = "admin@demo.com"; password = "Password123!" } | ConvertTo-Json
    $login = Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/v1/auth/login" -ContentType "application/json" -Body $loginBody
    if (-not $login.access_token) { Fail "Login did not return an access token" }

    Step "Checking authenticated APIs"
    $headers = @{ Authorization = "Bearer $($login.access_token)" }
    Invoke-RestMethod -Uri "http://localhost:8000/api/v1/analytics/dashboard" -Headers $headers | Out-Null
    $leads = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/leads/" -Headers $headers
    Invoke-RestMethod -Uri "http://localhost:8000/api/v1/publishers/" -Headers $headers | Out-Null
    Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/v1/ai/manager-copilot" -Headers $headers -ContentType "application/json" -Body (@{ question = "Why are conversions down?" } | ConvertTo-Json) | Out-Null
    if ($leads.items.Count -gt 0) {
        $leadId = $leads.items[0].id
        Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/v1/calls/simulate-stream/$leadId" -Headers $headers | Out-Null
    }

    Step "Checking frontend"
    Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing | Out-Null
    Invoke-RestMethod -Uri "http://localhost:3000/api/health" | Out-Null
    Invoke-WebRequest -Uri "http://localhost:8501/_stcore/health" -UseBasicParsing | Out-Null
    Invoke-WebRequest -Uri "http://localhost:9090/-/ready" -UseBasicParsing | Out-Null
    Invoke-WebRequest -Uri "http://localhost:3001/api/health" -UseBasicParsing | Out-Null
}
catch {
    Fail $_.Exception.Message
}
finally {
    Pop-Location
}

Write-Host ""
if ($Warnings.Count -gt 0) {
    Write-Host "Warnings:" -ForegroundColor Yellow
    $Warnings | ForEach-Object { Write-Host "- $_" -ForegroundColor Yellow }
}

if ($Failures.Count -gt 0) {
    Write-Host "FAIL" -ForegroundColor Red
    $Failures | ForEach-Object { Write-Host "- $_" -ForegroundColor Red }
    exit 1
}

Write-Host "PASS" -ForegroundColor Green
