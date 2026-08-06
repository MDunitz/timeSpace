import pandas as pd
import pytest

from timeSpace.cli import parse_args, load_dataframe, build_figure, write_html, main


def _conforming_df():
    return pd.DataFrame(
        {
            "Name": ["diffusion", "advection", "mixing"],
            "Color": ["#1f77b4", "#ff7f0e", "#2ca02c"],
            "Time_min": [1.0, 3600.0, 86400.0],
            "Time_max": [3600.0, 86400.0, 3.15e7],
            "Space_min": [1.0, 1e3, 1e6],
            "Space_max": [1e3, 1e6, 1e9],
            "Category": ["physical", "physical", "biological"],
        }
    )


@pytest.fixture
def csv_path(tmp_path):
    path = tmp_path / "input.csv"
    _conforming_df().to_csv(path, index=False)
    return path


class TestParseArgs:
    def test_csv_and_sheet_mutually_exclusive(self):
        with pytest.raises(SystemExit):
            parse_args(["--csv", "a.csv", "--sheet-id", "abc"])

    def test_requires_a_source(self):
        with pytest.raises(SystemExit):
            parse_args(["--output", "out.html"])

    def test_defaults(self):
        args = parse_args(["--csv", "a.csv"])
        assert args.output == "stommel.html"
        assert args.time_on_x is False
        assert args.n_points == 1000


class TestPipeline:
    def test_load_dataframe_csv(self, csv_path):
        df = load_dataframe(csv=csv_path)
        assert list(df.Name) == ["diffusion", "advection", "mixing"]

    def test_build_figure_space_on_x(self):
        fig = build_figure(_conforming_df(), space_on_x=True, n_points=100)
        assert fig.xaxis[0].axis_label.startswith("Space")

    def test_build_figure_time_on_x(self):
        fig = build_figure(_conforming_df(), space_on_x=False, n_points=100)
        assert fig.xaxis[0].axis_label.startswith("Time")

    def test_build_figure_static(self):
        fig = build_figure(_conforming_df(), n_points=100, interactive=False)
        assert fig is not None

    def test_write_html_self_contained(self, tmp_path):
        fig = build_figure(_conforming_df(), n_points=100)
        out = write_html(fig, tmp_path / "out.html", title="t")
        assert out.exists()
        assert "<html" in out.read_text().lower()


class TestMain:
    def test_main_writes_output(self, csv_path, tmp_path):
        out = tmp_path / "diagram.html"
        rc = main(["--csv", str(csv_path), "--output", str(out), "--n-points", "100"])
        assert rc == 0
        assert out.exists()

    def test_main_time_on_x(self, csv_path, tmp_path):
        out = tmp_path / "diagram.html"
        rc = main(["--csv", str(csv_path), "--output", str(out), "--time-on-x", "--n-points", "100"])
        assert rc == 0
        assert out.exists()
