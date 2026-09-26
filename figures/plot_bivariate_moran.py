"""Publication-quality redraw of the bivariate Moran's I heatmap
(land use x spatial lag of KAB Empirical-Bayes crash rate).

Layout ideas:
  * land uses grouped thematically (row brackets), crash types grouped by mechanism
  * a marginal "significance balance" bar for every land use and panel
  * Times New Roman throughout, vector PDF with embedded TrueType fonts
"""
import json
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from matplotlib.lines import Line2D

HERE = Path(__file__).parent

mpl.rcParams.update({
    "font.family": "serif",
    # Liberation Serif is metric-identical to Times New Roman (fallback on Linux)
    "font.serif": ["Times New Roman", "Times", "Liberation Serif", "Nimbus Roman"],
    "mathtext.fontset": "stix",
    "font.size": 8,
    "axes.linewidth": 0.6,
    "xtick.major.width": 0.5, "ytick.major.width": 0.5,
    "xtick.major.size": 2, "ytick.major.size": 0,
    "pdf.fonttype": 42, "ps.fonttype": 42, "svg.fonttype": "none",
})

LAND_USES = ["Mixed-use buildings", "Gas stations", "Supermarkets",
             "Regional shopping centers", "Community shopping centers",
             "Fast-food restaurants", "Sit-down restaurants", "Bars", "Hotels",
             "Office buildings", "Department / big-box stores", "Banks",
             "Auto sales & service", "Repair shops", "Single-tenant retail stores",
             "Parks & recreation", "Schools", "Hospitals", "Industrial"]
CRASHES = ["All", "Angle", "Left turn", "Right turn", "Rear end", "Sideswipe",
           "Head on", "Run-off-road", "Rollover", "Single veh.", "Pedestrian",
           "Bicycle", "Alcohol"]

ROW_GROUPS = [
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
COL_GROUPS = [("Total", 0, 0), ("Multi-vehicle", 1, 6),
              ("Single-veh.", 7, 9), ("Road user", 10, 12)]

VMAX = 0.20
CMAP = LinearSegmentedColormap.from_list(
    "moran_div", ["#08306b", "#2171b5", "#9ecae1", "#f4f2ee",
                  "#fcae91", "#cb181d", "#67000d"])
NEG_C, POS_C = "#2171b5", "#cb181d"


def load():
    raw = json.loads((HERE / "bivariate_moran_data.json").read_text())
    order = [LAND_USES.index(n) for _, names in ROW_GROUPS for n in names]
    out = {}
    for key in ("int", "seg"):
        v = np.array(raw[key]["v"])[order]
        m = np.array(raw[key]["m"])[order]
        out[key] = (v, m)
    labels = [LAND_USES[i] for i in order]
    return out, labels


def heat(ax, v, m, title, tag, show_y, labels):
    nr, nc = v.shape
    norm = TwoSlopeNorm(0, -VMAX, VMAX)
    im = ax.pcolormesh(np.arange(nc + 1), np.arange(nr + 1), v, cmap=CMAP,
                       norm=norm, edgecolor="white", linewidth=0.6)
    ax.set_xlim(0, nc); ax.set_ylim(nr, 0)
    yy, xx = np.nonzero(m == 1)
    ax.scatter(xx + .5, yy + .5, s=13, c="black", lw=0, zorder=3)
    yy, xx = np.nonzero(m == -1)
    ax.scatter(xx + .5, yy + .5, s=13, facecolor="white", edgecolor="black",
               lw=0.7, zorder=3)

    # row-group and column-group separators
    b = 0
    for _, names in ROW_GROUPS[:-1]:
        b += len(names)
        ax.axhline(b, color="#3a3a3a", lw=0.9)
    for _, s, e in COL_GROUPS[:-1]:
        ax.axvline(e + 1, color="#3a3a3a", lw=0.9)

    ax.set_xticks(np.arange(nc) + .5)
    ax.set_xticklabels(CRASHES, rotation=55, ha="right", rotation_mode="anchor")
    ax.set_yticks(np.arange(nr) + .5)
    ax.set_yticklabels(labels if show_y else [])
    ax.tick_params(axis="y", length=0, pad=3)
    for s in ax.spines.values():
        s.set_color("#3a3a3a")

    # column-group header brackets
    for name, s, e in COL_GROUPS:
        ax.annotate("", xy=(s + .12, -0.35), xytext=(e + .88, -0.35),
                    xycoords="data", annotation_clip=False,
                    arrowprops=dict(arrowstyle="-", lw=0.6, color="#555"))
        ax.text((s + e + 1) / 2, -0.55, name if e > s else "", ha="center",
                va="bottom", fontsize=6.5, style="italic", color="#333",
                clip_on=False)
    ax.set_title(f"({tag}) {title}", fontsize=10, fontweight="bold",
                 pad=17, loc="left")
    return im


def balance(ax, m):
    """Marginal bar: number of significant +/- associations per land use."""
    nr = m.shape[0]
    pos = (m == 1).sum(1); neg = (m == -1).sum(1)
    y = np.arange(nr) + .5
    ax.barh(y, pos, height=.62, color=POS_C, lw=0)
    ax.barh(y, -neg, height=.62, color=NEG_C, lw=0)
    ax.axvline(0, color="#3a3a3a", lw=0.6)
    b = 0
    for _, names in ROW_GROUPS[:-1]:
        b += len(names)
        ax.axhline(b, color="#bbbbbb", lw=0.5, ls=(0, (2, 2)))
    lim = 13
    ax.set_xlim(-lim, lim); ax.set_ylim(nr, 0)
    ax.set_yticks([])
    ax.set_xticks([-10, 0, 10]); ax.set_xticklabels(["10", "0", "10"], fontsize=6.5)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.set_xlabel("sig. cells\n$-$  |  +", fontsize=6.5, labelpad=1)
    ax.text(0, -0.55, "Balance", ha="center", va="bottom", fontsize=6.5,
            style="italic", color="#333", clip_on=False)


def row_brackets(fig, ax):
    """Thematic land-use group labels to the far left of panel (a)."""
    tr = ax.get_yaxis_transform()
    b = 0
    for name, names in ROW_GROUPS:
        s, e = b, b + len(names); b = e
        x = -0.83
        ax.plot([x, x], [s + .15, e - .15], transform=tr, color="#555",
                lw=0.7, clip_on=False)
        ax.text(x - 0.02, (s + e) / 2, name, transform=tr, ha="right",
                va="center", fontsize=6.8, style="italic", color="#333",
                linespacing=1.0)


def main():
    data, labels = load()
    fig = plt.figure(figsize=(7.16, 5.1))  # double-column width (in)
    gs = fig.add_gridspec(1, 5, width_ratios=[13, 2.3, 13, 2.3, 0.45],
                          wspace=0.08, left=0.265, right=0.935,
                          top=0.9, bottom=0.2)
    ax1 = fig.add_subplot(gs[0]); bx1 = fig.add_subplot(gs[1])
    ax2 = fig.add_subplot(gs[2]); bx2 = fig.add_subplot(gs[3])
    cax = fig.add_subplot(gs[4])

    im = heat(ax1, *data["int"], "Intersections", "a", True, labels)
    balance(bx1, data["int"][1])
    heat(ax2, *data["seg"], "Segments", "b", False, labels)
    balance(bx2, data["seg"][1])
    row_brackets(fig, ax1)

    # shift the right-hand pair slightly to open a gutter between panels
    for a in (ax2, bx2):
        p = a.get_position(); a.set_position([p.x0 + 0.012, p.y0, p.width, p.height])

    cb = fig.colorbar(im, cax=cax, ticks=np.linspace(-VMAX, VMAX, 9))
    cb.outline.set_linewidth(0.5)
    cb.ax.tick_params(labelsize=7, width=0.5, length=2)
    cb.ax.set_yticklabels([f"{t:.2f}".replace("-", "−")
                           for t in np.linspace(-VMAX, VMAX, 9)])
    cb.set_label("Bivariate Moran’s $I$\n(land use × spatial lag of KAB EB rate)",
                 fontsize=7.5, labelpad=4)
    handles = [
        Line2D([], [], ls="", marker="o", ms=4.5, mfc="black", mec="black",
               label="Significant positive association"),
        Line2D([], [], ls="", marker="o", ms=4.5, mfc="white", mec="black",
               mew=0.7, label="Significant negative association"),
        Line2D([], [], ls="", marker="s", ms=5, mfc=POS_C, mec="none",
               label="No. of significant +/− cells (Balance)"),
    ]
    handles[2] = (Line2D([], [], ls="", marker="s", ms=5, mfc=NEG_C, mec="none"),
                  handles[2])
    from matplotlib.legend_handler import HandlerTuple
    fig.legend(handles=[handles[0], handles[1], handles[2]],
               labels=[h.get_label() if not isinstance(h, tuple) else h[1].get_label()
                       for h in handles],
               handler_map={tuple: HandlerTuple(ndivide=None, pad=0.2)},
               loc="lower center", ncol=3, frameon=False, fontsize=7.5,
               bbox_to_anchor=(0.6, 0.005), handletextpad=0.4, columnspacing=1.6)
    fig.text(0.6, 0.0, "Permutation test, $p$ < 0.05 (499 permutations); "
             "– denotes fewer than 10 crashes.", ha="center", va="bottom",
             fontsize=6.8, style="italic", color="#444")

    for ext, kw in (("pdf", {}), ("png", {"dpi": 600}), ("tiff", {"dpi": 600, "pil_kwargs": {"compression": "tiff_lzw"}})):
        fig.savefig(HERE / f"bivariate_moran_heatmap.{ext}", bbox_inches="tight",
                    pad_inches=0.03, **kw)


if __name__ == "__main__":
    main()
