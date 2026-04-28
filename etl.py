from timeSpace.constants import base_space, base_time, POSSIBLE_COL_LIST
from timeSpace.calculations import create_ellipse_data, classify_process_geometry
from timeSpace.plotting_helpers import (
    create_name,
    set_fill_alpha,
    set_measurement_text_jitter,
)


def process_magnitude_column(row, column):
    """Parse a time/space column value and attach astropy units.

    Handles two input formats:
    - Colon-separated: "1.00E+01: ~10 seconds" → extracts "1.00E+01"
    - Plain numeric: 100.0 → used directly

    Parameters
    ----------
    row : Series
        DataFrame row.
    column : str
        Column name. Prefix "Time" → seconds, "Space" → cubic meters.

    Returns
    -------
    astropy Quantity
        Value with units (seconds or m³).
    """
    try:
        new_val = row[column].split(":").pop(0)
    except AttributeError:
        new_val = row[column]
    if column.startswith("Time"):
        return float(new_val) * base_time
    elif column.startswith("Space"):
        return float(new_val) * base_space


def transform_process_response_sheet(responses_df, possible_col_list=POSSIBLE_COL_LIST):
    """Clean and transform Google Form process responses for plotting.

    Applies unit conversion, filters invalid rows (min > max), generates
    ellipse polygon data, and computes display properties (alpha, name).

    Parameters
    ----------
    responses_df : DataFrame
        Raw Google Form responses with Time_min, Time_max, Space_min, Space_max.
    possible_col_list : list of str
        Column names to retain from the form response.

    Returns
    -------
    DataFrame
        With added columns: Name, FillAlpha, TextAlpha, geometry, x_coords, y_coords.
    """
    # Validate required columns
    required = {"Time_min", "Time_max", "Space_min", "Space_max"}
    missing = required - set(responses_df.columns)
    if missing:
        raise ValueError(
            f"DataFrame missing required columns: {missing}. "
            f"Expected: Time_min, Time_max, Space_min, Space_max. "
            f"If using predefined data, try transform_predefined_processes() instead."
        )

    columns_list = list(set(possible_col_list) & set(responses_df.columns))
    plottable_responses_df = responses_df[columns_list].copy()

    for column in ["Time_min", "Time_max", "Space_min", "Space_max"]:
        plottable_responses_df[column] = plottable_responses_df.apply(process_magnitude_column, column=column, axis=1)
    # Drop if min and max is wrong
    min_max_time_reverse = plottable_responses_df["Time_min"] > plottable_responses_df["Time_max"]
    min_max_space_reverse = plottable_responses_df["Space_min"] > plottable_responses_df["Space_max"]
    plottable_responses_df = plottable_responses_df[~(min_max_time_reverse | min_max_space_reverse)]
    plottable_responses_df["Name"] = plottable_responses_df.apply(create_name, axis=1)
    plottable_responses_df["FillAlpha"] = plottable_responses_df.apply(set_fill_alpha, axis=1)
    plottable_responses_df["TextAlpha"] = plottable_responses_df.apply(lambda row: min(1, 4 * row["FillAlpha"]), axis=1)
    plottable_responses_df["Time Max"] = plottable_responses_df.apply(lambda row: row["Time_max"].value, axis=1)
    plottable_responses_df["Space Min"] = plottable_responses_df.apply(lambda row: row["Space_min"].value, axis=1)
    plottable_responses_df["geometry"] = plottable_responses_df.apply(classify_process_geometry, axis=1)
    ellipse_mask = plottable_responses_df["geometry"] == "ellipse"
    if ellipse_mask.any():
        ellipse_coords = (
            plottable_responses_df.loc[ellipse_mask, ["Time_min", "Time_max", "Space_min", "Space_max"]]
            .apply(create_ellipse_data, axis=1, result_type="expand")
            .rename(columns={0: "x_coords", 1: "y_coords"})
        )
        plottable_responses_df.loc[ellipse_mask, ["x_coords", "y_coords"]] = ellipse_coords
    return plottable_responses_df


def transform_predefined_processes(plottable_responses_df, space_on_x=True):
    """Transform a predefined process CSV for plotting on a Stommel diagram.

    Normalizes column names (Process/EcologicalUnit/Model → Name), applies
    astropy units, classifies geometry, generates ellipse data, and
    computes display alpha values.

    Parameters
    ----------
    plottable_responses_df : DataFrame
        CSV data with Time_min, Time_max, Space_min, Space_max columns.
        Name column can be called Name, Process, EcologicalUnit, or Model.
        Legacy names emit a FutureWarning.

    Returns
    -------
    DataFrame
        With added columns: Name, geometry, x_coords, y_coords, FillAlpha, TextAlpha.
    """
    # Normalize name column — accept Name, Process, EcologicalUnit, or Model
    if "Name" not in plottable_responses_df.columns:
        for alt in ("Process", "EcologicalUnit", "Model"):
            if alt in plottable_responses_df.columns:
                plottable_responses_df = plottable_responses_df.rename(columns={alt: "Name"})
                break

    # Validate required columns
    required = {"Time_min", "Time_max", "Space_min", "Space_max"}
    missing = required - set(plottable_responses_df.columns)
    if missing:
        raise ValueError(
            f"DataFrame missing required columns: {missing}. " f"Expected: Time_min, Time_max, Space_min, Space_max."
        )

    for column in ["Time_min", "Time_max", "Space_min", "Space_max"]:
        plottable_responses_df[column] = plottable_responses_df.apply(process_magnitude_column, column=column, axis=1)

    # Validate values after unit conversion
    for column in ["Time_min", "Time_max", "Space_min", "Space_max"]:
        values = plottable_responses_df[column].apply(lambda q: q.value)
        bad = values <= 0
        if bad.any():
            bad_names = (
                plottable_responses_df.loc[bad, "Name"].tolist()
                if "Name" in plottable_responses_df.columns
                else bad.index[bad].tolist()
            )
            raise ValueError(
                f"Column '{column}' has zero or negative values for: {bad_names}. "
                f"All time and space values must be positive (log-log axes)."
            )
    plottable_responses_df["geometry"] = plottable_responses_df.apply(classify_process_geometry, axis=1)
    ellipse_mask = plottable_responses_df["geometry"] == "ellipse"
    if ellipse_mask.any():
        ellipse_coords = (
            plottable_responses_df.loc[ellipse_mask, ["Time_min", "Time_max", "Space_min", "Space_max"]]
            .apply(create_ellipse_data, axis=1, result_type="expand", space_on_x=space_on_x)
            .rename(columns={0: "x_coords", 1: "y_coords"})
        )
        plottable_responses_df.loc[ellipse_mask, ["x_coords", "y_coords"]] = ellipse_coords
    plottable_responses_df["FillAlpha"] = plottable_responses_df.apply(set_fill_alpha, axis=1)
    plottable_responses_df["TextAlpha"] = plottable_responses_df.apply(lambda row: min(1, 3 * row["FillAlpha"]), axis=1)
    return plottable_responses_df


def transform_measurement_sheet(sheet_df):
    """Transform measurement form responses for scatter plotting.

    Renames columns, applies units, extracts scalar values for Bokeh,
    and computes label jitter offsets for co-located points.

    Parameters
    ----------
    sheet_df : DataFrame
        Google Form measurement responses with Time Scale, Spatial Scale columns.

    Returns
    -------
    DataFrame
        With columns: Time_value, Space_value, Name, x_offset, y_offset, etc.
    """
    possible_col_list = [
        "Prefix",
        "ShortName",
        "Time Scale",
        "Spatial Scale",
        "Color",
        "Lab",
    ]
    columns_list = list(set(possible_col_list) & set(sheet_df.columns))
    plottable_responses_df = sheet_df[columns_list].rename(
        columns={
            "Time Scale": "Time",
            "Spatial Scale": "Space",
        }
    )
    for column in ["Time", "Space"]:
        plottable_responses_df[column] = plottable_responses_df.apply(process_magnitude_column, column=column, axis=1)
    plottable_responses_df["Name"] = plottable_responses_df.apply(create_name, axis=1)
    plottable_responses_df["Time_value"] = plottable_responses_df.apply(lambda row: row["Time"].value, axis=1)
    plottable_responses_df["Space_value"] = plottable_responses_df.apply(lambda row: row["Space"].value, axis=1)
    plottable_responses_df = set_measurement_text_jitter(plottable_responses_df)
    return plottable_responses_df
