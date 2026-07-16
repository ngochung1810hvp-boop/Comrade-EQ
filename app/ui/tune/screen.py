"""Screen 3 — Tune (BUILD_PLAN.md GD2).

Layout per handoff: 66px icon rail | scrollable main column (header, graph
card, 10-band card, export bar) | 296px DAC side panel. The chat drawer is
GD4 scope and not mounted yet.
"""

import flet as ft

import eq_model
import theme
from equalize import Options, compute, list_targets
from exporters import export_file
from state import AppState
from ui.settings_modal import open_settings_modal
from ui.tune.band_strip import BandStripCard
from ui.tune.chat_drawer import chat_overlay
from ui.tune.dac_panel import DacPanel
from ui.tune.profiles_modal import open_profiles_modal
from ui.tune.export_bar import ExportBar
from ui.tune.graph import GraphCard
from ui.tune.save_modal import open_save_modal
from ui.widgets import Pressable, pill_toggle, show_toast

TARGET_MENU_WIDTH = 320
TARGET_MENU_HEIGHT = 340


def _default_target(form: str, targets: list[str]) -> str:
    preferred = (
        "Harman in-ear 2019" if form in ("in-ear", "earbud") else "Harman over-ear 2018"
    )
    return preferred if preferred in targets else targets[0]


def _ensure_fr(state: AppState, targets: list[str]) -> None:
    """Computes/caches the processed FrequencyResponse for headphone+target.

    GD3: when the taste toggle is on, the active profile's preference curve
    rides along as sound_signature (AI_ROADMAP Layer 3 wiring).
    """
    if state.headphone is None:
        state.fr = None
        state.fr_key = None
        return
    if state.target not in targets:
        state.target = _default_target(state.headphone.form, targets)
    signature = None
    if state.taste_on and state.profile is not None:
        signature = state.profile.as_sound_signature(state.headphone.name)
    key = (
        state.headphone.path,
        state.target,
        state.profile.updated_at if signature is not None else None,
    )
    if state.fr_key == key and state.fr is not None:
        return
    state.fr = compute(
        state.headphone.path, state.target, Options(sound_signature=signature)
    )
    state.fr_key = key


def _rail_button(icon, active: bool, on_press=None) -> ft.Control:
    button = ft.Container(
        width=42,
        height=42,
        border_radius=10,
        bgcolor=theme.SURFACE_ACTIVE if active else "transparent",
        alignment=ft.Alignment.CENTER,
        content=ft.Icon(icon, size=18, color=theme.INK if active else theme.TEXT_TERTIARY),
    )
    if on_press is None:
        return button
    return Pressable(button, on_press=on_press, press_scale=theme.PRESS_SCALE_ICON)


def tune_screen(page: ft.Page, state: AppState, devices, on_devices) -> ft.Control:
    targets = list_targets()
    _ensure_fr(state, targets)

    def toast(text: str) -> None:
        page.run_task(show_toast, page, text)

    # -- shared derived data --------------------------------------------------

    def get_curves():
        fr = state.fr
        if fr is None:
            return None
        measured = fr.smoothed if state.smoothed and len(fr.smoothed) else fr.raw
        eq = eq_model.eq_curve(state.bands, fr.frequency) if state.eq_on else None
        return {
            "f": fr.frequency,
            "measured": measured,
            "target": fr.target if len(fr.target) else None,
            "eq": eq,
            "result": measured + eq if eq is not None else measured,
        }

    def get_preamp() -> float:
        if state.fr is None or not state.eq_on:
            return 0.0
        return eq_model.preamp_db(state.bands, state.fr.frequency)

    # -- cards ------------------------------------------------------------

    def bands_changed():
        graph.refresh()
        export_bar.refresh()
        if graph.page:
            graph.update()
            export_bar.update()

    def do_auto_fit(e=None):
        if state.fr is None:
            toast("Pick headphones first")
            return
        state.bands = eq_model.auto_fit(state.fr, state.bands)
        strip.refresh()
        strip.update()
        bands_changed()
        toast("Auto-fit applied")

    def do_reset(e=None):
        state.reset_bands()
        strip.refresh()
        strip.update()
        bands_changed()
        toast("Bands reset")

    def do_export(e=None):
        if state.headphone is None:
            toast("Pick headphones first")
            return
        path = export_file(state.eq_app, state.headphone.name, state.bands, get_preamp())
        toast(f"Exported {state.eq_app}")

    graph = GraphCard(state, get_curves, on_toggle_smoothed=lambda e: _toggle_smoothed())
    strip = BandStripCard(state, bands_changed, do_auto_fit, do_reset)
    export_bar = ExportBar(state, get_preamp, do_export)
    dac_panel = DacPanel(
        state, devices, on_device_changed=lambda: None, get_preamp=get_preamp
    )

    def _toggle_smoothed():
        state.smoothed = not state.smoothed
        graph.refresh()
        graph.update()

    # -- header ------------------------------------------------------------

    eq_toggle_holder = ft.Container()

    def refresh_eq_toggle():
        eq_toggle_holder.content = ft.Row(
            [
                ft.Text("EQ", style=theme.mono(size=10.5)),
                pill_toggle(state.eq_on, on_change=_set_eq_on),
            ],
            spacing=8,
            tight=True,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def _set_eq_on(value: bool):
        state.eq_on = value
        refresh_eq_toggle()
        eq_toggle_holder.update()
        bands_changed()

    # GD3 — "Ap dung gu nghe": apply the saved profile's preference curve.
    taste_toggle_holder = ft.Container()

    def refresh_taste_toggle():
        taste_toggle_holder.content = ft.Row(
            [
                ft.Text("TASTE", style=theme.mono(size=10.5)),
                pill_toggle(state.taste_on, on_change=_set_taste_on),
            ],
            spacing=8,
            tight=True,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def _set_taste_on(value: bool):
        if value and state.profile is None:
            toast("Save a profile first")
            refresh_taste_toggle()
            taste_toggle_holder.update()
            return
        state.taste_on = value
        if value and (
            state.profile.as_sound_signature(
                state.headphone.name if state.headphone else None
            )
            is None
        ):
            toast("Profile has no taste data yet")
        _ensure_fr(state, targets)
        refresh_taste_toggle()
        taste_toggle_holder.update()
        bands_changed()

    target_menu_holder = ft.Container()
    target_button_holder = ft.Container()

    def refresh_target_control():
        target_button_holder.content = Pressable(
            ft.Container(
                content=ft.Row(
                    [
                        ft.Text("TARGET", style=theme.mono(size=9.5)),
                        ft.Text(
                            state.target or "—",
                            style=theme.sans(size=12.5),
                            max_lines=1,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                        ft.Icon(
                            ft.Icons.KEYBOARD_ARROW_UP if state.target_menu
                            else ft.Icons.KEYBOARD_ARROW_DOWN,
                            size=15,
                            color=theme.TEXT_TERTIARY,
                        ),
                    ],
                    spacing=8,
                    tight=True,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                border=ft.Border.all(1, theme.BORDER_DEFAULT),
                border_radius=theme.RADIUS_BUTTON_SM,
                padding=ft.Padding(left=12, right=8, top=7, bottom=7),
                bgcolor=ft.Colors.WHITE,
                shadow=theme.SHADOW_XS,
            ),
            on_press=lambda e: _toggle_target_menu(),
        )
        target_menu_holder.content = _build_target_menu() if state.target_menu else None

    def _toggle_target_menu():
        state.target_menu = not state.target_menu
        refresh_target_control()
        target_button_holder.update()
        target_menu_holder.update()

    def _build_target_menu() -> ft.Control:
        rows = []
        for name in targets:
            selected = name == state.target
            rows.append(
                Pressable(
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Text(name, style=theme.sans(size=13), expand=True,
                                        max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                                ft.Icon(ft.Icons.CHECK, size=13, color=theme.INK)
                                if selected else ft.Container(width=13),
                            ],
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        bgcolor=theme.SURFACE_ACTIVE if selected else "transparent",
                        border_radius=8,
                        padding=ft.Padding(left=10, right=10, top=7, bottom=7),
                    ),
                    on_press=_select_target(name),
                )
            )
        return ft.Container(
            content=ft.Column(rows, spacing=1, scroll=ft.ScrollMode.AUTO),
            width=TARGET_MENU_WIDTH,
            height=TARGET_MENU_HEIGHT,
            bgcolor=theme.PAPER,
            border=ft.Border.all(1, theme.BORDER_SUBTLE),
            border_radius=theme.RADIUS_CARD,
            shadow=theme.SHADOW_LG,
            padding=6,
            top=40,
            right=0,
        )

    def _select_target(name: str):
        def handler(e):
            state.target = name
            state.target_menu = False
            _ensure_fr(state, targets)
            refresh_target_control()
            target_button_holder.update()
            target_menu_holder.update()
            bands_changed()
        return handler

    refresh_eq_toggle()
    refresh_taste_toggle()
    refresh_target_control()

    headphone_name = state.headphone.name if state.headphone else "No headphone selected"
    meta = state.headphone.meta if state.headphone else "Go back and pick a measurement"

    header = ft.Row(
        [
            ft.Column(
                [
                    ft.Row(
                        [
                            ft.Text(headphone_name, style=theme.serif(size=27)),
                            ft.Container(
                                content=ft.Text(
                                    "Reference",
                                    style=theme.mono(size=10.5, color=theme.INK),
                                ),
                                bgcolor=theme.CORAL_BLOCK,
                                border_radius=theme.RADIUS_PILL,
                                padding=ft.Padding(left=10, right=10, top=3, bottom=3),
                            ),
                        ],
                        spacing=10,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Text(meta.upper(), style=theme.mono(size=11.5)),
                ],
                spacing=4,
                expand=True,
            ),
            ft.Stack([ft.Row([target_button_holder]), target_menu_holder]),
            taste_toggle_holder,
            eq_toggle_holder,
        ],
        spacing=16,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    # -- rail + assembly ---------------------------------------------------

    def open_save(e=None):
        open_save_modal(
            page, state, get_preamp,
            on_saved=lambda path: toast(f"Saved {state.profile_name.strip()}"),
        )

    def _profile_loaded(profile):
        """A loaded profile restores bands/target and becomes the taste."""
        _ensure_fr(state, targets)
        refresh_target_control()
        target_button_holder.update()
        refresh_taste_toggle()
        taste_toggle_holder.update()
        strip.refresh()
        strip.update()
        bands_changed()
        toast(f"Loaded {profile.name}")

    def open_profiles(e=None):
        open_profiles_modal(page, state, on_loaded=_profile_loaded,
                            open_save=open_save)

    rail = ft.Container(
        width=66,
        bgcolor=theme.SURFACE_SUNKEN,
        border=ft.Border(right=ft.BorderSide(1, theme.BORDER_SUBTLE)),
        content=ft.Column(
            [
                _rail_button(ft.Icons.TUNE, active=True),
                _rail_button(ft.Icons.HEADPHONES_OUTLINED, active=False, on_press=on_devices),
                _rail_button(ft.Icons.BOOKMARK_OUTLINE, active=False, on_press=open_profiles),
                ft.Container(expand=True),
                _rail_button(
                    ft.Icons.SETTINGS_OUTLINED, active=False,
                    on_press=lambda e: open_settings_modal(page, toast),
                ),
                _rail_button(
                    ft.Icons.HELP_OUTLINE, active=False,
                    on_press=lambda e: toast("Help arrives with the assistant"),
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10,
            expand=True,
        ),
        padding=ft.Padding(top=16, left=0, right=0, bottom=16),
    )

    main = ft.Container(
        content=ft.Column(
            [header, graph, strip, export_bar],
            spacing=16,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        ),
        padding=ft.Padding(left=24, right=24, top=22, bottom=22),
        expand=True,
    )

    # GD4: chat assistant FAB + drawer overlay the whole screen.
    def _chat_bands_changed():
        strip.refresh()
        if strip.page:
            strip.update()
        bands_changed()

    chat_layer = chat_overlay(
        page,
        state,
        get_headphone=lambda: state.headphone.name if state.headphone else None,
        on_bands_changed=_chat_bands_changed,
        toast=toast,
    )

    return ft.Container(
        content=ft.Stack(
            [
                ft.Row([rail, main, dac_panel], spacing=0, expand=True),
                chat_layer,
            ],
            expand=True,
        ),
        expand=True,
        bgcolor=theme.PAPER,
    )
