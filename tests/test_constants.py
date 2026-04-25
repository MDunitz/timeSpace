import astropy.units as u

import numpy as np

from timeSpace.constants import (
    base_time,
    base_space,
    O2_diffusion_rate,
    CO2_diffusion_rate,
    glucose_diffusion_rate,
    OCEAN_VOLUME,
    OCEAN_VOLUME_cubic_meters,
    TIME_MARKERS,
    SPACE_MARKERS,
    CO2_VOLUME,
    CO2_VDW_RADIUS,
    OCEAN_SURFACE_AREA,
    OCEAN_MIXED_LAYER_DEPTH,
    OCEAN_SURFACE_VOLUME,
    ROUGH_ESTIMATE_EVEREST_VOLUME,
    EVEREST_BASE_RADIUS,
    EVEREST_HEIGHT,
)


class TestBaseUnits:
    def test_base_time_is_seconds(self):
        assert base_time == u.second

    def test_base_space_is_cubic_meters(self):
        assert base_space == u.m**3


class TestDiffusionCoefficients:
    # All diffusion coefficients should be in cm^2/s as defined,
    # and convertible to m^2/s for calculations.

    def test_o2_units(self):
        converted = O2_diffusion_rate.to(u.m**2 / u.s)
        assert converted.unit == u.m**2 / u.s

    def test_co2_units(self):
        converted = CO2_diffusion_rate.to(u.m**2 / u.s)
        assert converted.unit == u.m**2 / u.s

    def test_glucose_units(self):
        converted = glucose_diffusion_rate.to(u.m**2 / u.s)
        assert converted.unit == u.m**2 / u.s

    def test_o2_order_of_magnitude(self):
        # O2 diffusion in water ~2e-5 cm^2/s = 2e-9 m^2/s
        val = O2_diffusion_rate.to(u.m**2 / u.s).value
        assert 1e-10 < val < 1e-8


class TestOceanConstants:
    def test_ocean_volume_convertible(self):
        vol = OCEAN_VOLUME.to(u.m**3)
        assert vol.unit == u.m**3

    def test_ocean_volume_cubic_meters_consistent(self):
        assert OCEAN_VOLUME_cubic_meters.unit == u.m**3
        expected = OCEAN_VOLUME.to(u.m**3)
        assert abs(OCEAN_VOLUME_cubic_meters.value - expected.value) < 1e10


class TestMarkerKeys:
    def test_time_markers_are_numeric(self):
        for key in TIME_MARKERS:
            assert isinstance(key, (int, float))

    def test_space_markers_are_numeric(self):
        for key in SPACE_MARKERS:
            assert isinstance(key, (int, float))

    def test_time_markers_span_expected_range(self):
        keys = sorted(TIME_MARKERS.keys())
        assert keys[0] < 1e-10  # sub-nanosecond
        assert keys[-1] > 1e15  # geologic


class TestVolumeConstantDerivations:
    """Verify volume constants match their astropy derivations (#222)."""

    def test_co2_volume_from_radius(self):
        """V = (4/3)πr³ for van der Waals radius."""
        expected = (4.0 / 3.0 * np.pi * CO2_VDW_RADIUS**3).to(u.m**3)
        assert abs(CO2_VOLUME.value - expected.value) / expected.value < 1e-10

    def test_co2_volume_order_of_magnitude(self):
        """CO₂ molecule ~5e-29 m³."""
        assert 1e-30 < CO2_VOLUME.to(u.m**3).value < 1e-28

    def test_ocean_surface_volume_derivation(self):
        """V = area × depth."""
        expected = (OCEAN_SURFACE_AREA.to(u.m**2) * OCEAN_MIXED_LAYER_DEPTH).to(u.m**3)
        assert abs(OCEAN_SURFACE_VOLUME.value - expected.value) / expected.value < 1e-10

    def test_ocean_surface_volume_order_of_magnitude(self):
        """Ocean mixed layer ~3.6e16 m³."""
        assert 1e15 < OCEAN_SURFACE_VOLUME.to(u.m**3).value < 1e18

    def test_everest_volume_from_cone(self):
        """V = (1/3)πr²h for cone approximation."""
        expected = (1.0 / 3.0 * np.pi * EVEREST_BASE_RADIUS**2 * EVEREST_HEIGHT).to(u.m**3)
        assert abs(ROUGH_ESTIMATE_EVEREST_VOLUME.value - expected.value) / expected.value < 1e-10

    def test_everest_volume_order_of_magnitude(self):
        """Everest cone ~3.7e11 m³."""
        assert 1e10 < ROUGH_ESTIMATE_EVEREST_VOLUME.to(u.m**3).value < 1e13
