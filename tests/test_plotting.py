from bokeh.models import LogAxis

from timeSpace.plotting import add_magnitude_labels, create_space_time_figure


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
