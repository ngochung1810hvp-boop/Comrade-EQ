"""Graph card — 4-curve frequency-response chart (BUILD_PLAN.md GD2.2).

Recreates the handoff's "Graph card": white card, green accent tab, legend
row + SMOOTHED chip, then a log-x chart 20 Hz-20 kHz / -30..+20 dB drawing
measured (coral), target (dashed gray), EQ (green) and result (ink) paths
on a flet canvas (LineChart lacks log axes + dashed strokes).
"""

import math

import flet as ft
import flet.canvas as cv

import theme
from ui.widgets import chip

F_MIN, F_MAX = 20.0, 20000.0
DB_MIN, DB_MAX = -30.0, 20.0

X_GRID = [20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000]
Y_GRID = [20, 10, 0, -10, -20, -30]

PAD_LEFT, PAD_RIGHT, PAD_TOP, PAD_BOTTOM = 8, 8, 6, 18
CHART_HEIGHT = 300

_LOG_MIN = math.log10(F_MIN)
_LOG_SPAN = math.log10(F_MAX) - _LOG_MIN


def _x_label(f: int) -> str:
    return f"{f // 1000}k" if f >= 1000 else str(f)


def _legend_item(color: str, label: str, dashed: bool = False) -> ft.Control:
    if dashed:
        swatch = ft.Row(
            [ft.Container(width=4, height=2, bgcolor=color) for _ in range(3)],
            spacing=2,
            tight=True,
        )
    else:
        swatch = ft.Container(width=14, height=2.5, bgcolor=color, border_radius=2)
    return ft.Row(
        [swatch, ft.Text(label, style=theme.mono(size=10.5))],
        spacing=6,
        tight=True,
    )


class GraphCard(ft.Container):
    """get_curves() must return a dict with numpy arrays under keys
    "f", "measured", "target", "eq", "result" (any of the last four may be
    None to skip that path), recomputed from current state on each call.
    """

    def __init__(self, state, get_curves, on_toggle_smoothed):
        self._state = state
        self._get_curves = get_curves
        self._canvas = cv.Canvas(
            shapes=[],
            height=CHART_HEIGHT,
            expand=True,
            on_resize=self._resized,
            resize_interval=50,
        )
        self._width = 0.0
        self._smoothed_chip_holder = ft.Container()

        legend = ft.Row(
            [
                ft.Row(
                    [
                        _legend_item(theme.CORAL_EDGE, "Measured"),
                        _legend_item(theme.BORDER_STRONG, "Target", dashed=True),
                        _legend_item(theme.GREEN_EDGE, "EQ applied"),
                        _legend_item(theme.INK, "Result"),
                    ],
                    spacing=16,
                ),
                self._smoothed_chip_holder,
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        self._on_toggle_smoothed = on_toggle_smoothed
        accent_tab = ft.Container(
            width=44, height=4, bgcolor=theme.GREEN_BLOCK,
            border_radius=ft.BorderRadius(
                top_left=0, top_right=0, bottom_left=3, bottom_right=3),
        )
        super().__init__(
            content=ft.Column(
                [
                    ft.Row([ft.Container(width=18), accent_tab]),
                    ft.Container(
                        content=ft.Column([legend, self._canvas], spacing=10),
                        padding=ft.Padding(left=20, right=20, top=12, bottom=16),
                    ),
                ],
                spacing=0,
            ),
            bgcolor=ft.Colors.WHITE,
            border_radius=theme.RADIUS_CARD,
            shadow=theme.SHADOW_SM,
        )
        self._refresh_smoothed_chip()

    # -- layout ------------------------------------------------------------

    def _resized(self, e: cv.CanvasResizeEvent):
        self._width = e.width
        self._draw()
        self._canvas.update()

    def refresh(self) -> None:
        self._refresh_smoothed_chip()
        self._draw()

    def _refresh_smoothed_chip(self) -> None:
        self._smoothed_chip_holder.content = chip(
            "SMOOTHED",
            selected=self._state.smoothed,
            on_click=self._on_toggle_smoothed,
        )

    # -- drawing ------------------------------------------------------------

    def _plot_rect(self):
        w = max(self._width - PAD_LEFT - PAD_RIGHT, 10)
        h = CHART_HEIGHT - PAD_TOP - PAD_BOTTOM
        return PAD_LEFT, PAD_TOP, w, h

    def _x(self, f: float) -> float:
        x0, _, w, _ = self._plot_rect()
        return x0 + (math.log10(max(f, 1.0)) - _LOG_MIN) / _LOG_SPAN * w

    def _y(self, db: float) -> float:
        _, y0, _, h = self._plot_rect()
        clipped = max(min(db, DB_MAX), DB_MIN)
        return y0 + (1 - (clipped - DB_MIN) / (DB_MAX - DB_MIN)) * h

    def _curve_path(self, f, values, color: str, width: float, dash=None) -> cv.Path:
        elements = []
        step = max(len(f) // 250, 1)  # ~250 segments is plenty at any width
        for i in range(0, len(f), step):
            x, y = self._x(f[i]), self._y(values[i])
            elements.append(cv.Path.MoveTo(x, y) if not elements else cv.Path.LineTo(x, y))
        return cv.Path(
            elements,
            paint=ft.Paint(
                color=color,
                stroke_width=width,
                style=ft.PaintingStyle.STROKE,
                stroke_cap=ft.StrokeCap.ROUND,
                stroke_join=ft.StrokeJoin.ROUND,
                stroke_dash_pattern=dash,
                anti_alias=True,
            ),
        )

    def _draw(self) -> None:
        if self._width <= 0:
            return
        x0, y0, w, h = self._plot_rect()
        grid_paint = ft.Paint(color=theme.BORDER_SUBTLE, stroke_width=1)
        shapes: list[cv.Shape] = []

        for f in X_GRID:
            x = self._x(f)
            shapes.append(cv.Line(x, y0, x, y0 + h, paint=grid_paint))
            shapes.append(cv.Text(
                x, y0 + h + 4, _x_label(f),
                style=theme.mono(size=8.5),
                alignment=ft.Alignment.TOP_CENTER,
            ))
        for db in Y_GRID:
            y = self._y(db)
            shapes.append(cv.Line(
                x0, y, x0 + w, y,
                paint=grid_paint if db != 0 else ft.Paint(color=theme.BORDER_DEFAULT, stroke_width=1),
            ))
            shapes.append(cv.Text(
                x0 + 4, y - 3, f"{db:+d}" if db else "0",
                style=theme.mono(size=8.5),
                alignment=ft.Alignment.BOTTOM_LEFT,
            ))

        curves = self._get_curves()
        if curves is not None:
            f = curves["f"]
            if curves.get("target") is not None:
                shapes.append(self._curve_path(
                    f, curves["target"], theme.BORDER_STRONG, 1.5, dash=[5, 5]))
            if curves.get("measured") is not None:
                shapes.append(self._curve_path(f, curves["measured"], theme.CORAL_EDGE, 1.8))
            if curves.get("eq") is not None:
                shapes.append(self._curve_path(f, curves["eq"], theme.GREEN_EDGE, 1.8))
            if curves.get("result") is not None:
                shapes.append(self._curve_path(f, curves["result"], theme.INK, 2.4))

        self._canvas.shapes = shapes
