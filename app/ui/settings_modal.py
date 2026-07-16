"""Settings modal (BUILD_PLAN.md GD5.3): AI provider + keys + endpoint.

Provider: Auto / Anthropic API / OpenAI-compatible (OpenAI, DeepSeek,
Gemini's OpenAI-compat API, Ollama, LM Studio). API keys are stored in the
OS keyring only; base URL + model go to ~/.config/comrade-eq/config.json
via settings_store.
"""

import flet as ft

import settings_store
import theme
from ui.widgets import Pressable, chip, modal

PROVIDERS = (("auto", "Auto"), ("anthropic", "Anthropic API"), ("openai", "OpenAI-compatible"))


def open_settings_modal(page: ft.Page, toast) -> None:
    config = settings_store.load()
    selected = {"provider": config["provider"]}

    def field(value: str, hint: str, password: bool = False) -> ft.TextField:
        return ft.TextField(
            value=value,
            hint_text=hint,
            password=password,
            can_reveal_password=password,
            border_color=theme.BORDER_DEFAULT,
            focused_border_color=theme.INK,
            border_radius=8,
            text_style=theme.sans(size=13.5, weight=ft.FontWeight.W_400),
            hint_style=theme.sans(size=13.5, weight=ft.FontWeight.W_400,
                                  color=theme.TEXT_TERTIARY),
            content_padding=ft.Padding(left=12, right=12, top=9, bottom=9),
        )

    key_hint = (
        "Key saved in keyring — enter to replace"
        if settings_store.has_api_key("anthropic")
        else "sk-ant-…"
    )
    key_field = field("", key_hint, password=True)
    openai_key_hint = (
        "Key saved in keyring — enter to replace"
        if settings_store.has_api_key("openai")
        else "sk-… (OpenAI, DeepSeek, Gemini, or leave blank for local)"
    )
    openai_key_field = field("", openai_key_hint, password=True)
    base_url_field = field(config["base_url"], settings_store.DEFAULTS["base_url"])
    model_field = field(config["model"], settings_store.DEFAULTS["model"])

    provider_row_holder = ft.Container()

    def refresh_providers():
        provider_row_holder.content = ft.Row(
            [
                chip(
                    label,
                    selected=selected["provider"] == value,
                    on_click=(lambda v: lambda e: _pick(v))(value),
                    mono_style=False,
                )
                for value, label in PROVIDERS
            ],
            spacing=6,
        )

    def _pick(value: str):
        selected["provider"] = value
        refresh_providers()
        provider_row_holder.update()

    def close(e=None):
        if holder in page.overlay:
            page.overlay.remove(holder)
            page.update()

    def submit(e=None):
        settings_store.save(
            {
                "provider": selected["provider"],
                "base_url": base_url_field.value.strip(),
                "model": model_field.value.strip(),
            }
        )
        stored, keyring_failed = False, False
        key = key_field.value.strip()
        if key:
            if settings_store.set_api_key("anthropic", key):
                stored = True
            else:
                keyring_failed = True
        openai_key = openai_key_field.value.strip()
        if openai_key:
            if settings_store.set_api_key("openai", openai_key):
                stored = True
            else:
                keyring_failed = True
        if keyring_failed:
            toast("Settings saved · keyring unavailable, key NOT stored")
        elif stored:
            toast("Settings saved · key stored in keyring")
        else:
            toast("Settings saved")
        close()

    def label(text: str) -> ft.Control:
        return ft.Text(text, style=theme.mono(size=9.5))

    refresh_providers()
    content = ft.Column(
        [
            ft.Text("Assistant settings", style=theme.serif(size=23)),
            ft.Text(
                "Pick who translates your feedback into EQ. Auto uses the "
                "Anthropic API when a key exists, otherwise the OpenAI-compatible "
                "endpoint below — point it at OpenAI, DeepSeek, Gemini's "
                "OpenAI-compat API, or a local model (Ollama, LM Studio).",
                style=theme.sans(size=13, weight=ft.FontWeight.W_400,
                                 color=theme.TEXT_SECONDARY, height=1.5),
            ),
            ft.Container(height=2),
            label("PROVIDER"),
            provider_row_holder,
            label("ANTHROPIC API KEY (KEYRING)"),
            key_field,
            label("OPENAI-COMPATIBLE ENDPOINT (OPENAI / DEEPSEEK / GEMINI / OLLAMA / LM STUDIO)"),
            base_url_field,
            label("OPENAI-COMPATIBLE API KEY (KEYRING)"),
            openai_key_field,
            label("MODEL"),
            model_field,
            ft.Container(height=4),
            ft.Row(
                [
                    Pressable(
                        ft.Container(
                            content=ft.Text("Cancel", style=theme.sans(size=13.5)),
                            height=38,
                            padding=ft.Padding(left=16, right=16, top=0, bottom=0),
                            border=ft.Border.all(1, theme.BORDER_DEFAULT),
                            border_radius=theme.RADIUS_BUTTON,
                            alignment=ft.Alignment.CENTER,
                        ),
                        on_press=close,
                    ),
                    Pressable(
                        ft.Container(
                            content=ft.Text("Save settings", style=theme.sans(
                                size=13.5, color=theme.PAPER)),
                            height=38,
                            padding=ft.Padding(left=18, right=18, top=0, bottom=0),
                            bgcolor=theme.INK,
                            border_radius=theme.RADIUS_BUTTON,
                            alignment=ft.Alignment.CENTER,
                            shadow=theme.SHADOW_MD,
                        ),
                        on_press=submit,
                    ),
                ],
                alignment=ft.MainAxisAlignment.END,
                spacing=10,
            ),
        ],
        spacing=8,
        width=430,
        tight=True,
    )

    holder = modal(content, on_dismiss=close)
    page.overlay.append(holder)
    page.update()
