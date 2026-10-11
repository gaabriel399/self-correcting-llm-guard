import json
import os
import sys
import time
from pathlib import Path
import urllib.request

GITHUB_REPO = "gaabriel399/self-correcting-llm-guard"
REMOTE_PLUGIN_URL = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/plugin.json"
CACHE_FILE = Path(os.environ.get("TEMP", ".")) / "self_correcting_guard_update_cache.json"
CACHE_TTL_SECONDS = 6 * 3600  # Controlla al massimo una volta ogni 6 ore


def get_local_version() -> str:
    """Legge la versione locale installata da plugin.json."""
    for base in [Path.cwd(), Path(__file__).resolve().parent.parent, Path(__file__).resolve().parent]:
        p = base / "plugin.json"
        if p.exists():
            try:
                with open(p, "r", encoding="utf-8") as f:
                    return json.load(f).get("version", "1.0.0")
            except Exception:
                pass
    return "1.0.0"


def check_for_updates(force: bool = False) -> dict:
    """
    Controlla se su GitHub è presente una versione più recente.
    Usa una cache locale di 6 ore per non rallentare l'esecuzione.
    """
    now = time.time()
    local_ver = get_local_version()

    # Controlla se abbiamo un risultato recente in cache
    if not force and CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if now - data.get("timestamp", 0) < CACHE_TTL_SECONDS:
                    remote_ver = data.get("remote_version", local_ver)
                    has_update = _is_newer(remote_ver, local_ver)
                    return {
                        "has_update": has_update,
                        "local_version": local_ver,
                        "remote_version": remote_ver,
                        "cached": True
                    }
        except Exception:
            pass

    # Esegui chiamata di rete leggera con timeout breve (1.5 secondi)
    remote_ver = local_ver
    try:
        req = urllib.request.Request(
            REMOTE_PLUGIN_URL,
            headers={"User-Agent": "Antigravity-Guard-Updater/1.0"}
        )
        with urllib.request.urlopen(req, timeout=1.5) as res:
            remote_data = json.loads(res.read().decode("utf-8"))
            remote_ver = remote_data.get("version", local_ver)

        # Salva in cache
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "timestamp": now,
                "remote_version": remote_ver
            }, f)
    except Exception:
        # Fail-safe: se non c'è connessione o timeout, non bloccare nulla
        pass

    has_update = _is_newer(remote_ver, local_ver)
    return {
        "has_update": has_update,
        "local_version": local_ver,
        "remote_version": remote_ver,
        "cached": False
    }


def _is_newer(remote: str, local: str) -> bool:
    """Confronta due stringhe di versione semantica (es. 1.2.0 > 1.1.0)."""
    try:
        r_parts = [int(x) for x in remote.split(".")]
        l_parts = [int(x) for x in local.split(".")]
        return r_parts > l_parts
    except Exception:
        return False


def get_update_notice() -> str:
    """Restituisce il messaggio formattato di notifica se è disponibile un aggiornamento."""
    info = check_for_updates()
    if info.get("has_update"):
        return (
            f"🔔 [AGGIORNAMENTO GUARDRAIL DISPONIBILE: v{info['remote_version']} (installata: v{info['local_version']})]\n"
            f"Per aggiornare automaticamente con un comando, esegui in PowerShell:\n"
            f"irm https://raw.githubusercontent.com/{GITHUB_REPO}/main/install.ps1 | iex\n"
        )
    return ""


if __name__ == "__main__":
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    res = check_for_updates(force=True)
    if res["has_update"]:
        print(f"🔔 Aggiornamento disponibile: v{res['remote_version']} (attuale: v{res['local_version']})")
        print(f"Comando di aggiornamento: irm https://raw.githubusercontent.com/{GITHUB_REPO}/main/install.ps1 | iex")
    else:
        print(f"✅ Self-Correcting LLM Guard è aggiornato all'ultima versione (v{res['local_version']}).")
