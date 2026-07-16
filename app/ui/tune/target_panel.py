"""Target section — lives in the right side panel, below the DAC block.

Target selection used to be a floating dropdown anchored in a Stack, which
mis-rendered. With 61 targets a dropdown was the wrong form anyway: this
section keeps the list visible and scrollable, with a search box to narrow
it, and no overlay. The parent side column owns width/background/border.
"""

import flet as ft

import theme
from state import AppState
from ui.widgets import Pressable


class TargetPanel(ft.Container):
    def __init__(self, state: AppState, targets: list[str], on_target_changed):
        self._state = state
        self._targets = targets
        self._on_target_changed = on_target_changed
        self._list_holder = ft.Container(expand=True)
        self._count_label = ft.Text("", style=theme.mono(size=9.5))
        self._search = ft.TextField(
            value=state.target_query,
            hint_text="Search targets",
            hint_style=theme.sans(size=13, color=theme.TEXT_TERTIARY),
            text_style=theme.sans(size=13),
            prefix_icon=ft.Icons.SEARCH,
            border_radius=10,
            filled=True,
            fill_color=ft.Colors.WHITE,
            border_color=theme.BORDER_SUBTLE,
            focused_border_color=theme.BORDER_STRONG,
            content_padding=ft.Padding(left=10, right=10, top=8, bottom=8),
            dense=True,
            on_change=self._query_changed,
        )

        super().__init__(
            expand=True,
            border=ft.Border(top=ft.BorderSide(1, theme.BORDER_SUBTLE)),
            padding=ft.Padding(left=18, right=18, top=16, bottom=22),
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Text(
                                "TARGET",
                                style=theme.mono(
                                    size=11,
                                    color=theme.TEXT_SECONDARY,
                                    letter_spacing=0.08,
                                ),
                            ),
                            ft.Container(expand=True),
                            self._count_label,
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    self._search,
                    self._list_holder,
                ],
                spacing=12,
                expand=True,
            ),
        )
        self.refresh()

    def _visible_targets(self) -> list[str]:
        query = self._state.target_query.strip().lower()
        if not query:
            return self._targets
        return [name for name in self._targets if query in name.lower()]

    def refresh(self) -> None:
        names = self._visible_targets()
        self._count_label.value = str(len(names))
        if not names:
            self._list_holder.content = ft.Text(
                "No target matches that search.",
                style=theme.sans(size=12.5, color=theme.TEXT_TERTIARY),
            )
            return
        self._list_holder.content = ft.Column(
            [self._row(name) for name in names],
            spacing=2,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    def _row(self, name: str) -> ft.Control:
        selected = name == self._state.target
        return Pressable(
            ft.Container(
                content=ft.Row(
                    [
                        ft.Text(
                            name,
                            style=theme.sans(size=13),
                            expand=True,
                            max_lines=2,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                        ft.Icon(ft.Icons.CHECK, size=13, color=theme.INK)
                        if selected
                        else ft.Container(width=13),
                    ],
                    spacing=6,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                bgcolor=ft.Colors.WHITE if selected else "transparent",
                border=ft.Border.all(1, theme.INK if selected else "transparent"),
                border_radius=8,
                padding=ft.Padding(left=10, right=10, top=7, bottom=7),
            ),
            on_press=self._select(name),
        )

    def _query_changed(self, e) -> None:
        self._state.target_query = e.control.value
        self.refresh()
        self.update()

    def _select(self, name: str):
        def handler(e):
            self._on_target_changed(name)
            self.refresh()
            self.update()

        return handler
