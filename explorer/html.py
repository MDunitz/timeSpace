"""Serialise a Bokeh layout into a self-contained explorer HTML page."""

from bokeh.resources import CDN
from bokeh.embed import components


def write_explorer_html(output_path, layout, header_html):
    """Serialise a Bokeh layout into a self-contained explorer page.

    Uses components() + a hand-rolled wrapper to avoid the Bokeh 3
    sanitizer stripping <script> from Div content (issue #89).
    """
    script, div = components(layout)
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>timeSpace Reference Object Explorer</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    {CDN.render()}
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            margin: 0;
            padding: 16px;
            background: #fff;
        }}
        .header {{
            max-width: 820px;
            margin: 0 auto 8px auto;
        }}
        .header h2 {{
            margin: 0 0 4px 0;
            font-size: 18px;
            color: #333;
        }}
        .header p {{
            margin: 0;
            font-size: 13px;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="header">
        {header_html}
    </div>
    {div}
    {script}
</body>
</html>"""
    with open(output_path, "w") as f:
        f.write(html)
    print(f"Built {output_path} ({len(html):,} bytes)")
