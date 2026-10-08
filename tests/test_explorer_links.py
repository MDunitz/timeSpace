"""Tests for explorer/links.py: identifier-to-URL rules for Reference text."""

import pandas as pd
import pytest

from timeSpace.explorer.links import identifier_urls, linkify_reference

CSV = "data/datasets/time_space_reference_objects.csv"


@pytest.mark.parametrize(
    "text, url",
    [
        ("rate (BioNumbers 111975) x", "https://bionumbers.hms.harvard.edu/bionumber.aspx?id=111975"),
        ("see doi:10.1098/rsbl.2010.1084; next", "https://doi.org/10.1098/rsbl.2010.1084"),
        ("height (arXiv:2501.10600) = 22 m", "https://arxiv.org/abs/2501.10600"),
        ("Mouli et al. (PMC2711405)", "https://pmc.ncbi.nlm.nih.gov/articles/PMC2711405"),
    ],
)
def test_each_identifier_kind_maps_to_its_url(text, url):
    assert identifier_urls(text) == [url]
    assert f'href="{url}"' in linkify_reference(text)


def test_text_without_identifiers_is_only_escaped():
    assert linkify_reference("depth <5 m & rising (Britannica)") == "depth &lt;5 m &amp; rising (Britannica)"


def test_several_identifiers_keep_their_order():
    urls = identifier_urls("a (BioNumbers 101904) b (BioNumbers 100662)")
    assert [u[-6:] for u in urls] == ["101904", "100662"]


def test_csv_identifiers_all_link():
    """Every identifier present in the shipped CSV is picked up."""
    refs = pd.read_csv(CSV).Reference.dropna()
    assert refs.str.count(r"BioNumbers \d+|doi:10\.|arXiv:\d|PMC\d").sum() == sum(len(identifier_urls(r)) for r in refs)
