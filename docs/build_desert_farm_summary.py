"""
Build the desert farm leverage points summary diagram.

Uses the timeSpace package API for all rendering. Only custom code is
the cascade arrows connecting leverage points and the HTML template.

Stommel convention: x=space (m³), y=time (s), reversed y-axis.
"""

import numpy as np
import pandas as pd
from pathlib import Path
from bokeh.models import Arrow, VeeHead
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
    - create_ellipse_data (Stommel axis order)
    - set_fill_alpha (area-based transparency)
    """
    df = pd.read_csv(csv_path)
    process_df = transform_process_response_sheet(df)
    process_df["x_offset"] = 0
    process_df["y_offset"] = 0
    return process_df


def add_cascade_arrows(p, process_df):
    """Draw dashed arrows connecting leverage points in time order.

    Stommel convention: x=space, y=time.
    """
    lp = process_df[process_df.Prefix == "leverage point"].copy()
    if len(lp) < 2:
        return

    lp["center_space"] = np.sqrt(lp.Space_min.apply(lambda q: q.value) * lp.Space_max.apply(lambda q: q.value))
    lp["center_time"] = np.sqrt(lp.Time_min.apply(lambda q: q.value) * lp.Time_max.apply(lambda q: q.value))
    lp = lp.sort_values("center_time")

    centers = list(zip(lp.center_space, lp.center_time))
    for i in range(len(centers) - 1):
        x0, y0 = centers[i]
        x1, y1 = centers[i + 1]
        p.add_layout(
            Arrow(
                end=VeeHead(size=8, fill_color="#CC6600", line_color="#CC6600"),
                x_start=x0,
                y_start=y0,
                x_end=x1,
                y_end=y1,
                line_color="#CC6600",
                line_width=1.5,
                line_dash="dashed",
                line_alpha=0.5,
            )
        )


def build_summary_figure(csv_path=None, output_path=None):
    csv_path = csv_path or DEFAULT_CSV
    output_path = output_path or Path(__file__).resolve().parent / "desert_farm_summary.html"

    process_df = load_and_transform(csv_path)

    p = create_space_time_figure(
        width=950,
        height=700,
        title="Desert Algae Carbon Capture — Leverage Points",
    )
    p.title.text_font_size = "16pt"
    p.title.text_font_style = "bold"

    add_magnitude_labels(p, font_size="10pt")
    add_diffusion_lines(p)
    add_processes(
        p,
        process_df,
        group="Prefix",
        interactive=False,
        font_size="8pt",
    )
    add_cascade_arrows(p, process_df)
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
