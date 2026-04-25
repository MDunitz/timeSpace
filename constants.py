import numpy as np
from astropy import units

base_space = units.meter * units.meter * units.meter
base_time = units.second


colors = [
    "#33CCCC",
    "#009999",
    "#006666",
    "#669999",
    "#76DDDA",
    "#0F793D",
    "#064C26",
    "#013333",
    "#354C3E",
    "#0F2B1B",
    "#99CC33",
    "#669933",
    "#CDDE60",
    "#669966",
    "#6ABD45",
    "#FFCC33",
    "#FF9900",
    "#CC9933",
    "#996600",
    "#724419",
]

POSSIBLE_COL_LIST = ["Prefix", "ShortName", "Time_min", "Time_max", "Space_min", "Space_max", "Color", "Lab"]


PREDEFINED_PROCESSES_URI = "16ENjOsx4j2DD24mz0k-I08zF3R0CkfiujjqyYCGuAxg"
PROCESSES_URI = "14WirbmkElI-ALP9dBNciObL_nnpNwkGc2cfh_7Wm7YQ"
MEASUREMENTS_URI = "1oXf2-ikeeEB6QIhXBh-IjWGXkXkRI2jxu2HuaK8j9S4"

# PROJECT_ROOT=f"{os.getcwd()}/timeSpace"

diffusion_unit = units.cm * units.cm / units.second

# ── Volume constants — derived via astropy ─────────────────────────
# Each constant shows its derivation so the final value can be verified.

# CO₂ molecule: V = (4/3)πr³
# van der Waals radius r ≈ 2.3 Å (Bondi 1964, J Phys Chem 68(3):441)
# Note: CO₂ is linear so a sphere overestimates; this is a conventional
# "molecular volume" used in the Stommel diagram, not a precise measurement.
CO2_VDW_RADIUS = 2.3e-10 * units.m  # 2.3 Å
CO2_VOLUME = (4.0 / 3.0 * np.pi * CO2_VDW_RADIUS**3).to(units.m**3)

# Ocean volume: Eakins & Sharman (2010) NOAA Technical Memorandum
# https://rwu.pressbooks.pub/webboceanography/chapter/1-1-overview-of-the-oceans/
OCEAN_VOLUME = 1.37e9 * units.km**3
OCEAN_VOLUME_cubic_meters = OCEAN_VOLUME.to(units.m**3)

# Ocean surface layer: V = area × mixed layer depth
# Surface area: 3.61e8 km² (same source)
OCEAN_SURFACE_AREA = 3.61e8 * units.km**2
# Mixed layer depth: ~100 m annual mean (de Boyer Montégut et al. 2004)
OCEAN_MIXED_LAYER_DEPTH = 100 * units.meter
OCEAN_SURFACE_VOLUME = (OCEAN_SURFACE_AREA.to(units.m**2) * OCEAN_MIXED_LAYER_DEPTH).to(units.m**3)

# Mt Everest: V = (1/3)πr²h (cone approximation)
# Base radius ~10 km, height above base ~3.5 km
# This is a rough order-of-magnitude estimate for the Stommel diagram.
EVEREST_BASE_RADIUS = 10.0 * units.km
EVEREST_HEIGHT = 3.5 * units.km
ROUGH_ESTIMATE_EVEREST_VOLUME = (1.0 / 3.0 * np.pi * EVEREST_BASE_RADIUS**2 * EVEREST_HEIGHT).to(units.m**3)
# ≈ 3.7e11 m³ ≈ 367 km³


# ── Molecular diffusion coefficients in water at 25°C ──────────────
# All values in cm² s⁻¹. These are empirical measurements — astropy
# provides fundamental constants (k_B, etc.) but not molecular diffusivities.

O2_diffusion_rate = 2.1e-5 * diffusion_unit  # Ferrell & Himmelblau (1967) J Chem Eng Data 12(1):111
CO2_diffusion_rate = 1.92e-5 * diffusion_unit  # Tamimi et al. (1994) J Chem Eng Data 39(2):330
glucose_diffusion_rate = 6.7e-6 * diffusion_unit  # Longsworth (1953) J Am Chem Soc 75(22):5705
H2O_diffusion_rate = 2.3e-5 * diffusion_unit  # Holz et al. (2000) Phys Chem Chem Phys 2:4740 (self-diffusion)

# ── Biological motility / Stokes-Einstein diffusion ───────────────

# E. coli effective diffusion from run-and-tumble motility (NOT Brownian diffusion).
# 3 orders of magnitude above Stokes-Einstein prediction for a 1 µm particle.
e_coli_motility_coefficient = 5e-6 * diffusion_unit  # Berg & Brown (1972) Nature 239:500

# E. coli Brownian (Stokes-Einstein) diffusion: D = kT / (6πηr)
# k_B = 1.381e-23 J/K, T = 298.15 K, η = 8.9e-4 Pa·s, r ≈ 0.5 µm
e_coli_diffusion_rate = 4.9e-9 * diffusion_unit  # Stokes-Einstein, r ≈ 0.5 µm at 25°C

virus_diffusion_rate = 1.55e-7 * diffusion_unit  # ~100 nm particle; Stokes-Einstein approx.

DIFFUSION_COEFFICIENTS = {
    "CO2": CO2_diffusion_rate,
}

cubic_angstrom = 1e-30 * base_space
cubic_nm = 1e-27 * base_space
cubic_µm = 1e-18 * base_space
cubic_mm = 1e-9 * base_space
cubic_cm = 1e-6 * base_space
cubic_m = 1e0 * base_space
cubic_km = 1e9 * base_space
cubic_Mm = 1e18 * base_space

# Add time markers on x-axis
TIME_MARKERS = {
    1e-19: "Electron movement",
    1e-15: "Period of wave \nof visible light",  # https://en.wikipedia.org/wiki/Femtosecond
    1e-6: "Protein Folding",  # https://en.wikipedia.org/wiki/Microsecond
    1e-3: "Neuron Firing",  # https://en.wikipedia.org/wiki/Millisecond
    1e0: "Second",
    1e5: "Day",
    3.156e7: "Year",  # 365.25 days
    3.156e9: "Century",  # 100 years
    1e12: "Glacial-interglacial",
    1e15: "Geologic",
    1e18: "Deep Time",
}
# to do how can i access the relevant prefix from the astropy type?
SPACE_MARKERS = {
    cubic_nm.value: "nm³",
    cubic_µm.value: "µm³",
    cubic_mm.value: "mm³",
    cubic_cm.value: "cm³",
    cubic_m.value: "m³",
    cubic_km.value: "km³",
    cubic_Mm.value: "Mm³",
}

SPACE_EXAMPLES = {
    CO2_VOLUME.value: r"\(CO_{2}\)",
    OCEAN_VOLUME_cubic_meters.value: "Ocean",
    OCEAN_SURFACE_VOLUME.value: "Surface Ocean",
    ROUGH_ESTIMATE_EVEREST_VOLUME.value: "Everest",
}

OFFSETS = {"6": [-10, 35], "4": [0, 20], "1": [10, 5], "5": [15, -10], "2": [10, -25], "3": [-10, -40]}
