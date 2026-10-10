"""Figure scaffold: log-log Bokeh figure plus time/space reference markers."""

from bokeh.plotting import figure

from timeSpace.constants import TIME_MARKERS, SPACE_MARKERS
from timeSpace.marker_axes import add_marker_axes

from .config import FIGURE_HEIGHT, X_RANGE, Y_RANGE, FONT_SIZE, LABEL_FONT_SIZE


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

    # Time on x, space on y: time names on the top axis, volume names on the right.
    add_marker_axes(p, TIME_MARKERS, SPACE_MARKERS, LABEL_FONT_SIZE, space_on_x=False)
    return p
