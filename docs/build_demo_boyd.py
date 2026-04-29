"""Build a Boyd-orientation Stommel demo from the canonical Boyd (2015) CSV.

Boyd orientation: time on x-axis (bottom), space on y-axis. This is the
convention used in Boyd et al. (2015) and most oceanographic/biogeochemical
literature. The package default is the opposite orientation
(``space_on_x=True``); this script demonstrates how to pass
``space_on_x=False`` end-to-end.

The legend is moved to the right (default placement) so it sits outside the
plot area rather than covering data.

Run from repo root:
    python docs/build_demo_boyd.py

Produces:
    docs/demo_stommel_boyd.html
"""

import os

import pandas as pd
from bokeh.io import output_file, save

from timeSpace.etl import transform_predefined_processes
from timeSpace.plotting import (
    add_diffusion_lines,
    add_legend,
    add_magnitude_labels,
    add_predefined_processes,
    create_space_time_figure,
)

# Resolve paths relative to repo root regardless of where the script is run from
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
CSV_IN = os.path.join(REPO, "data", "datasets", "stommel_boyd2015_volumes.csv")
HTML_OUT = os.path.join(HERE, "demo_stommel_boyd.html")


def build():
    df_raw = pd.read_csv(CSV_IN)
    df = transform_predefined_processes(df_raw, space_on_x=False)

    p = create_space_time_figure(
        title="Boyd (2015) Stommel diagram — time on x, space on y",
        space_on_x=False,
    )
    add_magnitude_labels(p, space_on_x=False)
    add_diffusion_lines(p, space_on_x=False)
    add_predefined_processes(p, df, space_on_x=False)
    add_legend(p, position="right")

    output_file(HTML_OUT, title="timeSpace demo — Boyd orientation", mode="cdn")
    save(p)
    print(f"Built {HTML_OUT} ({os.path.getsize(HTML_OUT):,} bytes)")


if __name__ == "__main__":
    build()
