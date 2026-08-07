"""Regression tests for the copied US regional Google Form response sheets.

Mads copied the live US measurements and processes Forms in 2026; the copies
have new spreadsheet IDs but should stay schema-compatible with the existing
ingestion path (rename map -> transform). These tests guard two things:

1. The saved fixtures still expose the exact raw question titles the rename
   maps key on. A changed title, or a re-introduced trailing space in a mapped
   column (cf. the #77 ETL breakage), fails ``test_exact_headers`` loudly
   instead of silently dropping a column downstream.
2. Applying ``US_PROCESS_COLUMN_MAP`` / ``US_MEASUREMENT_COLUMN_MAP`` (the same
   constants ``projects/prime_regional_US.py`` uses) and running the transform
   yields the internal columns plotting needs, with correct astropy units.

Fixtures (saved via the gviz ``out:csv`` endpoint, no index column):
- ``data/datasets/us_processes_copy.csv``    (sheet 1kDh...,  gid 243872990)
- ``data/datasets/us_measurements_copy.csv`` (sheet 1xlgy..., gid 776962054)

Refresh procedure: re-download from
``https://docs.google.com/spreadsheets/d/{id}/gviz/tq?tqx=out:csv&gid={gid}``
so headers stay index-free. Saving via ``extract_google_sheet(cache=True)``
writes a leading index column; ``_form_headers`` tolerates that artifact, but
prefer the gviz endpoint to keep the fixtures clean.
"""

import pandas as pd
import pytest

from timeSpace import PROJECT_ROOT
from timeSpace.constants import (
    US_PROCESS_COLUMN_MAP,
    US_MEASUREMENT_COLUMN_MAP,
    base_time,
    base_space,
)
from timeSpace.etl import transform_process_response_sheet, transform_measurement_sheet

DATASETS = PROJECT_ROOT / "data" / "datasets"

EXPECTED_PROCESS_HEADERS = [
    "Timestamp",
    "Your initials",
    "Lab",
    "Short Project Name (max 10 char)",
    "Minimum Time Scale",
    "Maximum Time Scale",
    "Minimum Spatial Scale",
    "Maximum Spatial Scale",
    "What concept does your research address?",
    "What question are you trying to answer with your research?",
]

EXPECTED_MEASUREMENT_HEADERS = [
    "Timestamp",
    "Initials",
    "Lab",
    "Short Project Name (max 10 char)",
    "Time Scale",
    "Spatial Scale",
    "Optional: What concept does your research address?",
    "Optional: What question are you trying to answer with your research?",
]


def _form_headers(df):
    """Form question titles, dropping any leading unnamed index column.

    ``df.to_csv()`` (as used by ``extract_google_sheet(cache=True)``) prepends
    an unnamed index column; that is a serialization artifact, not a form
    change, so we ignore it and compare only real question titles. Trailing or
    leading whitespace on a real column is preserved, so it still fails.
    """
    return [c for c in df.columns if not str(c).startswith("Unnamed")]


@pytest.fixture
def processes_raw():
    return pd.read_csv(DATASETS / "us_processes_copy.csv")


@pytest.fixture
def measurements_raw():
    return pd.read_csv(DATASETS / "us_measurements_copy.csv")


class TestProcessFormSchema:
    def test_exact_headers(self, processes_raw):
        assert _form_headers(processes_raw) == EXPECTED_PROCESS_HEADERS

    def test_rename_keys_present(self, processes_raw):
        missing = set(US_PROCESS_COLUMN_MAP) - set(processes_raw.columns)
        assert not missing, f"rename keys absent from form: {missing}"

    def test_transform_pipeline(self, processes_raw):
        df = processes_raw.rename(columns=US_PROCESS_COLUMN_MAP)
        out = transform_process_response_sheet(df)
        for col in ("Time_min", "Time_max", "Space_min", "Space_max", "Name", "geometry", "x_coords", "y_coords"):
            assert col in out.columns, f"missing transformed column: {col}"
        assert out.iloc[0].Time_min.unit == base_time
        assert out.iloc[0].Space_max.unit == base_space


class TestMeasurementFormSchema:
    def test_exact_headers(self, measurements_raw):
        assert _form_headers(measurements_raw) == EXPECTED_MEASUREMENT_HEADERS

    def test_rename_keys_present(self, measurements_raw):
        missing = set(US_MEASUREMENT_COLUMN_MAP) - set(measurements_raw.columns)
        assert not missing, f"rename keys absent from form: {missing}"

    def test_transform_pipeline(self, measurements_raw):
        df = measurements_raw.rename(columns=US_MEASUREMENT_COLUMN_MAP)
        out = transform_measurement_sheet(df)
        for col in ("Time_value", "Space_value", "Name"):
            assert col in out.columns, f"missing transformed column: {col}"
        assert out.iloc[0].Time.unit == base_time
        assert out.iloc[0].Space.unit == base_space
