"""LOP 3 — persistent preference memory (BUILD_PLAN.md GD3, AI_ROADMAP section 3).

profiles/<name>.json keeps the user's taste in two forms:

- ``filter_deltas`` — the semantic source form: tag from VOCABULARY.md,
  deterministic type/fc/Q, gain plus a confidence ``weight``. This is the
  form that gets displayed, edited and decayed.
- ``preference_curve`` — the apply form: the deltas rendered with ``PEQ.fr``
  on the standard 20 Hz-20 kHz grid. It is passed to
  ``FrequencyResponse.process()`` as ``sound_signature``, so the core stays
  untouched (AI_ROADMAP's key finding).

The file also carries the GD2 tune snapshot (bands/target/preamp) and an
accept/undo ``history`` that GD4-5 feed the learning loop from.
"""

import json
import os
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone

import numpy as np

from autoeq.constants import DEFAULT_FS
from autoeq.frequency_response import FrequencyResponse
from autoeq.peq import PEQ, HighShelf, LowShelf, Peaking

PROFILES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "profiles"
)

SCHEMA_VERSION = 1
# AI_ROADMAP GD3: gain_new = alpha * proposed + (1 - alpha) * old
EMA_ALPHA = 0.4
WEIGHT_INITIAL = 0.5
WEIGHT_STEP = 0.1
# VOCABULARY.md safety clamps (also enforced upstream in GD4's engine).
DELTA_GAIN_LIMIT_DB = 6.0
DELTA_Q_MIN = 0.3
DELTA_Q_MAX = 6.0

_FILTER_CLASSES = {"LOW_SHELF": LowShelf, "PEAKING": Peaking, "HIGH_SHELF": HighShelf}


def _utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class FilterDelta:
    """One semantic preference adjustment; ``tag`` matches VOCABULARY.md."""

    tag: str
    type: str  # LOW_SHELF | PEAKING | HIGH_SHELF
    fc: float
    q: float
    gain: float
    scope: str = "global"  # "global" or "headphone:<name>"
    source: str = "manual"  # "manual" or "ai"
    weight: float = WEIGHT_INITIAL

    def clamped(self) -> "FilterDelta":
        return FilterDelta(
            tag=self.tag,
            type=self.type,
            fc=float(np.clip(self.fc, 20.0, 20000.0)),
            q=float(np.clip(self.q, DELTA_Q_MIN, DELTA_Q_MAX)),
            gain=float(np.clip(self.gain, -DELTA_GAIN_LIMIT_DB, DELTA_GAIN_LIMIT_DB)),
            scope=self.scope,
            source=self.source,
            weight=float(np.clip(self.weight, 0.0, 1.0)),
        )

    def applies_to(self, headphone: str | None) -> bool:
        if self.scope == "global":
            return True
        return headphone is not None and self.scope == f"headphone:{headphone}"


@dataclass
class Profile:
    name: str = "default"
    updated_at: str = ""
    # GD2 tune snapshot
    headphone: str | None = None
    target: str | None = None
    preamp: float = 0.0
    bands: list = field(default_factory=list)
    # Preference memory (AI_ROADMAP section 3 schema)
    filter_deltas: list = field(default_factory=list)
    history: list = field(default_factory=list)

    def deltas_for(self, headphone: str | None = None) -> list:
        return [d for d in self.filter_deltas if d.applies_to(headphone)]

    def render_curve(
        self, headphone: str | None = None, fs: int = DEFAULT_FS
    ) -> tuple[np.ndarray, np.ndarray]:
        """Renders filter_deltas into the apply-form curve on the standard grid.

        Each delta contributes gain scaled by its confidence weight, so an
        unconfirmed taste (weight 0.5) applies at half strength until the
        learning loop reinforces it.
        """
        f = FrequencyResponse.generate_frequencies()
        deltas = [d for d in self.deltas_for(headphone) if d.gain * d.weight != 0.0]
        if not deltas:
            return f, np.zeros(f.shape)
        filters = [
            _FILTER_CLASSES[d.type](f, fs, fc=d.fc, q=d.q, gain=d.gain * d.weight)
            for d in deltas
        ]
        return f, PEQ(f, fs, filters=filters).fr

    def as_sound_signature(
        self, headphone: str | None = None
    ) -> FrequencyResponse | None:
        """The preference curve as a FrequencyResponse for compute(...,
        sound_signature=...), or None when there is nothing to apply."""
        f, curve = self.render_curve(headphone)
        if not np.any(curve):
            return None
        return FrequencyResponse(name="sound signature", frequency=f, raw=curve)

    def merge_delta(self, delta: FilterDelta, alpha: float = EMA_ALPHA) -> FilterDelta:
        """Merges a proposed delta into filter_deltas (AI_ROADMAP GD3).

        Same tag+scope -> EMA on gain and a weight bump; the deterministic
        type/fc/Q of the existing entry win. New tag -> appended at the
        initial confidence weight. Returns the stored entry.
        """
        delta = delta.clamped()
        for existing in self.filter_deltas:
            if existing.tag == delta.tag and existing.scope == delta.scope:
                existing.gain = float(
                    np.clip(
                        alpha * delta.gain + (1 - alpha) * existing.gain,
                        -DELTA_GAIN_LIMIT_DB,
                        DELTA_GAIN_LIMIT_DB,
                    )
                )
                existing.weight = float(min(1.0, existing.weight + WEIGHT_STEP))
                existing.source = delta.source
                return existing
        delta.weight = WEIGHT_INITIAL
        self.filter_deltas.append(delta)
        return delta

    def record_history(self, **entry) -> dict:
        entry = {"ts": _utcnow(), **entry}
        self.history.append(entry)
        return entry

    def to_dict(self) -> dict:
        f, curve = self.render_curve()
        return {
            "version": SCHEMA_VERSION,
            "profile_name": self.name,
            "updated_at": self.updated_at,
            "headphone": self.headphone,
            "target": self.target,
            "preamp": round(self.preamp, 2),
            "bands": self.bands,
            "preference_curve": {
                "frequency": [round(float(x), 2) for x in f],
                "raw": [round(float(y), 3) for y in curve],
            },
            "filter_deltas": [asdict(d) for d in self.filter_deltas],
            "history": self.history,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Profile":
        return cls(
            name=data.get("profile_name", "default"),
            updated_at=data.get("updated_at", ""),
            headphone=data.get("headphone"),
            target=data.get("target"),
            preamp=data.get("preamp", 0.0),
            bands=data.get("bands", []),
            filter_deltas=[FilterDelta(**d) for d in data.get("filter_deltas", [])],
            history=data.get("history", []),
        )


class ProfileStore:
    """Loads/saves profiles/<name>.json with atomic writes."""

    def __init__(self, directory: str = PROFILES_DIR):
        self.directory = directory

    def path(self, name: str) -> str:
        safe = re.sub(r'[<>:"/\\|?*]', "_", name.strip())
        return os.path.join(self.directory, f"{safe}.json")

    def list_names(self) -> list[str]:
        if not os.path.isdir(self.directory):
            return []
        names = []
        for fname in sorted(os.listdir(self.directory)):
            if fname.endswith(".json"):
                names.append(fname[:-5])
        return names

    def exists(self, name: str) -> bool:
        return os.path.isfile(self.path(name))

    def load(self, name: str) -> Profile:
        with open(self.path(name), encoding="utf-8") as fh:
            return Profile.from_dict(json.load(fh))

    def load_latest(self) -> Profile | None:
        """The most recently updated profile, or None when there is none."""
        latest = None
        for name in self.list_names():
            try:
                profile = self.load(name)
            except (OSError, ValueError, KeyError, TypeError):
                continue
            if latest is None or profile.updated_at > latest.updated_at:
                latest = profile
        return latest

    def save(self, profile: Profile) -> str:
        os.makedirs(self.directory, exist_ok=True)
        profile.updated_at = _utcnow()
        path = self.path(profile.name)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(profile.to_dict(), fh, indent=2)
        os.replace(tmp, path)
        return path
