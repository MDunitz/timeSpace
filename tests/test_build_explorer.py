import re
from pathlib import Path

import pytest

from timeSpace.explorer import build_explorer

REPO = Path(__file__).resolve().parent.parent
CSV = REPO / "data" / "datasets" / "time_space_reference_objects.csv"


@pytest.fixture(scope="module")
def toggle_html(tmp_path_factory):
    out = tmp_path_factory.mktemp("toggle") / "explorer_toggle.html"
    build_explorer(str(CSV), str(out), mode="toggle")
    return out.read_text()


@pytest.fixture(scope="module")
def select_html(tmp_path_factory):
    out = tmp_path_factory.mktemp("select") / "explorer.html"
    build_explorer(str(CSV), str(out))
    return out.read_text()


class TestSelectMode:
    def test_builds_with_layered_category_checkboxes(self, select_html):
        assert "<html" in select_html.lower()
        assert "CheckboxGroup" in select_html
        assert "activeSet" in select_html

    def test_callbacks_never_write_back_to_the_other_widget(self):
        # The old category and object callbacks each reset the other's
        # dropdown, which blanked the plot when an object was picked after
        # a category. The shared callback must only read widget state.
        from timeSpace.explorer.callbacks import VISIBILITY_JS

        assert "obj_select.value =" not in VISIBILITY_JS
        assert "checkbox.active =" not in VISIBILITY_JS

    def test_starts_empty(self, select_html):
        assert "Tick one or more categories" in select_html


class TestToggleMode:
    def test_self_contained(self, toggle_html):
        assert "<html" in toggle_html.lower()

    def test_has_checkbox_group(self, toggle_html):
        assert "CheckboxGroup" in toggle_html

    def test_has_accumulate_callback(self, toggle_html):
        # accumulate-visibility JS marker (union of checked categories)
        assert "activeSet" in toggle_html

    def test_tiered_labels_marker(self, toggle_html):
        # labels revealed only for the pinned individual
        assert "lal[i] = (isSel ||" in toggle_html
        assert re.search(r"label_lone_category[^a-z]{0,12}false", toggle_html)


class TestPointMarkersHiddenOnLoad:
    def test_scatter_outline_follows_alpha_column(self):
        from bokeh.models import Scatter

        from timeSpace.explorer.data import load_reference_objects
        from timeSpace.explorer.figure import create_figure
        from timeSpace.explorer.sources import add_custom_glyphs, add_reference_glyphs

        p = create_figure()
        add_reference_glyphs(p, load_reference_objects(str(CSV)))
        add_custom_glyphs(p)
        scatters = [r for r in p.renderers if isinstance(r.glyph, Scatter)]
        assert len(scatters) == 2
        for r in scatters:
            assert r.glyph.line_alpha == r.glyph.fill_alpha
            assert set(r.data_source.data["alpha"]) == {0.0}


class TestReferenceInTooltip:
    def test_every_object_has_source_text_and_tooltip_shows_it(self):
        from bokeh.models import HoverTool

        from timeSpace.explorer.config import UNSOURCED_LABEL
        from timeSpace.explorer.data import load_reference_objects
        from timeSpace.explorer.figure import create_figure
        from timeSpace.explorer.sources import add_reference_glyphs

        p = create_figure()
        source, *_ = add_reference_glyphs(p, load_reference_objects(str(CSV)))
        refs = source.data["reference"]
        assert len(refs) == len(source.data["name"])
        assert all(isinstance(r, str) and r for r in refs)
        assert UNSOURCED_LABEL in refs
        assert any(r != UNSOURCED_LABEL for r in refs)
        hover = [t for t in p.tools if isinstance(t, HoverTool)][-1]
        assert "@reference" in hover.tooltips


@pytest.fixture(scope="module")
def built():
    from timeSpace.explorer.data import data_ranges, load_reference_objects
    from timeSpace.explorer.figure import create_figure
    from timeSpace.explorer.sources import add_reference_glyphs

    df = load_reference_objects(str(CSV))
    x_range, y_range = data_ranges(df)
    p = create_figure(x_range, y_range)
    return df, x_range, y_range, p, add_reference_glyphs(p, df)


class TestHoverAndRanges:
    def test_every_object_is_inside_the_default_view(self, built):
        df, x_range, y_range, *_ = built
        assert x_range[0] < min(q.value for q in df.Time_min) and max(q.value for q in df.Time_max) < x_range[1]
        assert y_range[0] < min(q.value for q in df.Space_min) and max(q.value for q in df.Space_max) < y_range[1]

    def test_hover_covers_all_shapes_and_skips_hidden_ones(self, built):
        from bokeh.models import HoverTool

        *_, p, _ = built
        hover = [t for t in p.tools if isinstance(t, HoverTool)][-1]
        assert len(hover.renderers) == 3
        assert "@alpha" in hover.filters
        for r in hover.renderers:
            assert {"alpha", "name", "time_label", "space_label", "reference"} <= set(r.data_source.data)

    def test_tooltip_uses_unit_labels(self, built):
        *_, (source, *_rest) = built
        i = source.data["name"].index("Human lifespan")
        assert source.data["time_label"][i].endswith("yr")
        assert source.data["space_label"][i].endswith("L")

    def test_header_links_to_the_colab_notebook(self, tmp_path):
        out = tmp_path / "explorer.html"
        build_explorer(str(CSV), str(out))
        assert (
            "colab.research.google.com/github/MDunitz/timeSpace/blob/main/docs/reference_explorer_colab.ipynb"
            in out.read_text()
        )
