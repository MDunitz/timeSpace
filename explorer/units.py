"""Human-readable time and volume labels for explorer tooltips.

Values stay in SI (s, m³) everywhere else; these helpers only pick the
unit a reader would use for a magnitude and format the number.
"""

import numpy as np
import astropy.units as u

TIME_UNITS = [
    (u.fs, "fs"),
    (u.ps, "ps"),
    (u.ns, "ns"),
    (u.us, "µs"),
    (u.ms, "ms"),
    (u.s, "s"),
    (u.min, "min"),
    (u.h, "h"),
    (u.day, "days"),
    (u.yr, "yr"),
    (u.kyr, "kyr"),
    (u.Myr, "Myr"),
    (u.Gyr, "Gyr"),
]

VOLUME_UNITS = [
    (u.nm**3, "nm³"),
    (u.fL, "fL"),
    (u.pL, "pL"),
    (u.nL, "nL"),
    (u.uL, "µL"),
    (u.mL, "mL"),
    (u.L, "L"),
    (u.m**3, "m³"),
    (u.km**3, "km³"),
]

# Smallest value that still prints as 1 at three significant figures; keeps
# 1e-9 s from landing in "1,000 ps" through float error.
ROUNDS_TO_ONE = 0.9995

_SUPERSCRIPTS = str.maketrans("-0123456789", "⁻⁰¹²³⁴⁵⁶⁷⁸⁹")


def format_number(value, sig=3):
    """Format a positive number to `sig` significant figures.

    Plain digits from 1 up to 9,999; otherwise mantissa × 10ⁿ.
    """
    exponent = int(np.floor(np.log10(value)))
    rounded = round(value, sig - 1 - exponent)
    if 1 <= rounded < 1e4:
        return (
            f"{rounded:,.{max(sig - 1 - exponent, 0)}f}".rstrip("0").rstrip(".") if rounded % 1 else f"{rounded:,.0f}"
        )
    exponent = int(np.floor(np.log10(rounded)))
    mantissa = f"{rounded / 10**exponent:.{sig - 1}f}".rstrip("0").rstrip(".")
    power = "10" + str(exponent).translate(_SUPERSCRIPTS)
    return power if mantissa == "1" else f"{mantissa} × {power}"


def pick_unit(quantity, units):
    """Return (value, symbol) in the largest unit that keeps the value near or above 1.

    Falls back to the smallest unit when the quantity is below all of them.
    """
    best = units[0]
    for unit, symbol in units:
        if quantity.to_value(unit) >= ROUNDS_TO_ONE:
            best = (unit, symbol)
    return quantity.to_value(best[0]), best[1]


def format_quantity(quantity, units):
    value, symbol = pick_unit(quantity, units)
    return f"{format_number(value)} {symbol}"


def format_range(q_min, q_max, units):
    """Label a min–max pair, collapsing to one value when they coincide."""
    lo, hi = format_quantity(q_min, units), format_quantity(q_max, units)
    if lo == hi:
        return lo
    lo_value, lo_symbol = pick_unit(q_min, units)
    hi_value, hi_symbol = pick_unit(q_max, units)
    if lo_symbol == hi_symbol:
        return f"{format_number(lo_value)} – {format_number(hi_value)} {hi_symbol}"
    return f"{lo} – {hi}"


def format_time_range(t_min, t_max):
    return format_range(t_min, t_max, TIME_UNITS)


def format_volume_range(v_min, v_max):
    return format_range(v_min, v_max, VOLUME_UNITS)
