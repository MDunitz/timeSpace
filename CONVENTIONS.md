# Conventions and assumptions

This document describes the physical and mathematical conventions used by
timeSpace so that anyone using the package for publication knows which
choices follow the literature and which are implementation decisions.

## Axis convention

The default figure layout (`create_space_time_figure`) places **Space (m³)
on the x-axis (top)** and **Time (s) on the y-axis (left, reversed)**.
Small times are at the top, large times at the bottom. This matches the
layout used in Boyd et al. (2015) Fig. 1.

Stommel diagrams appear in the literature with both orientations — the
original Stommel (1963) paper was a 3D spectral diagram of sea level
variability, and the biological adaptation by Haury et al. (1978) has
been drawn both ways by different authors. The `space_on_x` parameter on
`create_ellipse_data` controls this: `space_on_x=True` (default) puts
space on x and time on y; `space_on_x=False` swaps them.

## Spatial scale as volume (m³)

All spatial scales are expressed in **cubic metres** (m³). Boyd et al.
(2015) used characteristic length on the spatial axis; this package
converts lengths to volumes so that a single axis can represent spatial
extent consistently across scales. This is a deliberate simplification:
real processes may be better characterised by length, area, or
anisotropic dimensions.

The conversion from a characteristic length *L* to volume uses the sphere
approximation:

    V = (4/3) π L³

This assumes **isotropy**. Ocean processes are famously anisotropic —
horizontal length scales are often 10²–10⁴× larger than vertical scales.
A mesoscale eddy might be 100 km wide but only 1 km deep; the sphere
approximation collapses that into a single volume number.

For the purposes of a Stommel diagram (visualising order-of-magnitude
ranges on a log-log plot), this approximation is adequate — the
anisotropy introduces at most a few orders of magnitude of error, which
is within the visual resolution of a 30+-order axis. But users should be
aware that the spatial axis represents "characteristic spatial scale" as
a volume proxy, not a physical enclosure.

## Diffusion length equation

`calculate_diffusion_length` uses the **3D RMS displacement**:

    L = √(6 D t)

This is the characteristic radius of the sphere of space explored by a
molecule undergoing three-dimensional Brownian motion. Combined with
`calculate_sphere_volume` (V = 4/3·π·L³), it produces the diffusion
volume plotted on the Stommel diagram spatial axis.

Note: Boyd et al. (2015) used the 1D mean displacement √(4Dt/π), which
gives volumes ~11× smaller. We use the 3D formula because the spatial
axis represents volume — the 3D displacement is the physically correct
radius for "how much space has this molecule explored."

## Speed-of-light causality boundary

`add_light_cone` draws the speed-of-light line on the diagram:

    L = c · t
    V = (4/3) π (c · t)³

On the log-log plot this is a straight line with slope 3 (V ∝ t³),
steeper than diffusion lines (slope 3/2, since V ∝ t^{3/2}). Everything
physical must fall below this line. It is included by default when
`add_diffusion_lines` is called (set `include_light_cone=False` to
disable).

## Diffusion coefficients

All molecular diffusion coefficients in `constants.py` are for
**water at 25 °C** unless noted. Sources:

| Species   | Value (cm² s⁻¹) | Source                              |
|-----------|------------------|-------------------------------------|
| O₂        | 2.1 × 10⁻⁵      | Ferrell & Himmelblau (1967)         |
| CO₂       | 1.92 × 10⁻⁵     | Tamimi et al. (1994)                |
| Glucose   | 6.7 × 10⁻⁶      | Longsworth (1953)                   |
| H₂O self  | 2.3 × 10⁻⁵      | Holz et al. (2000)                  |

Temperature dependence is significant — O₂ diffusivity roughly doubles
between 5 °C and 35 °C. The package does not currently model temperature
dependence; all calculations assume 25 °C.

### Biological transport coefficients

E. coli's `motility_coefficient` (5 × 10⁻⁶ cm² s⁻¹) is the effective
diffusion coefficient arising from run-and-tumble motility (Berg &
Brown, 1972). This is **not** Brownian diffusion — the Stokes-Einstein
prediction for an E. coli-sized particle (~0.5 µm radius) gives
~4.9 × 10⁻⁹ cm² s⁻¹, three orders of magnitude smaller.

Both values are available in `constants.py`:
- `e_coli_motility_coefficient`: run-and-tumble effective diffusion
- `e_coli_diffusion_rate`: Stokes-Einstein Brownian diffusion

## Fill alpha (transparency) heuristic

Process ellipses use a transparency formula so that large processes
(spanning many orders of magnitude) are more transparent, keeping
overlaps between large and small processes readable:

    alpha = min(0.5 / ln(log_area + 2), 1)

where `log_area` is the product of the process's time and space extents
in orders of magnitude. The `+2` is a smoothing constant that prevents
a singularity at `ln(0)` for point processes (area = 0). This is a
purely aesthetic heuristic, not a physical quantity.

## Degenerate axis classification

`classify_process_geometry` uses a threshold of **1 × 10⁻¹⁰ orders of
magnitude** to distinguish points/lines from ellipses. This is
effectively testing floating-point identity — it classifies a process
as "degenerate" only when Time_min ≈ Time_max to within numerical
precision. This works well when the data comes from the ETL pipeline
(where degenerate values are intentionally equal), but would not catch
"nearly equal" values entered manually (e.g. 1.0 s and 1.001 s would
still render as an ellipse rather than a point).

## CSV Schema

All process CSV files under `data/datasets/` use a canonical set of
column names. The ETL functions accept legacy names with a deprecation
warning but new data files should use the canonical names below.

### Required columns

| Column       | Type   | Description                                      |
|--------------|--------|--------------------------------------------------|
| `Name`       | string | Full process name (display label on the diagram) |
| `Time_min`   | string or float | Minimum temporal scale in seconds       |
| `Time_max`   | string or float | Maximum temporal scale in seconds       |
| `Space_min`  | string or float | Minimum spatial scale in m³             |
| `Space_max`  | string or float | Maximum spatial scale in m³             |

Time and space values can be plain floats (`1e3`) or colon-separated
with a human-readable description (`1.00E+03: ~15 minutes`). The ETL
layer parses only the numeric portion before the colon.

### Optional columns

| Column       | Type   | Description                                       |
|--------------|--------|---------------------------------------------------|
| `Color`      | string | Hex color for the process glyph (e.g. `#7BA3B3`)  |
| `Category`   | string | Grouping label (e.g. "Physical processes")         |
| `Reference`  | string | Literature citation                                |
| `Notes`      | string | Free-text annotation                               |
| `ShortName`  | string | Abbreviated label (used by `create_name` if present) |
| `Prefix`     | string | Group prefix (used for legend grouping in `add_processes`) |
| `label_side` | string | `"left"` or `"right"` — per-row label anchor override |
| `Definition` | string | Extended description of the process                |

### Deprecated column names

The following names are accepted by `transform_predefined_processes`
but emit a `FutureWarning`. Update your CSVs to use `Name` instead:

- `Process` → `Name`
- `EcologicalUnit` → `Name`
- `Model` → `Name`
