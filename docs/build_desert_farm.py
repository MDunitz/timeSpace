"""
Build a static Bokeh HTML figure for the desert farm blog post.

Shows all processes across 6 scales (Molecular → Global), colored by
dominant energy type (Chemical / Radiative / Thermal / Mechanical).
Designed for embedding on Google Sites via iframe.
"""

import pandas as pd
import numpy as np
from bokeh.models import (
    BoxZoomTool,
    ColumnDataSource,
    HoverTool,
    Legend,
    LegendItem,
    PanTool,
    ResetTool,
    WheelZoomTool,
)
from bokeh.resources import CDN
from bokeh.embed import components

from timeSpace.etl import transform_process_response_sheet, POSSIBLE_COL_LIST
from timeSpace.plotting import create_space_time_figure, add_magnitude_labels

# ── Configuration ──────────────────────────────────────────────────
X_RANGE = (1e-3, 1e13)
Y_RANGE = (1e-28, 1e22)

EXPLORER_N_POINTS = 100

ENERGY_COLORS = {
    "Chemical": "#7A8C5C",  # olive — bonds, reactions, metabolism
    "Radiative": "#E5C16E",  # warm sand — photons, solar
    "Thermal": "#7B3F3F",  # deep rust — heat, evaporation, climate
    "Mechanical": "#4F6B82",  # slate — kinetic, mixing, pumping
}

ENERGY_ORDER = ["Chemical", "Radiative", "Thermal", "Mechanical"]

FONT_SIZE = "11pt"
LABEL_FONT_SIZE = "9pt"

COLAB_URL = "https://colab.research.google.com/github/MDunitz/timeSpace/blob/main/docs/desert_farm_colab.ipynb"


# ── Data loading ───────────────────────────────────────────────────


def load_processes(csv_path):
    """Read desert farm process CSV and run the ETL pipeline.

    Pre-ETL: derive Color from Energy_type and rename Name → FullName so
    create_name's ShortName fallback doesn't overwrite the original name.
    The hover tooltip uses FullName; the legend groups by Energy_type.
    """
    df = pd.read_csv(csv_path)
    df = df.rename(columns={"Name": "FullName"})
    df["Color"] = df.Energy_type.map(ENERGY_COLORS)

    return transform_process_response_sheet(
        df,
        possible_col_list=POSSIBLE_COL_LIST + ["FullName", "Scale", "Energy_type"],
        space_on_x=False,
        n_points=EXPLORER_N_POINTS,
    )


# ── Build ──────────────────────────────────────────────────────────


def build_desert_farm_figure(csv_path, output_path):
    df = load_processes(csv_path)

    p = create_space_time_figure(
        width=900,
        height=650,
        title="Desert Farm — Processes Across Scale",
        space_on_x=False,
    )
    p.x_range.start, p.x_range.end = X_RANGE
    p.y_range.start, p.y_range.end = Y_RANGE
    p.title.text_font_size = "16pt"
    p.title.text_font_style = "bold"
    p.axis.axis_label_text_font_size = FONT_SIZE
    p.axis.major_label_text_font_size = "10pt"
    p.background_fill_color = "#fafafa"
    p.toolbar_location = "above"
    p.toolbar.tools = [PanTool(), WheelZoomTool(), BoxZoomTool(), ResetTool()]

    add_magnitude_labels(p, font_size=LABEL_FONT_SIZE, space_on_x=False)

    legend_items = []

    def _hover_display(val_min, val_max, unit):
        """Format axis display: exact value when degenerate, range otherwise."""
        if abs(np.log10(val_max) - np.log10(val_min)) < 1e-10:
            return f"{val_min:.1e} {unit}"
        return f"{val_min:.1e} → {val_max:.1e} {unit}"

    for etype in ENERGY_ORDER:
        edf = df[df.Energy_type == etype]
        if edf.empty:
            continue
        color = ENERGY_COLORS[etype]
        renderers = []

        # ── Ellipse processes (batched patches) ──
        ell = edf[edf.geometry == "ellipse"]
        if not ell.empty:
            source = ColumnDataSource(
                data=dict(
                    xs=[row.x_coords.tolist() for _, row in ell.iterrows()],
                    ys=[row.y_coords.tolist() for _, row in ell.iterrows()],
                    alpha=ell.FillAlpha.tolist(),
                    name=ell.FullName.tolist(),
                    short_name=ell.ShortName.tolist(),
                    scale=ell.Scale.tolist(),
                    energy_type=ell.Energy_type.tolist(),
                    time_display=[_hover_display(r.Time_min.value, r.Time_max.value, "s") for _, r in ell.iterrows()],
                    space_display=[
                        _hover_display(r.Space_min.value, r.Space_max.value, "m³") for _, r in ell.iterrows()
                    ],
                    label_x=[row.Time_max.value for _, row in ell.iterrows()],
                    label_y=ell.label_y.tolist(),
                )
            )

            patch_r = p.patches(
                "xs",
                "ys",
                source=source,
                fill_color=color,
                fill_alpha="alpha",
                line_color=color,
                line_alpha=0.8,
                line_width=1.5,
            )
            text_r = p.text(
                "label_x",
                "label_y",
                source=source,
                text="short_name",
                text_font_size="7pt",
                text_color=color,
                text_alpha=0.9,
                text_align="left",
                text_baseline="middle",
                x_offset=5,
            )
            renderers.extend([patch_r, text_r])

            hover = HoverTool(
                renderers=[patch_r],
                tooltips=[
                    ("Name", "@name"),
                    ("Scale", "@scale"),
                    ("Energy", "@energy_type"),
                    ("Time", "@time_display"),
                    ("Space", "@space_display"),
                ],
            )
            p.add_tools(hover)

        # ── Line / point processes (individual glyphs) ──
        non_ell = edf[edf.geometry != "ellipse"]
        for _, row in non_ell.iterrows():
            geom = row.geometry
            if geom == "vline":
                t_val = row.Time_min.value
                r = p.line(
                    [t_val, t_val],
                    [row.Space_min.value, row.Space_max.value],
                    line_color=color,
                    line_width=2.5,
                    line_alpha=0.8,
                )
            elif geom == "hline":
                s_val = row.Space_min.value
                r = p.line(
                    [row.Time_min.value, row.Time_max.value],
                    [s_val, s_val],
                    line_color=color,
                    line_width=2.5,
                    line_alpha=0.8,
                )
            elif geom == "point":
                r = p.scatter(
                    [row.Time_min.value],
                    [row.Space_min.value],
                    marker="diamond",
                    size=12,
                    fill_color=color,
                    fill_alpha=0.6,
                    line_color=color,
                    line_width=1.5,
                )
            else:
                continue

            renderers.append(r)

            lx = row.Time_min.value if geom == "point" else row.label_x
            ly = row.Space_max.value if geom == "vline" else row.label_y
            tr = p.text(
                x=lx,
                y=ly,
                text=[row.ShortName],
                text_font_size="7pt",
                text_color=color,
                text_alpha=0.9,
                text_align="left",
                text_baseline="middle",
                x_offset=5,
            )
            renderers.append(tr)

        if renderers:
            legend_items.append(LegendItem(label=etype, renderers=renderers))

    # Compact legend — one row per energy type, click to hide
    legend = Legend(
        items=legend_items,
        location="top_left",
        label_text_font_size="10pt",
        click_policy="hide",
        title="Dominant Energy",
        title_text_font_size="11pt",
        title_text_font_style="bold",
    )
    p.add_layout(legend, "right")

    # ── Render HTML ────────────────────────────────────────────────
    script, div = components(p)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>Desert Farm — Stommel Diagram</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    {CDN.render()}
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            margin: 0;
            padding: 16px;
            background: #fff;
        }}
        .header {{
            max-width: 920px;
            margin: 0 auto 12px auto;
        }}
        .header h2 {{
            margin: 0 0 6px 0;
            font-size: 20px;
            color: #333;
        }}
        .header p {{
            margin: 0 0 4px 0;
            font-size: 13px;
            color: #666;
            line-height: 1.5;
        }}
        .footer {{
            max-width: 920px;
            margin: 12px auto 0 auto;
            font-size: 12px;
            color: #888;
        }}
        .footer a {{
            color: #7A8C5C;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h2>Operating Across Scale: From Molecules to Climate</h2>
        <p>Every process that matters to a desert algae farm, plotted on a
           Stommel diagram. The x-axis is time (seconds to millennia), the
           y-axis is the volume of space involved (cubic angstroms to the
           atmosphere). Color indicates the dominant energy type:
           chemical (green), radiative (gold), thermal (red), mechanical (blue).
           Click the legend to toggle energy types on/off.</p>
    </div>
    {div}
    {script}
    <div class="footer">
        <p>Built with <a href="https://github.com/MDunitz/timeSpace">timeSpace</a>.
           Want to add your own processes?
           <a href="{COLAB_URL}">Open the interactive notebook</a>.</p>
    </div>
</body>
</html>"""

    with open(output_path, "w") as f:
        f.write(html)
    print(f"Built {output_path} ({len(html):,} bytes)")


if __name__ == "__main__":
    import sys
    from pathlib import Path

    HERE = Path(__file__).resolve().parent
    csv_path = sys.argv[1] if len(sys.argv) > 1 else HERE / "desert_farm_processes.csv"
    output_path = sys.argv[2] if len(sys.argv) > 2 else HERE / "desert_farm_stommel.html"
    build_desert_farm_figure(csv_path, output_path)
