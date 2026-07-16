"""Save-profile modal (BUILD_PLAN.md GD2.6, upgraded in GD3.3).

Handoff spec: centered 400px card, scale-in — serif "Save sound profile"
title, description naming the current headphone, profile-name input, 2-up
Target/Preamp summary, Cancel / Save buttons.

GD3: writes the full profile schema via ProfileStore (preference_curve,
filter_deltas, history) instead of the minimal GD2 payload. Re-saving an
existing name keeps its accumulated taste memory and only refreshes the
tune snapshot.
"""

import flet as ft

import theme
from profile_store import Profile, ProfileStore
from state import AppState
from ui.widgets import Pressable, modal


def save_profile(state: AppState, preamp: float) -> str:
    """Writes the full profiles/<name>.json via ProfileStore; returns the
    path and sets the saved profile as the active one (state.profile)."""
    store = ProfileStore()
    name = state.profile_name.strip()
    if store.exists(name):
        profile = store.load(name)
        profile.name = name
    else:
        profile = Profile(name=name)
    profile.headphone = state.headphone.name if state.headphone else None
    profile.target = state.target
    profile.preamp = round(preamp, 2)
    profile.bands = [
        {"fc": b.fc, "type": b.type, "gain": b.gain, "q": b.q}
        for b in state.bands
    ]
    profile.record_history(
        action="save", headphone=profile.headphone, target=profile.target
    )
    path = store.save(profile)
    state.profile = profile
    return path


def open_save_modal(page: ft.Page, state: AppState, get_preamp, on_saved) -> None:
    """Mounts the save modal into page.overlay; on_saved(path) after write."""
    state.save_open = True

    def close(e=None):
        state.save_open = False
        if holder in page.overlay:
            page.overlay.remove(holder)
            page.update()

    def submit(e=None):
        if not state.profile_name.strip():
            name_field.error_text = "Name the profile first"
            name_field.update()
            return
        path = save_profile(state, get_preamp())
        close()
        on_saved(path)

    def on_name_change(e):
        state.profile_name = e.control.value
        if name_field.error_text:
            name_field.error_text = None
            name_field.update()

    name_field = ft.TextField(
        value=state.profile_name,
        hint_text="e.g. Evening jazz",
        border_color=theme.BORDER_DEFAULT,
        focused_border_color=theme.INK,
        border_radius=8,
        text_style=theme.sans(size=14, weight=ft.FontWeight.W_400),
        hint_style=theme.sans(size=14, weight=ft.FontWeight.W_400, color=theme.TEXT_TERTIARY),
        on_change=on_name_change,
        on_submit=submit,
        content_padding=ft.Padding(left=12, right=12, top=10, bottom=10),
    )

    headphone = state.headphone.name if state.headphone else "your headphones"

    def summary_cell(label: str, value: str) -> ft.Control:
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(label, style=theme.mono(size=9.5)),
                    ft.Text(value, style=theme.sans(size=13), max_lines=1,
                            overflow=ft.TextOverflow.ELLIPSIS),
                ],
                spacing=3,
            ),
            bgcolor=theme.SURFACE_SUNKEN,
            border_radius=8,
            padding=ft.Padding(left=12, right=12, top=8, bottom=8),
            expand=True,
        )

    cancel_button = Pressable(
        ft.Container(
            content=ft.Text("Cancel", style=theme.sans(size=13.5)),
            height=38,
            padding=ft.Padding(left=16, right=16, top=0, bottom=0),
            border=ft.Border.all(1, theme.BORDER_DEFAULT),
            border_radius=theme.RADIUS_BUTTON,
            alignment=ft.Alignment.CENTER,
        ),
        on_press=close,
    )
    save_button = Pressable(
        ft.Container(
            content=ft.Text("Save profile", style=theme.sans(size=13.5, color=theme.PAPER)),
            height=38,
            padding=ft.Padding(left=18, right=18, top=0, bottom=0),
            bgcolor=theme.INK,
            border_radius=theme.RADIUS_BUTTON,
            alignment=ft.Alignment.CENTER,
            shadow=theme.SHADOW_MD,
        ),
        on_press=submit,
    )

    content = ft.Column(
        [
            ft.Text("Save sound profile", style=theme.serif(size=23)),
            ft.Text(
                f"Keep this tune for {headphone} and re-apply it anytime.",
                style=theme.sans(size=13, weight=ft.FontWeight.W_400,
                                 color=theme.TEXT_SECONDARY, height=1.5),
            ),
            ft.Container(height=4),
            ft.Text("PROFILE NAME", style=theme.mono(size=9.5)),
            name_field,
            ft.Row(
                [
                    summary_cell("TARGET", state.target or "—"),
                    summary_cell("PREAMP", f"{get_preamp():.1f} dB"),
                ],
                spacing=8,
            ),
            ft.Container(height=6),
            ft.Row(
                [cancel_button, save_button],
                alignment=ft.MainAxisAlignment.END,
                spacing=10,
            ),
        ],
        spacing=10,
        width=400,
        tight=True,
    )

    holder = modal(content, on_dismiss=close)
    page.overlay.append(holder)
    page.update()
