"""Pre-ETL adapter: reference-objects CSV -> package ETL pipeline."""

import pandas as pd

from timeSpace.etl import transform_process_response_sheet, POSSIBLE_COL_LIST

from .config import CATEGORY_COLORS, EXPLORER_N_POINTS, UNSOURCED_LABEL


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

    return transform_process_response_sheet(
        df,
        possible_col_list=POSSIBLE_COL_LIST + ["FullName", "Category", "Reference"],
        space_on_x=False,
        n_points=EXPLORER_N_POINTS,
    )
