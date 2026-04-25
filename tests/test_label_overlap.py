"""Tests that co-located measurements get non-overlapping labels.

The jitter pipeline has two layers:
  1. plotting_helpers.set_measurement_text_jitter — assigns distinct
     (x_offset, y_offset) to measurements sharing the same data coords
  2. measurements.add_measurements — wires those offsets into a Bokeh
     LabelSet so the rendered labels are visually separated

These tests verify both layers for the simplest collision case:
two measurements at the exact same (Time_value, Space_value).

Known limitation (see issue #107): OFFSETS dict only has keys 1-6.
For 7+ co-located measurements, the KeyError fallback sends them
all to key "1", causing full overlap.
"""

import pandas as pd
from bokeh.models import LabelSet
from bokeh.plotting import figure as bokeh_figure

from timeSpace.constants import OFFSETS
from timeSpace.measurements import add_measurements
from timeSpace.plotting_helpers import set_measurement_text_jitter


def make_colocated_pair():
    """Two measurements at the exact same time x space coordinates."""
    return pd.DataFrame(
        {
            "Time_value": [1e3, 1e3],
            "Space_value": [1e-9, 1e-9],
            "Color": ["#33CCCC", "#009999"],
            "Name": ["Process A", "Process B"],
            "ShortName": ["PA", "PB"],
            "Prefix": ["Lab1", "Lab2"],
        }
    )


def make_log_figure():
    return bokeh_figure(
        x_axis_type="log",
        y_axis_type="log",
        width=600,
        height=400,
    )


# -- Layer 1: jitter assignment (plotting_helpers) ----


class TestSetMeasurementTextJitter:
    def test_assigns_different_offsets_to_colocated_pair(self):
        df = make_colocated_pair()
        result = set_measurement_text_jitter(df)
        offsets = list(zip(result["x_offset"], result["y_offset"]))
        assert offsets[0] != offsets[1], f"Co-located labels got identical offsets: {offsets[0]}"

    def test_duplicate_magnitudes_counted_correctly(self):
        df = make_colocated_pair()
        result = set_measurement_text_jitter(df)
        assert list(result["duplicate_magnitudes"]) == [1, 2]

    def test_first_gets_offset_key_1(self):
        df = make_colocated_pair()
        result = set_measurement_text_jitter(df)
        row1 = result.iloc[0]
        expected = OFFSETS["1"]
        assert row1["x_offset"] == expected[0]
        assert row1["y_offset"] == expected[1]

    def test_second_gets_offset_key_2(self):
        df = make_colocated_pair()
        result = set_measurement_text_jitter(df)
        row2 = result.iloc[1]
        expected = OFFSETS["2"]
        assert row2["x_offset"] == expected[0]
        assert row2["y_offset"] == expected[1]

    def test_non_colocated_both_get_offset_key_1(self):
        """Measurements at different coords should each be duplicate_magnitudes=1."""
        df = pd.DataFrame(
            {
                "Time_value": [1e3, 1e6],
                "Space_value": [1e-9, 1e0],
                "Color": ["#33CCCC", "#009999"],
                "Name": ["A", "B"],
                "ShortName": ["A", "B"],
                "Prefix": ["X", "Y"],
            }
        )
        result = set_measurement_text_jitter(df)
        assert list(result["duplicate_magnitudes"]) == [1, 1]
        expected = OFFSETS["1"]
        for _, row in result.iterrows():
            assert row["x_offset"] == expected[0]
            assert row["y_offset"] == expected[1]

    def test_three_colocated_all_distinct(self):
        df = pd.DataFrame(
            {
                "Time_value": [1e3, 1e3, 1e3],
                "Space_value": [1e-9, 1e-9, 1e-9],
                "Color": ["#33CCCC", "#009999", "#006666"],
                "Name": ["A", "B", "C"],
                "ShortName": ["A", "B", "C"],
                "Prefix": ["X", "Y", "Z"],
            }
        )
        result = set_measurement_text_jitter(df)
        offsets = list(zip(result["x_offset"], result["y_offset"]))
        assert len(set(offsets)) == 3, f"Expected 3 distinct offsets, got {offsets}"

    def test_six_colocated_all_distinct(self):
        """OFFSETS has keys 1-6, so 6 co-located points is the max
        the current system can separate."""
        df = pd.DataFrame(
            {
                "Time_value": [1e3] * 6,
                "Space_value": [1e-9] * 6,
                "Color": [f"#{i}0{i}0{i}0" for i in range(6)],
                "Name": [f"P{i}" for i in range(6)],
                "ShortName": [f"P{i}" for i in range(6)],
                "Prefix": [f"L{i}" for i in range(6)],
            }
        )
        result = set_measurement_text_jitter(df)
        offsets = list(zip(result["x_offset"], result["y_offset"]))
        assert len(set(offsets)) == 6, f"Expected 6 distinct offsets, got {len(set(offsets))}: {offsets}"


# -- Layer 2: offsets wired into Bokeh LabelSet ----


class TestLabelOffsetsInRenderedFigure:
    def test_labelset_source_has_distinct_offsets(self):
        """After jitter + add_measurements, the LabelSet's backing
        ColumnDataSource should contain distinct offset pairs."""
        df = make_colocated_pair()
        df = set_measurement_text_jitter(df)
        p = make_log_figure()
        add_measurements(p, df)

        labels = [obj for obj in p.center if isinstance(obj, LabelSet)]
        assert len(labels) == 1
        src = labels[0].source
        offsets = list(zip(src.data["x_offset"], src.data["y_offset"]))
        assert offsets[0] != offsets[1], f"LabelSet source has identical offsets for co-located points: {offsets}"

    def test_labelset_reads_offset_columns(self):
        """LabelSet x_offset and y_offset should reference the DataFrame
        columns, not be hardcoded scalars."""
        df = make_colocated_pair()
        df = set_measurement_text_jitter(df)
        p = make_log_figure()
        add_measurements(p, df)

        label = [obj for obj in p.center if isinstance(obj, LabelSet)][0]
        assert label.x_offset == "x_offset"
        assert label.y_offset == "y_offset"
