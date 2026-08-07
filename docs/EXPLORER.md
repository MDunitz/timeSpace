# Reference-object explorer

The `timeSpace.explorer` subpackage renders the 102 reference objects
(`data/datasets/time_space_reference_objects.csv`, 10 categories) as a
self-contained HTML page for GitHub Pages / iframe embedding.
`docs/build_explorer.py` is a thin CLI shim over it.

```python
from timeSpace.explorer import build_explorer

build_explorer("data/datasets/time_space_reference_objects.csv", "docs/explorer.html")               # select mode
build_explorer("data/datasets/time_space_reference_objects.csv", "docs/explorer_toggle.html", mode="toggle")
```

Running the script directly builds both pages.

## Modes

The `mode` argument controls how the viewer chooses what to display.

### `mode="select"` (default)

Single-select reveal. Everything starts hidden; the viewer picks **one**
category **or** **one** object from a dropdown, and picking a new value
replaces the previous one. Also includes a panel to define and plot a
custom object. Use this when the goal is to inspect items one at a time
against the reference grid.

### `mode="toggle"`

Multi-toggle. A `CheckboxGroup` of the 10 categories drives visibility
with **accumulate** semantics — any combination of categories can be on
at once. An object dropdown additionally **pins** one individual (shown
even if its category is off). Use this to compare whole categories and
see how groups distribute across time and space.

Labels are **tiered**: only a pinned object gets a text label; every
other visible object is identified on hover. Because label density is
capped by what the viewer turns on (not by the full 102-object set), the
toggle view needs no label-collision placement (see issue #6 for why the
solver is unusable at full density).
