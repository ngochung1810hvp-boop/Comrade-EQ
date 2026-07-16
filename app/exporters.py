"""Export writers for the 4 formats in the Tune export bar (BUILD_PLAN.md
GD2.4 / handoff "Export bar": Custom Parametric Eq / 10-band Graphic Eq /
EqualizerAPO / AUNBandEq).

Each formatter is deterministic text generated from the UI band model +
auto preamp; files are written next to the repo in exports/.
"""

import math
import os
import re

from state import Band

EQAPO_TYPES = {"LOW_SHELF": "LSC", "PEAKING": "PK", "HIGH_SHELF": "HSC"}
AUN_TYPES = {"LOW_SHELF": "Low Shelf", "PEAKING": "Parametric", "HIGH_SHELF": "High Shelf"}

EXPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "exports")


def _fc_str(fc: float) -> str:
    return f"{fc:.0f}"


def _q_to_bandwidth_oct(q: float) -> float:
    """Q factor -> bandwidth in octaves (AUNBandEQ uses bandwidth)."""
    return 2 * math.asinh(1 / (2 * q)) / math.log(2)


def parametric_csv(bands: list[Band], preamp: float) -> str:
    lines = ["Filter,Type,Fc (Hz),Q,Gain (dB)"]
    for i, b in enumerate(bands, start=1):
        lines.append(f"{i},{b.type},{_fc_str(b.fc)},{b.q:.2f},{b.gain:.1f}")
    lines.append(f"Preamp,,,,{preamp:.1f}")
    return "\n".join(lines) + "\n"


def graphic_eq_10(bands: list[Band], preamp: float) -> str:
    """EqualizerAPO GraphicEQ line sampled at the 10 band centers (also
    importable by Wavelet and friends). Preamp folded into the gains."""
    points = "; ".join(f"{_fc_str(b.fc)} {b.gain + preamp:.1f}" for b in bands)
    return f"GraphicEQ: {points}\n"


def equalizer_apo(bands: list[Band], preamp: float) -> str:
    lines = [f"Preamp: {preamp:.1f} dB"]
    for i, b in enumerate(bands, start=1):
        lines.append(
            f"Filter {i}: ON {EQAPO_TYPES[b.type]} Fc {_fc_str(b.fc)} Hz "
            f"Gain {b.gain:.1f} dB Q {b.q:.2f}"
        )
    return "\n".join(lines) + "\n"


def aunbandeq(bands: list[Band], preamp: float) -> str:
    lines = [
        "AUNBandEQ configuration",
        f"Global gain (preamp): {preamp:.1f} dB",
        "",
    ]
    for i, b in enumerate(bands, start=1):
        lines.append(
            f"Band {i}: {AUN_TYPES[b.type]} · Frequency {_fc_str(b.fc)} Hz · "
            f"Gain {b.gain:.1f} dB · Bandwidth {_q_to_bandwidth_oct(b.q):.2f} oct"
        )
    return "\n".join(lines) + "\n"


# Chip label -> (formatter, file extension); order matches the design's chips.
EXPORT_FORMATS = {
    "Custom Parametric Eq": (parametric_csv, "csv"),
    "10-band Graphic Eq": (graphic_eq_10, "txt"),
    "EqualizerAPO": (equalizer_apo, "txt"),
    "AUNBandEq": (aunbandeq, "txt"),
}


def export_string(fmt: str, bands: list[Band], preamp: float) -> str:
    formatter, _ = EXPORT_FORMATS[fmt]
    return formatter(bands, preamp)


def export_file(fmt: str, headphone_name: str, bands: list[Band], preamp: float) -> str:
    """Writes the export to exports/<headphone> - <format>.<ext>; returns the path."""
    formatter, ext = EXPORT_FORMATS[fmt]
    os.makedirs(EXPORTS_DIR, exist_ok=True)
    safe = re.sub(r'[<>:"/\\|?*]', "_", f"{headphone_name} - {fmt}")
    path = os.path.join(EXPORTS_DIR, f"{safe}.{ext}")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(formatter(bands, preamp))
    return path
