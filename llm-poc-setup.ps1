#!/usr/bin/env pwsh
# Quick start script for Phase 1 LLM Analysis POC
# 
# Usage:
#   .\llm-poc-setup.ps1
#
# This script:
# 1. Checks prerequisites
# 2. Installs anthropic if needed
# 3. Displays instructions for running the POC

Write-Host "===== Phase 1: Self-Healing Test Automation - Setup Check =====" -ForegroundColor Cyan

# Check 1: Backend venv
Write-Host "`n1. Checking backend venv..." -ForegroundColor Yellow
$venvPath = "backend\venv\Scripts\Activate.ps1"
if (Test-Path $venvPath) {
    Write-Host "   [OK] Virtual environment found" -ForegroundColor Green
} else {
    Write-Host "   [ERROR] Virtual environment not found at $venvPath" -ForegroundColor Red
    Write-Host "   Please create: cd backend && python -m venv venv"
    exit 1
}

# Check 2: anthropic package
Write-Host "`n2. Checking anthropic package..." -ForegroundColor Yellow
cd backend
& .\venv\Scripts\Activate.ps1
$anthropicCheck = python -c "import anthropic; print('OK')" 2>$null
if ($anthropicCheck -eq "OK") {
    Write-Host "   [OK] anthropic package is installed" -ForegroundColor Green
} else {
    Write-Host "   [INSTALLING] anthropic package..." -ForegroundColor Yellow
    pip install -q anthropic
    if ($?) {
        Write-Host "   [OK] anthropic installed successfully" -ForegroundColor Green
    } else {
        Write-Host "   [ERROR] Failed to install anthropic" -ForegroundColor Red
        exit 1
    }
}
cd ..

# Check 3: Claude API key
Write-Host "`n3. Checking Claude API key..." -ForegroundColor Yellow
$apiKey = $env:CLAUDE_API_KEY
if (-not $apiKey) {
    # Try to read from .env
    if (Test-Path ".env") {
        $envContent = Get-Content ".env"
        $apiKeyLine = $envContent | Select-String "^CLAUDE_API_KEY="
        if ($apiKeyLine) {
            $apiKey = $apiKeyLine -replace "^CLAUDE_API_KEY=""(.+?)""$", '$1'
        }
    }
}

if ($apiKey -and $apiKey -like "sk-ant-*") {
    Write-Host "   [OK] Claude API key detected (****" + $apiKey.Substring($apiKey.Length - 8) + ")" -ForegroundColor Green
} else {
    Write-Host "   [WARNING] Claude API key not found in environment or .env" -ForegroundColor Yellow
    Write-Host "   Please set: `$env:CLAUDE_API_KEY = 'sk-ant-...'"
}

# Check 4: Frontend setup
Write-Host "`n4. Checking frontend setup..." -ForegroundColor Yellow
if (Test-Path "frontend\node_modules") {
    Write-Host "   [OK] Frontend dependencies installed" -ForegroundColor Green
} else {
    Write-Host "   [WARNING] Frontend node_modules not found" -ForegroundColor Yellow
    Write-Host "   Please run: npm install --prefix frontend"
}

# Check 5: Playwright
Write-Host "`n5. Checking Playwright installation..." -ForegroundColor Yellow
$playwrightCheck = npm --prefix frontend list @playwright/test 2>$null | Select-String "@playwright/test"
if ($playwrightCheck) {
    Write-Host "   [OK] Playwright is installed" -ForegroundColor Green
} else {
    Write-Host "   [WARNING] Playwright not found" -ForegroundColor Yellow
}

# Summary
Write-Host "`n===== Setup Summary =====" -ForegroundColor Cyan
Write-Host @"
Prerequisites Status: Ready for Phase 1 testing

Next Steps:
1. Terminal 1: Start Backend
   cd backend
   .\venv\Scripts\Activate.ps1
   python -m uvicorn app.main:app --reload --port 8000

2. Terminal 2: Start Frontend
   cd frontend
   npm start

3. Terminal 3: Run POC Test
   cd frontend
   npx playwright test e2e/poc-llm-analysis.spec.js

4. Check Results
   Get-Content test-results/llm-analysis/llm-analysis-report.json | jq .

Documentation:
   - frontend/e2e/LLM_ANALYSIS_GUIDE.md (comprehensive guide)
   - Roadmap.md (overall initiative roadmap)

"@ -ForegroundColor Cyan
