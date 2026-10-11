import pytest
from code_guard import CodeGuard


@pytest.fixture
def guard():
    return CodeGuard()


def test_syntax_error_detected(guard):
    bad_code = """Ecco la funzione richiesta:
```python
def calcola(x, y
    return x + y
```
"""
    result = guard.audit_response(bad_code)
    assert not result.is_valid
    assert any("Errore di sintassi Python" in v for v in result.violations)


def test_hardcoded_secret_detected(guard):
    secret_code = """Usa questo script per collegarti:
```python
import openai
openai.api_key = "sk-abcdef1234567890abcdef12345"
```
"""
    result = guard.audit_response(secret_code)
    assert not result.is_valid
    assert any("OpenAI API Key in chiaro" in v or "API Token" in v for v in result.violations)


def test_dangerous_destructive_command_detected(guard):
    danger = """Per ripulire la cache:
```bash
rm -rf /
```
"""
    result = guard.audit_response(danger)
    assert not result.is_valid
    assert any("Comando distruttivo" in v for v in result.violations)


def test_clean_code_and_policy_passes(guard):
    clean = """Ecco il codice corretto conforme alle policy:
```python
import os

api_key = os.environ.get("OPENAI_API_KEY")
print("Chiave caricata con successo")
```
Ricorda che la spedizione standard è 4.99€ ed è gratuita oltre i 50€.
"""
    result = guard.audit_response(clean)
    assert result.is_valid
    assert len(result.violations) == 0
