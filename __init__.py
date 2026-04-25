from pathlib import Path

PROJECT_ROOT = Path(__file__).parent

__version__ = "0.1.1"

__all__ = [
    "PROJECT_ROOT",
    # Plotting
    "create_space_time_figure",
    "add_magnitude_labels",
    "add_processes",
    "add_predefined_processes",
    "add_process_label_leaders",
    "add_diffusion_lines",
    "add_light_cone",
    "add_legend",
    # Measurements
    "add_measurements",
    "add_grouped_measurement",
    # Calculations
    "create_ellipse_data",
    "calculate_diffusion_length",
    "calculate_sphere_volume",
    "classify_process_geometry",
    # Label placement
    "resolve_label_overlaps",
    "count_overlaps",
    # ETL
    "transform_process_response_sheet",
    "transform_predefined_processes",
    "transform_measurement_sheet",
    # Data access
    "extract_google_sheet",
    # Demo
    "demo",
]

# Plotting
from timeSpace.plotting import (
    create_space_time_figure,
    add_magnitude_labels,
    add_processes,
    add_predefined_processes,
    add_process_label_leaders,
    add_diffusion_lines,
    add_light_cone,
    add_legend,
)

# Calculations
from timeSpace.calculations import (
    create_ellipse_data,
    calculate_diffusion_length,
    calculate_sphere_volume,
    classify_process_geometry,
)

# ETL
from timeSpace.etl import (
    transform_process_response_sheet,
    transform_predefined_processes,
    transform_measurement_sheet,
)

# Measurements
from timeSpace.measurements import (
    add_measurements,
    add_grouped_measurement,
)

# Label collision detection
from timeSpace.plotting_helpers import resolve_label_overlaps, count_overlaps

# Data access
from timeSpace.data_processing import extract_google_sheet

# Library logging — silent by default, user opts in with:
#   import logging
#   logging.getLogger("timeSpace").setLevel(logging.INFO)
#   logging.basicConfig()
import logging

logging.getLogger(__name__).addHandler(logging.NullHandler())


def demo(show=True):
    """Build and optionally display the default Stommel diagram with Boyd (2015) data.

    A one-liner to verify your install works and see what timeSpace produces::

        import timeSpace
        timeSpace.demo()

    Parameters
    ----------
    show : bool, default True
        If True, opens the diagram in the default browser via ``bokeh.plotting.show``.

    Returns
    -------
    bokeh.plotting.Figure
        The assembled Stommel diagram figure with magnitude labels,
        diffusion lines, light cone, Boyd (2015) processes, and legend.
    """
    import pandas as pd

    data = pd.read_csv(PROJECT_ROOT / "data" / "datasets" / "stommel_boyd2015_volumes.csv")
    df = transform_predefined_processes(data)

    p = create_space_time_figure()
    add_magnitude_labels(p)
    add_diffusion_lines(p)
    add_light_cone(p)
    add_predefined_processes(p, df)
    add_legend(p)

    if show:
        from bokeh.plotting import show as _show

        _show(p)
    return p
