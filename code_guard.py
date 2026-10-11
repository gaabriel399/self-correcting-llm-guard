import ast
import json
import re
from typing import List, Dict, Any, Tuple
from pathlib import Path

from models import CritiqueResult
from guardrail_critic import GuardrailCritic


class CodeGuard:
    """
    Validatore avanzato di codice e sicurezza:
    - Verifica la correttezza sintattica (Python AST, JSON)
    - Intercetta credenziali / segreti / API keys hardcoded
    - Blocca pattern pericolosi / distruttivi (rm -rf, rmtree /, fork bomb, eval non sicuro)
    - Esegue le verifiche di policy e allucinazioni tramite GuardrailCritic
    """

    SECRET_PATTERNS = [
        (re.compile(r"sk-[a-zA-Z0-9]{20,}"), "OpenAI API Key in chiaro"),
        (re.compile(r"ghp_[a-zA-Z0-9]{36}"), "GitHub Personal Access Token in chiaro"),
        (re.compile(r"AKIA[0-9A-Z]{16}"), "AWS Access Key ID in chiaro"),
        (re.compile(r"""(?i)(?:api_key|secret_key|private_key|auth_token)\s*=\s*['\"][a-zA-Z0-9_\-\.]{16,}['\"]"""), "API Token / Chiave segreta hardcoded (usa variabili d'ambiente)"),
        (re.compile(r"""(?i)password\s*=\s*['\"][^'\"]{6,}['\"]"""), "Password in chiaro nel codice (usa variabili d'ambiente o secret manager)")
    ]

    DANGEROUS_PATTERNS = [
        (re.compile(r"rm\s+-rf\s+[\/~]"), "Comando distruttivo di cancellazione radice/home ('rm -rf')"),
        (re.compile(r"shutil\.rmtree\s*\(\s*['\"][\/~]"), "Cancellazione ricorsiva distruttiva su filesystem radice"),
        (re.compile(r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;"), "Fork bomb bash rilevata"),
        (re.compile(r"""DROP\s+DATABASE\s+["`']?[a-zA-Z0-9_]+["`']?""", re.IGNORECASE), "Comando SQL distruttivo DROP DATABASE senza protezioni"),
    ]

    def __init__(self, knowledge_base_path: str = "knowledge_base.json"):
        self.critic = GuardrailCritic(knowledge_base_path=knowledge_base_path)

    def extract_code_blocks(self, text: str) -> List[Dict[str, str]]:
        """Estrae tutti i blocchi di codice markdown con il rispettivo linguaggio."""
        pattern = re.compile(r"```([a-zA-Z0-9_+-]*)\n(.*?)```", re.DOTALL)
        blocks = []
        for match in pattern.finditer(text):
            lang = (match.group(1) or "").strip().lower()
            code = match.group(2)
            blocks.append({"lang": lang, "code": code})
        return blocks

    def check_syntax(self, lang: str, code: str) -> List[str]:
        """Verifica la validità sintattica del codice."""
        errors = []
        if lang in ("python", "py"):
            try:
                ast.parse(code)
            except SyntaxError as e:
                errors.append(f"Errore di sintassi Python alla riga {e.lineno}: {e.msg}")
        elif lang in ("json",):
            try:
                json.loads(code)
            except json.JSONDecodeError as e:
                errors.append(f"Errore di sintassi JSON alla riga {e.lineno}: {e.msg}")
        return errors

    def check_security_and_secrets(self, text_or_code: str) -> List[str]:
        """Rileva segreti, credenziali esposte e comandi distruttivi."""
        violations = []
        for pattern, desc in self.SECRET_PATTERNS:
            if pattern.search(text_or_code):
                violations.append(f"Vulnerabilità di sicurezza: {desc}")

        for pattern, desc in self.DANGEROUS_PATTERNS:
            if pattern.search(text_or_code):
                violations.append(f"Operazione ad alto rischio rilevata: {desc}")

        return violations

    def audit_response(self, text_response: str, user_query: str = "") -> CritiqueResult:
        """
        Esegue l'ispezione completa su una risposta proposta:
        1. Valutazione testo e policy (sconti, resi, competitor, injection)
        2. Ispezione segreti e comandi distruttivi
        3. Verifica sintattica di ogni blocco di codice proposto
        """
        violations = []
        notes = []
        fixes = []

        # 1. Policy & Business Hallucinations
        policy_critique = self.critic.evaluate_draft(text_response, user_query)
        if not policy_critique.is_valid:
            violations.extend(policy_critique.violations)
            notes.append(policy_critique.critique_notes)
            fixes.append(policy_critique.suggested_fix)

        # 2. Segreti e comandi distruttivi nel testo complessivo
        sec_violations = self.check_security_and_secrets(text_response)
        if sec_violations:
            violations.extend(sec_violations)
            notes.append("Trovate violazioni di sicurezza (credenziali in chiaro o comandi distruttivi).")
            fixes.append("Rimuovi chiavi hardcoded usando os.environ.get(...) ed evita comandi distruttivi non controllati.")

        # 3. Controllo sintattico blocchi di codice
        blocks = self.extract_code_blocks(text_response)
        for b in blocks:
            syntax_errors = self.check_syntax(b["lang"], b["code"])
            if syntax_errors:
                violations.extend(syntax_errors)
                notes.append(f"Il blocco di codice {b['lang']} contiene errori sintattici.")
                fixes.append("Correggi la sintassi del codice prima di consegnarlo.")

        is_valid = len(violations) == 0
        return CritiqueResult(
            is_valid=is_valid,
            violations=violations,
            critique_notes=" ".join(notes),
            suggested_fix=" ".join(fixes)
        )
