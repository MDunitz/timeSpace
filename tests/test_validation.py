"""Tests for timeSpace.validation.

Every fixture here is synthetic. Nothing asserts anything about the bundled
datasets, so the seven data-correction PRs in flight cannot break this file and
this file cannot pre-empt their review. The pass over `data/datasets/` belongs
in a follow-up once those land.
"""

import pandas as pd
import pytest
from astropy import units as u

from timeSpace import validation as v


def frame(**cols):
    """Build a one-row Stommel frame, defaulting anything not given."""
    base = {"Name": "x", "Time_min": 1.0, "Time_max": 10.0, "Space_min": 1e-18, "Space_max": 1e-15}
    base.update(cols)
    return pd.DataFrame([base])


# ── parsing ────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("1.00E-15: 10 cubic µm", 1e-15),
        (1e-15, 1e-15),
        (1e-15 * u.m**3, 1e-15),
        ("3600", 3600.0),
        ("not a number", None),
        (float("nan"), None),
    ],
)
def test_numeric_parses_every_cell_form(raw, expected):
    assert v._numeric(raw) == expected


def test_label_is_the_half_after_the_colon():
    assert v._label("1.00E-15: 10 cubic µm") == "10 cubic µm"
    assert v._label(1e-15) is None


# ── finite / monotonic ─────────────────────────────────────────────


def test_finite_rejects_nonpositive_and_unparseable():
    findings = v.check_finite(frame(Space_min=0.0, Time_min="banana"))
    assert {f.column for f in findings} == {"Space_min", "Time_min"}
    assert all(f.severity == v.ERROR for f in findings)


def test_finite_accepts_a_clean_row():
    assert v.check_finite(frame()) == []


def test_monotonic_catches_inverted_bounds():
    findings = v.check_monotonic(frame(Space_min=1e-9, Space_max=1e-15))
    assert len(findings) == 1
    assert findings[0].column == "Space_max"


def test_monotonic_allows_equal_bounds():
    assert v.check_monotonic(frame(Time_min=5.0, Time_max=5.0)) == []


# ── cubed-prefix labels ────────────────────────────────────────────


@pytest.mark.parametrize(
    "cell",
    [
        "1.00E-27: 1 cubic nm",
        "1.00E-24: 10 cubic nm",
        "1.00E-18: 1 cubic µm",
        "1.00E-15: 10 cubic µm",
        "1.00E-12: 100 cubic µm",
        "1.00E+09: 1 cubic km",
        "1.00E+12: 10 cubic km",
        "1.00E+18: 1 cubic Mm",
    ],
)
def test_cubed_prefix_ladder_is_consistent(cell):
    """N cubic X means an N-by-X cube, so (10 µm)^3 = 1e-15 m3."""
    assert v.check_cubed_prefix_labels(frame(Space_min=cell, Space_max=cell)) == []


def test_cubed_prefix_catches_the_conventional_misreading():
    """If someone 'fixes' 10 cubic µm to mean 10 µm^3, the value is 100x off."""
    findings = v.check_cubed_prefix_labels(frame(Space_min="1.00E-17: 10 cubic µm"))
    assert len(findings) == 1
    assert "1e-15" in findings[0].message or "1.00e-15" in findings[0].message


def test_cubed_prefix_accepts_ascii_um():
    assert v.check_cubed_prefix_labels(frame(Space_min="1.00E-15: 10 cubic um")) == []


def test_cubed_prefix_ignores_prose_labels():
    assert v.check_cubed_prefix_labels(frame(Space_min="1.00E-15: single cell")) == []


# ── explicit volume-unit labels ────────────────────────────────────


def test_volume_unit_catches_the_fL_pL_confusion():
    """1e-15 m3 is 1 pL; calling it 1 fL is a factor of 1000."""
    findings = v.check_volume_unit_labels(frame(Space_min="1.00E-15: 1 fL (single cell)"))
    assert len(findings) == 1


def test_volume_unit_accepts_the_correction():
    assert v.check_volume_unit_labels(frame(Space_min="1.00E-15: 1 pL (single cell)")) == []


@pytest.mark.parametrize("cell", ["1.00E-09: 1 mm³ (single particle)", "1.00E-06: 1 mL", "1.00E-03: 1 L"])
def test_volume_unit_accepts_correct_labels(cell):
    assert v.check_volume_unit_labels(frame(Space_min=cell, Space_max=cell)) == []


def test_volume_unit_catches_a_displaced_mm_cubed():
    """1 mm3 is 1e-9 m3, not 1e-8."""
    assert len(v.check_volume_unit_labels(frame(Space_min="1.00E-08: 1 mm³"))) == 1


# ── duration labels ────────────────────────────────────────────────


@pytest.mark.parametrize(
    "cell",
    [
        "1.00E+03: ~15 minutes",
        "1.00E+04: ~3 hours",
        "1.00E+05: ~1 day",
        "6.05E+05: ~1 week",
        "1.00E+07: ~4 months",
        "1.00E+10: ~310 years",
    ],
)
def test_duration_labels_within_tolerance_pass(cell):
    assert v.check_duration_labels(frame(Time_min=cell, Time_max=cell)) == []


def test_duration_catches_a_decade_slip():
    """1e3 s is 16.7 minutes, not 3 hours."""
    findings = v.check_duration_labels(frame(Time_min="1.00E+03: ~3 hours"))
    assert len(findings) == 1
    assert "10.8x off" in findings[0].message


def test_duration_catches_hours_labelled_on_a_months_value():
    """1e7 s is 116 days."""
    assert len(v.check_duration_labels(frame(Time_max="1.00E+07: ~3 hours"))) == 1


def test_duration_tolerance_is_configurable():
    cell = "1.00E+05: ~1 day"  # 1.16x
    assert v.check_duration_labels(frame(Time_min=cell), tol=1.1) != []
    assert v.check_duration_labels(frame(Time_min=cell), tol=2.0) == []


# ── length-vs-volume heuristic ─────────────────────────────────────


def test_lengths_masquerading_as_volumes_are_flagged():
    df = pd.DataFrame(
        {
            "Name": ["a", "b", "c"],
            "Time_min": [1.0, 1.0, 1.0],
            "Time_max": [10.0, 10.0, 10.0],
            "Space_min": [1e-3, 1.0, 1e3],  # mm, m, km read as lengths
            "Space_max": [1.0, 1e3, 1e5],
        }
    )
    findings = v.check_spatial_values_look_like_volumes(df)
    assert len(findings) == 1
    assert findings[0].severity == v.WARNING
    assert "calculate_sphere_volume" in findings[0].message


def test_a_dataset_straddling_the_band_is_not_flagged():
    df = pd.DataFrame(
        {
            "Name": ["cell", "pond", "ocean"],
            "Time_min": [1.0, 1.0, 1.0],
            "Time_max": [10.0, 10.0, 10.0],
            "Space_min": [1e-18, 1e3, 1e15],
            "Space_max": [1e-15, 1e4, 1.37e18],
        }
    )
    assert v.check_spatial_values_look_like_volumes(df) == []


def test_two_rows_inside_the_band_are_not_enough_to_fire():
    df = pd.DataFrame(
        {
            "Name": ["a", "b"],
            "Time_min": [1.0] * 2,
            "Time_max": [10.0] * 2,
            "Space_min": [1.0, 10.0],
            "Space_max": [10.0, 100.0],
        }
    )
    assert v.check_spatial_values_look_like_volumes(df) == []


def test_length_warning_can_be_switched_off():
    df = pd.DataFrame(
        {
            "Name": ["a", "b", "c"],
            "Time_min": [1.0] * 3,
            "Time_max": [10.0] * 3,
            "Space_min": [1.0, 10.0, 100.0],
            "Space_max": [10.0, 100.0, 1000.0],
        }
    )
    assert v.validate_dataset(df, warn_on_lengths=True) != []
    assert v.validate_dataset(df, warn_on_lengths=False) == []


# ── driver ─────────────────────────────────────────────────────────


def test_validate_dataset_is_clean_on_a_well_formed_frame():
    df = pd.DataFrame(
        {
            "Name": ["bacterium", "eddy"],
            "Time_min": ["1.20E+03: ~20 minutes", "6.05E+05: ~1 week"],
            "Time_max": ["7.20E+03: ~2 hours", "1.00E+07: ~4 months"],
            "Space_min": ["1.00E-18: 1 cubic µm", "5.00E+10"],
            "Space_max": ["1.00E-15: 10 cubic µm", "2.00E+15"],
        }
    )
    assert v.validate_dataset(df) == []


def test_validate_dataset_sorts_errors_before_warnings():
    df = pd.DataFrame(
        {
            "Name": ["a", "b", "c"],
            "Time_min": [1.0, 1.0, 1.0],
            "Time_max": [10.0, 10.0, 10.0],
            "Space_min": [10.0, "1.00E+02: 10 cubic m", 30.0],  # second is (10 m)^3 = 1e3, not 1e2
            "Space_max": [100.0, 1000.0, 300.0],
        }
    )
    findings = v.validate_dataset(df)
    assert [f.severity for f in findings] == [v.ERROR, v.WARNING]
    assert len(v.errors(findings)) == 1


def test_format_findings_reports_a_clean_bill():
    assert v.format_findings([]) == "No findings."


def test_finding_str_names_the_row_and_column():
    text = str(v.Finding("demo", v.ERROR, "boom", row=3, column="Space_min"))
    assert "row 3" in text and "Space_min" in text and "ERROR" in text
