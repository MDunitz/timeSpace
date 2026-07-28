"""SVG icon glyphs for Stommel diagrams.

Icons are drawn as filled Bokeh patches at the log-space centre of each
process ellipse. Every icon is scaled to the same ink area, so a sparse
outline drawing and a solid shape carry equal visual weight.
"""

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


def add_icons(p, process_df, icon_dir, size_px=28, space_on_x=True, plot_size_px=None, alpha=1.0):
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
        Folder of .svg icons.
    size_px : float
        Nominal icon size. Every icon is scaled to cover size_px**2 of ink,
        regardless of the size of the process ellipse it sits on.
    space_on_x : bool
        Must match the value passed to create_space_time_figure.
    plot_size_px : tuple of (width, height), optional
        Plot frame size. Defaults to (p.width, p.height), which includes axis
        furniture and so renders icons a few percent small; pass the inner
        frame size for exact sizing.
    alpha : float
        Opacity applied to every icon.
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
            cache[name] = normalize_icon(load_icon(icon_dir / f"{name}.svg"), target_area)
        time_center = calculate_log_center(row.Time_min.value, row.Time_max.value)
        space_center = calculate_log_center(row.Space_min.value, row.Space_max.value)
        if space_on_x:
            x_center_log, y_center_log = space_center, time_center
        else:
            x_center_log, y_center_log = time_center, space_center
        place_icon(
            p,
            cache[name],
            x_center_log,
            y_center_log,
            x_span,
            y_span,
            width_px,
            height_px,
            alpha=alpha,
        )
    return p
