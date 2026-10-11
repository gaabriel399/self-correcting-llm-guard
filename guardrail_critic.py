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
        self.company_name = self.detect_company_name()

    def detect_company_name(self) -> str:
        """
        Rileva dinamicamente il nome dell'azienda o del progetto attuale:
        1. Cerca package.json (Next.js, Node, React)
        2. Fallback sul nome della directory del progetto
        3. Fallback sul company_name della knowledge base
        """
        for candidate_dir in (Path.cwd(), Path(__file__).resolve().parent, Path(__file__).resolve().parent.parent):
            pkg = candidate_dir / "package.json"
            if pkg.exists():
                try:
                    with open(pkg, "r", encoding="utf-8") as f:
                        name = json.load(f).get("name", "").strip()
                        if name:
                            return name.capitalize()
                except Exception:
                    pass

        # Usa il nome della cartella corrente se significativo
        cwd_name = Path.cwd().name
        if cwd_name and cwd_name.lower() not in ("src", "root", "workspace", "scratch", "temp"):
            return cwd_name.capitalize()

        kb_name = self.kb.get("company_name", "")
        if kb_name and kb_name not in ("Progetto Corrente", "NovaTech Solutions"):
            return kb_name

        return "la nostra azienda"


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
        has_discount_context = any(
            k in draft_lower or (user_query and k in user_query.lower())
            for k in ("sconto", "sconti", "discount", "promozione", "promo", "coupon", "ribasso", "saldi")
        )
        if has_discount_context:
            discount_patterns = [
                r"(?:sconto|ribasso|offerta|coupon|promo|promozione|taglio|meno|risparmi[a-z]*)\D{0,25}(\d+)\s*%",
                r"(\d+)\s*%\s*(?:di\s+)?(?:sconto|ribasso|promozione|meno|in meno|off)",
            ]
            found_pcts = []
            for pat in discount_patterns:
                for match in re.finditer(pat, draft_lower):
                    found_pcts.append(int(match.group(1)))

            # Se la query chiedeva uno sconto/promo e nessuna regex specifica ha fatto match, controlla le percentuali generiche
            if not found_pcts and any(k in (user_query or "").lower() for k in ("sconto", "discount", "promo")):
                for pct_str in re.findall(r"(\d+)\s*%", draft):
                    found_pcts.append(int(pct_str))

            for pct_val in found_pcts:
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
                fixes.append(f"Rimuovi ogni menzione del concorrente e focalizzati unicamente sui punti di forza di {self.company_name}.")


        is_valid = len(violations) == 0

        return CritiqueResult(
            is_valid=is_valid,
            violations=violations,
            critique_notes=" ".join(critique_notes),
            suggested_fix=" ".join(fixes)
        )
