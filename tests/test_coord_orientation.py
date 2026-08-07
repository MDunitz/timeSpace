"""#23 — space_on_x orientation guard between coord baking and plotting."""

import pandas as pd
import pytest

from timeSpace.constants import COORD_ORIENTATION_COL
from timeSpace.etl import transform_process_response_sheet, transform_predefined_processes
from timeSpace.plotting import add_processes, add_predefined_processes, create_space_time_figure


def _response_df():
    return pd.DataFrame(
        {
            "ShortName": ["A"],
            "Prefix": ["X"],
            "Color": ["#336699"],
            "Time_min": ["1e2"],
            "Time_max": ["1e4"],
            "Space_min": ["1e-6"],
            "Space_max": ["1e-2"],
        }
    )


@pytest.mark.parametrize("space_on_x", [True, False])
def test_process_transform_stamps_orientation(space_on_x):
    result = transform_process_response_sheet(_response_df(), space_on_x=space_on_x)
    assert (result[COORD_ORIENTATION_COL] == space_on_x).all()


def _predefined_df():
    df = _response_df()
    df["Name"] = ["A"]
    return df


@pytest.mark.parametrize("space_on_x", [True, False])
def test_predefined_transform_stamps_orientation(space_on_x):
    result = transform_predefined_processes(_predefined_df(), space_on_x=space_on_x)
    assert (result[COORD_ORIENTATION_COL] == space_on_x).all()


def test_add_processes_matching_orientation_is_fine():
    df = transform_process_response_sheet(_response_df(), space_on_x=False)
    p = create_space_time_figure(space_on_x=False)
    add_processes(p, df, space_on_x=False)  # no raise


def test_add_processes_raises_on_mismatch():
    df = transform_process_response_sheet(_response_df(), space_on_x=True)
    p = create_space_time_figure(space_on_x=False)
    with pytest.raises(ValueError, match="space_on_x mismatch"):
        add_processes(p, df, space_on_x=False)


def test_add_predefined_processes_raises_on_mismatch():
    df = transform_predefined_processes(_predefined_df(), space_on_x=True)
    p = create_space_time_figure(space_on_x=False)
    with pytest.raises(ValueError, match="space_on_x mismatch"):
        add_predefined_processes(p, df, space_on_x=False)


def test_absent_orientation_column_does_not_raise():
    """A hand-built frame without the stamp is the caller's responsibility."""
    df = transform_process_response_sheet(_response_df(), space_on_x=True)
    df = df.drop(columns=[COORD_ORIENTATION_COL])
    p = create_space_time_figure(space_on_x=True)
    add_processes(p, df, space_on_x=True)  # no raise
