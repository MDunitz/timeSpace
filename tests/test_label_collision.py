import warnings

import numpy as np
import pandas as pd

from timeSpace.label_collision import (
    data_to_pixel,
    pixel_to_data,
    estimate_label_bbox,
    _boxes_overlap,
)
from timeSpace.plotting_helpers import (
    resolve_label_overlaps,
    count_overlaps,
)

# Standard Stommel diagram ranges used across tests
X_RANGE = (1e-3, 1e13)  # time axis: milliseconds to ~300 kyr
Y_RANGE = (1e-28, 1e22)  # space axis: molecules to ocean basins


class TestDataToPixel:
    def test_log_transform_endpoints(self):
        """Axis endpoints should map to 0 and fig dimension."""
        px_x, px_y = data_to_pixel(
            [1e-3, 1e13],
            [1e-28, 1e22],
            X_RANGE,
            Y_RANGE,
            900,
            600,
        )
        np.testing.assert_allclose(px_x, [0.0, 900.0])
        np.testing.assert_allclose(px_y, [0.0, 600.0])

    def test_midpoint(self):
        """Geometric midpoint of log range should map to half the dimension."""
        px_x, _ = data_to_pixel(
            [1e5],
            [1e-3],
            X_RANGE,
            Y_RANGE,
            900,
            600,
        )
        np.testing.assert_allclose(px_x, [450.0])

    def test_roundtrip(self):
        """data_to_pixel → pixel_to_data should recover original coords."""
        x_orig = np.array([1e-1, 1e3, 1e8])
        y_orig = np.array([1e-20, 1e0, 1e15])

        px_x, px_y = data_to_pixel(x_orig, y_orig, X_RANGE, Y_RANGE, 900, 600)
        x_back, y_back = pixel_to_data(px_x, px_y, X_RANGE, Y_RANGE, 900, 600)

        np.testing.assert_allclose(x_back, x_orig, rtol=1e-10)
        np.testing.assert_allclose(y_back, y_orig, rtol=1e-10)


class TestEstimateBbox:
    def test_known_string(self):
        """'Photosynthesis' at 12px should be approximately 97x16 px."""
        w, h = estimate_label_bbox("Photosynthesis", font_size_px=12)
        assert 90 < w < 110
        assert 14 < h < 18

    def test_empty_string(self):
        """Empty string should have zero width, nonzero height."""
        w, h = estimate_label_bbox("", font_size_px=12)
        assert w == 0.0
        assert h > 0

    def test_scales_with_font_size(self):
        """Larger font -> proportionally larger bbox."""
        w12, h12 = estimate_label_bbox("Test", font_size_px=12)
        w24, h24 = estimate_label_bbox("Test", font_size_px=24)
        np.testing.assert_allclose(w24 / w12, 2.0)
        np.testing.assert_allclose(h24 / h12, 2.0)


class TestBoxesOverlap:
    def test_overlapping(self):
        assert _boxes_overlap(0, 0, 10, 10, 5, 5, 10, 10)

    def test_non_overlapping(self):
        assert not _boxes_overlap(0, 0, 10, 10, 100, 100, 10, 10)

    def test_touching_edges_no_overlap(self):
        # Boxes touching at edge are not overlapping (< not <=)
        assert not _boxes_overlap(0, 0, 10, 10, 10, 0, 10, 10)

    def test_padding_creates_overlap(self):
        """Boxes just beyond touching should overlap with padding."""
        assert not _boxes_overlap(0, 0, 10, 10, 10, 0, 10, 10, padding=0)
        assert _boxes_overlap(0, 0, 10, 10, 10, 0, 10, 10, padding=1)


class TestResolveLabelOverlaps:
    def test_no_overlap_unchanged(self):
        """Labels that don't overlap should converge immediately."""
        df = pd.DataFrame(
            {
                "Name": ["A", "B", "C"],
                "label_x": [1e-1, 1e5, 1e11],
                "label_y": [1e-20, 1e0, 1e18],
            }
        )
        result, converged = resolve_label_overlaps(df, X_RANGE, Y_RANGE)
        assert converged
        assert "label_x_offset" in result.columns
        assert "label_y_offset" in result.columns

    def test_two_overlapping_labels_separate(self):
        """Two labels at the same position should be pushed apart."""
        df = pd.DataFrame(
            {
                "Name": ["Label One", "Label Two"],
                "label_x": [1e3, 1e3],
                "label_y": [1e0, 1e0],
            }
        )
        result, converged = resolve_label_overlaps(df, X_RANGE, Y_RANGE)
        assert converged
        assert count_overlaps(result, X_RANGE, Y_RANGE) == 0

    def test_respects_figure_bounds(self):
        """Labels should not be pushed outside the figure range."""
        df = pd.DataFrame(
            {
                "Name": ["Edge Label A", "Edge Label B"],
                "label_x": [1e-2, 1e-2],
                "label_y": [1e-27, 1e-27],
            }
        )
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            result, _ = resolve_label_overlaps(df, X_RANGE, Y_RANGE)
        anchor_px_x, anchor_px_y = data_to_pixel(
            result["label_x"].values,
            result["label_y"].values,
            X_RANGE,
            Y_RANGE,
            900,
            600,
        )
        px_x = anchor_px_x + result["label_x_offset"].values
        px_y = anchor_px_y + result["label_y_offset"].values
        assert np.all(px_x >= 0)
        assert np.all(px_x <= 900)
        assert np.all(px_y >= 0)
        assert np.all(px_y <= 600)

    def test_many_labels_no_overlap(self):
        """With 20+ labels, no final bounding boxes should overlap."""
        rng = np.random.RandomState(42)
        n = 25
        log_x = rng.uniform(-3, 13, n)
        log_y = rng.uniform(-28, 22, n)
        names = [f"Process {i}" for i in range(n)]

        df = pd.DataFrame(
            {
                "Name": names,
                "label_x": 10.0**log_x,
                "label_y": 10.0**log_y,
            }
        )
        result, converged = resolve_label_overlaps(
            df,
            X_RANGE,
            Y_RANGE,
            max_iterations=200,
        )
        assert converged
        assert count_overlaps(result, X_RANGE, Y_RANGE) == 0

    def test_manual_override_preserved(self):
        """Labels with existing x_offset/y_offset should not be moved."""
        df = pd.DataFrame(
            {
                "Name": ["Manual", "Auto"],
                "label_x": [1e3, 1e3],
                "label_y": [1e0, 1e0],
                "x_offset": [100.0, None],
                "y_offset": [200.0, None],
            }
        )
        result, _ = resolve_label_overlaps(df, X_RANGE, Y_RANGE)
        manual_row = result[result["Name"] == "Manual"].iloc[0]
        assert manual_row["label_x_offset"] == 100.0
        assert manual_row["label_y_offset"] == 200.0

    def test_log_scale_distances(self):
        """Labels 1+ orders of magnitude apart should not overlap."""
        df = pd.DataFrame(
            {
                "Name": ["Short A", "Short B"],
                "label_x": [1e0, 1e3],
                "label_y": [1e0, 1e5],
            }
        )
        result, converged = resolve_label_overlaps(df, X_RANGE, Y_RANGE)
        assert converged
        assert count_overlaps(result, X_RANGE, Y_RANGE) == 0

    def test_returns_copy(self):
        """resolve_label_overlaps should not mutate the input DataFrame."""
        df = pd.DataFrame(
            {
                "Name": ["A"],
                "label_x": [1e3],
                "label_y": [1e0],
            }
        )
        original_cols = set(df.columns)
        resolve_label_overlaps(df, X_RANGE, Y_RANGE)
        assert set(df.columns) == original_cols

    def test_converged_true_when_resolved(self):
        """Converged flag should be True when all overlaps are resolved."""
        df = pd.DataFrame(
            {
                "Name": ["A", "B"],
                "label_x": [1e0, 1e0],
                "label_y": [1e0, 1e0],
            }
        )
        _, converged = resolve_label_overlaps(df, X_RANGE, Y_RANGE)
        assert converged is True

    def test_converged_false_when_impossible(self):
        """Converged flag should be False and warning raised when solver cannot finish."""
        # Two overlapping labels with zero iterations — guaranteed non-convergence
        df = pd.DataFrame(
            {
                "Name": ["Label A", "Label B"],
                "label_x": [1e3, 1e3],
                "label_y": [1e0, 1e0],
            }
        )
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            _, converged = resolve_label_overlaps(df, X_RANGE, Y_RANGE, max_iterations=0)
            assert converged is False
            assert len(w) == 1
            assert "did not converge" in str(w[0].message)
            assert "overlapping label pair" in str(w[0].message)
