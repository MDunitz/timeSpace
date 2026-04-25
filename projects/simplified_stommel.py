"""
Simplified Stommel-style diagram project.

Creates a time-space plot with:
- X-axis (top): Space (m³) - volume
- Y-axis: Time (s) - from 10^12 at bottom to 10^-3 at top (reversed)
- Labels positioned at the axes
- Ellipse patches with labels (similar to oceanographic Stommel diagrams)

Based on Boyd et al. (2015), adapted from Dickey (2003).
"""

import os
from bokeh.plotting import output_file, save, show
from bokeh.io import export_png
from time import time
import pandas as pd

from timeSpace.plotting import (
    create_space_time_figure,
    add_magnitude_labels,
    add_predefined_processes,
    add_legend,
)
from timeSpace.etl import transform_process_response_sheet
from timeSpace.plotting_helpers import set_color_by_prefix

# Get paths relative to this script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)  # timeSpace directory


def transform_data(config_data):
    """Load and transform data for Stommel-style plotting."""
    data_path = os.path.join(PROJECT_ROOT, "data/datasets/stommel_boyd2015.csv")
    data = pd.read_csv(data_path)
    data.dropna(subset=["Time_min", "Time_max", "Space_min", "Space_max"], inplace=True)
    data.rename(columns={config_data["concept_name"]: "ShortName"}, inplace=True)
    data["Prefix"] = data.apply(lambda x: x["ShortName"][0:3], axis=1)

    columns = ["Prefix", "ShortName", "Time_min", "Time_max", "Space_min", "Space_max", "Color"]
    # Top-level ETL now defaults to is_boyd=True orientation (x=space, y=time)
    transformed_data = transform_process_response_sheet(data, possible_col_list=columns)
    transformed_data = set_color_by_prefix(transformed_data)

    return transformed_data


def make_simplified_plot(transformed_data, title="Stommel Diagram"):
    """Create a simplified Stommel-style plot with legend for show/hide."""
    p = create_space_time_figure(title=title)
    p = add_magnitude_labels(p)
    p = add_predefined_processes(p, transformed_data)
    p = add_legend(p)

    return p


if __name__ == "__main__":
    config_data = {
        "title": "Oceanographic Time-Space Scales (Boyd et al. 2015)",
        "output_file": "stommel-boyd2015",
        "concept_name": "Process",
    }

    transformed_data = transform_data(config_data)
    p = make_simplified_plot(transformed_data, title=config_data["title"])

    file_name = f"{int(time())}-{config_data['output_file']}"
    output_path = os.path.join(PROJECT_ROOT, "saved_plots", f"{file_name}.html")
    output_file(output_path, mode="inline")
    save(p)
    show(p)
