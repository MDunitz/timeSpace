import numpy as np
import colorcet as cc
import pandas as pd
from bokeh.plotting import figure
from bokeh.models import Label, Span, CustomJS
from timeSpace.constants import DIFFUSION_COEFFICIENTS, TIME_MARKERS, SPACE_MARKERS, base_time
from timeSpace.calculations import calculate_diffusion_length, calculate_sphere_volume

DEFAULT_FONT_SIZE = "14pt"


# HELPER FUNCTIONS
def ordered_colors(row, palette, color_indices):
    """Map a ranked row to a color from a palette.

    Parameters
    ----------
    row : Series
        Must have an 'order' column (1-indexed rank).
    palette : list
        Color palette (e.g. colorcet.gouldian).
    color_indices : array
        Pre-computed indices into the palette for each rank.

    Returns
    -------
    str
        Hex color string.
    """
    order = int(row["order"])
    color_index = color_indices[order - 1]
    color = palette[color_index]
    return color


def set_diffusion_line_colors(diffusion_coefficients):
    """Assign evenly-spaced colors to diffusion coefficients.

    Ranks coefficients by magnitude and maps each to a color from the
    colorcet gouldian palette.

    Parameters
    ----------
    diffusion_coefficients : dict
        Mapping of molecule name to diffusion coefficient (astropy Quantity).

    Returns
    -------
    DataFrame
        Columns: example, diffusion coefficient, order, color.
    """
    diffusion_df = pd.Series(diffusion_coefficients).to_frame("diffusion coefficient")
    diffusion_df["order"] = diffusion_df["diffusion coefficient"].rank()
    palette = cc.gouldian
    color_indices = np.linspace(0, len(palette) - 1, len(diffusion_df)).astype(int)
    diffusion_df["color"] = diffusion_df.apply(ordered_colors, palette=palette, color_indices=color_indices, axis=1)
    diffusion_df = diffusion_df.reset_index().rename(columns={"index": "example"})
    return diffusion_df


# SETUP
def add_legend(p, position="right", font_size="12pt"):
    """Move the figure legend and enable click-to-hide.

    Parameters
    ----------
    p : figure
        Bokeh figure with at least one legend.
    position : str
        Where to place the legend: "right", "above", "below", "left".
    font_size : str
        Legend label font size.

    Returns
    -------
    figure
    """
    leg = p.legend[0]
    p.add_layout(leg, position)
    p.legend.click_policy = "hide"
    p.legend.label_text_font_size = font_size
    if position in ("above", "below"):
        p.legend.orientation = "horizontal"
        p.legend.nrows = 2
    return p


def create_space_time_figure(width=1600, height=900, title=" ", space_on_x=True):
    """Create a Stommel-style time-space figure.

    Parameters
    ----------
    space_on_x : bool
        If True (default), x=Space, y=Time (reversed). If False, x=Time, y=Space.
    """
    if space_on_x:
        xl, yl = "Space (m\u00b3)", "Time (s)"
        xr, yr = (1e-27, 1e21), (1e12, 1e-3)
    else:
        xl, yl = "Time (s)", "Space (m\u00b3)"
        xr, yr = (1e-3, 1e12), (1e-21, 1e21)
    p = figure(
        width=width,
        height=height,
        x_axis_type="log",
        y_axis_type="log",
        x_axis_label=xl,
        y_axis_label=yl,
        x_range=xr,
        y_range=yr,
        title=title,
        toolbar_location="below",
        x_axis_location="above",
    )
    p.axis.axis_label_text_font_size = "24pt"
    p.axis.major_label_text_font_size = "12pt"
    p.title.text_font_size = "24pt"
    p.background_fill_color = "#f8f8f8"
    p.grid.grid_line_color = "white"
    p.grid.grid_line_width = 2

    return p


# PREDEFINED DATA


def add_diffusion_lines(p, diffusion_coefficients=DIFFUSION_COEFFICIENTS, include_light_cone=True, space_on_x=True):
    """Add diffusion curves and optional light cone.

    Parameters
    ----------
    p : figure
        Bokeh figure.
    diffusion_coefficients : dict
        Mapping of name → astropy diffusion coefficient.
    include_light_cone : bool
        If True (default), also draw the speed-of-light causality boundary.
    """
    diffusion_df = set_diffusion_line_colors(diffusion_coefficients)
    diffusion_timepoints = np.logspace(-19, 30) * base_time

    for i in range(0, len(diffusion_df)):
        data = diffusion_df.iloc[i]
        diffusion_distance = [
            calculate_diffusion_length(x, data["diffusion coefficient"]) for x in diffusion_timepoints
        ]
        diffusion_volume = [calculate_sphere_volume(x) for x in diffusion_distance]
        vols = [x.value for x in diffusion_volume]
        times = [x.value for x in diffusion_timepoints]
        p.line(
            vols if space_on_x else times,
            times if space_on_x else vols,
            line_alpha=0.5,
            line_width=1,
            line_color=data.color,
            legend_label=f"{data.example} diffusion",
        )
    if include_light_cone:
        p = add_light_cone(p, space_on_x=space_on_x)
    return p


def add_light_cone(p, color="#8B8000", line_dash="solid", line_width=1.5, line_alpha=0.6, space_on_x=True):
    """Add speed-of-light causality boundary to a Stommel diagram.

    Light cone equation:
        L = c * t                     (causal horizon at time t)
        V = (4/3) * pi * (c * t)^3   (maximum causally-connected volume)

    On a log-log Stommel diagram this is a straight line with slope 3
    (log V = 3 log t + const), steeper than diffusion lines (slope 3/2).

    Everything physical must lie below this line.

    Parameters
    ----------
    p : figure
        Bokeh figure.
    color : str
        Line color. Default is dark gold.
    line_dash : str
        Bokeh line dash style.
    line_width : float
        Line width in pixels.
    line_alpha : float
        Line opacity.
    """
    from astropy import constants as const

    c = const.c.to("m/s")  # speed of light in m/s
    timepoints = np.logspace(-19, 13) * base_time  # covers full y-range
    volumes = [calculate_sphere_volume(c * t) for t in timepoints]

    vols = [v.value for v in volumes]
    times = [t.value for t in timepoints]
    p.line(
        vols if space_on_x else times,
        times if space_on_x else vols,
        line_color=color,
        line_width=line_width,
        line_alpha=line_alpha,
        line_dash=line_dash,
        legend_label="Speed of light",
    )
    return p


def add_magnitude_labels(p, font_size=DEFAULT_FONT_SIZE, space_on_x=True):
    """Add axis reference lines and labels.

    Parameters
    ----------
    space_on_x : bool
        If True, TIME→y-axis (horizontal), SPACE→x-axis (vertical).
        If False, TIME→x-axis (vertical), SPACE→y-axis (horizontal).
    """
    # Orientation: which markers go on which axis
    if space_on_x:
        time_dim, space_dim = "width", "height"
    else:
        time_dim, space_dim = "height", "width"

    time_labels = []
    edge = p.x_range.start if hasattr(p.x_range, "start") else 10**-27
    for time_val, label_text in TIME_MARKERS.items():
        time_span = Span(location=time_val, dimension=time_dim, line_color="#cccccc", line_dash="dashed", line_width=1)
        if space_on_x:
            lbl_kwargs = dict(x=edge, y=time_val, text_align="left", text_baseline="middle")
        else:
            lbl_kwargs = dict(
                x=time_val,
                y=p.y_range.end if hasattr(p.y_range, "end") else 1e21,
                text_align="center",
                text_baseline="top",
            )
        label = Label(
            **lbl_kwargs,
            text=label_text,
            text_font_size=font_size,
            text_color="#aaaaaa",
        )
        p.add_layout(label)
        p.add_layout(time_span)
        time_labels.append(label)

    space_labels = []
    for space_val, label_text in SPACE_MARKERS.items():
        space_span = Span(
            location=space_val, dimension=space_dim, line_color="#dddddd", line_dash="dashed", line_width=1
        )
        if space_on_x:
            y_top = (p.y_range.end if hasattr(p.y_range, "end") else 10**-1) * 3
            lbl_kwargs = dict(x=space_val, y=y_top, text_align="center", text_baseline="top")
        else:
            lbl_kwargs = dict(
                y=space_val,
                x=p.x_range.start if hasattr(p.x_range, "start") else 10**-3,
                text_align="left",
                text_baseline="middle",
            )
        label = Label(
            **lbl_kwargs,
            text=label_text,
            text_font_size=font_size,
            text_color="#aaaaaa",
        )
        p.add_layout(label)
        p.add_layout(space_span)
        space_labels.append(label)

    # Sticky callbacks: labels follow visible range edges on pan/zoom.
    if space_on_x:
        time_cb = CustomJS(
            args=dict(labels=time_labels, x_range=p.x_range),
            code="const left = Math.min(x_range.start, x_range.end); for (const l of labels) { l.x = left; }",
        )
        p.x_range.js_on_change("start", time_cb)
        p.x_range.js_on_change("end", time_cb)
        space_cb = CustomJS(
            args=dict(labels=space_labels, y_range=p.y_range),
            code="const top = Math.min(y_range.start, y_range.end) * 3; for (const l of labels) { l.y = top; }",
        )
        p.y_range.js_on_change("start", space_cb)
        p.y_range.js_on_change("end", space_cb)
    else:
        time_cb = CustomJS(
            args=dict(labels=time_labels, y_range=p.y_range),
            code="const top = Math.max(y_range.start, y_range.end); for (const l of labels) { l.y = top; }",
        )
        p.y_range.js_on_change("start", time_cb)
        p.y_range.js_on_change("end", time_cb)
        space_cb = CustomJS(
            args=dict(labels=space_labels, x_range=p.x_range),
            code="const left = Math.min(x_range.start, x_range.end); for (const l of labels) { l.x = left; }",
        )
        p.x_range.js_on_change("start", space_cb)
        p.x_range.js_on_change("end", space_cb)

    return p


def _render_glyph(p, row, color, alpha, visible, legend_label, space_on_x=True):
    """Render a single process glyph based on its geometry classification.

    Geometry types (from classify_process_geometry):
        "ellipse" — both axes have range
        "vline"   — single time value, spans a range of space
        "hline"   — single space value, spans a range of time
        "point"   — single value on both axes
    """
    geometry = row.get("geometry", "ellipse")

    if geometry == "ellipse":
        p.patch(
            row.x_coords,
            row.y_coords,
            fill_color=color,
            fill_alpha=alpha,
            line_color=color,
            legend_label=legend_label,
            visible=visible,
        )
    elif geometry == "vline":
        # Single time value spanning a range of space
        t_val = row.Time_min.value
        xs = [row.Space_min.value, row.Space_max.value]
        ys = [t_val, t_val]
        if not space_on_x:
            xs, ys = ys, xs
        p.line(
            xs,
            ys,
            line_color=color,
            line_width=2.5,
            line_alpha=0.8,
            legend_label=legend_label,
            visible=visible,
        )
    elif geometry == "hline":
        # Single space value spanning a range of time
        s_val = row.Space_min.value
        xs = [s_val, s_val]
        ys = [row.Time_min.value, row.Time_max.value]
        if not space_on_x:
            xs, ys = ys, xs
        p.line(
            xs,
            ys,
            line_color=color,
            line_width=2.5,
            line_alpha=0.8,
            legend_label=legend_label,
            visible=visible,
        )
    elif geometry == "point":
        # Single point on both axes
        sx, sy = [row.Space_min.value], [row.Time_min.value]
        if not space_on_x:
            sx, sy = sy, sx
        p.scatter(
            sx,
            sy,
            marker="diamond",
            size=12,
            fill_color=color,
            fill_alpha=0.6,
            line_color=color,
            line_width=1.5,
            legend_label=legend_label,
            visible=visible,
        )


def _label_anchor(row, space_on_x=True):
    """Return (x, y, align) for label placement based on geometry type."""
    geometry = row.get("geometry", "ellipse")
    if geometry == "vline":
        if space_on_x:
            return row.Space_max.value, row.Time_min.value, "left"
        else:
            return row.Time_min.value, row.Space_max.value, "left"
    elif geometry == "hline":
        if space_on_x:
            return row.Space_min.value, row.Time_max.value, "left"
        else:
            return row.Time_max.value, row.Space_min.value, "left"
    elif geometry == "point":
        if space_on_x:
            return row.Space_min.value, row.Time_min.value, "left"
        else:
            return row.Time_min.value, row.Space_min.value, "left"
    else:
        return None, None, None  # caller uses existing logic


def add_predefined_processes(p, process_df, interactive=True, font_size=DEFAULT_FONT_SIZE, space_on_x=True):
    """Render predefined process glyphs with labels.

    Parameters
    ----------
    space_on_x : bool
        Must match the space_on_x used in transform_predefined_processes().
    """
    required = {"Name", "FillAlpha", "TextAlpha", "geometry", "Color"}
    missing = required - set(process_df.columns)
    if missing:
        raise ValueError(
            f"process_df is missing columns: {missing}. "
            f"Did you forget to call transform_predefined_processes() first?"
        )
    visible = not interactive
    for i, row in process_df.iterrows():
        _render_glyph(p, row, row.Color, row.FillAlpha, visible, row.Name, space_on_x=space_on_x)

        lx, ly, align = _label_anchor(row, space_on_x=space_on_x)
        if lx is None:
            has_side = "label_side" in process_df.columns
            side = str(row.label_side).strip() if has_side and str(row.get("label_side", "")).strip() else "right"
            if space_on_x:
                lx = row.Space_min.value if side == "left" else row.Space_max.value
                ly = np.sqrt(row.Time_min.value * row.Time_max.value)
            else:
                lx = row.Time_min.value if side == "left" else row.Time_max.value
                ly = np.sqrt(row.Space_min.value * row.Space_max.value)
            align = "right" if side == "left" else "left"

        has_xo = "x_offset" in process_df.columns
        has_yo = "y_offset" in process_df.columns
        xo_val = str(row.get("x_offset", "")).strip() if has_xo else ""
        yo_val = str(row.get("y_offset", "")).strip() if has_yo else ""
        p.text(
            x=lx,
            y=ly,
            text=[row.Name],
            text_font_size=font_size,
            text_color=row.Color,
            text_alpha=row.TextAlpha,
            text_align=align,
            x_offset=int(float(xo_val)) if xo_val else 0,
            y_offset=int(float(yo_val)) if yo_val else 0,
            legend_label=row.Name,
            visible=visible,
        )
    return p


# USER DATA
def add_processes(
    p,
    process_df,
    group="Prefix",
    interactive=True,
    font_size=DEFAULT_FONT_SIZE,
    label_side="right",
    category_col=None,
    category_colors=None,
    space_on_x=True,
):
    """Render process ellipses and labels on a Stommel diagram.

    label_side: global default — "left" or "right".
    Per-row override: set a "label_side" column in process_df to "left" or "right".
      "left"  → anchor at Space_min, right-aligned (label sits left of ellipse)
      "right" → anchor at Space_max, left-aligned  (label sits right of ellipse)

    category_col: column name holding category strings (e.g. "category_type").
      When provided alongside category_colors, inserts an invisible header glyph
      before each new category group so the legend shows section labels.
    category_colors: dict mapping category string → hex color.
    """
    required = {"Name", "FillAlpha", "geometry"}
    missing = required - set(process_df.columns)
    if missing:
        raise ValueError(
            f"process_df is missing columns: {missing}. "
            f"Did you forget to call transform_process_response_sheet() first?"
        )
    visible = not interactive
    has_col = "label_side" in process_df.columns

    # Track last seen category for header injection
    prev_cat = None

    for group_name, df in process_df.groupby(group, sort=False):
        for i, row in df.iterrows():

            # Inject category header glyph before first process in each category
            if category_col and category_colors:
                cat = row.get(category_col)
                if cat is not None and cat != prev_cat:
                    color = category_colors.get(cat, "#888888")
                    p.circle(
                        [],
                        [],
                        legend_label=f"— {cat} —",
                        fill_color=color,
                        size=10,
                        fill_alpha=0.0,
                        line_alpha=0.0,
                    )
                    prev_cat = cat

            glyph_color = (
                category_colors.get(row.get(category_col), row.Color) if category_col and category_colors else row.Color
            )
            _render_glyph(p, row, glyph_color, row.FillAlpha, visible, row.Name, space_on_x=space_on_x)

            side = row.label_side if has_col and row.label_side in ("left", "right") else label_side
            # For non-ellipse geometries, use geometry-aware label placement
            geom_lx, geom_ly, geom_align = _label_anchor(row, space_on_x=space_on_x)
            if geom_lx is not None:
                lx = geom_lx
                ly = geom_ly
                align = geom_align
            else:
                if space_on_x:
                    if side == "left":
                        lx = row.Space_min.value
                        align = "right"
                    else:
                        lx = row.Space_max.value
                        align = "left"
                    ly = np.sqrt(row.Time_min.value * row.Time_max.value)
                else:
                    if side == "left":
                        lx = row.Time_min.value
                        align = "right"
                    else:
                        lx = row.Time_max.value
                        align = "left"
                    ly = np.sqrt(row.Space_min.value * row.Space_max.value)
            has_label_text = "label_text" in process_df.columns
            display = row.label_text if has_label_text else row.ShortName
            lines = display.split("\n")
            LINE_PX = 15  # vertical gap between lines in screen pixels
            for line_i, line_text in enumerate(lines):
                p.text(
                    x=lx,
                    y=ly,
                    y_offset=row.y_offset + line_i * LINE_PX,
                    x_offset=row.x_offset,
                    text=[line_text],
                    text_font_size=font_size,
                    text_font_style="bold",
                    text_color=glyph_color,
                    text_alpha=1.0,
                    text_align=align,
                    legend_label=row.Name,
                    visible=visible,
                )
    return p
