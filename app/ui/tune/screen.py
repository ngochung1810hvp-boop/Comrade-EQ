"""Screen 3 — Tune.

Placeholder for GD0: the full workspace (graph, 10-band strip, export bar,
DAC panel, chat drawer) is BUILD_PLAN.md phases GD2-GD4. This stub only
makes the screen reachable so routing can be exercised end-to-end.
"""

import flet as ft

import theme
from ui.widgets import Pressable


def tune_screen(state, on_back_to_welcome) -> ft.Control:
    rail = ft.Container(
        width=66,
        bgcolor=theme.SURFACE_SUNKEN,
        content=ft.Column(
            [
                ft.Container(
                    width=42,
                    height=42,
                    border_radius=10,
                    bgcolor=theme.SURFACE_ACTIVE,
                    alignment=ft.Alignment.CENTER,
                    content=ft.Icon(ft.Icons.TUNE, size=18, color=theme.INK),
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=ft.Padding(top=16, left=0, right=0, bottom=16),
    )
    main = ft.Container(
        content=ft.Column(
            [
                Pressable(
                    ft.Row(
                        [
                            ft.Icon(ft.Icons.ARROW_BACK, size=14, color=theme.TEXT_TERTIARY),
                            ft.Text("BACK TO WELCOME", style=theme.mono(size=11, letter_spacing=0.06)),
                        ],
                        spacing=6,
                        tight=True,
                    ),
                    on_press=on_back_to_welcome,
                ),
                ft.Container(height=16),
                ft.Text(
                    state.headphone.name if state.headphone else "No headphone selected",
                    style=theme.serif(size=27),
                ),
                ft.Container(height=8),
                ft.Text(
                    "Graph, 10-band strip, export bar, DAC panel land in phase GD2.",
                    style=theme.sans(size=13.5, color=theme.TEXT_SECONDARY),
                ),
            ],
            spacing=0,
        ),
        padding=24,
        expand=True,
    )
    dac_panel = ft.Container(width=296, bgcolor=theme.SURFACE_SUNKEN)
    return ft.Container(
        content=ft.Row([rail, main, dac_panel], spacing=0, expand=True),
        expand=True,
        bgcolor=theme.PAPER,
    )
