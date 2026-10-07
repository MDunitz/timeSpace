"""Pre-ETL adapter: reference-objects CSV -> package ETL pipeline."""

import numpy as np
import pandas as pd

from timeSpace.etl import transform_process_response_sheet, POSSIBLE_COL_LIST

from .config import CATEGORY_COLORS, EXPLORER_N_POINTS, RANGE_PAD_DECADES, UNSOURCED_LABEL
from .units import format_time_range, format_volume_range


def load_reference_objects(csv_path):
    """Read reference objects CSV and run the package ETL pipeline.

    Pre-ETL adapter: the reference-objects CSV uses a different schema
    from a Google Form response sheet, so we adapt before delegating to
    transform_process_response_sheet:
      - Rename Name → FullName so create_name's ShortName fallback inside
        the ETL doesn't overwrite the descriptive name we want for hover
        tooltips and labels.
      - Map Category → Color (uppercase to match POSSIBLE_COL_LIST).
      - Set ShortName = FullName since reference objects don't have
        separate short forms; create_name needs ShortName to exist.
      - Carry Reference through for the hover tooltip, labelling rows
        that have none.

    transform_process_response_sheet handles unit conversion, geometry
    classification, ellipse polygon generation, label_x/label_y, and
    filters out rows where Time_min > Time_max or Space_min > Space_max.
    """
    df = pd.read_csv(csv_path)
    df = df.rename(columns={"Name": "FullName"})
    df["Color"] = df.Category.map(CATEGORY_COLORS)
    df["ShortName"] = df.FullName
    df["Reference"] = df.Reference.fillna(UNSOURCED_LABEL)

    df = transform_process_response_sheet(
        df,
        possible_col_list=POSSIBLE_COL_LIST + ["FullName", "Category", "Reference"],
        space_on_x=False,
        n_points=EXPLORER_N_POINTS,
    )
    df["TimeLabel"] = [format_time_range(r.Time_min, r.Time_max) for _, r in df.iterrows()]
    df["SpaceLabel"] = [format_volume_range(r.Space_min, r.Space_max) for _, r in df.iterrows()]
    return df


def padded_decade_range(q_min, q_max, pad=RANGE_PAD_DECADES):
    """Axis range covering [min, max], snapped out to whole decades plus `pad`."""
    lo = np.floor(np.log10(min(q.value for q in q_min))) - pad
    hi = np.ceil(np.log10(max(q.value for q in q_max))) + pad
    return (10.0**lo, 10.0**hi)


def data_ranges(df):
    """(x_range, y_range) that keep every object in view: time on x, space on y."""
    return (
        padded_decade_range(df.Time_min, df.Time_max),
        padded_decade_range(df.Space_min, df.Space_max),
    )
