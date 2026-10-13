"""Legends drawn on the plot canvas, so the save tool's PNG carries them.

The checkbox row is HTML and is left out of the downloaded image. Two canvas
legends sit right of the plot instead:
- the colour legend: one swatch per category with something showing, plus
  the custom object while one is plotted;
- the number key: in "Numbers" label mode, number -> name for every object
  showing, each with its category swatch.
"""

from bokeh.models import Legend, LegendItem

from .config import CATEGORY_COLORS, CUSTOM_COLOR

LEGEND_SWATCH_ALPHA = 0.5
LEGEND_SWATCH_SIZE = 12
LEGEND_FONT_SIZE = "10pt"
KEY_SWATCH_SIZE = 8
KEY_FONT_SIZE = "8pt"
KEY_ROW_HEIGHT = 11
# Rows per key column before the key wraps into another column; sized so a
# column fits the plot frame at the explorer's figure height.
KEY_MAX_ROWS = 42


def swatch(p, color, size):
    """Renderer that draws nothing on the plot (its one point is NaN) but
    gives a legend item a coloured square to paint."""
    return p.scatter(
        [float("nan")],
        [float("nan")],
        marker="square",
        size=size,
        fill_color=color,
        fill_alpha=LEGEND_SWATCH_ALPHA,
        line_color=color,
    )


def canvas_legend(p, items, visible, **style):
    legend = Legend(
        items=items,
        visible=visible,
        border_line_color=None,
        background_fill_alpha=0.0,
        padding=4,
        margin=12,
        **style,
    )
    p.add_layout(legend, "right")
    return legend


def add_category_legend(p, categories, shown=False, custom=False):
    """Colour legend: one item per category, then a custom-object item.

    `shown` sets the starting state of the category items. With `custom`, a
    last item (hidden until an object is plotted) carries the custom colour.
    """
    items = [
        LegendItem(label=cat, renderers=[swatch(p, CATEGORY_COLORS[cat], LEGEND_SWATCH_SIZE)], visible=shown)
        for cat in categories
    ]
    if custom:
        items.append(LegendItem(label="Custom", renderers=[swatch(p, CUSTOM_COLOR, LEGEND_SWATCH_SIZE)], visible=False))
    return canvas_legend(p, items, shown, label_text_font_size=LEGEND_FONT_SIZE, spacing=2)


def key_label(number, name):
    return f"{number}  {name}"


def add_number_key(p, df):
    """Number key: one hidden item per object, in number order.

    Returns (legend, rows), where rows[j] is the df position of item j, so a
    callback can show the items for whichever objects are on the plot.
    """
    ordered = df.reset_index(drop=True).sort_values("Number")
    items = [
        LegendItem(
            label=key_label(r.Number, r.FullName),
            renderers=[swatch(p, CATEGORY_COLORS[r.Category], KEY_SWATCH_SIZE)],
            visible=False,
        )
        for _, r in ordered.iterrows()
    ]
    legend = canvas_legend(
        p,
        items,
        False,
        label_text_font_size=KEY_FONT_SIZE,
        label_height=KEY_ROW_HEIGHT,
        glyph_height=KEY_ROW_HEIGHT,
        glyph_width=KEY_ROW_HEIGHT,
        spacing=0,
        nrows=KEY_MAX_ROWS,
    )
    return legend, ordered.index.tolist()
