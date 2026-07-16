"""Tests for the Comrade Curve app modules (app/) — BUILD_PLAN.md GD1+."""

import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "app"))

from audio_devices import list_output_devices  # noqa: E402
from equalize import Options, compute, list_targets, load_target  # noqa: E402
from headphone_index import build_index, search  # noqa: E402
from profile_store import (  # noqa: E402
    EMA_ALPHA,
    WEIGHT_INITIAL,
    WEIGHT_STEP,
    FilterDelta,
    Profile,
    ProfileStore,
)

MEASUREMENTS_DIR = os.path.join(ROOT, "measurements")
HD650 = os.path.join(
    MEASUREMENTS_DIR, "oratory1990", "data", "over-ear", "Sennheiser HD 650.csv"
)
HD600 = os.path.join(
    MEASUREMENTS_DIR, "oratory1990", "data", "over-ear", "Sennheiser HD 600.csv"
)


class TestHeadphoneIndex:
    def test_build_index_finds_thousands_of_entries(self):
        entries = build_index(MEASUREMENTS_DIR)
        assert len(entries) > 5000
        e = entries[0]
        assert e.name and e.source and e.form in ("earbud", "in-ear", "over-ear")
        assert os.path.isfile(e.path)

    def test_index_includes_rig_level_sources(self):
        entries = build_index(MEASUREMENTS_DIR)
        assert any(e.rig for e in entries), "Rtings/HypetheSonics rig dirs missed"

    def test_search_all_tokens_must_match(self):
        entries = build_index(MEASUREMENTS_DIR)
        results = search(entries, "sennheiser hd 650")
        assert results and all("HD 650" in e.name for e in results)

    def test_search_empty_query_returns_head_of_list(self):
        entries = build_index(MEASUREMENTS_DIR)
        assert len(search(entries, "", limit=10)) == 10

    def test_search_respects_limit(self):
        entries = build_index(MEASUREMENTS_DIR)
        assert len(search(entries, "e", limit=5)) == 5

    def test_meta_line_contains_source_and_form(self):
        entries = build_index(MEASUREMENTS_DIR)
        e = search(entries, "sennheiser hd 650 oratory1990")[0]
        assert e.meta == "oratory1990 · over-ear"


class TestAudioDevices:
    def test_list_output_devices_returns_valid_structure(self):
        devices = list_output_devices()
        # May legitimately be empty on CI/headless machines.
        for d in devices:
            assert d.name
            assert d.sample_rate > 0
            assert "·" in d.meta
        if devices:
            assert devices[0].is_default or not any(d.is_default for d in devices)


class TestEqualize:
    def test_list_targets_contains_harman(self):
        targets = list_targets()
        assert any("Harman over-ear 2018" in t for t in targets)

    def test_load_target_by_name(self):
        fr = load_target("Harman over-ear 2018")
        assert len(fr.frequency) > 0

    def test_load_target_unknown_raises(self):
        try:
            load_target("No Such Target")
            assert False, "expected ValueError"
        except ValueError:
            pass

    def test_compute_smoothen_only_when_no_target(self):
        fr = compute(HD650, None)
        assert len(fr.smoothed) == len(fr.frequency)
        assert len(fr.equalization) == 0

    def test_compute_with_target_produces_equalization(self):
        fr = compute(HD650, "Harman over-ear 2018")
        assert len(fr.equalization) == len(fr.frequency)
        assert len(fr.equalized_raw) == len(fr.frequency)
        assert len(fr.target) == len(fr.frequency)
        # Correction must be bounded by max_gain plus headroom tolerance
        assert np.max(fr.equalization) <= Options().max_gain + 1.0

    def test_compute_max_gain_option_is_respected(self):
        fr = compute(HD650, "Harman over-ear 2018", Options(max_gain=3.0))
        assert np.max(fr.equalization) <= 4.0


def _warmth(gain=3.0, weight=1.0, **kwargs) -> FilterDelta:
    return FilterDelta(
        tag="warmth", type="LOW_SHELF", fc=200.0, q=0.7, gain=gain,
        weight=weight, **kwargs,
    )


class TestProfileStore:
    """BUILD_PLAN.md GD3 — Layer 3 memory."""

    def test_save_load_roundtrip(self, tmp_path):
        store = ProfileStore(str(tmp_path))
        profile = Profile(name="default", headphone="Sennheiser HD 650",
                          target="Harman over-ear 2018", preamp=-4.4)
        profile.bands = [{"fc": 25.0, "type": "LOW_SHELF", "gain": 1.5, "q": 0.7}]
        profile.filter_deltas.append(_warmth())
        profile.record_history(action="save", headphone="Sennheiser HD 650")
        path = store.save(profile)
        assert os.path.isfile(path) and not os.path.isfile(path + ".tmp")

        loaded = store.load("default")
        assert loaded.name == "default"
        assert loaded.headphone == "Sennheiser HD 650"
        assert loaded.bands == profile.bands
        assert loaded.filter_deltas == profile.filter_deltas
        assert loaded.history[0]["action"] == "save"
        assert loaded.updated_at  # stamped by save()

    def test_saved_file_matches_roadmap_schema(self, tmp_path):
        store = ProfileStore(str(tmp_path))
        profile = Profile(name="default")
        profile.filter_deltas.append(_warmth())
        store.save(profile)
        with open(store.path("default"), encoding="utf-8") as fh:
            data = json.load(fh)
        assert data["version"] == 1
        assert set(data["preference_curve"]) == {"frequency", "raw"}
        assert len(data["preference_curve"]["frequency"]) == \
            len(data["preference_curve"]["raw"])
        delta = data["filter_deltas"][0]
        assert set(delta) == {"tag", "type", "fc", "q", "gain", "scope",
                              "source", "weight"}

    def test_render_curve_boosts_at_delta_fc(self):
        profile = Profile()
        profile.filter_deltas.append(_warmth(gain=3.0, weight=1.0))
        f, curve = profile.render_curve()
        low = curve[f <= 100]
        high = curve[f >= 5000]
        assert np.all(low > 1.5)  # low shelf raises the bass region
        assert np.all(np.abs(high) < 0.5)  # and leaves treble alone

    def test_render_curve_scales_gain_by_weight(self):
        full = Profile()
        full.filter_deltas.append(_warmth(gain=4.0, weight=1.0))
        half = Profile()
        half.filter_deltas.append(_warmth(gain=4.0, weight=0.5))
        f, curve_full = full.render_curve()
        _, curve_half = half.render_curve()
        idx = f <= 100
        ratio = np.mean(curve_half[idx]) / np.mean(curve_full[idx])
        assert abs(ratio - 0.5) < 0.05

    def test_as_sound_signature_none_when_empty(self):
        assert Profile().as_sound_signature() is None

    def test_scope_filters_by_headphone(self):
        profile = Profile()
        profile.filter_deltas.append(_warmth(scope="global"))
        profile.filter_deltas.append(
            FilterDelta(tag="harsh", type="PEAKING", fc=4500.0, q=2.0,
                        gain=-2.0, scope="headphone:HD 650")
        )
        assert len(profile.deltas_for(None)) == 1
        assert len(profile.deltas_for("HD 650")) == 2
        assert len(profile.deltas_for("HD 600")) == 1

    def test_merge_delta_ema_and_weight_bump(self):
        profile = Profile()
        profile.filter_deltas.append(_warmth(gain=2.0, weight=0.5))
        merged = profile.merge_delta(_warmth(gain=4.0))
        assert len(profile.filter_deltas) == 1
        expected = EMA_ALPHA * 4.0 + (1 - EMA_ALPHA) * 2.0
        assert abs(merged.gain - expected) < 1e-9
        assert abs(merged.weight - (0.5 + WEIGHT_STEP)) < 1e-9

    def test_merge_delta_new_tag_appends_at_initial_weight(self):
        profile = Profile()
        merged = profile.merge_delta(
            FilterDelta(tag="mud", type="PEAKING", fc=300.0, q=1.2,
                        gain=-2.0, weight=0.9)
        )
        assert len(profile.filter_deltas) == 1
        assert merged.weight == WEIGHT_INITIAL

    def test_merge_delta_clamps_vocabulary_limits(self):
        profile = Profile()
        merged = profile.merge_delta(
            FilterDelta(tag="punch", type="PEAKING", fc=100.0, q=99.0, gain=20.0)
        )
        assert merged.gain <= 6.0
        assert merged.q <= 6.0

    def test_load_latest_returns_most_recent(self, tmp_path):
        store = ProfileStore(str(tmp_path))
        store.save(Profile(name="older"))
        newer = Profile(name="newer")
        store.save(newer)
        newer.updated_at = "2099-01-01T00:00:00Z"
        with open(store.path("newer"), "w", encoding="utf-8") as fh:
            json.dump(newer.to_dict(), fh)
        latest = store.load_latest()
        assert latest is not None and latest.name == "newer"

    def test_ai_engine_group_a_mapping_is_deterministic(self):
        from ai_engine import vocabulary

        mapped = vocabulary.map_adjustment("mud", "reduce", 0.6)
        (f,) = mapped.filters
        assert (f.type, f.fc, f.q) == ("PEAKING", 300, 1.2)
        assert f.gain == -2.4  # 0.6 * base 4 dB, cut
        boosted = vocabulary.map_adjustment("thin_cool", "reduce", 1.0).filters[0]
        assert boosted.gain > 0  # deficiency tag: reducing it boosts lows

    def test_ai_engine_clamps(self):
        from ai_engine import vocabulary
        from profile_store import FilterDelta

        f = vocabulary.map_adjustment("harsh", "reduce", 1.0).filters[0]
        assert abs(f.gain) <= vocabulary.GAIN_LIMIT_DB
        overlapping = [
            FilterDelta(tag="boomy", type="PEAKING", fc=125, q=1.4, gain=-5.0),
            FilterDelta(tag="bloated", type="PEAKING", fc=250, q=1.4, gain=-6.0),
        ]
        vocabulary.clamp_overlap(overlapping)
        assert sum(abs(f.gain) for f in overlapping) <= vocabulary.OVERLAP_LIMIT_DB + 0.01

    def test_ai_engine_group_c_explains_without_filters(self):
        from ai_engine import vocabulary

        mapped = vocabulary.map_adjustment("spatial", "increase", 0.8)
        assert mapped.explanation and not mapped.filters

    def test_engine_propose_and_apply_with_fake_provider(self):
        from ai_engine import engine
        from ai_engine.providers.base import Adjustment, InterpretResult, Provider
        from state import default_bands

        class FakeProvider(Provider):
            name = "fake"

            def interpret(self, feedback, context=None):
                return InterpretResult(
                    adjustments=[Adjustment("punch", "increase", 0.6, "more bass")],
                    reply="Adding punch.",
                )

        bands = default_bands()
        proposal = engine.propose("more bass", provider=FakeProvider())
        assert proposal.changes_eq and not proposal.error
        snapshot, detail = engine.apply_proposal(bands, proposal)
        # punch region 60-150 Hz covers bands 1 (51 Hz is outside) and 2
        changed = [i for i, (b, s) in enumerate(zip(bands, snapshot)) if b.gain != s]
        assert changed, "no band moved"
        assert all(60 <= bands[i].fc <= 150 for i in changed)
        assert "punch" in detail
        engine.restore_snapshot(bands, snapshot)
        assert [b.gain for b in bands] == snapshot

    def test_engine_clarify_and_error_paths(self):
        from ai_engine import engine
        from ai_engine.providers.base import InterpretResult, Provider, ProviderError

        class ClarifyProvider(Provider):
            name = "fake"

            def interpret(self, feedback, context=None):
                return InterpretResult(clarify=True, question="Tonal or transient?")

        class BrokenProvider(Provider):
            name = "fake"

            def interpret(self, feedback, context=None):
                raise ProviderError("no model configured")

        p = engine.propose("muddy", provider=ClarifyProvider())
        assert p.clarify and not p.changes_eq and "Tonal" in p.reply
        p = engine.propose("muddy", provider=BrokenProvider())
        assert p.error and "no model" in p.reply

    def test_parse_result_drops_hallucinated_tags(self):
        from ai_engine.providers.base import parse_result

        result = parse_result(
            '{"adjustments": [{"tag": "bass_cannon", "direction": "reduce", '
            '"intensity": 5, "quote": ""}, {"tag": "air", "direction": "increase", '
            '"intensity": 5, "quote": ""}], "clarify": false, "question": null, '
            '"reply": "ok"}'
        )
        assert [a.tag for a in result.adjustments] == ["air"]
        assert result.adjustments[0].intensity == 1.0  # clamped

    def test_ab_preview_fir_and_convolution(self):
        import ab_preview
        from state import default_bands

        bands = default_bands()
        bands[1].gain = 4.0
        fir = ab_preview.build_fir(bands, preamp_db=-4.4, fs=48000)
        assert fir.ndim == 1 and len(fir) > 100
        assert np.all(np.isfinite(fir))
        noise = ab_preview.pink_noise(seconds=0.25, fs=48000)
        assert np.max(np.abs(noise)) <= 0.3
        player = ab_preview.ABPlayer(fs=48000)
        player.prepare(bands, preamp_db=-4.4, signal=noise)
        assert player._eq is not None and len(player._eq) == len(noise)
        assert np.max(np.abs(player._eq)) <= 1.0

    def test_learn_accept_merges_and_records_history(self):
        profile = Profile()
        f = _warmth(gain=3.0)
        profile.learn_accept("HD 650", "warmer please", [("warmth", "increase", 0.75)], [f])
        assert len(profile.filter_deltas) == 1
        assert profile.filter_deltas[0].weight == WEIGHT_INITIAL
        entry = profile.history[-1]
        assert entry["accepted"] and entry["headphone"] == "HD 650"
        assert entry["tags"] == ["warmth"]
        assert entry["applied"][0]["fc"] == 200.0
        # Second confirmation: EMA on gain, weight bumped.
        profile.learn_accept("HD 650", "warmer", [("warmth", "increase", 1.0)],
                             [_warmth(gain=4.0)])
        d = profile.filter_deltas[0]
        assert abs(d.gain - (EMA_ALPHA * 4.0 + (1 - EMA_ALPHA) * 3.0)) < 1e-9
        assert abs(d.weight - (WEIGHT_INITIAL + WEIGHT_STEP)) < 1e-9

    def test_learn_undo_weakens_delta(self):
        profile = Profile()
        profile.filter_deltas.append(_warmth(weight=0.6))
        profile.learn_undo("HD 650", [("warmth", "increase", 0.5)])
        assert abs(profile.filter_deltas[0].weight - (0.6 - WEIGHT_STEP)) < 1e-9
        assert profile.history[-1]["accepted"] is False

    def test_scope_rule_demotes_and_promotes(self):
        profile = Profile()
        profile.filter_deltas.append(_warmth())
        # Confirmed twice, only ever on HD 650 -> that headphone's flaw.
        for _ in range(2):
            profile.record_history(headphone="HD 650", tags=["warmth"], accepted=True)
        profile.apply_scope_rule()
        assert profile.filter_deltas[0].scope == "headphone:HD 650"
        # Later confirmed on a second headphone -> back to a global taste.
        profile.record_history(headphone="HD 600", tags=["warmth"], accepted=True)
        profile.apply_scope_rule()
        assert profile.filter_deltas[0].scope == "global"

    def test_settings_store_roundtrip_and_defaults(self, tmp_path):
        import settings_store

        path = str(tmp_path / "config.json")
        assert settings_store.load(path) == settings_store.DEFAULTS
        settings_store.save({"provider": "anthropic", "junk": "x"}, path)
        loaded = settings_store.load(path)
        assert loaded["provider"] == "anthropic"
        assert "junk" not in loaded
        assert loaded["base_url"] == settings_store.DEFAULTS["base_url"]

    def test_taste_tilts_two_headphones_the_same_way(self):
        """GD3.4 acceptance: one profile applied to two different headphones
        tilts both results toward the preference."""
        profile = Profile()
        profile.filter_deltas.append(_warmth(gain=3.0, weight=1.0))
        for path in (HD650, HD600):
            signature = profile.as_sound_signature()
            plain = compute(path, "Harman over-ear 2018")
            tasted = compute(path, "Harman over-ear 2018",
                             Options(sound_signature=signature))
            idx = tasted.frequency <= 100
            lift = np.mean(tasted.target[idx] - plain.target[idx])
            assert lift > 1.5, f"taste not applied for {os.path.basename(path)}"
