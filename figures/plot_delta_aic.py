"""Publication-quality redraw of the model-comparison figure: does adding
land use improve the design-only crash models?

Layout ideas:
  * cell colour = delta AIC (design-only minus design + land use) on a
    brown-teal diverging scale, deliberately distinct from the red/blue
    risk scale of the IRR figures (teal = land use improves the model)
  * each cell carries a micro-bar for the McFadden pseudo-R2 gain, so both
    measures read at a glance; LR-test significance keeps its asterisk and
    is also set in bold
  * crash types grouped as in the other figures; not-estimated cells hatched
  * Times New Roman throughout, vector PDF with embedded TrueType fonts
"""
import json
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from matplotlib.patches import Patch, Rectangle

from plot_irr_heatmap import ROW_GROUPS

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

VMAX = 30
NORM = TwoSlopeNorm(0, -VMAX, VMAX)
CMAP = LinearSegmentedColormap.from_list("aic_div", [
    "#543005", "#8c510a", "#dfc27d", "#f5f3ee", "#80cdc1", "#01665e", "#003c30"])
NA_FC, NA_HATCH = "#eeece7", "#b9b5ab"
R2_MAX = 12.0      # pseudo-R2 gain (pts) mapped to full micro-bar width


def panel(ax, grid, rows, cols, title, tag, show_y):
    nr, nc = len(rows), len(cols)
    for i in range(nr):
        for j in range(nc):
            c = grid[i][j]
            if c is None:
                ax.add_patch(Rectangle((j + .04, i + .05), .92, .9, fc=NA_FC,
                                       ec=NA_HATCH, hatch="////", lw=0))
                continue
            txt, r2 = c
            v = float(txt.rstrip("*"))
            sig = txt.endswith("*")
            t = NORM(v)
            ax.add_patch(Rectangle((j + .04, i + .05), .92, .9, fc=CMAP(t),
                                   ec="none", zorder=1))
            dark = abs(t - .5) > .3
            ink = "white" if dark else "#1a1a1a"
            ax.text(j + .5, i + .36, txt.replace("-", "−"), ha="center",
                    va="center", fontsize=7.4, color=ink,
                    fontweight="bold" if sig else "normal", zorder=3)
            # pseudo-R2 micro-bar + value
            w = 0.52 * min(r2, R2_MAX) / R2_MAX
            ax.add_patch(Rectangle((j + .1, i + .66), 0.52, .13, fc="none",
                                   ec=ink, lw=0.3, alpha=0.5, zorder=2))
            ax.add_patch(Rectangle((j + .1, i + .66), w, .13, fc=ink, lw=0,
                                   alpha=0.85, zorder=2))
            ax.text(j + .66, i + .725, f"{r2:.1f}", ha="left", va="center",
                    fontsize=5.6, color=ink, zorder=3)
    for _, _, e in ROW_GROUPS[:-1]:
        ax.axhline(e + 1, color="#8a8a8a", lw=0.6)
    ax.set_xlim(0, nc); ax.set_ylim(nr, 0)
    ax.set_xticks(np.arange(nc) + .5); ax.set_xticklabels(cols)
    ax.xaxis.tick_top()
    ax.set_yticks(np.arange(nr) + .5)
    ax.set_yticklabels(rows if show_y else [])
    ax.tick_params(length=0, pad=3)
    for s in ax.spines.values():
        s.set_color("#8a8a8a"); s.set_linewidth(0.6)
    ax.set_title(f"({tag}) {title}", loc="left", fontsize=10, fontweight="bold",
                 pad=16)


def row_brackets(ax):
    tr = ax.get_yaxis_transform()
    for name, s, e in ROW_GROUPS:
        x = -0.43
        ax.plot([x, x], [s + .15, e + .85], transform=tr, color="#555", lw=0.7,
                clip_on=False)
        ax.text(x - 0.03, (s + e + 1) / 2, name, transform=tr, ha="right",
                va="center", fontsize=6.8, style="italic", color="#333",
                linespacing=1.0)


def main():
    d = json.loads((HERE / "delta_aic_data.json").read_text())
    fig = plt.figure(figsize=(7.16, 5.0))
    gs = fig.add_gridspec(1, 3, width_ratios=[4, 4, 0.22], wspace=0.08,
                          left=0.2, right=0.9, top=0.9, bottom=0.12)
    ax1, ax2, cax = (fig.add_subplot(gs[k]) for k in range(3))
    panel(ax1, d["panels"]["Intersections"], d["rows"], d["columns"],
          "Intersections", "a", True)
    panel(ax2, d["panels"]["Segments"], d["rows"], d["columns"],
          "Segments", "b", False)
    row_brackets(ax1)

    sm = mpl.cm.ScalarMappable(norm=NORM, cmap=CMAP)
    cb = fig.colorbar(sm, cax=cax, ticks=range(-30, 31, 10), extend="neither")
    cb.ax.set_yticklabels([f"{t:+d}".replace("-", "−") if t else "0"
                           for t in range(-30, 31, 10)])
    cb.outline.set_linewidth(0.5)
    cb.ax.tick_params(labelsize=7, width=0.5, length=2)
    cb.set_label("$\\Delta$AIC (design-only − design + land use)", fontsize=7.8,
                 labelpad=3)
    cax.text(0.5, 1.02, "land use\nimproves fit", transform=cax.transAxes,
             ha="center", va="bottom", fontsize=6.5, style="italic", color="#01665e")
    cax.text(0.5, -0.02, "no\nimprovement", transform=cax.transAxes,
             ha="center", va="top", fontsize=6.5, style="italic", color="#8c510a")

    handles = [Patch(fc="#555", ec="none"), Patch(fc=NA_FC, ec=NA_HATCH, hatch="////", lw=0)]
    fig.legend(handles=handles,
               labels=[f"Micro-bar: gain in McFadden pseudo-$R^2$ (percentage points; full bar = {R2_MAX:g})",
                       "Joint model not estimated"],
               loc="lower center", ncol=2, frameon=False, fontsize=7.2,
               bbox_to_anchor=(0.5, 0.0), handlelength=1.4, columnspacing=1.6)
    fig.text(0.5, -0.01, "Top line: $\\Delta$AIC; bold with * = likelihood-ratio test of all "
             "land uses jointly, $p$ < 0.05.", ha="center", fontsize=6.8,
             style="italic", color="#444")

    for ext, kw in (("pdf", {}), ("png", {"dpi": 600}),
                    ("tiff", {"dpi": 600, "pil_kwargs": {"compression": "tiff_lzw"}})):
        fig.savefig(HERE / f"delta_aic.{ext}", bbox_inches="tight",
                    pad_inches=0.03, **kw)


if __name__ == "__main__":
    main()
