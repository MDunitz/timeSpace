import numpy as np
import pandas as pd
import astropy.units as u

from timeSpace.plotting_helpers import (
    _log_extent_area,
    set_fill_alpha,
    create_name,
)


class TestCalculateNumberOfMagnitudeCombos:
    def test_single_decade_each(self):
        # 1 decade time × 1 decade space = 1, plus the +2 offset → 3
        result = _log_extent_area(1e0, 1e1, 1e0, 1e1)
        np.testing.assert_allclose(result, 3.0, rtol=1e-10)

    def test_multi_decade(self):
        # 4 decades time × 2 decades space = 8 + 2 = 10
        result = _log_extent_area(1e0, 1e4, 1e-6, 1e-4)
        np.testing.assert_allclose(result, 10.0, rtol=1e-10)

    def test_always_positive(self):
        # Even minimal span (zero decades) → 0 + 2 = 2 (avoids div-by-zero)
        result = _log_extent_area(1e0, 1e0, 1e0, 1e0)
        assert result == 2.0


class TestSetFillAlpha:
    def test_small_ellipse_higher_alpha(self):
        small = pd.Series(
            {
                "Time_min": 1e0 * u.second,
                "Time_max": 1e1 * u.second,
                "Space_min": 1e0 * u.m**3,
                "Space_max": 1e1 * u.m**3,
            }
        )
        large = pd.Series(
            {
                "Time_min": 1e0 * u.second,
                "Time_max": 1e10 * u.second,
                "Space_min": 1e-18 * u.m**3,
                "Space_max": 1e10 * u.m**3,
            }
        )
        assert set_fill_alpha(small) > set_fill_alpha(large)

    def test_alpha_between_zero_and_one(self):
        row = pd.Series(
            {
                "Time_min": 1e2 * u.second,
                "Time_max": 1e6 * u.second,
                "Space_min": 1e-6 * u.m**3,
                "Space_max": 1e0 * u.m**3,
            }
        )
        alpha = set_fill_alpha(row)
        assert 0 < alpha <= 1

    def test_alpha_capped_at_one(self):
        # Very small area → alpha formula could exceed 1, but is clamped
        row = pd.Series(
            {
                "Time_min": 1e0 * u.second,
                "Time_max": 1.01e0 * u.second,
                "Space_min": 1e0 * u.m**3,
                "Space_max": 1.01e0 * u.m**3,
            }
        )
        assert set_fill_alpha(row) <= 1.0


class TestCreateName:
    def test_short_name_unchanged(self):
        row = pd.Series({"ShortName": "Nitrification", "Prefix": ""})
        assert create_name(row) == "Nitrification"

    def test_long_name_gets_newline(self):
        long_name = "Very Long Biogeochemical Process Name That Exceeds Fifty Characters Easily"
        row = pd.Series({"ShortName": long_name, "Prefix": ""})
        result = create_name(row)
        assert "\n" in result
        # Both halves should be non-empty
        parts = result.split("\n")
        assert len(parts) == 2
        assert all(len(p.strip()) > 0 for p in parts)

    def test_prefix_included_when_requested(self):
        row = pd.Series({"ShortName": "Nitrification", "Prefix": "Marine"})
        result = create_name(row, include_prefix=True)
        assert result == "Marine - Nitrification"

    def test_prefix_excluded_by_default(self):
        row = pd.Series({"ShortName": "Nitrification", "Prefix": "Marine"})
        result = create_name(row)
        assert result == "Nitrification"
