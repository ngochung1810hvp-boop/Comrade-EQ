"""ft.run entry point — routes between the 3 Comrade Curve screens by
state.screen, per BUILD_PLAN.md section 3 and the handoff's "Navigation"
behavior (Welcome -> Device Setup -> Tune, Back returns Device -> Welcome).
"""

import os

import flet as ft

import theme
from audio_devices import list_output_devices
from headphone_index import build_index
from profile_store import ProfileStore
from state import AppState
from ui.device_setup import device_setup_screen
from ui.tune.screen import tune_screen
from ui.welcome import welcome_screen

MEASUREMENTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "measurements")


def main(page: ft.Page) -> None:
    page.title = "Comrade Curve"
    page.bgcolor = theme.PAPER
    page.fonts = theme.FONT_FILES
    page.theme = theme.theme()
    page.padding = 0
    if not page.web:
        # ft.Window controls the native OS window and isn't meaningful in a
        # browser tab (used for flet run -w screenshots during development).
        page.overlay.append(
            ft.Window(
                width=1240,
                height=824,
                min_width=1100,
                min_height=720,
            )
        )

    state = AppState()
    entries = build_index(MEASUREMENTS_DIR)
    devices = list_output_devices()
    # Preselect the OS default output so only the headphone pick is required.
    state.device = next((d for d in devices if d.is_default), None)
    # GD3: resume the most recently saved profile as the active taste memory.
    state.profile = ProfileStore().load_latest()
    if state.profile is not None:
        state.profile_name = state.profile.name

    def render() -> None:
        page.controls.clear()
        if state.screen == "welcome":
            page.controls.append(welcome_screen(go_device, go_device))
        elif state.screen == "device":
            page.controls.append(device_setup_screen(state, entries, devices, go_welcome, go_tune))
        else:
            page.controls.append(tune_screen(page, state, devices, go_device))
        page.update()

    def go_welcome(e=None) -> None:
        state.screen = "welcome"
        render()

    def go_device(e=None) -> None:
        state.screen = "device"
        render()

    def go_tune(e=None) -> None:
        state.screen = "tune"
        render()

    render()


if __name__ == "__main__":
    ft.run(main)
