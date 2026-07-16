"""10-band parametric EQ card (BUILD_PLAN.md GD2.3).

Handoff spec: header row ("10-BAND PARAMETRIC EQ" + Auto-fit green outline
chip + Reset chip), 10 draggable vertical faders (120px track, fill from
center, green boost / coral cut, 0.5 dB steps, +-12 dB), per-band frequency
labels, and a detail row for the selected band (fc log slider, Q 0.3-6,
signed gain readout).
"""

import math

import flet as ft

import theme
from state import BAND_GAIN_RANGE_DB, AppState, Band
from ui.widgets import Pressable, chip

TRACK_HEIGHT = 120
TRACK_WIDTH = 26
RAIL_WIDTH = 6
HANDLE_WIDTH = 18
HANDLE_HEIGHT = 10
GAIN_STEP_DB = 0.5

FC_SLIDER_MIN, FC_SLIDER_MAX = 20.0, 20000.0
Q_MIN, Q_MAX = 0.3, 6.0

_TYPE_LABELS = {"LOW_SHELF": "Low shelf", "PEAKING": "Peaking", "HIGH_SHELF": "High shelf"}


def _fc_label(fc: float) -> str:
    if fc >= 10000:
        return f"{fc / 1000:.0f}k"
    if fc >= 1000:
        return f"{fc / 1000:g}k"
    return f"{fc:.0f}"


def _fc_readout(fc: float) -> str:
    return f"{fc / 1000:.2f} kHz" if fc >= 1000 else f"{fc:.0f} Hz"


def _gain_color(gain: float) -> str:
    if gain > 0:
        return theme.GREEN_EDGE
    if gain < 0:
        return theme.CORAL_EDGE
    return theme.TEXT_TERTIARY


class _Fader(ft.GestureDetector):
    """One draggable band pill: rail + fill-from-center + handle."""

    def __init__(self, index: int, strip: "BandStripCard"):
        self.index = index
        self._strip = strip
        self._fill = ft.Container(
            width=RAIL_WIDTH, border_radius=3,
            left=(TRACK_WIDTH - RAIL_WIDTH) / 2,
        )
        self._handle = ft.Container(
            width=HANDLE_WIDTH,
            height=HANDLE_HEIGHT,
            bgcolor=theme.INK,
            border_radius=theme.RADIUS_PILL,
            left=(TRACK_WIDTH - HANDLE_WIDTH) / 2,
            shadow=theme.SHADOW_XS,
        )
        self._rail = ft.Container(
            width=RAIL_WIDTH,
            height=TRACK_HEIGHT,
            bgcolor=theme.SURFACE_ACTIVE,
            border_radius=3,
            left=(TRACK_WIDTH - RAIL_WIDTH) / 2,
            top=0,
        )
        super().__init__(
            content=ft.Stack(
                [self._rail, self._fill, self._handle],
                width=TRACK_WIDTH,
                height=TRACK_HEIGHT,
            ),
            mouse_cursor=ft.MouseCursor.RESIZE_UP_DOWN,
            on_tap_down=self._tapped,
            on_vertical_drag_start=self._drag_started,
            on_vertical_drag_update=self._dragged,
            drag_interval=16,  # ~60 fps redraw throttle (BUILD_PLAN section 6)
        )
        self.sync()

    # gain <-> pixel mapping: 0 dB at track center, +range at top.
    def _gain_to_y(self, gain: float) -> float:
        half = TRACK_HEIGHT / 2
        return half - (gain / BAND_GAIN_RANGE_DB) * half

    def _y_to_gain(self, y: float) -> float:
        half = TRACK_HEIGHT / 2
        gain = (half - y) / half * BAND_GAIN_RANGE_DB
        gain = round(gain / GAIN_STEP_DB) * GAIN_STEP_DB
        return max(min(gain, BAND_GAIN_RANGE_DB), -BAND_GAIN_RANGE_DB)

    def sync(self) -> None:
        band = self._strip.state.bands[self.index]
        y = self._gain_to_y(band.gain)
        center = TRACK_HEIGHT / 2
        self._fill.bgcolor = theme.GREEN_BLOCK if band.gain >= 0 else theme.CORAL_BLOCK
        self._fill.top = min(y, center)
        self._fill.height = max(abs(center - y), 2)
        self._handle.top = min(max(y - HANDLE_HEIGHT / 2, 0), TRACK_HEIGHT - HANDLE_HEIGHT)
        selected = self._strip.state.selected_band == self.index
        self._handle.bgcolor = theme.INK if selected else ft.Colors.with_opacity(0.75, theme.INK)

    def _set_gain_from_y(self, y: float) -> None:
        band = self._strip.state.bands[self.index]
        gain = self._y_to_gain(y)
        if gain != band.gain:
            band.gain = gain
            self._strip.select_band(self.index, notify=True)

    def _tapped(self, e: ft.TapEvent):
        self._set_gain_from_y(e.local_position.y)
        self._strip.select_band(self.index, notify=True)

    def _drag_started(self, e):
        self._strip.select_band(self.index, notify=False)

    def _dragged(self, e: ft.DragUpdateEvent):
        self._set_gain_from_y(e.local_position.y)


class BandStripCard(ft.Container):
    def __init__(self, state: AppState, on_bands_changed, on_auto_fit, on_reset):
        self.state = state
        self._on_bands_changed = on_bands_changed
        self._faders = [_Fader(i, self) for i in range(len(state.bands))]
        self._detail_holder = ft.Container()

        fader_row = ft.Row(
            [
                ft.Column(
                    [
                        fader,
                        ft.Text(_fc_label(state.bands[i].fc), style=theme.mono(size=8.5)),
                    ],
                    spacing=6,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    expand=True,
                )
                for i, fader in enumerate(self._faders)
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.END,
        )

        header = ft.Row(
            [
                ft.Text(
                    "10-BAND PARAMETRIC EQ",
                    style=theme.mono(size=11, color=theme.TEXT_SECONDARY, letter_spacing=0.08),
                ),
                ft.Row(
                    [
                        chip("Auto-fit", border_color=theme.GREEN_EDGE, on_click=on_auto_fit),
                        chip("Reset", on_click=on_reset),
                    ],
                    spacing=8,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        super().__init__(
            content=ft.Column(
                [header, fader_row, self._detail_holder],
                spacing=16,
            ),
            bgcolor=ft.Colors.WHITE,
            border_radius=theme.RADIUS_CARD,
            shadow=theme.SHADOW_SM,
            padding=ft.Padding(left=20, right=20, top=16, bottom=16),
        )
        self._refresh_detail()

    # -- selection / updates -------------------------------------------------

    def select_band(self, index: int, notify: bool) -> None:
        self.state.selected_band = index
        self.refresh()
        if self.page:
            self.update()
        if notify:
            self._on_bands_changed()

    def refresh(self) -> None:
        for fader in self._faders:
            fader.sync()
        self._refresh_detail()

    # -- detail row ------------------------------------------------------------

    def _refresh_detail(self) -> None:
        index = self.state.selected_band
        if index is None:
            self._detail_holder.content = ft.Container(
                content=ft.Text(
                    "Select a band to edit its frequency and width.",
                    style=theme.sans(size=12.5, weight=ft.FontWeight.W_400, color=theme.TEXT_TERTIARY),
                ),
                padding=ft.Padding(left=0, right=0, top=6, bottom=2),
            )
            return
        band = self.state.bands[index]
        self._detail_holder.content = ft.Container(
            content=ft.Row(
                [
                    ft.Column(
                        [
                            ft.Text(
                                f"BAND {index + 1:02d} · {_TYPE_LABELS[band.type]}",
                                style=theme.mono(size=10.5),
                            ),
                            ft.Text(_fc_readout(band.fc), style=theme.serif(size=20)),
                        ],
                        spacing=2,
                        width=150,
                    ),
                    self._labeled_slider(
                        "FREQUENCY",
                        value=self._fc_to_pct(band.fc),
                        on_change=self._fc_changed(band),
                    ),
                    self._labeled_slider(
                        "Q / WIDTH",
                        value=(band.q - Q_MIN) / (Q_MAX - Q_MIN) * 100,
                        on_change=self._q_changed(band),
                        readout=f"{band.q:.2f}",
                    ),
                    ft.Text(
                        f"{band.gain:+.1f} dB" if band.gain else "0.0 dB",
                        style=theme.mono(size=18, color=_gain_color(band.gain)),
                        text_align=ft.TextAlign.RIGHT,
                        width=90,
                    ),
                ],
                spacing=18,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            border=ft.Border(top=ft.BorderSide(1, theme.BORDER_SUBTLE)),
            padding=ft.Padding(left=0, right=0, top=12, bottom=0),
        )

    def _labeled_slider(self, label: str, value: float, on_change, readout: str | None = None) -> ft.Control:
        title = ft.Row(
            [ft.Text(label, style=theme.mono(size=9.5))],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )
        if readout:
            title.controls.append(ft.Text(readout, style=theme.mono(size=9.5, color=theme.TEXT_SECONDARY)))
        return ft.Column(
            [
                title,
                ft.Slider(
                    min=0,
                    max=100,
                    value=max(0.0, min(100.0, value)),
                    on_change=on_change,
                    active_color=theme.INK,
                    inactive_color=theme.BORDER_DEFAULT,
                    thumb_color=theme.INK,
                ),
            ],
            spacing=0,
            expand=True,
        )

    @staticmethod
    def _fc_to_pct(fc: float) -> float:
        span = math.log10(FC_SLIDER_MAX) - math.log10(FC_SLIDER_MIN)
        return (math.log10(fc) - math.log10(FC_SLIDER_MIN)) / span * 100

    def _fc_changed(self, band: Band):
        def handler(e):
            span = math.log10(FC_SLIDER_MAX) - math.log10(FC_SLIDER_MIN)
            band.fc = round(10 ** (math.log10(FC_SLIDER_MIN) + e.control.value / 100 * span), 1)
            self._refresh_detail()
            self.update()
            self._on_bands_changed()
        return handler

    def _q_changed(self, band: Band):
        def handler(e):
            band.q = round(Q_MIN + e.control.value / 100 * (Q_MAX - Q_MIN), 2)
            self._refresh_detail()
            self.update()
            self._on_bands_changed()
        return handler
