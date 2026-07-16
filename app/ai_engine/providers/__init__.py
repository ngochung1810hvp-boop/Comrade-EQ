"""LLM providers (AI_ROADMAP section 4.1): Anthropic API or any
OpenAI-compatible endpoint (Ollama, LM Studio).

Selection (Settings UI arrives in GD5):
- COMRADE_AI_PROVIDER = "anthropic" | "openai" forces one;
- otherwise anthropic when a key is available, else the OpenAI-compatible
  local endpoint (Ollama default http://localhost:11434/v1).
"""

import os

from ai_engine.providers.anthropic_provider import AnthropicProvider
from ai_engine.providers.base import Provider, ProviderError
from ai_engine.providers.openai_compat import OpenAICompatProvider


def get_provider() -> Provider:
    choice = os.environ.get("COMRADE_AI_PROVIDER", "").strip().lower()
    if choice == "anthropic":
        return AnthropicProvider()
    if choice in ("openai", "openai_compat", "ollama", "lmstudio"):
        return OpenAICompatProvider()
    if AnthropicProvider.has_key():
        return AnthropicProvider()
    return OpenAICompatProvider()
