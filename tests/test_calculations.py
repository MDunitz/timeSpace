import numpy as np
import pandas as pd
import astropy.units as u
import pytest

from timeSpace.calculations import (
    calculate_diffusion_length,
    calculate_log10_y_for_ellipse,
    calculate_log_center,
    calculate_log_width,
    calculate_sphere_volume,
    classify_process_geometry,
    create_ellipse_data,
)


class TestCalculateSphereVolume:
    # V = (4/3) * pi * r^3

    def test_unit_sphere(self):
        vol = calculate_sphere_volume(1 * u.m)
        expected = (4 / 3) * np.pi * u.m**3
        assert vol.unit == u.m**3
        np.testing.assert_allclose(vol.value, expected.value, rtol=1e-10)

    def test_kilometer_input(self):
        vol = calculate_sphere_volume(1 * u.km)
        assert vol.unit == u.m**3
        np.testing.assert_allclose(vol.value, (4 / 3) * np.pi * 1e9, rtol=1e-10)

    def test_rejects_wrong_unit(self):
        with pytest.raises(u.UnitsError):
            calculate_sphere_volume(1 * u.second)


class TestCalculateDiffusionLength:
    # L = sqrt(6 * D * t)   (3D RMS displacement)

    def test_returns_meters(self):
        length = calculate_diffusion_length(1 * u.second)
        assert length.unit == u.m

    def test_scales_with_sqrt_time(self):
        l1 = calculate_diffusion_length(1 * u.second)
        l4 = calculate_diffusion_length(4 * u.second)
        np.testing.assert_allclose(l4.value / l1.value, 2.0, rtol=1e-10)

    def test_rejects_wrong_unit(self):
        with pytest.raises(u.UnitsError):
            calculate_diffusion_length(1 * u.meter)


class TestLogHelpers:
    def test_log_center_symmetric(self):
        center = calculate_log_center(1e2, 1e4)
        np.testing.assert_allclose(center, 3.0, rtol=1e-10)

    def test_log_width(self):
        width = calculate_log_width(1e2, 1e4)
        np.testing.assert_allclose(width, 1.0, rtol=1e-10)


class TestCreateEllipseData:
    @pytest.fixture
    def sample_row(self):
        return pd.Series(
            {
                "Time_min": 1e2 * u.second,
                "Time_max": 1e4 * u.second,
                "Space_min": 1e-6 * u.m**3,
                "Space_max": 1e-2 * u.m**3,
            }
        )

    def test_returns_two_arrays(self, sample_row):
        x, y = create_ellipse_data(sample_row, n_points=100)
        assert len(x) == 200  # 2 * n_points (upper + lower arcs)
        assert len(y) == 200

    def test_default_space_on_x_x_is_space(self, sample_row):
        """Default space_on_x=True maps x=space, y=time."""
        x, y = create_ellipse_data(sample_row, n_points=100)
        # x should span space range
        np.testing.assert_allclose(min(x), 1e-6, rtol=1e-2)
        np.testing.assert_allclose(max(x), 1e-2, rtol=1e-2)
        # y should span time range
        np.testing.assert_allclose(min(y), 1e2, rtol=1e-2)
        np.testing.assert_allclose(max(y), 1e4, rtol=1e-2)

    def test_not_boyd_x_is_time(self, sample_row):
        """space_on_x=False maps x=time, y=space."""
        x, y = create_ellipse_data(sample_row, n_points=100, space_on_x=False)
        # x should span time range
        np.testing.assert_allclose(min(x), 1e2, rtol=1e-2)
        np.testing.assert_allclose(max(x), 1e4, rtol=1e-2)
        # y should span space range
        np.testing.assert_allclose(min(y), 1e-6, rtol=1e-2)
        np.testing.assert_allclose(max(y), 1e-2, rtol=1e-2)

    def test_closed_polygon(self, sample_row):
        x, y = create_ellipse_data(sample_row, n_points=100)
        # First and last points should be the same x (both at x_min)
        np.testing.assert_allclose(x[0], x[-1], rtol=1e-2)

    def test_boyd_and_stommel_are_transposed(self, sample_row):
        """space_on_x True and False should swap space/time across x/y axes.

        The ellipse is parameterized by sweeping x = logspace(x_min, x_max)
        and computing y. When axes swap, a different variable is swept, so
        the discrete sample points differ. We verify that both orientations
        cover the same physical ranges (space and time bounds from the input).
        """
        xs, ys = create_ellipse_data(sample_row, n_points=100, space_on_x=True)
        xc, yc = create_ellipse_data(sample_row, n_points=100, space_on_x=False)

        space_min = sample_row.Space_min.value
        space_max = sample_row.Space_max.value
        time_min = sample_row.Time_min.value
        time_max = sample_row.Time_max.value

        # Stommel: x = space, y = time
        # x is swept so it exactly hits space bounds; y reaches time bounds approximately
        np.testing.assert_allclose(min(xs), space_min, rtol=1e-10)
        np.testing.assert_allclose(max(xs), space_max, rtol=1e-10)
        # Classic: x = time, y = space
        np.testing.assert_allclose(min(xc), time_min, rtol=1e-10)
        np.testing.assert_allclose(max(xc), time_max, rtol=1e-10)

    def test_degenerate_time_raises(self):
        """Degenerate time axis should raise ValueError."""
        row = pd.Series(
            {
                "Time_min": 1e3 * u.second,
                "Time_max": 1e3 * u.second,
                "Space_min": 1e-6 * u.m**3,
                "Space_max": 1e-2 * u.m**3,
            }
        )
        with pytest.raises(ValueError, match="Degenerate axis"):
            create_ellipse_data(row)

    def test_degenerate_space_raises(self):
        """Degenerate space axis should raise ValueError."""
        row = pd.Series(
            {
                "Time_min": 1e2 * u.second,
                "Time_max": 1e4 * u.second,
                "Space_min": 1e-6 * u.m**3,
                "Space_max": 1e-6 * u.m**3,
            }
        )
        with pytest.raises(ValueError, match="Degenerate axis"):
            create_ellipse_data(row)


class TestCalculateLog10YForEllipse:
    """Tests for the log10-space ellipse Y solver."""

    def test_at_center_returns_extremes(self):
        # At x = 10^c_x, inner term is zero → y = c_y ± b
        c_x, c_y, a, b = 3.0, 5.0, 2.0, 1.5
        x = 10**c_x
        plus, minus = calculate_log10_y_for_ellipse(x, c_y, c_x, b, a)
        np.testing.assert_allclose(plus, c_y + b, rtol=1e-10)
        np.testing.assert_allclose(minus, c_y - b, rtol=1e-10)

    def test_at_edge_returns_center(self):
        # At x = 10^(c_x + a) (right edge), y should collapse to c_y
        c_x, c_y, a, b = 3.0, 5.0, 2.0, 1.5
        x = 10 ** (c_x + a)
        plus, minus = calculate_log10_y_for_ellipse(x, c_y, c_x, b, a)
        np.testing.assert_allclose(plus, c_y, atol=1e-6)
        np.testing.assert_allclose(minus, c_y, atol=1e-6)

    def test_symmetric_about_center(self):
        c_x, c_y, a, b = 3.0, 5.0, 2.0, 1.5
        # Points equidistant from center in log-x should give same y spread
        x_left = 10 ** (c_x - 1.0)
        x_right = 10 ** (c_x + 1.0)
        p_l, m_l = calculate_log10_y_for_ellipse(x_left, c_y, c_x, b, a)
        p_r, m_r = calculate_log10_y_for_ellipse(x_right, c_y, c_x, b, a)
        np.testing.assert_allclose(p_l - m_l, p_r - m_r, rtol=1e-10)


class TestClassifyProcessGeometry:
    """Tests for geometry classification of process axes."""

    @staticmethod
    def _make_row(t_min, t_max, s_min, s_max):
        return pd.Series(
            {
                "Time_min": t_min * u.second,
                "Time_max": t_max * u.second,
                "Space_min": s_min * u.m**3,
                "Space_max": s_max * u.m**3,
            }
        )

    def test_ellipse(self):
        row = self._make_row(1, 100, 1e-18, 1e-13)
        assert classify_process_geometry(row) == "ellipse"

    def test_vline(self):
        row = self._make_row(1, 1, 1e-18, 1e-13)
        assert classify_process_geometry(row) == "vline"

    def test_hline(self):
        row = self._make_row(1, 100, 1e-16, 1e-16)
        assert classify_process_geometry(row) == "hline"

    def test_point(self):
        row = self._make_row(1, 1, 1e-16, 1e-16)
        assert classify_process_geometry(row) == "point"

    def test_near_equal_now_degenerate(self):
        """Values differing by < 0.1 OOM are degenerate with default threshold."""
        row = self._make_row(1.0, 1.001, 1e-16, 1.001e-16)
        assert classify_process_geometry(row) == "point"

    def test_small_but_visible_range_is_ellipse(self):
        """Values spanning 0.1+ OOM are non-degenerate (1.0 vs 1.3 = 0.114 OOM)."""
        row = self._make_row(1.0, 1.3, 1e-16, 1.3e-16)
        assert classify_process_geometry(row) == "ellipse"

    def test_custom_threshold(self):
        """Passing a tighter threshold restores old behavior."""
        row = self._make_row(1.0, 1.001, 1e-16, 1.001e-16)
        assert classify_process_geometry(row, threshold=1e-10) == "ellipse"
