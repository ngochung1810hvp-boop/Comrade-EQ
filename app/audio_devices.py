"""Output audio device listing via sounddevice (BUILD_PLAN.md GD1.2).

Bit depth / exclusive-mode status are not reliably readable through
PortAudio; per BUILD_PLAN.md section 2.5 those render as "—" until a
platform-specific path exists.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class AudioDevice:
    index: int
    name: str
    hostapi: str
    sample_rate: int
    is_default: bool

    @property
    def meta(self) -> str:
        return f"{self.hostapi} · {self.sample_rate / 1000:g} kHz"


def list_output_devices() -> list[AudioDevice]:
    """Returns output-capable devices, default device first. Empty list if
    PortAudio has no devices or sounddevice fails to load.

    PortAudio exposes every physical device once per host API (and MME
    truncates names to 31 chars), so the list is restricted to a single
    host API: WASAPI when available (Windows), else the default output's.
    """
    try:
        import sounddevice as sd

        hostapis = sd.query_hostapis()
        default_output = sd.default.device[1]
        preferred = next(
            (i for i, h in enumerate(hostapis) if "WASAPI" in h["name"]),
            sd.query_devices(default_output)["hostapi"] if default_output >= 0 else 0,
        )
        hostapi_default = hostapis[preferred]["default_output_device"]
        devices = []
        for i, d in enumerate(sd.query_devices()):
            if d["max_output_channels"] <= 0 or d["hostapi"] != preferred:
                continue
            devices.append(AudioDevice(
                index=i,
                name=d["name"],
                hostapi=hostapis[preferred]["name"],
                sample_rate=int(d["default_samplerate"]),
                is_default=i == hostapi_default,
            ))
        devices.sort(key=lambda d: not d.is_default)
        return devices
    except Exception:
        return []
