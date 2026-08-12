"""Build the static Bokeh HTML explorer (select + toggle modes).

Generates a standalone HTML file with a Stommel-style log-log diagram, a
dropdown/checkbox filter, and a define-your-own-object panel. All
interactions run via CustomJS (no server). Designed for iframe embedding on
Google Sites. To upgrade to a Bokeh server later, replace the CustomJS
callbacks with Python callbacks.
"""

from bokeh.models import CustomJS, Select, TextInput, Button, Div, CheckboxGroup
from bokeh.layouts import column, row

from .config import CATEGORY_COLORS
from .data import load_reference_objects
from .figure import create_figure
from .sources import add_reference_glyphs, add_custom_glyphs
from .html import write_explorer_html
from .callbacks import (
    CUSTOM_OBJECT_JS,
    TOGGLE_JS,
    CLEAR_TOGGLE_JS,
    SELECT_CAT_JS,
    SELECT_OBJ_JS,
    SELECT_CLEAR_JS,
)


def build_explorer(csv_path, output_path, mode="select"):
    """Build the reference-object explorer as a self-contained HTML page.

    mode : {"select", "toggle"}
        "select" (default) — one category or one object visible at a time
        via dropdowns; picking a new one replaces the last. Includes the
        define-your-own-object panel.
        "toggle" — category CheckboxGroup with accumulate visibility
        (multiple categories on at once) plus an object dropdown to pin an
        individual. Labels are tiered (only the pinned object is labelled;
        the rest are identified on hover), so no label-collision solver is
        needed. See docs/EXPLORER.md.
    """
    df = load_reference_objects(csv_path)

    p = create_figure()

    source, line_source, point_source, label_source, patches = add_reference_glyphs(p, df)
    custom_source, custom_line_source, custom_point_source, custom_label_source = add_custom_glyphs(p)

    # ── Widgets ────────────────────────────────────────────────────
    cat_labels = sorted(CATEGORY_COLORS.keys())
    objects = ["— Select object —"] + sorted(df.FullName.tolist())
    obj_select = Select(title="Or pick an object:", value=objects[0], options=objects, width=280)
    if mode == "toggle":
        cat_checkbox = CheckboxGroup(labels=cat_labels, active=list(range(len(cat_labels))), width=240)
    else:
        categories = ["— Select category —"] + cat_labels
        cat_select = Select(title="Filter by category:", value=categories[0], options=categories, width=220)

    # Custom input fields
    custom_name = TextInput(title="Name:", value="My process", width=180)
    custom_tmin = TextInput(title="Time min (s):", value="1e0", width=120)
    custom_tmax = TextInput(title="Time max (s):", value="1e5", width=120)
    custom_smin = TextInput(title="Space min (m³):", value="1e-6", width=120)
    custom_smax = TextInput(title="Space max (m³):", value="1e0", width=120)
    custom_btn = Button(label="Plot custom object", button_type="primary", width=160)
    clear_btn = Button(label="Clear all", button_type="warning", width=100)

    info_div = Div(
        text="<i>Select a category, an object, or define your own.</i>",
        width=700,
        styles={"font-size": "12px", "color": "#555"},
    )

    # ── Full data as JSON for JS callbacks ─────────────────────────
    full_data = [
        {
            "Name": r.Name,
            "Category": r.Category,
            "geometry": r.geometry,
            "Time_min": r.Time_min.value,
            "Time_max": r.Time_max.value,
            "Space_min": r.Space_min.value,
            "Space_max": r.Space_max.value,
        }
        for _, r in df.iterrows()
    ]

    # ── Toggle mode: category checkboxes + accumulate visibility ───
    if mode == "toggle":
        # Default: all categories on. Bake the initial visible state into
        # the sources (js_on_change does not fire on load). Labels stay
        # hidden — tiered visibility, revealed only on pin/hover.
        n = len(df)
        source.data["alpha"] = [0.30] * n
        source.data["line_alpha"] = [0.7] * n
        line_source.data["alpha"] = [0.7] * n
        point_source.data["alpha"] = [0.6] * n

        toggle_cb = CustomJS(
            args=dict(
                source=source,
                label_source=label_source,
                line_source=line_source,
                point_source=point_source,
                checkbox=cat_checkbox,
                obj_select=obj_select,
                info=info_div,
                data=full_data,
                cats=cat_labels,
            ),
            code=TOGGLE_JS,
        )
        cat_checkbox.js_on_change("active", toggle_cb)
        obj_select.js_on_change("value", toggle_cb)

        clear_toggle_cb = CustomJS(
            args=dict(checkbox=cat_checkbox, obj_select=obj_select),
            code=CLEAR_TOGGLE_JS,
        )
        clear_btn.js_on_click(clear_toggle_cb)

        controls = row(cat_checkbox, obj_select, clear_btn)
        layout = column(controls, info_div, p, sizing_mode="stretch_width")
        header = (
            "<h2>timeSpace — Reference Object Explorer (toggle)</h2>"
            "<p>102 reference objects across 10 categories. Toggle categories with the "
            "checkboxes; pick an object to pin its label. Hover any glyph for details.</p>"
        )
        write_explorer_html(output_path, layout, header)
        return

    # ── JS Callbacks (select mode) ─────────────────────────────────

    # Category selection → show all objects in category
    cat_cb = CustomJS(
        args=dict(
            source=source,
            label_source=label_source,
            line_source=line_source,
            point_source=point_source,
            info=info_div,
            obj_select=obj_select,
            data=full_data,
        ),
        code=SELECT_CAT_JS,
    )
    cat_select.js_on_change("value", cat_cb)

    # Object selection → highlight single object
    obj_cb = CustomJS(
        args=dict(
            source=source,
            label_source=label_source,
            line_source=line_source,
            point_source=point_source,
            info=info_div,
            cat_select=cat_select,
            data=full_data,
        ),
        code=SELECT_OBJ_JS,
    )
    obj_select.js_on_change("value", obj_cb)

    # Custom object button — classifies geometry and renders via
    # the appropriate source (see CUSTOM_OBJECT_JS)
    custom_cb = CustomJS(
        args=dict(
            csrc=custom_source,
            clsrc=custom_label_source,
            clnsrc=custom_line_source,
            cptsrc=custom_point_source,
            tmin=custom_tmin,
            tmax=custom_tmax,
            smin=custom_smin,
            smax=custom_smax,
            cname=custom_name,
            info=info_div,
        ),
        code=CUSTOM_OBJECT_JS,
    )
    custom_btn.js_on_click(custom_cb)

    # Clear button
    clear_cb = CustomJS(
        args=dict(
            source=source,
            label_source=label_source,
            line_source=line_source,
            point_source=point_source,
            csrc=custom_source,
            clsrc=custom_label_source,
            clnsrc=custom_line_source,
            cptsrc=custom_point_source,
            cat_select=cat_select,
            obj_select=obj_select,
            info=info_div,
        ),
        code=SELECT_CLEAR_JS,
    )
    clear_btn.js_on_click(clear_cb)

    # ── Layout ─────────────────────────────────────────────────────
    dropdown_row = row(cat_select, obj_select, clear_btn)
    custom_row = row(custom_name, custom_tmin, custom_tmax, custom_smin, custom_smax, custom_btn)
    layout = column(dropdown_row, custom_row, info_div, p, sizing_mode="stretch_width")

    header = (
        "<h2>timeSpace — Reference Object Explorer</h2>"
        "<p>102 reference objects spanning molecular to planetary scales. "
        "Select a category, pick an individual object, or define your own.</p>"
    )
    write_explorer_html(output_path, layout, header)
