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
# the current widget state (checked categories plus any pinned objects) and
# never writes back to a widget, so the category and pin controls cannot
# reset each other. Categories and pins both accumulate.
#
# Labels: pinned objects are always labelled by name. Every other visible
# object follows the label mode: its name, a number that the key beside the
# plot resolves, or nothing (identified on hover).
VISIBILITY_JS = """
    function esc(s) {
        return String(s).replace(/[&<>"']/g, function(c) {
            return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":"&#39;"}[c];
        });
    }
    const activeSet = checkbox.active.map(k => cats[k]);
    const pins = pin_choice.value;
    const a = source.data['alpha'];
    const la = source.data['line_alpha'];
    const lal = label_source.data['alpha'];
    const lna = line_source.data['alpha'];
    const pta = point_source.data['alpha'];
    let shown = 0;
    const names = [];
    for (let i = 0; i < a.length; i++) {
        const inCat = activeSet.indexOf(data[i].Category) !== -1;
        const isSel = pins.indexOf(data[i].Name) !== -1;
        const on = inCat || isSel;
        a[i] = on ? (isSel ? 0.5 : 0.30) : 0.0;
        la[i] = on ? (isSel ? 1.0 : 0.7) : 0.0;
        lna[i] = on ? (isSel ? 1.0 : 0.7) : 0.0;
        pta[i] = on ? (isSel ? 0.8 : 0.6) : 0.0;
        if (on) shown++;
        if (inCat) names.push(data[i].Name);
    }
    const NAMES = 0, NUMBERS = 1;
    const mode = label_mode.active;
    const nal = label_source.data['num_alpha'];
    const pla = label_source.data['plate_alpha'];
    const npla = label_source.data['num_plate_alpha'];
    const keyParts = [];
    for (let i = 0; i < a.length; i++) {
        const isSel = pins.indexOf(data[i].Name) !== -1;
        const on = a[i] > 0;
        lal[i] = (isSel || (on && mode === NAMES)) ? 1.0 : 0.0;
        nal[i] = (on && !isSel && mode === NUMBERS) ? 1.0 : 0.0;
        pla[i] = name_plate_alpha * lal[i];
        npla[i] = number_plate_alpha * nal[i];
    }
    // Key beside the plot: number -> name for what is showing, by category.
    if (mode === NUMBERS) {
        for (const cat of cats) {
            const lines = data.filter((d, i) => d.Category === cat && a[i] > 0)
                              .sort((x, y) => x.Number - y.Number).map(d => d.KeyLine);
            if (lines.length) keyParts.push(key_headers[cat] + lines.join(''));
        }
    }
    key.text = keyParts.join('');
    key.visible = keyParts.length > 0;
    source.change.emit();
    label_source.change.emit();
    line_source.change.emit();
    point_source.change.emit();

    // Pinned objects, newest first: full details for the latest, one line
    // each for the rest.
    const byName = {};
    for (const d of data) byName[d.Name] = d;
    const pinned = pins.map(n => byName[n]).reverse();
    const parts = [];
    if (pinned.length) {
        const d = pinned[0];
        parts.push('<b>' + esc(d.Name) + '</b> (' + esc(d.Category) + ')<br>' +
            'Time: ' + esc(d.TimeLabel) + '<br>' +
            'Space: ' + esc(d.SpaceLabel) + '<br>' +
            '<span style="color:#444">Source: ' + d.ReferenceHtml + '</span>');
    }
    if (pinned.length > 1) {
        parts.push('<b>Also pinned:</b> ' + pinned.slice(1).map(d =>
            esc(d.Name) + ' (' + esc(d.TimeLabel) + '; ' + esc(d.SpaceLabel) + ')').join(' · '));
    }
    if (activeSet.length === 1) {
        parts.push('<b>' + esc(activeSet[0]) + '</b>: ' + names.length + ' objects — ' + names.map(esc).join(', '));
    } else if (activeSet.length > 1) {
        parts.push('<b>' + shown + '</b> objects shown across ' + activeSet.length +
            ' categories (' + activeSet.map(esc).join(', ') + '). ' +
            (mode === NAMES ? 'Click' :
             mode === NUMBERS ? 'Numbers are listed in the key; click' : 'Hover for names; click') +
            ' an object to pin it and see its source.');
    }
    info.text = parts.length ? parts.join('<br>') : empty_text;
"""

# Tap-to-pin: a tooltip follows the cursor and cannot be clicked, so a tap on
# a shape adds that object to the pins (it stays until removed or cleared),
# which puts its source (with links) in the info panel. Hidden shapes are ignored; where shapes overlap, the one covering
# the fewest decades (log time span x log volume span) wins. The selection
# is cleared again so the tap leaves no selection state behind.
TAP_PIN_JS = """
    const hit = cb_obj.indices.filter(i => src.data['alpha'][i] > 0);
    if (cb_obj.indices.length) cb_obj.indices = [];
    if (!hit.length) return;
    const decades = i => Math.log10(data[i].Time_max / data[i].Time_min) *
                         Math.log10(data[i].Space_max / data[i].Space_min);
    hit.sort((i, j) => decades(i) - decades(j));
    const name = data[hit[0]].Name;
    const pins = pin_choice.value;
    if (pins.indexOf(name) === -1) pin_choice.value = pins.concat([name]);
"""

CLEAR_TOGGLE_JS = """
    checkbox.active = [];
    pin_choice.value = [];
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
        pin_choice.value = [];
        info.text = empty_text;
    """
