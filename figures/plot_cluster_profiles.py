"""Publication-quality redraw of the land-use cluster profile heatmap
(cluster mean z-score of log establishment counts; cell text = raw means).

Layout ideas:
  * rows ordered by each cluster's signature land use, so the defining
    cells run down a diagonal; the signature cell (max z) is outlined
  * marginal bar showing cluster size (share of sites / segments)
  * Times New Roman throughout, vector PDF with embedded TrueType fonts
"""
import json
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from matplotlib.patches import Rectangle

HERE = Path(__file__).parent

mpl.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "Times", "Liberation Serif", "Nimbus Roman"],
    "mathtext.fontset": "stix",
    "font.size": 8,
    "axes.linewidth": 0.6,
    "xtick.major.width": 0.5, "ytick.major.width": 0.5,
    "xtick.major.size": 0, "ytick.major.size": 0,
    "pdf.fonttype": 42, "ps.fonttype": 42, "svg.fonttype": "none",
})

VMAX = 2.0
CMAP = LinearSegmentedColormap.from_list(
    "profile_div", ["#08306b", "#2171b5", "#9ecae1", "#f4f2ee",
                    "#fcae91", "#cb181d", "#67000d"])
BAR_C = "#6b6b6b"


def order_rows(z, rows):
    """Sort clusters by the column of their maximum z (diagonal layout);
    clusters with no positive signature go last."""
    sig = z.argmax(1)
    key = [(sig[i] if z[i].max() > 0.3 else 99, -z[i].max()) for i in range(len(rows))]
    return sorted(range(len(rows)), key=lambda i: key[i])


def panel(ax, bx, d, cols, title, tag, unit, show_x):
    z = np.array(d["z"]); mean = np.array(d["mean"]); n = np.array(d["n"])
    idx = order_rows(z, d["rows"])
    z, mean, n = z[idx], mean[idx], n[idx]
    rows = [d["rows"][i] for i in idx]
    nr, nc = z.shape

    im = ax.pcolormesh(np.arange(nc + 1), np.arange(nr + 1), z, cmap=CMAP,
                       norm=TwoSlopeNorm(0, -VMAX, VMAX),
                       edgecolor="white", linewidth=1.0)
    ax.set_xlim(0, nc); ax.set_ylim(nr, 0)
    for i in range(nr):
        for j in range(nc):
            dark = abs(z[i, j]) > 1.1
            ax.text(j + .5, i + .5, f"{mean[i, j]:.1f}", ha="center", va="center",
                    fontsize=7.5, color="white" if dark else "#1a1a1a")
        j = z[i].argmax()
        if z[i, j] > 0.3:  # signature land use of the cluster
            ax.add_patch(Rectangle((j + .04, i + .06), .92, .88, fill=False,
                                   ec="black", lw=1.1, zorder=4))

    ax.set_yticks(np.arange(nr) + .5)
    ax.set_yticklabels(rows)
    ax.set_xticks(np.arange(nc) + .5)
    ax.set_xticklabels(cols if show_x else [], rotation=30, ha="right",
                       rotation_mode="anchor")
    ax.tick_params(pad=3)
    for s in ax.spines.values():
        s.set_color("#3a3a3a")
    ax.set_title(f"({tag}) {title}", loc="left", fontsize=10, fontweight="bold", pad=4)
    ax.text(1.0, 1.015, f"cell values: mean establishments {unit}",
            transform=ax.transAxes, ha="right", va="bottom", fontsize=7,
            style="italic", color="#444")

    # marginal cluster-size bar
    share = 100 * n / n.sum()
    y = np.arange(nr) + .5
    bx.barh(y, share, height=.5, color=BAR_C, lw=0)
    for yi, s, k in zip(y, share, n):
        bx.text(s + 1, yi, f"{k}", va="center", fontsize=7, color="#333")
    bx.set_ylim(nr, 0); bx.set_xlim(0, 45); bx.set_yticks([])
    bx.set_xticks([0, 20, 40])
    bx.tick_params(axis="x", labelsize=6.5, length=2)
    for side in ("top", "right", "left"):
        bx.spines[side].set_visible(False)
    bx.set_xlabel("Share of units (%)" if show_x else "", fontsize=7, labelpad=2)
    bx.set_title("Cluster size ($n$)", fontsize=7, style="italic", color="#444",
                 pad=4, loc="left")
    return im


def main():
    d = json.loads((HERE / "cluster_profiles_data.json").read_text())
    cols = d["columns"]
    fig = plt.figure(figsize=(7.16, 5.0))
    gs = fig.add_gridspec(2, 3, width_ratios=[7, 1.25, 0.18], hspace=0.28,
                          wspace=0.06, left=0.25, right=0.9, top=0.94, bottom=0.2)
    ax1, bx1 = fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1])
    ax2, bx2 = fig.add_subplot(gs[1, 0]), fig.add_subplot(gs[1, 1])
    cax = fig.add_subplot(gs[:, 2])

    im = panel(ax1, bx1, d["int"], cols, "Intersections", "a", "per site", False)
    panel(ax2, bx2, d["seg"], cols, "Segments", "b", "per mile", True)

    ticks = np.linspace(-VMAX, VMAX, 9)
    cb = fig.colorbar(im, cax=cax, ticks=ticks, extend="both", extendfrac=0.03)
    cb.outline.set_linewidth(0.5)
    cb.ax.tick_params(labelsize=7, width=0.5, length=2)
    cb.ax.set_yticklabels([f"{t:.1f}".replace("-", "−") for t in ticks])
    cb.set_label("Cluster mean ($z$-score of log count)", fontsize=8, labelpad=4)

    fig.text(0.575, -0.02,
             "Colour: cluster mean of standardized log establishment counts. "
             "Boxed cell: signature land use of each cluster (highest $z$).\n"
             "Rows ordered by signature land use; clusters with no dominant land use "
             "listed last.",
             ha="center", va="bottom", fontsize=6.8, style="italic", color="#444")

    for ext, kw in (("pdf", {}), ("png", {"dpi": 600}),
                    ("tiff", {"dpi": 600, "pil_kwargs": {"compression": "tiff_lzw"}})):
        fig.savefig(HERE / f"cluster_profiles_heatmap.{ext}", bbox_inches="tight",
                    pad_inches=0.03, **kw)


if __name__ == "__main__":
    main()
