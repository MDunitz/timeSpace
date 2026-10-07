"""Glyph + ColumnDataSource construction for the explorer figure.

Each builder creates its sources and attaches its glyphs to the figure in
the same order the original inline build_explorer did, so the emitted Bokeh
document is structurally identical. Reference and custom (user-defined)
objects use parallel patch/line/point/label sources; index alignment across
the reference sources lets the JS callbacks toggle everything by one index.
"""

from bokeh.models import ColumnDataSource, CustomJS, HoverTool

# HTML template (not the tuple form) so long Reference text wraps.
REFERENCE_TOOLTIP = """
<div style="max-width: 360px; font-size: 12px; line-height: 1.35;">
  <div><b>@name</b> <span style="color: #666;">(@category)</span></div>
  <div>Time: @time_label</div>
  <div>Space: @space_label</div>
  <div style="color: #444;">Source: @reference</div>
</div>
"""

# Hidden objects keep their geometry and are switched off through alpha, so
# without this filter the hover tool still reports them.
HOVER_ONLY_VISIBLE_JS = "export default (args, tool, {value}) => value > 0"


def _hover_columns(df):
    """Columns every hoverable reference source carries for the tooltip."""
    return dict(
        name=df.FullName.tolist(),
        category=df.Category.tolist(),
        reference=df.Reference.tolist(),
        time_label=df.TimeLabel.tolist(),
        space_label=df.SpaceLabel.tolist(),
    )


def add_reference_glyphs(p, df):
    """Build the index-aligned reference-object sources and attach glyphs.

    Returns (source, line_source, point_source, label_source, patches),
    where `patches` is the renderer the hover tool is bound to.
    """

    # Main reference object patches (ellipses only). Non-ellipse objects get
    # empty xs/ys — they render via the line/point sources below. Index
    # alignment is preserved so JS callbacks toggle all sources by index.
    def _patch_coords(row):
        if row.geometry == "ellipse":
            return row.x_coords.tolist(), row.y_coords.tolist()
        return [], []

    source = ColumnDataSource(
        data=dict(
            xs=[_patch_coords(row)[0] for _, row in df.iterrows()],
            ys=[_patch_coords(row)[1] for _, row in df.iterrows()],
            color=df.Color.tolist(),
            alpha=[0.0] * len(df),  # start hidden
            line_alpha=[0.0] * len(df),
            **_hover_columns(df),
            time_min=[row.Time_min.value for _, row in df.iterrows()],
            time_max=[row.Time_max.value for _, row in df.iterrows()],
            space_min=[row.Space_min.value for _, row in df.iterrows()],
            space_max=[row.Space_max.value for _, row in df.iterrows()],
        )
    )

    patches = p.patches(
        "xs",
        "ys",
        source=source,
        fill_color="color",
        fill_alpha="alpha",
        line_color="color",
        line_alpha="line_alpha",
        line_width=2,
    )

    # Line source for vline/hline objects (index-aligned)
    def _line_coords(row):
        if row.geometry == "vline":
            t = row.Time_min.value
            return [t, t], [row.Space_min.value, row.Space_max.value]
        elif row.geometry == "hline":
            s = row.Space_min.value
            return [row.Time_min.value, row.Time_max.value], [s, s]
        return [], []

    line_source = ColumnDataSource(
        data=dict(
            xs=[_line_coords(row)[0] for _, row in df.iterrows()],
            ys=[_line_coords(row)[1] for _, row in df.iterrows()],
            color=df.Color.tolist(),
            alpha=[0.0] * len(df),
            **_hover_columns(df),
        )
    )

    lines = p.multi_line(
        "xs",
        "ys",
        source=line_source,
        line_color="color",
        line_alpha="alpha",
        line_width=2.5,
    )

    # Point source for fully degenerate objects (index-aligned)
    point_source = ColumnDataSource(
        data=dict(
            x=[row.Time_min.value if row.geometry == "point" else float("nan") for _, row in df.iterrows()],
            y=[row.Space_min.value if row.geometry == "point" else float("nan") for _, row in df.iterrows()],
            color=df.Color.tolist(),
            alpha=[0.0] * len(df),
            **_hover_columns(df),
        )
    )

    points = p.scatter(
        "x",
        "y",
        source=point_source,
        marker="diamond",
        size=12,
        fill_color="color",
        fill_alpha="alpha",
        line_color="color",
        line_alpha="alpha",
        line_width=1.5,
    )

    # Hover on every reference shape (ellipses, lines and points), not on
    # text glyphs or the custom source, and only while the shape is shown.
    hover = HoverTool(
        renderers=[patches, lines, points],
        tooltips=REFERENCE_TOOLTIP,
        filters={"@alpha": CustomJS(code=HOVER_ONLY_VISIBLE_JS)},
    )
    p.add_tools(hover)

    # Name labels (hidden until selection)
    label_source = ColumnDataSource(
        data=dict(
            x=df.label_x.tolist(),
            y=df.label_y.tolist(),
            text=df.FullName.tolist(),
            alpha=[0.0] * len(df),
            color=df.Color.tolist(),
        )
    )

    p.text(
        "x",
        "y",
        source=label_source,
        text="text",
        text_font_size="8pt",
        text_color="color",
        text_alpha="alpha",
        text_align="center",
        text_baseline="middle",
    )

    return source, line_source, point_source, label_source, patches


def add_custom_glyphs(p):
    """Build the user-defined-object sources and attach glyphs.

    Returns (custom_source, custom_line_source, custom_point_source,
    custom_label_source). Geometry is chosen browser-side in CUSTOM_OBJECT_JS.
    """
    custom_source = ColumnDataSource(
        data=dict(
            xs=[[1, 1, 1, 1]],
            ys=[[1, 1, 1, 1]],
            alpha=[0.0],
            line_alpha=[0.0],
        )
    )

    p.patches(
        "xs",
        "ys",
        source=custom_source,
        fill_color="#E8336D",
        fill_alpha="alpha",
        line_color="#E8336D",
        line_alpha="line_alpha",
        line_width=3,
    )

    custom_line_source = ColumnDataSource(
        data=dict(
            xs=[[]],
            ys=[[]],
            alpha=[0.0],
        )
    )

    p.multi_line("xs", "ys", source=custom_line_source, line_color="#E8336D", line_alpha="alpha", line_width=3)

    custom_point_source = ColumnDataSource(
        data=dict(
            x=[float("nan")],
            y=[float("nan")],
            alpha=[0.0],
        )
    )

    p.scatter(
        "x",
        "y",
        source=custom_point_source,
        marker="diamond",
        size=14,
        fill_color="#E8336D",
        fill_alpha="alpha",
        line_color="#E8336D",
        line_alpha="alpha",
        line_width=2,
    )

    custom_label_source = ColumnDataSource(
        data=dict(
            x=[1],
            y=[1],
            text=["Custom"],
            alpha=[0.0],
        )
    )

    p.text(
        "x",
        "y",
        source=custom_label_source,
        text="text",
        text_font_size="9pt",
        text_color="#E8336D",
        text_alpha="alpha",
        text_align="center",
        text_baseline="middle",
        text_font_style="bold",
    )

    return custom_source, custom_line_source, custom_point_source, custom_label_source
