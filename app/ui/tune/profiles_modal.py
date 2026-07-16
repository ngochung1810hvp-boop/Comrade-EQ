"""Profiles modal (BUILD_PLAN.md GD5.3 — multiple profiles: EDM/Jazz/movie).

Lists saved profiles; selecting one makes it the active taste memory and
restores its saved tune (bands + target). "Save current…" opens the GD2/3
save modal.
"""

import flet as ft

import theme
from profile_store import ProfileStore
from state import AppState, Band
from ui.widgets import Pressable, modal


def open_profiles_modal(page: ft.Page, state: AppState, on_loaded, open_save) -> None:
    store = ProfileStore()
    names = store.list_names()

    def close(e=None):
        if holder in page.overlay:
            page.overlay.remove(holder)
            page.update()

    def _load(name: str):
        def handler(e):
            profile = store.load(name)
            state.profile = profile
            state.profile_name = profile.name
            if profile.bands:
                state.bands = [
                    Band(fc=b["fc"], type=b["type"], gain=b["gain"], q=b["q"])
                    for b in profile.bands
                ]
            if profile.target:
                state.target = profile.target
            close()
            on_loaded(profile)
        return handler

    rows: list[ft.Control] = []
    for name in names:
        try:
            profile = store.load(name)
        except Exception:
            continue
        active = state.profile is not None and state.profile.name == name
        meta_parts = [p for p in (profile.headphone, profile.target) if p]
        deltas = len(profile.filter_deltas)
        if deltas:
            meta_parts.append(f"{deltas} taste delta{'s' if deltas != 1 else ''}")
        rows.append(
            Pressable(
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Column(
                                [
                                    ft.Text(profile.name, style=theme.sans(size=14)),
                                    ft.Text(" · ".join(meta_parts) or "empty",
                                            style=theme.mono(size=10),
                                            max_lines=1,
                                            overflow=ft.TextOverflow.ELLIPSIS),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                            ft.Icon(ft.Icons.CHECK, size=14, color=theme.INK)
                            if active else ft.Container(width=14),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    bgcolor=theme.SURFACE_ACTIVE if active else "transparent",
                    border_radius=8,
                    padding=ft.Padding(left=12, right=12, top=9, bottom=9),
                ),
                on_press=_load(name),
            )
        )
    if not rows:
        rows.append(
            ft.Container(
                content=ft.Text(
                    "No profiles yet — save your first tune below.",
                    style=theme.sans(size=13, weight=ft.FontWeight.W_400,
                                     color=theme.TEXT_SECONDARY),
                ),
                padding=ft.Padding(left=12, right=12, top=10, bottom=10),
            )
        )

    def _save_current(e=None):
        close()
        open_save()

    content = ft.Column(
        [
            ft.Text("Sound profiles", style=theme.serif(size=23)),
            ft.Text(
                "One taste memory per mood — EDM, jazz, movies. Loading a "
                "profile restores its tune and applies its taste to any "
                "headphone.",
                style=theme.sans(size=13, weight=ft.FontWeight.W_400,
                                 color=theme.TEXT_SECONDARY, height=1.5),
            ),
            ft.Container(
                content=ft.Column(rows, spacing=2, tight=True,
                                  scroll=ft.ScrollMode.AUTO),
                height=min(260, max(60, 52 * max(1, len(rows)))),
                border=ft.Border.all(1, theme.BORDER_SUBTLE),
                border_radius=10,
                padding=4,
            ),
            ft.Row(
                [
                    ft.Container(expand=True),
                    Pressable(
                        ft.Container(
                            content=ft.Text("Save current…", style=theme.sans(
                                size=13.5, color=theme.PAPER)),
                            height=38,
                            padding=ft.Padding(left=18, right=18, top=0, bottom=0),
                            bgcolor=theme.INK,
                            border_radius=theme.RADIUS_BUTTON,
                            alignment=ft.Alignment.CENTER,
                            shadow=theme.SHADOW_MD,
                        ),
                        on_press=_save_current,
                    ),
                ],
            ),
        ],
        spacing=10,
        width=420,
        tight=True,
    )

    holder = modal(content, on_dismiss=close)
    page.overlay.append(holder)
    page.update()
