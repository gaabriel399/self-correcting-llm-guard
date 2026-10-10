from typing import List, Optional
from pydantic import BaseModel, Field


class CritiqueResult(BaseModel):
    """Risultato dell'analisi del Guardrail / Giudice."""
    is_valid: bool = Field(description="True se la risposta rispetta tutte le policy, False altrimenti.")
    violations: List[str] = Field(default_factory=list, description="Elenco delle violazioni o allucinazioni rilevate.")
    critique_notes: str = Field(default="", description="Spiegazione dettagliata dell'errore per il modello che si deve correggere.")
    suggested_fix: str = Field(default="", description="Istruzione esatta su cosa correggere nella nuova bozza.")


class AttemptStep(BaseModel):
    """Registra un singolo tentativo nel ciclo di auto-correzione."""
    round_number: int
    draft_response: str
    critique: CritiqueResult


class ExecutionTrace(BaseModel):
    """Tracciamento completo del ciclo di ragionamento ed esecuzione."""
    user_query: str
    status: str = Field(description="Stato: 'PASSED_FIRST_TRY', 'SELF_CORRECTED', 'BLOCKED_BY_GUARDRAIL', o 'FAILED'")
    attempts: List[AttemptStep] = Field(default_factory=list)
    final_response: str
    total_corrections: int = 0
