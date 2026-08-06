import numpy as np
import pandas as pd
import pytest
from astropy import units

from timeSpace.calculations import calculate_log_center
from timeSpace.icons import (
    add_icons,
    load_icon,
    crop_to_content,
    load_raster_icon,
    log_span,
    measure_ink_area,
    normalize_icon,
    raster_display_size,
)
from timeSpace.plotting import create_space_time_figure

SQUARE = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
    '<rect x="10" y="10" width="80" height="80" fill="#336699"/></svg>'
)

# Same bounding box as SQUARE but a fraction of the ink, and a 4:1 aspect ratio.
BAR = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
    '<rect x="10" y="40" width="80" height="20" fill="#993366"/></svg>'
)

TWO_TONE = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
    '<rect x="0" y="0" width="100" height="50" fill="#111111"/>'
    '<rect x="0" y="50" width="100" height="50" fill="#eeeeee"/></svg>'
)


@pytest.fixture
def icon_dir(tmp_path):
    (tmp_path / "square.svg").write_text(SQUARE)
    (tmp_path / "bar.svg").write_text(BAR)
    (tmp_path / "two_tone.svg").write_text(TWO_TONE)
    return tmp_path


def process_row(name, icon, time_min, time_max, space_min, space_max):
    return {
        "Name": name,
        "icon": icon,
        "Time_min": time_min * units.s,
        "Time_max": time_max * units.s,
        "Space_min": space_min * units.m**3,
        "Space_max": space_max * units.m**3,
    }


def patch_renderers(p):
    return [r for r in p.renderers if "xs" in r.data_source.data]


def test_measure_ink_area_ignores_empty_bbox_space(icon_dir):
    """The bar covers a quarter of the square's ink despite an equal bounding box."""
    square = measure_ink_area(load_icon(icon_dir / "square.svg"))
    bar = measure_ink_area(load_icon(icon_dir / "bar.svg"))
    assert square == pytest.approx(80 * 80, rel=0.02)
    assert bar == pytest.approx(80 * 20, rel=0.02)


def test_normalize_gives_equal_ink_area(icon_dir):
    """Two icons of different shape and density normalize to the same ink area."""
    target = 28.0**2
    square = normalize_icon(load_icon(icon_dir / "square.svg"), target)
    bar = normalize_icon(load_icon(icon_dir / "bar.svg"), target)
    assert measure_ink_area(square) == pytest.approx(target, rel=0.02)
    assert measure_ink_area(bar) == pytest.approx(target, rel=0.02)


def test_normalize_preserves_aspect_ratio(icon_dir):
    """Equal-area scaling is uniform, so the 4:1 bar stays 4:1."""
    shapes = normalize_icon(load_icon(icon_dir / "bar.svg"), 28.0**2)
    xs = np.concatenate([s[0] for s in shapes])
    ys = np.concatenate([s[1] for s in shapes])
    assert (xs.max() - xs.min()) / (ys.max() - ys.min()) == pytest.approx(4.0, rel=0.01)


def test_normalize_centres_on_origin(icon_dir):
    shapes = normalize_icon(load_icon(icon_dir / "bar.svg"), 28.0**2)
    xs = np.concatenate([s[0] for s in shapes])
    ys = np.concatenate([s[1] for s in shapes])
    assert (xs.min() + xs.max()) / 2 == pytest.approx(0.0, abs=1e-9)
    assert (ys.min() + ys.max()) / 2 == pytest.approx(0.0, abs=1e-9)


def test_log_span_is_negative_for_reversed_axis():
    """The default space_on_x figure has a reversed time axis."""
    p = create_space_time_figure()
    assert log_span(p.x_range) > 0
    assert log_span(p.y_range) < 0


def test_icon_is_concentric_with_its_ellipse(icon_dir):
    """Icon centre lands on the same log-space point the ellipse is drawn around."""
    df = pd.DataFrame([process_row("a", "square", 1e2, 1e6, 1e-9, 1e-3)])
    p = create_space_time_figure()
    add_icons(p, df, icon_dir, size_px=40)

    renderer = patch_renderers(p)[0]
    xs = np.concatenate(renderer.data_source.data["xs"])
    ys = np.concatenate(renderer.data_source.data["ys"])
    x_mid = (np.log10(xs.min()) + np.log10(xs.max())) / 2
    y_mid = (np.log10(ys.min()) + np.log10(ys.max())) / 2

    assert x_mid == pytest.approx(calculate_log_center(1e-9, 1e-3), abs=1e-9)
    assert y_mid == pytest.approx(calculate_log_center(1e2, 1e6), abs=1e-9)


def test_icon_size_is_independent_of_ellipse_size(icon_dir):
    """A process spanning 12 decades gets the same icon as one spanning 2."""
    df = pd.DataFrame(
        [
            process_row("small", "square", 1e2, 1e4, 1e-9, 1e-7),
            process_row("large", "square", 1e-2, 1e10, 1e-21, 1e15),
        ]
    )
    p = create_space_time_figure()
    add_icons(p, df, icon_dir, size_px=40)

    spans = []
    for renderer in patch_renderers(p):
        xs = np.concatenate(renderer.data_source.data["xs"])
        spans.append(np.log10(xs.max()) - np.log10(xs.min()))
    assert len(spans) == 2
    assert spans[0] == pytest.approx(spans[1], rel=1e-9)


def test_on_screen_aspect_ratio_survives_unequal_decade_counts(icon_dir):
    """x and y scale independently, so a square icon is square in pixels."""
    df = pd.DataFrame([process_row("a", "square", 1e2, 1e6, 1e-9, 1e-3)])
    p = create_space_time_figure(width=1600, height=900)
    add_icons(p, df, icon_dir, size_px=40)

    renderer = patch_renderers(p)[0]
    xs = np.concatenate(renderer.data_source.data["xs"])
    ys = np.concatenate(renderer.data_source.data["ys"])
    width_px = (np.log10(xs.max()) - np.log10(xs.min())) / log_span(p.x_range) * 1600
    height_px = (np.log10(ys.max()) - np.log10(ys.min())) / log_span(p.y_range) * 900
    assert abs(width_px) == pytest.approx(abs(height_px), rel=0.01)


def test_subpath_fills_are_preserved(icon_dir):
    """Each subpath keeps its own colour, so multi-colour icons survive."""
    df = pd.DataFrame([process_row("a", "two_tone", 1e2, 1e6, 1e-9, 1e-3)])
    p = create_space_time_figure()
    add_icons(p, df, icon_dir, size_px=40)

    colors = patch_renderers(p)[0].data_source.data["fill_color"]
    assert sorted(colors) == ["#111111", "#eeeeee"]


def test_rows_without_an_icon_are_skipped(icon_dir):
    df = pd.DataFrame(
        [
            process_row("a", "square", 1e2, 1e6, 1e-9, 1e-3),
            process_row("b", "", 1e2, 1e6, 1e-9, 1e-3),
            process_row("c", np.nan, 1e2, 1e6, 1e-9, 1e-3),
        ]
    )
    p = create_space_time_figure()
    add_icons(p, df, icon_dir, size_px=40)
    assert len(patch_renderers(p)) == 1


def test_repeated_icon_is_loaded_once(icon_dir, monkeypatch):
    import timeSpace.icons as icons_module

    calls = []
    original = icons_module.load_icon

    def counted(path, *args, **kwargs):
        calls.append(path)
        return original(path, *args, **kwargs)

    monkeypatch.setattr(icons_module, "load_icon", counted)
    df = pd.DataFrame(
        [
            process_row("a", "square", 1e2, 1e6, 1e-9, 1e-3),
            process_row("b", "square", 1e3, 1e7, 1e-8, 1e-2),
        ]
    )
    add_icons(create_space_time_figure(), df, icon_dir, size_px=40)
    assert len(calls) == 1


def write_png(path, width, height, opaque_box, alpha=255):
    """Write an RGBA PNG: transparent canvas with one opaque (or semi-opaque) box."""
    from PIL import Image, ImageDraw

    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    x0, y0, x1, y1 = opaque_box
    ImageDraw.Draw(image).rectangle([x0, y0, x1 - 1, y1 - 1], fill=(51, 102, 153, alpha))
    image.save(path)


@pytest.fixture
def png_icon_dir(tmp_path):
    write_png(tmp_path / "block.png", 100, 100, (10, 10, 90, 90))  # 80x80 content, 20px margin
    write_png(tmp_path / "wide.png", 100, 100, (10, 40, 90, 60))  # 80x20 content, 4:1
    write_png(tmp_path / "faint.png", 100, 100, (10, 10, 90, 90), alpha=128)  # same box, half alpha
    write_png(tmp_path / "big.png", 1000, 1000, (0, 0, 1000, 1000))  # 1000px content, no margin
    return tmp_path


def image_renderers(p):
    return [r for r in p.renderers if type(r.glyph).__name__ == "ImageURL"]


def test_crop_to_content_returns_opaque_bbox(png_icon_dir):
    """crop_to_content tightens a padded canvas to just its opaque pixels."""
    from PIL import Image

    cropped = crop_to_content(Image.open(png_icon_dir / "block.png").convert("RGBA"))
    assert cropped.size == (80, 80)


def test_crop_to_content_removes_transparent_margin(png_icon_dir):
    """The 20px transparent border is dropped; loader reports content dimensions."""
    _uri, w, h = load_raster_icon(png_icon_dir / "block.png")
    assert (w, h) == (80, 80)


def test_raster_display_size_fits_longest_side(png_icon_dir):
    """The content's longest side becomes size_px, giving a consistent footprint."""
    size_px = 28.0
    _uri, w, h = load_raster_icon(png_icon_dir / "wide.png")  # 80x20 content
    dw, dh = raster_display_size(w, h, size_px)
    assert max(dw, dh) == pytest.approx(size_px, rel=1e-9)
    assert dw / dh == pytest.approx(w / h, rel=1e-9)  # aspect preserved


def test_raster_size_is_independent_of_alpha_level(png_icon_dir):
    """A half-alpha icon and an opaque one with the same box size identically."""
    solid = load_raster_icon(png_icon_dir / "block.png")[1:]
    faint = load_raster_icon(png_icon_dir / "faint.png")[1:]
    assert solid == faint


def test_downscale_cap_limits_longest_side(png_icon_dir):
    """A 1000px content icon is capped to max_source_px on load."""
    _uri, w, h = load_raster_icon(png_icon_dir / "big.png", max_source_px=128)
    assert max(w, h) == pytest.approx(128, abs=1)


def test_load_raster_icon_is_self_contained(png_icon_dir):
    """URI is an embedded base64 PNG so standalone HTML has no external deps."""
    uri, _w, _h = load_raster_icon(png_icon_dir / "block.png")
    assert uri.startswith("data:image/png;base64,")


def test_raster_icon_is_centred_on_its_ellipse(png_icon_dir):
    """The image glyph anchors on the same log-space centre as the ellipse."""
    df = pd.DataFrame([process_row("a", "block", 1e2, 1e6, 1e-9, 1e-3)])
    p = create_space_time_figure()
    add_icons(p, df, png_icon_dir, size_px=40)

    renderer = image_renderers(p)[0]
    assert renderer.glyph.anchor == "center"
    assert renderer.glyph.w_units == "screen" and renderer.glyph.h_units == "screen"
    x = renderer.data_source.data["x"][0]
    y = renderer.data_source.data["y"][0]
    assert np.log10(x) == pytest.approx(calculate_log_center(1e-9, 1e-3), abs=1e-9)
    assert np.log10(y) == pytest.approx(calculate_log_center(1e2, 1e6), abs=1e-9)


def test_png_is_preferred_over_svg(png_icon_dir):
    """When both {name}.png and {name}.svg exist, the raster path wins."""
    (png_icon_dir / "block.svg").write_text(SQUARE)
    df = pd.DataFrame([process_row("a", "block", 1e2, 1e6, 1e-9, 1e-3)])
    p = create_space_time_figure()
    add_icons(p, df, png_icon_dir, size_px=40)
    assert len(image_renderers(p)) == 1
    assert len(patch_renderers(p)) == 0


def test_raster_and_vector_icons_coexist(png_icon_dir):
    """A PNG row and an SVG row in the same call each get their own glyph type."""
    (png_icon_dir / "sq.svg").write_text(SQUARE)
    df = pd.DataFrame(
        [
            process_row("a", "block", 1e2, 1e6, 1e-9, 1e-3),
            process_row("b", "sq", 1e3, 1e7, 1e-8, 1e-2),
        ]
    )
    p = create_space_time_figure()
    add_icons(p, df, png_icon_dir, size_px=40)
    assert len(image_renderers(p)) == 1
    assert len(patch_renderers(p)) == 1


def test_icon_scale_column_enlarges_named_icon(png_icon_dir):
    """A row's icon_scale multiplies its display size vs an unscaled row."""
    df = pd.DataFrame(
        [
            process_row("a", "block", 1e2, 1e6, 1e-9, 1e-3),
            process_row("b", "block", 1e3, 1e7, 1e-8, 1e-2),
        ]
    )
    df["icon_scale"] = [1.0, 2.0]
    p = create_space_time_figure()
    add_icons(p, df, png_icon_dir, size_px=40)
    imgs = image_renderers(p)
    w1 = imgs[0].glyph.w
    w2 = imgs[1].glyph.w
    assert w2 == pytest.approx(2 * w1, rel=1e-6)
