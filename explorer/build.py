"""Build the static Bokeh HTML explorer (select + toggle modes).

Generates a standalone HTML file with a Stommel-style log-log diagram, a
dropdown/checkbox filter, and a define-your-own-object panel. All
interactions run via CustomJS (no server). Designed for iframe embedding on
Google Sites. To upgrade to a Bokeh server later, replace the CustomJS
callbacks with Python callbacks.
"""

from bokeh.models import (
    CustomJS,
    MultiChoice,
    TextInput,
    Button,
    Div,
    CheckboxGroup,
    InlineStyleSheet,
    TapTool,
    RadioButtonGroup,
)
from bokeh.layouts import column, row

from .config import CATEGORY_COLORS, DIY_LINKS_HTML
from .data import data_ranges, load_reference_objects
from .figure import create_figure
from .sources import NAME_PLATE_ALPHA, NUMBER_PLATE_OPACITY, add_reference_glyphs, add_custom_glyphs
from .html import write_explorer_html
from .key import KEY_STYLES, KEY_WIDTH, LABEL_MODES, NAMES, key_header
from .callbacks import (
    CUSTOM_OBJECT_JS,
    VISIBILITY_JS,
    CLEAR_TOGGLE_JS,
    SELECT_CLEAR_JS,
    TAP_PIN_JS,
)


def category_key_stylesheet(cat_labels):
    """Stylesheet that puts each category's plot colour beside its checkbox.

    The checkbox row doubles as the colour key, so the key always matches
    the order and names of the controls.
    """
    rules = [
        f".bk-input-group label:nth-of-type({i}) span::before "
        f'{{ content: "■"; color: {CATEGORY_COLORS[cat]}; font-size: 15px; margin-right: 3px; }}'
        for i, cat in enumerate(cat_labels, start=1)
    ]
    return InlineStyleSheet(css="\n".join(rules))


def build_explorer(csv_path, output_path, mode="select"):
    """Build the reference-object explorer as a self-contained HTML page.

    Both modes drive visibility from a category CheckboxGroup (categories
    accumulate) plus an object dropdown that pins one individual on top.

    mode : {"select", "toggle"}
        "select" (default) — starts empty; includes the define-your-own-object
        panel. A single checked category is labelled; with several on, only
        the pinned object is labelled and the rest are identified on hover.
        "toggle" — starts with every category on; only the pinned object is
        labelled. No custom-object panel. See docs/EXPLORER.md.
    """
    df = load_reference_objects(csv_path)

    p = create_figure(*data_ranges(df))

    source, line_source, point_source, label_source, shapes = add_reference_glyphs(p, df)
    custom_source, custom_line_source, custom_point_source, custom_label_source = add_custom_glyphs(p)

    # ── Widgets ────────────────────────────────────────────────────
    cat_labels = sorted(CATEGORY_COLORS.keys())
    toggle = mode == "toggle"
    # Pins accumulate: each stays until its chip is removed or "Clear all".
    pin_choice = MultiChoice(
        title="Pinned objects (click shapes or pick here; they stay until removed):",
        value=[],
        options=sorted(df.FullName.tolist()),
        placeholder="Pick objects to pin",
        width=420,
    )
    key = category_key_stylesheet(cat_labels)
    if toggle:
        cat_checkbox = CheckboxGroup(
            labels=cat_labels, active=list(range(len(cat_labels))), width=240, stylesheets=[key]
        )
    else:
        cat_checkbox = CheckboxGroup(labels=cat_labels, active=[], inline=True, stylesheets=[key])
    # Both modes start on names; Numbers (with the side key) and None are a
    # click away when many objects are showing.
    label_mode = RadioButtonGroup(labels=LABEL_MODES, active=NAMES, width=210)
    label_title = Div(text="Labels:", styles={"font-size": "13px", "padding-top": "6px"})
    key_div = Div(text="", width=KEY_WIDTH, visible=False, styles=KEY_STYLES)
    cat_title = Div(
        text="Categories (tick any number to layer them; the square is each one's colour on the plot):",
        styles={"font-size": "13px"},
    )

    # Custom input fields
    custom_name = TextInput(title="Name:", value="My process", width=180)
    custom_tmin = TextInput(title="Time min (s):", value="1e0", width=120)
    custom_tmax = TextInput(title="Time max (s):", value="1e5", width=120)
    custom_smin = TextInput(title="Space min (m³):", value="1e-6", width=120)
    custom_smax = TextInput(title="Space max (m³):", value="1e0", width=120)
    custom_btn = Button(label="Plot custom object", button_type="primary", width=160)
    clear_btn = Button(label="Clear all", button_type="warning", width=100)

    empty_text = (
        "<i>Tick one or more categories, pin objects, or define your own. "
        "Click any shape to pin it and see its source.</i>"
    )
    info_div = Div(
        text=empty_text,
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
            "ReferenceHtml": r.ReferenceHtml,
            "Number": int(r.Number),
            "KeyLine": r.KeyLine,
            "TimeLabel": r.TimeLabel,
            "SpaceLabel": r.SpaceLabel,
        }
        for _, r in df.iterrows()
    ]

    # ── Visibility: one callback recomputes from widget state ──────
    visibility_cb = CustomJS(
        args=dict(
            source=source,
            label_source=label_source,
            line_source=line_source,
            point_source=point_source,
            checkbox=cat_checkbox,
            pin_choice=pin_choice,
            info=info_div,
            data=full_data,
            cats=cat_labels,
            label_mode=label_mode,
            key=key_div,
            key_headers={c: key_header(c) for c in cat_labels},
            name_plate_alpha=NAME_PLATE_ALPHA,
            number_plate_alpha=NUMBER_PLATE_OPACITY,
            empty_text=empty_text,
        ),
        code=VISIBILITY_JS,
    )
    cat_checkbox.js_on_change("active", visibility_cb)
    pin_choice.js_on_change("value", visibility_cb)
    label_mode.js_on_change("active", visibility_cb)

    # ── Tap a shape to pin it (source links live in the info panel) ─
    p.add_tools(TapTool(renderers=shapes))
    for src in (source, line_source, point_source):
        src.selected.js_on_change(
            "indices", CustomJS(args=dict(src=src, pin_choice=pin_choice, data=full_data), code=TAP_PIN_JS)
        )

    # ── Toggle mode: starts with every category on ─────────────────
    if toggle:
        # Default: all categories on. Bake the initial visible state into
        # the sources (js_on_change does not fire on load): every object
        # shown and labelled by name.
        n = len(df)
        info_div.text = (
            f"<b>{n}</b> objects shown across {len(cat_labels)} categories. "
            "Click an object to pin it and see its source."
        )
        label_source.data["alpha"] = [1.0] * n
        label_source.data["plate_alpha"] = [NAME_PLATE_ALPHA] * n
        source.data["alpha"] = [0.30] * n
        source.data["line_alpha"] = [0.7] * n
        line_source.data["alpha"] = [0.7] * n
        point_source.data["alpha"] = [0.6] * n

        clear_toggle_cb = CustomJS(
            args=dict(checkbox=cat_checkbox, pin_choice=pin_choice),
            code=CLEAR_TOGGLE_JS,
        )
        clear_btn.js_on_click(clear_toggle_cb)

        controls = row(cat_checkbox, pin_choice, label_title, label_mode, clear_btn)
        layout = column(controls, info_div, row(p, key_div, sizing_mode="stretch_width"), sizing_mode="stretch_width")
        header = (
            "<h2>timeSpace — Reference Object Explorer (toggle)</h2>"
            "<p>102 reference objects across 10 categories. Toggle categories with the "
            "checkboxes. Switch Labels to Numbers for a numbered key beside the plot, or to "
            "None to hide them. Click or pick objects to pin them; pins stay until removed. " + DIY_LINKS_HTML + "</p>"
        )
        write_explorer_html(output_path, layout, header)
        return

    # ── Select mode: custom-object panel and clear ─────────────────

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
            csrc=custom_source,
            clsrc=custom_label_source,
            clnsrc=custom_line_source,
            cptsrc=custom_point_source,
            checkbox=cat_checkbox,
            pin_choice=pin_choice,
            info=info_div,
            empty_text=empty_text,
        ),
        code=SELECT_CLEAR_JS,
    )
    clear_btn.js_on_click(clear_cb)

    # ── Layout ─────────────────────────────────────────────────────
    pin_row = row(pin_choice, label_title, label_mode, clear_btn)
    custom_row = row(custom_name, custom_tmin, custom_tmax, custom_smin, custom_smax, custom_btn)
    plot_row = row(p, key_div, sizing_mode="stretch_width")
    layout = column(cat_title, cat_checkbox, pin_row, custom_row, info_div, plot_row, sizing_mode="stretch_width")

    header = (
        "<h2>timeSpace — Reference Object Explorer</h2>"
        "<p>102 reference objects spanning molecular to planetary scales. "
        "Tick categories to layer them, pin individual objects, or define your own. " + DIY_LINKS_HTML + "</p>"
    )
    write_explorer_html(output_path, layout, header)
