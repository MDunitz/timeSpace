# ---------------------------------------------------------------------------
# Label collision detection and resolution (force-directed placement)
# ---------------------------------------------------------------------------
#
# Force-directed label placement for log-log Stommel diagrams.
# Based on the adjustText iterative-repulsion approach, adapted for
# log-scale axes where Euclidean distance in data coordinates is
# meaningless — all geometry is computed in a normalized pixel space
# derived from the log10 transform of each axis.

import numpy as np


def data_to_pixel(x_data, y_data, x_range, y_range, w_px, h_px):
    """Convert log-log data coordinates to pixel-space coordinates.

    Stommel diagram coordinate mapping:
        px_x = (log10(x) - log10(x_min)) / (log10(x_max) - log10(x_min)) * w_px
        px_y = (log10(y) - log10(y_min)) / (log10(y_max) - log10(y_min)) * h_px

    Parameters
    ----------
    x_data, y_data : array-like
        Positions in data coordinates (must be > 0 for log10).
    x_range : (x_min, x_max)
        Data-coordinate extent of the x axis.
    y_range : (y_min, y_max)
        Data-coordinate extent of the y axis.
    w_px, h_px : int
        Figure dimensions in pixels.

    Returns
    -------
    px_x, px_y : ndarray
        Positions in pixel-space coordinates.
    """
    x_data = np.asarray(x_data, dtype=float)
    y_data = np.asarray(y_data, dtype=float)

    log_x = np.log10(x_data)
    log_y = np.log10(y_data)

    log_x_min, log_x_max = np.log10(x_range[0]), np.log10(x_range[1])
    log_y_min, log_y_max = np.log10(y_range[0]), np.log10(y_range[1])

    px_x = (log_x - log_x_min) / (log_x_max - log_x_min) * w_px
    px_y = (log_y - log_y_min) / (log_y_max - log_y_min) * h_px

    return px_x, px_y


def pixel_to_data(px_x, px_y, x_range, y_range, w_px, h_px):
    """Convert pixel-space coordinates back to log-log data coordinates.

    Inverse of data_to_pixel:
        x_data = 10^(px_x / w_px * (log10(x_max) - log10(x_min)) + log10(x_min))

    Parameters
    ----------
    px_x, px_y : array-like
        Positions in pixel-space coordinates.
    x_range, y_range : (min, max)
        Data-coordinate axis extents.
    w_px, h_px : int
        Figure dimensions in pixels.

    Returns
    -------
    x_data, y_data : ndarray
        Positions in data coordinates.
    """
    px_x = np.asarray(px_x, dtype=float)
    px_y = np.asarray(px_y, dtype=float)

    log_x_min, log_x_max = np.log10(x_range[0]), np.log10(x_range[1])
    log_y_min, log_y_max = np.log10(y_range[0]), np.log10(y_range[1])

    log_x = px_x / w_px * (log_x_max - log_x_min) + log_x_min
    log_y = px_y / h_px * (log_y_max - log_y_min) + log_y_min

    return np.power(10.0, log_x), np.power(10.0, log_y)


def estimate_label_bbox(text, font_size_px=12):
    """Estimate label bounding box in pixel units.

    Empirical ratio for sans-serif (Anthropic Sans / Helvetica):
        char_width ≈ 0.58 × font_size
        line_height ≈ 1.3 × font_size

    Parameters
    ----------
    text : str
        Label text.
    font_size_px : int
        Font size in pixels.

    Returns
    -------
    (width_px, height_px) : tuple of float
    """
    char_width = font_size_px * 0.58
    return len(str(text)) * char_width, font_size_px * 1.3


def _boxes_overlap(cx_a, cy_a, w_a, h_a, cx_b, cy_b, w_b, h_b, padding=0.0):
    """Check whether two axis-aligned bounding boxes overlap.

    Each box is defined by its centre (cx, cy) and full (width, height).
    An optional padding expands each box before testing.

    Returns
    -------
    bool
    """
    half_w_a, half_h_a = w_a / 2 + padding, h_a / 2 + padding
    half_w_b, half_h_b = w_b / 2 + padding, h_b / 2 + padding

    return abs(cx_a - cx_b) < half_w_a + half_w_b and abs(cy_a - cy_b) < half_h_a + half_h_b


def _overlap_vector(cx_a, cy_a, w_a, h_a, cx_b, cy_b, w_b, h_b, padding=0.0):
    """Compute the overlap penetration vector between two AABBs.

    Returns (ox, oy) — the amount of overlap along each axis.
    Positive values mean overlap; negative means separation.
    """
    half_w_a, half_h_a = w_a / 2 + padding, h_a / 2 + padding
    half_w_b, half_h_b = w_b / 2 + padding, h_b / 2 + padding

    ox = (half_w_a + half_w_b) - abs(cx_a - cx_b)
    oy = (half_h_a + half_h_b) - abs(cy_a - cy_b)

    return ox, oy


def repulsion_step(positions, bboxes, anchors, k_repel=1.0, k_attract=0.1, padding=0.0):
    """One iteration of force-directed label placement.

    Two-phase update:

    Phase 1 — Repulsion:  Accumulate displacements from all overlapping
    pairs computed against the ORIGINAL positions, then apply all at once.
    Each label in a pair is pushed by slightly more than half the overlap
    depth (0.51×) to guarantee floating-point clearance.  A minimum push
    of ``padding`` pixels prevents oscillation near the overlap boundary.

    Phase 2 — Attraction:  Labels that were NOT overlapping at the START
    of this iteration are gently pulled back toward their anchor points.
    Labels involved in overlaps skip attraction so repulsion can work
    unimpeded.

    Parameters
    ----------
    positions : ndarray, shape (N, 2)
        Current label centre positions in pixel space.
    bboxes : ndarray, shape (N, 2)
        (width, height) of each label in pixel space.
    anchors : ndarray, shape (N, 2)
        Original anchor positions (pixel space).
    k_repel : float
        Repulsion strength multiplier.
    k_attract : float
        Attraction-to-anchor strength.
    padding : float
        Extra padding around each box (pixels).

    Returns
    -------
    new_positions : ndarray, shape (N, 2)
    """
    n = len(positions)

    # Identify which labels are currently overlapping BEFORE repulsion.
    # These labels will not receive attraction this iteration — they need
    # full freedom to separate without being pulled back.
    involved_in_overlap = np.zeros(n, dtype=bool)
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
                padding=padding,
            ):
                involved_in_overlap[i] = True
                involved_in_overlap[j] = True

    # Phase 1: Repulsion — accumulate displacements from all overlapping
    # pairs BEFORE applying any moves.  Computing against original positions
    # prevents cascading under-correction from in-place updates.
    displacements = np.zeros_like(positions)
    for i in range(n):
        for j in range(i + 1, n):
            ox, oy = _overlap_vector(
                positions[i, 0],
                positions[i, 1],
                bboxes[i, 0],
                bboxes[i, 1],
                positions[j, 0],
                positions[j, 1],
                bboxes[j, 0],
                bboxes[j, 1],
                padding=padding,
            )
            if ox > 0 and oy > 0:
                if ox < oy:
                    # Push by at least padding to prevent oscillation
                    push_amount = max(ox * 0.51, padding) * k_repel
                    sign = 1.0 if positions[i, 0] < positions[j, 0] else -1.0
                    displacements[i, 0] -= push_amount * sign
                    displacements[j, 0] += push_amount * sign
                else:
                    push_amount = max(oy * 0.51, padding) * k_repel
                    sign = 1.0 if positions[i, 1] < positions[j, 1] else -1.0
                    displacements[i, 1] -= push_amount * sign
                    displacements[j, 1] += push_amount * sign

    new_positions = positions + displacements

    # Phase 2: Attraction — gently pull free labels back toward anchors.
    free_mask = ~involved_in_overlap
    drift = new_positions - anchors
    new_positions[free_mask] -= k_attract * drift[free_mask]

    return new_positions
