"""Tests for measurement plotting functions.

Covers add_measurements (grey/colored modes, hover tools, visibility,
label offsets) and add_grouped_measurement (per-group scatter/labels).
"""

import pandas as pd
from bokeh.models import GlyphRenderer, HoverTool, LabelSet
from bokeh.plotting import figure as bokeh_figure

from timeSpace.measurements import add_measurements, add_grouped_measurement


def make_measurement_df(n=3):
    """Create a minimal measurements DataFrame for testing."""
    return pd.DataFrame(
        {
            "Time_value": [1e0, 1e3, 1e6][:n],
            "Space_value": [1e-18, 1e-9, 1e0][:n],
            "Color": ["#33CCCC", "#009999", "#006666"][:n],
            "Name": ["Protein Folding", "Cell Division", "Ecosystem Shift"][:n],
            "ShortName": ["PF", "CD", "ES"][:n],
            "Prefix": ["Bio", "Bio", "Eco"][:n],
            "x_offset": [5, 10, -5][:n],
            "y_offset": [10, -10, 5][:n],
        }
    )


def make_log_figure():
    return bokeh_figure(
        x_axis_type="log",
        y_axis_type="log",
        width=600,
        height=400,
    )


class TestAddMeasurements:
    def test_returns_figure(self):
        p = make_log_figure()
        result = add_measurements(p, make_measurement_df())
        assert result is p

    def test_adds_scatter_renderer(self):
        p = make_log_figure()
        renderers_before = len(p.renderers)
        add_measurements(p, make_measurement_df())
        scatter_renderers = [r for r in p.renderers[renderers_before:] if isinstance(r, GlyphRenderer)]
        assert len(scatter_renderers) == 1

    def test_adds_labelset_to_center(self):
        """LabelSet added via add_layout appears in p.center, not p.renderers."""
        p = make_log_figure()
        center_before = len(p.center)
        add_measurements(p, make_measurement_df())
        new_labels = [obj for obj in p.center[center_before:] if isinstance(obj, LabelSet)]
        assert len(new_labels) == 1

    def test_colored_mode_uses_color_column(self):
        p = make_log_figure()
        add_measurements(p, make_measurement_df(), grey=False)
        scatter = [r for r in p.renderers if isinstance(r, GlyphRenderer)][-1]
        assert scatter.glyph.fill_color == "Color"

    def test_grey_mode_uses_grey_fill(self):
        p = make_log_figure()
        add_measurements(p, make_measurement_df(), grey=True)
        scatter = [r for r in p.renderers if isinstance(r, GlyphRenderer)][-1]
        assert scatter.glyph.fill_color == "Grey"

    def test_grey_mode_labels_show_prefix(self):
        p = make_log_figure()
        center_before = len(p.center)
        add_measurements(p, make_measurement_df(), grey=True)
        label = [obj for obj in p.center[center_before:] if isinstance(obj, LabelSet)][0]
        assert label.text == "Prefix"

    def test_colored_mode_labels_show_name(self):
        p = make_log_figure()
        center_before = len(p.center)
        add_measurements(p, make_measurement_df(), grey=False)
        label = [obj for obj in p.center[center_before:] if isinstance(obj, LabelSet)][0]
        assert label.text == "Name"

    def test_grey_mode_adds_hover_tool(self):
        p = make_log_figure()
        tools_before = len(p.tools)
        add_measurements(p, make_measurement_df(), grey=True)
        new_hovers = [t for t in p.tools[tools_before:] if isinstance(t, HoverTool)]
        assert len(new_hovers) == 1

    def test_colored_mode_no_extra_hover(self):
        p = make_log_figure()
        tools_before = len(p.tools)
        add_measurements(p, make_measurement_df(), grey=False)
        new_hovers = [t for t in p.tools[tools_before:] if isinstance(t, HoverTool)]
        assert len(new_hovers) == 0

    def test_scatter_starts_invisible(self):
        p = make_log_figure()
        add_measurements(p, make_measurement_df())
        scatter = [r for r in p.renderers if isinstance(r, GlyphRenderer)][-1]
        assert scatter.visible is False

    def test_labels_start_invisible(self):
        p = make_log_figure()
        center_before = len(p.center)
        add_measurements(p, make_measurement_df())
        label = [obj for obj in p.center[center_before:] if isinstance(obj, LabelSet)][0]
        assert label.visible is False

    def test_label_offsets_from_dataframe(self):
        p = make_log_figure()
        center_before = len(p.center)
        add_measurements(p, make_measurement_df())
        label = [obj for obj in p.center[center_before:] if isinstance(obj, LabelSet)][0]
        assert label.x_offset == "x_offset"
        assert label.y_offset == "y_offset"


class TestAddGroupedMeasurement:
    def test_returns_figure(self):
        p = make_log_figure()
        result = add_grouped_measurement(p, make_measurement_df())
        assert result is p

    def test_creates_one_scatter_per_group(self):
        df = make_measurement_df()
        n_groups = df["Prefix"].nunique()
        p = make_log_figure()
        renderers_before = len(p.renderers)
        add_grouped_measurement(p, df, group="Prefix")
        new_renderers = [r for r in p.renderers[renderers_before:] if isinstance(r, GlyphRenderer)]
        assert len(new_renderers) == n_groups

    def test_creates_one_labelset_per_group(self):
        df = make_measurement_df()
        n_groups = df["Prefix"].nunique()
        p = make_log_figure()
        center_before = len(p.center)
        add_grouped_measurement(p, df, group="Prefix")
        new_labels = [obj for obj in p.center[center_before:] if isinstance(obj, LabelSet)]
        assert len(new_labels) == n_groups

    def test_all_scatter_start_invisible(self):
        p = make_log_figure()
        renderers_before = len(p.renderers)
        add_grouped_measurement(p, make_measurement_df())
        for r in p.renderers[renderers_before:]:
            if isinstance(r, GlyphRenderer):
                assert r.visible is False

    def test_uses_color_column(self):
        p = make_log_figure()
        renderers_before = len(p.renderers)
        add_grouped_measurement(p, make_measurement_df())
        for r in p.renderers[renderers_before:]:
            if isinstance(r, GlyphRenderer):
                assert r.glyph.fill_color == "Color"


class TestMeasurementAxisMapping:
    """Verify measurements use default axis mapping: x=Space, y=Time."""

    def test_scatter_maps_space_to_x(self):
        p = make_log_figure()
        renderers_before = len(p.renderers)
        add_measurements(p, make_measurement_df())
        scatter = [r for r in p.renderers[renderers_before:] if isinstance(r, GlyphRenderer)][-1]
        assert scatter.glyph.x == "Space_value"

    def test_scatter_maps_time_to_y(self):
        p = make_log_figure()
        renderers_before = len(p.renderers)
        add_measurements(p, make_measurement_df())
        scatter = [r for r in p.renderers[renderers_before:] if isinstance(r, GlyphRenderer)][-1]
        assert scatter.glyph.y == "Time_value"

    def test_grouped_scatter_maps_space_to_x(self):
        p = make_log_figure()
        renderers_before = len(p.renderers)
        add_grouped_measurement(p, make_measurement_df())
        scatter = [r for r in p.renderers[renderers_before:] if isinstance(r, GlyphRenderer)][-1]
        assert scatter.glyph.x == "Space_value"

    def test_labels_map_space_to_x(self):
        p = make_log_figure()
        center_before = len(p.center)
        add_measurements(p, make_measurement_df())
        label = [obj for obj in p.center[center_before:] if isinstance(obj, LabelSet)][0]
        assert label.x == "Space_value"
