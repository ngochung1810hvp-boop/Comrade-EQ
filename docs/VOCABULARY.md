# Bảng ánh xạ thuật ngữ Audiophile → PEQ (Vocabulary Mapping)

> Nguồn thuật ngữ: `Audiophile Term.docx` (glossary người dùng cung cấp).
> Đây là **đặc tả cho `app/ai_engine/vocabulary.py`** — tầng ánh xạ tất định.
> LLM chỉ được phép trả về `tag` trong danh sách này (enum đóng); mọi con số Hz/Gain/Q
> do bảng này + safety clamps quyết định, không phải LLM.

## Dải tần tham chiếu (theo glossary)

| Vùng | Dải tần |
|---|---|
| Sub-Bass | 20 – 60 Hz |
| Bass | 60 – 150 Hz |
| Upper Bass | 150 – 250 Hz |
| Midrange | 250 – 3000 Hz |
| Upper Midrange | 3000 – 5000 Hz |
| Treble | 5000 – 20000 Hz |

## Quy ước

- `direction`: `reduce` (bớt) / `increase` (thêm). Gain = `direction × intensity × base_gain`.
- `intensity`: LLM ước lượng từ ngôn từ — "hơi/một chút" ≈ 0.3, "khá/rõ" ≈ 0.6, "rất/quá" ≈ 1.0.
- `base_gain` mặc định 4 dB (peaking) / 3 dB (shelf), clamp cuối: |gain| ≤ 6 dB/filter, tổng chồng lấn ≤ 9 dB, Q ∈ [0.3, 6].

---

## Nhóm A — EQ xử lý trực tiếp được (sinh filter)

| Tag | Thuật ngữ (EN) | Cảm nhận (VI) | Dải tần | Filter mặc định |
|---|---|---|---|---|
| `sub_bass_weight` | Weight, Sub-Bass, seismic, rumble | uy lực, rền sâu, "cảm được" | 20–60 Hz | LOW_SHELF 60 Hz, Q 0.7 |
| `punch` | Punch, Thump, slam, impact | độ nảy, lực đấm | 60–150 Hz | PEAKING 100 Hz, Q 1.0 |
| `boomy` | Boomy | bass ù, dội, cộng hưởng | ~125 Hz | PEAKING 125 Hz, Q 1.4 |
| `bloated` | Bloated, Thick | mid-bass phình, chậm | ~250 Hz | PEAKING 250 Hz, Q 1.4 |
| `bass_bleed` | Bass-Bleed | bass tràn che mất giọng | 150–300 Hz | PEAKING 200 Hz, Q 1.2 |
| `warmth` | Warm, Full, Lush | ấm, dày, đầy đặn | 100–300 Hz | LOW_SHELF 200 Hz, Q 0.7 |
| `thin_cool` | Thin, Cool, Dry | mỏng, lạnh, thiếu nền | < 150 Hz | LOW_SHELF 150 Hz, Q 0.7 (boost) |
| `mud` | Muddy (phần tonal) | lùng bùng, đục | 200–500 Hz | PEAKING 300 Hz, Q 1.2 |
| `boxy` | Boxy | tiếng hộp, úp tay | 250–500 Hz | PEAKING 400 Hz, Q 1.5 |
| `honky_nasal` | Honky, Nasal | giọng mũi, loa kèn | 500–700 Hz | PEAKING 600 Hz, Q 2.0 |
| `mid_recessed` | Hollow, V-Shaped, Recessed mids | giọng hát bị lùi, rỗng | 500–3000 Hz | PEAKING 1500 Hz, Q 0.8 (boost) |
| `forward_aggressive` | Forward, Aggressive, shouty | dồn vào mặt, gắt | 1–4 kHz | PEAKING 2500 Hz, Q 1.0 |
| `presence` | Presence | độ rõ, hiện diện của giọng | 3–5 kHz | PEAKING 4000 Hz, Q 1.4 |
| `harsh` | Harsh, Edgy, Grain | chói, gắt, sạn | 3–6 kHz | PEAKING 4500 Hz, Q 2.0 |
| `piercing` | Piercing, Peaky | nhức, xuyên tai | 3–10 kHz | PEAKING 8000 Hz, Q 3.0 |
| `sibilance` | Sibilant | xì chữ S/Sh, chói cymbal | 4–9 kHz | PEAKING 7000 Hz, Q 3.0 |
| `bright` | Bright, Crisp | sáng | 5–16 kHz | HIGH_SHELF 6000 Hz, Q 0.7 |
| `dark_veiled` | Dark, Veiled, Closed, Roll-Off | tối, như có màn che | > 8 kHz | HIGH_SHELF 10 kHz, Q 0.7 (boost) |
| `air` | Airy, Open, Sparkle, Brilliance, Sweet, Delicate | thoáng, lấp lánh | 10–16 kHz | HIGH_SHELF 12 kHz, Q 0.7 |

## Nhóm B — EQ hỗ trợ gián tiếp (sinh filter kèm giải thích giới hạn)

| Tag | Thuật ngữ (EN) | Chiến lược EQ | Ghi chú cho LLM |
|---|---|---|---|
| `detail_clarity` | Detailed, Analytical, Articulate, Definition, Resolving, Transparent | giảm masking 200–400 Hz (−1..2 dB) + nâng nhẹ 3–8 kHz | Chi tiết thực sự do driver quyết định; EQ chỉ "vén màn" |
| `tight` | Tight (yêu cầu bass gọn) | giảm 150–300 Hz, giữ nguyên sub-bass | Transient response không đổi được bằng PEQ |
| `smooth_relaxed` | Smooth, Laid-Back, Relaxed, non-fatiguing | giảm 2–5 kHz Q rộng + hạ nhẹ treble shelf | |
| `fatigue` | Fatigue (nghe lâu bị mệt) | giảm 3–6 kHz và 7–9 kHz mỗi vùng −1.5..2 dB | Hỏi lại người dùng mệt do chói hay do sib |
| `balance_natural` | Balance, Natural, Musical, Flat | kéo các delta hiện có về 0 theo tỷ lệ | Là tín hiệu "bớt EQ đi", không phải thêm filter |

## Nhóm C — EQ KHÔNG xử lý được (không sinh filter, phải giải thích)

| Nhóm thuật ngữ | Thuật ngữ (EN) | Phản hồi chuẩn của AI |
|---|---|---|
| Không gian | Soundstage, Headstage, Imaging, Width, Depth, Spatial Localization, Focus | PEQ không tạo được không gian; gợi ý crossfeed/DSP riêng. Có thể chào mời `air` boost như xấp xỉ nhẹ về "độ thoáng" |
| Thời gian/động | Speed, Fast, Transient Response, Attack, Decay, Sustain, Release (ADSR), PRaT, Dynamics, Energy, Smeared, Blurred | Đặc tính driver + bản thu; EQ chỉ giúp gián tiếp qua `tight` nếu vấn đề nằm ở bass |
| Chất âm tổng hợp | Timbre, Texture, Euphonic, Coherent, Liquid, Color | Tổ hợp nhiều yếu tố; hỏi lại người dùng để tách thành tag Nhóm A/B |
| Thiết bị/bản thu | Hiss, Pop, Bleed (device), Low-Level Detail, Accuracy, Fidelity | Thuộc nguồn phát/bản thu, không thuộc EQ |

## Quy tắc xử lý xung đột & mơ hồ

1. **Xung đột trực tiếp** ("ấm hơn nhưng đừng lùng bùng"): apply `warmth` với Q thấp hơn (0.5)
   và fc hạ xuống 150 Hz để tránh vùng 250–500 Hz của `mud`; ghi cả hai tag vào history.
2. **Thuật ngữ đa nghĩa** (Muddy = tonal + transient; Bright = tích cực hoặc tiêu cực):
   LLM phải kèm `quote` (trích nguyên văn) và suy ra `direction` từ ngữ cảnh; nếu không chắc,
   trả `clarify: true` để UI hỏi lại thay vì đoán.
3. **Nhiều tag cùng dải tần** (boomy + bloated + mud chồng 125–500 Hz): gộp thành tối đa
   2 filter, tổng gain vùng chồng lấn tuân clamp ≤ 9 dB.
4. **Tag Nhóm C**: tuyệt đối không sinh filter "cho có" — trung thực về giới hạn của EQ
   là yêu cầu sản phẩm, không phải nhược điểm.
