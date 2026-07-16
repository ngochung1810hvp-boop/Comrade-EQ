"""Screen 2 — Device Setup (BUILD_PLAN.md GD1).

Recreates handoff README section 2 / prototype lines 83-146: header with
back button + step eyebrow + serif H2, a 2-column grid (headphone search
list | output device list + callout), and a sticky footer with the pairing
summary and the "Start tuning" button.
"""

import flet as ft

import theme
from headphone_index import HeadphoneEntry, search
from ui.widgets import Pressable

SEARCH_LIMIT = 100

WHY_IT_MATTERS = (
    "Studio applies correction before your DAC, and auto-sets preamp "
    "to prevent clipping at high sample rates."
)


def _check_badge(selected: bool) -> ft.Control:
    return ft.Container(
        width=22,
        height=22,
        border_radius=theme.RADIUS_PILL,
        bgcolor=theme.INK if selected else "transparent",
        border=None if selected else ft.Border.all(1.5, theme.BORDER_STRONG),
        alignment=ft.Alignment.CENTER,
        content=ft.Icon(ft.Icons.CHECK, size=13, color=theme.PAPER) if selected else None,
    )


def _row_container(content: ft.Control, selected: bool, on_click) -> ft.Control:
    return Pressable(
        ft.Container(
            content=content,
            bgcolor=theme.PAPER,
            border=ft.Border.all(1, theme.INK if selected else theme.BORDER_SUBTLE),
            border_radius=10,
            padding=ft.Padding(left=14, right=14, top=10, bottom=10),
            shadow=theme.SHADOW_SM if selected else theme.SHADOW_XS,
        ),
        on_press=on_click,
    )


def _headphone_row(entry: HeadphoneEntry, selected: bool, on_click) -> ft.Control:
    return _row_container(
        ft.Row(
            [
                ft.Column(
                    [
                        ft.Text(entry.name, style=theme.sans(size=14)),
                        ft.Text(entry.meta, style=theme.mono(size=11)),
                    ],
                    spacing=2,
                    expand=True,
                ),
                _check_badge(selected),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        selected,
        on_click,
    )


def _device_row(device, selected: bool, on_click) -> ft.Control:
    return _row_container(
        ft.Row(
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
                        ft.Text(device.name, style=theme.sans(size=14)),
                        ft.Text(device.meta, style=theme.mono(size=11)),
                    ],
                    spacing=2,
                    expand=True,
                ),
                _check_badge(selected),
            ],
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        selected,
        on_click,
    )


def _callout() -> ft.Control:
    return ft.Container(
        margin=ft.Margin(top=6, left=0, right=0, bottom=0),
        padding=14,
        border=ft.Border.all(1, theme.BORDER_DEFAULT),
        border_radius=10,
        bgcolor=theme.SURFACE_SUNKEN,
        content=ft.Column(
            [
                ft.Text("WHY IT MATTERS", style=theme.mono(size=10.5, color=theme.CORAL_EDGE)),
                ft.Text(
                    WHY_IT_MATTERS,
                    style=theme.sans(size=12.5, weight=ft.FontWeight.W_400, color=theme.TEXT_SECONDARY, height=1.5),
                ),
            ],
            spacing=5,
        ),
    )


def device_setup_screen(state, entries: list[HeadphoneEntry], devices, on_back, on_start_tuning) -> ft.Control:
    hp_list = ft.ListView(spacing=6, expand=True)
    device_list = ft.Column(spacing=8, expand=False)
    pairing_text = ft.Text("", style=theme.sans(size=13, color=theme.TEXT_SECONDARY))
    start_button_holder = ft.Container()

    def refresh_headphones() -> None:
        results = search(entries, state.hp_query, limit=SEARCH_LIMIT)
        hp_list.controls = [
            _headphone_row(e, e == state.headphone, _select_headphone(e)) for e in results
        ]

    def refresh_devices() -> None:
        device_list.controls = [
            _device_row(d, d == state.device, _select_device(d)) for d in devices
        ] + [_callout()]

    def refresh_footer() -> None:
        hp = state.headphone.name if state.headphone else "Choose headphones"
        dev = state.device.name if state.device else "choose an output device"
        pairing_text.value = f"{hp} → {dev}"
        ready = state.headphone is not None and state.device is not None
        start_button_holder.content = _start_button(ready)

    def _select_headphone(entry):
        def handler(e):
            state.headphone = entry
            refresh_headphones()
            refresh_footer()
            hp_list.update()
            pairing_text.update()
            start_button_holder.update()
        return handler

    def _select_device(device):
        def handler(e):
            state.device = device
            refresh_devices()
            refresh_footer()
            device_list.update()
            pairing_text.update()
            start_button_holder.update()
        return handler

    def _on_query(e):
        state.hp_query = e.control.value
        refresh_headphones()
        hp_list.update()

    def _start_button(enabled: bool) -> ft.Control:
        button = ft.Container(
            content=ft.Row(
                [
                    ft.Text("Start tuning", style=theme.sans(size=15, color=theme.PAPER)),
                    ft.Icon(ft.Icons.ARROW_FORWARD, size=17, color=theme.PAPER),
                ],
                spacing=9,
                tight=True,
            ),
            height=42,
            padding=ft.Padding(left=22, right=22, top=0, bottom=0),
            bgcolor=theme.INK,
            border_radius=theme.RADIUS_BUTTON,
            alignment=ft.Alignment.CENTER,
            opacity=1.0 if enabled else 0.35,
        )
        if not enabled:
            return button
        return Pressable(button, on_press=on_start_tuning)

    search_field = ft.Container(
        height=40,
        padding=ft.Padding(left=13, right=13, top=0, bottom=0),
        border=ft.Border.all(1, theme.BORDER_DEFAULT),
        border_radius=8,
        bgcolor=theme.PAPER,
        shadow=theme.SHADOW_XS,
        content=ft.Row(
            [
                ft.Icon(ft.Icons.SEARCH, size=16, color=theme.TEXT_TERTIARY),
                ft.TextField(
                    value=state.hp_query,
                    hint_text="Search Sennheiser, Focal, HIFIMAN…",
                    border=ft.InputBorder.NONE,
                    text_style=theme.sans(size=14, weight=ft.FontWeight.W_400),
                    hint_style=theme.sans(size=14, weight=ft.FontWeight.W_400, color=theme.TEXT_TERTIARY),
                    on_change=_on_query,
                    expand=True,
                    content_padding=ft.Padding(left=0, right=0, top=8, bottom=8),
                ),
            ],
            spacing=9,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )

    left_column = ft.Column(
        [
            ft.Row(
                [
                    ft.Text("HEADPHONES", style=theme.mono(size=11, color=theme.TEXT_SECONDARY, letter_spacing=0.08)),
                    ft.Text(f"{len(entries):,}+ measured", style=theme.mono(size=11)),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            search_field,
            hp_list,
        ],
        spacing=12,
        expand=True,
    )

    right_column = ft.Column(
        [
            ft.Text("OUTPUT DEVICE · DAC", style=theme.mono(size=11, color=theme.TEXT_SECONDARY, letter_spacing=0.08)),
            ft.Column([device_list], scroll=ft.ScrollMode.AUTO, expand=True),
        ],
        spacing=12,
        expand=True,
    )

    back_button = Pressable(
        ft.Row(
            [
                ft.Icon(ft.Icons.ARROW_BACK, size=14, color=theme.TEXT_TERTIARY),
                ft.Text("BACK", style=theme.mono(size=11, letter_spacing=0.06)),
            ],
            spacing=6,
            tight=True,
        ),
        on_press=on_back,
    )

    header = ft.Column(
        [
            back_button,
            ft.Container(height=14),
            ft.Text("STEP 1 / 2 · SET UP YOUR RIG", style=theme.mono(size=11, letter_spacing=0.12)),
            ft.Container(height=8),
            ft.Text("What are you listening on?", style=theme.serif(size=34, letter_spacing=-0.02)),
        ],
        spacing=0,
    )

    footer = ft.Row(
        [pairing_text, start_button_holder],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    refresh_headphones()
    refresh_devices()
    refresh_footer()

    return ft.Container(
        content=ft.Column(
            [
                ft.Container(content=header, padding=ft.Padding(left=44, right=44, top=30, bottom=20)),
                ft.Container(
                    content=ft.Row([left_column, right_column], spacing=24, expand=True),
                    padding=ft.Padding(left=44, right=44, top=0, bottom=20),
                    expand=True,
                ),
                ft.Container(
                    content=footer,
                    padding=ft.Padding(left=44, right=44, top=16, bottom=16),
                    border=ft.Border(top=ft.BorderSide(1, theme.BORDER_SUBTLE)),
                ),
            ],
            spacing=0,
            expand=True,
        ),
        expand=True,
        bgcolor=theme.PAPER,
    )
