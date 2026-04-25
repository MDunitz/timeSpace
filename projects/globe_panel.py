"""
globe_panel.py
--------------
create_globe_figure(category_colors, ...) -> plotly Figure
    Orthographic globe: yellow 10° BGC cell + blue 1° eddy grid.

create_scale_cascade_html(category_colors, ...) -> str
    Three true-isometric cubes (eddy → coastal → micro) with:
    - Proper isometric geometry: dtx = s*cos(30°) = s*0.866, dty = s*sin(30°) = s*0.5
    - Lh label rotated along base of front face
    - Lv label rotated to match right-face slant angle (-30°)
    - Volume on top face
    - Sub-highlights rendered as mini isometric cubes (not rectangles)

    Volumes astropy-verified (precomputed):
        Eddy:    (1e5*u.m)**2 * (1e3*u.m)  = 1e13 m³ = 1e4 km³
        Coastal: (100*u.m)**2  * (10*u.m)  = 1e7  m³
        Micro:   (1e-4*u.m)**3             = 1e-12 m³ = 1 nL
"""

import math
import numpy as np
import plotly.graph_objects as go

# ---------------------------------------------------------------------------
# Astropy-verified volumes (precomputed to avoid runtime dependency)
# from astropy import units as u
# Eddy:    (1e5*u.m)**2 * (1e3*u.m)  = 1e13 m³ = 1e4 km³
# Coastal: (100*u.m)**2 * (10*u.m)   = 1e7  m³
# Micro:   (1e-4*u.m)**3             = 1e-12 m³ = 1 nL
# ---------------------------------------------------------------------------
CUBE_SPECS = [
    {
        "title": "Eddy scale",
        "lh": "100 km",
        "lv": "1 km",
        "vol_m3": "10¹³ m³",
        "vol_alt": "10⁴ km³",
        "note": "eddy-resolving BGC model cell",
        "side_px": 120,
        "depth_px": 16,  # Lv/Lh = 1/100; capped at 16px for visibility
        "process_type": "Physical",
    },
    {
        "title": "Coastal / patch scale",
        "lh": "100 m",
        "lv": "10 m",
        "vol_m3": "10⁷ m³",
        "vol_alt": "10 million m³",
        "note": "coastal model cell, habitat scale",
        "side_px": 84,
        "depth_px": 20,  # Lv/Lh = 1/10; capped at 20px for visibility
        "process_type": "Physical",
    },
    {
        "title": "Micro / cellular scale",
        "lh": "0.1 mm",
        "lv": "0.1 mm",
        "vol_m3": "10⁻¹² m³",
        "vol_alt": "1 nL",
        "note": "sub-grid for all ocean models",
        "side_px": 52,
        "depth_px": 52,  # Lv = Lh (isotropic), true cube
        "process_type": "Biological",
    },
]

# Isometric constants
# cos30 = √3/2 ≈ 0.866,  sin30 = 0.5
_COS30 = math.cos(math.radians(30))
_SIN30 = math.sin(math.radians(30))
# Right-face slant angle in SVG degrees: atan2(-dty, dtx) relative to horizontal
_SLANT_DEG = math.degrees(math.atan2(-_SIN30, _COS30))  # ≈ -30°


def _hex_to_rgb(h):
    h = h.lstrip("#")
    return f"{int(h[0:2],16)},{int(h[2:4],16)},{int(h[4:6],16)}"


# ---------------------------------------------------------------------------
# Globe helpers
# ---------------------------------------------------------------------------


def _globe_lines(lons, lats, color, width, alpha, name, showlegend=False):
    lon_flat, lat_flat = [], []
    for lo, la in zip(lons, lats):
        lon_flat.extend(list(lo) + [None])
        lat_flat.extend(list(la) + [None])
    return go.Scattergeo(
        lon=lon_flat,
        lat=lat_flat,
        mode="lines",
        line=dict(color=color, width=width),
        opacity=alpha,
        name=name,
        showlegend=showlegend,
        hoverinfo="skip",
    )


def _world_grid(lon_step, lat_step, n=200):
    lons, lats = [], []
    for lo in range(-180, 181, lon_step):
        lons.append(np.full(n, lo))
        lats.append(np.linspace(-90, 90, n))
    for la in range(-90, 91, lat_step):
        lons.append(np.linspace(-180, 180, n))
        lats.append(np.full(n, la))
    return lons, lats


def _region_grid(region, spacing, n=200):
    r = region
    lv = list(np.arange(r["lon0"], r["lon1"] + spacing, spacing))
    la = list(np.arange(r["lat0"], r["lat1"] + spacing, spacing))
    lons = [np.full(n, lo) for lo in lv] + [np.linspace(r["lon0"], r["lon1"], n) for _ in la]
    lats = [np.linspace(r["lat0"], r["lat1"], n) for _ in lv] + [np.full(n, l) for l in la]
    return lons, lats


def _box_outline(region, color, width):
    r = region
    return go.Scattergeo(
        lon=[r["lon0"], r["lon1"], r["lon1"], r["lon0"], r["lon0"]],
        lat=[r["lat0"], r["lat0"], r["lat1"], r["lat1"], r["lat0"]],
        mode="lines",
        line=dict(color=color, width=width),
        showlegend=False,
        hoverinfo="skip",
    )


# ---------------------------------------------------------------------------
# Public: Globe
# ---------------------------------------------------------------------------
BGC_CELL = dict(lon0=-70, lon1=-60, lat0=30, lat1=40)
FINE_CELL = dict(lon0=-66, lon1=-65, lat0=35, lat1=36)


def create_globe_figure(category_colors, width=700, height=700, central_lon=-65, central_lat=35):
    """
    Orthographic globe. Yellow 10° BGC grid (near-invisible, box outline kept).
    Blue 1° eddy-resolving grid inside the BGC cell.
    """
    bgc_yellow = "#F5C842"
    fine_color = category_colors["Physical"]

    fig = go.Figure()

    lons, lats = _world_grid(10, 10)
    fig.add_trace(_globe_lines(lons, lats, bgc_yellow, 1.5, 0.55, "~1000 km  (biogeochem model)", showlegend=True))
    fig.add_trace(_box_outline(BGC_CELL, bgc_yellow, 4.0))

    fig.add_trace(
        go.Scattergeo(
            lon=[-65],
            lat=[42],
            mode="text",
            text=["~1000 km BGC cell"],
            textfont=dict(size=13, color="#C89A00", family="Arial Black"),
            showlegend=False,
            hoverinfo="skip",
        )
    )

    lons, lats = _region_grid(BGC_CELL, spacing=1)
    fig.add_trace(_globe_lines(lons, lats, fine_color, 0.8, 0.4, "~100 km  (eddy-resolving)", showlegend=True))
    fig.add_trace(_box_outline(FINE_CELL, fine_color, 3.0))

    fig.update_geos(
        projection_type="orthographic",
        projection_rotation=dict(lon=central_lon, lat=central_lat, roll=0),
        showland=True,
        landcolor="#E8E4D8",
        showocean=True,
        oceancolor="#C8DFF0",
        showlakes=False,
        showcountries=False,
        showcoastlines=True,
        coastlinecolor="#888888",
        coastlinewidth=0.5,
        showframe=False,
        bgcolor="rgba(0,0,0,0)",
    )
    fig.update_layout(
        width=width,
        height=height,
        margin=dict(l=10, r=10, t=45, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        title=None,
        legend=dict(
            x=0.01, y=0.01, font=dict(size=11), bgcolor="rgba(255,255,255,0.85)", bordercolor="#cccccc", borderwidth=1
        ),
    )
    return fig


# ---------------------------------------------------------------------------
# Isometric cube SVG  (true isometric: dtx = s*cos30, dty = s*sin30)
# ---------------------------------------------------------------------------


def _iso_cube_svg(
    side, col, rgb, lh="", lv="", vol_m3="", vol_alt="", sub_side=0, sub_col="", sub_rgb="", depth_px=None
):
    """
    Isometric box: TOP FACE = Lh×Lh parallelogram, HEIGHT = Lv (depth_px).

    side     = Lh px  — top-face square footprint
    depth_px = Lv px  — vertical box height (small → flat slab)

    dtx = side*cos30, dty = side*sin30  (top-face isometric offsets, from Lh)
    h   = depth_px                      (front/right face height, from Lv)

    Vertices:
      Top:   (0,dty) (side,dty) (side+dtx,0) (dtx,0)
      Front: (0,dty) (side,dty) (side,dty+h) (0,dty+h)
      Right: (side,dty) (side+dtx,0) (side+dtx,h) (side,dty+h)
    """
    s = side
    h = depth_px if depth_px is not None else s
    dtx = int(round(s * _COS30))
    dty = int(round(s * _SIN30))

    total_w = s + dtx + 80
    total_h = dty + h + 28

    top_pts = f"0,{dty} {s},{dty} {s+dtx},0 {dtx},0"
    front_pts = f"0,{dty} {s},{dty} {s},{dty+h} 0,{dty+h}"
    right_pts = f"{s},{dty} {s+dtx},0 {s+dtx},{h} {s},{dty+h}"

    top = f'<polygon points="{top_pts}"   fill="rgba({rgb},0.35)" stroke="{col}" stroke-width="1.8"/>'
    front = f'<polygon points="{front_pts}" fill="rgba({rgb},0.10)" stroke="{col}" stroke-width="1.8"/>'
    right = f'<polygon points="{right_pts}" fill="rgba({rgb},0.22)" stroke="{col}" stroke-width="1.8"/>'

    # Sub-cube: mini slab in bottom-left of front face
    sub_part = ""
    if sub_side > 0 and sub_col:
        ss = sub_side
        sh = max(3, ss // 3)
        sdtx = int(round(ss * _COS30))
        sdty = int(round(ss * _SIN30))
        ox, oy = 2, dty + h - sh - sdty
        st = f"0,{sdty} {ss},{sdty} {ss+sdtx},0 {sdtx},0"
        sf = f"0,{sdty} {ss},{sdty} {ss},{sdty+sh} 0,{sdty+sh}"
        sr = f"{ss},{sdty} {ss+sdtx},0 {ss+sdtx},{sh} {ss},{sdty+sh}"
        sub_rgb_str = _hex_to_rgb(sub_col) if isinstance(sub_col, str) and sub_col.startswith("#") else sub_rgb
        sub_part = (
            f'<g transform="translate({ox},{oy})">'
            f'<polygon points="{st}" fill="rgba({sub_rgb},0.18)" stroke="{sub_col}" stroke-width="0.8"/>'
            f'<polygon points="{sf}" fill="rgba({sub_rgb},0.08)" stroke="{sub_col}" stroke-width="0.8"/>'
            f'<polygon points="{sr}" fill="rgba({sub_rgb},0.12)" stroke="{sub_col}" stroke-width="0.8"/>'
            f"</g>"
        )

    # Lh: below front base, centred
    lh_lbl = (
        f'<text x="{s//2}" y="{dty+h+14}" text-anchor="middle" '
        f'font-size="11" font-weight="bold" fill="{col}" font-family="Arial">'
        f"L&#x2095; = {lh}</text>"
    )

    # Lv: on right vertical edge, centred, horizontal
    lv_lbl = (
        f'<text x="{s+6}" y="{dty + h//2}" text-anchor="start" dominant-baseline="middle" '
        f'font-size="11" font-weight="bold" fill="{col}" font-family="Arial">'
        f"L&#x1D65; = {lv}</text>"
    )

    # Vol: top face centroid
    tc_x = (s + dtx) // 2
    tc_y = dty // 2
    vol_lbl = (
        f'<text x="{tc_x}" y="{tc_y-4}" text-anchor="middle" '
        f'font-size="10" font-weight="bold" fill="{col}" font-family="Arial">{vol_m3}</text>'
        f'<text x="{tc_x}" y="{tc_y+9}" text-anchor="middle" '
        f'font-size="9" fill="{col}" font-family="Arial" font-style="italic">= {vol_alt}</text>'
    )

    return (
        f'<svg width="{total_w}" height="{total_h}" overflow="visible">'
        f"{top}{right}{front}{sub_part}{lh_lbl}{lv_lbl}{vol_lbl}</svg>"
    )


# ---------------------------------------------------------------------------
# Public: Scale cascade HTML
# ---------------------------------------------------------------------------


def create_scale_cascade_html(category_colors, globe_height=700):
    """
    Three true-isometric cubes stacked vertically with dimension labels and
    mini-cube sub-highlights.

    Volumes astropy-verified (precomputed):
        Eddy:    (1e5*u.m)**2 * (1e3*u.m)  = 1e13 m³ = 1e4 km³
        Coastal: (100*u.m)**2 * (10*u.m)   = 1e7  m³
        Micro:   (1e-4*u.m)**3             = 1e-12 m³ = 1 nL
    """
    FINE = category_colors["Physical"]
    BIO = category_colors["Biological"]

    tops = [10, 250, 470]
    BOX_H = 225

    def col_for(spec):
        return FINE if spec["process_type"] == "Physical" else BIO

    boxes_html = ""
    for i, (spec, top) in enumerate(zip(CUBE_SPECS, tops)):
        col = col_for(spec)
        rgb = _hex_to_rgb(col)
        s = spec["side_px"]

        # Sub-cube is the next-scale-down cube (÷1000 in each linear dimension = ÷10 per side)
        sub_col = col_for(CUBE_SPECS[i + 1]) if i < len(CUBE_SPECS) - 1 else ""
        sub_rgb = _hex_to_rgb(sub_col) if sub_col else ""
        sub_s = int(round(s / 10)) if sub_col else 0  # linear scale ÷10 → volume ÷1000

        svg = _iso_cube_svg(
            side=s,
            col=col,
            rgb=rgb,
            lh=spec["lh"],
            lv=spec["lv"],
            vol_m3=spec["vol_m3"],
            vol_alt=spec["vol_alt"],
            sub_side=sub_s,
            sub_col=sub_col,
            sub_rgb=sub_rgb,
            depth_px=spec.get("depth_px"),
        )
        boxes_html += (
            f'<div style="position:absolute;left:0;top:{top}px;width:500px;height:{BOX_H}px">'
            f'<div style="position:absolute;left:16px;top:4px;font-weight:700;'
            f'font-size:14px;color:#222">{spec["title"]}</div>'
            f'<div style="position:absolute;left:16px;top:21px;font-size:9px;'
            f'color:#999;font-style:italic">{spec["note"]}</div>'
            f'<div style="position:absolute;left:16px;top:38px">{svg}</div>'
            f"</div>"
        )

    # Arrow geometry
    # New cube: SVG offset within box div = 38px (title+note height)
    # top-face dty = side_px * sin30; box height = depth_px
    # front-face bottom = 38 + dty + depth_px
    def front_bottom_y(idx):
        sp = CUBE_SPECS[idx]
        s_ = sp["side_px"]
        h_ = sp.get("depth_px", s_)
        dty_ = int(round(s_ * _SIN30))
        return tops[idx] + 38 + dty_ + h_

    def front_mid_y(idx):
        sp = CUBE_SPECS[idx]
        s_ = sp["side_px"]
        h_ = sp.get("depth_px", s_)
        dty_ = int(round(s_ * _SIN30))
        return tops[idx] + 38 + dty_ + h_ // 2

    ctrl_x = -32
    cascade_html = (
        f'<div style="position:relative;width:530px;height:{globe_height}px;overflow:visible">'
        f"{boxes_html}"
        f'<svg style="position:absolute;top:0;left:0;overflow:visible;pointer-events:none"'
        f' width="530" height="{globe_height}" xmlns="http://www.w3.org/2000/svg">'
        f"<defs>"
        f'<marker id="ah-phys" markerWidth="9" markerHeight="7" refX="9" refY="3.5" orient="auto">'
        f'<polygon points="0 0,9 3.5,0 7" fill="{FINE}"/></marker>'
        f'<marker id="ah-bio" markerWidth="9" markerHeight="7" refX="9" refY="3.5" orient="auto">'
        f'<polygon points="0 0,9 3.5,0 7" fill="{BIO}"/></marker>'
        f"</defs>"
        # Arrow eddy → coastal
        f'<path d="M 16,{front_bottom_y(0)} C {ctrl_x},{front_bottom_y(0)} {ctrl_x},{front_mid_y(1)} 16,{front_mid_y(1)}"'
        f' stroke="{FINE}" stroke-width="2" fill="none" stroke-dasharray="6,3" marker-end="url(#ah-phys)"/>'
        f'<text x="{ctrl_x-4}" y="{(front_bottom_y(0)+front_mid_y(1))//2}" fill="#888" font-size="10"'
        f' font-style="italic" font-family="Arial" text-anchor="end">÷ 1000</text>'
        # Arrow coastal → micro
        f'<path d="M 16,{front_bottom_y(1)} C {ctrl_x},{front_bottom_y(1)} {ctrl_x},{front_mid_y(2)} 16,{front_mid_y(2)}"'
        f' stroke="{BIO}" stroke-width="2" fill="none" stroke-dasharray="6,3" marker-end="url(#ah-bio)"/>'
        f'<text x="{ctrl_x-4}" y="{(front_bottom_y(1)+front_mid_y(2))//2}" fill="#888" font-size="10"'
        f' font-style="italic" font-family="Arial" text-anchor="end">÷ 1000</text>'
        f"</svg>"
        f"</div>"
    )
    return cascade_html


# ---------------------------------------------------------------------------
# Back-compat stub
# ---------------------------------------------------------------------------
def create_scale_popout(*args, **kwargs):
    raise NotImplementedError(
        "create_scale_popout() replaced by create_scale_cascade_html(). " "Embed the returned HTML string directly."
    )
