# 🛡️ Self-Correcting LLM Guard & Evals

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Pattern](https://img.shields.io/badge/Architecture-Reflection%20Pattern-orange.svg)]()
[![Evals](https://img.shields.io/badge/Evals-Passing%20(100%25)-brightgreen.svg)]()
[![License](https://img.shields.io/badge/License-MIT-purple.svg)]()

> Un sistema agentico di **Auto-Correzione (Reflection Pattern)** e **Guardrails di Sicurezza** per LLM. Intercetta in tempo reale allucinazioni, promesse non autorizzate e prompt injection, costringendo l'AI ad auto-correggersi prima di consegnare la risposta all'utente.

---

## 📌 Perché questo progetto?

Nei sistemi AI in produzione, i modelli linguistici possono essere ingannevoli: inventano dati (*allucinazioni*), infrangono policy aziendali (es. promettendo sconti non autorizzati) o subiscono attacchi di prompt injection.

Questo progetto implementa una **pipeline affidabile e verificata**:
1. **Guardrail di Ingresso**: Blocca istantaneamente attacchi di injection prima ancora di chiamare il modello.
2. **Generatore (Attore)**: Produce la prima bozza di risposta.
3. **Giudice (Critico)**: Verifica la bozza rispetto alle policy e alle verità ufficiali (`knowledge_base.json`).
4. **Ciclo di Auto-Correzione**: Se il Giudice rileva allucinazioni, invia un feedback correttivo all'Attore per rigenerare una risposta conforme.
5. **Suite di Valutazione (Evals)**: Test automatici con `pytest` per misurare la robustezza ed evitare regressioni.

---

## 🏗️ Architettura del Sistema

```mermaid
flowchart TD
    User([👤 Utente]) --> InGuard{1. Input Guardrail\nFiltro Sicurezza}
    
    InGuard -->|Attacco Rilevato| Blocked[🚫 Richiesta Rifiutata]
    InGuard -->|Query Sicura| Actor[2. Attore / Generatore\nProduce Bozza]
    
    Actor --> Critic{3. Giudice / Critic\nVerifica Policy & Fatti}
    
    Critic -->|Violazione Rilevata| Refine[4. Ciclo di Riflessione\nInvia Feedback Correttivo]
    Refine --> Actor
    
    Critic -->|Bozza Conforme| Output([✅ Risposta Validata all'Utente])
```

---

## 🚀 Avvio Rapido

### 1. Prerequisiti e Installazione
Clona il repository e installa le dipendenze:
```bash
git clone https://github.com/tuo-username/self-correcting-llm-guard.git
cd self-correcting-llm-guard

pip install -r requirements.txt
```

### 2. Esecuzione Interattiva (Terminal UI a colori)
Avvia la dashboard interattiva da terminale:
```bash
python main.py
```

Potrai scegliere tra diversi scenari di test (sconti vietati, violazioni sui resi, injection) e **vedere a schermo l'AI mentre si corregge da sola in tempo reale**.

### 3. Esecuzione della Suite di Valutazione (Evals)
Lancia la suite di test automatizzati:
```bash
pytest tests/test_evals.py -v
```

Output atteso:
```text
tests/test_evals.py::test_discount_hallucination_is_self_corrected PASSED [ 25%]
tests/test_evals.py::test_return_policy_hallucination_is_self_corrected PASSED [ 50%]
tests/test_evals.py::test_prompt_injection_is_blocked_immediately PASSED [ 75%]
tests/test_evals.py::test_legitimate_query_passes_without_corrections PASSED [100%]
============================== 4 passed in 0.25s ==============================
```

---

## 🧩 Struttura del Progetto

```text
self-correcting-llm-guard/
├── knowledge_base.json     # Policy aziendali e vincoli ufficiali
├── models.py               # Schemi Pydantic per Critique e Tracciamento
├── guardrail_critic.py     # Motore Giudice (Validazione regole e allucinazioni)
├── agent.py                # Agente principale (Reflection loop)
├── llm_provider.py         # Provider modulari (Simulatore locale, Ollama, API Cloud)
├── main.py                 # CLI interattiva con visualizzazione Rich
├── tests/
│   └── test_evals.py       # Suite di valutazione automatizzata (Evals)
├── requirements.txt        # Dipendenze Python
└── README.md               # Documentazione del progetto
```

---

## 🔌 Come collegare modelli locali (Ollama)

Se vuoi usare un modello locale sul tuo computer (es. `Llama 3.2` o `Qwen 2.5`):
1. Installa [Ollama](https://ollama.com/) e scarica il modello:
   ```bash
   ollama run llama3.2
   ```
2. In `main.py` o nel tuo script, passa `OllamaLLMProvider`:
   ```python
   from llm_provider import OllamaLLMProvider
   from agent import SelfCorrectingAgent

   agent = SelfCorrectingAgent(llm_provider=OllamaLLMProvider(model_name="llama3.2"))
   ```

---

## 📜 Licenza
Rilasciato sotto licenza MIT. Libero per uso didattico e portfolio professionale.
