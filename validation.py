"""Consistency checks for Stommel diagram datasets.

Every check here is an *internal* consistency check: it compares a value to
something else the same file already asserts. None of them can tell you that a
correctly-formatted value is wrong about the world - that a hurricane really
occupies 1e19 m3 rather than 1e14 - which still needs a human or a literature
cross-check.

The checks run over any DataFrame with the Stommel schema, not just the
bundled datasets, so they are equally usable on a Google Sheet pulled through
`etl.transform_process_response_sheet`.
"""

import math
import re
from dataclasses import dataclass

from astropy import units as u

SPACE_COLS = ("Space_min", "Space_max")
TIME_COLS = ("Time_min", "Time_max")
MAGNITUDE_COLS = SPACE_COLS + TIME_COLS

ERROR = "error"
WARNING = "warning"

# Spatial labels are cubed prefixes: "10 cubic um" means a 10-um cube, i.e.
# (10 um)^3 = 1e-15 m3, not 10 um^3. See CONVENTIONS.md.
_CUBED_PREFIX_RE = re.compile(r"^\s*([\d.]+)\s+cubic\s+(nm|µm|um|mm|cm|dm|m|km|Mm)\s*$")

# Labels that name an explicit unit of volume rather than a cubed prefix.
_VOLUME_UNIT_RE = re.compile(r"^\s*([\d.]+)\s*(fL|pL|nL|µL|uL|mL|L|nm³|µm³|um³|mm³|cm³|m³|km³)\b")

# Durations named in prose: "~3 hours", "~4 months", "~310 years".
_DURATION_RE = re.compile(r"~?\s*([\d.]+)\s*(second|minute|hour|day|week|month|year|kyr|Myr)s?\b", re.I)

_DURATION_SECONDS = {
    "second": 1.0,
    "minute": 60.0,
    "hour": 3600.0,
    "day": 86400.0,
    "week": 604800.0,
    "month": 2629800.0,  # Julian year / 12
    "year": 31557600.0,  # Julian year
    "kyr": 31557600.0e3,
    "myr": 31557600.0e6,
}

# Below this the values are plausibly molecular volumes and above it planetary,
# but in between a bare length reads as a volume without complaint. See #3.
LENGTH_SUSPICION_BAND = (1e-6, 1e6)


@dataclass(frozen=True)
class Finding:
    """One problem found in a dataset.

    `row` is the positional index into the DataFrame, not the label.
    """

    check: str
    severity: str
    message: str
    row: int = None
    column: str = None

    def __str__(self):
        where = ""
        if self.row is not None:
            where = f" [row {self.row}"
            where += f", {self.column}]" if self.column else "]"
        return f"{self.severity.upper()}: {self.check}{where}: {self.message}"


def _numeric(value):
    """Return the numeric prefix of a `1.00E-15: 10 cubic um` cell, or None.

    Mirrors `etl.process_magnitude_column`, which parses only the text before
    the colon. Quantities are unwrapped so checks work pre- and post-ETL.
    """
    if value is None:
        return None
    if isinstance(value, u.Quantity):
        return float(value.value)
    if isinstance(value, (int, float)):
        return None if isinstance(value, float) and math.isnan(value) else float(value)
    try:
        return float(str(value).split(":")[0])
    except ValueError:
        return None


def _label(value):
    """Return the human-readable half of a `value: label` cell, or None."""
    if not isinstance(value, str) or ":" not in value:
        return None
    return value.split(":", 1)[1].strip()


def check_finite(df):
    """Every magnitude cell must parse to a finite, positive number.

    Non-positive values cannot be placed on a log axis; unparseable ones are
    silently dropped by the ETL and vanish from the figure.
    """
    findings = []
    for col in MAGNITUDE_COLS:
        if col not in df.columns:
            continue
        for i, raw in enumerate(df[col]):
            value = _numeric(raw)
            if value is None:
                findings.append(Finding("finite", ERROR, f"does not parse to a number: {raw!r}", i, col))
            elif not math.isfinite(value):
                findings.append(Finding("finite", ERROR, f"is not finite: {value}", i, col))
            elif value <= 0:
                findings.append(Finding("finite", ERROR, f"is not positive ({value}); log axis requires > 0", i, col))
    return findings


def check_monotonic(df):
    """`*_max` must be at least `*_min` on every row."""
    findings = []
    for lo_col, hi_col in (SPACE_COLS, TIME_COLS):
        if lo_col not in df.columns or hi_col not in df.columns:
            continue
        for i, (lo_raw, hi_raw) in enumerate(zip(df[lo_col], df[hi_col])):
            lo, hi = _numeric(lo_raw), _numeric(hi_raw)
            if lo is None or hi is None:
                continue
            if hi < lo:
                findings.append(Finding("monotonic", ERROR, f"{hi_col} ({hi:g}) < {lo_col} ({lo:g})", i, hi_col))
    return findings


def check_cubed_prefix_labels(df, rtol=1e-9):
    """Spatial gloss `N cubic X` must equal (N·X)³ in m³.

    Convention: "10 cubic um" is a 10-micrometre cube, (10 um)^3 = 1e-15 m3.
    Read conventionally it would be 10 um^3 = 1e-17 m3, so a wrong value here
    is off by a factor of 100 or more and is invisible on inspection.
    """
    findings = []
    for col in SPACE_COLS:
        if col not in df.columns:
            continue
        for i, raw in enumerate(df[col]):
            label = _label(raw)
            value = _numeric(raw)
            if label is None or value is None:
                continue
            match = _CUBED_PREFIX_RE.match(label)
            if not match:
                continue
            side, prefix = float(match.group(1)), match.group(2).replace("um", "µm")
            expected = ((side * u.Unit(prefix)) ** 3).to_value(u.m**3)
            if not math.isclose(value, expected, rel_tol=rtol):
                findings.append(
                    Finding(
                        "cubed_prefix_label",
                        ERROR,
                        f"{label!r} is ({side:g} {prefix})^3 = {expected:.3g} m3, but the value is {value:.3g}",
                        i,
                        col,
                    )
                )
    return findings


def check_volume_unit_labels(df, rtol=1e-9):
    """Spatial gloss naming an explicit volume unit must match the value.

    Catches the fL/pL class: 1e-15 m3 is 1 pL, and calling it 1 fL is a
    factor of 1000.
    """
    findings = []
    for col in SPACE_COLS:
        if col not in df.columns:
            continue
        for i, raw in enumerate(df[col]):
            label, value = _label(raw), _numeric(raw)
            if label is None or value is None:
                continue
            match = _VOLUME_UNIT_RE.match(label)
            if not match:
                continue
            amount = float(match.group(1))
            unit = match.group(2).replace("uL", "µL").replace("um³", "µm³")
            expected = (amount * u.Unit(unit.replace("³", "3"))).to_value(u.m**3)
            if not math.isclose(value, expected, rel_tol=rtol):
                findings.append(
                    Finding(
                        "volume_unit_label",
                        ERROR,
                        f"{label!r} is {expected:.3g} m3, but the value is {value:.3g}",
                        i,
                        col,
                    )
                )
    return findings


def check_duration_labels(df, tol=2.0):
    """Temporal gloss must be within `tol`× of the value it names.

    A factor of 2 is deliberately loose: these are order-of-magnitude ladder
    rungs, so `1e5 s: ~1 day` (1.16 days) is fine while `1e3 s: ~3 hours`
    (16.7 minutes) is not.
    """
    findings = []
    for col in TIME_COLS:
        if col not in df.columns:
            continue
        for i, raw in enumerate(df[col]):
            label, value = _label(raw), _numeric(raw)
            if label is None or value is None or value <= 0:
                continue
            match = _DURATION_RE.search(label)
            if not match:
                continue
            expected = float(match.group(1)) * _DURATION_SECONDS[match.group(2).lower()]
            ratio = max(value / expected, expected / value)
            if ratio > tol:
                findings.append(
                    Finding(
                        "duration_label",
                        ERROR,
                        f"{label!r} is {expected:.3g} s, but the value is {value:.3g} s ({ratio:.1f}x off)",
                        i,
                        col,
                    )
                )
    return findings


def check_spatial_values_look_like_volumes(df, band=LENGTH_SUSPICION_BAND, min_rows=3):
    """Warn when every spatial value sits in the band where lengths hide.

    The spatial axis is m3, but `Space_min`/`Space_max` do not say so, and a
    dataset transcribed as characteristic lengths plots without complaint. A
    genuine volume dataset almost always straddles the band - cells at 1e-18,
    ocean basins at 1e15 - so the signal is the whole column staying inside
    it, not any single row. Warning only; a pond-scale dataset can legitimately
    live entirely between 1e-6 and 1e6 m3.

    Needs at least `min_rows` rows to fire - two rows inside the band is not
    evidence of anything, and small fixtures would trip it constantly.
    """
    lo, hi = band
    values = []
    for col in SPACE_COLS:
        if col not in df.columns:
            continue
        values += [v for v in (_numeric(raw) for raw in df[col]) if v is not None and v > 0]
    if len(df) < min_rows or not values or not all(lo <= v <= hi for v in values):
        return []
    return [
        Finding(
            "spatial_values_look_like_lengths",
            WARNING,
            f"all {len(values)} spatial values fall in [{lo:g}, {hi:g}] m3, the range where a column of "
            f"characteristic lengths is indistinguishable from volumes. If these are lengths, convert them "
            f"with calculations.calculate_sphere_volume() first.",
        )
    ]


DEFAULT_CHECKS = (
    check_finite,
    check_monotonic,
    check_cubed_prefix_labels,
    check_volume_unit_labels,
    check_duration_labels,
    check_spatial_values_look_like_volumes,
)


def validate_dataset(df, checks=DEFAULT_CHECKS, warn_on_lengths=True):
    """Run consistency checks over a Stommel dataset.

    Parameters
    ----------
    df : DataFrame
        Stommel schema. Cells may be plain numbers, astropy Quantities, or
        `value: label` strings; checks that need a label skip the others.
    checks : iterable of callable
        Each takes the DataFrame and returns a list of Finding.
    warn_on_lengths : bool
        Include the length-vs-volume heuristic. Off for datasets known to sit
        entirely at one scale.

    Returns
    -------
    list of Finding
        Errors first, then warnings; row order within each.
    """
    findings = []
    for check in checks:
        if not warn_on_lengths and check is check_spatial_values_look_like_volumes:
            continue
        findings += check(df)
    return sorted(findings, key=lambda f: (f.severity != ERROR, f.row if f.row is not None else -1))


def errors(findings):
    """Filter to findings that are errors."""
    return [f for f in findings if f.severity == ERROR]


def format_findings(findings):
    """Render findings as newline-joined text, or a clean-bill message."""
    if not findings:
        return "No findings."
    return "\n".join(str(f) for f in findings)
