import json
import sys
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


KB_PATH = Path("knowledge_base.json")
if not KB_PATH.exists():
    KB_PATH = Path(__file__).resolve().parent.parent / "knowledge_base.json"


def load_kb():
    if KB_PATH.exists():
        with open(KB_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"custom_policies": [], "policies": {}, "security": {}}


def save_kb(data):
    with open(KB_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def add_policy(policy_text: str):
    kb = load_kb()
    if "custom_policies" not in kb:
        kb["custom_policies"] = []
    kb["custom_policies"].append(policy_text)
    save_kb(kb)
    print(f"🛡️ [OK] Nuova policy aggiunta con successo: '{policy_text}'")


def list_policies():
    kb = load_kb()
    print("🛡️ --- POLICY ATTIVE NEL PROGETTO ---")
    company = kb.get("company_name", "Progetto Corrente")
    print(f"Azienda / Progetto: {company}")
    custom = kb.get("custom_policies", [])
    if custom:
        print("\nRegole Personalizzate:")
        for i, p in enumerate(custom, 1):
            print(f"  {i}. {p}")
    else:
        print("\nNessuna regola personalizzata aggiuntiva (valgono le impostazioni standard).")


def remove_policy(index: int):
    kb = load_kb()
    custom = kb.get("custom_policies", [])
    if 1 <= index <= len(custom):
        removed = custom.pop(index - 1)
        save_kb(kb)
        print(f"🛡️ [OK] Policy rimossa: '{removed}'")
    else:
        print(f"❌ Indice {index} non valido.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        list_policies()
        sys.exit(0)

    cmd = sys.argv[1].lower()
    if cmd == "add" and len(sys.argv) >= 3:
        add_policy(" ".join(sys.argv[2:]))
    elif cmd == "list":
        list_policies()
    elif cmd == "remove" and len(sys.argv) >= 3:
        remove_policy(int(sys.argv[2]))
    else:
        print("Uso: python manage_policy.py [add 'regola' | list | remove <numero>]")
