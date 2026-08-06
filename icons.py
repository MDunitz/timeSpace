"""Icon glyphs for Stommel diagrams.

Icons are drawn at the log-space centre of each process ellipse. An SVG icon
is flattened to filled Bokeh patches; a PNG icon is drawn as a raster image
glyph, which preserves gradients and soft alpha edges that the vector path
collapses to a flat colour. Either way every icon is scaled to the same ink
area, so a sparse drawing and a solid shape carry equal visual weight.
"""

import base64
import io
from pathlib import Path as FilePath

import numpy as np
from PIL import Image, ImageDraw
from svgelements import SVG, Path as SvgPath, Shape

from timeSpace.calculations import calculate_log_center

CURVE_SAMPLES = 16
AREA_RASTER = 256


def _hex(color):
    """Return an SVG paint as a hex string, or None when unpainted."""
    if color is None or getattr(color, "value", None) is None:
        return None
    return color.hex


def _bbox(shapes):
    xs = np.concatenate([shape[0] for shape in shapes])
    ys = np.concatenate([shape[1] for shape in shapes])
    return xs.min(), ys.min(), xs.max(), ys.max()


def _sample_subpath(subpath, curve_samples):
    """Flatten one subpath into polygon vertices, dropping repeated points."""
    points = []
    for segment in subpath:
        kind = type(segment).__name__
        if kind == "Move":
            continue
        if kind in ("Line", "Close"):
            samples = [segment.point(0.0), segment.point(1.0)]
        else:
            samples = [segment.point(i / curve_samples) for i in range(curve_samples + 1)]
        for point in samples:
            if not points or abs(point.x - points[-1][0]) > 1e-9 or abs(point.y - points[-1][1]) > 1e-9:
                points.append((point.x, point.y))
    return points


def load_icon(svg_path, curve_samples=CURVE_SAMPLES):
    """Flatten an SVG file into polygons in SVG user coordinates.

    Group transforms are composed by the parser, so vertices come back in the
    document's own coordinate system with y increasing downward.

    Returns
    -------
    list of (xs, ys, fill, stroke)
        One entry per subpath. `fill` is None for stroke-only subpaths.
    """
    svg = SVG.parse(str(svg_path), reify=True)
    shapes = []
    for element in svg.elements():
        if not isinstance(element, Shape):
            continue
        fill = _hex(element.fill)
        stroke = _hex(element.stroke)
        if fill is None and stroke is None:
            continue
        for subpath in SvgPath(element).as_subpaths():
            points = _sample_subpath(subpath, curve_samples)
            if len(points) < 2:
                continue
            xs = np.array([point[0] for point in points], dtype=float)
            ys = np.array([point[1] for point in points], dtype=float)
            shapes.append((xs, ys, fill, stroke))
    return shapes


def measure_ink_area(shapes, raster=AREA_RASTER):
    """Union area covered by an icon's filled subpaths, in SVG user units squared.

    Rasterizes rather than summing per-subpath shoelace areas: icon outlines
    routinely overlap their own fills, and summing double-counts the overlap.
    """
    filled = [shape for shape in shapes if shape[2] is not None] or shapes
    x0, y0, x1, y1 = _bbox(filled)
    width, height = x1 - x0, y1 - y0
    image = Image.new("1", (raster, raster), 0)
    draw = ImageDraw.Draw(image)
    for xs, ys, _fill, _stroke in filled:
        px = (xs - x0) / width * (raster - 1)
        py = (ys - y0) / height * (raster - 1)
        draw.polygon(list(zip(px, py)), fill=1)
    covered = np.asarray(image, dtype=bool).sum()
    return covered / raster**2 * width * height


def normalize_icon(shapes, target_area, raster=AREA_RASTER):
    """Scale an icon to a target ink area and centre it on the origin.

    Equal-area normalization:
        s = sqrt(A_target / A_icon)

    The scale is uniform in x and y, so the icon's aspect ratio is preserved.
    """
    scale = np.sqrt(target_area / measure_ink_area(shapes, raster))
    x0, y0, x1, y1 = _bbox(shapes)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    return [((xs - cx) * scale, (ys - cy) * scale, fill, stroke) for xs, ys, fill, stroke in shapes]


def log_span(axis_range):
    """Signed log10 extent of an axis; negative when the range is reversed.

    Equation:
        span = log10(end) - log10(start)
    """
    return np.log10(axis_range.end) - np.log10(axis_range.start)


def place_icon(p, shapes, x_center_log, y_center_log, x_span, y_span, width_px, height_px, alpha=1.0):
    """Map pixel-space icon polygons onto log axes at a given centre.

    Equations:
        dx_log = px_x * (log10(x_end) - log10(x_start)) / width_px
        dy_log = -px_y * (log10(y_end) - log10(y_start)) / height_px
        x = 10 ** (x_center_log + dx_log)
        y = 10 ** (y_center_log + dy_log)

    x and y are scaled independently because one log decade spans a different
    number of pixels on each axis. The minus sign on dy_log converts SVG's
    downward y to the axis direction; a reversed range (start > end) is
    carried by the sign of y_span and needs no special case.
    """
    fill_xs, fill_ys, fill_colors = [], [], []
    line_xs, line_ys, line_colors = [], [], []
    for xs, ys, fill, stroke in shapes:
        data_x = 10 ** (x_center_log + xs * x_span / width_px)
        data_y = 10 ** (y_center_log - ys * y_span / height_px)
        if fill is not None:
            fill_xs.append(data_x)
            fill_ys.append(data_y)
            fill_colors.append(fill)
        else:
            line_xs.append(data_x)
            line_ys.append(data_y)
            line_colors.append(stroke)
    if fill_xs:
        p.patches(xs=fill_xs, ys=fill_ys, fill_color=fill_colors, line_color=fill_colors, alpha=alpha)
    if line_xs:
        p.multi_line(xs=line_xs, ys=line_ys, line_color=line_colors, alpha=alpha)
    return p


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
    axis ranges, matching place_icon; anchor="center" puts the raster's own
    centre on the process ellipse centre. Transparent regions of the PNG let
    the grid and ellipse behind it show through.
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


def add_icons(p, process_df, icon_dir, size_px=28, space_on_x=True, plot_size_px=None, alpha=1.0, max_source_px=256):
    """Draw an icon at the log-space centre of each process ellipse.

    Icon size is fixed in pixels, which means vertices are baked into data
    coordinates at call time. Call this last, after the axis ranges and figure
    dimensions are final; changing either afterwards distorts the icons.

    Parameters
    ----------
    p : bokeh.plotting.figure
        Figure with log axes, ranges already set.
    process_df : pandas.DataFrame
        Rows with Time_min, Time_max, Space_min, Space_max as astropy
        Quantities, plus an `icon` column naming a file in `icon_dir`
        without its extension. Rows with a blank icon are skipped.
    icon_dir : path-like
        Folder of .png and/or .svg icons. For a given name a PNG is used
        when present (raster, gradients preserved), else the SVG.
    size_px : float
        Nominal icon size in pixels. An SVG icon is scaled to cover size_px**2
        of ink; a PNG icon has its content bounding box fitted so its longest
        side is size_px. Either way the size is independent of the process
        ellipse the icon sits on.
    space_on_x : bool
        Must match the value passed to create_space_time_figure.
    plot_size_px : tuple of (width, height), optional
        Plot frame size. Defaults to (p.width, p.height), which includes axis
        furniture and so renders icons a few percent small; pass the inner
        frame size for exact sizing.
    alpha : float
        Opacity applied to every icon.
    max_source_px : int
        PNG icons are downscaled so their longest side is at most this before
        being embedded, capping the base64 payload.
    """
    width_px, height_px = plot_size_px or (p.width, p.height)
    x_span = log_span(p.x_range)
    y_span = log_span(p.y_range)
    target_area = float(size_px) ** 2
    icon_dir = FilePath(icon_dir)
    cache = {}

    for row in process_df.itertuples():
        name = str(getattr(row, "icon", "") or "").strip()
        if not name or name == "nan":
            continue
        if name not in cache:
            cache[name] = _prepare_icon(icon_dir, name, target_area, size_px, max_source_px)
        time_center = calculate_log_center(row.Time_min.value, row.Time_max.value)
        space_center = calculate_log_center(row.Space_min.value, row.Space_max.value)
        if space_on_x:
            x_center_log, y_center_log = space_center, time_center
        else:
            x_center_log, y_center_log = time_center, space_center
        kind, payload = cache[name]
        if kind == "raster":
            uri, display_w_px, display_h_px = payload
            place_raster_icon(p, uri, x_center_log, y_center_log, display_w_px, display_h_px, alpha=alpha)
        else:
            place_icon(p, payload, x_center_log, y_center_log, x_span, y_span, width_px, height_px, alpha=alpha)
    return p


def _prepare_icon(icon_dir, name, target_area, size_px, max_source_px):
    """Load and normalize one icon, dispatching on the file present in icon_dir.

    A ``{name}.png`` is drawn as a raster image glyph (gradients and soft
    alpha edges survive), cropped to content and fitted by bounding box;
    otherwise ``{name}.svg`` is flattened to vector patches and normalized by
    ink area. PNG is preferred when both exist.

    Returns
    -------
    ("raster", (uri, display_w_px, display_h_px)) or ("vector", shapes)
    """
    png_path = icon_dir / f"{name}.png"
    if png_path.exists():
        uri, width_px, height_px = load_raster_icon(png_path, max_source_px)
        display_w_px, display_h_px = raster_display_size(width_px, height_px, size_px)
        return "raster", (uri, display_w_px, display_h_px)
    return "vector", normalize_icon(load_icon(icon_dir / f"{name}.svg"), target_area)
