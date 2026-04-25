from bokeh.models import LogAxis

from timeSpace.plotting import create_space_time_figure


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
        from timeSpace.plotting import add_magnitude_labels, create_space_time_figure

        p = create_space_time_figure()
        before = len(p.center)
        add_magnitude_labels(p)
        after = len(p.center)
        # Each marker adds a Label + a Span → at least 2 per marker
        assert after > before

    def test_returns_figure(self):
        from timeSpace.plotting import add_magnitude_labels, create_space_time_figure

        p = create_space_time_figure()
        result = add_magnitude_labels(p)
        assert type(result).__name__ == "figure"


class TestAddPredefinedProcessesLabelText:
    """Per-row `label_text` overrides the Name displayed on the plot.
    Legend continues to use Name unchanged."""

    def _row_factory(self, label_text_value):
        import pandas as pd
        import timeSpace
        from timeSpace import transform_predefined_processes

        csv_dir = timeSpace.PROJECT_ROOT / "data" / "datasets"
        df = pd.read_csv(csv_dir / "stommel_boyd2015_volumes.csv")
        # Use only the first row, set its label_text
        df = df.iloc[:1].copy()
        df["label_text"] = [label_text_value]
        return transform_predefined_processes(df, space_on_x=False)

    def _text_glyph_values(self, p):
        from bokeh.models.glyphs import Text

        out = []
        for r in p.renderers:
            if isinstance(r.glyph, Text):
                src = r.data_source
                if "text" in src.data:
                    out.extend(src.data["text"])
        return out

    def test_label_text_renders_when_set(self):
        from timeSpace.plotting import add_predefined_processes, create_space_time_figure

        transformed = self._row_factory("custom\nlabel")
        p = create_space_time_figure(space_on_x=False)
        add_predefined_processes(p, transformed, space_on_x=False)
        texts = self._text_glyph_values(p)
        assert "custom\nlabel" in texts

    def test_empty_string_falls_back_to_name(self):
        from timeSpace.plotting import add_predefined_processes, create_space_time_figure

        transformed = self._row_factory("")
        p = create_space_time_figure(space_on_x=False)
        add_predefined_processes(p, transformed, space_on_x=False)
        texts = self._text_glyph_values(p)
        # Row 0 is Diffusion boundary layers
        assert "Diffusion boundary layers" in texts

    def test_nan_falls_back_to_name(self):
        import numpy as np

        from timeSpace.plotting import add_predefined_processes, create_space_time_figure

        transformed = self._row_factory(np.nan)
        p = create_space_time_figure(space_on_x=False)
        add_predefined_processes(p, transformed, space_on_x=False)
        texts = self._text_glyph_values(p)
        assert "Diffusion boundary layers" in texts
