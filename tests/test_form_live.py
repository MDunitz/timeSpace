"""Live drift check: pull the real Google Form sheets and run the ETL.

Unlike the fixture-based tests, this hits Google Sheets over the network to
catch drift in the *live* forms — a renamed question, a re-introduced trailing
space, a changed answer-option format — the moment it happens, rather than when
someone next refreshes a saved CSV.

It is opt-in so the normal (offline, deterministic) test matrix never depends on
network or Google availability:

    TIMESPACE_LIVE_FORM_TESTS=1 python -m pytest tests/test_form_live.py

The GitHub Actions ``live-form-tests`` job sets that variable. Sheet IDs default
to the copied US forms and can be overridden without a code change via the
``TIMESPACE_PROCESS_SHEET_ID`` / ``TIMESPACE_MEASUREMENT_SHEET_ID`` env vars (or
repo variables of the same name), so repointing at the canonical forms is a
settings change, not a commit.
"""

import os

import pytest

from timeSpace.data_processing import extract_google_sheet
from timeSpace.etl import transform_process_response_sheet, transform_measurement_sheet

LIVE = os.environ.get("TIMESPACE_LIVE_FORM_TESTS") == "1"

# `or` (not a get default) so an unset repo variable — which GitHub Actions
# passes as an empty string, not absent — falls back to the copy IDs.
PROCESS_SHEET_ID = os.environ.get("TIMESPACE_PROCESS_SHEET_ID") or "1kDh5Ja8x3ic1OhsYR3aPT7ZHu7MDoM3HN5aiYprIONA"
MEASUREMENT_SHEET_ID = (
    os.environ.get("TIMESPACE_MEASUREMENT_SHEET_ID") or "1xlgy0Mos930oAFEUBp4P1S87aOWzdWMdB6bebKJRY-c"
)

pytestmark = pytest.mark.skipif(
    not LIVE,
    reason="live Google Form pull disabled; set TIMESPACE_LIVE_FORM_TESTS=1 to enable",
)


def test_live_processes_form_normalizes_and_transforms():
    df = extract_google_sheet(PROCESS_SHEET_ID, "live-processes", from_cache=False)
    out = transform_process_response_sheet(df)  # self-normalizes raw form headers
    for col in ("Time_min", "Time_max", "Space_min", "Space_max", "Name", "geometry"):
        assert col in out.columns, f"live processes form drift: transform did not produce {col}"


def test_live_measurements_form_normalizes_and_transforms():
    df = extract_google_sheet(MEASUREMENT_SHEET_ID, "live-measurements", from_cache=False)
    out = transform_measurement_sheet(df)  # self-normalizes raw form headers
    for col in ("Time_value", "Space_value", "Name"):
        assert col in out.columns, f"live measurements form drift: transform did not produce {col}"
