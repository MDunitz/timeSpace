import pandas as pd
import astropy.units as u
from timeSpace.etl import process_magnitude_column, transform_predefined_processes
from timeSpace.constants import base_time, base_space


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
