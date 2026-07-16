"""DAC side panel, 296px sunken column (BUILD_PLAN.md GD2.5).

Handoff spec: "OUTPUT · DAC" label, a device-picker button (36x36 icon chip
+ name/type) opening a dropdown of devices (rate + selection dot), and a
3-up stat row: SAMPLE rate, bit DEPTH, EXCLUSIVE status. Depth/exclusive
render "—" (read-only best-effort per BUILD_PLAN section 2.5).
"""

import flet as ft

import theme
from state import AppState
from ui.widgets import Pressable


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
    def __init__(self, state: AppState, devices, on_device_changed):
        self._state = state
        self._devices = devices
        self._on_device_changed = on_device_changed
        self._picker_holder = ft.Container()
        self._menu_holder = ft.Container()
        self._stats_holder = ft.Container()

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
