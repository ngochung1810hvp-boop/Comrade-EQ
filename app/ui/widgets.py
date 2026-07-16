"""Shared building-block widgets: Pressable, chip, pill toggle, dropdown, toast, modal.

Motion follows theme.py tokens (press ~140ms scale(0.97), drawer/dropdown/modal
durations + eases) per docs/design_handoff_comrade_curve/README.md "Motion".
"""

import asyncio

import flet as ft

import theme


class Pressable(ft.GestureDetector):
    """Wraps content with the design system's universal press feedback:
    transform: scale(0.97) (icon-only controls use 0.94) on press, released
    back to 1.0, with the press-duration ease.
    """

    def __init__(
        self,
        content: ft.Control,
        on_press=None,
        press_scale: float = theme.PRESS_SCALE,
        **kwargs,
    ):
        super().__init__(
            content=content,
            mouse_cursor=ft.MouseCursor.CLICK,
            scale=1.0,
            animate_scale=ft.Animation(theme.DURATION_PRESS, theme.EASE_OUT),
            on_tap_down=self._pressed,
            on_tap_up=self._released,
            on_tap_cancel=self._released,
            on_tap=lambda e: on_press(e) if on_press else None,
            **kwargs,
        )
        self._press_scale = press_scale

    def _pressed(self, e: ft.TapEvent):
        self.scale = self._press_scale
        self.update()

    def _released(self, e):
        self.scale = 1.0
        self.update()


def chip(
    text: str,
    *,
    selected: bool = False,
    bgcolor: str | None = None,
    text_color: str | None = None,
    border_color: str | None = None,
    on_click=None,
    mono_style: bool = True,
    padding: ft.Padding | None = None,
) -> ft.Control:
    """A small pill/rounded-rect label used for tags, target chips, suggestion
    chips, etc. Selected state gets a 1px ink border, matching the handoff's
    "selected = ink border" convention (export bar, target menu).
    """
    resolved_bg = bgcolor or (theme.SURFACE_ACTIVE if selected else "transparent")
    resolved_border = border_color or (theme.INK if selected else theme.BORDER_DEFAULT)
    label_style = (
        theme.mono(size=10.5, color=text_color or theme.TEXT_PRIMARY, letter_spacing=0.06)
        if mono_style
        else theme.sans(size=13.5, color=text_color or theme.TEXT_PRIMARY)
    )
    container = ft.Container(
        content=ft.Text(text, style=label_style),
        bgcolor=resolved_bg,
        border=ft.Border.all(1, resolved_border),
        border_radius=theme.RADIUS_PILL,
        padding=padding or ft.Padding(left=12, right=12, top=6, bottom=6),
        animate=ft.Animation(theme.DURATION_PRESS, theme.EASE_OUT),
    )
    if on_click is None:
        return container
    return Pressable(container, on_press=on_click)


def pill_toggle(value: bool, on_change=None) -> ft.Control:
    """34x20 on/off switch, green tint when on, per the Tune header EQ toggle."""
    track_w, track_h, knob = 34, 20, 16
    knob_container = ft.Container(
        width=knob,
        height=knob,
        bgcolor=theme.PAPER,
        border_radius=theme.RADIUS_PILL,
        left=track_w - knob - 2 if value else 2,
        top=2,
        animate_position=ft.Animation(theme.DURATION_DRAWER, theme.EASE_DRAWER),
    )
    track = ft.Stack(
        controls=[knob_container],
        width=track_w,
        height=track_h,
    )
    wrapper = ft.Container(
        content=track,
        width=track_w,
        height=track_h,
        bgcolor=theme.GREEN_BLOCK if value else theme.BORDER_DEFAULT,
        border_radius=theme.RADIUS_PILL,
        animate=ft.Animation(theme.DURATION_DRAWER, theme.EASE_DRAWER),
    )

    def _toggle(e):
        if on_change:
            on_change(not value)

    return Pressable(wrapper, on_press=_toggle, press_scale=theme.PRESS_SCALE_ICON)


def dropdown_menu(
    trigger: ft.Control,
    items: list[ft.Control],
    *,
    open: bool = False,
    width: int | None = None,
) -> ft.Control:
    """A trigger button with a floating panel of items directly below it.

    Anchoring is local (Stack around trigger+panel) rather than
    screen-coordinate based, which keeps this reusable without wiring up
    global position tracking; sufficient for the app's fixed-layout screens.
    """
    panel = ft.Container(
        content=ft.Column(items, spacing=2, tight=True),
        bgcolor=theme.PAPER,
        border=ft.Border.all(1, theme.BORDER_SUBTLE),
        border_radius=theme.RADIUS_CARD,
        shadow=theme.SHADOW_LG,
        padding=6,
        width=width,
        top=44,
        left=0,
        opacity=1 if open else 0,
        visible=open,
        animate_opacity=ft.Animation(theme.DURATION_DROPDOWN, theme.EASE_OUT),
    )
    return ft.Stack(controls=[trigger, panel])


def toast(text: str) -> ft.Container:
    """Bottom-center floating pill toast (ink bg, white text, green check)."""
    return ft.Container(
        content=ft.Row(
            [
                ft.Container(
                    width=16,
                    height=16,
                    bgcolor=theme.GREEN_BLOCK,
                    border_radius=theme.RADIUS_PILL,
                    content=ft.Icon(ft.Icons.CHECK, size=11, color=theme.INK),
                    alignment=ft.Alignment.CENTER,
                ),
                ft.Text(text, style=theme.sans(size=13.5, color=theme.PAPER)),
            ],
            spacing=8,
            tight=True,
        ),
        bgcolor=theme.INK,
        border_radius=theme.RADIUS_PILL,
        padding=ft.Padding(left=16, right=18, top=10, bottom=10),
        shadow=theme.SHADOW_LG,
    )


async def show_toast(page: ft.Page, text: str) -> None:
    """Mounts a toast at bottom-center, slide-up + fade-in, auto-dismiss."""
    bubble = toast(text)
    holder = ft.Container(
        content=bubble,
        alignment=ft.Alignment.BOTTOM_CENTER,
        padding=ft.Padding(bottom=32, left=0, right=0, top=0),
        opacity=0,
        offset=ft.Offset(0, 0.15),
        animate_opacity=ft.Animation(theme.DURATION_DRAWER, theme.EASE_OUT),
        animate_offset=ft.Animation(theme.DURATION_DRAWER, theme.EASE_OUT),
        expand=True,
    )
    page.overlay.append(holder)
    page.update()
    holder.opacity = 1
    holder.offset = ft.Offset(0, 0)
    holder.update()
    await asyncio.sleep(theme.DURATION_TOAST / 1000)
    holder.opacity = 0
    holder.offset = ft.Offset(0, 0.15)
    holder.update()
    await asyncio.sleep(theme.DURATION_DRAWER / 1000)
    if holder in page.overlay:
        page.overlay.remove(holder)
        page.update()


def modal(content: ft.Control, on_dismiss=None) -> ft.Control:
    """Centered card that scale-ins from 0.94->1 with a dimming scrim behind it.

    Returns a full-page Stack meant to be appended to page.overlay.
    """
    card = ft.Container(
        content=content,
        bgcolor=theme.PAPER,
        border_radius=14,
        shadow=theme.SHADOW_XL,
        padding=24,
        scale=1,
        opacity=1,
        animate_scale=ft.Animation(theme.DURATION_MODAL, theme.EASE_OUT),
        animate_opacity=ft.Animation(theme.DURATION_MODAL, theme.EASE_OUT),
    )
    scrim = ft.Container(
        bgcolor=ft.Colors.with_opacity(0.5, theme.INK),
        expand=True,
        on_click=(lambda e: on_dismiss(e)) if on_dismiss else None,
    )
    return ft.Stack(
        controls=[
            scrim,
            ft.Container(content=card, alignment=ft.Alignment.CENTER, expand=True),
        ],
        expand=True,
    )
