"""Numbered labels and their side key.

In "Numbers" label mode each object is marked with a short number instead
of its name, and a key beside the plot lists number -> name grouped by
category. Numbers run in key order (category, then name), so each
category is a contiguous block.
"""

import html

from .config import CATEGORY_COLORS

LABEL_MODES = ["Names", "Numbers", "None"]
NAMES, NUMBERS, NO_LABELS = range(3)

KEY_WIDTH = 270
KEY_STYLES = {"font-size": "12px", "line-height": "1.4", "max-height": "640px", "overflow-y": "auto"}


def assign_numbers(df):
    """1-based key number per row: sorted by category, then by name."""
    order = df.sort_values(["Category", "FullName"]).index
    return df.index.map({idx: n for n, idx in enumerate(order, start=1)})


def key_header(category):
    """Key heading for one category, in that category's plot colour."""
    return f'<div style="margin-top:6px;font-weight:bold;color:{CATEGORY_COLORS[category]}">{category}</div>'


def key_line(number, name):
    """One key entry: the number as drawn on the plot, then the object name."""
    return f'<div><b style="display:inline-block;min-width:26px">{number}</b>{html.escape(name)}</div>'


def key_html(df, categories):
    """Full key for the rows of `df` whose category is in `categories`."""
    parts = []
    for cat in categories:
        rows = df[df.Category == cat].sort_values("Number")
        if len(rows):
            parts.append(key_header(cat) + "".join(rows.KeyLine))
    return "".join(parts)
