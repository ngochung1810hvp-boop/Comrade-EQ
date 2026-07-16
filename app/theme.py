"""Design tokens for Comrade Curve, ported from docs/design_handoff_comrade_curve/README.md."""

import flet as ft

# --- Colors ------------------------------------------------------------

INK = "#131210"
PAPER = "#fdfcfa"
DESK = "#efece6"

GREEN_BLOCK = "#c8e6cd"
GREEN_EDGE = "#8fbf9c"
CORAL_BLOCK = "#f3c9b6"
CORAL_EDGE = "#d99a7c"

# Warm grays derived from ink at reduced opacity, per handoff:
# "Text secondary/tertiary: warm grays derived from ink".
TEXT_PRIMARY = INK
TEXT_SECONDARY = ft.Colors.with_opacity(0.68, INK)
TEXT_TERTIARY = ft.Colors.with_opacity(0.46, INK)

BORDER_SUBTLE = ft.Colors.with_opacity(0.07, INK)
BORDER_DEFAULT = ft.Colors.with_opacity(0.12, INK)
BORDER_STRONG = ft.Colors.with_opacity(0.24, INK)

SURFACE_PAGE = PAPER
SURFACE_ACTIVE = ft.Colors.with_opacity(0.06, INK)
SURFACE_SUNKEN = ft.Colors.with_opacity(0.035, INK)

# Decorative only (prototype title-bar traffic lights); kept for reference,
# not used in the native app shell per BUILD_PLAN.md section 2.
TRAFFIC_RED = "#ec6a5e"
TRAFFIC_AMBER = "#f4bf4f"
TRAFFIC_GREEN = "#61c554"

# --- Typography ----------------------------------------------------------

FONT_SERIF = "Newsreader"
FONT_SANS = "Geist"
FONT_MONO = "Geist Mono"

FONT_FILES = {
    FONT_SERIF: "fonts/Newsreader.ttf",
    "Newsreader Italic": "fonts/Newsreader-Italic.ttf",
    FONT_SANS: "fonts/Geist.ttf",
    FONT_MONO: "fonts/GeistMono.ttf",
}


def serif(
    size: int = 16,
    weight: ft.FontWeight = ft.FontWeight.W_400,
    color: str = TEXT_PRIMARY,
    letter_spacing: float = 0,
    height: float | None = None,
    italic: bool = False,
) -> ft.TextStyle:
    return ft.TextStyle(
        font_family="Newsreader Italic" if italic else FONT_SERIF,
        size=size,
        weight=weight,
        color=color,
        letter_spacing=letter_spacing,
        height=height,
        italic=italic,
    )


def sans(
    size: int = 14,
    weight: ft.FontWeight = ft.FontWeight.W_500,
    color: str = TEXT_PRIMARY,
    letter_spacing: float = 0,
    height: float | None = None,
) -> ft.TextStyle:
    return ft.TextStyle(
        font_family=FONT_SANS,
        size=size,
        weight=weight,
        color=color,
        letter_spacing=letter_spacing,
        height=height,
    )


def mono(
    size: int = 11,
    weight: ft.FontWeight = ft.FontWeight.W_400,
    color: str = TEXT_TERTIARY,
    letter_spacing: float = 0.06,
    height: float | None = None,
) -> ft.TextStyle:
    return ft.TextStyle(
        font_family=FONT_MONO,
        size=size,
        weight=weight,
        color=color,
        letter_spacing=letter_spacing,
        height=height,
    )


# --- Radius --------------------------------------------------------------

RADIUS_WINDOW = 16
RADIUS_CARD = 12
RADIUS_BUTTON = 9
RADIUS_BUTTON_SM = 7
RADIUS_PILL = 999

# --- Spacing (4px base) ----------------------------------------------------

SPACE_1 = 4
SPACE_2 = 6
SPACE_3 = 8
SPACE_4 = 12
SPACE_5 = 16
SPACE_6 = 18
SPACE_7 = 20
SPACE_8 = 22
SPACE_9 = 24

# --- Shadows ---------------------------------------------------------------
# Elevation scale derived from the one exact value given in the handoff
# (app-window shadow "0 40px 90px -30px rgba(19,18,16,.45)" == SHADOW_XL);
# xs/sm/md/lg are estimated proportionally since the source design-system
# stylesheet (colors.css/elevation.css) isn't checked into this repo.

SHADOW_XS = [
    ft.BoxShadow(
        blur_radius=3,
        spread_radius=0,
        offset=ft.Offset(0, 1),
        color=ft.Colors.with_opacity(0.06, INK),
    ),
]

SHADOW_SM = [
    ft.BoxShadow(
        blur_radius=8,
        spread_radius=-2,
        offset=ft.Offset(0, 3),
        color=ft.Colors.with_opacity(0.10, INK),
    ),
]

SHADOW_MD = [
    ft.BoxShadow(
        blur_radius=20,
        spread_radius=-6,
        offset=ft.Offset(0, 8),
        color=ft.Colors.with_opacity(0.16, INK),
    ),
]

SHADOW_LG = [
    ft.BoxShadow(
        blur_radius=45,
        spread_radius=-15,
        offset=ft.Offset(0, 20),
        color=ft.Colors.with_opacity(0.30, INK),
    ),
]

SHADOW_XL = [
    ft.BoxShadow(
        blur_radius=90,
        spread_radius=-30,
        offset=ft.Offset(0, 40),
        color=ft.Colors.with_opacity(0.45, INK),
    ),
]

# --- Motion ------------------------------------------------------------

DURATION_PRESS = 140
DURATION_DRAWER = 260
DURATION_MODAL = 360
DURATION_DROPDOWN = 180
DURATION_TOAST = 2600

# Flet only exposes Flutter's built-in Curves as an enum (no arbitrary
# cubic-bezier), so the handoff's custom eases are approximated with the
# closest built-in curve.
EASE_OUT = ft.AnimationCurve.EASE_OUT_CUBIC  # handoff: cubic-bezier(.23,1,.32,1)
EASE_DRAWER = ft.AnimationCurve.DECELERATE  # handoff: cubic-bezier(.32,.72,0,1)

PRESS_SCALE = 0.97
PRESS_SCALE_ICON = 0.94


def theme() -> ft.Theme:
    return ft.Theme(
        font_family=FONT_SANS,
        color_scheme=ft.ColorScheme(
            primary=INK,
            on_primary=PAPER,
            surface=PAPER,
            on_surface=INK,
        ),
        scrollbar_theme=ft.ScrollbarTheme(
            thumb_color=ft.Colors.with_opacity(0.18, INK),
        ),
    )
