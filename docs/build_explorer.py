"""Thin CLI shim for the reference-object explorer.

The implementation now lives in the importable ``timeSpace.explorer``
subpackage (see #67). This file is kept as the command-line entry point and
the GitHub Pages build hook:

    python docs/build_explorer.py <csv_path> <output_html>
"""

from timeSpace.explorer import build_explorer  # noqa: F401  (re-exported for callers)

if __name__ == "__main__":
    import sys

    csv_path = sys.argv[1] if len(sys.argv) > 1 else "data/datasets/time_space_reference_objects.csv"
    output_path = sys.argv[2] if len(sys.argv) > 2 else "docs/explorer.html"
    build_explorer(csv_path, output_path)
    build_explorer(csv_path, output_path.replace(".html", "_toggle.html"), mode="toggle")
