import pandas as pd
import pytest
import astropy.units as u
from timeSpace.etl import process_magnitude_column, transform_predefined_processes, transform_process_response_sheet
from timeSpace.constants import base_time, base_space, POSSIBLE_COL_LIST


class TestProcessMagnitudeColumn:
    def test_time_column_applies_seconds(self):
        row = pd.Series({"Time_min": "1e3"})
        result = process_magnitude_column(row, "Time_min")
        assert result.unit == base_time
        assert result.value == 1e3

    def test_space_column_applies_cubic_meters(self):
        row = pd.Series({"Space_max": "1e-6"})
        result = process_magnitude_column(row, "Space_max")
        assert result.unit == base_space
        assert result.value == 1e-6

    def test_colon_separated_value(self):
        # Google Sheets export sometimes has "1e3:extra" format
        row = pd.Series({"Time_max": "1e5:some_note"})
        result = process_magnitude_column(row, "Time_max")
        assert result.value == 1e5

    def test_numeric_input(self):
        # Already a float, not a string
        row = pd.Series({"Space_min": 1e-12})
        result = process_magnitude_column(row, "Space_min")
        assert result.unit == base_space
        assert result.value == 1e-12


class TestTransformPredefinedProcesses:
    def test_produces_expected_columns(self):

        df = pd.DataFrame(
            {
                "ShortName": ["Nitrification", "Denitrification"],
                "Prefix": ["N-cycle", "N-cycle"],
                "Color": ["#33CCCC", "#009999"],
                "Time_min": ["1e2", "1e4"],
                "Time_max": ["1e6", "1e8"],
                "Space_min": ["1e-12", "1e-6"],
                "Space_max": ["1e-6", "1e0"],
            }
        )
        result = transform_predefined_processes(df)
        for col in ["x_coords", "y_coords", "FillAlpha", "TextAlpha"]:
            assert col in result.columns, f"Missing column: {col}"

    def test_units_applied(self):

        df = pd.DataFrame(
            {
                "ShortName": ["Test"],
                "Prefix": ["X"],
                "Color": ["#000000"],
                "Time_min": ["1e3"],
                "Time_max": ["1e5"],
                "Space_min": ["1e-9"],
                "Space_max": ["1e-3"],
            }
        )
        result = transform_predefined_processes(df)
        row = result.iloc[0]
        assert row.Time_min.unit == u.second
        assert row.Space_max.unit == u.m**3

    def test_ellipse_data_generated(self):

        df = pd.DataFrame(
            {
                "ShortName": ["Test"],
                "Prefix": ["X"],
                "Color": ["#000000"],
                "Time_min": ["1e2"],
                "Time_max": ["1e4"],
                "Space_min": ["1e-6"],
                "Space_max": ["1e-2"],
            }
        )
        result = transform_predefined_processes(df)
        row = result.iloc[0]
        assert len(row.x_coords) == 2000  # default n_points=1000, 2 arcs
        assert len(row.y_coords) == 2000


class TestTransformProcessResponseSheet:
    """Happy-path tests for transform_process_response_sheet (#22, #24)."""

    def _basic_df(self):
        return pd.DataFrame(
            {
                "ShortName": ["A", "B"],
                "Time_min": ["1e-3", "1e2"],
                "Time_max": ["1e0", "1e6"],
                "Space_min": ["1e-12", "1e-9"],
                "Space_max": ["1e-6", "1e-3"],
            }
        )

    def test_produces_expected_columns(self):
        result = transform_process_response_sheet(self._basic_df())
        for col in ["x_coords", "y_coords", "FillAlpha", "TextAlpha", "Name", "geometry"]:
            assert col in result.columns, f"Missing column: {col}"

    def test_units_applied(self):
        result = transform_process_response_sheet(self._basic_df())
        row = result.iloc[0]
        assert row.Time_min.unit == u.second
        assert row.Space_max.unit == u.m**3

    def test_filters_inverted_ranges(self):
        df = pd.DataFrame(
            {
                "ShortName": ["valid", "bad-time", "bad-space"],
                "Time_min": ["1", "100", "1"],
                "Time_max": ["10", "10", "10"],  # row 1: 100 > 10 (bad)
                "Space_min": ["1e-9", "1e-9", "1e-3"],
                "Space_max": ["1e-6", "1e-6", "1e-9"],  # row 2: 1e-3 > 1e-9 (bad)
            }
        )
        result = transform_process_response_sheet(df)
        assert len(result) == 1
        assert result.iloc[0].ShortName == "valid"

    def test_space_on_x_default_stommel_orientation(self):
        # Default: x_coords come from space, y_coords from time
        # x bounds are exact (logspace endpoints); y bounds are within 0.1% (ellipse equation)
        result = transform_process_response_sheet(self._basic_df())
        row = result.iloc[0]
        assert row.x_coords.min() == pytest.approx(row.Space_min.value, rel=1e-9)
        assert row.x_coords.max() == pytest.approx(row.Space_max.value, rel=1e-9)
        assert row.y_coords.min() == pytest.approx(row.Time_min.value, rel=1e-3)
        assert row.y_coords.max() == pytest.approx(row.Time_max.value, rel=1e-3)

    def test_space_on_x_false_boyd_orientation(self):
        # space_on_x=False: x_coords come from time, y_coords from space
        result = transform_process_response_sheet(self._basic_df(), space_on_x=False)
        row = result.iloc[0]
        assert row.x_coords.min() == pytest.approx(row.Time_min.value, rel=1e-9)
        assert row.x_coords.max() == pytest.approx(row.Time_max.value, rel=1e-9)
        assert row.y_coords.min() == pytest.approx(row.Space_min.value, rel=1e-3)
        assert row.y_coords.max() == pytest.approx(row.Space_max.value, rel=1e-3)

    def test_n_points_controls_vertex_count(self):
        result_default = transform_process_response_sheet(self._basic_df())
        assert len(result_default.iloc[0].x_coords) == 2000  # 2 * 1000

        result_small = transform_process_response_sheet(self._basic_df(), n_points=50)
        assert len(result_small.iloc[0].x_coords) == 100  # 2 * 50

    def test_label_x_is_geometric_mean_of_time_range(self):
        result = transform_process_response_sheet(self._basic_df())
        row = result.iloc[0]
        expected = (row.Time_min.value * row.Time_max.value) ** 0.5
        assert row.label_x == pytest.approx(expected, rel=1e-9)

    def test_label_y_is_geometric_mean_of_space_range(self):
        result = transform_process_response_sheet(self._basic_df())
        row = result.iloc[0]
        expected = (row.Space_min.value * row.Space_max.value) ** 0.5
        assert row.label_y == pytest.approx(expected, rel=1e-9)

    def test_label_x_csv_override_preserved(self):
        # If input already has label_x, ETL should not overwrite
        df = self._basic_df()
        df["label_x"] = [42.0, 99.0]
        result = transform_process_response_sheet(
            df, possible_col_list=POSSIBLE_COL_LIST + ["label_x"]
        )
        assert result.label_x.iloc[0] == 42.0
        assert result.label_x.iloc[1] == 99.0

    def test_label_y_csv_override_preserved(self):
        df = self._basic_df()
        df["label_y"] = [1.5, 2.5]
        result = transform_process_response_sheet(
            df, possible_col_list=POSSIBLE_COL_LIST + ["label_y"]
        )
        assert result.label_y.iloc[0] == 1.5
        assert result.label_y.iloc[1] == 2.5
