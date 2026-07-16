"""DAC side panel, 296px sunken column (BUILD_PLAN.md GD2.5).

Handoff spec: "OUTPUT · DAC" label, a device-picker button (36x36 icon chip
+ name/type) opening a dropdown of devices (rate + selection dot), and a
3-up stat row: SAMPLE rate, bit DEPTH, EXCLUSIVE status. Depth/exclusive
render "—" (read-only best-effort per BUILD_PLAN section 2.5).
"""

import random
import threading

import flet as ft

import ab_preview
import theme
from profile_store import ProfileStore
from state import AppState
from ui.widgets import Pressable, pill_toggle


def _stat_cell(label: str, value: str, *, chip_style: bool = False) -> ft.Control:
    value_control = ft.Text(value, style=theme.mono(size=13, color=theme.TEXT_PRIMARY))
    if chip_style:
        value_control = ft.Container(
            content=ft.Text(value, style=theme.mono(size=10.5, color=theme.TEXT_PRIMARY)),
            bgcolor=theme.SURFACE_ACTIVE,
            border_radius=theme.RADIUS_PILL,
            padding=ft.Padding(left=10, right=10, top=3, bottom=3),
        )
    return ft.Container(
        content=ft.Column(
            [
                ft.Text(label, style=theme.mono(size=9.5)),
                value_control,
            ],
            spacing=6,
            horizontal_alignment=ft.CrossAxisAlignment.START,
        ),
        bgcolor=ft.Colors.WHITE,
        border_radius=10,
        padding=ft.Padding(left=12, right=12, top=10, bottom=10),
        shadow=theme.SHADOW_XS,
        expand=True,
    )


class DacPanel(ft.Container):
    def __init__(self, state: AppState, devices, on_device_changed, get_preamp=None):
        self._state = state
        self._devices = devices
        self._on_device_changed = on_device_changed
        self._get_preamp = get_preamp or (lambda: 0.0)
        self._picker_holder = ft.Container()
        self._menu_holder = ft.Container()
        self._stats_holder = ft.Container()
        self._preview_holder = ft.Container()
        self._player = ab_preview.ABPlayer()
        self._preparing = False
        # GD5 blind test: {"eq_is_x": bool, "current": "X"|"Y", "result": str|None}
        self._blind: dict | None = None

        super().__init__(
            width=296,
            bgcolor=theme.SURFACE_SUNKEN,
            border=ft.Border(left=ft.BorderSide(1, theme.BORDER_SUBTLE)),
            padding=ft.Padding(left=18, right=18, top=22, bottom=22),
            content=ft.Column(
                [
                    ft.Text(
                        "OUTPUT · DAC",
                        style=theme.mono(size=11, color=theme.TEXT_SECONDARY, letter_spacing=0.08),
                    ),
                    ft.Stack([ft.Column([self._picker_holder]), self._menu_holder]),
                    self._stats_holder,
                    self._preview_holder,
                ],
                spacing=14,
            ),
        )
        self.refresh()

    def refresh(self) -> None:
        device = self._state.device
        name = device.name if device else "No output device"
        meta = device.meta if device else "Select a device"
        self._picker_holder.content = Pressable(
            ft.Container(
                content=ft.Row(
                    [
                        ft.Container(
                            width=36,
                            height=36,
                            border_radius=8,
                            bgcolor=theme.SURFACE_ACTIVE,
                            alignment=ft.Alignment.CENTER,
                            content=ft.Icon(ft.Icons.SPEAKER_OUTLINED, size=19, color=theme.INK),
                        ),
                        ft.Column(
                            [
                                ft.Text(name, style=theme.sans(size=13.5), max_lines=1,
                                        overflow=ft.TextOverflow.ELLIPSIS),
                                ft.Text(meta, style=theme.mono(size=10.5)),
                            ],
                            spacing=2,
                            expand=True,
                        ),
                        ft.Icon(
                            ft.Icons.KEYBOARD_ARROW_DOWN if not self._state.out_menu
                            else ft.Icons.KEYBOARD_ARROW_UP,
                            size=16,
                            color=theme.TEXT_TERTIARY,
                        ),
                    ],
                    spacing=10,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                bgcolor=ft.Colors.WHITE,
                border=ft.Border.all(1, theme.BORDER_SUBTLE),
                border_radius=10,
                padding=ft.Padding(left=10, right=10, top=8, bottom=8),
                shadow=theme.SHADOW_XS,
            ),
            on_press=self._toggle_menu,
        )
        self._menu_holder.content = self._build_menu() if self._state.out_menu else None

        sample = f"{device.sample_rate / 1000:g}k" if device else "—"
        self._stats_holder.content = ft.Row(
            [
                _stat_cell("SAMPLE", sample),
                _stat_cell("DEPTH", "—"),
                _stat_cell("EXCLUSIVE", "—", chip_style=True),
            ],
            spacing=8,
        )
        self._preview_holder.content = self._build_preview()

    def _build_preview(self) -> ft.Control:
        """GD4.5 A/B listen: pink noise convolved with the current EQ FIR."""
        playing = self._player.playing
        if self._preparing:
            play_label, play_icon = "Preparing…", ft.Icons.HOURGLASS_EMPTY
        elif playing:
            play_label, play_icon = "Stop", ft.Icons.STOP
        else:
            play_label, play_icon = "Play", ft.Icons.PLAY_ARROW
        play_button = Pressable(
            ft.Container(
                content=ft.Row(
                    [
                        ft.Icon(play_icon, size=14,
                                color=theme.PAPER if playing else theme.INK),
                        ft.Text(play_label, style=theme.sans(
                            size=12.5,
                            color=theme.PAPER if playing else theme.INK)),
                    ],
                    spacing=6,
                    tight=True,
                ),
                bgcolor=theme.INK if playing else ft.Colors.WHITE,
                border=None if playing else ft.Border.all(1, theme.BORDER_DEFAULT),
                border_radius=theme.RADIUS_BUTTON_SM,
                padding=ft.Padding(left=12, right=14, top=7, bottom=7),
                shadow=theme.SHADOW_XS,
            ),
            on_press=self._toggle_play,
        )
        if self._blind is not None:
            current = self._blind["current"]
            ab_row = ft.Row(
                [
                    ft.Text("X", style=theme.mono(
                        size=10.5, color=theme.INK if current == "X"
                        else theme.TEXT_TERTIARY)),
                    pill_toggle(current == "Y", on_change=self._blind_flip),
                    ft.Text("Y", style=theme.mono(
                        size=10.5, color=theme.INK if current == "Y"
                        else theme.TEXT_TERTIARY)),
                ],
                spacing=6, tight=True,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )
        else:
            ab_row = ft.Row(
                [
                    ft.Text("A", style=theme.mono(size=10.5)),
                    pill_toggle(self._player.eq_on, on_change=self._set_ab),
                    ft.Text("B·EQ", style=theme.mono(size=10.5)),
                ],
                spacing=6, tight=True,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )

        rows: list[ft.Control] = [
            ft.Row(
                [
                    ft.Text("PREVIEW · A/B", style=theme.mono(size=9.5)),
                    ft.Container(expand=True),
                    Pressable(
                        ft.Container(
                            content=ft.Text(
                                "exit blind" if self._blind is not None else "blind test",
                                style=theme.mono(size=9.5, color=theme.INK),
                            ),
                            border=ft.Border.all(1, theme.BORDER_DEFAULT),
                            border_radius=theme.RADIUS_PILL,
                            padding=ft.Padding(left=10, right=10, top=4, bottom=4),
                        ),
                        on_press=self._toggle_blind,
                    ),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            ft.Row(
                [play_button, ft.Container(expand=True), ab_row],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        ]
        if self._blind is not None:
            guess = [
                ft.Text("WHICH HAS EQ?", style=theme.mono(size=9.5)),
                ft.Container(expand=True),
            ]
            for choice in ("X", "Y"):
                guess.append(
                    Pressable(
                        ft.Container(
                            content=ft.Text(choice, style=theme.mono(
                                size=10.5, color=theme.INK)),
                            border=ft.Border.all(1, theme.BORDER_DEFAULT),
                            border_radius=theme.RADIUS_PILL,
                            padding=ft.Padding(left=12, right=12, top=4, bottom=4),
                        ),
                        on_press=(lambda c: lambda e: self._blind_guess(c))(choice),
                    )
                )
            rows.append(ft.Row(guess, spacing=6,
                               vertical_alignment=ft.CrossAxisAlignment.CENTER))
            if self._blind.get("result"):
                rows.append(ft.Text(self._blind["result"], style=theme.sans(
                    size=12, weight=ft.FontWeight.W_400,
                    color=theme.TEXT_SECONDARY)))

        return ft.Container(
            content=ft.Column(rows, spacing=8, tight=True),
            bgcolor=ft.Colors.WHITE,
            border_radius=10,
            padding=ft.Padding(left=12, right=12, top=10, bottom=10),
            shadow=theme.SHADOW_XS,
        )

    def _toggle_play(self, e=None) -> None:
        if self._preparing:
            return
        if self._player.playing:
            self._player.stop()
            self.refresh()
            self.update()
            return
        self._preparing = True
        self.refresh()
        self.update()

        def worker():
            try:
                self._player.prepare(self._state.bands, self._get_preamp())
                blind = self._blind
                self._player.set_eq(True if blind is None else blind["eq_is_x"])
                self._player.start()
            except Exception:
                pass  # no audio device / portaudio missing: stay stopped
            self._preparing = False
            self.refresh()
            try:
                self.update()
            except Exception:
                pass  # page may have navigated away meanwhile

        threading.Thread(target=worker, daemon=True).start()

    def _set_ab(self, value: bool) -> None:
        self._player.set_eq(value)
        self.refresh()
        self.update()

    # -- GD5 blind A/B test: anti-placebo, high-quality weight signal ------

    def _toggle_blind(self, e=None) -> None:
        if self._blind is not None:
            self._blind = None
            self._player.set_eq(True)
        else:
            self._blind = {"eq_is_x": random.random() < 0.5, "current": "X",
                           "result": None}
            self._player.set_eq(self._blind["eq_is_x"])
            if not self._player.playing:
                self._toggle_play()
                return  # _toggle_play refreshes when ready
        self.refresh()
        self.update()

    def _blind_flip(self, to_y: bool) -> None:
        if self._blind is None:
            return
        self._blind["current"] = "Y" if to_y else "X"
        is_eq = self._blind["eq_is_x"] == (self._blind["current"] == "X")
        self._player.set_eq(is_eq)
        self.refresh()
        self.update()

    def _blind_guess(self, choice: str) -> None:
        if self._blind is None:
            return
        eq_side = "X" if self._blind["eq_is_x"] else "Y"
        correct = choice == eq_side
        self._blind["result"] = (
            f"Correct — {eq_side} had your EQ. That difference is real."
            if correct
            else f"Not this time — {eq_side} had the EQ. Maybe soften the change?"
        )
        # High-quality signal for the learning loop (AI_ROADMAP GD4).
        profile = self._state.profile
        if profile is not None:
            profile.record_history(action="blind_ab", guess=choice,
                                   eq_side=eq_side, correct=correct)
            try:
                ProfileStore().save(profile)
            except OSError:
                pass
        self.refresh()
        self.update()

    def _build_menu(self) -> ft.Control:
        rows = []
        for device in self._devices:
            selected = device == self._state.device
            rows.append(
                Pressable(
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Column(
                                    [
                                        ft.Text(device.name, style=theme.sans(size=13),
                                                max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                                        ft.Text(device.meta, style=theme.mono(size=10)),
                                    ],
                                    spacing=1,
                                    expand=True,
                                ),
                                ft.Container(
                                    width=8,
                                    height=8,
                                    border_radius=theme.RADIUS_PILL,
                                    bgcolor=theme.GREEN_EDGE if selected else "transparent",
                                    border=None if selected else ft.Border.all(1, theme.BORDER_STRONG),
                                ),
                            ],
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        bgcolor=theme.SURFACE_ACTIVE if selected else "transparent",
                        border_radius=8,
                        padding=ft.Padding(left=10, right=10, top=8, bottom=8),
                    ),
                    on_press=self._select(device),
                )
            )
        return ft.Container(
            content=ft.Column(rows, spacing=2, tight=True, scroll=ft.ScrollMode.AUTO),
            bgcolor=theme.PAPER,
            border=ft.Border.all(1, theme.BORDER_SUBTLE),
            border_radius=theme.RADIUS_CARD,
            shadow=theme.SHADOW_LG,
            padding=6,
            top=58,
            left=0,
            right=0,
        )

    def _toggle_menu(self, e=None) -> None:
        self._state.out_menu = not self._state.out_menu
        self.refresh()
        self.update()

    def _select(self, device):
        def handler(e):
            self._state.device = device
            self._state.out_menu = False
            self.refresh()
            self.update()
            self._on_device_changed()
        return handler
