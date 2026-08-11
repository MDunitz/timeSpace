"""Figure scaffold: log-log Bokeh figure plus time/space reference markers."""

from bokeh.plotting import figure
from bokeh.models import Span, Label

from timeSpace.constants import TIME_MARKERS, SPACE_MARKERS

from .config import X_RANGE, Y_RANGE, FONT_SIZE, LABEL_FONT_SIZE


def create_figure():
    p = figure(
        width=1200,
        height=720,
        sizing_mode="stretch_width",
        x_axis_type="log",
        y_axis_type="log",
        x_axis_label="Time (s)",
        y_axis_label="Space (m³)",
        x_range=X_RANGE,
        y_range=Y_RANGE,
        title="Stommel Diagram — Reference Object Explorer",
        toolbar_location="above",
        tools="pan,wheel_zoom,box_zoom,reset",
    )
    p.axis.axis_label_text_font_size = FONT_SIZE
    p.axis.major_label_text_font_size = "10pt"
    p.title.text_font_size = "14pt"
    p.background_fill_color = "#fafafa"

    # Reference grid lines
    for t, label_text in TIME_MARKERS.items():
        p.add_layout(Span(location=t, dimension="height", line_color="#cccccc", line_dash="dashed", line_width=1))
        p.add_layout(
            Label(
                x=t,
                y=Y_RANGE[1],
                text=label_text,
                text_font_size=LABEL_FONT_SIZE,
                text_color="#aaaaaa",
                text_align="center",
                text_baseline="top",
            )
        )

    for s, label_text in SPACE_MARKERS.items():
        p.add_layout(Span(location=s, dimension="width", line_color="#dddddd", line_dash="dashed", line_width=1))
        p.add_layout(
            Label(
                y=s,
                x=X_RANGE[0] * 1.5,
                text=label_text,
                text_font_size=LABEL_FONT_SIZE,
                text_color="#aaaaaa",
                text_align="left",
            )
        )

    return p
