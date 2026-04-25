from bokeh.plotting import output_file, save, show
from time import time
from bokeh.io import export_png

from timeSpace.plotting import add_processes, create_space_time_figure, add_legend, add_magnitude_labels

from timeSpace.etl import transform_process_response_sheet
from timeSpace.data_processing import extract_google_sheet

from bokeh.plotting import show
import pandas as pd
from timeSpace.plotting_helpers import set_color_by_prefix

config = {"title": "Modeled Processes ", "output_file": "modeled-processes", "concept_name": "bgcmModels"}


def transform_data(config_data):
    data = pd.read_csv("timeSpace/data/datasets/stommel_boyd2015_volumes.csv")
    data.dropna(subset=["Time_min", "Time_max", "Space_min", "Space_max"], inplace=True)
    data.rename(columns={"Process": "ShortName"}, inplace=True)
    data["Prefix"] = data.apply(lambda x: x["ShortName"][0:3], axis=1)

    columns = ["Prefix", "ShortName", "Time_min", "Time_max", "Space_min", "Space_max", "Color"]
    transformed_data = transform_process_response_sheet(data, possible_col_list=columns)
    transformed_data = set_color_by_prefix(transformed_data)
    transformed_data["Sorted_Index_in_Group"] = (
        transformed_data.groupby("Space_min")["Space_max"].rank(method="first", ascending=True).astype(int)
    )
    transformed_data["y_offset"] = transformed_data.apply(lambda x: -30 * (x["Sorted_Index_in_Group"] - 1), axis=1)
    transformed_data["x_offset"] = 0
    return transformed_data


def make_plot(transformed_data, config_data, interactive=True):
    p = create_space_time_figure(title=config_data["title"])
    p = add_magnitude_labels(p)
    # p = add_diffusion_lines(p, diffusion_coefficients)

    p = add_processes(p, transformed_data, interactive=interactive)
    p = add_legend(p)
    return p


def bgcm_plot(config_data, interactive):
    transformed_data = transform_data(config_data)
    # transformed_data.loc[transformed_data["ShortName"]=="Local communities and populations", "x_offset"] = 10
    # transformed_data.loc[transformed_data["ShortName"]=="microenvironment", "y_offset"] = -75
    p = make_plot(transformed_data=transformed_data, config_data=config_data, interactive=interactive)
    return p


p = bgcm_plot(config, True)
file_name = f"{int(time())}-{config['output_file']}"

# p = model_plot(model_config_data, spreadsheet_id, interactive)
# file_name = f"{int(time())}-{model_config_data['output_file']}"

# p = microbial_process_plot(mp_config_data, spreadsheet_id, interactive)
# file_name = f"{int(time())}-{mp_config_data['output_file']}"

output_file(f"{file_name}.html", mode="inline")
# export_png(p, filename=f"{file_name}.png")
save(p)
show(p)
