"""Export bar card (BUILD_PLAN.md GD2.4).

Handoff spec: single card row — "EXPORT" mono label, 4 selectable app-target
chips (selected = ink border), right-aligned auto-computed PREAMP readout,
and a primary green Export button that triggers a toast.
"""

import flet as ft

import theme
from exporters import EXPORT_FORMATS
from state import AppState
from ui.widgets import Pressable, chip


class ExportBar(ft.Container):
    def __init__(self, state: AppState, get_preamp, on_export):
        self._state = state
        self._get_preamp = get_preamp
        self._chips_row = ft.Row(spacing=8, wrap=True)
        self._preamp_text = ft.Text(style=theme.mono(size=12, color=theme.TEXT_PRIMARY))

        if state.eq_app not in EXPORT_FORMATS:
            state.eq_app = next(iter(EXPORT_FORMATS))

        export_button = Pressable(
            ft.Container(
                content=ft.Text("Export", style=theme.sans(size=13.5)),
                height=34,
                padding=ft.Padding(left=18, right=18, top=0, bottom=0),
                bgcolor=theme.GREEN_BLOCK,
                border_radius=theme.RADIUS_BUTTON_SM,
                alignment=ft.Alignment.CENTER,
                shadow=theme.SHADOW_XS,
            ),
            on_press=on_export,
        )

        super().__init__(
            content=ft.Row(
                [
                    ft.Text(
                        "EXPORT",
                        style=theme.mono(size=11, color=theme.TEXT_SECONDARY, letter_spacing=0.08),
                    ),
                    ft.Container(content=self._chips_row, expand=True),
                    ft.Column(
                        [
                            ft.Text("PREAMP", style=theme.mono(size=9.5)),
                            self._preamp_text,
                        ],
                        spacing=1,
                        horizontal_alignment=ft.CrossAxisAlignment.END,
                    ),
                    export_button,
                ],
                spacing=16,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=ft.Colors.WHITE,
            border_radius=theme.RADIUS_CARD,
            shadow=theme.SHADOW_SM,
            padding=ft.Padding(left=20, right=16, top=12, bottom=12),
        )
        self.refresh()

    def refresh(self) -> None:
        self._chips_row.controls = [
            chip(name, selected=self._state.eq_app == name, on_click=self._select(name))
            for name in EXPORT_FORMATS
        ]
        self._preamp_text.value = f"{self._get_preamp():.1f} dB"

    def _select(self, name: str):
        def handler(e):
            self._state.eq_app = name
            self.refresh()
            self.update()
        return handler
