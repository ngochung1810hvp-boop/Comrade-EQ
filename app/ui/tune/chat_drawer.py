"""Chat assistant drawer (BUILD_PLAN.md GD4.3, handoff "Chat assistant").

Floating pill FAB bottom-right -> 392px right drawer (slide-in + scrim):
header, scrollable bubbles (user right ink-filled, assistant left bordered),
"APPLIED" diff card (green border, title + detail + undo link that restores
the band-gain snapshot), 4 suggestion chips, pill input + circular send.

The provider call runs in a worker thread via page.run_task so the UI stays
responsive; a typing indicator bubble shows while waiting.
"""

import asyncio

import flet as ft

import theme
from ai_engine import engine
from state import AppState, ChatMessage
from ui.widgets import Pressable, chip

DRAWER_WIDTH = 392
SUGGESTIONS = ("More bass", "Warmer vocals", "More air / detail", "What does Q do?")

WELCOME = (
    "Tell me how it sounds — “bass is boomy”, “vocals feel "
    "distant” — and I’ll move the bands for you."
)


def chat_overlay(page: ft.Page, state: AppState, get_headphone, on_bands_changed, toast):
    """Returns a Stack layer with the FAB + drawer; append over the screen."""

    def _assistant_bubble(content: ft.Control) -> ft.Control:
        return ft.Row(
            [
                ft.Container(
                    content=content,
                    bgcolor=theme.PAPER,
                    border=ft.Border.all(1, theme.BORDER_DEFAULT),
                    border_radius=ft.BorderRadius(14, 14, 4, 14),
                    padding=ft.Padding(left=14, right=14, top=9, bottom=9),
                    width=DRAWER_WIDTH * 0.8,
                )
            ],
            alignment=ft.MainAxisAlignment.START,
        )

    message_list = ft.ListView(expand=True, spacing=10, padding=ft.Padding(
        left=16, right=16, top=14, bottom=14), auto_scroll=True)
    input_field = ft.TextField(
        value="",
        hint_text="Describe the sound…",
        border_color="transparent",
        text_style=theme.sans(size=13.5, weight=ft.FontWeight.W_400),
        hint_style=theme.sans(size=13.5, weight=ft.FontWeight.W_400,
                              color=theme.TEXT_TERTIARY),
        content_padding=ft.Padding(left=16, right=8, top=9, bottom=9),
        on_submit=lambda e: _send(input_field.value),
        expand=True,
    )
    typing_row = ft.Container(visible=False, content=_assistant_bubble(
        ft.Text("…", style=theme.sans(size=14, color=theme.TEXT_TERTIARY))))

    # -- message rendering -------------------------------------------------

    def _user_bubble(text: str) -> ft.Control:
        return ft.Row(
            [
                ft.Container(
                    content=ft.Text(text, style=theme.sans(
                        size=13.5, color=theme.PAPER, height=1.45)),
                    bgcolor=theme.INK,
                    border_radius=ft.BorderRadius(14, 14, 14, 4),
                    padding=ft.Padding(left=14, right=14, top=9, bottom=9),
                    width=DRAWER_WIDTH * 0.72,
                )
            ],
            alignment=ft.MainAxisAlignment.END,
        )

    def _applied_card(msg: ChatMessage) -> ft.Control:
        undone = msg.snapshot is None

        def _undo(e):
            if msg.snapshot is None:
                return
            engine.restore_snapshot(state.bands, msg.snapshot)
            msg.snapshot = None
            refresh_messages()
            on_bands_changed()
            toast("Change undone")
            page.update()

        return ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Text("APPLIED", style=theme.mono(
                                size=9.5, color=theme.GREEN_EDGE)),
                            ft.Container(expand=True),
                            ft.Text("undone", style=theme.mono(
                                size=9.5, color=theme.TEXT_TERTIARY))
                            if undone else Pressable(
                                ft.Text("↺ undo", style=theme.mono(
                                    size=10.5, color=theme.INK)),
                                on_press=_undo,
                            ),
                        ],
                    ),
                    ft.Text(msg.diff_title or "", style=theme.sans(size=13)),
                    ft.Text(msg.diff_detail or "", style=theme.mono(
                        size=10, color=theme.TEXT_SECONDARY)),
                ],
                spacing=5,
                tight=True,
            ),
            border=ft.Border.all(1.5, theme.GREEN_EDGE),
            border_radius=10,
            padding=ft.Padding(left=12, right=12, top=9, bottom=9),
            opacity=0.75 if undone else 1,
        )

    def _assistant_message(msg: ChatMessage) -> ft.Control:
        blocks: list[ft.Control] = [
            ft.Text(msg.text, style=theme.sans(size=13.5, height=1.45)),
        ]
        if msg.diff_title:
            blocks.append(_applied_card(msg))
        return _assistant_bubble(ft.Column(blocks, spacing=8, tight=True))

    def refresh_messages():
        message_list.controls.clear()
        if not state.messages:
            message_list.controls.append(_assistant_message(
                ChatMessage(role="assistant", text=WELCOME)))
        for msg in state.messages:
            if msg.role == "user":
                message_list.controls.append(_user_bubble(msg.text))
            else:
                message_list.controls.append(_assistant_message(msg))
        message_list.controls.append(typing_row)

    # -- sending -------------------------------------------------------------

    def _send(text: str):
        text = text.strip()
        if not text or typing_row.visible:
            return
        input_field.value = ""
        state.chat_input = ""
        state.messages.append(ChatMessage(role="user", text=text))
        typing_row.visible = True
        refresh_messages()
        page.update()
        page.run_task(_ask, text)

    async def _ask(text: str):
        headphone = get_headphone()
        proposal = await asyncio.to_thread(
            engine.propose, text, headphone, state.bands
        )
        diff_title = diff_detail = None
        snapshot = None
        if proposal.changes_eq:
            applied = engine.apply_proposal(state.bands, proposal)
            if applied:
                snapshot, diff_detail = applied
                names = ", ".join(dict.fromkeys(
                    t.replace("_", " ") for t, _, _ in proposal.tags)) or "EQ"
                diff_title = f"Adjusted: {names}"
        reply = proposal.reply
        if proposal.note:
            reply = f"{reply}\n{proposal.note}"
        state.messages.append(ChatMessage(
            role="assistant", text=reply,
            diff_title=diff_title, diff_detail=diff_detail, snapshot=snapshot,
        ))
        typing_row.visible = False
        refresh_messages()
        if snapshot is not None:
            on_bands_changed()
            toast("Assistant adjusted the EQ")
        page.update()

    # -- drawer chrome -------------------------------------------------------

    def _assistant_mark(size: int = 26) -> ft.Control:
        return ft.Container(
            width=size,
            height=size,
            bgcolor=theme.CORAL_BLOCK,
            border_radius=theme.RADIUS_PILL,
            alignment=ft.Alignment.CENTER,
            content=ft.Icon(ft.Icons.HEADPHONES_OUTLINED, size=size * 0.58,
                            color=theme.INK),
        )

    header = ft.Container(
        content=ft.Row(
            [
                _assistant_mark(),
                ft.Text("Tuning assistant", style=theme.serif(size=18)),
                ft.Container(expand=True),
                Pressable(
                    ft.Container(
                        content=ft.Icon(ft.Icons.CLOSE, size=16,
                                        color=theme.TEXT_SECONDARY),
                        width=30, height=30, border_radius=theme.RADIUS_PILL,
                        alignment=ft.Alignment.CENTER,
                    ),
                    on_press=lambda e: _set_open(False),
                    press_scale=theme.PRESS_SCALE_ICON,
                ),
            ],
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=ft.Padding(left=16, right=12, top=14, bottom=12),
        border=ft.Border(bottom=ft.BorderSide(1, theme.BORDER_SUBTLE)),
    )

    def _chip_row() -> ft.Control:
        return ft.Row(
            [chip(s, on_click=(lambda text: lambda e: _send(text))(s),
                  mono_style=False,
                  padding=ft.Padding(left=10, right=10, top=5, bottom=5))
             for s in SUGGESTIONS],
            wrap=True,
            spacing=6,
            run_spacing=6,
        )

    send_button = Pressable(
        ft.Container(
            width=34, height=34, bgcolor=theme.INK,
            border_radius=theme.RADIUS_PILL, alignment=ft.Alignment.CENTER,
            content=ft.Icon(ft.Icons.ARROW_UPWARD, size=15, color=theme.PAPER),
            shadow=theme.SHADOW_MD,
        ),
        on_press=lambda e: _send(input_field.value),
        press_scale=theme.PRESS_SCALE_ICON,
    )

    footer = ft.Container(
        content=ft.Column(
            [
                _chip_row(),
                ft.Container(
                    content=ft.Row([input_field, send_button], spacing=4,
                                   vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    border=ft.Border.all(1, theme.BORDER_DEFAULT),
                    border_radius=theme.RADIUS_PILL,
                    padding=ft.Padding(left=0, right=4, top=2, bottom=2),
                ),
            ],
            spacing=10,
            tight=True,
        ),
        padding=ft.Padding(left=16, right=16, top=10, bottom=14),
        border=ft.Border(top=ft.BorderSide(1, theme.BORDER_SUBTLE)),
    )

    drawer = ft.Container(
        content=ft.Column([header, message_list, footer], spacing=0, expand=True),
        width=DRAWER_WIDTH,
        bgcolor=theme.PAPER,
        shadow=theme.SHADOW_XL,
        offset=ft.Offset(1, 0),
        animate_offset=ft.Animation(theme.DURATION_DRAWER, theme.EASE_DRAWER),
    )
    scrim = ft.Container(
        bgcolor=ft.Colors.with_opacity(0.4, theme.INK),
        expand=True,
        visible=False,
        opacity=0,
        animate_opacity=ft.Animation(theme.DURATION_DRAWER, theme.EASE_OUT),
        on_click=lambda e: _set_open(False),
    )
    drawer_row = ft.Row([ft.Container(expand=True), drawer], spacing=0, expand=True,
                        visible=False)

    fab = ft.Container(
        content=Pressable(
            ft.Container(
                content=ft.Row(
                    [
                        _assistant_mark(20),
                        ft.Text("Ask the assistant", style=theme.sans(
                            size=13.5, color=theme.PAPER)),
                    ],
                    spacing=8,
                    tight=True,
                ),
                bgcolor=theme.INK,
                border_radius=theme.RADIUS_PILL,
                padding=ft.Padding(left=12, right=18, top=10, bottom=10),
                shadow=theme.SHADOW_LG,
            ),
            on_press=lambda e: _set_open(True),
        ),
        alignment=ft.Alignment.BOTTOM_RIGHT,
        padding=ft.Padding(right=24, bottom=24, left=0, top=0),
    )
    fab_layer = ft.Row(
        [fab],
        alignment=ft.MainAxisAlignment.END,
        vertical_alignment=ft.CrossAxisAlignment.END,
        expand=True,
    )

    def _set_open(value: bool):
        state.chat_open = value
        fab_layer.visible = not value
        scrim.visible = True
        drawer_row.visible = True
        scrim.opacity = 1 if value else 0
        drawer.offset = ft.Offset(0, 0) if value else ft.Offset(1, 0)
        if not value:
            scrim.visible = False
            drawer_row.visible = False
        refresh_messages()
        page.update()

    refresh_messages()
    return ft.Stack([scrim, drawer_row, fab_layer], expand=True)
