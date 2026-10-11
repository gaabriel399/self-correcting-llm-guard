# 🛡️ Self-Correcting Code & Safety Guardrail (Claude Code Guide)

## Guidelines for Claude Code
These rules must be observed for all code suggestions, executions, and responses in this project.

1. **Syntactic Integrity**: Always ensure code (Python, JS, TS, Bash, JSON) is valid and executable.
2. **Zero Leaks**: Never print hardcoded credentials or API keys. Always use environment variables (`os.environ.get(...)`).
3. **Safe Commands**: Never execute or propose destructive deletion commands or unrestricted database drops.
4. **Knowledge Base Alignment**: Adhere to `knowledge_base.json` limits for discounts, return policies, and competitors.
5. **Self-Correction & Badge**: When fixing a detected risk or hallucination, display the badge:
   > 🛡️ **[Guardrail Attivo - Auto-Correzione Applicata]**
   > * **Rischio / Violazione intercettata:** [Descrizione]
   > * **Intervento:** [Correzione]
