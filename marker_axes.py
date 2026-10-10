"""Named magnitude markers (Second, Day, km³ ...) drawn as extra axes.

Each marker gets a dashed guide line across the plot and a tick label on an
axis outside the plot frame. An axis follows pan and zoom on its own and only
draws the ticks currently in view, so the names never cover the data and stay
visible for as long as their magnitude is on screen.
"""

from bokeh.models import FixedTicker, LogAxis, Span

MARKER_COLOR = "#888888"
TIME_GUIDE_COLOR = "#cccccc"
SPACE_GUIDE_COLOR = "#dddddd"
# Time names are long; on a horizontal axis they are slanted so that
# neighbours two decades apart do not collide.
TIME_MARKER_ANGLE = 0.6  # radians


def marker_axis(markers, font_size, orientation=0.0):
    """Log axis whose only ticks are the named markers ({value: name})."""
    ticks = sorted(markers)
    return LogAxis(
        ticker=FixedTicker(ticks=ticks, minor_ticks=[]),
        major_label_overrides={t: markers[t].replace("\n", " ") for t in ticks},
        major_label_text_font_size=font_size,
        major_label_text_color=MARKER_COLOR,
        major_label_orientation=orientation,
        major_tick_line_color=MARKER_COLOR,
        axis_line_color=None,
        major_tick_in=0,
    )


def marker_axis_sides(p):
    """(x side, y side) for the marker axes: opposite the figure's own axes."""
    x_side = "below" if any(a in list(p.above) for a in p.xaxis) else "above"
    y_side = "left" if any(a in list(p.right) for a in p.yaxis) else "right"
    return x_side, y_side


def add_marker_axes(p, time_markers, space_markers, font_size, space_on_x=True):
    """Add guide lines and a named marker axis for time and for space.

    space_on_x : bool
        True when the figure has space on x and time on y; False for time on
        x and space on y. Decides which markers go on which axis.
    """
    x_markers, y_markers = (space_markers, time_markers) if space_on_x else (time_markers, space_markers)
    x_color, y_color = (SPACE_GUIDE_COLOR, TIME_GUIDE_COLOR) if space_on_x else (TIME_GUIDE_COLOR, SPACE_GUIDE_COLOR)
    for value in x_markers:
        p.add_layout(Span(location=value, dimension="height", line_color=x_color, line_dash="dashed", line_width=1))
    for value in y_markers:
        p.add_layout(Span(location=value, dimension="width", line_color=y_color, line_dash="dashed", line_width=1))

    x_side, y_side = marker_axis_sides(p)
    x_angle = 0.0 if space_on_x else TIME_MARKER_ANGLE
    p.add_layout(marker_axis(x_markers, font_size, orientation=x_angle), x_side)
    p.add_layout(marker_axis(y_markers, font_size), y_side)
    return p
