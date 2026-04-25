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


class TestStartVisibleColumn:
    """Verify the per-row start_visible column overrides the global
    `interactive`-derived default in add_predefined_processes.
    """

    def _df(self, start_visible_values):
        import pandas as pd
        import timeSpace
        from timeSpace import transform_predefined_processes

        csv_dir = timeSpace.PROJECT_ROOT / "data" / "datasets"
        df = pd.read_csv(csv_dir / "stommel_boyd2015_volumes.csv")
        # Override start_visible per-row by name-index order
        df["start_visible"] = start_visible_values
        return transform_predefined_processes(df, space_on_x=False)

    def test_parser_accepts_bool(self):
        from timeSpace.plotting import _resolve_start_visible
        import pandas as pd

        row_true = pd.Series({"start_visible": True})
        row_false = pd.Series({"start_visible": False})
        assert _resolve_start_visible(row_true, True, default=True) is True
        assert _resolve_start_visible(row_false, True, default=True) is False

    def test_parser_accepts_strings(self):
        from timeSpace.plotting import _resolve_start_visible
        import pandas as pd

        for s in ("true", "True", "TRUE", "1", "yes", "y"):
            row = pd.Series({"start_visible": s})
            assert _resolve_start_visible(row, True, default=False) is True
        for s in ("false", "False", "0", "no", "n"):
            row = pd.Series({"start_visible": s})
            assert _resolve_start_visible(row, True, default=True) is False

    def test_parser_falls_back_on_missing(self):
        from timeSpace.plotting import _resolve_start_visible
        import pandas as pd

        row_nan = pd.Series({"start_visible": float("nan")})
        row_empty = pd.Series({"start_visible": ""})
        assert _resolve_start_visible(row_nan, True, default=True) is True
        assert _resolve_start_visible(row_empty, True, default=False) is False
        # Column not present → always default
        row_missing = pd.Series({"other": "x"})
        assert _resolve_start_visible(row_missing, False, default=True) is True

    def test_csv_has_two_off_by_default(self):
        """Regression: the shipped CSV marks exactly
        'Habitat-scale hydrodynamics' and 'Biological pump' as start hidden."""
        import pandas as pd
        import timeSpace

        csv_dir = timeSpace.PROJECT_ROOT / "data" / "datasets"
        df = pd.read_csv(csv_dir / "stommel_boyd2015_volumes.csv")
        hidden = set(df.loc[~df["start_visible"].astype(bool), "Name"])
        expected = {"Habitat-scale hydrodynamics", "Biological pump", "Benthic boundary layers"}
        assert hidden == expected, f"unexpected hidden set: {hidden}"
