"""End-to-end guard for the documented Google Form response flow.

A raw Google Form export has human-readable headers ("Minimum Time Scale", ...)
and admits partial submissions. The README documents

    extract_google_sheet(...) -> transform_process_response_sheet(...)
      -> set_color_palettes_by_lab(...) -> add_processes(...)

This test runs that flow against the bundled real export (us_processes.csv) so
the header normalization and incomplete-row handling in the ETL cannot regress.
"""

import pandas as pd

import timeSpace
from timeSpace import create_space_time_figure, add_processes, set_color_palettes_by_lab
from timeSpace.etl import transform_process_response_sheet, transform_measurement_sheet

RAW_FORM_CSV = timeSpace.PROJECT_ROOT / "data" / "datasets" / "us_processes.csv"
RAW_MEASUREMENT_CSV = timeSpace.PROJECT_ROOT / "data" / "datasets" / "us_measurements.csv"


def _raw():
    return pd.read_csv(RAW_FORM_CSV)


def test_raw_form_headers_are_normalized():
    raw = _raw()
    # the export does NOT contain the schema names; the ETL must map them
    assert "Minimum Time Scale" in raw.columns
    assert "Time_min" not in raw.columns
    out = transform_process_response_sheet(raw)
    for col in ("Time_min", "Time_max", "Space_min", "Space_max", "geometry", "Name"):
        assert col in out.columns


def test_incomplete_responses_are_dropped():
    raw = _raw()
    out = transform_process_response_sheet(raw)
    # every surviving row has all four bounds and a name
    assert out[["Time_min", "Time_max", "Space_min", "Space_max"]].notna().all().all()
    assert out["Name"].notna().all()
    assert len(out) > 0


def test_full_documented_flow_renders():
    out = transform_process_response_sheet(_raw())
    out = set_color_palettes_by_lab(out)
    assert out["Color"].notna().all()
    p = add_processes(create_space_time_figure(), out)
    assert p is not None


def test_transform_is_idempotent_on_schema_headers():
    # already-renamed input still works (pass-through rename)
    schema = _raw().rename(
        columns={
            "Minimum Time Scale": "Time_min",
            "Maximum Time Scale": "Time_max",
            "Minimum Spatial Scale": "Space_min",
            "Maximum Spatial Scale": "Space_max",
        }
    )
    out = transform_process_response_sheet(schema)
    assert len(out) > 0


def test_raw_measurement_headers_are_normalized():
    raw = pd.read_csv(RAW_MEASUREMENT_CSV)
    # default measurement export uses Initials / Short Project Name, not schema names
    assert "Initials" in raw.columns
    assert "Prefix" not in raw.columns
    out = transform_measurement_sheet(raw)
    for col in ("Name", "Time_value", "Space_value"):
        assert col in out.columns
    assert len(out) > 0


def test_measurement_transform_idempotent_on_schema_headers():
    schema = pd.read_csv(RAW_MEASUREMENT_CSV).rename(
        columns={"Initials": "Prefix", "Short Project Name (max 10 char)": "ShortName"}
    )
    out = transform_measurement_sheet(schema)
    assert len(out) > 0


def test_process_headers_with_trailing_whitespace_are_handled():
    # Live Google Forms emit trailing spaces in question titles
    # ("Minimum Time Scale "); the bundled export has them stripped, so
    # simulate the live headers to lock whitespace robustness.
    raw = pd.read_csv(RAW_FORM_CSV).rename(columns=lambda c: str(c) + " ")
    out = transform_process_response_sheet(raw)
    assert {"Time_min", "Time_max", "Space_min", "Space_max"} <= set(out.columns)
    assert len(out) > 0


def test_measurement_headers_with_trailing_whitespace_are_handled():
    raw = pd.read_csv(RAW_MEASUREMENT_CSV).rename(columns=lambda c: str(c) + " ")
    out = transform_measurement_sheet(raw)
    assert "Time_value" in out.columns
    assert len(out) > 0
