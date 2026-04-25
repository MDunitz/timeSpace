from bokeh.models import ColumnDataSource, HoverTool, LabelSet


def add_measurements(p, measurements_df, grey=False):
    """Add measurement scatter points with linked labels to a Stommel figure.

    Each measurement appears as a circle at its (time, space) coordinate.
    Labels are linked to scatter visibility via js_link so toggling the
    legend entry hides both the point and its label.

    Parameters
    ----------
    p : figure
        Bokeh figure (Stommel layout).
    measurements_df : DataFrame
        From transform_measurement_sheet(). Needs: Time_value, Space_value,
        Color, Name, ShortName, Prefix, x_offset, y_offset.
    grey : bool
        If True, all points are grey with a HoverTool showing ShortName.
        If False, points use the Color column and labels show Name.

    Returns
    -------
    figure
    """
    source = ColumnDataSource(
        measurements_df[["Time_value", "Space_value", "Color", "Name", "ShortName", "Prefix", "x_offset", "y_offset"]]
    )
    if grey:
        scatter = p.scatter(
            source=source,
            x="Space_value",
            y="Time_value",
            size=20,
            fill_alpha=0.3,
            fill_color="Grey",
            legend_label="Measurements",
            visible=False,
        )
        labels = LabelSet(
            x="Space_value",
            y="Time_value",
            text="Prefix",
            name="Measurements",
            x_offset="x_offset",
            y_offset="y_offset",
            source=source,
            visible=False,
        )
        hover = HoverTool(tooltips="""
    <div>
        <span style="font-size: 18px;">@ShortName</span>
    </div>
""")
        hover.renderers = [scatter]
        p.add_tools(hover)
    else:
        scatter = p.scatter(
            source=source,
            x="Space_value",
            y="Time_value",
            size=20,
            fill_alpha=0.3,
            fill_color="Color",
            legend_label="Measurements",
            visible=False,
        )
        labels = LabelSet(
            x="Space_value",
            y="Time_value",
            text="Name",
            name="Measurements",
            x_offset="x_offset",
            y_offset="y_offset",
            source=source,
            visible=False,
            # level="glyph"
        )
    p.add_layout(labels)
    scatter.js_link("visible", labels, "visible")  # Link visibility for legend
    return p


def add_grouped_measurement(p, measurements_df, group="Prefix"):
    """Add measurement points grouped by a column, each group as a separate legend entry.

    Creates one scatter renderer and one LabelSet per group. Legend entries
    use ``legend_group`` so Bokeh auto-generates one entry per unique value.

    Parameters
    ----------
    p : figure
        Bokeh figure (Stommel layout).
    measurements_df : DataFrame
        From transform_measurement_sheet().
    group : str
        Column name to group by (default "Prefix").

    Returns
    -------
    figure
    """
    data_sources = []
    scatter_points = []
    for group_name, df in measurements_df.groupby(group):
        source = ColumnDataSource(
            df[["Time_value", "Space_value", "Color", "Name", group, "x_offset", "y_offset", "ShortName"]]
        )
        scatter = p.scatter(
            source=source,
            x="Space_value",
            y="Time_value",
            size=20,
            fill_alpha=0.3,
            fill_color="Color",
            legend_group=group,
            visible=False,
        )
        labels = LabelSet(
            x="Space_value",
            y="Time_value",
            text=group_name,
            x_offset="x_offset",
            y_offset="y_offset",
            text_font_size="12pt",
            source=source,
            visible=False,
            # level="annotation"
        )
        p.add_layout(labels)
        scatter.js_link("visible", labels, "visible")  # Link visibility for legend
        data_sources.append(source)
        scatter_points.append(scatter)
    return p
