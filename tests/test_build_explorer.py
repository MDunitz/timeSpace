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
