param(
    [string]$TargetDir = "."
)

Write-Host "🛡️ Installazione Self-Correcting LLM Guard in corso..." -ForegroundColor Cyan

$SourceDir = $PSScriptRoot

# Lista delle cartelle e dei file essenziali per il Guardrail
$ItemsToCopy = @(
    ".agents",
    "scripts",
    "code_guard.py",
    "guardrail_critic.py",
    "models.py",
    "knowledge_base.json",
    "agent.py",
    "llm_provider.py",
    "main.py",
    "tests"
)


foreach ($item in $ItemsToCopy) {
    $srcPath = Join-Path $SourceDir $item
    if (Test-Path $srcPath) {
        Copy-Item -Path $srcPath -Destination $TargetDir -Recurse -Force
        Write-Host "  [OK] Copiato $item" -ForegroundColor Green
    } else {
        Write-Host "  [!] Elemento non trovato: $item" -ForegroundColor Yellow
    }
}

Write-Host "✅ Installazione completata con successo in: $(Resolve-Path $TargetDir)" -ForegroundColor Green
Write-Host "Ora l'AI applicherà il controllo di sicurezza su ogni domanda e risposta di codice nel progetto!" -ForegroundColor White
