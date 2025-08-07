# =============================================================================
# QUICK GIT UNLOCK SCRIPT
# =============================================================================
# Script rápido para resolver problemas de lock do Git

Write-Host "🔧 Desbloqueando Git..." -ForegroundColor Yellow

# Finalizar processos
taskkill /f /im git.exe 2>$null
taskkill /f /im Code.exe 2>$null
Start-Sleep -Seconds 2

# Remover lock
if (Test-Path ".git/index.lock") {
    Remove-Item -Path ".git/index.lock" -Force
    Write-Host "✅ Lock removido!" -ForegroundColor Green
} else {
    Write-Host "✅ Nenhum lock encontrado" -ForegroundColor Green
}

# Verificar status
Write-Host "`n📊 Status do Git:" -ForegroundColor Cyan
git status --short
