import numpy as np
import pandas as pd
import pytest
from astropy import units

from timeSpace.calculations import calculate_log_center
from timeSpace.icons import (
    add_icons,
    crop_to_content,
    load_raster_icon,
    raster_display_size,
)
from timeSpace.plotting import create_space_time_figure


def process_row(name, icon, time_min, time_max, space_min, space_max):
    return {
        "Name": name,
        "icon": icon,
        "Time_min": time_min * units.s,
        "Time_max": time_max * units.s,
        "Space_min": space_min * units.m**3,
        "Space_max": space_max * units.m**3,
    }


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


def test_icon_size_is_independent_of_ellipse_size(png_icon_dir):
    """A process spanning 12 decades gets the same on-screen icon as one spanning 2."""
    df = pd.DataFrame(
        [
            process_row("small", "block", 1e2, 1e4, 1e-9, 1e-7),
            process_row("large", "block", 1e-2, 1e10, 1e-21, 1e15),
        ]
    )
    p = create_space_time_figure()
    add_icons(p, df, png_icon_dir, size_px=40)

    widths = [r.glyph.w for r in image_renderers(p)]
    assert len(widths) == 2
    assert widths[0] == pytest.approx(widths[1], rel=1e-9)


def test_rows_without_an_icon_are_skipped(png_icon_dir):
    df = pd.DataFrame(
        [
            process_row("a", "block", 1e2, 1e6, 1e-9, 1e-3),
            process_row("b", "", 1e2, 1e6, 1e-9, 1e-3),
            process_row("c", np.nan, 1e2, 1e6, 1e-9, 1e-3),
        ]
    )
    p = create_space_time_figure()
    add_icons(p, df, png_icon_dir, size_px=40)
    assert len(image_renderers(p)) == 1


def test_repeated_icon_is_loaded_once(png_icon_dir, monkeypatch):
    import timeSpace.icons as icons_module

    calls = []
    original = icons_module.load_raster_icon

    def counted(path, *args, **kwargs):
        calls.append(path)
        return original(path, *args, **kwargs)

    monkeypatch.setattr(icons_module, "load_raster_icon", counted)
    df = pd.DataFrame(
        [
            process_row("a", "block", 1e2, 1e6, 1e-9, 1e-3),
            process_row("b", "block", 1e3, 1e7, 1e-8, 1e-2),
        ]
    )
    add_icons(create_space_time_figure(), df, png_icon_dir, size_px=40)
    assert len(calls) == 1


def test_missing_png_raises(png_icon_dir):
    """Icons are PNG-only; a name with no {name}.png is a hard error, not a silent skip."""
    df = pd.DataFrame([process_row("a", "no_such_icon", 1e2, 1e6, 1e-9, 1e-3)])
    p = create_space_time_figure()
    with pytest.raises(FileNotFoundError):
        add_icons(p, df, png_icon_dir, size_px=40)


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
