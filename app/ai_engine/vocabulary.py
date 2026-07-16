"""Deterministic tag -> PEQ filter mapping, generated from docs/VOCABULARY.md.

The LLM may only return tags from the closed enum below; every Hz/Q/dB
number comes from this table plus the safety clamps, never from the LLM.

Groups (VOCABULARY.md):
- A: EQ can address directly -> produces filters.
- B: EQ helps indirectly -> produces filters plus an honest limitation note.
- C: EQ cannot address -> no filters, only an explanation.

Direction convention: ``reduce``/``increase`` applies to the *perception*
named by the tag. For deficiency tags (thin_cool, mid_recessed, dark_veiled)
reducing the problem means boosting the region, encoded via ``reduce_sign``.
"""

from dataclasses import dataclass, field

from profile_store import FilterDelta

# VOCABULARY.md "Quy uoc" + safety clamps
BASE_GAIN_PEAKING = 4.0
BASE_GAIN_SHELF = 3.0
GAIN_LIMIT_DB = 6.0  # per filter
OVERLAP_LIMIT_DB = 9.0  # summed |gain| of region-overlapping filters
Q_MIN, Q_MAX = 0.3, 6.0


@dataclass(frozen=True)
class TagSpec:
    type: str  # LOW_SHELF | PEAKING | HIGH_SHELF
    fc: float
    q: float
    f_lo: float  # perceptual region, also used to pour deltas into UI bands
    f_hi: float
    reduce_sign: float = -1.0  # deficiency tags: reduce the problem = boost
    note: str | None = None  # group B honest-limitation note


# -- Group A ---------------------------------------------------------------

GROUP_A: dict[str, TagSpec] = {
    "sub_bass_weight": TagSpec("LOW_SHELF", 60, 0.7, 20, 60),
    "punch": TagSpec("PEAKING", 100, 1.0, 60, 150),
    "boomy": TagSpec("PEAKING", 125, 1.4, 100, 160),
    "bloated": TagSpec("PEAKING", 250, 1.4, 200, 320),
    "bass_bleed": TagSpec("PEAKING", 200, 1.2, 150, 300),
    "warmth": TagSpec("LOW_SHELF", 200, 0.7, 100, 300),
    "thin_cool": TagSpec("LOW_SHELF", 150, 0.7, 20, 150, reduce_sign=1.0),
    "mud": TagSpec("PEAKING", 300, 1.2, 200, 500),
    "boxy": TagSpec("PEAKING", 400, 1.5, 250, 500),
    "honky_nasal": TagSpec("PEAKING", 600, 2.0, 500, 700),
    "mid_recessed": TagSpec("PEAKING", 1500, 0.8, 500, 3000, reduce_sign=1.0),
    "forward_aggressive": TagSpec("PEAKING", 2500, 1.0, 1000, 4000),
    "presence": TagSpec("PEAKING", 4000, 1.4, 3000, 5000),
    "harsh": TagSpec("PEAKING", 4500, 2.0, 3000, 6000),
    "piercing": TagSpec("PEAKING", 8000, 3.0, 3000, 10000),
    "sibilance": TagSpec("PEAKING", 7000, 3.0, 4000, 9000),
    "bright": TagSpec("HIGH_SHELF", 6000, 0.7, 5000, 16000),
    "dark_veiled": TagSpec("HIGH_SHELF", 10000, 0.7, 8000, 20000, reduce_sign=1.0),
    "air": TagSpec("HIGH_SHELF", 12000, 0.7, 10000, 16000),
}

# -- Group B (indirect: one or two filters at reduced strength + a note) ----

_NOTE_DETAIL = (
    "True detail is set by the driver; EQ can only lift the veil by cutting "
    "masking lows and lifting the presence region a little."
)
_NOTE_TIGHT = (
    "Transient response can't be changed with PEQ; trimming 150-300 Hz keeps "
    "sub-bass but makes bass feel tighter."
)
_NOTE_SMOOTH = "Softening 2-5 kHz and the treble shelf relaxes the sound."
_NOTE_FATIGUE = (
    "Fatigue usually comes from 3-6 kHz glare or 7-9 kHz sibilance; both are "
    "eased slightly."
)

GROUP_B: dict[str, list[tuple[TagSpec, float]]] = {
    # tag -> [(spec, strength multiplier applied to base gain), ...]
    "detail_clarity": [
        (TagSpec("PEAKING", 300, 1.0, 200, 400, note=_NOTE_DETAIL), -0.4),
        (TagSpec("PEAKING", 5000, 1.0, 3000, 8000, note=_NOTE_DETAIL), 0.4),
    ],
    "tight": [(TagSpec("PEAKING", 200, 1.0, 150, 300, note=_NOTE_TIGHT), -0.6)],
    "smooth_relaxed": [
        (TagSpec("PEAKING", 3500, 0.8, 2000, 5000, note=_NOTE_SMOOTH), -0.6),
        (TagSpec("HIGH_SHELF", 8000, 0.7, 6000, 16000, note=_NOTE_SMOOTH), -0.3),
    ],
    "fatigue": [
        (TagSpec("PEAKING", 4500, 1.4, 3000, 6000, note=_NOTE_FATIGUE), -0.45),
        (TagSpec("PEAKING", 8000, 1.4, 7000, 9000, note=_NOTE_FATIGUE), -0.45),
    ],
}

# balance_natural is group B but maps to an action (scale deltas toward 0),
# not to new filters.
RELAX_TAG = "balance_natural"

# -- Group C (no filters; honest explanation) -------------------------------

GROUP_C: dict[str, str] = {
    "spatial": (
        "Soundstage, imaging and width can't be created with a parametric EQ — "
        "they come from the headphone and recording. Crossfeed or spatial DSP "
        "can help; a small 'air' boost is the closest EQ approximation."
    ),
    "temporal": (
        "Speed, attack, decay and dynamics are driver and recording traits that "
        "EQ can't change. If the looseness lives in the bass, a 'tighter bass' "
        "request can help indirectly."
    ),
    "timbre": (
        "Timbre and texture are a blend of many factors. Tell me which region "
        "sounds off — bass, mids, treble — and I can translate that into EQ."
    ),
    "source": (
        "Hiss, pops and recording quality come from the source device or the "
        "track itself, not something EQ can fix."
    ),
}

ALL_TAGS: tuple[str, ...] = (
    *GROUP_A, *GROUP_B, RELAX_TAG, *GROUP_C,
)


@dataclass
class Mapped:
    """Deterministic result of one (tag, direction, intensity) adjustment."""

    filters: list[FilterDelta] = field(default_factory=list)
    relax: float = 0.0  # 0..1 — scale existing gains toward 0 by this much
    note: str | None = None
    explanation: str | None = None  # group C: reply text, no filters


def _clamp_gain(gain: float) -> float:
    return max(-GAIN_LIMIT_DB, min(GAIN_LIMIT_DB, gain))


def _delta(tag: str, spec: TagSpec, gain: float) -> FilterDelta:
    return FilterDelta(
        tag=tag,
        type=spec.type,
        fc=spec.fc,
        q=max(Q_MIN, min(Q_MAX, spec.q)),
        gain=round(_clamp_gain(gain), 2),
        source="ai",
    )


def map_adjustment(tag: str, direction: str, intensity: float) -> Mapped:
    """VOCABULARY.md table lookup: tag -> filters/action/explanation.

    intensity is the LLM's 0..1 estimate ("a bit" ~0.3, "quite" ~0.6,
    "very" ~1.0); gain = direction * intensity * base_gain.
    """
    intensity = max(0.0, min(1.0, intensity))
    sign = 1.0 if direction == "reduce" else -1.0  # applied to reduce_sign

    if tag in GROUP_A:
        spec = GROUP_A[tag]
        base = BASE_GAIN_SHELF if spec.type.endswith("SHELF") else BASE_GAIN_PEAKING
        gain = sign * spec.reduce_sign * intensity * base
        return Mapped(filters=[_delta(tag, spec, gain)])

    if tag in GROUP_B:
        filters = []
        note = None
        for spec, strength in GROUP_B[tag]:
            base = BASE_GAIN_SHELF if spec.type.endswith("SHELF") else BASE_GAIN_PEAKING
            # Group B strengths encode the strategy sign for the "reduce the
            # complaint" direction; "increase" flips it.
            gain = (1.0 if direction == "reduce" else -1.0) * strength * intensity * base
            filters.append(_delta(tag, spec, gain))
            note = spec.note
        return Mapped(filters=filters, note=note)

    if tag == RELAX_TAG:
        return Mapped(relax=0.5 * intensity + 0.25)

    if tag in GROUP_C:
        return Mapped(explanation=GROUP_C[tag])

    raise ValueError(f"Unknown tag {tag!r}")


def region_for(tag: str) -> tuple[float, float]:
    """Perceptual frequency region of a group A/B tag (for band pouring)."""
    if tag in GROUP_A:
        spec = GROUP_A[tag]
        return spec.f_lo, spec.f_hi
    if tag in GROUP_B:
        specs = GROUP_B[tag]
        return min(s.f_lo for s, _ in specs), max(s.f_hi for s, _ in specs)
    raise ValueError(f"No region for tag {tag!r}")


def clamp_overlap(filters: list[FilterDelta]) -> list[FilterDelta]:
    """VOCABULARY.md rule 3: overlapping regions obey a summed 9 dB budget.

    Filters are grouped by overlapping fc octaves (within ~1 octave of each
    other); if the summed |gain| of a group exceeds the budget, the whole
    group is scaled down proportionally.
    """
    if not filters:
        return filters
    ordered = sorted(filters, key=lambda d: d.fc)
    groups: list[list[FilterDelta]] = [[ordered[0]]]
    for f in ordered[1:]:
        if f.fc <= groups[-1][-1].fc * 2:
            groups[-1].append(f)
        else:
            groups.append([f])
    for group in groups:
        total = sum(abs(f.gain) for f in group)
        if total > OVERLAP_LIMIT_DB:
            scale = OVERLAP_LIMIT_DB / total
            for f in group:
                f.gain = round(f.gain * scale, 2)
    return filters
