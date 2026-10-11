"""Category colour legend drawn on the plot canvas.

The checkbox row is the on-screen colour key, but it is HTML and so is left
out of the image the save tool writes. This legend lives on the canvas, lists
only the categories currently showing, and is therefore part of the download.
"""

from bokeh.models import Legend, LegendItem

from .config import CATEGORY_COLORS

LEGEND_SWATCH_ALPHA = 0.5
LEGEND_SWATCH_SIZE = 12
LEGEND_FONT_SIZE = "10pt"


def add_category_legend(p, categories, shown=False):
    """Add a legend with one colour swatch per category, right of the plot.

    Swatches come from renderers whose single point is NaN: nothing is drawn
    on the plot, but the legend still gets a glyph to paint. `shown` sets the
    starting state of every item.
    """
    items = []
    for category in categories:
        color = CATEGORY_COLORS[category]
        swatch = p.scatter(
            [float("nan")],
            [float("nan")],
            marker="square",
            size=LEGEND_SWATCH_SIZE,
            fill_color=color,
            fill_alpha=LEGEND_SWATCH_ALPHA,
            line_color=color,
        )
        items.append(LegendItem(label=category, renderers=[swatch], visible=shown))
    legend = Legend(
        items=items,
        visible=shown,
        label_text_font_size=LEGEND_FONT_SIZE,
        border_line_color=None,
        background_fill_alpha=0.0,
        spacing=2,
        padding=4,
        margin=12,
    )
    p.add_layout(legend, "right")
    return legend
