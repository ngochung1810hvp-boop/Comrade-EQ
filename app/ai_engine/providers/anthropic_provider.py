"""Anthropic API provider (AI_ROADMAP section 4.1).

API key resolution: ANTHROPIC_API_KEY env var, then the OS keyring
(service "comrade-eq", username "anthropic"). Structured output is
enforced with output_config.format json_schema, so the response is
guaranteed to be valid JSON matching RESULT_SCHEMA.
"""

import os

from ai_engine.providers.base import (
    KEYRING_SERVICE,
    InterpretResult,
    Provider,
    ProviderError,
    RESULT_SCHEMA,
    SYSTEM_PROMPT,
    parse_result,
    user_message,
)

DEFAULT_MODEL = "claude-opus-4-8"


def _api_key() -> str | None:
    key = os.environ.get("ANTHROPIC_API_KEY")
    if key:
        return key
    try:
        import keyring

        return keyring.get_password(KEYRING_SERVICE, "anthropic")
    except Exception:
        return None


class AnthropicProvider(Provider):
    name = "anthropic"

    def __init__(self, model: str | None = None):
        self.model = model or os.environ.get("COMRADE_AI_MODEL_ANTHROPIC", DEFAULT_MODEL)

    @staticmethod
    def has_key() -> bool:
        return bool(_api_key())

    def interpret(self, feedback: str, context: dict | None = None) -> InterpretResult:
        key = _api_key()
        if not key:
            raise ProviderError(
                "No Anthropic API key found. Set ANTHROPIC_API_KEY or store one "
                'in the OS keyring (service "comrade-eq", user "anthropic").'
            )
        try:
            import anthropic
        except ImportError as exc:
            raise ProviderError("The 'anthropic' package is not installed.") from exc

        client = anthropic.Anthropic(api_key=key)
        try:
            response = client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                output_config={"format": {"type": "json_schema", "schema": RESULT_SCHEMA}},
                messages=[{"role": "user", "content": user_message(feedback, context)}],
            )
        except anthropic.APIConnectionError as exc:
            raise ProviderError("Could not reach the Anthropic API.") from exc
        except anthropic.AuthenticationError as exc:
            raise ProviderError("Anthropic API key was rejected.") from exc
        except anthropic.APIStatusError as exc:
            raise ProviderError(f"Anthropic API error: {exc.message}") from exc

        if response.stop_reason == "refusal":
            raise ProviderError("The model declined to process this request.")
        text = next((b.text for b in response.content if b.type == "text"), "")
        return parse_result(text)
