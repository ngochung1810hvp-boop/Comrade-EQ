"""Screen 1 — Welcome.

Recreates docs/design_handoff_comrade_curve/README.md section 1, pixel-close
to the prototype markup (comrade-curve.dc.html lines 51-81), minus the fake
window chrome (native OS window is used instead, per BUILD_PLAN.md section 2).
"""

from dataclasses import replace

import flet as ft
import flet.canvas as fc

import theme
from ui.widgets import Pressable

WELCOME_FEATURES = [
    ("AI TUNING", "Describe the sound; the curve follows."),
    ("DAC CONTROL", "Hardware volume, preamp & output device."),
    ("5,300+ MEASURED", "oratory1990, crinacle, Rtings & more."),
]


def _wavy_background() -> ft.Control:
    """Two faint decorative wavy lines (coral/green), ported from the SVG
    paths in the prototype (viewBox 0 0 1240 780).
    """
    coral_path = fc.Path(
        elements=[
            fc.Path.MoveTo(0, 470),
            fc.Path.CubicTo(180, 470, 240, 300, 360, 300),
            fc.Path.CubicTo(470, 300, 500, 430, 620, 430),
            fc.Path.CubicTo(760, 430, 780, 250, 900, 250),
            fc.Path.CubicTo(1010, 250, 1060, 400, 1240, 400),
        ],
        paint=ft.Paint(
            style=ft.PaintingStyle.STROKE,
            stroke_width=2,
            color=ft.Colors.with_opacity(0.55, theme.CORAL_EDGE),
        ),
    )
    green_path = fc.Path(
        elements=[
            fc.Path.MoveTo(0, 500),
            fc.Path.CubicTo(180, 500, 240, 380, 360, 380),
            fc.Path.CubicTo(470, 380, 520, 460, 620, 460),
            fc.Path.CubicTo(760, 460, 800, 360, 900, 360),
            fc.Path.CubicTo(1010, 360, 1080, 440, 1240, 440),
        ],
        paint=ft.Paint(
            style=ft.PaintingStyle.STROKE,
            stroke_width=2,
            color=ft.Colors.with_opacity(0.7, theme.GREEN_EDGE),
        ),
    )
    return ft.Container(
        content=fc.Canvas(shapes=[coral_path, green_path], width=1240, height=780),
        opacity=0.5,
        alignment=ft.Alignment.TOP_LEFT,
    )


def _icon_badge() -> ft.Control:
    # Logo/app mark is not decided yet (BUILD_PLAN.md section 2.3): use a
    # plain monochrome geometric placeholder until an original mark exists.
    return ft.Container(
        width=60,
        height=60,
        bgcolor=theme.INK,
        border_radius=14,
        shadow=theme.SHADOW_LG,
        alignment=ft.Alignment.CENTER,
        margin=ft.Margin(bottom=26, left=0, right=0, top=0),
        content=ft.Container(
            width=14,
            height=14,
            bgcolor=theme.GREEN_BLOCK,
            border_radius=3,
        ),
    )


def _headline() -> ft.Control:
    # TextSpan doesn't inherit color from the parent Text.style in this Flet
    # version, so every span needs its own explicit style.
    base = theme.serif(size=52, height=1.08, letter_spacing=-0.025)
    return ft.Text(
        spans=[
            ft.TextSpan("Tune your headphones —\nor just ", style=base),
            ft.TextSpan(
                "ask",
                style=replace(base, bgcolor=theme.GREEN_BLOCK),
            ),
            ft.TextSpan(" in plain words.", style=base),
        ],
        text_align=ft.TextAlign.CENTER,
    )


def _body_paragraph() -> ft.Control:
    base = theme.sans(size=16, weight=ft.FontWeight.W_400, color=theme.TEXT_SECONDARY, height=1.6)
    italic = theme.serif(size=16, italic=True, color=theme.TEXT_SECONDARY, height=1.6)
    return ft.Text(
        spans=[
            ft.TextSpan(
                "Auto EQ Studio measures your headphones against a target "
                'curve and corrects them in real time. Not sure what to '
                'change? Tell the assistant ',
                style=base,
            ),
            ft.TextSpan("“warmer vocals”", style=italic),
            ft.TextSpan(" and watch the curve move.", style=base),
        ],
        text_align=ft.TextAlign.CENTER,
        width=520,
    )


def _primary_button(on_click) -> ft.Control:
    return Pressable(
        ft.Container(
            content=ft.Row(
                [
                    ft.Text("Get started", style=theme.sans(size=15, color=theme.PAPER)),
                    ft.Icon(ft.Icons.ARROW_FORWARD, size=17, color=theme.PAPER),
                ],
                spacing=9,
                tight=True,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            height=46,
            padding=ft.Padding(left=24, right=24, top=0, bottom=0),
            bgcolor=theme.INK,
            border_radius=theme.RADIUS_BUTTON,
            shadow=theme.SHADOW_MD,
            alignment=ft.Alignment.CENTER,
        ),
        on_press=on_click,
    )


def _secondary_button(on_click) -> ft.Control:
    return Pressable(
        ft.Container(
            content=ft.Text("Import a profile", style=theme.sans(size=15, color=theme.TEXT_PRIMARY)),
            height=46,
            padding=ft.Padding(left=22, right=22, top=0, bottom=0),
            bgcolor=theme.PAPER,
            border=ft.Border.all(1, theme.BORDER_DEFAULT),
            border_radius=theme.RADIUS_BUTTON,
            shadow=theme.SHADOW_SM,
            alignment=ft.Alignment.CENTER,
        ),
        on_press=on_click,
    )


def _feature(tag: str, text: str) -> ft.Control:
    return ft.Container(
        width=150,
        content=ft.Column(
            [
                ft.Text(tag, style=theme.mono(size=10.5, color=theme.CORAL_EDGE, letter_spacing=0.1)),
                ft.Text(
                    text,
                    style=theme.sans(size=13.5, weight=ft.FontWeight.W_400, color=theme.TEXT_SECONDARY, height=1.45),
                ),
            ],
            spacing=6,
            horizontal_alignment=ft.CrossAxisAlignment.START,
        ),
    )


def welcome_screen(on_get_started, on_import_profile) -> ft.Control:
    content = ft.Column(
        [
            _icon_badge(),
            ft.Text(
                "TUNE · LISTEN · SHAPE BY EAR",
                style=theme.mono(size=11, letter_spacing=0.14),
            ),
            ft.Container(height=18),
            _headline(),
            ft.Container(height=18),
            _body_paragraph(),
            ft.Container(height=30),
            ft.Row(
                [_primary_button(on_get_started), _secondary_button(on_import_profile)],
                spacing=12,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            ft.Container(height=44),
            ft.Row(
                [_feature(tag, text) for tag, text in WELCOME_FEATURES],
                spacing=40,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=0,
        width=640,
    )
    return ft.Stack(
        controls=[
            _wavy_background(),
            ft.Container(
                content=content,
                alignment=ft.Alignment.CENTER,
                expand=True,
                padding=ft.Padding(left=40, right=40, top=0, bottom=0),
            ),
        ],
        expand=True,
    )
