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
from timeSpace.etl import transform_process_response_sheet

RAW_FORM_CSV = timeSpace.PROJECT_ROOT / "data" / "datasets" / "us_processes.csv"


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
