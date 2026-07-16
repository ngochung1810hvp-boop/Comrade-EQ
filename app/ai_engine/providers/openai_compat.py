"""OpenAI-compatible chat-completions provider for local models
(Ollama http://localhost:11434/v1, LM Studio http://localhost:1234/v1).

Uses stdlib urllib so no extra dependency is needed for local inference.
JSON mode (response_format json_object) is requested; parse_result still
validates and drops anything outside the closed tag enum. Suggested local
models (AI_ROADMAP): Qwen 2.5 7B-instruct or Llama 3.1 8B.
"""

import json
import os
import urllib.error
import urllib.request

from ai_engine.providers.base import (
    KEYRING_SERVICE,
    InterpretResult,
    Provider,
    ProviderError,
    SYSTEM_PROMPT,
    parse_result,
    user_message,
)

DEFAULT_BASE_URL = "http://localhost:11434/v1"
DEFAULT_MODEL = "qwen2.5:7b"
TIMEOUT_S = 60

# JSON mode alone doesn't enforce the schema, so restate it in the prompt.
_JSON_INSTRUCTION = (
    "\nReturn ONLY a JSON object: {\"adjustments\": [{\"tag\": str, "
    "\"direction\": \"reduce\"|\"increase\", \"intensity\": number 0..1, "
    "\"quote\": str}], \"clarify\": bool, \"question\": str|null, "
    "\"reply\": str}."
)


def _api_key() -> str | None:
    key = os.environ.get("OPENAI_API_KEY")
    if key:
        return key
    try:
        import keyring

        return keyring.get_password(KEYRING_SERVICE, "openai")
    except Exception:
        return None


class OpenAICompatProvider(Provider):
    name = "openai_compat"

    def __init__(self, base_url: str | None = None, model: str | None = None):
        self.base_url = (
            base_url or os.environ.get("COMRADE_AI_BASE_URL", DEFAULT_BASE_URL)
        ).rstrip("/")
        self.model = model or os.environ.get("COMRADE_AI_MODEL", DEFAULT_MODEL)

    def interpret(self, feedback: str, context: dict | None = None) -> InterpretResult:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT + _JSON_INSTRUCTION},
                {"role": "user", "content": user_message(feedback, context)},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2,
        }
        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        key = _api_key()
        if key:
            request.add_header("Authorization", f"Bearer {key}")
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT_S) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise ProviderError(
                f"Could not reach the local model at {self.base_url} — is Ollama "
                "or LM Studio running?"
            ) from exc
        except json.JSONDecodeError as exc:
            raise ProviderError("Local model returned a non-JSON response.") from exc

        try:
            text = body["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderError("Unexpected response shape from the local model.") from exc
        return parse_result(text)
