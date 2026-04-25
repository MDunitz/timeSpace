import warnings

import colorcet as cc
import numpy as np
import pandas as pd
from timeSpace.constants import OFFSETS, colors
from timeSpace.label_collision import (
    data_to_pixel,
    estimate_label_bbox,
    _boxes_overlap,
    repulsion_step,
)


def set_prefix_color(row, prefix_list, palette=colors):
    """Assign a color to a row based on its Prefix position in a list.

    Parameters
    ----------
    row : Series
        Must have a 'Prefix' column.
    prefix_list : list of str
        Ordered unique prefixes.
    palette : list
        Color palette to sample from.

    Returns
    -------
    str
        Hex color string.
    """
    prefix_id = prefix_list.index(row["Prefix"])
    offset = len(palette) / len(prefix_list)
    color_id = int(offset * prefix_id)
    return palette[color_id]


def set_color_by_prefix(df, palette=colors):
    """Add a Color column to a DataFrame, one color per unique Prefix.

    Parameters
    ----------
    df : DataFrame
        Must have a 'Prefix' column.
    palette : list
        Color palette.

    Returns
    -------
    DataFrame
        With added 'Color' column.
    """
    df["Prefix"] = df["Prefix"].fillna("Blank")
    prefix_list = df["Prefix"].unique().tolist()
    df["Color"] = df.apply(lambda x: set_prefix_color(x, prefix_list, palette=palette), axis=1)
    return df


def set_color_by_lab(row, palette, lab_list):
    """Assign a color to a row based on Lab and within-lab ordering.

    Parameters
    ----------
    row : Series
        Must have 'Lab' and 'lab_order' columns.
    palette : list
        Color palette (256+ entries recommended).
    lab_list : list of str
        Ordered unique lab names.

    Returns
    -------
    str
        Hex color string.
    """
    lab_id = lab_list.index(row["Lab"])
    order_id = row["lab_order"]
    offset = 256 / len(lab_list)
    color_id = int(lab_id * offset + order_id)
    return palette[color_id]


def set_color_palettes_by_lab(df, palette=cc.CET_R4):
    """Add a Color column grouped by Lab, with distinct colors within each lab.

    Parameters
    ----------
    df : DataFrame
        Must have 'Lab' and 'Prefix' columns.
    palette : list
        Color palette (default colorcet CET_R4).

    Returns
    -------
    DataFrame
        With added 'Color' and 'lab_order' columns.
    """
    df["Lab"] = df["Lab"].fillna("Blank")
    lab_list = df["Lab"].unique().tolist()

    df["lab_order"] = df.sort_values("Prefix").groupby("Lab").cumcount() + 1
    df["Color"] = df.apply(lambda x: set_color_by_lab(x, palette=palette, lab_list=lab_list), axis=1)
    return df


def set_y_offset(row, offset_map=OFFSETS):
    """Look up the y pixel offset for a measurement label based on co-location count.

    Parameters
    ----------
    row : Series
        Must have 'duplicate_magnitudes' column (1-indexed count).
    offset_map : dict
        Maps str(count) to [x_offset, y_offset] pairs.

    Returns
    -------
    int
        Y offset in pixels.
    """
    try:
        return offset_map[str(row["duplicate_magnitudes"])][1]
    except KeyError:
        return offset_map["1"][1]


def set_x_offset(row, offset_map=OFFSETS):
    """Look up the x pixel offset for a measurement label based on co-location count.

    Parameters
    ----------
    row : Series
        Must have 'duplicate_magnitudes' column (1-indexed count).
    offset_map : dict
        Maps str(count) to [x_offset, y_offset] pairs.

    Returns
    -------
    int
        X offset in pixels.
    """
    try:
        return offset_map[str(row["duplicate_magnitudes"])][0]
    except KeyError:
        return offset_map["1"][0]


def set_measurement_text_jitter(df):
    """Compute label offsets to spread co-located measurement points.

    Groups measurements by (Space_value, Time_value) magnitude bin and
    assigns incrementing offsets from the OFFSETS lookup table so labels
    don't stack on top of each other.

    Parameters
    ----------
    df : DataFrame
        Must have 'Space_value' and 'Time_value' columns.

    Returns
    -------
    DataFrame
        With added columns: duplicate_magnitudes, x_offset, y_offset.
    """
    df["duplicate_magnitudes"] = df.groupby(["Space_value", "Time_value"]).cumcount() + 1
    df["x_offset"] = df.apply(set_x_offset, axis=1)
    df["y_offset"] = df.apply(set_y_offset, axis=1)
    return df


def _log_extent_area(time_min, time_max, space_min, space_max):
    """Area of the process rectangle in log10-log10 space (orders² of magnitude).

    Equation:
        area = (log10(time_max) - log10(time_min)) * (log10(space_max) - log10(space_min)) + 2

    The +2 is a smoothing constant that prevents a singularity at ln(0)
    for point processes (area = 0) and provides a gentle alpha ramp for
    small extents.

    Parameters
    ----------
    time_min, time_max : float
        Time range endpoints (seconds).
    space_min, space_max : float
        Space range endpoints (m³).

    Returns
    -------
    float
        Log-space area + 2 (smoothing constant).
    """
    time_mags = np.log10(time_max) - np.log10(time_min)
    space_mags = np.log10(space_max) - np.log10(space_min)
    return time_mags * space_mags + 2  # avoid divide by zero errors


def set_fill_alpha(row):
    """Compute fill opacity for a process ellipse — smaller = more opaque.

    Equation:
        alpha = min(0.5 / ln(magnitude_combos), 1.0)

    Processes spanning many orders of magnitude get lower alpha so they
    don't obscure smaller processes underneath.

    Parameters
    ----------
    row : Series
        Must have Time_min, Time_max, Space_min, Space_max (astropy Quantities).

    Returns
    -------
    float
        Alpha value between 0 and 1.
    """
    extent = _log_extent_area(row.Time_min.value, row.Time_max.value, row.Space_min.value, row.Space_max.value)
    return min(0.5 * (1 / np.log(extent)), 1)


def create_name(row, include_prefix=False):
    """Build a display name for a process, optionally with a lab/person prefix.

    Long names (>50 chars) are split at the midpoint with a newline for
    label readability.

    Parameters
    ----------
    row : Series
        Must have 'ShortName'. Optionally 'Prefix'.
    include_prefix : bool
        If True and Prefix is non-empty, prepends "Prefix - " to the name.

    Returns
    -------
    str
        Display name, possibly with embedded newline.
    """
    short_name = row["ShortName"]

    if len(short_name) > 50:
        word_list = short_name.split(" ")
        break_pt = int(len(word_list) / 2)
        short_name = " ".join(word_list[0:break_pt]) + "\n" + " ".join(word_list[break_pt:])

    if include_prefix:
        prefix = row["Prefix"]
        if prefix and str(prefix).strip():
            return str(prefix) + " - " + short_name

    return short_name


def resolve_label_overlaps(
    df,
    fig_x_range,
    fig_y_range,
    fig_width_px=900,
    fig_height_px=600,
    font_size_px=12,
    max_iterations=200,
    padding_px=4.0,
    k_repel=1.0,
    k_attract=0.1,
):
    """Compute non-overlapping label positions for a Stommel diagram.

    Takes a DataFrame with columns Name, label_x, label_y (anchor points
    in data coordinates).  Returns the same DataFrame with added columns
    label_x_offset and label_y_offset in screen pixels, suitable for
    Bokeh LabelSet x_offset / y_offset.

    Algorithm (force-directed, log-log adapted):
      1. Convert data coords → normalised pixel space via log10 transform.
      2. Estimate label bounding boxes from text length × font size.
      3. Run iterative repulsion: overlapping labels push apart, spring
         force pulls back toward the anchor.
      4. Output resolved offsets in screen pixels.

    Manual overrides are respected: if the input DataFrame already contains
    non-null x_offset / y_offset columns, those labels are pinned in place
    and excluded from the solver.

    Priority: manual > computed > default (zero offset).

    Parameters
    ----------
    df : DataFrame
        Must contain columns: Name, label_x, label_y.
        Optional: x_offset, y_offset (manual overrides, in pixels).
    fig_x_range : (x_min, x_max)
        Data-coordinate extent of the time axis.
    fig_y_range : (y_min, y_max)
        Data-coordinate extent of the space axis.
    fig_width_px : int
        Figure width in pixels (for aspect ratio).
    fig_height_px : int
        Figure height in pixels.
    font_size_px : int
        Label font size for bounding-box estimation.
    max_iterations : int
        Maximum repulsion iterations.
    padding_px : float
        Minimum gap between label edges in pixel space.
    k_repel : float
        Repulsion force multiplier.
    k_attract : float
        Anchor-attraction force multiplier.

    Returns
    -------
    (DataFrame, bool)
        Tuple of (result DataFrame with label_x_offset/label_y_offset columns
        in screen pixels, converged flag). converged is True if all overlaps
        were resolved within max_iterations, False otherwise.

    Notes
    -----
    The solver uses O(n²) pairwise overlap checks per iteration, so it is
    designed for diagram-scale inputs (tens to low hundreds of labels).
    A warning is emitted for inputs exceeding 500 labels.
    """
    df = df.copy()

    if len(df) > 500:
        warnings.warn(
            f"resolve_label_overlaps has O(n²) complexity per iteration; "
            f"{len(df)} labels will be very slow. Consider reducing the "
            f"dataset or pre-filtering to the visible region.",
            stacklevel=2,
        )

    # Identify manually pinned labels
    has_manual_x = "x_offset" in df.columns
    has_manual_y = "y_offset" in df.columns
    if has_manual_x and has_manual_y:
        manual_mask = df["x_offset"].notna() & df["y_offset"].notna()
    else:
        manual_mask = pd.Series(False, index=df.index)

    # Convert anchor positions to pixel space
    anchors_px_x, anchors_px_y = data_to_pixel(
        df["label_x"].values,
        df["label_y"].values,
        fig_x_range,
        fig_y_range,
        fig_width_px,
        fig_height_px,
    )

    # Estimate bounding boxes
    bboxes = np.array([estimate_label_bbox(name, font_size_px) for name in df["Name"]])

    # Initial positions = anchors, offset slightly right and above
    # to avoid sitting directly on the data point
    default_nudge_x = font_size_px * 0.5
    default_nudge_y = font_size_px * 0.5
    positions = np.column_stack(
        [
            anchors_px_x + default_nudge_x,
            anchors_px_y + default_nudge_y,
        ]
    )
    anchors = positions.copy()

    # Pin manual overrides: convert their pixel offsets to absolute
    # pixel positions and freeze them
    if manual_mask.any():
        manual_idx = np.where(manual_mask.values)[0]
        for idx in manual_idx:
            positions[idx] = [
                anchors_px_x[idx] + df["x_offset"].iloc[idx],
                anchors_px_y[idx] + df["y_offset"].iloc[idx],
            ]
            anchors[idx] = positions[idx].copy()

    # Iterative repulsion
    for _ in range(max_iterations):
        # Check if any overlaps remain
        n = len(positions)
        has_overlap = False
        for i in range(n):
            for j in range(i + 1, n):
                if _boxes_overlap(
                    positions[i, 0],
                    positions[i, 1],
                    bboxes[i, 0],
                    bboxes[i, 1],
                    positions[j, 0],
                    positions[j, 1],
                    bboxes[j, 0],
                    bboxes[j, 1],
                    padding=padding_px,
                ):
                    has_overlap = True
                    break
            if has_overlap:
                break

        if not has_overlap:
            break

        positions = repulsion_step(
            positions,
            bboxes,
            anchors,
            k_repel=k_repel,
            k_attract=k_attract,
            padding=padding_px,
        )

        # Re-pin manual labels
        if manual_mask.any():
            manual_idx = np.where(manual_mask.values)[0]
            for idx in manual_idx:
                positions[idx] = anchors[idx]

    # Clamp to figure bounds
    for i in range(len(positions)):
        half_w = bboxes[i, 0] / 2
        half_h = bboxes[i, 1] / 2
        positions[i, 0] = np.clip(positions[i, 0], half_w, fig_width_px - half_w)
        positions[i, 1] = np.clip(positions[i, 1], half_h, fig_height_px - half_h)

    # Offsets in screen pixels = resolved position - anchor position.
    # Bokeh LabelSet x_offset/y_offset are in screen units (pixels),
    # so pixel-space offsets are the correct output format.
    anchor_positions = np.column_stack([anchors_px_x, anchors_px_y])
    df["label_x_offset"] = positions[:, 0] - anchor_positions[:, 0]
    df["label_y_offset"] = positions[:, 1] - anchor_positions[:, 1]

    # Manually pinned labels keep their original offsets
    if manual_mask.any():
        df.loc[manual_mask, "label_x_offset"] = df.loc[manual_mask, "x_offset"]
        df.loc[manual_mask, "label_y_offset"] = df.loc[manual_mask, "y_offset"]

    # Check convergence
    remaining = count_overlaps(
        df,
        fig_x_range,
        fig_y_range,
        fig_width_px,
        fig_height_px,
        font_size_px,
        padding_px,
    )
    converged = remaining == 0

    if not converged:
        warnings.warn(
            f"resolve_label_overlaps did not converge after {max_iterations} "
            f"iterations: {remaining} overlapping label pair(s) remain. "
            f"Try increasing max_iterations, reducing font_size_px, or "
            f"increasing figure dimensions.",
            stacklevel=2,
        )

    return df, converged


def count_overlaps(df, fig_x_range, fig_y_range, fig_width_px=900, fig_height_px=600, font_size_px=12, padding_px=4.0):
    """Count the number of overlapping label pairs after resolution.

    Useful for testing and diagnostics.

    Parameters
    ----------
    df : DataFrame
        Must have Name, label_x, label_y, label_x_offset, label_y_offset.
    fig_x_range, fig_y_range, fig_width_px, fig_height_px, font_size_px,
    padding_px : same as resolve_label_overlaps.

    Returns
    -------
    int : number of overlapping label pairs.
    """
    # Convert data anchors to pixel space, then add pixel offsets
    anchor_px_x, anchor_px_y = data_to_pixel(
        df["label_x"].values,
        df["label_y"].values,
        fig_x_range,
        fig_y_range,
        fig_width_px,
        fig_height_px,
    )
    px_x = anchor_px_x + df["label_x_offset"].values
    px_y = anchor_px_y + df["label_y_offset"].values

    bboxes = np.array([estimate_label_bbox(name, font_size_px) for name in df["Name"]])

    overlap_count = 0
    n = len(df)
    for i in range(n):
        for j in range(i + 1, n):
            if _boxes_overlap(
                px_x[i],
                px_y[i],
                bboxes[i, 0],
                bboxes[i, 1],
                px_x[j],
                px_y[j],
                bboxes[j, 0],
                bboxes[j, 1],
                padding=padding_px,
            ):
                overlap_count += 1

    return overlap_count
