import json
import os
import sys
from pathlib import Path

# Aggiungi la root del pacchetto al path per importare code_guard
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code_guard import CodeGuard


def get_last_assistant_content(transcript_path: str) -> str:
    """Estrae l'ultimo testo o codice prodotto dal modello dal file transcript.jsonl."""
    if not transcript_path or not os.path.exists(transcript_path):
        return ""
    
    try:
        with open(transcript_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        
        # Scansiona all'indietro per trovare l'ultimo messaggio o chiamata del modello
        for line in reversed(lines):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                # Cerca risposte dell'agente / modello
                if data.get("source") in ("MODEL", "AGENT") or data.get("type") in ("PLANNER_RESPONSE", "ASSISTANT_RESPONSE"):
                    content = data.get("content", "")
                    if content:
                        return content
                    # Se il contenuto include tool calls come write_to_file
                    tool_calls = data.get("tool_calls", [])
                    code_snippets = []
                    for tc in tool_calls:
                        args = tc.get("args", {})
                        if "CodeContent" in args:
                            code_snippets.append(args["CodeContent"])
                        if "CommandLine" in args:
                            code_snippets.append(args["CommandLine"])
                    if code_snippets:
                        return "\n\n".join(code_snippets)
            except Exception:
                continue
    except Exception:
        pass
    return ""


def handle_pre_tool(payload: dict, guard: CodeGuard) -> dict:
    """Ispeziona i tool call prima dell'esecuzione (es. comandi da terminale)."""
    tool_call = payload.get("toolCall", {})
    tool_name = tool_call.get("name", "")
    args = tool_call.get("args", {})

    cmd = args.get("CommandLine", "")
    if tool_name == "run_command" and cmd:
        # 1. Controlla injection / frasi bloccate
        is_safe, reason = guard.critic.check_input_security(cmd)
        if not is_safe:
            return {"decision": "deny", "reason": f"Bloccato da Guardrail: {reason}"}

        # 2. Controlla comandi distruttivi
        sec_violations = guard.check_security_and_secrets(cmd)
        if sec_violations:
            return {
                "decision": "deny",
                "reason": f"Bloccato per sicurezza: {'; '.join(sec_violations)}"
            }

    # Se si tenta di scrivere direttamente codice pericoloso o segreti su file
    code_content = args.get("CodeContent", "")
    if tool_name in ("write_to_file", "replace_file_content") and code_content:
        audit = guard.audit_response(code_content)
        if not audit.is_valid:
            return {
                "decision": "deny",
                "reason": f"Rilevate violazioni nel codice da scrivere: {'; '.join(audit.violations)}. Correggile prima di salvare!"
            }

    return {"decision": "allow"}


def handle_stop(payload: dict, guard: CodeGuard) -> dict:
    """
    Hook di chiusura turno (Stop):
    Prima che l'AI consegni la risposta finale, ispeziona il contenuto prodotto.
    Se rileva violazioni, forza il ciclo di auto-correzione (Reflection).
    """
    exec_num = payload.get("executionNum", 1)
    # Evita loop infiniti se l'AI fallisce per più di 3 tentativi consecutivi
    if exec_num >= 3:
        return {"decision": "allow"}

    transcript_path = payload.get("transcriptPath", "")
    content = get_last_assistant_content(transcript_path)

    if not content:
        return {"decision": "allow"}

    audit = guard.audit_response(content)
    if not audit.is_valid:
        error_details = "\n".join([f"• {v}" for v in audit.violations])
        return {
            "decision": "continue",
            "reason": (
                f"🛡️ AUTO-CORRECTION REQUIRED (Guardrail Reflection Loop):\n"
                f"La tua risposta o il codice proposto contengono le seguenti violazioni:\n{error_details}\n\n"
                f"Istruzione correttiva: {audit.suggested_fix}\n"
                f"Riscrivi la risposta correggendo tutte le violazioni prima di consegnarla all'utente."
            )
        }

    return {"decision": "allow"}


def main():
    try:
        raw_input = sys.stdin.read()
        if not raw_input.strip():
            print(json.dumps({"decision": "allow"}))
            return

        payload = json.loads(raw_input)
        kb_path = project_root / "knowledge_base.json"
        guard = CodeGuard(knowledge_base_path=str(kb_path))

        # Determina il tipo di hook dal payload
        if "toolCall" in payload:
            response = handle_pre_tool(payload, guard)
        elif "executionNum" in payload or "terminationReason" in payload:
            response = handle_stop(payload, guard)
        else:
            response = {"decision": "allow"}

        print(json.dumps(response))
    except Exception as e:
        # Fail-safe: non bloccare l'editor se c'è un errore inatteso nel parsing
        print(json.dumps({"decision": "allow", "reason": f"Guardrail bypass on error: {str(e)}"}))


if __name__ == "__main__":
    main()
