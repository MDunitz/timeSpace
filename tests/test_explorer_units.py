import astropy.units as u
import pytest

from timeSpace.explorer.units import format_number, format_time_range, format_volume_range


@pytest.mark.parametrize(
    "value, expected",
    [(1, "1"), (12.34, "12.3"), (1234.5, "1,230"), (123456, "1.23 × 10⁵"), (1e21, "10²¹"), (0.0012, "1.2 × 10⁻³")],
)
def test_format_number(value, expected):
    assert format_number(value) == expected


@pytest.mark.parametrize(
    "t_min, t_max, expected",
    [
        (1.39e-11, 1e-9, "13.9 ps – 1 ns"),
        (8.6e9, 1.6e10, "273 – 507 yr"),
        (7.6e11, 7.6e11, "24.1 kyr"),
        (5.05e15, 5.68e15, "160 – 180 Myr"),
        (3.156e7, 3.156e7, "1 yr"),
        (44700, 44700, "12.4 h"),
    ],
)
def test_format_time_range(t_min, t_max, expected):
    assert format_time_range(t_min * u.s, t_max * u.s) == expected


@pytest.mark.parametrize(
    "v_min, v_max, expected",
    [
        (9e-17, 1e-16, "90 – 100 fL"),
        (7e-5, 3e-4, "70 – 300 mL"),
        (1e-12, 1e-9, "1 nL – 1 µL"),
        (2.48e6, 3.33e6, "2.48 × 10⁶ – 3.33 × 10⁶ m³"),
        (1.08e21, 1.08e21, "1.08 × 10¹² km³"),
    ],
)
def test_format_volume_range(v_min, v_max, expected):
    assert format_volume_range(v_min * u.m**3, v_max * u.m**3) == expected
