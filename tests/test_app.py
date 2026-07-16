"""Tests for the Comrade Curve app modules (app/) — BUILD_PLAN.md GD1."""

import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "app"))

from audio_devices import list_output_devices  # noqa: E402
from equalize import Options, compute, list_targets, load_target  # noqa: E402
from headphone_index import build_index, search  # noqa: E402

MEASUREMENTS_DIR = os.path.join(ROOT, "measurements")
HD650 = os.path.join(
    MEASUREMENTS_DIR, "oratory1990", "data", "over-ear", "Sennheiser HD 650.csv"
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
