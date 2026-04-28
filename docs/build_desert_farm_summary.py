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
    process_df["x_offset"] = 0
    process_df["y_offset"] = 0
    return process_df


def build_summary_figure(csv_path=None, output_path=None):
    csv_path = csv_path or DEFAULT_CSV
    output_path = output_path or Path(__file__).resolve().parent / "desert_farm_summary.html"

    process_df = load_and_transform(csv_path)

    p = create_space_time_figure(
        width=950,
        height=700,
        title="Desert Algae Carbon Capture — Leverage Points",
        space_on_x=False,
    )
    p.title.text_font_size = "16pt"
    p.title.text_font_style = "bold"

    add_magnitude_labels(p, font_size="10pt", space_on_x=False)
    add_diffusion_lines(p, space_on_x=False)
    add_processes(
        p,
        process_df,
        group="Prefix",
        interactive=False,
        font_size="8pt",
        space_on_x=False,
    )
    add_legend(p)

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
        .header {{ max-width: 970px; margin: 0 auto 12px auto; }}
        .header h2 {{ margin: 0 0 6px 0; font-size: 20px; color: #333; }}
        .header p {{ margin: 0 0 4px 0; font-size: 13px; color: #666; line-height: 1.5; }}
        .footer {{ max-width: 970px; margin: 12px auto 0 auto; font-size: 12px; color: #888; }}
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
           Explore the full 24-process diagram:
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
