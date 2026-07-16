"""AppState — mirrors the "State Management" section of
docs/design_handoff_comrade_curve/README.md.

`bands` is the source of truth for the 10-band parametric EQ model (see
BUILD_PLAN.md section 3, "Mo hinh band"): 10 bands log-spaced 25 Hz-16 kHz,
band 0 = low shelf, band 9 = high shelf, the rest peaking.
"""

from dataclasses import dataclass, field
from typing import Literal

Screen = Literal["welcome", "device", "tune"]
FilterType = Literal["LOW_SHELF", "PEAKING", "HIGH_SHELF"]

BAND_COUNT = 10
BAND_FC_MIN = 25.0
BAND_FC_MAX = 16000.0
BAND_GAIN_RANGE_DB = 12.0
BAND_GAIN_AUTOFIT_CLAMP_DB = 9.0
PEAKING_Q_DEFAULT = 1.4
SHELF_Q_DEFAULT = 0.7


@dataclass
class Band:
    fc: float
    type: FilterType
    gain: float = 0.0
    q: float = PEAKING_Q_DEFAULT


def default_bands() -> list[Band]:
    ratio = (BAND_FC_MAX / BAND_FC_MIN) ** (1 / (BAND_COUNT - 1))
    bands = []
    for i in range(BAND_COUNT):
        fc = BAND_FC_MIN * (ratio**i)
        if i == 0:
            bands.append(Band(fc=fc, type="LOW_SHELF", q=SHELF_Q_DEFAULT))
        elif i == BAND_COUNT - 1:
            bands.append(Band(fc=fc, type="HIGH_SHELF", q=SHELF_Q_DEFAULT))
        else:
            bands.append(Band(fc=fc, type="PEAKING", q=PEAKING_Q_DEFAULT))
    return bands


@dataclass
class ChatMessage:
    role: Literal["user", "assistant"]
    text: str
    diff_title: str | None = None
    diff_detail: str | None = None
    snapshot: list[float] | None = None


@dataclass
class AppState:
    screen: Screen = "welcome"

    # Selected option objects (HeadphoneEntry / AudioDevice) or None; the
    # handoff's State Management section allows "option objects/strings".
    headphone: object | None = None
    device: object | None = None
    target: str | None = None
    eq_app: str | None = None

    bands: list[Band] = field(default_factory=default_bands)
    selected_band: int | None = None

    eq_on: bool = True
    smoothed: bool = False
    preamp_auto: bool = True

    chat_open: bool = False
    save_open: bool = False
    out_menu: bool = False
    target_menu: bool = False

    messages: list[ChatMessage] = field(default_factory=list)

    profile_name: str = ""
    hp_query: str = ""
    chat_input: str = ""

    # Computed FrequencyResponse cache for the Tune screen; fr_key tracks
    # the (measurement path, target) pair the cache was built from.
    fr: object | None = None
    fr_key: tuple | None = None

    toast_text: str | None = None

    def reset_bands(self) -> None:
        self.bands = default_bands()
