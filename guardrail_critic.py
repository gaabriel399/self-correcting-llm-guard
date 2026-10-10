import json
import re
from pathlib import Path
from models import CritiqueResult


class GuardrailCritic:
    """Il Giudice: valida l'input dell'utente e valuta le bozze generate dall'AI."""

    def __init__(self, knowledge_base_path: str = "knowledge_base.json"):
        kb_file = Path(knowledge_base_path)
        if not kb_file.exists():
            # Fallback se cercato da cartella radice differente
            kb_file = Path(__file__).parent / "knowledge_base.json"
        
        with open(kb_file, "r", encoding="utf-8") as f:
            self.kb = json.load(f)
            
        self.policies = self.kb.get("policies", {})
        self.security = self.kb.get("security", {})

    def check_input_security(self, user_query: str) -> tuple[bool, str]:
        """
        Guardrail di ingresso:
        Blocca prompt injection, jailbreak o tentativi di estrazione del prompt di sistema.
        """
        query_lower = user_query.lower()
        blocked_phrases = self.security.get("blocked_phrases", [])
        
        for phrase in blocked_phrases:
            if phrase in query_lower:
                return False, f"Rilevato tentativo di bypass / Prompt Injection: '{phrase}'"
        
        return True, ""

    def evaluate_draft(self, draft: str, user_query: str) -> CritiqueResult:
        """
        Guardrail di uscita:
        Esamina la bozza generata rispetto alle policy e alle verità ufficiali.
        Restituisce un CritiqueResult con le eventuali violazioni rilevate.
        """
        draft_lower = draft.lower()
        violations = []
        critique_notes = []
        fixes = []

        # 1. Controllo Sconti
        max_discount = self.policies.get("discounts", {}).get("max_allowed_percent", 10)
        # Cerca numeri seguiti da %
        percent_matches = re.findall(r"(\d+)\s*%", draft)
        for pct_str in percent_matches:
            pct_val = int(pct_str)
            if pct_val > max_discount:
                violations.append(f"Sconto non autorizzato: promesso sconto del {pct_val}% (il massimo consentito è {max_discount}%)")
                critique_notes.append(f"Hai promesso uno sconto del {pct_val}%, ma la policy aziendale vieta sconti oltre il {max_discount}%.")
                fixes.append(f"Offri solo il codice ufficiale {self.policies['discounts']['welcome_code']} per uno sconto del {max_discount}%.")

        # 2. Controllo Politica di Reso
        max_return_days = self.policies.get("returns", {}).get("max_days", 30)
        # Cerca promesse/autorizzazioni esplicite oltre i 30 giorni (es. 'fino a 60 giorni', 'entro 45 giorni')
        allow_matches = re.findall(r"(?:fino a|entro|accettiamo\s+(?:resi\s+)?fino\s+a|possibile\s+entro)\s*(\d+)\s*giorni", draft_lower)
        for d_str in allow_matches:
            d_val = int(d_str)
            if d_val > max_return_days:
                violations.append(f"Allucinazione su politica resi: autorizzati {d_val} giorni (limite ufficiale: {max_return_days} giorni)")
                critique_notes.append(f"Hai affermato che il reso è possibile entro {d_val} giorni. Il limite massimo è {max_return_days} giorni.")
                fixes.append(f"Chiarisci esplicitamente che il reso è consentito SOLO entro {max_return_days} giorni dall'acquisto con scontrino.")

        # 3. Controllo Spedizione Gratuita Incondizionata
        if "spedizione" in draft_lower and ("sempre gratuita" in draft_lower or "completamente gratuita per qualsiasi" in draft_lower):
            threshold = self.policies.get("shipping", {}).get("free_threshold", 50.0)
            cost = self.policies.get("shipping", {}).get("standard_cost", 4.99)
            violations.append("Spedizione gratuita promessa senza soglia minima d'ordine")
            critique_notes.append(f"La spedizione non è sempre gratuita: costa {cost}€ ed è gratis solo sopra i {threshold}€.")
            fixes.append(f"Specifica che la spedizione standard costa {cost}€ ed è gratuita esclusivamente per ordini superiori a {threshold}€.")

        # 4. Controllo Menzioni Concorrenti
        forbidden_competitors = self.policies.get("forbidden_competitors", [])
        for comp in forbidden_competitors:
            if comp.lower() in draft_lower:
                violations.append(f"Menzione di competitor non consentito: '{comp}'")
                critique_notes.append(f"Hai citato il concorrente '{comp}'. La policy vieta di fare pubblicità o confronti con aziende terze.")
                fixes.append("Rimuovi ogni menzione del concorrente e focalizzati unicamente sui punti di forza di NovaTech Solutions.")

        is_valid = len(violations) == 0

        return CritiqueResult(
            is_valid=is_valid,
            violations=violations,
            critique_notes=" ".join(critique_notes),
            suggested_fix=" ".join(fixes)
        )
