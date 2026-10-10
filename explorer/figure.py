"""Figure scaffold: log-log Bokeh figure plus time/space reference markers."""

from bokeh.plotting import figure
from bokeh.models import FixedTicker, LogAxis, Span

from timeSpace.constants import TIME_MARKERS, SPACE_MARKERS

from .config import FIGURE_HEIGHT, X_RANGE, Y_RANGE, FONT_SIZE, LABEL_FONT_SIZE

MARKER_COLOR = "#888888"
# Time-marker names are slanted so neighbours two decades apart do not collide.
TIME_MARKER_ANGLE = 0.6  # radians


def create_figure(x_range=X_RANGE, y_range=Y_RANGE):
    p = figure(
        width=1200,
        height=FIGURE_HEIGHT,
        sizing_mode="stretch_width",
        x_axis_type="log",
        y_axis_type="log",
        x_axis_label="Time (s)",
        y_axis_label="Space (m³)",
        x_range=x_range,
        y_range=y_range,
        title="Stommel Diagram — Reference Object Explorer",
        toolbar_location="above",
        tools="pan,wheel_zoom,box_zoom,reset",
    )
    p.axis.axis_label_text_font_size = FONT_SIZE
    p.axis.major_label_text_font_size = "10pt"
    p.title.text_font_size = "14pt"
    p.background_fill_color = "#fafafa"

    add_marker_axes(p)
    return p


def marker_axis(markers, orientation=0.0):
    """Log axis whose only ticks are the named markers.

    An axis sits outside the plot frame, follows pan and zoom on its own and
    only draws the ticks currently in view, so marker names never cover the
    data and never scroll out of sight while their magnitude is on screen.
    """
    ticks = sorted(markers)
    return LogAxis(
        ticker=FixedTicker(ticks=ticks, minor_ticks=[]),
        major_label_overrides={t: markers[t].replace("\n", " ") for t in ticks},
        major_label_text_font_size=LABEL_FONT_SIZE,
        major_label_text_color=MARKER_COLOR,
        major_label_orientation=orientation,
        major_tick_line_color=MARKER_COLOR,
        axis_line_color=None,
        major_tick_in=0,
    )


def add_marker_axes(p):
    """Dashed guide lines at each marker, named on a top and a right axis."""
    for t in TIME_MARKERS:
        p.add_layout(Span(location=t, dimension="height", line_color="#cccccc", line_dash="dashed", line_width=1))
    for s in SPACE_MARKERS:
        p.add_layout(Span(location=s, dimension="width", line_color="#dddddd", line_dash="dashed", line_width=1))
    p.add_layout(marker_axis(TIME_MARKERS, orientation=TIME_MARKER_ANGLE), "above")
    p.add_layout(marker_axis(SPACE_MARKERS), "right")
