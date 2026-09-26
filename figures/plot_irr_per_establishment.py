"""Publication-quality redraw of the per-establishment IRR heatmap
(land use x crash type, intersections and segments).

Layout ideas (consistent with the Moran's I figure):
  * land uses in the same thematic groups, crash types in the same
    mechanism groups, crash counts shown under each crash type
  * diverging log colour mapping centred on IRR = 1
  * explicit cell states: significant (coloured + value), highlighted
    (bold + outline), not significant (faint dot), not estimated (hatched)
  * Times New Roman throughout, vector PDF with embedded TrueType fonts
"""
import json
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap, LogNorm
from matplotlib.legend_handler import HandlerTuple
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Rectangle

HERE = Path(__file__).parent

mpl.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "Times", "Liberation Serif", "Nimbus Roman"],
    "mathtext.fontset": "stix",
    "font.size": 8,
    "axes.linewidth": 0.6,
    "hatch.linewidth": 0.4,
    "pdf.fonttype": 42, "ps.fonttype": 42, "svg.fonttype": "none",
})

LO, HI = 0.25, 4.0                      # symmetric in log space around 1
NORM = LogNorm(LO, HI)
CMAP = LinearSegmentedColormap.from_list("irr_div", [
    (0.0, "#08306b"), (0.25, "#2171b5"), (0.42, "#9ecae1"), (0.5, "#f7f5f0"),
    (0.58, "#fcd3c1"), (0.7, "#fb8a6a"), (0.82, "#d7301f"), (1.0, "#67000d")])
NA_FC, NA_HATCH, NS_DOT = "#eeece7", "#b9b5ab", "#d3cec4"

ROW_GROUPS = [   # same thematic groups as the Moran's I figure
    ("Retail &\ncommercial", ["Mixed-use buildings", "Supermarkets",
                              "Regional shopping centers", "Community shopping centers",
                              "Department / big-box stores", "Single-tenant retail stores"]),
    ("Food, drink\n& lodging", ["Fast-food restaurants", "Sit-down restaurants",
                                "Bars", "Hotels"]),
    ("Automotive", ["Gas stations", "Auto sales & service", "Repair shops"]),
    ("Office &\nservices", ["Office buildings", "Banks"]),
    ("Institutional\n& open space", ["Schools", "Hospitals", "Parks & recreation"]),
    ("Industrial", ["Industrial"]),
]
COL_GROUPS = [("", 0, 0), ("Multi-vehicle", 1, 6), ("Single-veh.", 7, 9),
              ("Road user", 10, 12)]


def cell(grid, row, col):
    """-> (value, highlighted, state) with state in sig / ns / na."""
    r = grid.get(row, {})
    if r == "na":
        return np.nan, False, "na"
    v = r.get(col)
    if v is None:
        return np.nan, False, "ns"
    if isinstance(v, str):
        return float(v.rstrip("*")), v.endswith("*"), "sig"
    return float(v), False, "sig"


def heat(ax, grid, rows, cols, counts, title, tag, labels):
    nr, nc = len(rows), len(cols)
    for i, row in enumerate(rows):
        for j, col in enumerate(cols):
            v, box, st = cell(grid, row, col)
            if st == "na":
                ax.add_patch(Rectangle((j + .05, i + .06), .9, .88, fc=NA_FC,
                                       ec=NA_HATCH, hatch="////", lw=0))
            elif st == "ns":
                ax.plot(j + .5, i + .5, "o", ms=1.3, color=NS_DOT, mew=0)
            else:
                t = NORM(v)
                ax.add_patch(Rectangle((j + .05, i + .06), .9, .88, fc=CMAP(t),
                                       ec="#111" if box else "none",
                                       lw=0.9 if box else 0, zorder=2))
                ax.text(j + .5, i + .53, f"{v:.2f}", ha="center", va="center",
                        fontsize=5.6, zorder=3,
                        color="white" if abs(t - .5) > .27 else "#1a1a1a",
                        fontweight="bold" if box else "normal")
    b = 0
    for _, names in ROW_GROUPS[:-1]:
        b += len(names)
        ax.axhline(b, color="#8a8a8a", lw=0.6)
    for _, _, e in COL_GROUPS[:-1]:
        ax.axvline(e + 1, color="#8a8a8a", lw=0.6)
    ax.set_xlim(0, nc); ax.set_ylim(nr, 0)
    ax.set_xticks(np.arange(nc) + .5)
    ax.set_xticklabels([f"{c}  ({n:,})" for c, n in zip(cols, counts)],
                       rotation=60, ha="right", rotation_mode="anchor", fontsize=7)
    ax.set_yticks(np.arange(nr) + .5)
    ax.set_yticklabels(labels if labels else [])
    ax.tick_params(length=0, pad=3)
    for s in ax.spines.values():
        s.set_color("#8a8a8a"); s.set_linewidth(0.6)
    for name, s, e in COL_GROUPS:
        if not name:
            continue
        ax.plot([s + .12, e + .88], [-0.35, -0.35], color="#555", lw=0.6,
                clip_on=False)
        ax.text((s + e + 1) / 2, -0.55, name, ha="center", va="bottom",
                fontsize=6.5, style="italic", color="#333", clip_on=False)
    ax.set_title(f"({tag}) {title}", loc="left", fontsize=10, fontweight="bold",
                 pad=15)


def row_brackets(ax):
    tr = ax.get_yaxis_transform()
    b = 0
    for name, names in ROW_GROUPS:
        s, e = b, b + len(names); b = e
        x = -0.72
        ax.plot([x, x], [s + .15, e - .15], transform=tr, color="#555", lw=0.7,
                clip_on=False)
        ax.text(x - 0.02, (s + e) / 2, name, transform=tr, ha="right",
                va="center", fontsize=6.8, style="italic", color="#333",
                linespacing=1.0)


def main():
    d = json.loads((HERE / "irr_per_establishment_data.json").read_text())
    rows = [n for _, names in ROW_GROUPS for n in names]
    labels = [n + (" (per 10)" if n in d["per10"] else "")
              + (" †" if n in d["dagger"] else "") for n in rows]
    cols = d["columns"]

    fig = plt.figure(figsize=(7.16, 5.3))
    gs = fig.add_gridspec(1, 3, width_ratios=[13, 13, 0.45], wspace=0.05,
                          left=0.265, right=0.935, top=0.92, bottom=0.22)
    ax1, ax2, cax = (fig.add_subplot(gs[k]) for k in range(3))
    heat(ax1, d["panels"]["Intersections"], rows, cols, d["n"]["int"],
         "Intersections", "a", labels)
    heat(ax2, d["panels"]["Segments"], rows, cols, d["n"]["seg"],
         "Segments", "b", None)
    row_brackets(ax1)
    p = cax.get_position(); cax.set_position([p.x0 + 0.012, p.y0, p.width, p.height])

    sm = mpl.cm.ScalarMappable(norm=NORM, cmap=CMAP)
    ticks = [0.5, 0.67, 1, 1.5, 2, 3, 4]
    cb = fig.colorbar(sm, cax=cax, ticks=ticks, boundaries=np.geomspace(0.5, HI, 257))
    cb.ax.minorticks_off()
    cb.ax.set_yticklabels([f"{t:g}" for t in ticks])
    cb.outline.set_linewidth(0.5)
    cb.ax.tick_params(labelsize=7, width=0.5, length=2)
    cb.set_label("Incidence rate ratio per establishment (log scale)",
                 fontsize=7.5, labelpad=4)

    handles = [(Patch(fc=CMAP(0.72), ec="none"), Patch(fc=CMAP(0.3), ec="none")),
               Patch(fc=CMAP(0.62), ec="#111", lw=0.9),
               Line2D([], [], ls="", marker="o", ms=2, color=NS_DOT),
               Patch(fc=NA_FC, ec=NA_HATCH, hatch="////", lw=0)]
    labels_ = ["Significant IRR ($p$ < 0.05), value shown", d["box_label"],
               "Not significant", "Not estimated"]
    fig.legend(handles=handles, labels=labels_, loc="lower center", ncol=4,
               frameon=False, fontsize=7, bbox_to_anchor=(0.58, 0.0),
               handler_map={tuple: HandlerTuple(ndivide=None, pad=0.1)},
               handlelength=1.4, columnspacing=1.2, handletextpad=0.4)
    fig.text(0.58, -0.005, "Crash counts in parentheses. “per 10”: IRR per 10 "
             "establishments. " + d["dagger_label"] + ".", ha="center", va="top",
             fontsize=6.6, style="italic", color="#444")

    for ext, kw in (("pdf", {}), ("png", {"dpi": 600}),
                    ("tiff", {"dpi": 600, "pil_kwargs": {"compression": "tiff_lzw"}})):
        fig.savefig(HERE / f"irr_per_establishment.{ext}", bbox_inches="tight",
                    pad_inches=0.03, **kw)


if __name__ == "__main__":
    main()
