"""Bridge between the UI's 10 fixed bands and the autoeq core (BUILD_PLAN.md
section 3, "Mo hinh band").

`state.bands` stays the source of truth; whenever the EQ/preamp curve is
needed the bands are poured into `autoeq.peq` filters and summed via PEQ.fr.
Auto-fit runs the core optimizer with the 10-band layout fixed in fc/type
(gain and a narrow Q range optimized), falling back to the prototype's
"target minus raw at fc" sampling if the optimizer fails.
"""

import numpy as np

from autoeq.constants import DEFAULT_FS
from autoeq.frequency_response import FrequencyResponse
from autoeq.peq import PEQ, HighShelf, LowShelf, Peaking
from state import BAND_GAIN_AUTOFIT_CLAMP_DB, Band

PREAMP_HEADROOM_DB = 0.4

AUTOFIT_PEAKING_MIN_Q = 0.5
AUTOFIT_PEAKING_MAX_Q = 2.0
AUTOFIT_MAX_TIME_S = 2.0

_FILTER_CLASSES = {"LOW_SHELF": LowShelf, "PEAKING": Peaking, "HIGH_SHELF": HighShelf}


def build_peq(bands: list[Band], f: np.ndarray, fs: int = DEFAULT_FS) -> PEQ:
    filters = [
        _FILTER_CLASSES[b.type](f, fs, fc=b.fc, q=b.q, gain=b.gain)
        for b in bands
    ]
    return PEQ(f, fs, filters=filters)


def eq_curve(bands: list[Band], f: np.ndarray, fs: int = DEFAULT_FS) -> np.ndarray:
    """Summed frequency response of the 10 bands, in dB, over `f`."""
    if all(b.gain == 0 for b in bands):
        return np.zeros(len(f))
    return build_peq(bands, f, fs).fr


def preamp_db(bands: list[Band], f: np.ndarray, fs: int = DEFAULT_FS) -> float:
    """Auto preamp: -(max EQ boost + 0.4 dB headroom), never positive."""
    max_boost = float(np.max(eq_curve(bands, f, fs), initial=0.0))
    if max_boost <= 0:
        return 0.0
    return -(max_boost + PREAMP_HEADROOM_DB)


def auto_fit(fr: FrequencyResponse, bands: list[Band], fs: int = DEFAULT_FS) -> list[Band]:
    """Fits the 10 fixed bands to fr.equalization (requires a processed fr).

    Returns new Band objects; fc and type are kept, gain is clamped to
    +-BAND_GAIN_AUTOFIT_CLAMP_DB and Q optimized in a narrow range
    (shelves stay at their default Q).
    """
    try:
        config = {
            "optimizer": {"max_time": AUTOFIT_MAX_TIME_S},
            "filters": [_autofit_filter_config(b) for b in bands],
        }
        peq = fr.optimize_fixed_band_eq([config], fs, preamp=0.0)[0]
        return [
            Band(fc=b.fc, type=b.type, gain=round(f.gain * 2) / 2, q=round(f.q, 2))
            for b, f in zip(bands, peq.filters)
        ]
    except Exception:
        return _auto_fit_simple(fr, bands)


def _autofit_filter_config(band: Band) -> dict:
    config = {
        "type": band.type,
        "fc": band.fc,
        "min_gain": -BAND_GAIN_AUTOFIT_CLAMP_DB,
        "max_gain": BAND_GAIN_AUTOFIT_CLAMP_DB,
    }
    if band.type == "PEAKING":
        config["min_q"] = AUTOFIT_PEAKING_MIN_Q
        config["max_q"] = AUTOFIT_PEAKING_MAX_Q
    else:
        config["q"] = band.q  # shelves keep their default Q
    return config


def _auto_fit_simple(fr: FrequencyResponse, bands: list[Band]) -> list[Band]:
    """Prototype fallback: sample the error correction at each band fc."""
    clamp = BAND_GAIN_AUTOFIT_CLAMP_DB
    gains = np.interp(
        np.log10([b.fc for b in bands]),
        np.log10(fr.frequency),
        fr.equalization,
    )
    return [
        Band(fc=b.fc, type=b.type, q=b.q, gain=float(np.clip(round(g * 2) / 2, -clamp, clamp)))
        for b, g in zip(bands, gains)
    ]
