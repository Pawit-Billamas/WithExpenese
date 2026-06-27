# LINE Expense Tracker Bot - Quick Start Script
# Run this script to start the bot server

Write-Host "🚀 Starting LINE Expense Tracker Bot..." -ForegroundColor Green
Write-Host ""

# Check if .env exists
if (-Not (Test-Path ".env")) {
    Write-Host "❌ Error: .env file not found!" -ForegroundColor Red
    Write-Host "Please copy .env.example to .env and fill in your credentials." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Required variables:" -ForegroundColor Cyan
    Write-Host "  - LINE_CHANNEL_SECRET (you have: d964ef69ff35da377cb1e86914009e0c)" -ForegroundColor White
    Write-Host "  - LINE_CHANNEL_ACCESS_TOKEN (get from LINE Developers Console)" -ForegroundColor White
    Write-Host "  - OPENROUTER_API_KEY (get from openrouter.ai/keys)" -ForegroundColor White
    exit 1
}

# Check if dependencies are installed
Write-Host "📦 Checking dependencies..." -ForegroundColor Cyan
try {
    python -c "import fastapi, uvicorn, httpx, linebot" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "⚠️  Installing dependencies..." -ForegroundColor Yellow
        pip install -r requirements.txt
    } else {
        Write-Host "✅ Dependencies OK" -ForegroundColor Green
    }
} catch {
    Write-Host "⚠️  Installing dependencies..." -ForegroundColor Yellow
    pip install -r requirements.txt
}

Write-Host ""
Write-Host "🌐 Starting server on http://0.0.0.0:8000" -ForegroundColor Green
Write-Host ""
Write-Host "📝 Next steps:" -ForegroundColor Cyan
Write-Host "  1. Open another terminal and run: ngrok http 8000" -ForegroundColor White
Write-Host "  2. Copy the ngrok HTTPS URL" -ForegroundColor White
Write-Host "  3. Set it as webhook in LINE Developers Console" -ForegroundColor White
Write-Host "  4. Add your bot as friend and test!" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor DarkGray
Write-Host ""

# Run the server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
