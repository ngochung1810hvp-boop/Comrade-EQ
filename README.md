# Comrade EQ

**Comrade Curve** — a desktop parametric-EQ studio for headphones. Pick your headphones and DAC, tune a 10-band parametric EQ against a target curve, and export the correction to common EQ apps. An assistant drawer (in development) adjusts EQ bands from plain-language requests like *"more bass"* or *"warmer vocals"*.

Built on the measurement data and DSP core of [AutoEq](https://github.com/jaakkopasanen/AutoEq) by Jaakko Pasanen.

> **Status: early development.** The app shell, design system, device setup flow, and the in-process equalization core are working. The main tuning workspace (graph, band faders, export) is the current milestone. See [Roadmap](#roadmap).

## What works today

- **Welcome & Device Setup screens** — search 6,800+ headphone measurements (oratory1990, crinacle, Rtings, Innerfidelity, and more), pick an output device (detected via PortAudio/WASAPI), and pair them.
- **Equalization core** — `app/equalize.py` computes correction curves in-process using AutoEq's `FrequencyResponse` (no server, no web stack).
- **Design system** — warm paper/ink palette, Newsreader + Geist typography, motion tokens; implemented pixel-close to the Comrade Curve design spec in `docs/design_handoff_comrade_curve/`.

## Requirements

- **Python 3.11** (the AutoEq core pins `>=3.8,<3.12`)
- Windows, Linux, or macOS. Desktop packaging targets Linux and macOS (`flet build`); development runs anywhere via `flet run`.

## Getting started

```bash
git clone https://github.com/ngochung1810hvp-boop/Comrade-EQ.git
cd Comrade-EQ

python3.11 -m venv .venv
# Windows: .venv\Scripts\activate    Linux/macOS: source .venv/bin/activate

pip install -e ".[app]"
flet run app/main.py
```

To run the tests:

```bash
pip install pytest pandas
pytest tests/
```

## Project structure

```
app/            Comrade Curve desktop app (Flet)
├── main.py         entry point + screen routing
├── theme.py        design tokens (colors, type, motion)
├── state.py        app state + 10-band EQ model
├── equalize.py     in-process port of the AutoEq webapp's /equalize
├── headphone_index.py  index/search over measurements/
├── audio_devices.py    output device listing (sounddevice)
└── ui/             screens and shared widgets
autoeq/         AutoEq DSP core (unmodified)
measurements/   headphone frequency-response measurements (~6,800)
targets/        target curves (Harman, diffuse field, …)
webapp/         AutoEq's web API, kept as reference for ports
docs/           build plan, AI roadmap, design handoff
```

Precomputed AutoEq results are **not** included — the app computes corrections live. They remain available in the [upstream repository](https://github.com/jaakkopasanen/AutoEq).

## Roadmap

| Phase | Scope | Status |
|---|---|---|
| 0 | Design system, app shell, Welcome screen | ✅ done |
| 1 | Device Setup with real data, equalization core | ✅ done |
| 2 | Tune workspace: FR graph, 10-band faders, auto-fit, export (Parametric CSV / GraphicEQ / EqualizerAPO / AUNBandEq), DAC panel | ⏳ next |
| 3 | Sound-preference memory (profiles that carry across headphones) | planned |
| 4 | Assistant chat drawer: natural language → EQ adjustments (Anthropic API or local models via Ollama / LM Studio), A/B listening | planned |
| 5 | Preference learning, multi-profile, packaging (AppImage/Flatpak, notarized macOS) | planned |

Details live in [`docs/BUILD_PLAN.md`](docs/BUILD_PLAN.md).

## Credits & license

- **[AutoEq](https://github.com/jaakkopasanen/AutoEq)** (MIT) by Jaakko Pasanen — DSP core, measurement archive, and target curves. This repository retains its [MIT license](LICENSE).
- Measurement data by [oratory1990](https://www.reddit.com/r/oratory1990/), [crinacle](https://crinacle.com/), [Rtings](https://www.rtings.com/), [Innerfidelity](https://www.stereophile.com/content/innerfidelity-headphone-measurements), [Kuulokenurkka](https://kuulokenurkka.fi/), [Headphone.com](https://headphones.com/) and other sources credited per entry in the app.
- Fonts: [Newsreader](https://fonts.google.com/specimen/Newsreader) (Production Type) and [Geist / Geist Mono](https://vercel.com/font) (Vercel), both under the SIL Open Font License.
