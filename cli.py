"""Command-line interface for generating Stommel diagrams.

Thin wrapper over the package pipeline:
    extract_google_sheet / read_csv
      -> transform_process_response_sheet
      -> create_space_time_figure + add_processes
      -> self-contained HTML

Two input modes:

--form (interactive-activity mode)
    Raw Google Form response sheets, headers as form question titles
    ("Minimum Time Scale", etc). Copy the template form, share the response
    sheet publicly, pass its ID. Colors are assigned per Lab automatically.

default (curated-dataset mode)
    Data already conforming to the ETL contract: a name column (Name,
    Process, EcologicalUnit, or Model), Time_min, Time_max, Space_min,
    Space_max, and a non-null Color.

Usage
-----
    timespace --csv data.csv --output stommel.html
    timespace --sheet-id 1abc123 --output stommel.html
    timespace --sheet-id 1abc123 --form --sheet-gid 243872990 -o activity.html
    timespace --csv data.csv --output out.html --time-on-x --open
"""

import argparse
import sys
import webbrowser
from pathlib import Path

import pandas as pd
from bokeh.embed import file_html
from bokeh.resources import CDN

from timeSpace.data_processing import extract_google_sheet
from timeSpace.etl import (
    transform_predefined_processes,
    transform_process_response_sheet,
    normalize_form_responses,
)
from timeSpace.plotting import (
    create_space_time_figure,
    add_predefined_processes,
    add_processes,
    add_magnitude_labels,
)
from timeSpace.plotting_helpers import set_color_palettes_by_lab

DEFAULT_N_POINTS = 1000


def load_dataframe(csv=None, sheet_id=None, sheet_gid=0, data_name="cli_input"):
    """Return a raw DataFrame from a local CSV or a Google Sheet ID.

    Exactly one of ``csv`` / ``sheet_id`` is expected to be set.
    """
    if csv is not None:
        return pd.read_csv(csv)
    return extract_google_sheet(sheet_id, data_name, from_cache=False, sheet_id=sheet_gid)


def build_figure(raw_df, space_on_x=True, n_points=DEFAULT_N_POINTS, title=" ", interactive=True):
    """Run the ETL + plotting pipeline and return a Bokeh figure.

    interactive : when True, processes start hidden and are toggled via the
      click-to-hide legend (Bokeh default legend behaviour).
    """
    transformed = transform_predefined_processes(raw_df, space_on_x=space_on_x, warn_on_lengths=False)
    p = create_space_time_figure(space_on_x=space_on_x, title=title)
    add_predefined_processes(p, transformed, interactive=interactive, space_on_x=space_on_x)
    return p


def build_form_figure(raw_df, space_on_x=True, n_points=DEFAULT_N_POINTS, title=" ", interactive=True):
    """Build a figure from a raw Google Form process-response sheet.

    The interactive-activity path: normalize question titles -> transform ->
    assign one color ramp per Lab -> plot. Unlike build_figure this accepts
    the sheet exactly as the form emits it, so a copied form needs no manual
    column editing before it renders.

    Rows whose min exceeds max are dropped by transform_process_response_sheet
    (participants sometimes invert the two dropdowns).
    """
    normalized = normalize_form_responses(raw_df)
    transformed = transform_process_response_sheet(normalized, space_on_x=space_on_x, n_points=n_points)
    transformed = set_color_palettes_by_lab(transformed)
    p = create_space_time_figure(space_on_x=space_on_x, title=title)
    add_magnitude_labels(p, space_on_x=space_on_x)
    add_processes(p, transformed, interactive=interactive, space_on_x=space_on_x)
    return p


def write_html(figure, output_path, title="Stommel diagram"):
    """Write a self-contained HTML file and return its Path."""
    output = Path(output_path)
    output.write_text(file_html(figure, CDN, title))
    return output


def parse_args(argv):
    parser = argparse.ArgumentParser(
        prog="timespace",
        description="Generate a Stommel time-space diagram from a Google Sheet or CSV.",
    )
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--csv", help="Path to a local CSV in the ETL schema.")
    src.add_argument("--sheet-id", help="Google Sheet ID (the part between /d/ and /edit).")
    parser.add_argument("--sheet-gid", type=int, default=0, help="Sheet GID for multi-tab workbooks (default 0).")
    parser.add_argument(
        "--form",
        action="store_true",
        help="Input is a raw Google Form response sheet (question-title headers); colors assigned per Lab.",
    )
    parser.add_argument("--output", "-o", default="stommel.html", help="Output HTML path (default stommel.html).")
    parser.add_argument("--title", default=" ", help="Figure title.")
    parser.add_argument(
        "--time-on-x",
        action="store_true",
        help="Put time on the x-axis (default: space on x, time reversed on y).",
    )
    parser.add_argument(
        "--static",
        dest="interactive",
        action="store_false",
        help="Render all processes visible (default: interactive click-to-hide legend).",
    )
    parser.add_argument("--n-points", type=int, default=DEFAULT_N_POINTS, help="Ellipse resolution (default 1000).")
    parser.add_argument("--open", action="store_true", help="Open the output in a browser when done.")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(sys.argv[1:] if argv is None else argv)
    raw_df = load_dataframe(csv=args.csv, sheet_id=args.sheet_id, sheet_gid=args.sheet_gid)
    builder = build_form_figure if args.form else build_figure
    figure = builder(
        raw_df,
        space_on_x=not args.time_on_x,
        n_points=args.n_points,
        title=args.title,
        interactive=args.interactive,
    )
    output = write_html(figure, args.output, title=args.title.strip() or "Stommel diagram")
    print(f"Wrote {output.resolve()}")
    if args.open:
        webbrowser.open(output.resolve().as_uri())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
