"""
Build a static Bokeh HTML page for the timeSpace reference object explorer.

Generates a standalone HTML file with:
- Stommel-style log-log diagram (Time × Space)
- Dropdown to filter by category or select individual reference objects
- Text inputs for user-defined custom object
- All interactions via CustomJS (no server required)

Designed for embedding on Google Sites via iframe.
To upgrade to Bokeh server later: replace CustomJS callbacks with Python callbacks.
"""

import pandas as pd
import numpy as np
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, CustomJS, Select, TextInput, Button, Div, Span, Label, HoverTool
from bokeh.layouts import column, row
from bokeh.resources import CDN
from bokeh.embed import components

from timeSpace.constants import TIME_MARKERS, SPACE_MARKERS
from timeSpace.calculations import create_ellipse_data, classify_process_geometry
from timeSpace.etl import process_magnitude_column

# ── Configuration ──────────────────────────────────────────────────
# Match main figure axis ranges (from plotting.py's create_space_time_figure)
# TODO: move to constants.py so plotting.py and the explorer share a single source
X_RANGE = (1e-3, 1e12)
Y_RANGE = (1e-22, 1e20)

# Number of vertices per half-ellipse for reference objects.
# Main figure uses 1000; 100 keeps the static HTML under 1 MB of data
# while still rendering smooth curves on a log-log plot.
EXPLORER_N_POINTS = 100

# Category colors — explorer-specific (main figure uses per-process colors from CSV)
CATEGORY_COLORS = {
    "Molecular": "#33CCCC",
    "Cellular": "#009999",
    "Organism": "#0F793D",
    "Ecosystem": "#6ABD45",
    "Ocean": "#006666",
    "Atmosphere": "#99CC33",
    "Geographic": "#669933",
    "Geological": "#CC9933",
    "Human-built": "#FF9900",
    "Planetary": "#996600",
}

FONT_SIZE = "11pt"
LABEL_FONT_SIZE = "9pt"


# ── Data loading ───────────────────────────────────────────────────


def load_reference_objects(csv_path):
    """Read reference objects CSV and generate render coordinates.

    Classifies each object's geometry (ellipse/vline/hline/point) and only
    generates ellipse polygon data for true ellipses.  Degenerate axes are
    flagged so the rendering layer can use lines or point markers.

    Applies astropy units (seconds, m³) to match the package's ETL pipeline,
    then calls create_ellipse_data from timeSpace.calculations.
    """
    df = pd.read_csv(csv_path)

    # Apply units — same function as etl.py pipeline
    for col in ["Time_min", "Time_max", "Space_min", "Space_max"]:
        df[col] = df.apply(process_magnitude_column, column=col, axis=1)

    # Classify geometry before generating coords
    df["geometry"] = df.apply(classify_process_geometry, axis=1)

    # Only generate ellipse data for actual ellipses
    ellipse_mask = df["geometry"] == "ellipse"
    df.loc[ellipse_mask, ["x_coords", "y_coords"]] = df.loc[
        ellipse_mask, ["Time_min", "Time_max", "Space_min", "Space_max"]
    ].apply(create_ellipse_data, axis=1, result_type="expand", n_points=EXPLORER_N_POINTS, space_on_x=False)

    df["color"] = df.Category.map(CATEGORY_COLORS)

    # Center position for labels (geometric mean in log space)
    df["label_x"] = np.sqrt(df.Time_min.apply(lambda q: q.value) * df.Time_max.apply(lambda q: q.value))
    df["label_y"] = np.sqrt(df.Space_min.apply(lambda q: q.value) * df.Space_max.apply(lambda q: q.value))

    return df


# ── Figure construction ───────────────────────────────────────────


def create_figure():
    p = figure(
        width=800,
        height=550,
        x_axis_type="log",
        y_axis_type="log",
        x_axis_label="Time (s)",
        y_axis_label="Space (m³)",
        x_range=X_RANGE,
        y_range=Y_RANGE,
        title="Stommel Diagram — Reference Object Explorer",
        toolbar_location="above",
        tools="pan,wheel_zoom,box_zoom,reset",
    )
    p.axis.axis_label_text_font_size = FONT_SIZE
    p.axis.major_label_text_font_size = "10pt"
    p.title.text_font_size = "14pt"
    p.background_fill_color = "#fafafa"

    # Reference grid lines
    for t, label_text in TIME_MARKERS.items():
        p.add_layout(Span(location=t, dimension="height", line_color="#cccccc", line_dash="dashed", line_width=1))
        p.add_layout(
            Label(
                x=t,
                y=Y_RANGE[1],
                text=label_text,
                text_font_size=LABEL_FONT_SIZE,
                text_color="#aaaaaa",
                text_align="center",
                text_baseline="top",
            )
        )

    for s, label_text in SPACE_MARKERS.items():
        p.add_layout(Span(location=s, dimension="width", line_color="#dddddd", line_dash="dashed", line_width=1))
        p.add_layout(
            Label(
                y=s,
                x=X_RANGE[0] * 1.5,
                text=label_text,
                text_font_size=LABEL_FONT_SIZE,
                text_color="#aaaaaa",
                text_align="left",
            )
        )

    return p


# ── JS code for custom object (browser-side) ─────────────────
# Classifies geometry (ellipse/vline/hline/point) and renders using
# the appropriate data source.  Ellipse math replicates the same
# algorithm as timeSpace.calculations.create_ellipse_data.

CUSTOM_OBJECT_JS = """
    function esc(s) {
        return String(s).replace(/[&<>"']/g, function(c) {
            return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":"&#39;"}[c];
        });
    }
    const t0 = parseFloat(tmin.value);
    const t1 = parseFloat(tmax.value);
    const s0 = parseFloat(smin.value);
    const s1 = parseFloat(smax.value);
    if (isNaN(t0) || isNaN(t1) || isNaN(s0) || isNaN(s1) ||
        t0 <= 0 || t1 <= 0 || s0 <= 0 || s1 <= 0) {
        info.text = '<span style="color:red">Enter positive numbers (scientific notation OK, e.g. 1e-3)</span>';
        return;
    }

    // Classify geometry: detect degenerate axes (min ≈ max in log10 space)
    const DEGEN_THRESH = 1e-10;
    const t_degen = Math.abs(Math.log10(t1) - Math.log10(t0)) < DEGEN_THRESH;
    const s_degen = Math.abs(Math.log10(s1) - Math.log10(s0)) < DEGEN_THRESH;

    // Clear all custom renderers first
    csrc.data['xs'] = [[]];
    csrc.data['ys'] = [[]];
    csrc.data['alpha'] = [0.0];
    csrc.data['line_alpha'] = [0.0];
    clnsrc.data['xs'] = [[]];
    clnsrc.data['ys'] = [[]];
    clnsrc.data['alpha'] = [0.0];
    cptsrc.data['x'] = [NaN];
    cptsrc.data['y'] = [NaN];
    cptsrc.data['alpha'] = [0.0];

    let label_x, label_y;

    if (t_degen && s_degen) {
        // Point — both axes degenerate
        cptsrc.data['x'] = [t0];
        cptsrc.data['y'] = [s0];
        cptsrc.data['alpha'] = [0.8];
        label_x = t0;
        label_y = s0;
    } else if (t_degen) {
        // Vertical line — time degenerate, space has range
        clnsrc.data['xs'] = [[t0, t0]];
        clnsrc.data['ys'] = [[s0, s1]];
        clnsrc.data['alpha'] = [1.0];
        label_x = t0;
        label_y = Math.pow(10, (Math.log10(s0) + Math.log10(s1)) / 2);
    } else if (s_degen) {
        // Horizontal line — space degenerate, time has range
        clnsrc.data['xs'] = [[t0, t1]];
        clnsrc.data['ys'] = [[s0, s0]];
        clnsrc.data['alpha'] = [1.0];
        label_x = Math.pow(10, (Math.log10(t0) + Math.log10(t1)) / 2);
        label_y = s0;
    } else {
        // Ellipse — both axes have range
        // Same math as timeSpace.calculations.create_ellipse_data:
        //   calculate_log_center: (log10(min) + log10(max)) / 2
        //   calculate_log_width:  (log10(max) - log10(min)) / 2
        //   calculate_log10_y_for_ellipse: solve ellipse equation for y
        const cx = (Math.log10(t0) + Math.log10(t1)) / 2;
        const cy = (Math.log10(s0) + Math.log10(s1)) / 2;
        const a = (Math.log10(t1) - Math.log10(t0)) / 2;
        const b = (Math.log10(s1) - Math.log10(s0)) / 2;

        const n = 100;
        const log_t0 = Math.log10(t0), log_t1 = Math.log10(t1);
        const x_fwd = [], y_plus = [], y_minus = [];
        for (let i = 0; i < n; i++) {
            const log_x = log_t0 + (log_t1 - log_t0) * i / (n - 1);
            const x = Math.pow(10, log_x);
            x_fwd.push(x);
            const inner = (log_x - cx) / a;
            const disc = Math.max(0, 1 - inner * inner);
            y_plus.push(Math.pow(10, cy + b * Math.sqrt(disc)));
            y_minus.push(Math.pow(10, cy - b * Math.sqrt(disc)));
        }

        const ex = x_fwd.concat(x_fwd.slice().reverse());
        const ey = y_plus.concat(y_minus.slice().reverse());

        csrc.data['xs'] = [ex];
        csrc.data['ys'] = [ey];
        csrc.data['alpha'] = [0.4];
        csrc.data['line_alpha'] = [1.0];

        label_x = Math.pow(10, cx);
        label_y = Math.pow(10, cy);
    }

    csrc.change.emit();
    clnsrc.change.emit();
    cptsrc.change.emit();

    clsrc.data['x'] = [label_x];
    clsrc.data['y'] = [label_y];
    clsrc.data['text'] = [cname.value];
    clsrc.data['alpha'] = [1.0];
    clsrc.change.emit();

    // Build display text — show exact value on degenerate axes
    let time_str, space_str;
    if (t_degen) {
        time_str = t0.toExponential(1) + ' s (exact)';
    } else {
        time_str = t0.toExponential(1) + ' → ' + t1.toExponential(1) + ' s';
    }
    if (s_degen) {
        space_str = s0.toExponential(1) + ' m³ (exact)';
    } else {
        space_str = s0.toExponential(1) + ' → ' + s1.toExponential(1) + ' m³';
    }
    const geom = (t_degen && s_degen) ? 'point' : t_degen ? 'vline' : s_degen ? 'hline' : 'ellipse';
    info.text = '<b style="color:#E8336D">' + esc(cname.value) + '</b> (custom, ' + geom + ')<br>' +
        'Time: ' + time_str + '<br>' +
        'Space: ' + space_str;
"""


# ── Build the page ─────────────────────────────────────────────────


def build_explorer(csv_path, output_path):
    df = load_reference_objects(csv_path)

    p = create_figure()

    # ── Main reference object patches (ellipses only) ───────────────
    # Non-ellipse objects get empty xs/ys — they render via line/point
    # sources below. Index alignment is preserved so JS callbacks can
    # toggle all sources by the same index.
    def _patch_coords(row):
        if row.geometry == "ellipse":
            return row.x_coords.tolist(), row.y_coords.tolist()
        return [], []

    source = ColumnDataSource(
        data=dict(
            xs=[_patch_coords(row)[0] for _, row in df.iterrows()],
            ys=[_patch_coords(row)[1] for _, row in df.iterrows()],
            color=df.color.tolist(),
            alpha=[0.0] * len(df),  # start hidden
            line_alpha=[0.0] * len(df),
            name=df.Name.tolist(),
            category=df.Category.tolist(),
            time_min=[row.Time_min.value for _, row in df.iterrows()],
            time_max=[row.Time_max.value for _, row in df.iterrows()],
            space_min=[row.Space_min.value for _, row in df.iterrows()],
            space_max=[row.Space_max.value for _, row in df.iterrows()],
        )
    )

    patches = p.patches(
        "xs",
        "ys",
        source=source,
        fill_color="color",
        fill_alpha="alpha",
        line_color="color",
        line_alpha="line_alpha",
        line_width=2,
    )

    # ── Line source for vline/hline objects (index-aligned) ───────
    def _line_coords(row):
        if row.geometry == "vline":
            t = row.Time_min.value
            return [t, t], [row.Space_min.value, row.Space_max.value]
        elif row.geometry == "hline":
            s = row.Space_min.value
            return [row.Time_min.value, row.Time_max.value], [s, s]
        return [], []

    line_source = ColumnDataSource(
        data=dict(
            xs=[_line_coords(row)[0] for _, row in df.iterrows()],
            ys=[_line_coords(row)[1] for _, row in df.iterrows()],
            color=df.color.tolist(),
            alpha=[0.0] * len(df),
        )
    )

    p.multi_line(
        "xs",
        "ys",
        source=line_source,
        line_color="color",
        line_alpha="alpha",
        line_width=2.5,
    )

    # ── Point source for fully degenerate objects (index-aligned) ─
    point_source = ColumnDataSource(
        data=dict(
            x=[row.Time_min.value if row.geometry == "point" else float("nan") for _, row in df.iterrows()],
            y=[row.Space_min.value if row.geometry == "point" else float("nan") for _, row in df.iterrows()],
            color=df.color.tolist(),
            alpha=[0.0] * len(df),
        )
    )

    p.scatter(
        "x",
        "y",
        source=point_source,
        marker="diamond",
        size=12,
        fill_color="color",
        fill_alpha="alpha",
        line_color="color",
        line_width=1.5,
    )

    # Hover only on patches renderer (not text glyphs or custom source)
    hover = HoverTool(
        renderers=[patches],
        tooltips=[
            ("Name", "@name"),
            ("Category", "@category"),
            ("Time", "@time_min{%0.1e} → @time_max{%0.1e} s"),
            ("Space", "@space_min{%0.1e} → @space_max{%0.1e} m³"),
        ],
        formatters={
            "@time_min": "printf",
            "@time_max": "printf",
            "@space_min": "printf",
            "@space_max": "printf",
        },
    )
    p.add_tools(hover)

    # ── Name labels (hidden until selection) ───────────────────────
    label_source = ColumnDataSource(
        data=dict(
            x=df.label_x.tolist(),
            y=df.label_y.tolist(),
            text=df.Name.tolist(),
            alpha=[0.0] * len(df),
            color=df.color.tolist(),
        )
    )

    p.text(
        "x",
        "y",
        source=label_source,
        text="text",
        text_font_size="8pt",
        text_color="color",
        text_alpha="alpha",
        text_align="center",
        text_baseline="middle",
    )

    # ── Custom user-defined object ─────────────────────────────────
    custom_source = ColumnDataSource(
        data=dict(
            xs=[[1, 1, 1, 1]],
            ys=[[1, 1, 1, 1]],
            alpha=[0.0],
            line_alpha=[0.0],
        )
    )

    p.patches(
        "xs",
        "ys",
        source=custom_source,
        fill_color="#E8336D",
        fill_alpha="alpha",
        line_color="#E8336D",
        line_alpha="line_alpha",
        line_width=3,
    )

    custom_line_source = ColumnDataSource(
        data=dict(
            xs=[[]],
            ys=[[]],
            alpha=[0.0],
        )
    )

    p.multi_line("xs", "ys", source=custom_line_source, line_color="#E8336D", line_alpha="alpha", line_width=3)

    custom_point_source = ColumnDataSource(
        data=dict(
            x=[float("nan")],
            y=[float("nan")],
            alpha=[0.0],
        )
    )

    p.scatter(
        "x",
        "y",
        source=custom_point_source,
        marker="diamond",
        size=14,
        fill_color="#E8336D",
        fill_alpha="alpha",
        line_color="#E8336D",
        line_width=2,
    )

    custom_label_source = ColumnDataSource(
        data=dict(
            x=[1],
            y=[1],
            text=["Custom"],
            alpha=[0.0],
        )
    )

    p.text(
        "x",
        "y",
        source=custom_label_source,
        text="text",
        text_font_size="9pt",
        text_color="#E8336D",
        text_alpha="alpha",
        text_align="center",
        text_baseline="middle",
        text_font_style="bold",
    )

    # ── Widgets ────────────────────────────────────────────────────
    categories = ["— Select category —"] + sorted(CATEGORY_COLORS.keys())
    cat_select = Select(title="Filter by category:", value=categories[0], options=categories, width=220)

    objects = ["— Select object —"] + sorted(df.Name.tolist())
    obj_select = Select(title="Or pick an object:", value=objects[0], options=objects, width=280)

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

    # ── JS Callbacks ───────────────────────────────────────────────

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
        code="""
        function esc(s) {
        return String(s).replace(/[&<>"']/g, function(c) {
            return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":"&#39;"}[c];
        });
    }
    const cat = cb_obj.value;
        const alpha = source.data['alpha'];
        const la = source.data['line_alpha'];
        const lalpha = label_source.data['alpha'];
        const lna = line_source.data['alpha'];
        const pta = point_source.data['alpha'];
        let count = 0;
        const names = [];
        for (let i = 0; i < alpha.length; i++) {
            if (cat !== '— Select category —' && data[i].Category === cat) {
                alpha[i] = 0.35;
                la[i] = 0.8;
                lalpha[i] = 1.0;
                lna[i] = 0.8;
                pta[i] = 0.6;
                count++;
                names.push(data[i].Name);
            } else {
                alpha[i] = 0.0;
                la[i] = 0.0;
                lalpha[i] = 0.0;
                lna[i] = 0.0;
                pta[i] = 0.0;
            }
        }
        source.change.emit();
        label_source.change.emit();
        line_source.change.emit();
        point_source.change.emit();
        obj_select.value = '— Select object —';
        if (cat === '— Select category —') {
            info.text = '<i>Select a category, an object, or define your own.</i>';
        } else {
            info.text = '<b>' + esc(cat) + '</b>: ' + count + ' objects — ' + names.map(esc).join(', ');
        }
    """,
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
        code="""
        function esc(s) {
        return String(s).replace(/[&<>"']/g, function(c) {
            return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":"&#39;"}[c];
        });
    }
    const name = cb_obj.value;
        const alpha = source.data['alpha'];
        const la = source.data['line_alpha'];
        const lalpha = label_source.data['alpha'];
        const lna = line_source.data['alpha'];
        const pta = point_source.data['alpha'];
        for (let i = 0; i < alpha.length; i++) {
            if (name !== '— Select object —' && data[i].Name === name) {
                alpha[i] = 0.5;
                la[i] = 1.0;
                lalpha[i] = 1.0;
                lna[i] = 1.0;
                pta[i] = 0.8;
                const d = data[i];
                info.text = '<b>' + esc(d.Name) + '</b> (' + esc(d.Category) + ')<br>' +
                    'Time: ' + d.Time_min.toExponential(1) + ' → ' + d.Time_max.toExponential(1) + ' s<br>' +
                    'Space: ' + d.Space_min.toExponential(1) + ' → ' + d.Space_max.toExponential(1) + ' m³';
            } else {
                alpha[i] = 0.0;
                la[i] = 0.0;
                lalpha[i] = 0.0;
                lna[i] = 0.0;
                pta[i] = 0.0;
            }
        }
        source.change.emit();
        label_source.change.emit();
        line_source.change.emit();
        point_source.change.emit();
        cat_select.value = '— Select category —';
    """,
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
        code="""
        for (let i = 0; i < source.data['alpha'].length; i++) {
            source.data['alpha'][i] = 0.0;
            source.data['line_alpha'][i] = 0.0;
            label_source.data['alpha'][i] = 0.0;
            line_source.data['alpha'][i] = 0.0;
            point_source.data['alpha'][i] = 0.0;
        }
        csrc.data['alpha'] = [0.0];
        csrc.data['line_alpha'] = [0.0];
        clsrc.data['alpha'] = [0.0];
        clnsrc.data['alpha'] = [0.0];
        cptsrc.data['alpha'] = [0.0];
        source.change.emit();
        label_source.change.emit();
        line_source.change.emit();
        point_source.change.emit();
        csrc.change.emit();
        clsrc.change.emit();
        clnsrc.change.emit();
        cptsrc.change.emit();
        cat_select.value = '— Select category —';
        obj_select.value = '— Select object —';
        info.text = '<i>Select a category, an object, or define your own.</i>';
    """,
    )
    clear_btn.js_on_click(clear_cb)

    # ── Layout ─────────────────────────────────────────────────────
    dropdown_row = row(cat_select, obj_select, clear_btn)
    custom_row = row(custom_name, custom_tmin, custom_tmax, custom_smin, custom_smax, custom_btn)
    layout = column(dropdown_row, custom_row, info_div, p)

    # ── Render via components() (avoids Bokeh sanitizer issue #89) ─
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
        <h2>timeSpace — Reference Object Explorer</h2>
        <p>102 reference objects spanning molecular to planetary scales.
           Select a category, pick an individual object, or define your own.</p>
    </div>
    {div}
    {script}
</body>
</html>"""

    with open(output_path, "w") as f:
        f.write(html)
    print(f"Built {output_path} ({len(html):,} bytes)")


if __name__ == "__main__":
    import sys

    csv_path = sys.argv[1] if len(sys.argv) > 1 else "data/local_data/time_space_reference_objects.csv"
    output_path = sys.argv[2] if len(sys.argv) > 2 else "docs/explorer.html"
    build_explorer(csv_path, output_path)
