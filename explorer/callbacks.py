"""Browser-side CustomJS callback source for the explorer.

These strings are executed by Bokeh in the browser (no server). Ellipse
math mirrors timeSpace.calculations.create_ellipse_data. Kept as module
constants so build.py wiring stays readable.
"""

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


# Visibility callback shared by both modes. It recomputes every alpha from
# the current widget state (checked categories plus the optionally-pinned
# object) and never writes back to a widget, so the category and object
# controls cannot reset each other. Categories accumulate.
#
# Labels: the pinned object is always labelled. Every other visible object
# is labelled while the "Show labels" box is ticked; otherwise it is
# identified on hover.
VISIBILITY_JS = """
    function esc(s) {
        return String(s).replace(/[&<>"']/g, function(c) {
            return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":"&#39;"}[c];
        });
    }
    const activeSet = checkbox.active.map(k => cats[k]);
    const sel = obj_select.value;
    const NONE = obj_select.options[0];
    const a = source.data['alpha'];
    const la = source.data['line_alpha'];
    const lal = label_source.data['alpha'];
    const lna = line_source.data['alpha'];
    const pta = point_source.data['alpha'];
    let shown = 0;
    let pinned = null;
    const names = [];
    for (let i = 0; i < a.length; i++) {
        const inCat = activeSet.indexOf(data[i].Category) !== -1;
        const isSel = sel !== NONE && data[i].Name === sel;
        const on = inCat || isSel;
        a[i] = on ? (isSel ? 0.5 : 0.30) : 0.0;
        la[i] = on ? (isSel ? 1.0 : 0.7) : 0.0;
        lna[i] = on ? (isSel ? 1.0 : 0.7) : 0.0;
        pta[i] = on ? (isSel ? 0.8 : 0.6) : 0.0;
        if (on) shown++;
        if (inCat) names.push(data[i].Name);
        if (isSel) pinned = data[i];
    }
    const labelCategories = label_toggle.active.length > 0;
    for (let i = 0; i < a.length; i++) {
        const isSel = sel !== NONE && data[i].Name === sel;
        lal[i] = (isSel || (a[i] > 0 && labelCategories)) ? 1.0 : 0.0;
    }
    source.change.emit();
    label_source.change.emit();
    line_source.change.emit();
    point_source.change.emit();

    const parts = [];
    if (pinned) {
        parts.push('<b>' + esc(pinned.Name) + '</b> (' + esc(pinned.Category) + ')<br>' +
            'Time: ' + esc(pinned.TimeLabel) + '<br>' +
            'Space: ' + esc(pinned.SpaceLabel) + '<br>' +
            '<span style="color:#444">Source: ' + pinned.ReferenceHtml + '</span>');
    }
    if (activeSet.length === 1) {
        parts.push('<b>' + esc(activeSet[0]) + '</b>: ' + names.length + ' objects — ' + names.map(esc).join(', '));
    } else if (activeSet.length > 1) {
        parts.push('<b>' + shown + '</b> objects shown across ' + activeSet.length +
            ' categories (' + activeSet.map(esc).join(', ') + '). ' +
            (labelCategories ? '' : 'Hover for names; ') +
            'click an object to pin it and see its source.');
    }
    info.text = parts.length ? parts.join('<br>') : empty_text;
"""

# Tap-to-pin: a tooltip follows the cursor and cannot be clicked, so a tap on
# a shape pins that object, which puts its source (with links) in the info
# panel. Hidden shapes are ignored; where shapes overlap, the one covering
# the fewest decades (log time span x log volume span) wins. The selection
# is cleared again so the tap leaves no selection state behind.
TAP_PIN_JS = """
    const hit = cb_obj.indices.filter(i => src.data['alpha'][i] > 0);
    if (cb_obj.indices.length) cb_obj.indices = [];
    if (!hit.length) return;
    const decades = i => Math.log10(data[i].Time_max / data[i].Time_min) *
                         Math.log10(data[i].Space_max / data[i].Space_min);
    hit.sort((i, j) => decades(i) - decades(j));
    obj_select.value = data[hit[0]].Name;
"""

CLEAR_TOGGLE_JS = """
    checkbox.active = [];
    obj_select.value = obj_select.options[0];
"""


# Select-mode clear: also removes the custom object, then resets the widgets
# (which re-runs VISIBILITY_JS and hides every reference object).
SELECT_CLEAR_JS = """
        csrc.data['alpha'] = [0.0];
        csrc.data['line_alpha'] = [0.0];
        clsrc.data['alpha'] = [0.0];
        clnsrc.data['alpha'] = [0.0];
        cptsrc.data['alpha'] = [0.0];
        csrc.change.emit();
        clsrc.change.emit();
        clnsrc.change.emit();
        cptsrc.change.emit();
        checkbox.active = [];
        obj_select.value = obj_select.options[0];
        info.text = empty_text;
    """
