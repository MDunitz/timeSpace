"""Label modes and the numbering behind "Numbers" mode.

In "Numbers" label mode each object is marked with a short number instead
of its name, and the number key beside the plot (see legend.py) lists
number -> name. Numbers run in key order (category, then name), so each
category is a contiguous block.
"""

LABEL_MODES = ["Names", "Numbers", "None"]
NAMES, NUMBERS, NO_LABELS = range(3)


def assign_numbers(df):
    """1-based key number per row: sorted by category, then by name."""
    order = df.sort_values(["Category", "FullName"]).index
    return df.index.map({idx: n for n, idx in enumerate(order, start=1)})
