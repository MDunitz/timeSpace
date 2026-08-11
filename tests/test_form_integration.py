"""Contract tests for the interactive-activity Google Form templates.

The forms are meant to be *copied*: someone runs their own workshop, collects
responses in their own sheet, and renders a diagram without editing columns by
hand. That promise has two failure surfaces, and these tests pin both.

1. **Schema drift.** The fixtures are response exports from the current
   template forms (test submissions, not workshop data). If a question title
   is edited, deleted, or reordered in the template, ``test_exact_headers``
   fails — otherwise the break only shows up for a third party, mid-workshop,
   as ``missing required columns: {Time_min, ...}``.

2. **The copy-and-run path itself.** ``build_form_figure`` takes the sheet
   exactly as the form emits it through to HTML. Tested end to end so a
   regression anywhere in normalize -> transform -> color -> plot is caught.

Fixtures were saved via the gviz ``out:csv`` endpoint, which returns headers
verbatim and without an index column::

    https://docs.google.com/spreadsheets/d/{id}/gviz/tq?tqx=out:csv&gid={gid}

- ``form_processes_responses.csv``    — sheet ``TEMPLATE_PROCESS_FORM_URI``,     gid 243872990
- ``form_measurements_responses.csv`` — sheet ``TEMPLATE_MEASUREMENT_FORM_URI``, gid 776962054

Refreshing them via ``extract_google_sheet(cache=True)`` instead writes a
leading index column; ``_form_headers`` tolerates that artifact, but prefer
gviz to keep the fixtures clean.
"""

from pathlib import Path

import pandas as pd
import pytest

from timeSpace.cli import build_form_figure, write_html
from timeSpace.constants import (
    PROCESS_FORM_COLUMN_MAP,
    MEASUREMENT_FORM_COLUMN_MAP,
    base_time,
    base_space,
)
from timeSpace.etl import (
    normalize_form_responses,
    normalize_measurement_form_responses,
    transform_process_response_sheet,
    transform_measurement_sheet,
)

FIXTURES = Path(__file__).parent / "fixtures"

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
    """Form question titles, ignoring any leading unnamed index column.

    ``df.to_csv()`` prepends an unnamed index; that is a serialization
    artifact, not a form change. Whitespace on a real question title is
    preserved so drift still fails ``test_exact_headers``.
    """
    return [c for c in df.columns if not str(c).startswith("Unnamed")]


@pytest.fixture
def processes_raw():
    return pd.read_csv(FIXTURES / "form_processes_responses.csv")


@pytest.fixture
def measurements_raw():
    return pd.read_csv(FIXTURES / "form_measurements_responses.csv")


class TestProcessFormSchema:
    def test_exact_headers(self, processes_raw):
        assert _form_headers(processes_raw) == EXPECTED_PROCESS_HEADERS

    def test_column_map_keys_all_present(self, processes_raw):
        missing = set(PROCESS_FORM_COLUMN_MAP) - set(processes_raw.columns)
        assert not missing, f"column map references questions not in the form: {missing}"

    def test_normalize_then_transform(self, processes_raw):
        out = transform_process_response_sheet(normalize_form_responses(processes_raw))
        for col in ("Time_min", "Time_max", "Space_min", "Space_max", "Name", "geometry", "x_coords", "y_coords"):
            assert col in out.columns, f"missing transformed column: {col}"
        assert out.iloc[0].Time_min.unit == base_time
        assert out.iloc[0].Space_max.unit == base_space


class TestMeasurementFormSchema:
    def test_exact_headers(self, measurements_raw):
        assert _form_headers(measurements_raw) == EXPECTED_MEASUREMENT_HEADERS

    def test_column_map_keys_all_present(self, measurements_raw):
        missing = set(MEASUREMENT_FORM_COLUMN_MAP) - set(measurements_raw.columns)
        assert not missing, f"column map references questions not in the form: {missing}"

    def test_normalize_then_transform(self, measurements_raw):
        out = transform_measurement_sheet(normalize_measurement_form_responses(measurements_raw))
        for col in ("Time_value", "Space_value", "Name"):
            assert col in out.columns, f"missing transformed column: {col}"
        assert out.iloc[0].Time.unit == base_time
        assert out.iloc[0].Space.unit == base_space


class TestNormalizeFormResponses:
    """normalize_form_responses is the entry point a form copier hits first."""

    def test_tolerates_trailing_whitespace_in_question_title(self, processes_raw):
        # Google Forms intermittently emits trailing spaces in question titles;
        # an exact dict rename silently no-ops on these (the #77 breakage).
        drifted = processes_raw.rename(columns={"Minimum Time Scale": "Minimum Time Scale "})
        assert "Time_min" in normalize_form_responses(drifted).columns

    def test_tolerates_leading_whitespace_in_question_title(self, processes_raw):
        drifted = processes_raw.rename(columns={"Maximum Spatial Scale": " Maximum Spatial Scale"})
        assert "Space_max" in normalize_form_responses(drifted).columns

    def test_missing_question_names_itself(self, processes_raw):
        with pytest.raises(ValueError, match="Maximum Time Scale"):
            normalize_form_responses(processes_raw.drop(columns=["Maximum Time Scale"]))

    def test_missing_question_lists_available_columns(self, processes_raw):
        with pytest.raises(ValueError, match="Sheet has:"):
            normalize_form_responses(processes_raw.drop(columns=["Minimum Spatial Scale"]))

    def test_unmapped_columns_retained(self, processes_raw):
        # Timestamp and the free-text questions survive normalization; the
        # transforms drop them via POSSIBLE_COL_LIST filtering, not this step.
        assert "Timestamp" in normalize_form_responses(processes_raw).columns


class TestCopyAndRunPath:
    """End-to-end: a copied form's raw response sheet renders without editing."""

    def test_raw_form_sheet_builds_figure(self, processes_raw):
        figure = build_form_figure(processes_raw, title="Activity")
        assert figure is not None

    def test_colors_assigned_from_lab(self, processes_raw):
        # The form has no Color question — build_form_figure must supply one,
        # otherwise add_processes raises on the missing column.
        normalized = normalize_form_responses(processes_raw)
        transformed = transform_process_response_sheet(normalized)
        assert "Color" not in transformed.columns
        assert build_form_figure(processes_raw) is not None

    def test_writes_self_contained_html(self, processes_raw, tmp_path):
        output = write_html(build_form_figure(processes_raw), tmp_path / "activity.html")
        assert output.exists()
        assert "bokeh" in output.read_text().lower()

    def test_time_on_x_orientation(self, processes_raw):
        assert build_form_figure(processes_raw, space_on_x=False) is not None


class TestIncompleteResponsesDropped:
    """Real forms admit partial submissions; the transforms drop them before
    the unit parse rather than propagating NaN into astropy quantities.
    Ported from #77."""

    def test_process_row_missing_a_bound_is_dropped(self, processes_raw):
        normalized = normalize_form_responses(processes_raw)
        incomplete = normalized.iloc[[0]].copy()
        incomplete.loc[incomplete.index[0], "Space_max"] = None
        combined = pd.concat([normalized, incomplete], ignore_index=True)
        # The complete row survives, the bound-less row is dropped before parse.
        assert len(transform_process_response_sheet(combined)) == len(normalized)

    def test_measurement_row_missing_a_scale_is_dropped(self, measurements_raw):
        normalized = normalize_measurement_form_responses(measurements_raw)
        incomplete = normalized.iloc[[0]].copy()
        incomplete.loc[incomplete.index[0], "Time Scale"] = None
        combined = pd.concat([normalized, incomplete], ignore_index=True)
        assert len(transform_measurement_sheet(combined)) == len(normalized)
