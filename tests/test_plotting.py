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


class TestAddProcessLabelLeaders:
    def _transformed_df(self):
        import pandas as pd
        import timeSpace
        from timeSpace import transform_predefined_processes

        csv_dir = timeSpace.PROJECT_ROOT / "data" / "datasets"
        df = pd.read_csv(csv_dir / "stommel_boyd2015_volumes.csv")
        return transform_predefined_processes(df, space_on_x=False)

    def test_returns_figure(self):
        from timeSpace.plotting import (
            add_predefined_processes,
            add_process_label_leaders,
            create_space_time_figure,
        )

        transformed = self._transformed_df()
        p = create_space_time_figure(space_on_x=False)
        p = add_predefined_processes(p, transformed, space_on_x=False)
        result = add_process_label_leaders(p, transformed, space_on_x=False)
        assert type(result).__name__ == "figure"

    def test_adds_segments(self):
        """Leader lines should add at least one Segment glyph to the figure
        when labels have nonzero offsets above the threshold."""
        from bokeh.models import Segment
        from timeSpace.plotting import (
            add_predefined_processes,
            add_process_label_leaders,
            create_space_time_figure,
        )

        transformed = self._transformed_df()
        p = create_space_time_figure(space_on_x=False)
        add_predefined_processes(p, transformed, space_on_x=False)
        before = sum(1 for r in p.renderers if isinstance(r.glyph, Segment))
        add_process_label_leaders(p, transformed, space_on_x=False, min_offset_px=1)
        after = sum(1 for r in p.renderers if isinstance(r.glyph, Segment))
        assert after > before

    def test_threshold_skips_small_offsets(self):
        """When `min_offset_px` exceeds all label offsets in the data, no
        Segment glyph should be added."""
        from bokeh.models import Segment
        from timeSpace.plotting import (
            add_predefined_processes,
            add_process_label_leaders,
            create_space_time_figure,
        )

        transformed = self._transformed_df()
        p = create_space_time_figure(space_on_x=False)
        add_predefined_processes(p, transformed, space_on_x=False)
        before = sum(1 for r in p.renderers if isinstance(r.glyph, Segment))
        # 10_000 px threshold — larger than any realistic offset
        add_process_label_leaders(p, transformed, space_on_x=False, min_offset_px=10_000)
        after = sum(1 for r in p.renderers if isinstance(r.glyph, Segment))
        assert after == before

    def test_empty_dataframe_no_op(self):
        import pandas as pd
        from timeSpace.plotting import (
            add_process_label_leaders,
            create_space_time_figure,
        )

        empty = pd.DataFrame(
            columns=[
                "Name",
                "Time_min",
                "Time_max",
                "Space_min",
                "Space_max",
                "x_offset",
                "y_offset",
                "label_side",
                "Color",
            ]
        )
        p = create_space_time_figure(space_on_x=False)
        result = add_process_label_leaders(p, empty, space_on_x=False)
        assert type(result).__name__ == "figure"
