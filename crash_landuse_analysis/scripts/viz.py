"""Plot styling and the three-region map layout used by every map figure."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, ListedColormap
from matplotlib.lines import Line2D
import numpy as np
import geopandas as gpd
import pandas as pd

import common as C

# Reference palette (dataviz skill, light mode)
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
NEUTRAL = "#f0efec"
WATER = "#e3ebf2"
LAND = "#f4f3ef"
CAT = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
BLUE = ["#cde2fb", "#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec", "#5598e7", "#3987e5",
        "#2a78d6", "#256abf", "#1c5cab", "#184f95", "#104281", "#0d366b"]
RED_ARM = ["#f7d9d4", "#f1b3aa", "#ea8a80", "#e34948", "#c23434", "#9a2323"]
BLUE_ARM = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#1c5cab", "#104281"]

# Severity ordinal ramp (Total -> Fatal = light -> dark)
SEV_COLOR = {"TOT": "#86b6ef", "KAB": "#3987e5", "KSI": "#1c5cab", "FAT": "#0d366b"}
SEV_MARKER = {"TOT": "o", "KAB": "s", "KSI": "D", "FAT": "^"}

# Established GIS conventions for LISA / Gi* classes (GeoDa & ArcGIS defaults)
LISA_COLORS = {"High-High": "#d7191c", "Low-Low": "#2c7bb6", "Low-High": "#abd9e9",
               "High-Low": "#fdae61", "Not significant": "#d9d9d6"}
GI_COLORS = {"Hot spot 99%": "#b2182b", "Hot spot 95%": "#ef8a62", "Hot spot 90%": "#fddbc7",
             "Not significant": "#d9d9d6", "Cold spot 90%": "#d1e5f0",
             "Cold spot 95%": "#67a9cf", "Cold spot 99%": "#2166ac"}

DIVERGING = LinearSegmentedColormap.from_list(
    "irr", BLUE_ARM[::-1] + [NEUTRAL] + RED_ARM, N=256)
SEQ_BLUE = LinearSegmentedColormap.from_list("seqblue", ["#f4f8fd"] + BLUE, N=256)


def style():
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 8.5,
        "axes.facecolor": SURFACE,
        "figure.facecolor": "white",
        "axes.edgecolor": AXIS,
        "axes.labelcolor": INK2,
        "axes.titlecolor": INK,
        "axes.titlesize": 9.5,
        "axes.titleweight": "bold",
        "axes.grid": False,
        "grid.color": GRID,
        "grid.linewidth": 0.6,
        "xtick.color": INK2,
        "ytick.color": INK2,
        "xtick.labelsize": 7.5,
        "ytick.labelsize": 7.5,
        "legend.frameon": False,
        "legend.fontsize": 7.5,
        "savefig.dpi": 220,
        "savefig.bbox": "tight",
        "savefig.facecolor": "white",
    })


style()

_COUNTIES = None


def counties():
    global _COUNTIES
    if _COUNTIES is None:
        _COUNTIES = gpd.read_file(C.DATA / "fl_counties.gpkg").to_crs(C.CRS)
    return _COUNTIES


def region_bounds(g_all):
    """Extent of each region from all site geometries, padded."""
    out = {}
    for r, cs in C.REGIONS.items():
        sub = g_all[g_all["COUNTY"].isin(cs)]
        x0, y0, x1, y1 = sub.total_bounds
        pad = max(x1 - x0, y1 - y0) * 0.08 + 1500
        out[r] = (x0 - pad, y0 - pad, x1 + pad, y1 + pad)
    return out


def _scalebar(ax, km):
    x0, x1 = ax.get_xlim()
    y0, y1 = ax.get_ylim()
    bx = x0 + (x1 - x0) * 0.06
    by = y0 + (y1 - y0) * 0.05
    ax.plot([bx, bx + km * 1000], [by, by], color=INK, lw=2, solid_capstyle="butt", zorder=20)
    ax.text(bx + km * 500, by + (y1 - y0) * 0.018, f"{km} km", ha="center", va="bottom",
            fontsize=6.5, color=INK, zorder=20)


def _north(ax):
    ax.annotate("N", xy=(0.93, 0.95), xytext=(0.93, 0.85), xycoords="axes fraction",
                ha="center", va="center", fontsize=7.5, fontweight="bold", color=INK,
                arrowprops=dict(arrowstyle="-|>", color=INK, lw=1))


def region_axes(fig_w=7.2, fig_h=5.4, title=None):
    """Map layout: Tampa Bay (tall, left) | Orlando (top middle) + legend box
    (bottom middle) | Southeast Florida (tall, right). Returns fig, axes, legend-ax."""
    fig = plt.figure(figsize=(fig_w, fig_h))
    gs = fig.add_gridspec(2, 3, width_ratios=[1.25, 1.0, 0.62], height_ratios=[0.52, 1.0],
                          wspace=0.05, hspace=0.06)
    axes = {"Tampa Bay": fig.add_subplot(gs[:, 0]),
            "Orlando": fig.add_subplot(gs[0, 1]),
            "Southeast Florida": fig.add_subplot(gs[:, 2])}
    lax = fig.add_subplot(gs[1, 1])
    lax.set_axis_off()
    if title:
        fig.suptitle(title, fontsize=10, fontweight="bold", color=INK, y=0.995)
    return fig, axes, lax


ROUTE_NAME = {"Alt19": "Alt US 19", "Reg19": "US 19", "SR580": "SR 580", "SR600": "SR 600",
              "ColonialDrive": "Colonial Dr (SR 50)", "MilitaryTrail": "Military Trail",
              "LakeWorth": "Lake Worth Rd", "OaklandPark": "Oakland Park Blvd",
              "Sunrise": "Sunrise Blvd", "UniversityDrive": "University Dr"}
# label anchor: which end of the corridor to label and text offset (points)
ROUTE_LABEL_POS = {"Alt19": ("s", (-4, -8)), "Reg19": ("n", (6, 0)), "SR580": ("e", (4, 4)),
                   "SR600": ("s", (4, -4)), "ColonialDrive": ("w", (0, 6)),
                   "MilitaryTrail": ("n", (4, 4)), "LakeWorth": ("w", (-2, 6)),
                   "OaklandPark": ("e", (-10, 7)), "Sunrise": ("e", (3, -9)),
                   "UniversityDrive": ("s", (4, -2))}


def label_routes(ax, segs):
    for rg, sub in segs.groupby("Route_grp"):
        x0, y0, x1, y1 = sub.total_bounds
        end, off = ROUTE_LABEL_POS.get(rg, ("n", (4, 4)))
        cen = sub.geometry.centroid
        idx = {"n": cen.y.idxmax(), "s": cen.y.idxmin(), "e": cen.x.idxmax(),
               "w": cen.x.idxmin()}[end]
        p = cen.loc[idx]
        ha = "right" if off[0] < 0 else "left"
        ax.annotate(ROUTE_NAME.get(rg, rg), (p.x, p.y), fontsize=5.8, color=INK, zorder=8,
                    xytext=off, textcoords="offset points", ha=ha, va="center",
                    bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.8))


def draw_base(ax, region, bounds, segs=None):
    cty = counties()
    ax.set_facecolor(WATER)
    cty.plot(ax=ax, color=LAND, edgecolor="white", linewidth=0.9, zorder=0)
    if segs is not None:
        segs.plot(ax=ax, color="#b9b7ae", linewidth=0.9, zorder=1)
    x0, y0, x1, y1 = bounds[region]
    # keep aspect: expand the shorter side
    w, h = x1 - x0, y1 - y0
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_color(AXIS)
        s.set_linewidth(0.6)
    ax.set_title(region, fontsize=8.5, color=INK, fontweight="bold", pad=3)
    # county labels
    for _, r in cty.iterrows():
        if r["id"] in C.COUNTY_FIPS.values():
            c = r.geometry.representative_point()
            if x0 < c.x < x1 and y0 < c.y < y1:
                ax.text(c.x, c.y, r["name"], fontsize=6, color=MUTED, ha="center",
                        va="center", zorder=2, style="italic")
    km = 10 if max(w, h) > 40000 else 5
    _scalebar(ax, km)
    _north(ax)


def legend_handles(color_map, marker="o", size=6, edge="white"):
    return [Line2D([0], [0], marker=marker, color="none", markerfacecolor=c,
                   markeredgecolor=edge, markeredgewidth=0.5, markersize=size, label=k)
            for k, c in color_map.items()]


def savefig(fig, name):
    path = C.FIG / name
    fig.savefig(path)
    plt.close(fig)
    return path


_BOUNDS = None
_SEGS = None


def bounds():
    global _BOUNDS
    if _BOUNDS is None:
        _BOUNDS = pd.read_pickle(C.OUT / "region_bounds.pkl")
    return _BOUNDS


def segs_bg():
    global _SEGS
    if _SEGS is None:
        _SEGS = C.load("seg")[["Route_grp", "region", "geometry"]]
    return _SEGS


def region_map(g, cls_col, colors, kind, fname, legend_title, note=None, size=11,
               show_bg=True, routes=False, counts=True, marker_map=None):
    """Categorical map of sites across the three regions.

    g: GeoDataFrame with 'region', 'pt' (for points) or line geometry.
    colors: ordered dict class -> colour (first drawn lowest).
    """
    fig, axes, lax = region_axes()
    B = bounds()
    bg = segs_bg()
    order = list(colors)
    for reg, ax in axes.items():
        draw_base(ax, reg, B, segs=bg[bg["region"] == reg] if (show_bg and kind == "point") else None)
        sub = g[g["region"] == reg]
        for z, cl in enumerate(order):
            ss = sub[sub[cls_col] == cl]
            if not len(ss):
                continue
            if kind == "point":
                mk = marker_map.get(cl, "o") if marker_map else "o"
                big = cl not in ("Not significant", "n.s.")
                ax.scatter(ss["pt"].x, ss["pt"].y, s=size * (1.35 if big else 0.8),
                           color=colors[cl], marker=mk, edgecolor="white", linewidth=0.4,
                           zorder=4 + z)
            else:
                ss.plot(ax=ax, color=colors[cl], linewidth=2.6 if cl != "Not significant" else 1.6,
                        zorder=4 + z)
        if routes:
            label_routes(ax, bg[bg["region"] == reg])
    handles = []
    for cl in order:
        n = int((g[cls_col] == cl).sum())
        lab = f"{cl} ({n})" if counts else cl
        if kind == "point":
            mk = marker_map.get(cl, "o") if marker_map else "o"
            handles.append(Line2D([0], [0], marker=mk, color="none", markerfacecolor=colors[cl],
                                  markeredgecolor="white", markersize=7, label=lab))
        else:
            handles.append(Line2D([0], [0], color=colors[cl], lw=3, label=lab))
    lax.legend(handles=handles, loc="upper left", title=legend_title, title_fontsize=7.5,
               fontsize=7, alignment="left", borderaxespad=0.2)
    if note:
        lax.text(0.0, 0.02, note, transform=lax.transAxes, fontsize=6.3, color=INK2,
                 va="bottom", wrap=True)
    return savefig(fig, fname)
