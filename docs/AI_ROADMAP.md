# Lộ trình nâng cấp AutoEq: App desktop Flet (Linux/macOS) + AI Translation Engine + Persistent Preference Memory

> Mục tiêu: app desktop **native cho Linux và macOS, UI đẹp, viết bằng Flet (thuần Python)**.
> Người dùng mô tả cảm nhận bằng ngôn ngữ tự nhiên ("bass lùng bùng", "giọng hát chói"),
> AI dịch thành tinh chỉnh PEQ cụ thể, và hệ thống **ghi nhớ gu nghe** để tự áp dụng lên
> tai nghe mới mà **không cần gọi lại AI**.

**Quyết định công nghệ (đã chốt):**
- UI: **Flet** (engine Flutter, code Python) — đóng gói `flet build macos` (.app) / `flet build linux`.
- Gọi core **in-process**: UI import thẳng `autoeq` — KHÔNG cần FastAPI server, KHÔNG dùng React.
- Webapp cũ (`webapp/main.py` + `webapp/ui`) giữ nguyên làm tham khảo logic, không phát triển tiếp.
- Bảng thuật ngữ đầy đủ cho AI: xem **[VOCABULARY.md](VOCABULARY.md)** (xây từ glossary Audiophile Term).

---

## 0. Hiện trạng codebase (đã khảo sát)

| Thành phần | Vị trí | Vai trò trong kiến trúc mới |
|---|---|---|
| `autoeq/frequency_response.py` | `FrequencyResponse.process()` | **Lớp 1** — nội suy Raw FR → Target, đã hỗ trợ tham số `sound_signature` |
| `autoeq/peq.py` | `PEQ`, `Peaking`, `LowShelf`, `HighShelf` | Lớp 1 — optimizer PEQ; `PEQ.fr` dùng để render delta thành đường cong |
| `webapp/main.py` | FastAPI `POST /equalize` | **Tham khảo**: cách nối measurement → process → PEQ (dòng ~194-242) sẽ chuyển thành hàm gọi trực tiếp |
| `webapp/ui/` | React + MUI | **Không dùng nữa** — thay bằng app Flet mới |
| `measurements/`, `targets/`, `results/` | Dữ liệu đo + target chuẩn | Nguồn baseline cho app |

**Phát hiện then chốt:** `sound_signature` là một đường cong FR được cộng đè lên target trước khi
optimize PEQ. Lớp 3 (Memory) **không cần cơ chế mới ở core** — chỉ cần lưu "gu nghe" dưới dạng
đường cong này và truyền vào `FrequencyResponse.process()` mỗi lần chọn tai nghe mới.

---

## 1. Kiến trúc 3 lớp (trong một app Python duy nhất)

```
┌──────────────────────────────────────────────────────────────┐
│  app/  — Flet UI (native Linux/macOS)                        │
│  [Chọn tai nghe] [Đồ thị FR] [Chat cảm nhận] [A/B] [Export]  │
└──────────────┬───────────────────────────────┬───────────────┘
               │ gọi hàm trực tiếp             │
┌──────────────▼───────────────┐  ┌────────────▼───────────────┐
│ LỚP 2: app/ai_engine/        │  │ LỚP 3: app/profile_store.py│
│ interpret(feedback, ctx)     │  │ profiles/<tên>.json        │
│ LLM → tag ngữ nghĩa →        │  │ - preference_curve (FR)    │
│ vocabulary.py → deltas       │  │ - filter_deltas + history  │
│ Provider: API key | Ollama   │  │ load/merge/render          │
└──────────────┬───────────────┘  └────────────┬───────────────┘
               │ delta đã clamp                │ curve tự động
┌──────────────▼───────────────────────────────▼───────────────┐
│ LỚP 1: autoeq (core, KHÔNG SỬA)                              │
│ FrequencyResponse.process(target, sound_signature=curve)     │
│ → optimize PEQ → xuất EqualizerAPO / Wavelet / Peace ...     │
└──────────────────────────────────────────────────────────────┘
```

Nguyên tắc phân tách: **Base EQ** (tai nghe × target) tính lại được bất kỳ lúc nào từ Lớp 1.
**User Preference Delta** sống độc lập ở Lớp 3 — đổi tai nghe, đổi target vẫn giữ nguyên gu.

---

## 2. Giai đoạn 0 — Khung app Flet · ~1.5 tuần

1. Scaffold `app/` với Flet: cửa sổ chính, theme Material 3 + dark mode, layout 2 cột
   (điều khiển | đồ thị).
2. **Chọn tai nghe**: đọc index từ `measurements/` (autocomplete ~5000 model); chọn target
   từ `targets/`.
3. **Gọi core in-process**: port logic từ `webapp/main.py` `/equalize` thành
   `app/equalize.py::compute(measurement, target, options) -> (fr, peq)`.
4. **Đồ thị FR**: Flet `LineChart` (raw / target / equalized / PEQ tổng); tooltip theo tần số.
5. **Export**: tái dùng nguyên các hàm ghi EqualizerAPO GraphicEQ, Parametric CSV, Wavelet của core.
6. **Đóng gói thử sớm** (đừng để cuối): `flet build linux` + `flet build macos` chạy được
   trên cả 2 HĐH với đường dẫn dữ liệu đóng gói đúng.

> Kết thúc GĐ0: app desktop thay thế được webapp cho luồng cơ bản chọn-tai-nghe → EQ → export.

## 3. Giai đoạn 1 — Nền móng Memory (chưa cần AI) · ~1 tuần

Làm Memory trước AI: khi Lớp 3 chạy được bằng tay, Lớp 2 chỉ việc "đổ" delta vào đúng chỗ.

1. **Schema profile** `profiles/<tên>.json`:

```json
{
  "version": 1,
  "profile_name": "default",
  "updated_at": "2026-07-15T00:00:00Z",
  "preference_curve": {
    "frequency": [20, 50, 100, 200, "...", 20000],
    "raw": [0.0, 1.5, 0.8, -1.2, "...", 0.0]
  },
  "filter_deltas": [
    { "tag": "mud", "type": "PEAKING", "fc": 300, "q": 1.2, "gain": -2.0,
      "scope": "global", "source": "ai", "weight": 0.8 }
  ],
  "history": [
    { "ts": "...", "headphone": "HD 650", "feedback": "giọng hát hơi chói",
      "tags": ["harsh"], "applied": [{ "fc": 4500, "q": 2.0, "gain": -1.5 }],
      "accepted": true }
  ]
}
```

   - `preference_curve` = **dạng để apply** (truyền thẳng vào `sound_signature`).
   - `filter_deltas` = **dạng nguồn có ngữ nghĩa** (hiển thị, chỉnh sửa, suy giảm trọng số);
     trường `tag` khớp enum trong [VOCABULARY.md](VOCABULARY.md).
   - Curve = render tổng filter_deltas trên lưới tần số chuẩn bằng `PEQ.fr` có sẵn.

2. **`app/profile_store.py`**: class `ProfileStore` — load/save JSON (atomic write),
   `render_curve()`, `merge_delta()` (EMA), `as_sound_signature() -> FrequencyResponse`.
3. **Wire vào GĐ0**: toggle "Áp dụng gu nghe của tôi" → `compute(..., sound_signature=profile.as_sound_signature())`.
4. **Kiểm chứng**: 2 tai nghe khác nhau + 1 profile → cả 2 kết quả PEQ đều nghiêng theo gu.

> Kết thúc GĐ1: tính năng "nhớ và tự apply" hoạt động hoàn chỉnh, dù delta còn nhập tay.

## 4. Giai đoạn 2 — AI Translation Engine · ~2 tuần

1. **Provider trừu tượng** `app/ai_engine/providers/`:
   - `base.py`: `interpret(feedback, context) -> InterpretResult`
   - `anthropic_provider.py` (API key) và `openai_compat.py` — dùng chung cho OpenAI,
     **LM Studio**, **Ollama** (endpoint OpenAI-compatible `http://localhost:11434/v1`).
   - API key đọc từ keyring HĐH / file config local — không hard-code, không commit.
   - Model local đề xuất: Qwen 2.5 7B-instruct hoặc Llama 3.1 8B — đủ cho phân loại + điền schema.

2. **LLM trả về ngữ nghĩa, KHÔNG trả trực tiếp Hz/Q** — hai tầng:
   - **Tầng LLM** (structured output / tool-use): phân loại feedback thành tag thuộc **enum đóng**
     định nghĩa trong [VOCABULARY.md](VOCABULARY.md) (3 nhóm: A — sinh filter trực tiếp,
     B — hỗ trợ gián tiếp, C — ngoài khả năng EQ, phải giải thích trung thực):

```json
{ "adjustments": [
  { "tag": "mud", "direction": "reduce", "intensity": 0.6,
    "quote": "bass hơi lùng bùng" }
], "clarify": false }
```

   - **Tầng ánh xạ tất định** `app/ai_engine/vocabulary.py`: sinh từ bảng trong VOCABULARY.md —
     tag → (dải tần, loại filter, fc, Q, base_gain). Gain = `intensity × base_gain`.
     Kèm quy tắc xung đột/mơ hồ (mục cuối VOCABULARY.md): thuật ngữ đa nghĩa → `clarify: true`
     để UI hỏi lại; tag Nhóm C → không sinh filter, hiển thị giải thích.

3. **Safety clamps (ngoài LLM):** |gain| ≤ 6 dB/filter, tổng chồng lấn ≤ 9 dB, Q ∈ [0.3, 6],
   fc ∈ [20, 20000]; tính lại preamp sau mỗi lần apply.
4. **`app/ai_engine/engine.py`**: `propose(feedback, headphone, current_peq, profile) -> Proposal`
   — **chỉ đề xuất, chưa apply**.
5. **UI Flet**: panel chat cảm nhận + card đề xuất (đồ thị trước/sau, giải thích, tag) +
   nút **Chấp nhận / Bỏ qua**.
6. **Nghe thử A/B**: convolve nhạc mẫu bằng `scipy.signal.fftconvolve` với FIR từ core
   (`minimum_phase_impulse_response`), phát qua `sounddevice`; nút gạt A/B chuyển mượt.

## 5. Giai đoạn 3 — Học tích luỹ (khép vòng) · ~1 tuần

1. **Chấp nhận** đề xuất → ghi `history` + merge vào `filter_deltas`:
   - Cùng tag đã có → EMA: `gain_mới = α·gain_đề_xuất + (1−α)·gain_cũ` (α ≈ 0.4).
   - Tag mới → `weight` khởi điểm 0.5, tăng dần mỗi lần được xác nhận lại.
2. **Bỏ qua/hoàn tác** cũng ghi history (tín hiệu âm) → giảm weight tag tương ứng.
3. Re-render `preference_curve` sau mỗi merge → lần sau chọn tai nghe mới, curve tự áp,
   **không gọi LLM**.
4. **`scope` của delta**: mặc định `global` (gu chung); nếu một tag chỉ xuất hiện với 1 tai nghe
   mà không lặp ở tai khác → hạ về `scope: "headphone:HD 650"` (lỗi của tai đó, không phải gu).

## 6. Giai đoạn 4 — Hoàn thiện · ~1-2 tuần

- **Đa profile**: theo thể loại nhạc / hoàn cảnh (EDM, Jazz, xem phim) — mỗi profile 1 file JSON.
- **Settings**: chọn provider (Anthropic / OpenAI / Ollama local), nhập API key (keyring HĐH,
  fallback file config có cảnh báo).
- **Blind A/B test mode**: phát ngẫu nhiên bản có/không có preference delta — chống placebo,
  đồng thời là tín hiệu weight chất lượng cao.
- **Gợi ý chủ động**: thống kê history ("Bạn thường giảm 3–5 kHz, áp mặc định −1.5 dB
  cho tai nghe mới?").
- **Phân phối**: Linux — AppImage/Flatpak; macOS — codesign + notarize `.app` (cần Apple
  Developer ID nếu chia sẻ cho người khác; chạy máy mình thì bỏ qua).

## 7. Rủi ro & đối sách

| Rủi ro | Đối sách |
|---|---|
| LLM bịa số Hz/Gain vô lý | LLM chỉ trả tag trong enum đóng (VOCABULARY.md); số liệu do ánh xạ tất định + clamp |
| Người dùng yêu cầu điều EQ không làm được (soundstage, speed...) | Nhóm C trong VOCABULARY.md: từ chối sinh filter, giải thích trung thực + gợi ý thay thế |
| Delta tích luỹ phình to, méo tiếng | Giới hạn tổng gain, EMA, blind A/B để xác nhận |
| Gu nghe thực ra là lỗi của 1 tai nghe | Cơ chế `scope` tách delta theo tai nghe vs gu chung |
| `LineChart` của Flet thiếu tương tác sâu | Đủ cho đường cong EQ; nếu cần thì nhúng Plotly qua WebView |
| Audio A/B không còn Web Audio | `sounddevice` + `fftconvolve`; core đã có sẵn hàm sinh FIR |
| Build native cần Flutter SDK | Chỉ cần trên máy build; CI GitHub Actions build cho cả 2 HĐH |
| Python core yêu cầu `>=3.8,<3.12` | Cố định môi trường 3.11 cho toàn app |
| Lộ API key | Keyring HĐH, không commit; Ollama local = không cần key |

## 8. Thứ tự triển khai (tóm tắt, ~6-7 tuần)

1. **GĐ0** Khung Flet: chọn tai nghe → EQ → đồ thị → export, đóng gói thử Linux/macOS sớm
2. **GĐ1** ProfileStore + `sound_signature` wiring → *tính năng nhớ chạy được ngay*
3. **GĐ2** LLM provider + vocabulary (enum từ VOCABULARY.md) + UI chat + A/B preview
4. **GĐ3** Vòng lặp học: accept/reject → merge EMA → auto-apply
5. **GĐ4** Đa profile, settings key, blind A/B, đóng gói phân phối
