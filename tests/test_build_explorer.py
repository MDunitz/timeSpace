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

        assert "pin_choice.value =" not in VISIBILITY_JS
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

    def test_label_mode_marker(self, toggle_html):
        # pinned object always named; the rest follow the label mode
        assert "mode === NAMES" in toggle_html and "mode === NUMBERS" in toggle_html
        assert "label_mode.active" in toggle_html

    def test_has_label_modes_and_colour_key(self, toggle_html):
        assert "RadioButtonGroup" in toggle_html
        assert "nth-of-type(10) span::before" in toggle_html


@pytest.fixture(scope="module")
def df():
    from timeSpace.explorer.data import load_reference_objects

    return load_reference_objects(str(CSV))


class TestNumberedLabelsAndKey:
    def test_numbers_are_unique_and_contiguous_within_category(self, df):
        assert sorted(df.Number) == list(range(1, len(df) + 1))
        for _, rows in df.groupby("Category"):
            nums = sorted(rows.Number)
            assert nums == list(range(nums[0], nums[0] + len(nums)))
            assert list(rows.sort_values("Number").FullName) == sorted(rows.FullName)

    def test_key_lists_only_requested_categories_in_number_order(self, df):
        from timeSpace.explorer.key import key_html

        html = key_html(df, ["Cellular", "Ocean"])
        assert "Cellular" in html and "Ocean" in html and "Planetary" not in html
        cellular = df[df.Category == "Cellular"].sort_values("Number")
        positions = [html.index(line) for line in cellular.KeyLine]
        assert positions == sorted(positions)

    def test_both_pages_start_in_names_mode(self, toggle_html, select_html):
        for html in (toggle_html, select_html):
            compact = html.replace(" ", "")
            i = compact.index('"labels":["Names","Numbers","None"]')
            group = compact[compact.rindex("{", 0, i) : compact.index("}", i)]
            assert '"active":0' in group or '"active"' not in group

    def test_toggle_page_starts_without_a_baked_key(self, toggle_html):
        # category headings appear once each (callback argument), not a second
        # time inside a pre-filled key
        assert toggle_html.count("margin-top:6px;font-weight:bold") == 10

    def test_select_page_starts_in_names_mode_with_key_hidden(self, select_html):
        assert '"labels":["Names","Numbers","None"]' in select_html.replace(" ", "")


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


class TestTapToPinAndSourceLinks:
    @pytest.mark.parametrize("fixture", ["select_html", "toggle_html"])
    def test_page_has_tap_tool_and_identifier_links(self, fixture, request):
        html = request.getfixturevalue(fixture)
        assert "TapTool" in html
        assert "pin_choice.value = pins.concat([name])" in html
        assert "MultiChoice" in html
        assert "bionumbers.hms.harvard.edu/bionumber.aspx?id=111975" in html

    def test_tap_does_not_dim_other_shapes(self):
        from timeSpace.explorer.data import load_reference_objects
        from timeSpace.explorer.figure import create_figure
        from timeSpace.explorer.sources import add_reference_glyphs

        *_, shapes = add_reference_glyphs(create_figure(), load_reference_objects(str(CSV)))
        assert len(shapes) == 3
        assert all(r.nonselection_glyph is None and r.selection_glyph is None for r in shapes)


class TestPinsAccumulate:
    def test_tap_adds_to_pins_and_never_replaces_them(self):
        from timeSpace.explorer.callbacks import TAP_PIN_JS

        assert "pin_choice.value = pins.concat([name])" in TAP_PIN_JS
        assert "pin_choice.value = data" not in TAP_PIN_JS

    def test_only_clear_empties_the_pins(self):
        from timeSpace.explorer import callbacks

        assert "pin_choice.value = [];" in callbacks.CLEAR_TOGGLE_JS
        assert "pin_choice.value = [];" in callbacks.SELECT_CLEAR_JS
        assert "pin_choice.value = [];" not in callbacks.VISIBILITY_JS

    def test_panel_lists_every_pinned_object(self):
        from timeSpace.explorer.callbacks import VISIBILITY_JS

        assert "Also pinned:" in VISIBILITY_JS


class TestMarkerAxes:
    def test_marker_names_live_on_axes_outside_the_frame(self):
        from bokeh.models import Label, LogAxis

        from timeSpace.constants import SPACE_MARKERS, TIME_MARKERS
        from timeSpace.explorer.figure import create_figure

        p = create_figure()
        assert not [r for r in p.center if isinstance(r, Label)]
        (top,) = [a for a in p.above if isinstance(a, LogAxis)]
        (right,) = [a for a in p.right if isinstance(a, LogAxis)]
        assert sorted(top.ticker.ticks) == sorted(TIME_MARKERS)
        assert sorted(right.ticker.ticks) == sorted(SPACE_MARKERS)
        assert top.major_label_overrides[8.64e4] == "Day"
        assert set(right.major_label_overrides.values()) == set(SPACE_MARKERS.values())
