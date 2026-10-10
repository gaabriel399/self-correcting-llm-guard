from typing import Callable, Optional
from models import ExecutionTrace, AttemptStep
from guardrail_critic import GuardrailCritic
from llm_provider import LLMProvider, MockLLMProvider


class SelfCorrectingAgent:
    """
    Agente AI dotato di Reflection Pattern e Guardrail di sicurezza.
    Genera risposte, le fa verificare dal Critico interno e le corregge
    in autonomia prima di presentarle all'utente.
    """

    def __init__(
        self,
        llm_provider: Optional[LLMProvider] = None,
        critic: Optional[GuardrailCritic] = None,
        max_correction_attempts: int = 2
    ):
        self.llm = llm_provider or MockLLMProvider()
        self.critic = critic or GuardrailCritic()
        self.max_attempts = max_correction_attempts

    def process_query(
        self,
        user_query: str,
        on_event: Optional[Callable[[str, dict], None]] = None
    ) -> ExecutionTrace:
        """
        Elabora la domanda dell'utente con tracciamento completo degli eventi.
        'on_event' permette alla UI di mostrare a schermo i passaggi in tempo reale.
        """
        def emit(event_type: str, data: dict):
            if on_event:
                on_event(event_type, data)

        # 1. GUARDRAIL DI INGRESSO (Security & Prompt Injection)
        emit("INPUT_CHECK", {"query": user_query})
        is_safe, block_reason = self.critic.check_input_security(user_query)
        
        if not is_safe:
            emit("BLOCKED", {"reason": block_reason})
            return ExecutionTrace(
                user_query=user_query,
                status="BLOCKED_BY_GUARDRAIL",
                attempts=[],
                final_response=f"🚫 Richiesta rifiutata per motivi di sicurezza: {block_reason}",
                total_corrections=0
            )

        attempts = []
        current_prompt = f"Rispondi alla domanda del cliente di NovaTech Solutions: '{user_query}'"
        last_draft = ""

        for round_num in range(1, self.max_attempts + 1):
            emit("GENERATING_DRAFT", {"round": round_num})
            
            # Generazione bozza da parte dell'attore
            draft = self.llm.generate(current_prompt)
            last_draft = draft
            emit("DRAFT_READY", {"round": round_num, "draft": draft})

            # Analisi critica della bozza
            emit("CRITIQUE_START", {"round": round_num})
            critique = self.critic.evaluate_draft(draft, user_query)

            attempts.append(AttemptStep(
                round_number=round_num,
                draft_response=draft,
                critique=critique
            ))

            if critique.is_valid:
                emit("CRITIQUE_PASSED", {"round": round_num})
                status = "PASSED_FIRST_TRY" if round_num == 1 else "SELF_CORRECTED"
                return ExecutionTrace(
                    user_query=user_query,
                    status=status,
                    attempts=attempts,
                    final_response=draft,
                    total_corrections=round_num - 1
                )
            else:
                emit("VIOLATION_DETECTED", {
                    "round": round_num,
                    "violations": critique.violations,
                    "notes": critique.critique_notes,
                    "suggested_fix": critique.suggested_fix
                })

                # Se abbiamo ancora tentativi a disposizione, prepariamo il prompt di auto-correzione
                if round_num < self.max_attempts:
                    emit("CORRECTION_LOOP_TRIGGERED", {
                        "round": round_num + 1,
                        "instructions": critique.suggested_fix
                    })
                    current_prompt = (
                        f"Domanda originale del cliente: '{user_query}'\n\n"
                        f"Tua bozza precedente: '{draft}'\n\n"
                        f"CRITICA / CORREZIONE RICHIESTA: {critique.critique_notes}\n"
                        f"ISTRUZIONE DI CORREZIONE OBBLIGATORIA: {critique.suggested_fix}\n\n"
                        f"Correggi la tua bozza adesso formulando una risposta conforme e completa."
                    )

        # Se supera il numero massimo di tentativi senza passare
        fallback_msg = (
            "Mi scuso per l'attesa: per questa richiesta ti invito a contattare direttamente "
            "il nostro supporto clienti a supporto@novatech.it per verificare le condizioni aggiornate."
        )
        emit("FAILED_MAX_RETRIES", {"fallback": fallback_msg})

        return ExecutionTrace(
            user_query=user_query,
            status="FAILED",
            attempts=attempts,
            final_response=fallback_msg,
            total_corrections=len(attempts)
        )
