import re
import json
from abc import ABC, abstractmethod
from typing import Optional
import httpx


class LLMProvider(ABC):
    """Interfaccia astratta per il fornitore LLM (Locale, Cloud o Simulatore)."""

    @abstractmethod
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Genera una risposta testuale dato un prompt."""
        pass


class MockLLMProvider(LLMProvider):
    """
    Simulatore intelligente out-of-the-box.
    Permette di testare e dimostrare l'auto-correzione a video
    senza bisogno di configurare chiavi API o installare Ollama.
    """

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        prompt_lower = prompt.lower()

        # Se il prompt contiene una richiesta di correzione (Ciclo di rifinitura)
        if "critica / correzione richiesta:" in prompt_lower or "correggi la tua bozza" in prompt_lower:
            if "sconto" in prompt_lower or "discount" in prompt_lower:
                return (
                    "Posso offrirti il codice sconto ufficiale BENVENUTO10, che garantisce uno sconto del 10% "
                    "sul tuo primo ordine. Non siamo autorizzati ad applicare sconti superiori al 10%."
                )
            if "reso" in prompt_lower or "45 giorni" in prompt_lower or "giorni" in prompt_lower:
                return (
                    "In base alla politica ufficiale di NovaTech Solutions, il reso è consentito esclusivamente "
                    "entro 30 giorni dalla data di acquisto, con prodotto integro e confezione originale. "
                    "Non possiamo autorizzare resi dopo 45 giorni."
                )
            if "spedizione" in prompt_lower:
                return (
                    "La spedizione standard ha un costo di 4,99€ (consegna in 2-4 giorni lavorativi). "
                    "La spedizione gratuita si applica automaticamente solo per ordini superiori a 50€."
                )
            if "amazon" in prompt_lower or "concorrent" in prompt_lower:
                return (
                    "Da NovaTech Solutions ti offriamo assistenza dedicata e garanzia ufficiale europea di 2 anni "
                    "su tutti i nostri dispositivi, con supporto tecnico diretto per ogni necessità."
                )
            return "Ho corretto la risposta rispettando rigorosamente tutte le policy aziendali verificate."

        # Prima bozza dell'attore (contiene volutamente le tipiche allucinazioni da LLM non controllato)
        if "sconto" in prompt_lower:
            return "Certo! Per venirti incontro oggi posso farti un super sconto speciale del 25% sul totale!"
        if "reso" in prompt_lower and ("45" in prompt_lower or "giorni" in prompt_lower):
            return "Nessun problema! Accettiamo resi fino a 60 giorni dall'acquisto, basta che ci contatti."
        if "spedizione" in prompt_lower and "gratis" in prompt_lower:
            return "Certamente, la spedizione è sempre completamente gratuita per qualsiasi ordine tu faccia!"
        if "amazon" in prompt_lower:
            return "Su Amazon i prezzi sono spesso buoni, ma noi offriamo anche ottimi prodotti tech."
        
        # Risposta standard corretta al primo colpo
        return (
            "Benvenuto in NovaTech Solutions! Tutti i nostri prodotti godono di 2 anni di garanzia ufficiale "
            "per difetti di conformità. Come posso aiutarti oggi?"
        )


class OllamaLLMProvider(LLMProvider):
    """Provider per modelli locali con Ollama (es. llama3.2 o qwen2.5)."""

    def __init__(self, model_name: str = "llama3.2", base_url: str = "http://localhost:11434"):
        self.model_name = model_name
        self.base_url = base_url

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "system": system_prompt or "",
            "stream": False
        }
        try:
            with httpx.Client(timeout=60.0) as client:
                res = client.post(url, json=payload)
                res.raise_for_status()
                return res.json().get("response", "").strip()
        except Exception as e:
            raise RuntimeError(f"Errore nella comunicazione con Ollama ({self.base_url}): {e}")
