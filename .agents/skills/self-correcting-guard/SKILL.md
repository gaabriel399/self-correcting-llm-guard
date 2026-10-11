---
name: self-correcting-guard
description: Auto-correcting LLM guardrail and code safety engine. Evaluates code syntax, secrets, dangerous operations, and policy hallucinations on every interaction, enforcing reflection and self-correction.
---

# 🛡️ Self-Correcting Guard Skill

Questo modulo fornisce le istruzioni e gli strumenti per validare e auto-correggere le risposte e il codice generati da qualsiasi AI Agent o editor (Codex, Cursor, Windsurf, VS Code, Claude Code, Antigravity, Terminale).

## Obiettivi della Skill

1. **Intercettare Allucinazioni**: Confrontare le risposte con le policy ufficiali in `knowledge_base.json`.
2. **Validare la Sintassi del Codice**: Assicurarsi che i blocchi di codice Python/JSON siano sintatticamente corretti.
3. **Prevenire Fuga di Segreti**: Individuare chiavi API hardcoded (`sk-...`, `ghp_...`, `AKIA...`) o password esposte.
4. **Bloccare Comandi Distruttivi**: Rifiutare l'esecuzione di comandi pericolosi come `rm -rf /` o `DROP DATABASE`.
5. **Guidare l'Auto-Correzione**: Fornire istruzioni chiare e contestualizzate per guidare la riscrittura conforme.

## Come testare o eseguire le verifiche

### 1. Verifica manuale da terminale
Per eseguire l'ispezione di sicurezza interattiva su scenari di test:
```bash
python main.py
```

### 2. Esecuzione della suite Evals
Per lanciare tutti i test automatizzati di conformità:
```bash
pytest tests/ -v
```

### 3. Validazione di un testo o codice via script
```python
from code_guard import CodeGuard

guard = CodeGuard()
result = guard.audit_response("""
```python
import os
key = os.environ.get("API_KEY")
```
""")

if not result.is_valid:
    print("Violazioni:", result.violations)
    print("Correzione:", result.suggested_fix)
```

## Personalizzazione delle Regole
Per aggiornare le policy aziendali o le frasi bloccate, modifica direttamente `knowledge_base.json`.
