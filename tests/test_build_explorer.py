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


class TestSelectMode:
    def test_builds_and_has_no_checkbox(self, tmp_path):
        out = tmp_path / "explorer.html"
        build_explorer(str(CSV), str(out))
        html = out.read_text()
        assert "<html" in html.lower()
        assert "CheckboxGroup" not in html  # select mode uses dropdowns


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
        assert "lal[i] = isSel" in toggle_html


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
