"""Publication-quality redraw of the study-area map: intersections coloured
by land-use context typology in Tampa Bay, Orlando and Southeast Florida.

Layout ideas:
  * all three regions drawn at ONE common scale (single scale bar and north
    arrow), so corridor lengths are directly comparable across regions
  * colour-blind-safe (Okabe-Ito) palette + redundant marker shapes
  * Florida locator inset with the study counties highlighted
  * Times New Roman throughout, vector PDF with embedded TrueType fonts

Geometry comes from study_area_map_data.json (km, panel-local coordinates,
traced from the draft map by digitize_study_area_map.py).
"""
import json
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection, PatchCollection
from matplotlib.lines import Line2D
from matplotlib.patches import Polygon, Rectangle

HERE = Path(__file__).parent

mpl.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "Times", "Liberation Serif", "Nimbus Roman"],
    "mathtext.fontset": "stix",
    "font.size": 8,
    "axes.linewidth": 0.6,
    "pdf.fonttype": 42, "ps.fonttype": 42, "svg.fonttype": "none",
})

WATER, LAND, EDGE = "#dde8f1", "#f4f3ef", "#9a9a9a"
CORRIDOR = "#b9b6ad"

# Okabe-Ito colour-blind-safe palette, each class with its own shape
TYPES = [  # key, label, n, colour, marker, size
    ("low", "Low-intensity frontage", 93, "#8c8c8c", "o", 16),
    ("shop", "Shopping-center / big-box retail", 114, "#0072B2", "s", 15),
    ("ind", "Industrial & auto-oriented", 77, "#D55E00", "^", 19),
    ("civic", "Civic & recreation", 75, "#009E73", "D", 13),
    ("strip", "Small retail & services strip", 130, "#CC79A7", "P", 22),
]

REGIONS = [  # key, title, study counties (locator)
    ("tampa", "Tampa Bay", ["Pinellas", "Pasco", "Hillsborough"]),
    ("orlando", "Orlando", ["Orange"]),
    ("se", "Southeast Florida", ["Palm Beach", "Broward"]),
]
COUNTY_LABELS = {"tampa": [("Pasco", 48.0, 74.3), ("Pinellas", 13.8, 26.7)],
                 "orlando": [("Orange", 37.0, 35.5)], "se": []}
HIGHLIGHT = "#4d4d4d"


def area(ring):
    """Shoelace area (km^2); drops specks left over from tracing."""
    return 0.5 * abs(sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1)
                         in zip(ring, ring[1:] + ring[:1])))


def draw_region(ax, p, title, tag, layer):
    ax.set_facecolor(WATER)
    ax.add_collection(PatchCollection([Polygon(r) for r in p["land"] if area(r) > 0.5],
                                      fc=LAND, ec="none", zorder=1))
    ax.add_collection(LineCollection(p["county"], colors="white", lw=0.9,
                                     capstyle="round", zorder=2))
    layer(ax, tag)
    for name, x, y in COUNTY_LABELS.get(tag, []):
        ax.text(x, y, name, fontsize=7, style="italic", color="#6e6e6e",
                ha="center", va="center", zorder=5)
    ax.set_xlim(0, p["w_km"]); ax.set_ylim(0, p["h_km"])
    ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_color(EDGE)
    ax.set_title(title, fontsize=10, fontweight="bold", pad=3)


def intersection_layer(d):
    """Corridor lines + typology markers for the intersection map."""
    def layer(ax, tag):
        p = d[tag]
        mk = [(x, y) for _, x, y in p["markers"]]
        near = lambda q: min((q[0] - x) ** 2 + (q[1] - y) ** 2 for x, y in mk) < 9
        corridor = [sg for sg in p["corridor"] if near(sg[0])]  # drop tracing specks
        ax.add_collection(LineCollection(corridor, colors=CORRIDOR, lw=0.9,
                                         capstyle="round", zorder=3))
        # draw the largest classes first so rarer types stay visible
        for key, _, n, col, m, sz in sorted(TYPES, key=lambda t: -t[2]):
            xy = [(x, y) for k, x, y in p["markers"] if k == key]
            if xy:
                xs, ys = zip(*xy)
                ax.scatter(xs, ys, s=sz, c=col, marker=m, edgecolors="white",
                           linewidths=0.45, zorder=4)
    handles = [Line2D([], [], ls="", marker=m, ms=sz ** 0.5 * 1.25, mfc=col,
                      mec="white", mew=0.45, label=f"{lab} ($n$ = {n})")
               for _, lab, n, col, m, sz in TYPES]
    handles.append(Line2D([], [], color=CORRIDOR, lw=1.2, label="Study corridor"))
    return layer, handles


def draw_locator(ax, counties):
    study = {c: i for i, (_, _, cs) in enumerate(REGIONS) for c in cs}
    for name, rings in counties.items():
        hit = name in study
        for r in rings:
            ax.add_patch(Polygon(r, fc=HIGHLIGHT if hit else LAND,
                                 ec="white" if hit else "#c9c7c0", lw=0.25))
    ax.set_facecolor(WATER)
    ax.set_xlim(-87.7, -79.8); ax.set_ylim(24.4, 31.1)
    ax.set_aspect(1 / 0.88)  # ~cos(28 deg)
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_color(EDGE)
    for txt, x, y, ha in [("Tampa Bay", -83.05, 28.05, "right"),
                          ("Orlando", -81.2, 28.95, "left"),
                          ("Southeast\nFlorida", -80.95, 26.55, "right")]:
        ax.text(x, y, txt, fontsize=6.5, ha=ha, va="center", fontweight="bold",
                color="#222")
    ax.text(-87.4, 24.75, "Florida", fontsize=7, style="italic", color="#6e6e6e")
    ax.text(-86.1, 25.6, "Gulf of\nMexico", fontsize=6, style="italic",
            color="#7a93a8", ha="center")


def scale_bar(ax, s_in):
    """Common scale bar (0-10-20 km) at the true map scale of every panel."""
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    w = ax.get_position().width * ax.figure.get_figwidth()
    km = lambda k: k * s_in / w  # km -> axes fraction
    x0, y0, h = 0.02, 0.42, 0.2
    for i, c in enumerate(["black", "white"]):
        ax.add_patch(Rectangle((x0 + km(10 * i), y0), km(10), h, fc=c, ec="black",
                               lw=0.6, transform=ax.transAxes))
    for k in (0, 10, 20):
        ax.text(x0 + km(k), y0 - 0.08, f"{k}", ha="center", va="top", fontsize=7)
    ax.text(x0 + km(20) + 0.04, y0 - 0.08, "km", ha="left", va="top", fontsize=7)
    ax.text(x0 + km(20) + 0.13, y0 + h / 2, "Common scale\nfor all panels",
            fontsize=6.5, style="italic", color="#444", va="center")


def north_arrow(ax):
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    ax.annotate("", xy=(0.5, 0.98), xytext=(0.5, 0.35),
                arrowprops=dict(arrowstyle="-|>,head_width=0.3,head_length=0.6",
                                lw=1.0, color="black"))
    ax.text(0.5, 0.28, "N", ha="center", va="top", fontsize=9, fontweight="bold")


def main(make_layer=intersection_layer, unit="intersections", stem="study_area_map"):
    d = json.loads((HERE / "study_area_map_data.json").read_text())
    layer, handles = make_layer(d)
    counties = json.loads((HERE / "florida_counties.json").read_text())

    W = 7.16                                     # double-column width (in)
    gap_km, mx = 5.0, 0.06
    widths = [d[k]["w_km"] for k, _, _ in REGIONS]
    s = (W - 2 * mx) / (sum(widths) + 2 * gap_km)  # inches per km
    top_pad, bot_pad = 0.25, 0.08
    H = max(d[k]["h_km"] for k, _, _ in REGIONS) * s + top_pad + bot_pad
    fig = plt.figure(figsize=(W, H))

    x = mx; axes = {}
    for (key, title, _), w in zip(REGIONS, widths):
        h = d[key]["h_km"] * s
        ax = fig.add_axes([x / W, (H - top_pad - h) / H, w * s / W, h / H])
        draw_region(ax, d[key], title, key, layer)
        axes[key] = (x, w * s, h)
        x += (w + gap_km) * s

    # middle column below Orlando: legend, locator, scale bar
    ox, ow, oh = axes["orlando"]
    y_top = H - top_pad - oh - 0.12
    leg_h = 1.05
    lax = fig.add_axes([ox / W, (y_top - leg_h) / H, ow / W, leg_h / H]); lax.axis("off")
    lax.legend(handles=handles, loc="upper left", frameon=False, fontsize=7.5,
               title=f"Land-use context typology ({unit})",
               title_fontproperties={"weight": "bold", "size": 8},
               alignment="left", handletextpad=0.5, labelspacing=0.45,
               borderaxespad=0)

    loc_h = 1.55
    y_loc = y_top - leg_h - 0.08 - loc_h
    loc_w = loc_h * (7.9 * 0.88) / 6.7
    fax = fig.add_axes([(ox + 0.02) / W, y_loc / H, loc_w / W, loc_h / H])
    draw_locator(fax, counties)

    nax = fig.add_axes([(ox + loc_w + 0.15) / W, (y_loc + loc_h - 0.6) / H,
                        0.3 / W, 0.6 / H])
    north_arrow(nax)
    sax = fig.add_axes([(ox + 0.02) / W, (y_loc - 0.45) / H, ow / W, 0.4 / H])
    scale_bar(sax, s)

    for ext, kw in (("pdf", {}), ("png", {"dpi": 600}),
                    ("tiff", {"dpi": 600, "pil_kwargs": {"compression": "tiff_lzw"}})):
        fig.savefig(HERE / f"{stem}.{ext}", bbox_inches="tight",
                    pad_inches=0.03, **kw)


if __name__ == "__main__":
    main()
