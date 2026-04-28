"""
Smoke test for a built timeSpace package.

Run after installing from sdist/wheel (not editable mode):
    make test-package

Generates test_stommel.html — an embeddable Stommel diagram.

NOTE: Imports inside `main()` are intentional — verifying that the public
API is importable post-install (and capturing SyntaxWarnings during
`from timeSpace import constants`) is what this test does. Do not move
them to module level.
"""

import sys
import warnings


def main():
    errors = []

    # ── Version and root ─────────────────────────────────────────────
    import timeSpace

    print(f"timeSpace {timeSpace.__version__}")
    print(f"Installed at: {timeSpace.PROJECT_ROOT}")

    # ── Public API imports ───────────────────────────────────────────
    try:
        from timeSpace import (
            create_space_time_figure,
            add_magnitude_labels,
            add_processes,
            add_predefined_processes,
            add_diffusion_lines,
            add_light_cone,
            add_legend,
            create_ellipse_data,
            calculate_diffusion_length,
            calculate_sphere_volume,
            classify_process_geometry,
            transform_process_response_sheet,
            transform_predefined_processes,
            transform_measurement_sheet,
            add_measurements,
            add_grouped_measurement,
            resolve_label_overlaps,
            count_overlaps,
            extract_google_sheet,
        )

        print("Public API: 19 functions imported OK")
    except ImportError as e:
        errors.append(f"Import error: {e}")

    # ── Bundled CSV data ─────────────────────────────────────────────
    csv_dir = timeSpace.PROJECT_ROOT / "data" / "datasets"
    csvs = sorted(csv_dir.glob("*.csv"))
    print(f"CSV files: {len(csvs)}")
    if len(csvs) < 11:
        errors.append(f"Expected at least 11 CSVs, got {len(csvs)}")

    # ── No SyntaxWarning on import ───────────────────────────────────
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        from timeSpace import constants

        syntax_warns = [x for x in w if issubclass(x.category, SyntaxWarning)]
        if syntax_warns:
            errors.append(f"SyntaxWarnings: {syntax_warns}")
        else:
            print("No SyntaxWarnings")

    # ── Build diagram using library functions ─────────────────────────
    import pandas as pd

    df = pd.read_csv(csv_dir / "stommel_boyd2015_volumes.csv")
    transformed = transform_predefined_processes(df, space_on_x=False)
    print(f"Loaded {len(transformed)} processes")

    p = create_space_time_figure(width=1200, height=700, space_on_x=False)
    p = add_magnitude_labels(p, font_size="10pt", space_on_x=False)
    p = add_diffusion_lines(p, space_on_x=False)
    p = add_predefined_processes(p, transformed, interactive=False, font_size="9pt", space_on_x=False)
    p = add_legend(p, position="above", font_size="9pt")
    print("Built Stommel diagram OK")

    # ── Save embeddable HTML ─────────────────────────────────────────
    from bokeh.embed import components
    from bokeh.resources import CDN

    script, div = components(p)
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>timeSpace Stommel Diagram</title>
    {CDN.render()}
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            margin: 0; padding: 16px; background: #fff;
        }}
        .bk-root {{ max-width: 100%; }}
    </style>
</head>
<body>
    {div}
    {script}
</body>
</html>"""

    with open("test_stommel.html", "w") as f:
        f.write(html)
    print("Saved: test_stommel.html (embeddable)")

    # ── Result ───────────────────────────────────────────────────────
    if errors:
        print(f"\nFAILED — {len(errors)} errors:")
        for e in errors:
            print(f"  {e}")
        return 1
    else:
        print("\nAll checks passed. Open test_stommel.html in a browser to verify.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
