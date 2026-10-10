# Changelog

All notable changes to timeSpace are recorded here. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); the project aims for
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- Explorer: pins accumulate. Clicking shapes or picking from the pin control
  adds objects, and they stay until their chip is removed or "Clear all" is
  pressed. The panel shows full details for the latest pin and one line for
  each of the others. Replaces the single-object dropdown.
- Explorer: a pinned object's name sits just above its shape instead of on
  top of it, so small shapes are no longer hidden by their own label.

- Explorer: the time and volume marker names (Second, Day, km3 and so on)
  moved from inside the plot to a top and a right axis. They follow pan and
  zoom and show only while their magnitude is in view.
- `add_magnitude_labels` does the same for every figure: marker names are tick
  labels on two extra axes placed opposite the figure's own axes, in either
  orientation (new `marker_axes` module, shared with the explorer). The
  in-plot `Label` annotations and their pan/zoom callbacks are gone; the
  function's signature is unchanged.

### Fixed
- Domestic cat lifespan lower bound 12 yr -> 13 yr to match its cited source.

## [0.3.1] — 2026-10-08

Source links in the explorer, label modes, and a second round of
reference-object corrections.

### Added
- Explorer: clicking a shape pins that object, and the info panel shows its
  source with BioNumbers, DOI, arXiv and PubMed Central identifiers as links
  (`explorer/links.py`). Hover tooltips follow the cursor and cannot be
  clicked, so the links live in the panel. Citations with no such identifier
  stay plain text; the CSV holds no URLs.
- Explorer: "Labels" control with Names, Numbers and None. Numbers mode
  marks each object with a number and shows a key beside the plot grouped
  by category (`explorer/key.py`). Both pages start on Names. Name labels
  sit on a translucent white plate. Replaces the "Show labels" checkbox.
- Explorer plot is 765 px tall (was 720).
- Reference objects: `Reference_URL` column with 112 checked source pages
  across 73 rows; the explorer lists them under the pinned object's
  citation. With the identifier links, 89 of the 93 cited rows now link out.

### Fixed
- Seasonal algal bloom duration extended to 58 days (Silva et al. 2021).
- Pando aspen clone age set to 12,000-37,000 yr (revised Pineau et al.
  preprint; was 16,000-80,000 yr from its first version).
- Giant sequoia: ages 1,650 to 3,266 yr and bole volumes 790-1,487 m3 from
  Stephenson (2000), now cited to Madrono 47:61-67 instead of "USGS".
- Butterfly wing beat citation gains its year and sample sizes; values
  unchanged.
- Ice age cycle: ocean volume set to the cited paper's 1.332e18 m3 (was
  1.335e18 m3, a different estimate, credited to the same paper).
- Earth's orbit uses the volume the Earth sweeps in one year, 1.20e26 m3
  (cross-section x orbit circumference), instead of the 1 au sphere
  (1.4e34 m3). The volume axis now tops out at 1e29 m3 instead of 1e36.

## [0.3.0] — 2026-10-06

Reference objects sourced and corrected, and the explorer reworked around
them. 0.2.0 was tagged and archived on Zenodo but never uploaded to PyPI, so
this is the first PyPI release since 0.1.0.

### Fixed
- Seven reference-object rows corrected against primary sources and given a
  `Reference`: Grand Canyon, Great Wall of China and Hoover Dam volumes (each
  off by one to two decades), enzyme catalytic cycle time range, yeast and
  liver-cell volumes. "International Space Station orbit" renamed to
  "International Space Station (service life)" to match its time range.
- Further reference-object corrections: two citations that did not resolve
  (giant tortoise, blue whale), ranges for E. coli, giant sequoia, Pando,
  Moon formation, protein folding, DNA replication, red blood cell, ribosome
  and Greenland shark, and BioNumbers sources for molecular and cellular rows.
- Explorer point markers no longer show before an object is selected.
- Explorer no longer shows tooltips for hidden objects on an empty plot.
- Explorer no longer blanks when an object is picked after a category.
- Explorer axes now cover every reference object; 29 objects (including
  Earth's orbit and rotation) were partly or wholly outside the old view.
- Reference objects: 93 of 102 rows now cite a source. Ranges moved where the
  source disagreed (for example mycelial network age, mountain building,
  Pacific Ocean age, Amazon and France volumes, mouse and housefly
  lifespans, soil formation), and each Reference names any bound that is
  still unsourced.

### Changed
- Explorer categories are now checkboxes that layer; picking an object pins
  it on top of whatever categories are showing.
- Explorer category checkboxes carry each category's plot colour (the colour
  key), and a "Show labels" checkbox turns object labels on or off.
- Earth's orbit now uses the volume of the sphere enclosed by a 1 au orbit
  (1.41e34 m³) instead of the Earth's own volume.

### Added
- Explorer tooltips and the picked-object panel show time and volume in
  readable units (for example "273 – 507 yr", "90 – 100 fL") instead of raw
  seconds and m³; line and point objects now have tooltips too.
- Explorer header links to the Colab notebook for plotting your own objects.
- The explorer shows each reference object's source on hover and when an
  object is picked; rows without one read "not yet sourced".
- CONVENTIONS.md states how reference-object volumes are defined.

## [0.2.0] — 2026-08-10

First release cut from a tagged commit with a Zenodo DOI. Highlights since 0.1.0:

### Added
- Process icons: `add_icons` renders equal-area SVG glyphs on process
  ellipses, plus a raster PNG path that preserves gradients and alpha with
  crop-to-content sizing and a downscale cap.
- Energy taxonomy promoted into the package (partial; see the energy-axis work).
- `timespace` CLI to build Stommel diagrams from a CSV or Google Sheet.
- `x_axis_location` on `create_space_time_figure` (time-on-bottom layouts).
- Toggle mode for the reference-object explorer.
- Dataset validation module.

### Fixed
- Numerous dataset corrections: reference-object volumes, virus anchors and
  diffusion rate, off-by-a-decade time markers, CO₂ fixation bounds, sphere
  length-to-volume convention, unit labels.
- Axis orientation and label-placement fixes across the desert-farm and
  explorer builds.

### Changed
- README no longer advertises an energy axis that is not yet in the public API.

## [0.1.0] — 2026-04-18 (PyPI only, no matching public tag)

Initial public release, published to PyPI on 2026-04-18. **No git tag exists
for this version, and no commit in the public repository is content-identical
to the PyPI 0.1.0 artifact** — the repository was squash-republished after the
upload, so the exact source lives in the pre-squash private history. The commit
labelled "Initial release: timeSpace 0.1.0" (`8d743c44`, 2026-04-25) is the
closest public snapshot but differs from the PyPI sdist in four files. Treat
0.1.0 as an untagged prerelease; 0.2.0 is the first properly tagged release.

[0.2.0]: https://github.com/MDunitz/timeSpace/releases/tag/v0.2.0
