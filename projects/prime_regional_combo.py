from bokeh.plotting import output_file, save, show
from time import time
from timeSpace.plotting import (
    add_processes,
    add_diffusion_lines,
    create_space_time_figure,
    add_legend,
    add_magnitude_labels,
    add_predefined_processes,
)
from timeSpace.constants import (
    DIFFUSION_COEFFICIENTS,
    PREDEFINED_PROCESSES_URI,
)
from timeSpace.etl import transform_process_response_sheet, transform_measurement_sheet, transform_predefined_processes
from timeSpace.data_processing import extract_google_sheet
from timeSpace.measurements import add_grouped_measurement, add_measurements
from timeSpace.plotting_helpers import set_color_palettes_by_lab

# Point to the certifi package's CA bundle
# import os
# import certifi
# os.environ["SSL_CERT_FILE"] = certifi.where()

# https://docs.google.com/spreadsheets/d/1qxn4IEYCjx0fEICE0t3cJVJz0ubVLxAdJ7hISshfT8w/edit?gid=1398751704#gid=1398751704
# https://docs.google.com/spreadsheets/d/1vHFoVas31lZC35OkVsYhdngl2csQMH1_ZDz_44u48BM/edit?gid=2103729361#gid=2103729361

PRIME_PROCESSES_URI = "1vHFoVas31lZC35OkVsYhdngl2csQMH1_ZDz_44u48BM"
PRIME_MEASUREMENTS_URI = "1qxn4IEYCjx0fEICE0t3cJVJz0ubVLxAdJ7hISshfT8w"


predefined_processes_df = extract_google_sheet(PREDEFINED_PROCESSES_URI, "predefined")


processes_df = extract_google_sheet(PRIME_PROCESSES_URI, "us-processes")
measurements_df = extract_google_sheet(PRIME_MEASUREMENTS_URI, "us-measurements")


processes_df.rename(
    columns={
        "Your first name": "Prefix",
        "Your research topic (one word)": "ShortName",
        "Minimum Time Scale": "Time_min",
        "Maximum Time Scale": "Time_max",
        "Minimum Spatial Scale": "Space_min",
        "Maximum Spatial Scale": "Space_max",
    },
    inplace=True,
)
measurements_df.rename(
    columns={"Your first name": "Prefix", "Your research topic (one word)": "ShortName"}, inplace=True
)

transformed_processes_df = transform_process_response_sheet(processes_df)

transformed_measurements_df = transform_measurement_sheet(measurements_df)
transformed_predefined_processes_df = transform_predefined_processes(predefined_processes_df)

transformed_processes_df = set_color_palettes_by_lab(transformed_processes_df)
transformed_measurements_df = set_color_palettes_by_lab(transformed_measurements_df)

transformed_processes_df["lab_order"] = transformed_processes_df.groupby("Lab").cumcount() + 1
transformed_measurements_df["lab_order"] = transformed_measurements_df.groupby("Lab").cumcount() + 1


def day_one(
    transformed_measurements_df, title=" ", transformed_processes_df=None, diffusion_coefficients=DIFFUSION_COEFFICIENTS
):
    p = create_space_time_figure(title=title)
    p = add_magnitude_labels(p)
    p = add_diffusion_lines(p, diffusion_coefficients)
    # p = add_predefined_processes(p, predefined_processes_df)
    if transformed_processes_df is not None:
        p = add_processes(p, transformed_processes_df)
    p = add_grouped_measurement(p, transformed_measurements_df, "Initials")
    p = add_legend(p)
    return p


def day_two(
    predefined_processes_df,
    transformed_processes_df,
    transformed_measurements_df,
    title=" ",
    diffusion_coefficients=DIFFUSION_COEFFICIENTS,
):
    p = create_space_time_figure(width=3000, height=1600, title=title)
    p = add_magnitude_labels(p)
    p = add_diffusion_lines(p, diffusion_coefficients)
    p = add_predefined_processes(p, predefined_processes_df)
    p = add_processes(p, transformed_processes_df)
    p = add_measurements(p, transformed_measurements_df, grey=True)
    p = add_legend(p)
    p.legend.ncols = 2

    return p


# p = day_one(transformed_measurements_df)
# p = day_one(predefined_processes_df, transformed_measurements_df, transformed_processes_df)
p = day_two(predefined_processes_df, transformed_processes_df, transformed_measurements_df, title="PriME Projects")
output_file(f"{int(time())}-prime-combo-plot.html", mode="inline")
save(p)
show(p)
