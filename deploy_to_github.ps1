# Quick Deploy to GitHub Script
Write-Host "🚀 Deploying LINE Bot to GitHub..." -ForegroundColor Green
Write-Host ""

# Check if git is installed
$git = Get-Command git -ErrorAction SilentlyContinue
if (-not $git) {
    Write-Host "❌ Git is not installed!" -ForegroundColor Red
    Write-Host "   Download from: https://git-scm.com/download/win" -ForegroundColor Yellow
    exit 1
}

# Check if already initialized
if (-not (Test-Path ".git")) {
    Write-Host "📦 Initializing Git repository..." -ForegroundColor Cyan
    git init
    Write-Host "✅ Git initialized" -ForegroundColor Green
} else {
    Write-Host "✅ Git already initialized" -ForegroundColor Green
}

Write-Host ""

# Add all files
Write-Host "📝 Adding files..." -ForegroundColor Cyan
git add .

# Commit
Write-Host "💾 Creating commit..." -ForegroundColor Cyan
$commitMessage = Read-Host "Enter commit message (or press Enter for default)"
if ([string]::IsNullOrWhiteSpace($commitMessage)) {
    $commitMessage = "Initial commit - LINE Expense Tracker Bot"
}

git commit -m "$commitMessage"

Write-Host ""
Write-Host "=" * 60
Write-Host "✅ Code is ready to push!" -ForegroundColor Green
Write-Host "=" * 60
Write-Host ""

# Ask for GitHub repo URL
Write-Host "📋 Next steps:" -ForegroundColor Cyan
Write-Host "1. Create a new repository on GitHub:" -ForegroundColor White
Write-Host "   https://github.com/new" -ForegroundColor Blue
Write-Host ""
Write-Host "2. Repository name: linebot-expense-tracker" -ForegroundColor White
Write-Host "3. Make it Public or Private (your choice)" -ForegroundColor White
Write-Host "4. DON'T add README or .gitignore" -ForegroundColor Yellow
Write-Host "5. Click 'Create repository'" -ForegroundColor White
Write-Host ""

$pushNow = Read-Host "Have you created the GitHub repository? (y/n)"
if ($pushNow -eq 'y' -or $pushNow -eq 'Y') {
    Write-Host ""
    $repoUrl = Read-Host "Enter your GitHub repository URL"
    
    if ($repoUrl) {
        Write-Host ""
        Write-Host "🔗 Adding remote..." -ForegroundColor Cyan
        git remote add origin $repoUrl 2>$null
        
        Write-Host "📤 Pushing to GitHub..." -ForegroundColor Cyan
        git branch -M main
        git push -u origin main
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host ""
            Write-Host "=" * 60
            Write-Host "🎉 Successfully pushed to GitHub!" -ForegroundColor Green
            Write-Host "=" * 60
            Write-Host ""
            Write-Host "📱 Next: Deploy to Render" -ForegroundColor Cyan
            Write-Host "1. Go to https://render.com/" -ForegroundColor White
            Write-Host "2. Sign up with GitHub" -ForegroundColor White
            Write-Host "3. Follow instructions in DEPLOY_TO_RENDER.md" -ForegroundColor White
        } else {
            Write-Host ""
            Write-Host "⚠️  Push failed. Check the error above." -ForegroundColor Yellow
        }
    }
} else {
    Write-Host ""
    Write-Host "📝 When ready, run these commands:" -ForegroundColor Cyan
    Write-Host "git remote add origin YOUR_GITHUB_URL" -ForegroundColor White
    Write-Host "git branch -M main" -ForegroundColor White
    Write-Host "git push -u origin main" -ForegroundColor White
}

Write-Host ""
