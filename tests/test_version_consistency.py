"""Guard against version drift between pyproject.toml and CITATION.cff.

The package version (pyproject.toml [project].version) and the citable
version (CITATION.cff version:) must agree so that what a user installs
matches what they are told to cite. #57 documented three-way drift
(pyproject 0.2.0, PyPI 0.1.0, CITATION 0.1.0); this test locks the two
in-repo sources together.
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _pyproject_version() -> str:
    text = (ROOT / "pyproject.toml").read_text()
    match = re.search(r'^\s*version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    assert match, "no [project].version found in pyproject.toml"
    return match.group(1).strip()


def _citation_version() -> str:
    text = (ROOT / "CITATION.cff").read_text()
    match = re.search(r'^version:\s*"?([^"\n]+?)"?\s*$', text, re.MULTILINE)
    assert match, "no version: field found in CITATION.cff"
    return match.group(1).strip()


def test_pyproject_and_citation_versions_match():
    assert _pyproject_version() == _citation_version(), (
        f"version drift: pyproject={_pyproject_version()!r} " f"CITATION.cff={_citation_version()!r}"
    )
