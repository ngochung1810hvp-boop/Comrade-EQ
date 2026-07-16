# BUILD PLAN — Comrade Curve (Auto EQ Studio)

> **Plan tổng hợp nhất**, thay thế vai trò điều phối của [AI_ROADMAP.md](AI_ROADMAP.md).
> Ba tài liệu nguồn:
> - **Design handoff**: [design_handoff_comrade_curve/README.md](design_handoff_comrade_curve/README.md) + prototype `comrade-curve.dc.html` — spec UI high-fidelity, implement bám sát pixel.
> - **Kiến trúc & AI**: [AI_ROADMAP.md](AI_ROADMAP.md) — 3 lớp, provider LLM, memory.
> - **Từ vựng AI**: [VOCABULARY.md](VOCABULARY.md) — enum tag đóng cho LLM.

**Ngày lập:** 2026-07-16 · **Hiện trạng:** chưa có code app mới (`app/` chưa tồn tại); core `autoeq` + dữ liệu `measurements/`, `targets/` sẵn sàng.

---

## 1. Quyết định đã chốt (không bàn lại)

| Hạng mục | Quyết định |
|---|---|
| UI framework | **Flet** (Flutter engine, thuần Python) — KHÔNG React. Handoff README gợi ý React là default chung của định dạng handoff, **bỏ qua gợi ý đó**; tái tạo design bằng Flet. |
| Nền tảng đích | Desktop native **Linux + macOS** (`flet build linux` / `flet build macos`); dev trên Windows chạy `flet run` bình thường. |
| Gọi core | **In-process** — import thẳng `autoeq`, không FastAPI. `webapp/` giữ làm tham khảo logic. |
| AI | LLM chỉ trả **tag ngữ nghĩa** (enum trong VOCABULARY.md), ánh xạ sang filter là tất định + clamp. Provider: Anthropic API / OpenAI-compatible (Ollama, LM Studio). |
| Memory | Preference delta lưu ở Lớp 3, render thành `sound_signature` curve truyền vào `FrequencyResponse.process()` — core không sửa. |
| Design | **Comrade Curve** là spec chính thức của UI: 3 màn hình Welcome → Device Setup → Tune, đúng token màu/chữ/spacing trong handoff. |
| Python | Cố định **3.11** (core yêu cầu `>=3.8,<3.12`). |

## 2. Điều chỉnh design khi chuyển sang app native

Prototype vẽ một "cửa sổ giả" 1240×824 nằm trên nền desk `#efece6`. Với app native:

1. **Bỏ window card giả + 3 nút traffic-light + title bar tự vẽ** — dùng cửa sổ HĐH thật. Nội dung bên trong (padding, radius card, màu paper `#fdfcfa`) giữ nguyên. Kích thước cửa sổ mặc định 1240×824, min 1100×720, cho resize (layout flex đã sẵn co giãn: rail cố định 66px, panel DAC cố định 296px, cột giữa co giãn).
2. **Dot trạng thái DAC + tên thiết bị** (góc phải title bar cũ) → chuyển vào header của màn Tune / panel DAC.
3. **Logo/app mark đang để trống** (handoff ghi rõ) → cần thiết kế mark gốc; tạm dùng placeholder hình học đơn sắc ink, việc chốt logo là task riêng ở GĐ cuối.
4. **Font**: Newsreader (Google Fonts, OFL) + Geist / Geist Mono (Vercel, OFL) — bundle vào app qua `ft.app(...)` fonts config, không phụ thuộc font hệ thống.
5. **"EXCLUSIVE" mode** trên panel DAC: macOS (hog mode) và Linux (ALSA direct) khả thi ở mức khác nhau → GĐ đầu hiển thị trạng thái read-only/best-effort, không hứa toggle được.

## 3. Kiến trúc (giữ nguyên 3 lớp của AI_ROADMAP)

```
app/
├── main.py                  # ft.app entry, routing 3 screen theo state
├── theme.py                 # design tokens (mục 4) → ft.Theme + hằng số
├── ui/
│   ├── welcome.py           # Screen 1
│   ├── device_setup.py      # Screen 2
│   ├── tune/                # Screen 3
│   │   ├── screen.py        # layout rail | main | dac_panel
│   │   ├── graph.py         # đồ thị FR (canvas)
│   │   ├── band_strip.py    # 10 fader kéo dọc + detail row
│   │   ├── export_bar.py
│   │   ├── dac_panel.py
│   │   ├── chat_drawer.py   # GĐ4 gắn AI thật, trước đó disabled/canned
│   │   └── save_modal.py
│   └── widgets.py           # chip, pill toggle, toast, dropdown menu...
├── state.py                 # AppState (mirror mục State Management của handoff)
├── equalize.py              # port webapp/main.py::/equalize → compute() in-process
├── audio_devices.py         # liệt kê output device (sounddevice), sample rate/bit depth
├── profile_store.py         # LỚP 3 — profiles/<tên>.json
└── ai_engine/               # LỚP 2
    ├── engine.py            # propose() — chỉ đề xuất
    ├── vocabulary.py        # sinh từ VOCABULARY.md: tag → filter tất định
    └── providers/           # base / anthropic / openai_compat (Ollama, LM Studio)
```

**Mô hình band (hòa giải design ↔ core):** UI giữ đúng **10 band cố định** như design
(log-spaced 25 Hz–16 kHz; band đầu LOW_SHELF, band cuối HIGH_SHELF, còn lại PEAKING,
gain ±12 dB, auto-fit clamp ±9 dB). `bands` là source of truth của UI; khi cần render
đường EQ/preamp thì đổ vào `autoeq.peq.PEQ` để tính `PEQ.fr`. **Auto-fit** = chạy
optimizer của core với layout 10 band cố định fc/type (optimize gain, Q trong khoảng hẹp)
— chính xác hơn cách "lấy hiệu target−raw tại fc" của prototype; fallback đơn giản đó
dùng làm bước 1 nếu optimizer chậm.

## 4. Ánh xạ design token → Flet

| Token handoff | Cách làm trong Flet |
|---|---|
| Ink `#131210`, paper `#fdfcfa`, green `#c8e6cd`, coral `#f3c9b6`, border ≈7% ink | Hằng số trong `theme.py`; KHÔNG dùng màu Material mặc định |
| Newsreader / Geist / Geist Mono | `page.fonts = {...}` bundle file .ttf; 3 text style helper: `serif()`, `sans()`, `mono()` với size/letterspacing đúng spec |
| Shadow xs→xl | `ft.BoxShadow` layered; card nghỉ dùng shadow nhẹ thay vì border |
| Radius: card 12, button 7–10, pill full | Hằng số trong theme.py |
| Press `scale(0.97)` / icon `0.94` | `animate_scale` trên `on_tap_down`/`on_tap_up` — làm 1 wrapper `Pressable` dùng chung |
| Drawer/modal/toast transitions 200–420ms, ease-drawer cubic-bezier | `animate_offset`/`animate_opacity` với `ft.AnimationCurve`; chat drawer = `Stack` overlay + scrim, KHÔNG dùng `NavigationDrawer` mặc định |
| Đồ thị SVG 1000×300, log-x, 4 đường | `ft.canvas.Canvas` vẽ Path trực tiếp (kiểm soát hoàn toàn màu/dash/legend); KHÔNG dùng `LineChart` vì thiếu log-axis + dashed style |
| Fader kéo dọc 10 band | `GestureDetector` (`on_vertical_drag_update`) trên track 120px, map pixel→gain bước 0.5 dB |
| Icon SVG stroke đơn giản | `ft.Image(src=...svg)` từ bộ icon tự vẽ trong repo (extract từ prototype) |

## 5. Lộ trình theo giai đoạn (~7 tuần)

### GĐ0 — Design system + app shell · ~1 tuần
1. Scaffold `app/` + `theme.py` đầy đủ token, bundle 3 font.
2. Bộ widget dùng chung: `Pressable`, chip, pill toggle, dropdown menu nổi, toast, modal scale-in — **đúng motion spec** ngay từ đầu (làm sau sẽ không bao giờ làm).
3. Routing 3 screen theo `state.screen`; khung Welcome tĩnh hoàn chỉnh (eyebrow, H1 với chữ "ask" trong pill xanh, 2 nút, 3 cột feature, nền wavy SVG).
4. **Đóng gói thử sớm**: `flet build linux` + `flet build macos` với font/asset bundle đúng đường dẫn.

> Nghiệm thu: Welcome giống prototype khi đặt cạnh nhau; app build được trên cả 2 HĐH.

### GĐ1 — Device Setup + dữ liệu thật · ~1 tuần
1. Index tai nghe từ `measurements/` (~5000 model, kèm nguồn đo làm meta line) → search list cột trái, chọn kiểu circular check đúng design.
2. `audio_devices.py`: liệt kê output device qua `sounddevice` (tên, loại, sample rate) → cột phải + callout "WHY IT MATTERS".
3. Footer pairing summary + "Start tuning" → sang Tune.
4. `equalize.py::compute(measurement, target, options)` port từ `webapp/main.py` (dòng ~194-242) — chạy được từ test, chưa cần UI.

### GĐ2 — Màn Tune hoàn chỉnh (chưa AI) · ~2 tuần
1. Layout rail 66px | main | DAC panel 296px; header tên tai nghe + badge signature + TARGET dropdown + EQ on/off pill.
2. **Graph card**: canvas 4 đường (measured coral / target dashed / EQ green / result ink), gridline log 20 Hz–20 kHz, ±12 dB, legend + toggle SMOOTHED (dùng smoothing sẵn có của core).
3. **10-band strip**: drag gain, chọn band → detail row (fc slider log, Q slider 0.3–6, gain readout màu theo dấu); Auto-fit (optimizer core, clamp ±9 dB) + Reset; toast xác nhận.
4. **Export bar**: chip 4 định dạng (Parametric CSV / GraphicEQ 10-band / EqualizerAPO / AUNBandEq), preamp tự tính `-(max boost + 0.4 dB)`, nút Export ghi file bằng hàm core.
5. **DAC panel**: device picker dropdown (sync với lựa chọn ở Device Setup), stat SAMPLE/DEPTH/EXCLUSIVE (read-only).
6. **Save profile modal** (mới chỉ lưu tên + bands + target + preamp — schema đầy đủ ở GĐ3).

> Nghiệm thu: thay thế hoàn toàn webapp cho luồng chọn tai nghe → tune tay → export. Đây là mốc app "dùng được thật".

### GĐ3 — Memory (Lớp 3) · ~1 tuần
1. Schema `profiles/<tên>.json` đúng AI_ROADMAP §3: `preference_curve` (dạng apply) + `filter_deltas` (dạng ngữ nghĩa, tag khớp VOCABULARY) + `history`.
2. `ProfileStore`: atomic write, `render_curve()` (dùng `PEQ.fr`), `merge_delta()` EMA, `as_sound_signature()`.
3. Toggle "Áp dụng gu nghe" trong Tune → `compute(..., sound_signature=...)`; Save modal nâng cấp ghi profile đầy đủ.
4. Kiểm chứng: 1 profile áp lên 2 tai nghe khác nhau đều nghiêng theo gu.

### GĐ4 — AI chat drawer (Lớp 2) · ~2 tuần
1. Providers: `anthropic_provider` + `openai_compat` (Ollama `http://localhost:11434/v1`, LM Studio); key qua keyring HĐH. Model local đề xuất: Qwen 2.5 7B / Llama 3.1 8B.
2. LLM → structured output tag enum (Nhóm A/B/C của VOCABULARY.md, `clarify` khi mơ hồ); `vocabulary.py` ánh xạ tất định; clamp |gain|≤6 dB/filter, tổng ≤9 dB, Q∈[0.3,6].
3. **Chat drawer đúng design**: FAB pill → drawer 392px slide-in + scrim; bubble user/assistant; đề xuất hiển thị **card "APPLIED" viền xanh + link ↺ undo** (undo = restore snapshot band gains, đúng cơ chế prototype); 4 suggestion chip; Nhóm C → trả lời giải thích, không sinh filter.
4. Áp đề xuất = đổ delta vào 10 band hiện tại (cùng vùng tần) — người dùng thấy fader nhảy, nhất quán với canned behavior của prototype.
5. **Nghe thử A/B**: FIR từ `minimum_phase_impulse_response` + `fftconvolve`, phát qua `sounddevice`.

### GĐ5 — Học tích luỹ + hoàn thiện · ~1-1.5 tuần
1. Accept/undo → ghi `history`, merge EMA (α≈0.4), weight tăng/giảm; re-render `preference_curve` → tai nghe mới tự áp, **không gọi LLM**.
2. `scope` delta: global vs `headphone:<tên>` (tag chỉ lặp ở 1 tai → là lỗi tai đó, không phải gu).
3. Đa profile (EDM/Jazz/phim), Settings chọn provider + key, blind A/B test mode, gợi ý chủ động từ thống kê history.
4. App mark/logo chính thức (đang trống); phân phối: AppImage/Flatpak (Linux), codesign+notarize (macOS, cần Apple Developer ID nếu chia sẻ).

## 6. Rủi ro mới so với roadmap cũ

| Rủi ro | Đối sách |
|---|---|
| Flet không đạt độ fidelity của design (shadow, easing, serif) | GĐ0 làm design system trước và nghiệm thu bằng so sánh cạnh prototype; chỗ nào Flet bó tay thì ghi nhận deviation có chủ đích, không âm thầm hạ chất lượng |
| Fader drag + canvas chart hiệu năng kém khi redraw liên tục | Throttle update ~60fps, chỉ redraw path thay đổi |
| `sounddevice` không lấy được bit depth / exclusive mode | Hiển thị "—" khi không đọc được; exclusive để read-only best-effort (mục 2.5) |
| 10 band cố định không khớp kết quả optimizer tự do của core | Optimizer chạy chế độ fc/type cố định (core hỗ trợ cấu hình filter); export "Custom Parametric Eq" có thể dùng optimizer tự do đầy đủ |
| Prototype có behavior đã bị gỡ (volume knob, auto-preamp toggle) | KHÔNG tự thêm lại — handoff dặn confirm với design trước |
| Các rủi ro AI/memory | Giữ nguyên bảng đối sách AI_ROADMAP §7 |

## 7. Handoff cho session sau (bắt đầu code từ đâu)

1. **Đọc theo thứ tự**: file này → design handoff README → AI_ROADMAP §0-1 (hiện trạng core) → VOCABULARY.md (khi làm GĐ4).
2. **Mở prototype** `docs/design_handoff_comrade_curve/comrade-curve.dc.html` trong browser làm chuẩn so sánh trực quan (không copy code).
3. **Bắt đầu GĐ0**: tạo `app/theme.py` + `app/ui/widgets.py` trước, tải 3 font OFL vào `app/assets/fonts/`.
4. **Môi trường**: venv Python 3.11, `pip install -e .` (core) + `flet`, `sounddevice`, `scipy`, `keyring`.
5. **Điều chưa chốt, cần hỏi user khi chạm tới**: logo/app mark; danh sách target curve nào hiện trong TARGET dropdown (mặc định lấy từ `targets/`); có làm tiếng Việt cho UI hay giữ copy tiếng Anh của design (prototype toàn tiếng Anh).
