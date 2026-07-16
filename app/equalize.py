"""In-process port of the webapp /equalize core path (BUILD_PLAN.md GD1.4).

Mirrors webapp/main.py::equalize() lines ~194-242: build the measurement
FrequencyResponse, resolve the target, then either smoothen-only (no target)
or run FrequencyResponse.process(). Parametric/fixed-band optimizer output
is GD2 scope (Auto-fit) and not ported here.
"""

import os
from dataclasses import dataclass

from autoeq.constants import (
    DEFAULT_BASS_BOOST_FC,
    DEFAULT_BASS_BOOST_GAIN,
    DEFAULT_BASS_BOOST_Q,
    DEFAULT_FS,
    DEFAULT_MAX_GAIN,
    DEFAULT_MAX_SLOPE,
    DEFAULT_SMOOTHING_WINDOW_SIZE,
    DEFAULT_SOUND_SIGNATURE_SMOOTHING_WINDOW_SIZE,
    DEFAULT_TILT,
    DEFAULT_TREBLE_BOOST_FC,
    DEFAULT_TREBLE_BOOST_GAIN,
    DEFAULT_TREBLE_BOOST_Q,
    DEFAULT_TREBLE_F_LOWER,
    DEFAULT_TREBLE_F_UPPER,
    DEFAULT_TREBLE_GAIN_K,
    DEFAULT_TREBLE_SMOOTHING_WINDOW_SIZE,
)
from autoeq.frequency_response import FrequencyResponse

TARGETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "targets")


@dataclass
class Options:
    bass_boost_gain: float = DEFAULT_BASS_BOOST_GAIN
    bass_boost_fc: float = DEFAULT_BASS_BOOST_FC
    bass_boost_q: float = DEFAULT_BASS_BOOST_Q
    treble_boost_gain: float = DEFAULT_TREBLE_BOOST_GAIN
    treble_boost_fc: float = DEFAULT_TREBLE_BOOST_FC
    treble_boost_q: float = DEFAULT_TREBLE_BOOST_Q
    tilt: float = DEFAULT_TILT
    fs: int = DEFAULT_FS
    max_gain: float = DEFAULT_MAX_GAIN
    max_slope: float = DEFAULT_MAX_SLOPE
    window_size: float = DEFAULT_SMOOTHING_WINDOW_SIZE
    treble_window_size: float = DEFAULT_TREBLE_SMOOTHING_WINDOW_SIZE
    treble_f_lower: float = DEFAULT_TREBLE_F_LOWER
    treble_f_upper: float = DEFAULT_TREBLE_F_UPPER
    treble_gain_k: float = DEFAULT_TREBLE_GAIN_K
    sound_signature: FrequencyResponse | None = None
    sound_signature_smoothing_window_size: float | None = (
        DEFAULT_SOUND_SIGNATURE_SMOOTHING_WINDOW_SIZE
    )


# Reference sheets that live in targets/ but hold many curves per file
# (no single SPL column), so FrequencyResponse.read_csv can't load them.
NON_TARGET_FILES = {"All Harman Targets.csv"}


def list_targets(targets_dir: str = TARGETS_DIR) -> list[str]:
    return sorted(
        f[:-4]
        for f in os.listdir(targets_dir)
        if f.endswith(".csv") and f not in NON_TARGET_FILES
    )


def load_target(target: str, targets_dir: str = TARGETS_DIR) -> FrequencyResponse:
    """Loads a target curve by name from targets/ (or by explicit path)."""
    path = target if os.path.isfile(target) else os.path.join(targets_dir, f"{target}.csv")
    if not os.path.isfile(path):
        raise ValueError(f"Unknown target {target!r}")
    return FrequencyResponse.read_csv(path)


def compute(
    measurement: str | FrequencyResponse,
    target: str | FrequencyResponse | None,
    options: Options | None = None,
) -> FrequencyResponse:
    """Port of webapp/main.py::equalize() core path, in-process.

    measurement: CSV path or a ready FrequencyResponse.
    target: name in targets/, CSV path, FrequencyResponse, or None for
        smoothen-only (webapp's no-target branch).
    Returns the measurement FrequencyResponse with smoothed/error/target/
    equalization/equalized_raw fields populated (see fr.to_dict()).
    """
    options = options or Options()

    if isinstance(measurement, FrequencyResponse):
        fr = measurement
    else:
        fr = FrequencyResponse.read_csv(measurement)
    fr.interpolate()
    fr.center()

    if target is None:
        fr.smoothen(
            window_size=options.window_size,
            treble_window_size=options.treble_window_size,
            treble_f_lower=options.treble_f_lower,
            treble_f_upper=options.treble_f_upper,
        )
        return fr

    if not isinstance(target, FrequencyResponse):
        target = load_target(target)

    fr.process(
        target=target,
        min_mean_error=True,
        bass_boost_gain=options.bass_boost_gain,
        bass_boost_fc=options.bass_boost_fc,
        bass_boost_q=options.bass_boost_q,
        treble_boost_gain=options.treble_boost_gain,
        treble_boost_fc=options.treble_boost_fc,
        treble_boost_q=options.treble_boost_q,
        tilt=options.tilt,
        fs=options.fs,
        sound_signature=options.sound_signature,
        sound_signature_smoothing_window_size=options.sound_signature_smoothing_window_size,
        max_gain=options.max_gain,
        max_slope=options.max_slope,
        window_size=options.window_size,
        treble_window_size=options.treble_window_size,
        treble_f_lower=options.treble_f_lower,
        treble_f_upper=options.treble_f_upper,
        treble_gain_k=options.treble_gain_k,
    )
    return fr
