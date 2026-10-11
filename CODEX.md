# 🛡️ Self-Correcting Code & Safety Guardrail (Codex Integration)

Questo file definisce le direttive e le modalità di integrazione per **OpenAI Codex**, **Codex CLI** e agenti basati su modelli Codex.

## Direttive di Generazione per Codex

1. **Integrità Sintattica (AST)**:
   - Ogni blocco di codice generato deve essere immediatamente compilabile/interpretabile ed esente da errori di sintassi.
   - Per Python e JSON, la struttura sintattica viene validata tramite AST prima della consegna.

2. **Sicurezza & Zero Credenziali (Zero Leaks)**:
   - **MAI** inserire chiavi API, token o password in chiaro nei prompt o nel codice generato.
   - Utilizzare sempre pattern sicuri con variabili d'ambiente (`os.environ.get(...)`, `process.env.*`).
   - Non proporre né eseguire comandi distruttivi o operazioni prive di salvaguardie.

3. **Verifica delle Policy & Allucinazioni**:
   - Rispettare rigorosamente i vincoli stabiliti in `knowledge_base.json` (sconti massimi, termini di reso, soglie di spedizione ed esclusione competitor).

4. **Pattern di Riflessione (Self-Correction)**:
   - Prima di finalizzare l'output, eseguire un passaggio di auto-critica.
   - Se viene rilevata un'incongruenza, applicare l'auto-correzione esponendo il badge:
     > 🛡️ **[Guardrail Attivo - Auto-Correzione Applicata]**

## Utilizzo con Codex API / Wrapper Python

```python
from code_guard import CodeGuard

guard = CodeGuard()

# Esempio di validazione di codice prodotto da Codex
codex_generated_code = """
import os
token = os.environ.get("CODEX_API_KEY")
"""

audit = guard.audit_response(codex_generated_code)
if audit.is_valid:
    print("Codice Codex verificato e conforme!")
else:
    print("Violazioni da correggere:", audit.violations)
```
