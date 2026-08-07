"""Icon glyphs for Stommel diagrams.

Icons are drawn at the log-space centre of each process ellipse. Each icon is a
transparent PNG drawn as a raster image glyph, which preserves gradients and
soft alpha edges. Every icon is fitted so its content bounding box's longest
side is the same on-screen size, giving a consistent footprint regardless of
how sparse or dense the artwork is.
"""

import base64
import io
from pathlib import Path as FilePath

from PIL import Image

from timeSpace.calculations import calculate_log_center


def crop_to_content(image):
    """Crop an RGBA image to the bounding box of its opaque pixels.

    Removes the transparent margin so anchor="center" lands on the artwork's
    own centre rather than the canvas centre, and so bounding-box sizing
    measures the content rather than the exported canvas. A fully transparent
    image is returned unchanged.
    """
    bbox = image.getchannel("A").getbbox()
    return image.crop(bbox) if bbox else image


def load_raster_icon(png_path, max_source_px=256):
    """Load a transparent PNG as a self-contained data URI plus its geometry.

    The image is cropped to its opaque content and downscaled so its longest
    side is at most `max_source_px`, since the icon is displayed at a fixed
    pixel size far below a typical export resolution; capping the source keeps
    the base64 payload small without affecting appearance.

    Returns
    -------
    (uri, width_px, height_px)
        `uri` is a base64 ``data:image/png`` string so the icon embeds in a
        standalone HTML document with no external file dependency; width and
        height are the cropped (and possibly downscaled) content dimensions.
    """
    image = crop_to_content(Image.open(png_path).convert("RGBA"))
    longest = max(image.size)
    if longest > max_source_px:
        scale = max_source_px / longest
        image = image.resize((max(1, round(image.width * scale)), max(1, round(image.height * scale))), Image.LANCZOS)
    width_px, height_px = image.size
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    uri = "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")
    return uri, float(width_px), float(height_px)


def raster_display_size(width_px, height_px, size_px):
    """Screen size that fits a raster's content bounding box to size_px.

    Bounding-box normalization (uniform scale, aspect preserved):
        scale = size_px / max(width_px, height_px)

    The longest side of the content becomes size_px, so every icon occupies a
    consistent footprint regardless of how sparse or dense its artwork is.

    Returns
    -------
    (display_w_px, display_h_px)
        Screen-unit width and height for the image glyph.
    """
    scale = size_px / max(width_px, height_px)
    return width_px * scale, height_px * scale


def place_raster_icon(p, uri, x_center_log, y_center_log, display_w_px, display_h_px, alpha=1.0):
    """Draw a raster icon centred on a log-space point at a fixed screen size.

    Screen-unit sizing keeps the icon a constant pixel size independent of the
    axis ranges; anchor="center" puts the raster's own centre on the process
    ellipse centre. Transparent regions of the PNG let the grid and ellipse
    behind it show through.
    """
    p.image_url(
        url=[uri],
        x=[10**x_center_log],
        y=[10**y_center_log],
        w=display_w_px,
        h=display_h_px,
        w_units="screen",
        h_units="screen",
        anchor="center",
        global_alpha=alpha,
    )
    return p


def add_icons(
    p,
    process_df,
    icon_dir,
    size_px=28,
    space_on_x=True,
    alpha=1.0,
    max_source_px=256,
    scale_col="icon_scale",
):
    """Draw a PNG icon at the log-space centre of each process ellipse.

    Icon size is fixed in screen pixels, so the icon is a constant footprint
    independent of the axis ranges and of the ellipse it sits on. Call this
    last, after the axis ranges and figure dimensions are final.

    Parameters
    ----------
    p : bokeh.plotting.figure
        Figure with log axes, ranges already set.
    process_df : pandas.DataFrame
        Rows with Time_min, Time_max, Space_min, Space_max as astropy
        Quantities, plus an `icon` column naming a ``{name}.png`` file in
        `icon_dir` without its extension. Rows with a blank icon are skipped.
    icon_dir : path-like
        Folder of ``.png`` icons (transparent background; gradients preserved).
    size_px : float
        Nominal icon size in pixels: the content bounding box is fitted so its
        longest side is size_px, independent of the process ellipse.
    space_on_x : bool
        Must match the value passed to create_space_time_figure.
    alpha : float
        Opacity applied to every icon.
    max_source_px : int
        PNG icons are downscaled so their longest side is at most this before
        being embedded, capping the base64 payload.
    scale_col : str
        Optional per-row column of size multipliers on size_px (default 1.0),
        so individual icons can be enlarged or shrunk. Missing/blank -> 1.0.
    """
    icon_dir = FilePath(icon_dir)
    cache = {}

    for row in process_df.itertuples():
        name = str(getattr(row, "icon", "") or "").strip()
        if not name or name == "nan":
            continue
        if name not in cache:
            cache[name] = _load_icon(icon_dir, name, max_source_px)
        row_size = size_px * _row_scale(row, scale_col)
        time_center = calculate_log_center(row.Time_min.value, row.Time_max.value)
        space_center = calculate_log_center(row.Space_min.value, row.Space_max.value)
        if space_on_x:
            x_center_log, y_center_log = space_center, time_center
        else:
            x_center_log, y_center_log = time_center, space_center
        uri, width_px_src, height_px_src = cache[name]
        display_w_px, display_h_px = raster_display_size(width_px_src, height_px_src, row_size)
        place_raster_icon(p, uri, x_center_log, y_center_log, display_w_px, display_h_px, alpha=alpha)
    return p


def _row_scale(row, scale_col):
    """Per-row icon size multiplier; missing, blank, zero, or NaN -> 1.0."""
    value = getattr(row, scale_col, 1.0)
    try:
        scale = float(value)
    except (TypeError, ValueError):
        return 1.0
    if not scale or scale != scale:  # zero or NaN
        return 1.0
    return scale


def _load_icon(icon_dir, name, max_source_px):
    """Load one ``{name}.png`` as (uri, width_px, height_px).

    Geometry is returned separately from sizing so the same icon can be drawn
    at different sizes across rows. Raises FileNotFoundError if the PNG is
    absent (icons are PNG-only; there is no vector fallback).
    """
    png_path = icon_dir / f"{name}.png"
    if not png_path.exists():
        raise FileNotFoundError(f"icon '{name}' not found: expected {png_path}")
    return load_raster_icon(png_path, max_source_px)
