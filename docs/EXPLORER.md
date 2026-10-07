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

Both modes share one visibility rule: a `CheckboxGroup` of the 10
categories with **accumulate** semantics (any combination can be on at
once), plus an object dropdown that **pins** one individual on top (shown
even if its category is off). Visibility is recomputed from the widget
state on every change and the callback never writes back to a widget, so
ticking categories and pinning an object do not reset each other.

### `mode="select"` (default)

Starts empty. Tick categories to layer them, pin an object, or define and
plot a custom object in the panel. When exactly one category is ticked its
objects are labelled; with several on, only the pinned object is labelled.

### `mode="toggle"`

Starts with every category on and has no custom-object panel. Use this to
compare whole categories and see how groups distribute across time and
space.

Labels are **tiered**: with more than one category on, only a pinned object
gets a text label; every other visible object is identified on hover. Because label density is
capped by what the viewer turns on (not by the full 102-object set), the
toggle view needs no label-collision placement (see issue #6 for why the
solver is unusable at full density).
