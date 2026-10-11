param(
    [string]$TargetDir = "."
)

Write-Host "🛡️ Installazione Self-Correcting LLM Guard in corso..." -ForegroundColor Cyan

$ZipPath = Join-Path $env:TEMP "self-correcting-guard.zip"
$ExtractPath = Join-Path $env:TEMP "self-correcting-guard-extract"

# Determina se lo script è in esecuzione in locale o scaricato da Web (irm | iex)
$LocalSource = $PSScriptRoot
if ($LocalSource -and (Test-Path (Join-Path $LocalSource "code_guard.py"))) {
    $SourceDir = $LocalSource
    Write-Host "📦 Origine: File locali del pacchetto" -ForegroundColor DarkGray
} else {
    Write-Host "🌐 Origine: Download diretto da GitHub..." -ForegroundColor Yellow
    $RepoZipUrl = "https://github.com/gaabriel399/self-correcting-llm-guard/archive/refs/heads/main.zip"
    try {
        Invoke-WebRequest -Uri $RepoZipUrl -OutFile $ZipPath -UseBasicParsing
        if (Test-Path $ExtractPath) { Remove-Item -Path $ExtractPath -Recurse -Force }
        Expand-Archive -Path $ZipPath -DestinationPath $ExtractPath -Force
        $SourceDir = Join-Path $ExtractPath "self-correcting-llm-guard-main"
    } catch {
        Write-Host "❌ Errore durante il download da GitHub: $_" -ForegroundColor Red
        return
    }
}

# Elementi da installare nel progetto di destinazione
$ItemsToCopy = @(
    ".agents",
    ".cursorrules",
    ".windsurfrules",
    "CLAUDE.md",
    "scripts",
    "code_guard.py",
    "guardrail_critic.py",
    "models.py",
    "knowledge_base.json",
    "rules",
    "skills"
)

foreach ($item in $ItemsToCopy) {
    $srcPath = Join-Path $SourceDir $item
    if (Test-Path $srcPath) {
        Copy-Item -Path $srcPath -Destination $TargetDir -Recurse -Force
        Write-Host "  [OK] Installato $item" -ForegroundColor Green
    }
}

# Pulizia temporanei se scaricato da web
if (Test-Path $ZipPath) { Remove-Item -Path $ZipPath -Force }
if (Test-Path $ExtractPath) { Remove-Item -Path $ExtractPath -Recurse -Force }

Write-Host "✅ Installazione completata con successo in: $(Resolve-Path $TargetDir)" -ForegroundColor Green
Write-Host "Ora Cursor, Windsurf, VS Code, Claude Code, Antigravity e qualsiasi AI applicheranno i controlli di sicurezza!" -ForegroundColor White
