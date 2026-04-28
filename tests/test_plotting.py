import numpy as np
import pandas as pd
from bokeh.models import LogAxis
from bokeh.models.glyphs import Text

import timeSpace
from timeSpace import transform_predefined_processes
from timeSpace.plotting import (
    _resolve_start_visible,
    add_magnitude_labels,
    add_predefined_processes,
    create_space_time_figure,
)


class TestCreateSpaceTimeFigure:
    def test_returns_bokeh_figure(self):
        p = create_space_time_figure()
        assert type(p).__name__ == "figure"

    def test_log_axes(self):
        p = create_space_time_figure()
        assert p.x_scale.__class__.__name__ == "LogScale"
        assert p.y_scale.__class__.__name__ == "LogScale"

    def test_custom_dimensions(self):
        p = create_space_time_figure(width=800, height=600)
        assert p.width == 800
        assert p.height == 600

    def test_boyd_axis_labels(self):
        """Stommel convention: x=Space (top), y=Time (reversed)."""
        p = create_space_time_figure()
        assert "Space" in p.xaxis[0].axis_label
        assert "Time" in p.yaxis[0].axis_label

    def test_space_axis_on_top(self):
        p = create_space_time_figure()
        assert any(isinstance(r, LogAxis) for r in p.above)

    def test_time_axis_reversed(self):
        """y_range should be reversed: large time at bottom, small at top."""
        p = create_space_time_figure()
        y_start = p.y_range.start
        y_end = p.y_range.end
        assert y_start > y_end, f"y_range should be reversed for Stommel: start={y_start} should be > end={y_end}"


class TestAddMagnitudeLabels:
    def test_adds_layout_elements(self):
        p = create_space_time_figure()
        before = len(p.center)
        add_magnitude_labels(p)
        after = len(p.center)
        # Each marker adds a Label + a Span → at least 2 per marker
        assert after > before

    def test_returns_figure(self):
        p = create_space_time_figure()
        result = add_magnitude_labels(p)
        assert type(result).__name__ == "figure"


class TestRangeBoundsJSSafe:
    """Regression for Bokeh `out of range integer may result in loss of
    precision` warning. Range bounds get serialized to JS `Number`, which
    loses precision beyond 2**53 - 1. All axis-range bounds must therefore
    be floats, not Python ints.
    """

    _MAX_SAFE_INT = 2**53 - 1  # JavaScript Number.MAX_SAFE_INTEGER

    def _assert_safe(self, v):
        # Bokeh only warns for `int`, not `float`. The fix is to use 1eN
        # literals (floats) rather than 10**N (ints) for large bounds.
        if isinstance(v, int) and not isinstance(v, bool):
            assert abs(v) <= self._MAX_SAFE_INT, (
                f"range bound {v!r} is an int > 2**53; will trigger "
                "BokehUserWarning on serialization. Use a float literal."
            )

    def test_range_bounds_are_js_safe_space_on_x(self):
        p = create_space_time_figure(space_on_x=True)
        for v in (p.x_range.start, p.x_range.end, p.y_range.start, p.y_range.end):
            self._assert_safe(v)

    def test_range_bounds_are_js_safe_time_on_x(self):
        p = create_space_time_figure(space_on_x=False)
        for v in (p.x_range.start, p.x_range.end, p.y_range.start, p.y_range.end):
            self._assert_safe(v)


class TestAddPredefinedProcessesLabelText:
    """Per-row `label_text` overrides the Name displayed on the plot.
    Legend continues to use Name unchanged."""

    def _row_factory(self, label_text_value):
        csv_dir = timeSpace.PROJECT_ROOT / "data" / "datasets"
        df = pd.read_csv(csv_dir / "stommel_boyd2015_volumes.csv")
        df = df.iloc[:1].copy()
        df["label_text"] = [label_text_value]
        return transform_predefined_processes(df, space_on_x=False)

    def _text_glyph_values(self, p):
        out = []
        for r in p.renderers:
            if isinstance(r.glyph, Text):
                src = r.data_source
                if "text" in src.data:
                    out.extend(src.data["text"])
        return out

    def test_label_text_renders_when_set(self):
        transformed = self._row_factory("custom\nlabel")
        p = create_space_time_figure(space_on_x=False)
        add_predefined_processes(p, transformed, space_on_x=False)
        texts = self._text_glyph_values(p)
        assert "custom\nlabel" in texts

    def test_empty_string_falls_back_to_name(self):
        transformed = self._row_factory("")
        p = create_space_time_figure(space_on_x=False)
        add_predefined_processes(p, transformed, space_on_x=False)
        texts = self._text_glyph_values(p)
        assert "Diffusion boundary layers" in texts

    def test_nan_falls_back_to_name(self):
        transformed = self._row_factory(np.nan)
        p = create_space_time_figure(space_on_x=False)
        add_predefined_processes(p, transformed, space_on_x=False)
        texts = self._text_glyph_values(p)
        assert "Diffusion boundary layers" in texts


class TestStartVisibleColumn:
    """Verify the per-row start_visible column overrides the global
    `interactive`-derived default in add_predefined_processes.
    The CSV format is pandas' default bool serialization: 'True' / 'False'.
    """

    def test_resolves_true_and_false(self):
        assert _resolve_start_visible(pd.Series({"start_visible": "True"}), default=False) is True
        assert _resolve_start_visible(pd.Series({"start_visible": "False"}), default=True) is False

    def test_blank_cell_falls_back_to_default(self):
        assert _resolve_start_visible(pd.Series({"start_visible": ""}), default=True) is True
        assert _resolve_start_visible(pd.Series({"start_visible": ""}), default=False) is False

    def test_missing_column_falls_back_to_default(self):
        assert _resolve_start_visible(pd.Series({"other": "x"}), default=True) is True
        assert _resolve_start_visible(pd.Series({"other": "x"}), default=False) is False

    def test_csv_has_expected_off_by_default(self):
        """Regression on the shipped CSV: exactly these processes start hidden."""
        csv_dir = timeSpace.PROJECT_ROOT / "data" / "datasets"
        df = pd.read_csv(csv_dir / "stommel_boyd2015_volumes.csv")
        hidden = set(df.loc[~df["start_visible"].astype(bool), "Name"])
        expected = {"Habitat-scale hydrodynamics", "Biological pump"}
        assert hidden == expected, f"unexpected hidden set: {hidden}"
