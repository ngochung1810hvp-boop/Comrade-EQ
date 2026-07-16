"""Provider contract + the shared classification prompt/schema.

The LLM returns semantics only (AI_ROADMAP section 4.2): tags from the
closed VOCABULARY.md enum with direction/intensity/quote, a clarify flag
for ambiguous terms, and a short conversational reply. It never returns
Hz/Q/dB — vocabulary.py owns the numbers.
"""

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from ai_engine import vocabulary

KEYRING_SERVICE = "comrade-eq"


class ProviderError(RuntimeError):
    """Raised when a provider is unconfigured or the call/parse fails."""


@dataclass
class Adjustment:
    tag: str
    direction: str  # "reduce" | "increase"
    intensity: float  # 0..1
    quote: str = ""


@dataclass
class InterpretResult:
    adjustments: list = field(default_factory=list)
    clarify: bool = False
    question: str | None = None
    reply: str | None = None


SYSTEM_PROMPT = f"""You translate a listener's natural-language feedback about \
headphone sound into semantic EQ tags. You never output frequencies, Q values \
or dB numbers — only tags from this closed list:

Group A/B (adjustable): {", ".join([*vocabulary.GROUP_A, *vocabulary.GROUP_B, vocabulary.RELAX_TAG])}
Group C (EQ cannot fix; use the tag so the app can explain honestly): \
{", ".join(vocabulary.GROUP_C)}

Rules:
- direction is "reduce" or "increase" and applies to the perception named by \
the tag (e.g. "bass is boomy" -> tag "boomy", direction "reduce").
- intensity: "a bit/slightly" ~ 0.3, "quite/clearly" ~ 0.6, "very/way too" ~ 1.0.
- quote: copy the exact words that triggered the tag.
- Ambiguous terms (e.g. "muddy" could be tonal or transient, "bright" could be \
praise or complaint): if the context does not disambiguate, return clarify=true \
with a short question instead of guessing.
- Requests EQ cannot address (soundstage, speed, timbre, hiss) -> the matching \
group C tag, no group A/B tags for them.
- reply: one or two friendly sentences describing what you understood and what \
will change. No markdown.
Answer in the language the listener used."""

RESULT_SCHEMA = {
    "type": "object",
    "properties": {
        "adjustments": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "tag": {"type": "string", "enum": list(vocabulary.ALL_TAGS)},
                    "direction": {"type": "string", "enum": ["reduce", "increase"]},
                    "intensity": {"type": "number"},
                    "quote": {"type": "string"},
                },
                "required": ["tag", "direction", "intensity", "quote"],
                "additionalProperties": False,
            },
        },
        "clarify": {"type": "boolean"},
        "question": {"type": ["string", "null"]},
        "reply": {"type": "string"},
    },
    "required": ["adjustments", "clarify", "question", "reply"],
    "additionalProperties": False,
}


def user_message(feedback: str, context: dict | None = None) -> str:
    parts = []
    if context:
        if context.get("headphone"):
            parts.append(f"Headphones: {context['headphone']}")
        if context.get("bands"):
            parts.append(f"Current 10-band gains (dB): {context['bands']}")
    parts.append(f"Listener feedback: {feedback}")
    return "\n".join(parts)


def parse_result(text: str) -> InterpretResult:
    """Parses the model's JSON into an InterpretResult, dropping unknown tags."""
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ProviderError(f"Model returned invalid JSON: {exc}") from exc
    adjustments = []
    for item in data.get("adjustments", []):
        tag = item.get("tag")
        if tag not in vocabulary.ALL_TAGS:
            continue  # closed enum: silently drop hallucinated tags
        direction = item.get("direction", "reduce")
        if direction not in ("reduce", "increase"):
            direction = "reduce"
        try:
            intensity = float(item.get("intensity", 0.5))
        except (TypeError, ValueError):
            intensity = 0.5
        adjustments.append(
            Adjustment(
                tag=tag,
                direction=direction,
                intensity=max(0.0, min(1.0, intensity)),
                quote=str(item.get("quote", "")),
            )
        )
    return InterpretResult(
        adjustments=adjustments,
        clarify=bool(data.get("clarify", False)),
        question=data.get("question") or None,
        reply=data.get("reply") or None,
    )


class Provider(ABC):
    name: str = "base"

    @abstractmethod
    def interpret(self, feedback: str, context: dict | None = None) -> InterpretResult:
        """Classifies feedback into tags; raises ProviderError on failure."""
