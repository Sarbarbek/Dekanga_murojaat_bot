# GitHub ga push qilish uchun script
# Bu faylni PowerShell bilan ishga tushiring

$ErrorActionPreference = "Stop"
$repoPath = $PSScriptRoot
Set-Location -Path $repoPath
$remoteUrl = "https://github.com/Sarbarbek/Dekanga_murojaat_bot.git"

Write-Host "Git repositoriyasini tayyorlamoqda..." -ForegroundColor Cyan

# Config
git config --global core.autocrlf true

# Init
git init
Write-Host "✓ git init bajarildi" -ForegroundColor Green

# Branch
git branch -M main
Write-Host "✓ main branch yaratildi" -ForegroundColor Green

# Remote
git remote remove origin 2>$null
git remote add origin $remoteUrl
Write-Host "✓ Remote qo'shildi: $remoteUrl" -ForegroundColor Green

# Add all
git add .
Write-Host "✓ Barcha fayllar qo'shildi" -ForegroundColor Green

# Commit
git commit -m "initial commit: Dekanga murojaat boti"
Write-Host "✓ Commit qilindi" -ForegroundColor Green

# Push
Write-Host "`nGitHub ga push qilinmoqda..." -ForegroundColor Cyan
Write-Host "(GitHub username va Personal Access Token so'raladi)" -ForegroundColor Yellow
git push -u origin main

Write-Host "`n✅ Muvaffaqiyatli! Loyiha GitHub ga yuklandi." -ForegroundColor Green
Write-Host "GitHub: https://github.com/Sarbarbek/Dekanga_murojaat_bot" -ForegroundColor Cyan
