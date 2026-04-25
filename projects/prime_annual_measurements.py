from bokeh.plotting import output_file, save, show
from time import time
from bokeh.io import export_png

from timeSpace.plotting import add_processes, create_space_time_figure, add_legend, add_magnitude_labels

from timeSpace.etl import transform_process_response_sheet
from timeSpace.data_processing import extract_google_sheet

from bokeh.plotting import show
import pandas as pd
from timeSpace.plotting_helpers import set_color_by_prefix

sheets = {
    "eco": {
        "title": "Ecological Units",
        "output_file": "eco-units",
        "sheet_id": "1220282474",
        "sheet_name": "ecological-scales",
        "concept_name": "EcologicalUnit",
    },
    "models": {
        "title": "Models",
        "output_file": "models",
        "sheet_id": "20425231",
        "sheet_name": "models",
        "concept_name": "Model",
    },
    "microbial_processes": {
        "title": "Microbial Processes",
        "output_file": "micro-processes",
        "sheet_id": "509828764",
        "sheet_name": "microbial-processes",
        "concept_name": "EcologicalUnit",
    },
}
spreadsheet_id = "1ZyPPwtnDTnZIIuiUlGHEIaXJjeknTEQ_hIrIv6LUNYU"


def transform_data(config_data, spreadsheet_id=spreadsheet_id):
    data = extract_google_sheet(
        spreadsheet_id=spreadsheet_id,
        sheet_id=config_data["sheet_id"],
        data_name=config_data["sheet_name"],
        from_cache=True,
    )
    data.dropna(subset=["Time_min", "Time_max", "Space_min", "Space_max"], inplace=True)
    data.rename(columns={config_data["concept_name"]: "ShortName"}, inplace=True)
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


def eco_plot(config_data, spreadsheet_id, interactive):
    transformed_data = transform_data(config_data, spreadsheet_id=spreadsheet_id)
    transformed_data.loc[transformed_data["ShortName"] == "Nutrient Patches", "x_offset"] = -300
    transformed_data.loc[transformed_data["ShortName"] == "microcolonies (100 cells or less)", "x_offset"] = 20
    transformed_data.loc[transformed_data["ShortName"] == "Nutrient Plumes", "y_offset"] = -200
    transformed_data.loc[transformed_data["ShortName"] == "Local communities and populations", "y_offset"] = -65
    transformed_data.loc[transformed_data["ShortName"] == "Local communities and populations", "x_offset"] = 10
    transformed_data.loc[transformed_data["ShortName"] == "microenvironment", "y_offset"] = -75
    p = make_plot(transformed_data=transformed_data, config_data=config_data, interactive=interactive)
    return p


def model_plot(config_data, spreadsheet_id, interactive):
    transformed_data = transform_data(config_data, spreadsheet_id=spreadsheet_id)
    transformed_data.loc[transformed_data["ShortName"] == "Trait-Based Models", "x_offset"] = -370
    transformed_data.loc[transformed_data["ShortName"] == "Trait-Based Models", "y_offset"] = -100
    transformed_data.loc[transformed_data["ShortName"] == "Models with Increased Microbial Diversity", "x_offset"] = -65
    transformed_data.loc[transformed_data["ShortName"] == "Models with Increased Microbial Diversity", "y_offset"] = (
        -190
    )
    transformed_data.loc[transformed_data["ShortName"] == "Default Biogeochemical Models", "y_offset"] = -250
    transformed_data.loc[transformed_data["ShortName"] == "Proteome Allocation Models", "y_offset"] = -50
    transformed_data.loc[transformed_data["ShortName"] == "Macromolecular Models", "x_offset"] = -700
    transformed_data.loc[transformed_data["ShortName"] == "Particle-Associated Microbial Dynamics", "y_offset"] = -150

    p = make_plot(transformed_data=transformed_data, config_data=config_data, interactive=interactive)
    return p


def microbial_process_plot(config_data, spreadsheet_id, interactive):
    transformed_data = transform_data(config_data, spreadsheet_id=spreadsheet_id)
    transformed_data.loc[transformed_data["ShortName"] == "Chemotaxis", "x_offset"] = -250
    transformed_data.loc[transformed_data["ShortName"] == "Chemotaxis", "y_offset"] = -350
    transformed_data.loc[transformed_data["ShortName"] == "Biofilm formation", "y_offset"] = -400
    transformed_data.loc[transformed_data["ShortName"] == "Biofilm formation", "x_offset"] = -50

    p = make_plot(transformed_data=transformed_data, config_data=config_data, interactive=interactive)
    return p


interactive = False

eco_config_data = sheets["eco"]
mp_config_data = sheets["microbial_processes"]
model_config_data = sheets["models"]

# p = eco_plot(eco_config_data, spreadsheet_id, interactive)
# file_name = f"{int(time())}-{eco_config_data['output_file']}"

# p = model_plot(model_config_data, spreadsheet_id, interactive)
# file_name = f"{int(time())}-{model_config_data['output_file']}"

p = microbial_process_plot(mp_config_data, spreadsheet_id, interactive)
file_name = f"{int(time())}-{mp_config_data['output_file']}"

# output_file(f"{file_name}.html", mode='inline')
# export_png(p, filename=f"{file_name}.png")
save(p)
show(p)
