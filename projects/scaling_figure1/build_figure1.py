"""Build scaling paper Figure 1: a time-on-x Stommel diagram with process icons.

Self-contained: the dataset and icons live alongside this script. Run directly
(``python build_figure1.py``) to write ``scaling_figure1.html`` next to it.

Orientation is time-on-x / space-on-y with the time axis on the bottom, so
``space_on_x=False`` is threaded through every call (transform, figure, labels,
processes, icons) — the transform bakes ellipse coordinates in this order and it
must match the plotting calls.
"""

from pathlib import Path

import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import Range1d

from timeSpace.etl import transform_process_response_sheet
from timeSpace.plotting import add_legend, add_magnitude_labels, add_processes, create_space_time_figure
from timeSpace.icons import add_icons

HERE = Path(__file__).parent
DATASET = HERE / "scalingPaperFigure1Dataset.csv"
ICON_DIR = HERE / "icons"

SPACE_ON_X = False
YEAR_S = 3.156e7  # 1 Julian year in seconds

CATEGORY_COLORS = {"microscale experiments": "#E4A6A6", "large-scale models": "#A9B0B5"}

# Columns consumed from the CSV (icon + label placement carried through the transform).
DATA_COLUMNS = [
    "ShortName",
    "Time_min",
    "Time_max",
    "Space_min",
    "Space_max",
    "Color",
    "ProcessType",
    "icon",
    "label_side",
    "x_offset",
    "y_offset",
    "label_text",
    "start_visible",
]

# Reference time markers for this figure: {value in seconds: label}. Positions are
# round timescales, not the package defaults; kept 2 decades apart so labels do not
# collide at this axis scale.
TIME_MARKERS = {
    2.42e-17: "Electron movement",
    1.8e-15: "Period of wave \nof visible light",
    1.0: "Second",
    86400.0: "Day",
    1 * YEAR_S: "Year",
    100 * YEAR_S: "Century",
    1e4 * YEAR_S: "10,000 \nyears",
    1e6 * YEAR_S: "1 million \nyears",
    1e9 * YEAR_S: "1 billion \nyears",
}

# Time axis spans seconds to ~1 Gyr so decadal detail and geological markers coexist
# (log scale keeps the microbial region legible while the geological markers show).
TIME_RANGE = (1e-3, 3e16)


def load_processes(path=DATASET, space_on_x=SPACE_ON_X):
    """Load and transform the figure's process table into plottable form."""
    raw = pd.read_csv(path, keep_default_na=False)
    return transform_process_response_sheet(raw, possible_col_list=DATA_COLUMNS, space_on_x=space_on_x)


def build_figure(process_df, time_range=TIME_RANGE, size_px=48, space_on_x=SPACE_ON_X):
    """Assemble the Bokeh figure: axes, reference labels, process ellipses, icons, legend."""
    p = create_space_time_figure(
        width=1600,
        height=900,
        title="Scaling paper Figure 1",
        space_on_x=space_on_x,
        x_axis_location="below",
    )
    p.x_range = Range1d(*time_range)
    add_magnitude_labels(p, space_on_x=space_on_x, time_markers=TIME_MARKERS)
    add_processes(
        p,
        process_df,
        group="ProcessType",
        interactive=False,
        space_on_x=space_on_x,
        category_col="ProcessType",
        category_colors=CATEGORY_COLORS,
    )
    add_icons(p, process_df, ICON_DIR, size_px=size_px, space_on_x=space_on_x)
    add_legend(p)
    return p


def main(out_path=HERE / "scaling_figure1.html"):
    """Build the figure and write a standalone HTML file next to this script."""
    p = build_figure(load_processes())
    output_file(str(out_path))
    save(p)
    return out_path


if __name__ == "__main__":
    print("wrote", main())
