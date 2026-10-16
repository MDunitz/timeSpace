"""
Build the desert farm leverage points summary diagram.

Uses the timeSpace package API for all rendering.

Boyd convention: x=time (s), y=space (m³). x-axis labels at top via
create_space_time_figure().
"""

import pandas as pd
from pathlib import Path
from bokeh.resources import CDN
from bokeh.embed import components

from timeSpace.etl import transform_process_response_sheet
from timeSpace.plotting import (
    create_space_time_figure,
    add_magnitude_labels,
    add_diffusion_lines,
    add_processes,
    add_legend,
)

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "datasets"
DEFAULT_CSV = DATA_DIR / "desert_farm_leverage_points.csv"

# Half a decade of margin beyond the data extent on each side; every row
# in the CSV (MD models at 1e-30 m3, fossil-fuel formation at 3e15 s) stays
# inside the fixed view.
X_RANGE = (1e-16, 1e18)
Y_RANGE = (1e-31, 1e15)

# Per-row label overrides: ShortName -> (label text, x px, y px, side).
# Offsets are Bokeh screen pixels (positive y is down); "\n" splits lines;
# side is "left", "right", "above" or "below" (None keeps the default).
FONT_SCALE = 1.3  # all text sizes relative to the package defaults used before 2026-10-16


def pt(base):
    """Scale a base point size by FONT_SCALE and format for Bokeh."""
    return f"{base * FONT_SCALE:g}pt"


LABEL_OVERRIDES = {
    "Biogeochemical Circulation Models": (
        "Biogeochemical\nCirculation Models",
        0,
        round(-14 * FONT_SCALE),
        None,
    ),
    "Nutrient transport": (None, 0, round(8 * FONT_SCALE), None),
    "Photoautotroph cell growth": (None, 0, round(10 * FONT_SCALE), None),
    "Fossil-fuel formation": ("Fossil-fuel\nformation", 45, round(14 * FONT_SCALE), "below"),
}


def load_and_transform(csv_path):
    """Load CSV and run the standard ETL pipeline.

    Uses etl.transform_process_response_sheet which applies:
    - process_magnitude_column (astropy units)
    - classify_process_geometry (ellipse/vline/hline/point)
    - create_ellipse_data (Boyd order: x=time, y=space)
    - set_fill_alpha (area-based transparency)
    """
    df = pd.read_csv(csv_path)
    process_df = transform_process_response_sheet(df, space_on_x=False)
    process_df["label_text"] = process_df["ShortName"]
    process_df["x_offset"] = 0
    process_df["y_offset"] = 0
    process_df["label_side"] = ""
    for short_name, (text, xo, yo, side) in LABEL_OVERRIDES.items():
        mask = process_df["ShortName"] == short_name
        if text is not None:
            process_df.loc[mask, "label_text"] = text
        if side is not None:
            process_df.loc[mask, "label_side"] = side
        process_df.loc[mask, "x_offset"] = xo
        process_df.loc[mask, "y_offset"] = yo
    return process_df


def build_summary_figure(csv_path=None, output_path=None):
    csv_path = csv_path or DEFAULT_CSV
    output_path = output_path or Path(__file__).resolve().parent / "desert_farm_summary.html"

    process_df = load_and_transform(csv_path)

    p = create_space_time_figure(
        width=1400,
        height=760,
        title="Desert Algae Carbon Capture — Leverage Points",
        space_on_x=False,
    )
    p.sizing_mode = "stretch_width"
    p.x_range.start, p.x_range.end = X_RANGE
    p.y_range.start, p.y_range.end = Y_RANGE
    p.title.text_font_size = pt(16)
    p.title.text_font_style = "bold"
    p.axis.axis_label_text_font_size = pt(24)
    p.axis.major_label_text_font_size = pt(12)

    add_magnitude_labels(p, font_size=pt(10), space_on_x=False)
    add_diffusion_lines(p, space_on_x=False)
    add_processes(
        p,
        process_df,
        group="Prefix",
        interactive=False,
        font_size=pt(8),
        space_on_x=False,
    )
    add_legend(p, font_size=pt(12))

    script, div = components(p)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>Desert Algae Carbon Capture — Leverage Points</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    {CDN.render()}
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            margin: 0; padding: 16px; background: #fff;
        }}
        .header {{ max-width: 1420px; margin: 0 auto 12px auto; }}
        .header h2 {{ margin: 0 0 6px 0; font-size: 20px; color: #333; }}
        .header p {{ margin: 0 0 4px 0; font-size: 13px; color: #666; line-height: 1.5; }}
        .footer {{ max-width: 1420px; margin: 12px auto 0 auto; font-size: 12px; color: #888; }}
        .footer a {{ color: #006666; }}
    </style>
</head>
<body>
    <div class="header">
        <h2>From Molecule to Atmosphere: Leverage Points</h2>
        <p>Desert algae carbon capture spans 30 orders of magnitude in space
           and 26 in time. Teal ellipses are physical/biological processes,
           orange ellipses are engineering leverage points, and dark teal
           outlines show model domains at each scale.
           Click the legend to toggle individual items. Hover for details.</p>
    </div>
    {div}
    {script}
    <div class="footer">
        <p>Built with <a href="https://github.com/MDunitz/timeSpace">timeSpace</a>.
           Explore the full 23-process diagram:
           <a href="desert_farm_stommel.html">Desert Farm &mdash; Processes Across Scale</a>.</p>
    </div>
</body>
</html>"""

    Path(output_path).write_text(html)
    print(f"Built {output_path} ({len(html):,} bytes)")


if __name__ == "__main__":
    import sys

    csv_path = sys.argv[1] if len(sys.argv) > 1 else None
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    build_summary_figure(csv_path, output_path)
