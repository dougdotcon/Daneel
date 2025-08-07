# =============================================================================
# DANEEL PROJECT - GIT MANAGEMENT SCRIPT
# =============================================================================
# Script para gerenciar problemas de Git e a pasta AGENTES
# Resolve locks e gerencia repositórios embarcados

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("unlock", "status", "add-agentes", "clean")]
    [string]$Action = "status"
)

function Write-ColorOutput {
    param([string]$Message, [string]$Color = "White")
    Write-Host $Message -ForegroundColor $Color
}

function Remove-GitLock {
    Write-ColorOutput "🔧 Removendo arquivo de lock do Git..." "Yellow"
    
    # Finalizar processos Git e VSCode
    try {
        taskkill /f /im git.exe 2>$null
        taskkill /f /im Code.exe 2>$null
        Start-Sleep -Seconds 2
    } catch {
        Write-ColorOutput "⚠️  Nenhum processo Git/VSCode encontrado" "Yellow"
    }
    
    # Remover arquivo de lock
    if (Test-Path ".git/index.lock") {
        try {
            Remove-Item -Path ".git/index.lock" -Force
            Write-ColorOutput "✅ Arquivo de lock removido com sucesso!" "Green"
        } catch {
            Write-ColorOutput "❌ Erro ao remover arquivo de lock: $_" "Red"
            return $false
        }
    } else {
        Write-ColorOutput "✅ Nenhum arquivo de lock encontrado" "Green"
    }
    
    return $true
}

function Get-GitStatus {
    Write-ColorOutput "📊 Status do repositório Git:" "Cyan"
    git status --porcelain
    Write-ColorOutput "`n📋 Status detalhado:" "Cyan"
    git status
}

function Add-AgentesFolder {
    Write-ColorOutput "📁 Gerenciando pasta AGENTES..." "Yellow"
    
    # Verificar se há repositórios Git embarcados
    $gitDirs = Get-ChildItem -Path "AGENTES" -Recurse -Directory -Name ".git" -ErrorAction SilentlyContinue
    
    if ($gitDirs.Count -gt 0) {
        Write-ColorOutput "⚠️  Encontrados $($gitDirs.Count) repositórios Git embarcados:" "Yellow"
        foreach ($dir in $gitDirs) {
            Write-ColorOutput "   - $dir" "Yellow"
        }
        
        $response = Read-Host "Deseja remover os .git embarcados? (y/N)"
        if ($response -eq "y" -or $response -eq "Y") {
            foreach ($dir in $gitDirs) {
                $fullPath = Join-Path "AGENTES" $dir
                Remove-Item -Path $fullPath -Recurse -Force
                Write-ColorOutput "✅ Removido: $fullPath" "Green"
            }
        } else {
            Write-ColorOutput "❌ Pasta AGENTES não será adicionada devido aos repositórios embarcados" "Red"
            return $false
        }
    }
    
    # Adicionar pasta AGENTES
    try {
        git add AGENTES/
        Write-ColorOutput "✅ Pasta AGENTES adicionada com sucesso!" "Green"
        return $true
    } catch {
        Write-ColorOutput "❌ Erro ao adicionar pasta AGENTES: $_" "Red"
        return $false
    }
}

function Clean-Repository {
    Write-ColorOutput "🧹 Limpando repositório..." "Yellow"
    
    # Remover lock
    Remove-GitLock
    
    # Limpar cache Git
    git gc --prune=now
    
    # Verificar integridade
    git fsck
    
    Write-ColorOutput "✅ Limpeza concluída!" "Green"
}

# =============================================================================
# EXECUÇÃO PRINCIPAL
# =============================================================================

Write-ColorOutput "🤖 DANEEL - Git Management Script" "Magenta"
Write-ColorOutput "=================================" "Magenta"

switch ($Action) {
    "unlock" {
        Remove-GitLock
        Get-GitStatus
    }
    "status" {
        Get-GitStatus
    }
    "add-agentes" {
        if (Remove-GitLock) {
            Add-AgentesFolder
            Get-GitStatus
        }
    }
    "clean" {
        Clean-Repository
        Get-GitStatus
    }
    default {
        Write-ColorOutput "❌ Ação inválida: $Action" "Red"
        Write-ColorOutput "Ações disponíveis: unlock, status, add-agentes, clean" "Yellow"
    }
}

Write-ColorOutput "`n🎯 Script concluído!" "Green"
