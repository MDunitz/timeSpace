# Changelog

All notable changes to timeSpace are recorded here. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); the project aims for
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] — unreleased

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
