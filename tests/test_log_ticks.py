from bokeh.models import CustomJSTicker

from timeSpace.log_ticks import decade_log_ticker
from timeSpace.plotting import create_space_time_figure


def test_both_main_axes_use_decade_ticker():
    p = create_space_time_figure()
    assert isinstance(p.xaxis[0].ticker, CustomJSTicker)
    assert isinstance(p.yaxis[0].ticker, CustomJSTicker)


def test_ticker_args():
    t = decade_log_ticker(desired=6, steps=[1, 5])
    assert t.args == {"desired": 6, "steps": [1, 5]}
