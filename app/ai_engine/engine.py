"""engine.propose() — turns feedback into a Proposal; never applies it.

Pipeline (AI_ROADMAP section 4): provider.interpret() -> closed-enum tags ->
vocabulary.map_adjustment() (deterministic numbers) -> safety clamps ->
Proposal. apply_proposal() pours the proposal into the UI's 10 fixed bands
(same frequency region, faders visibly jump — matching the prototype's
canned behavior) and returns an undo snapshot.
"""

from dataclasses import dataclass, field

from ai_engine import vocabulary
from ai_engine.providers.base import Provider, ProviderError
from state import BAND_GAIN_RANGE_DB


@dataclass
class Proposal:
    reply: str
    filters: list = field(default_factory=list)  # FilterDelta, source="ai"
    relax: float = 0.0  # balance_natural: scale band gains toward 0
    note: str | None = None  # group B honest-limitation note
    clarify: bool = False
    error: bool = False
    tags: list = field(default_factory=list)  # (tag, direction, intensity)

    @property
    def changes_eq(self) -> bool:
        return bool(self.filters) or self.relax > 0


def propose(
    feedback: str,
    headphone: str | None = None,
    bands: list | None = None,
    provider: Provider | None = None,
) -> Proposal:
    """Classifies feedback and maps it to a deterministic, clamped proposal."""
    if provider is None:
        from ai_engine.providers import get_provider

        provider = get_provider()

    context = {"headphone": headphone}
    if bands:
        context["bands"] = [round(b.gain, 1) for b in bands]
    try:
        result = provider.interpret(feedback, context)
    except ProviderError as exc:
        return Proposal(reply=str(exc), error=True)

    if result.clarify:
        return Proposal(
            reply=result.question or result.reply or "Could you describe that differently?",
            clarify=True,
        )

    filters = []
    relax = 0.0
    notes = []
    explanations = []
    tags = []
    for adj in result.adjustments:
        mapped = vocabulary.map_adjustment(adj.tag, adj.direction, adj.intensity)
        filters.extend(mapped.filters)
        relax = max(relax, mapped.relax)
        if mapped.note:
            notes.append(mapped.note)
        if mapped.explanation:
            explanations.append(mapped.explanation)
        tags.append((adj.tag, adj.direction, adj.intensity))
    vocabulary.clamp_overlap(filters)

    reply = result.reply or ""
    if explanations and not filters and relax == 0:
        # Pure group C: honest explanation, no EQ change.
        reply = " ".join([reply, *explanations]).strip() or explanations[0]
        return Proposal(reply=reply, tags=tags)
    if explanations:
        reply = " ".join([reply, *explanations]).strip()
    if not reply:
        reply = "Here is what I would adjust." if filters or relax else (
            "I couldn't map that to an EQ change — try describing the region "
            "(bass, mids, treble) that bothers you."
        )
    return Proposal(
        reply=reply,
        filters=filters,
        relax=relax,
        note=" ".join(dict.fromkeys(notes)) or None,
        tags=tags,
    )


def apply_proposal(bands: list, proposal: Proposal) -> tuple[list, str] | None:
    """Pours the proposal's deltas into the 10 fixed bands, in place.

    Each filter's gain is added to every band whose fc falls in the tag's
    perceptual region; relax scales all gains toward 0. Returns
    (snapshot_of_previous_gains, detail_text) for the APPLIED card and its
    undo link, or None when the proposal changes nothing.
    """
    if not proposal.changes_eq:
        return None
    snapshot = [b.gain for b in bands]
    details = []
    for f in proposal.filters:
        try:
            f_lo, f_hi = vocabulary.region_for(f.tag)
        except ValueError:
            f_lo, f_hi = f.fc / 1.5, f.fc * 1.5
        touched = 0
        for band in bands:
            if f_lo <= band.fc <= f_hi:
                band.gain = _quantize(band.gain + f.gain)
                touched += 1
        details.append(f"{f.tag} {f.gain:+.1f} dB @ {_fmt_hz(f.fc)} · {touched} bands")
    if proposal.relax > 0:
        for band in bands:
            band.gain = _quantize(band.gain * (1 - proposal.relax))
        details.append(f"all bands relaxed {proposal.relax:.0%} toward 0")
    return snapshot, "\n".join(details)


def restore_snapshot(bands: list, snapshot: list) -> None:
    for band, gain in zip(bands, snapshot):
        band.gain = gain


def _quantize(gain: float) -> float:
    gain = max(-BAND_GAIN_RANGE_DB, min(BAND_GAIN_RANGE_DB, gain))
    return round(gain * 2) / 2


def _fmt_hz(fc: float) -> str:
    return f"{fc / 1000:.0f} kHz" if fc >= 1000 else f"{fc:.0f} Hz"
