"""Tests for ETL input validation (#224) and spatial length warnings (#226)."""

import pandas as pd
import pytest

from timeSpace.etl import transform_predefined_processes, transform_process_response_sheet


class TestTransformPredefinedValidation:
    """Column validation in transform_predefined_processes."""

    def test_missing_columns_raises(self):
        df = pd.DataFrame({"Name": ["A"], "Time_min": [1]})
        with pytest.raises(ValueError, match="missing required columns"):
            transform_predefined_processes(df)

    def test_error_names_missing_columns(self):
        df = pd.DataFrame({"Name": ["A"], "Time_min": [1], "Time_max": [2]})
        with pytest.raises(ValueError, match="Space_min"):
            transform_predefined_processes(df)


class TestTransformResponseSheetValidation:
    """Column validation in transform_process_response_sheet (#224)."""

    def test_missing_columns_raises(self):
        df = pd.DataFrame({"Name": ["A"], "Time_min": [1]})
        with pytest.raises(ValueError, match="missing required columns"):
            transform_process_response_sheet(df)

    def test_suggests_predefined_function(self):
        df = pd.DataFrame({"Name": ["A"], "Time_min": [1]})
        with pytest.raises(ValueError, match="transform_predefined_processes"):
            transform_process_response_sheet(df)
