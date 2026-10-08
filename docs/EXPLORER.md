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
plot a custom object in the panel. Labels start on "Names".

### `mode="toggle"`

Starts with every category on and has no custom-object panel; labels
start on "Numbers" with the full key beside the plot. Use this to
compare whole categories and see how groups distribute across time and
space.

Source links: clicking a shape pins it (where shapes overlap, the one
spanning the fewest decades is chosen). The info panel then shows the pinned
object's source, with BioNumbers, DOI, arXiv and PubMed Central identifiers
as links. The hover tooltip shows the same text but follows the cursor, so
it cannot hold clickable links. Below the citation, "Source pages" lists the
row's `Reference_URL` entries by host name: pages that were fetched and
checked against the citation (see `CONVENTIONS.md`).

Labels: the pinned object is always labelled by name. A three-way
"Labels" control sets how every other visible object is marked:

- **Names**: the object name, on a translucent white plate.
- **Numbers**: a short number on a white plate bordered in the category
  colour, with a key beside the plot listing number and name for whatever
  is showing, grouped by category. Numbers are fixed (category, then name),
  so an object keeps its number as categories are toggled.
- **None**: no labels; objects are identified on hover.

There is no label-collision placement (see issue #6), so labels overlap
when many objects are showing. The category checkboxes carry each
category's plot colour, so they double as the colour key.
