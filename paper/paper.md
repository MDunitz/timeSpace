---
title: 'timeSpace: interactive Stommel diagrams for biogeochemical and physical processes'
tags:
  - Python
  - oceanography
  - biogeochemistry
  - visualization
  - Stommel diagram
  - Bokeh
authors:
  - name: Madison Dunitz
    orcid: 0000-0001-7062-7528
    affiliation: 1
affiliations:
  - name: "California Institute of Technology, Pasadena, CA, USA"  # TODO: confirm exact affiliation / lab
    index: 1
date: 6 August 2026
bibliography: paper.bib
---

<!--
DRAFT — not submission-ready. Author-only decisions still open:
  * affiliation / lab name (line above)
  * Statement of need framing and the specific audience claim
  * the Boyd (2015) reference the bundled dataset is named for (see paper.bib TODO)
  * Acknowledgements / funding
  * whether to cite Haury et al. (1978) for the biological extension
JOSS length target is ~250-1000 words in Summary + Statement of need.
-->

# Summary

The *Stommel diagram* is a log--log plot of the characteristic spatial and
temporal scales of a set of processes, introduced to organize physical
oceanographic phenomena from surface waves to ice ages [@stommel1963] and later
adopted across biological oceanography and biogeochemistry to compare processes
that span many orders of magnitude. `timeSpace` is a Python package that builds
these diagrams programmatically. Each process is drawn as an ellipse spanning
its minimum and maximum time and space extents; reference objects, molecular
diffusion curves, and a speed-of-light causality boundary can be overlaid to
place a process in context. Diagrams are rendered with Bokeh [@bokeh], so the
output is interactive in a browser and can be exported as a self-contained HTML
file or embedded in another page. Physical quantities are carried as `astropy`
[@astropy2022] units so that scale calculations (for example the
three-dimensional root-mean-square diffusion length $\sqrt{6Dt}$) are unit-checked
rather than assumed. Process and reference data are read from CSV files or
directly from Google Sheets, which supports collaborative data entry.

# Statement of need

Stommel diagrams are widely used to reason about which processes dominate at
which scales, but they are almost always drawn by hand in illustration software.
That makes them slow to update, hard to reproduce, and impossible to interrogate:
a reader cannot toggle a process on or off, read off exact bounds, or regenerate
the figure when the underlying numbers change. `timeSpace` treats the diagram as
the deterministic output of a small, unit-checked pipeline instead of as a
drawing. Given a table of processes with time and space bounds, it produces a
consistent, log-correct figure with placed labels, and it re-derives every
geometric element (ellipse vertices, diffusion lines, the causality boundary)
from first principles rather than from pixel positions.

This is useful in two settings. First, for **teaching and synthesis**, where the
goal is to show a large, heterogeneous set of processes on one axis and let a
reader explore it interactively rather than squint at a static figure. Second,
for **collaborative scale elicitation**, where many researchers each contribute
the scales of their own work through a form; `timeSpace` ingests those responses
and renders them without manual redrawing.
<!-- TODO: sharpen the audience claim and, if appropriate, contrast with the
     hand-drawn status quo and any existing tooling. -->

# Functionality

`timeSpace` exposes a small public API from the top-level package. A base figure
is created with `create_space_time_figure`; processes are added from a prepared
DataFrame with `add_processes` (arbitrary user data) or `add_predefined_processes`
(a bundled dataset), and context layers are added with `add_magnitude_labels`,
`add_diffusion_lines`, `add_light_cone`, and `add_legend`. An extract--transform
layer (`extract_google_sheet`, `transform_process_response_sheet`,
`transform_predefined_processes`) cleans raw CSV or Google Sheets input into the
plotting schema. Geometry and scale helpers (`create_ellipse_data`,
`calculate_diffusion_length`, `calculate_sphere_volume`,
`classify_process_geometry`) return `astropy` quantities and handle degenerate
cases (a process with a single time or space value collapses to a line or point).
A command-line entry point, `timespace`, builds a diagram from a CSV or Google
Sheet in one call. Spatial extents are handled as volumes (m³) and temporal
extents as durations (s), both on base-10 log axes; the conventions are documented
in `CONVENTIONS.md`.

# Acknowledgements

<!-- TODO: funding sources, collaborators, workshop participants who contributed
     scale data. -->

# References
