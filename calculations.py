import numpy as np
from astropy import units
import astropy.units as u
from timeSpace.constants import O2_diffusion_rate


@u.quantity_input(time=u.second)
@u.quantity_input(diffusion_coefficient="diffusivity")
def calculate_diffusion_length(time, diffusion_coefficient=O2_diffusion_rate) -> u.Quantity[units.meter]:
    """3D RMS diffusion displacement as a function of time.

    Equation (3D root-mean-square displacement):
        L = sqrt(6 * D * t)

    This is the characteristic radius of the sphere of space explored
    by a molecule undergoing 3D Brownian motion. Used with
    calculate_sphere_volume() to produce diffusion volumes for the
    Stommel diagram spatial axis.

    Parameters
    ----------
    time : astropy Quantity [s]
        Elapsed time.
    diffusion_coefficient : astropy Quantity [m²/s]
        Molecular diffusion coefficient. Default is O₂ in water at 25°C.

    Returns
    -------
    astropy Quantity [m]
        Characteristic diffusion length.

    Notes
    -----
    Built-in diffusion coefficients (O₂, CO₂, glucose, etc. in constants.py)
    are measured at 25°C in pure water. For other temperatures or media,
    pass a custom diffusion_coefficient. See constants.py for sources.
    """
    # convert coefficient to meters^2/second
    diffusion_coefficient = diffusion_coefficient.to(units.meter * units.meter / units.second)
    return (6 * diffusion_coefficient * time) ** (1 / 2)


@u.quantity_input(length=u.m)
def calculate_sphere_volume(length) -> u.m**3:
    """Volume of a sphere with the given radius.

    Equation:
        V = (4/3) * π * r³

    Parameters
    ----------
    length : astropy Quantity [m]
        Sphere radius.

    Returns
    -------
    astropy Quantity [m³]
        Sphere volume.
    """
    return (4 / 3) * np.pi * length**3


def calculate_log_center(min_val, max_val):
    """Geometric center of an interval in log10 space.

    Equation:
        center = (log10(min) + log10(max)) / 2

    Parameters
    ----------
    min_val, max_val : float
        Interval endpoints (positive, linear scale).

    Returns
    -------
    float
        Log10 of the geometric mean.
    """
    log_min = np.log10(min_val)
    log_max = np.log10(max_val)
    log_center = (log_min + log_max) / 2

    return log_center


def calculate_log_width(min_val, max_val):
    """Half-width of an interval in log10 space (semi-axis length).

    Equation:
        half_width = (log10(max) - log10(min)) / 2

    Parameters
    ----------
    min_val, max_val : float
        Interval endpoints (positive, linear scale).

    Returns
    -------
    float
        Half the log10 range. Zero if min == max (degenerate).
    """
    log_min = np.log10(min_val)
    log_max = np.log10(max_val)
    return (log_max - log_min) / 2


def calculate_log10_y_for_ellipse(x, c_y, c_x, b, a):
    """
    Ellipse equation in log10 space:
        ((log10(x) - c_x) / a)^2 + ((log10(y) - c_y) / b)^2 = 1

    Solving for y gives:
        next = 1 - ((log10(x) - c_x) / a)^2
        y = 10^(c_y ± b * sqrt(next))

    disc is clamped to [0, 1] to guard against floating-point values of x
    landing just outside [time_min, time_max] (e.g. from np.logspace endpoints),
    which would make disc slightly negative and cause RuntimeWarning in **0.5.
    """
    inner = (np.log10(x) - c_x) / a
    disc = np.clip(1 - inner**2, 0, 1)
    plus_b = c_y + (b * (disc**0.5))
    minus_b = c_y - (b * (disc**0.5))
    return plus_b, minus_b


def create_ellipse_data(row, n_points=1000, space_on_x=True):
    """Generate ellipse vertices in log10 space.

    Ellipse equation:
        ((log10(x) - c_x) / a)^2 + ((log10(y) - c_y) / b)^2 = 1

    Traces the upper half (y+) left-to-right, then the lower half (y-)
    right-to-left, producing a closed polygon without a midline seam.

    Parameters
    ----------
    row : Series-like with Time_min, Time_max, Space_min, Space_max (astropy Quantities)
    n_points : int
        Number of x samples per half-ellipse. Total vertices = 2 * n_points.
    space_on_x : bool
        True (default): x=space, y=time (Boyd et al. 2015 Fig. 1 layout)
        False: x=time, y=space (original Stommel 1963 orientation)
    """
    time_min, time_max = row.Time_min.value, row.Time_max.value
    space_min, space_max = row.Space_min.value, row.Space_max.value

    # Check for degenerate axes on physical dimensions (before axis swap)
    time_log_width = calculate_log_width(time_min, time_max)
    space_log_width = calculate_log_width(space_min, space_max)
    if time_log_width == 0 or space_log_width == 0:
        raise ValueError(
            f"Degenerate axis: time width={time_log_width}, space width={space_log_width}. "
            f"Use classify_process_geometry() to detect and render as line/point."
        )

    if space_on_x:
        # Stommel convention: x = space, y = time
        x_min, x_max = space_min, space_max
        y_min, y_max = time_min, time_max
    else:
        # Classic orientation: x = time, y = space
        x_min, x_max = time_min, time_max
        y_min, y_max = space_min, space_max

    x_center = calculate_log_center(x_min, x_max)
    y_center = calculate_log_center(y_min, y_max)

    x_log_width = calculate_log_width(x_min, x_max)
    y_log_width = calculate_log_width(y_min, y_max)

    x_vals = np.logspace(np.log10(x_min), np.log10(x_max), n_points)
    y_plus = []
    y_minus = []

    for i in x_vals:
        plus, minus = calculate_log10_y_for_ellipse(i, c_y=y_center, c_x=x_center, b=y_log_width, a=x_log_width)
        y_plus.append(plus)
        y_minus.append(minus)

    y_plus_log = [10**y for y in y_plus]
    y_minus_log = [10**y for y in y_minus]
    # Combine top and bottom arcs into a closed polygon
    # Flip the bottom arc so the path traces a loop without a midline seam
    x_data_points = np.concatenate((x_vals, np.flip(x_vals)))
    y_data_points = np.concatenate((y_plus_log, np.flip(y_minus_log)))

    return x_data_points, y_data_points


def classify_process_geometry(row, threshold=0.1):
    """Classify whether each axis is degenerate (min ≈ max) in log10 space.

    A degenerate axis spans fewer than *threshold* orders of magnitude,
    meaning it is visually indistinguishable from a point or line on the
    diagram. On a typical 30-OOM Stommel axis, 0.1 OOM is ~3 pixels —
    below this the axis has no visible extent.

    Parameters
    ----------
    row : Series-like
        Must have Time_min, Time_max, Space_min, Space_max (astropy Quantities).
    threshold : float
        Minimum log10 range (orders of magnitude) to count as non-degenerate.
        Default 0.1 OOM.

    Returns
    -------
    str : one of "ellipse", "vline", "hline", "point"
        ellipse — both axes have range → render as filled ellipse
        vline   — time degenerate, space has range → vertical line at fixed time
        hline   — space degenerate, time has range → horizontal line at fixed space
        point   — both degenerate → single marker
    """
    t_min, t_max = row.Time_min.value, row.Time_max.value
    s_min, s_max = row.Space_min.value, row.Space_max.value

    t_degen = abs(np.log10(t_max) - np.log10(t_min)) < threshold
    s_degen = abs(np.log10(s_max) - np.log10(s_min)) < threshold

    if t_degen and s_degen:
        return "point"
    elif t_degen:
        return "vline"
    elif s_degen:
        return "hline"
    else:
        return "ellipse"
