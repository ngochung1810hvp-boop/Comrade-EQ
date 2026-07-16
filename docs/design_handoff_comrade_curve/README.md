# Handoff: Comrade Curve (Auto EQ Studio)

## Overview
A desktop parametric-EQ app for headphones: pick your headphones + DAC, tune a 10-band parametric EQ against a target curve, and export the correction to common EQ apps. Includes a chat-style "assistant" drawer that adjusts EQ bands from natural-language requests ("more bass", "warmer vocals").

## About the Design Files
The bundled HTML file (`comrade-curve.dc.html`) is a **design reference built in a proprietary prototyping format** (custom template syntax, inline styles, a lightweight component runtime) — it is not production code and should not be copied as-is. Treat it as a high-fidelity spec: recreate the same screens, layout, styling, and interactions in the target codebase's actual stack (React/Vue/native/etc.), using that codebase's existing component patterns, state management, and design tokens where they overlap with what's described below. If no frontend framework exists yet in the target repo, React is a reasonable default given the component-oriented structure of this design.

## Fidelity
**High-fidelity.** Colors, type, spacing, radii, shadows, and copy below are final values pulled directly from the working prototype — implement pixel-close, not just directionally.

## Design System Basis
Built on the "Hung Pham" personal design system: warm off-white paper background, warm near-black ink text, two pastel accent "blocks" (soft green `#c8e6cd` and warm coral `#f3c9b6`), Newsreader serif for display/headings, Geist sans for UI, Geist Mono for labels/numbers. Strong custom easing curves, sub-300ms UI transitions, `scale(0.97)` press feedback on every clickable element, and depth via soft layered shadows rather than borders.

## Screens / Views

The whole app lives inside a fixed "window" card: **1240×824px**, `border-radius: 16px`, drop shadow `0 40px 90px -30px rgba(19,18,16,.45)` + a 1px hairline ring, centered on a `#efece6` desk background. A 44px title bar with 3 traffic-light dots (red/amber/green, decorative only), centered app name "Comrade Curve" (12px mono, `--text-tertiary`), and a right-aligned DAC-connection dot + device name sits atop all 3 screens.

### 1. Welcome
**Purpose:** Landing/intro screen; entry point to the flow.
**Layout:** Full-height centered column, max-width 640px, over two faint decorative wavy SVG lines (coral/green, 55%/70% opacity) as background texture.
- 60×60px ink-colored rounded-square icon badge (14px radius) — currently empty after logo removal; needs an app mark.
- Mono eyebrow, 11px, letterspacing .14em, `--text-tertiary`: "TUNE · LISTEN · SHAPE BY EAR"
- Serif H1, 52px/1.08, letterspacing -.025em: "Tune your headphones — or just **ask** in plain words." (the word "ask" sits in a green highlight-block pill, 3px radius)
- Body paragraph, 16px/1.6, `--text-secondary`, max-width 520px, with an italic serif inline emphasis on the example phrase.
- Two buttons side by side (12px gap): primary "Get started" (ink bg, white text, 46px tall, 9px radius, trailing arrow icon) and secondary "Import a profile" (bordered, card bg).
- Three-column feature list below (40px gap), each: mono tag label (10.5px, coral ink, letterspacing .1em) over a 13.5px description line. Content: "AI TUNING / Describe the sound; the curve follows.", "DAC CONTROL / Hardware volume, preamp & output device.", "5,300+ MEASURED / oratory1990, crinacle, Rtings & more."

### 2. Device Setup
**Purpose:** Step 1 of 2 — choose headphones + output DAC before tuning.
**Layout:** Header row (back button, "STEP 1 / 2 · SET UP YOUR RIG" mono eyebrow, serif 34px H2 "What are you listening on?"), then a 2-column grid (24px gap) filling remaining height, then a sticky footer bar.
- **Left column — Headphones:** label row ("HEADPHONES" mono + "5,300+ measured" counter), a search input (40px tall, 8px radius, search icon), then a scrollable list of selectable rows. Each row: name (14px/500) + meta line (11px mono, tertiary) on the left, a circular checkmark badge on the right (filled ink circle when selected, empty ring otherwise). Selected row gets a 1px ink border + shadow-sm.
- **Right column — Output device / DAC:** label "OUTPUT DEVICE · DAC", scrollable list of device rows (36×36px rounded-8px icon chip + name/type+rate meta + selection check), plus a dashed-border info callout at the bottom: "WHY IT MATTERS" (coral ink mono label) + explanatory copy about pre-DAC correction and auto preamp.
- **Footer bar:** current pairing summary text ("{headphone} → {device}") on the left, primary "Start tuning" button (ink, 42px, arrow icon) on the right.

### 3. Tune (main screen)
**Purpose:** The core EQ workspace.
**Layout:** `display:flex` — a 66px icon rail on the left, a scrollable main content column, and a 296px DAC side panel on the right. A floating chat FAB + slide-in chat drawer overlay everything; a save-profile modal overlays on top of that.

**Icon rail (66px):** vertical stack of 42×42px icon buttons (10px radius): Tune (active, filled `--surface-active` bg), Devices, Profiles/save — pushed apart from a bottom-anchored Help icon via a flex spacer.

**Main column header:** headphone name (serif 27px) + a signature badge pill (mono 10.5px, coral block bg/ink text, e.g. "Reference") + meta line (mono 11.5px tertiary, e.g. lab/measurement credit). Right side: a "TARGET" dropdown button (opens a floating menu of target curve presets) and an EQ on/off pill toggle (34×20px switch, green tint when on).

**Graph card:** white card, 12px radius, shadow-sm, with a 44×4px green accent tab at the top-left corner. Legend row (swatches: coral solid = Measured, gray dashed = Target, green solid = EQ applied, ink solid = Result) plus a "SMOOTHED" toggle chip on the right. Below: a 1000×300 viewBox SVG chart, log-frequency x-axis (20Hz–20kHz gridlines with labels: 20/50/100/200/500/1k/2k/5k/10k/20k) and dB y-axis (gridlines at +12/+6/0/-6/-12), plotting 4 paths: dashed target curve, coral raw/measured curve, green EQ-correction curve, and a bold ink "result" curve (raw+EQ summed).

**10-band Parametric EQ card:** white card, header row with "10-BAND PARAMETRIC EQ" mono label + "Auto-fit" (green outline chip) and "Reset" (neutral chip) buttons. Below: a horizontal row of 10 vertical fader "bands" (120px tall track), each is a draggable pill: a background rail, a colored fill from center (0dB) to the current gain (green = boost, coral = cut), and a pill-shaped handle. Below the faders: frequency labels per band (8.5px mono, e.g. "25", "63", "160", "1k", "16k"). Below that, a detail row for the selected band: index+type label ("BAND 05 · Peaking"), center-frequency readout (serif 20px), a Frequency slider (0–100% mapped log-scale), a Q/width slider (0.3–6), and a live gain readout (18px mono, green/coral/tertiary colored by sign).
  - Band math: 10 bands log-spaced 25Hz–16kHz; band 0 = low shelf, band 9 (last) = high shelf, all others = peaking (Q≈1.4 default, shelves Q≈0.7). Gain range ±12dB (drag), auto-fit clamps to ±9dB.

**Export bar:** single card row: "EXPORT" mono label, a horizontal set of app-target chips (Custom Parametric Eq / 10-band Graphic Eq / EqualizerAPO / AUNBandEq — selectable, selected = ink border), a right-aligned "PREAMP" readout (auto-computed from headroom), and a primary green "Export" button (triggers a toast).

**DAC side panel (296px, sunken bg):** "OUTPUT · DAC" label, a device-picker button (36×36 icon chip + name/type, opens a dropdown menu of devices with rate + selection dot), and a 3-up stat row: SAMPLE rate, bit DEPTH, and an "EXCLUSIVE" status chip (green = ON).
  - Note: the previous version of this panel also had a volume knob (radial dial, dB + % readout) and an "Auto preamp" toggle row — both were removed per the latest design iteration. Confirm with design before reintroducing.

**Chat assistant (drawer):** a floating pill FAB bottom-right ("Ask the assistant", ink bg, icon selectable via `assistantIcon` prop: in-ear / over-ear / sparkle, tinted via `accent` prop — currently coral `#f3c9b6`). Clicking opens a 392px-wide right-side drawer (slides in via transform, with a dimming scrim behind it): header with assistant icon + "Tuning assistant" title + close button; a scrollable message list (user bubbles right-aligned ink-filled, assistant bubbles left-aligned bordered-card) — assistant replies that changed the EQ show an "APPLIED" diff card (green border, title + detail + "↺ undo" link); a footer with 4 suggestion chips ("More bass", "Warmer vocals", "More air / detail", "What does Q do?") and a rounded pill text input + circular send button.

**Save profile modal:** centered 400px card (14px radius, shadow-xl, scale-in transition): "Save sound profile" serif title, description line naming the current headphone, a profile-name text input, a 2-up summary of Target + Preamp values, and Cancel / Save profile buttons.

**Toast:** bottom-center floating pill (ink bg, white text, green checkmark badge), slides up + fades in on save/export/auto-fit actions, auto-dismisses after ~2.6s.

## Interactions & Behavior
- **Navigation:** Welcome → Device Setup → Tune are three mutually-exclusive screens (no URL routing in the prototype; swap on state). Back button returns Device→Welcome.
- **Headphone/device selection:** list-row click sets selection state; both rows in the Device screen and (for output device) the dropdown in the Tune side panel stay in sync.
- **Target curve dropdown & EQ on/off toggle:** simple floating menus/toggles, closed on outside click or re-toggle.
- **Band dragging:** pointerdown on a band captures the pointer; vertical drag maps pixel delta to gain (±12dB, 0.5dB steps); releasing a band also selects it, updating the detail-row sliders.
- **Auto-fit:** computes each band's gain as the difference between the target curve and the raw measured curve at that band's center frequency, clamped ±9dB; shows a confirmation toast.
- **Reset:** zeroes all band gains.
- **Chat:** clicking a suggestion chip or typing + pressing Enter appends a user message and a canned assistant reply, and (for 3 of the 4 canned intents) applies a batch gain shift to bands within a frequency region (e.g. "more bass" → +2.5–3dB to bands ≤150Hz). Each such reply carries an "undo" action that restores a pre-change snapshot of all band gains.
- **Preamp:** auto-computed as -(max EQ boost + 0.4dB headroom) when `preampAuto` is true (state exists in logic; its UI toggle was removed from the panel — currently always effectively "auto" since there's no way to turn it off in the UI).
- **Modals/drawers:** all use opacity + transform transitions (200–300ms range) with an ease-out/ease-drawer curve; the save modal also scales in from 0.94→1.
- **Transitions:** press states use `scale(0.97)` (icon-only buttons `0.94`) on `:active`. Toggle switches and drawers use a custom "ease-drawer" cubic-bezier. Dropdown menus fade+rise in ~180ms.

## State Management
Key state needed (see prototype's single component state object for exact shape):
- `screen`: 'welcome' | 'device' | 'tune'
- `headphone`, `device`, `target`, `eqApp`: selected option objects/strings
- `bands`: array of 10 `{ fc, gain, q, type }` — the core EQ model
- `selectedBand`: index into `bands` for the detail-row controls
- `eqOn`, `smoothed`, `preampAuto`: booleans (note: preampAuto has no UI control currently)
- `chatOpen`, `saveOpen`, `outMenu`, `targetMenu`: UI open/closed flags for overlays
- `messages`: chat transcript, each optionally carrying a `diff` (title/detail) and a `snap` (band-gain snapshot for undo)
- `profileName`, `hpQuery`, `chatInput`: text field bindings
- `toastText` / toast visibility + auto-dismiss timer
- Derived/computed (not stored, recompute from state): the 4 SVG curve paths (target, raw/measured, EQ delta, result), preamp dB value, all per-row selected/unselected styling

## Design Tokens

**Colors**
- Ink (text/primary dark): `#131210`
- Page/paper background: `#fdfcfa` (app card); desk background `#efece6`
- Text secondary/tertiary: warm grays derived from ink (see `--text-secondary`, `--text-tertiary` in the design system's `colors.css`)
- Green accent block: `#c8e6cd` (bg tint), with edge/ink variants for borders and text-on-tint
- Coral accent block: `#f3c9b6` (bg tint), with edge/ink variants
- Borders: `--border-subtle` ≈ 7% ink, `--border-default`, `--border-strong`
- Functional: window traffic lights `#ec6a5e` (red), `#f4bf4f` (amber), `#61c554` (green) — decorative only

**Typography**
- Serif (display/headings): Newsreader — H1 52px/1.08, H2 34px and 27px, card titles 20–23px
- Sans (UI/body): Geist — body 13–16px, buttons 13.5–15px, all 500 weight for labels/buttons
- Mono (labels/data/numbers): Geist Mono — eyebrows 10–12px w/ letterspacing .06–.14em, data readouts 12–26px
- Letterspacing: display tight (-.02 to -.025em), eyebrows loose (+.06 to +.14em)

**Spacing / Radius**
- App window: 16px radius; cards: 12px; buttons: 7–10px; chips/pills/switches: fully round
- Card padding: 16–24px; button height 28–46px depending on prominence
- 4px spacing base throughout (gaps of 6/8/12/16/18/20/22/24px)

**Shadows**
- `--shadow-xs` / `--shadow-sm` for resting cards and rows; `--shadow-md`/`--shadow-lg` for primary buttons and floating FAB; `--shadow-xl` for popovers, modals, and the chat drawer

**Motion**
- Durations: press ~140ms, drawer/toggle ~220–300ms (`--duration-drawer`), modal ~300–420ms (`--duration-modal`)
- Easing: `--ease-out` cubic-bezier(0.23,1,0.32,1) for enters; `--ease-drawer` cubic-bezier(0.32,0.72,0,1) for toggles/drawers
- Press feedback: `transform: scale(0.97)` on buttons, `scale(0.94)`/`scale(0.92)` on icon-only controls, on `:active`

## Assets
- No photographic or bitmap assets — pure SVG line icons (hand-drawn simple stroke icons: search, chevron, arrows, headphone/speaker glyphs, checkmark, close/X, help/question mark, DAC/device box, in-ear/over-ear headphone glyphs, sparkle).
- The app's icon badge on the Welcome screen and the nav-rail brand mark were both removed at the user's request and are currently blank — a replacement app mark/logo is needed (avoid any third-party or politically-branded emblem; keep it original).
- No external images/photos used anywhere in this design.

## Files
- `comrade-curve.dc.html` — the full interactive prototype (single file, all 3 screens, chat + save-profile modal, all interaction logic).
