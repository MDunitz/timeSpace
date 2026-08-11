"""Live drift check: pull the real Google Form sheets and run the ETL.

Unlike the fixture-based tests, this hits Google Sheets over the network to
catch drift in the *live* forms -- a renamed question, a re-introduced trailing
space, a changed answer-option format -- the moment it happens, rather than when
someone next refreshes a saved CSV.

It is opt-in so the normal (offline, deterministic) test matrix never depends on
network or Google availability:

    TIMESPACE_LIVE_FORM_TESTS=1 python -m pytest tests/test_form_live.py

The GitHub Actions ``live-form-tests`` job sets that variable. Sheet IDs default
to the copied US forms and can be overridden without a code change via the
``TIMESPACE_PROCESS_SHEET_ID`` / ``TIMESPACE_MEASUREMENT_SHEET_ID`` env vars (or
repo variables of the same name), so repointing at the canonical forms is a
settings change, not a commit.

Adapted to the --form architecture (PR #81): normalization is an explicit step
(normalize_form_responses / normalize_measurement_form_responses) that runs
before the transform, rather than being folded into the transform.
"""

import os

import pytest

from timeSpace.constants import (
    TEMPLATE_PROCESS_FORM_URI,
    TEMPLATE_MEASUREMENT_FORM_URI,
)
from timeSpace.data_processing import extract_google_sheet
from timeSpace.etl import (
    normalize_form_responses,
    normalize_measurement_form_responses,
    transform_process_response_sheet,
    transform_measurement_sheet,
)

LIVE = os.environ.get("TIMESPACE_LIVE_FORM_TESTS") == "1"

# `or` (not a get default) so an unset repo variable -- which GitHub Actions
# passes as an empty string, not absent -- falls back to the copy IDs.
PROCESS_SHEET_ID = os.environ.get("TIMESPACE_PROCESS_SHEET_ID") or TEMPLATE_PROCESS_FORM_URI
MEASUREMENT_SHEET_ID = os.environ.get("TIMESPACE_MEASUREMENT_SHEET_ID") or TEMPLATE_MEASUREMENT_FORM_URI

pytestmark = pytest.mark.skipif(
    not LIVE,
    reason="live Google Form pull disabled; set TIMESPACE_LIVE_FORM_TESTS=1 to enable",
)


def test_live_processes_form_normalizes_and_transforms():
    raw = extract_google_sheet(PROCESS_SHEET_ID, "live-processes", from_cache=False)
    out = transform_process_response_sheet(normalize_form_responses(raw))
    for col in ("Time_min", "Time_max", "Space_min", "Space_max", "Name", "geometry"):
        assert col in out.columns, f"live processes form drift: transform did not produce {col}"


def test_live_measurements_form_normalizes_and_transforms():
    raw = extract_google_sheet(MEASUREMENT_SHEET_ID, "live-measurements", from_cache=False)
    out = transform_measurement_sheet(normalize_measurement_form_responses(raw))
    for col in ("Time_value", "Space_value", "Name"):
        assert col in out.columns, f"live measurements form drift: transform did not produce {col}"
