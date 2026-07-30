"""Visual and characterization tests for timeSpace.add_icons.

The tests in test_icons.py assert on data-coordinate geometry (equal ink area,
concentricity, caching). None of them render, so they cannot see the render-time
behaviours PR #35 flagged as limitations. This module pins those behaviours so a
future change that silently alters them is caught, and provides a runnable
harness (``python -m tests.test_icons_visual``) that dumps an HTML page for
manual eyeballing.

Findings that motivated the corrective test below:
- A gradient fill collapses to a single flat colour, currently ``#000000``
  (svgelements returns black for an unresolved gradient paint). See
  test_gradient_flattens_to_single_flat_fill.
- An even-odd hole fills instead of cutting out. See
  test_evenodd_hole_fills_instead_of_cutting_out.
- A *closed* stroked outline is NOT dramatically over-scaled, contrary to the
  PR's limitation #1 wording: with no filled subpath, measure_ink_area rasterizes
  the stroke path as a filled polygon, so a ring is treated as its enclosed disc.
  See test_closed_outline_is_not_dramatically_overscaled.
"""

import numpy as np
import pandas as pd
import pytest
from astropy import units

from timeSpace import PROJECT_ROOT
from timeSpace.etl import transform_predefined_processes
from timeSpace.icons import add_icons, load_icon, measure_ink_area, normalize_icon
from timeSpace.plotting import create_space_time_figure

SOLID = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
    '<rect x="10" y="10" width="80" height="80" fill="#333333"/></svg>'
)

# fill="none" stroke -> no filled subpath; exercises the stroke-as-fill fallback.
OUTLINE = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
    '<circle cx="50" cy="50" r="40" fill="none" stroke="#cc0000" stroke-width="3"/></svg>'
)

# Even-odd path: outer square with an inner square meant as a hole.
HOLE = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
    '<path fill-rule="evenodd" fill="#0066cc" d="M10 10 H90 V90 H10 Z M35 35 H65 V65 H35 Z"/></svg>'
)

# Gradient fill: cannot resolve to a single stop colour.
GRADIENT = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
    '<defs><linearGradient id="g"><stop offset="0" stop-color="#00aa00"/>'
    '<stop offset="1" stop-color="#0000aa"/></linearGradient></defs>'
    '<rect x="10" y="10" width="80" height="80" fill="url(#g)"/></svg>'
)

# Two flat subpaths in different colours: the control that should render correctly.
TWO_TONE = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
    '<rect x="0" y="0" width="100" height="50" fill="#e6663a"/>'
    '<rect x="0" y="50" width="100" height="50" fill="#3a99cc"/></svg>'
)

ADVERSARIAL = {
    "solid": SOLID,
    "outline": OUTLINE,
    "hole": HOLE,
    "gradient": GRADIENT,
    "two_tone": TWO_TONE,
}


@pytest.fixture
def icon_dir(tmp_path):
    for name, svg in ADVERSARIAL.items():
        (tmp_path / f"{name}.svg").write_text(svg)
    return tmp_path


def patch_renderers(p):
    """Renderer layers that carry icon polygons (a patches layer has an 'xs' column)."""
    return [r for r in p.renderers if "xs" in r.data_source.data]


def process_row(name, icon, time_min=1e2, time_max=1e6, space_min=1e-9, space_max=1e-3):
    return {
        "Name": name,
        "icon": icon,
        "Time_min": time_min * units.s,
        "Time_max": time_max * units.s,
        "Space_min": space_min * units.m**3,
        "Space_max": space_max * units.m**3,
    }


def _icon_bbox(shapes):
    xs = np.concatenate([s[0] for s in shapes])
    ys = np.concatenate([s[1] for s in shapes])
    return xs.max() - xs.min(), ys.max() - ys.min()


def test_gradient_flattens_to_single_flat_fill(icon_dir):
    """A gradient paint collapses to one flat colour (currently #000000).

    Bokeh patches take a flat fill, so smooth shadings cannot survive. This pins
    the collapse; the specific black value is a known wart tracked separately.
    """
    shapes = load_icon(icon_dir / "gradient.svg")
    fills = [s[2] for s in shapes if s[2] is not None]
    assert len(fills) == 1
    assert fills[0].startswith("#") and len(fills[0]) == 7


def test_evenodd_hole_fills_instead_of_cutting_out(icon_dir):
    """An even-odd hole renders as two same-colour fills, not a cutout.

    Subpaths render in document order with no winding analysis, so the inner
    square fills over the outer one instead of punching through.
    """
    shapes = load_icon(icon_dir / "hole.svg")
    fills = [s[2] for s in shapes if s[2] is not None]
    assert len(fills) == 2
    assert fills[0] == fills[1] == "#0066cc"


def test_closed_outline_is_not_dramatically_overscaled(icon_dir):
    """A closed stroked outline is treated as its enclosed area, not thin ink.

    Corrects PR #35 limitation #1 for closed shapes: with no filled subpath,
    measure_ink_area falls back to rasterizing the stroke path as a filled
    polygon, so a ring ~= its enclosed disc. It normalizes to within a small
    factor of a solid of the same target area, not a runaway bloom. Genuinely
    open line art (little enclosed area) is the real over-scale risk.
    """
    target = 28.0**2
    outline_w, _ = _icon_bbox(normalize_icon(load_icon(icon_dir / "outline.svg"), target))
    solid_w, _ = _icon_bbox(normalize_icon(load_icon(icon_dir / "solid.svg"), target))
    assert outline_w / solid_w < 1.5

    outline_area = measure_ink_area(load_icon(icon_dir / "outline.svg"))
    solid_area = measure_ink_area(load_icon(icon_dir / "solid.svg"))
    assert 0.5 < outline_area / solid_area < 1.0


def test_two_tone_control_keeps_both_colours(icon_dir):
    """The control icon: two flat subpaths keep their distinct colours."""
    df = pd.DataFrame([process_row("a", "two_tone")])
    p = create_space_time_figure()
    add_icons(p, df, icon_dir, size_px=40)
    colors = sorted(patch_renderers(p)[0].data_source.data["fill_color"])
    assert colors == ["#3a99cc", "#e6663a"]


def build_visual_smoke(icon_dir, frame_px=(1400, 760), size_px=28):
    """Build the Boyd (2015) Stommel diagram with every adversarial icon placed.

    Cycles the five test icons across the 14 shipped processes and returns the
    assembled figure. frame_px is pinned so size_px is exact: the add_icons
    default plot_size_px=(p.width, p.height) uses the OUTER figure size, which
    includes axis furniture and renders icons a few percent small.
    """
    import timeSpace as ts

    data = pd.read_csv(PROJECT_ROOT / "data" / "datasets" / "stommel_boyd2015_volumes.csv")
    df = transform_predefined_processes(data).reset_index(drop=True)
    names = list(ADVERSARIAL)
    df["icon"] = [names[i % len(names)] for i in range(len(df))]

    frame_w, frame_h = frame_px
    p = ts.create_space_time_figure()
    p.frame_width, p.frame_height = frame_w, frame_h
    ts.add_magnitude_labels(p)
    ts.add_diffusion_lines(p)
    ts.add_light_cone(p)
    ts.add_predefined_processes(p, df)
    ts.add_legend(p)
    ts.add_icons(p, df, icon_dir, size_px=size_px, plot_size_px=(frame_w, frame_h))  # LAST
    return p, df


def test_visual_smoke_builds_all_modes(icon_dir):
    """End-to-end: every adversarial icon places on the real dataset without error.

    This is the CI-runnable half of the harness. It exercises the full add_icons
    path (load -> normalize -> place -> patches/multi_line) on 14 real processes
    and asserts a patch layer was emitted for each icon-bearing row.
    """
    p, df = build_visual_smoke(icon_dir)
    assert len(patch_renderers(p)) == len(df)


def render_visual_smoke(icon_dir, out_html="icons_smoke.html"):
    """Write the smoke figure to HTML for manual visual inspection.

    Not a pytest test: correctness here is 'looks right in a browser', which no
    assertion covers. Run: python -m tests.test_icons_visual
    """
    from bokeh.io import output_file, save

    p, _ = build_visual_smoke(icon_dir)
    output_file(out_html)
    save(p)
    return out_html


if __name__ == "__main__":
    import tempfile
    from pathlib import Path

    tmp = Path(tempfile.mkdtemp())
    for _name, _svg in ADVERSARIAL.items():
        (tmp / f"{_name}.svg").write_text(_svg)
    path = render_visual_smoke(tmp, out_html="icons_smoke.html")
    print(f"wrote {path} — open it and check: gradient renders black, hole has no cutout")
