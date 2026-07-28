"""Tests for timeSpace.energy."""

import pandas as pd
import pytest

from timeSpace import energy


def frame(*energy_types):
    return pd.DataFrame({"Name": list("abcdefg")[: len(energy_types)], "Energy_type": list(energy_types)})


def test_order_and_colors_cover_the_same_taxonomy():
    assert set(energy.ENERGY_ORDER) == set(energy.ENERGY_COLORS)


def test_validate_accepts_known_types():
    assert energy.validate_energy_types(frame("Chemical", "Thermal")) == []


def test_validate_reports_unknown_types():
    assert energy.validate_energy_types(frame("Chemical", "Kinetic")) == ["Kinetic"]


def test_validate_raises_without_the_column():
    with pytest.raises(ValueError, match="Energy_type"):
        energy.validate_energy_types(pd.DataFrame({"Name": ["a"]}))


def test_assign_maps_every_row_to_its_color():
    out = energy.assign_energy_colors(frame("Chemical", "Radiative"))
    assert out.Color.tolist() == [energy.ENERGY_COLORS["Chemical"], energy.ENERGY_COLORS["Radiative"]]


def test_assign_does_not_mutate_the_input():
    df = frame("Chemical")
    energy.assign_energy_colors(df)
    assert "Color" not in df.columns


def test_assign_raises_on_unknown_rather_than_colouring_them_grey():
    with pytest.raises(ValueError, match="Kinetic"):
        energy.assign_energy_colors(frame("Chemical", "Kinetic"))


def test_assign_accepts_an_explicit_default_for_unknown():
    out = energy.assign_energy_colors(frame("Chemical", "Kinetic"), default="#999999")
    assert out.Color.tolist() == [energy.ENERGY_COLORS["Chemical"], "#999999"]


def test_present_returns_legend_order_not_dataset_order():
    assert energy.energy_types_present(frame("Mechanical", "Radiative")) == ["Radiative", "Mechanical"]


def test_present_omits_absent_types():
    assert energy.energy_types_present(frame("Chemical")) == ["Chemical"]


def test_bundled_desert_farm_csv_uses_only_known_energy_types():
    """The one dataset that carries energy tags must stay inside the taxonomy."""
    from pathlib import Path

    csv = Path(__file__).resolve().parent.parent / "docs" / "desert_farm_processes.csv"
    assert energy.validate_energy_types(pd.read_csv(csv)) == []
