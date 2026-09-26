"""Publication-quality redraw of the incidence-rate-ratio (IRR) heatmap:
land-use context vs low-intensity frontage, by crash type and severity.

Layout ideas:
  * one diverging LOG colour mapping centred on IRR = 1 (0.1 -> 10), shared
    by the intersection and segment figures; each colour bar shows only
    the range its figure uses
  * three explicit cell states: significant (coloured, labelled),
    not significant (blank with a faint dot), not estimated (hatched)
  * crash types grouped as in the Moran's I figure; a key row (pedestrian)
    is highlighted across panels

Usage: python plot_irr_heatmap.py [data.json] [output_stem]
  * Times New Roman throughout, vector PDF with embedded TrueType fonts
"""
import json
import sys
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap, LogNorm
from matplotlib.legend_handler import HandlerTuple
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

VMIN, VMAX = 0.1, 10.0          # symmetric in log space around IRR = 1
NORM = LogNorm(VMIN, VMAX)
CMAP = LinearSegmentedColormap.from_list("irr_div", [
    (0.0, "#08306b"), (0.25, "#2171b5"), (0.42, "#9ecae1"), (0.5, "#f7f5f0"),
    (0.55, "#fde5d8"), (0.6, "#fcae91"), (0.7, "#fb6a4a"), (0.8, "#cb181d"),
    (0.9, "#8e0b17"), (1.0, "#4a0010")])
NA_FC, NA_HATCH, NS_DOT = "#eeece7", "#b9b5ab", "#cfcac0"
ROW_GROUPS = [("Overall", 0, 0), ("Multi-\nvehicle", 1, 6), ("Single-\nvehicle", 7, 9),
              ("Road user /\nfactor", 10, 12)]
SEVERITY_NOTE = {"Total": "all injury levels", "KAB": "K + A + B",
                 "KSI": "killed or seriously injured", "Fatal": "K only"}


def parse(cell):
    """-> (value for colour, label, state)"""
    if cell == "ns":
        return np.nan, "", "ns"
    if cell == "na":
        return np.nan, "", "na"
    if isinstance(cell, dict):
        return VMAX, f">{cell['gt']:g}", "sig"
    return float(cell), f"{cell:.1f}", "sig"


def panel(ax, grid, rows, cols, title, show_y, highlight):
    nr, nc = len(rows), len(cols)
    norm = NORM
    hi = rows.index(highlight)
    ax.add_patch(Rectangle((-0.02, hi + 0.02), nc + 0.04, 0.96, fc="none",
                           ec="#222", lw=0.9, zorder=5, clip_on=False))
    for i in range(nr):
        for j in range(nc):
            v, lab, st = parse(grid[i][j])
            if st == "na":
                ax.add_patch(Rectangle((j + .06, i + .06), .88, .88, fc=NA_FC,
                                       ec=NA_HATCH, hatch="////", lw=0))
            elif st == "ns":
                ax.plot(j + .5, i + .5, "o", ms=1.6, color=NS_DOT, mew=0)
            else:
                ax.add_patch(Rectangle((j + .06, i + .06), .88, .88,
                                       fc=CMAP(norm(v)), ec="none", zorder=2))
                dark = abs(norm(v) - 0.5) > 0.2
                ax.text(j + .5, i + .52, lab, ha="center", va="center",
                        fontsize=7.5, color="white" if dark else "#1a1a1a",
                        fontweight="bold" if (v >= 2 or v <= 0.5) else "normal", zorder=3)
    for _, _, e in ROW_GROUPS[:-1]:
        ax.axhline(e + 1, color="#8a8a8a", lw=0.6)
    ax.set_xlim(0, nc); ax.set_ylim(nr, 0)
    ax.set_xticks(np.arange(nc) + .5)
    ax.set_xticklabels(cols, rotation=55, ha="right", rotation_mode="anchor")
    ax.set_yticks(np.arange(nr) + .5)
    ax.set_yticklabels(rows if show_y else [])
    if show_y:
        for t in ax.get_yticklabels():
            if t.get_text() == highlight:
                t.set_fontweight("bold")
    ax.tick_params(length=0, pad=3)
    for s in ax.spines.values():
        s.set_color("#8a8a8a"); s.set_linewidth(0.6)
    ax.set_title(title, fontsize=10, fontweight="bold", pad=11)
    ax.text(0.5, 1.012, SEVERITY_NOTE[title], transform=ax.transAxes,
            ha="center", va="bottom", fontsize=6.8, style="italic", color="#555")


def row_brackets(ax):
    tr = ax.get_yaxis_transform()
    for name, s, e in ROW_GROUPS:
        x = -0.78
        ax.plot([x, x], [s + .15, e + .85], transform=tr, color="#555", lw=0.7,
                clip_on=False)
        ax.text(x - 0.04, (s + e + 1) / 2, name, transform=tr, ha="right",
                va="center", fontsize=6.8, style="italic", color="#333",
                linespacing=1.0)


def main(data="irr_heatmap_data.json", stem="irr_heatmap"):
    d = json.loads((HERE / data).read_text())
    hl = d["highlight"]
    vals = [parse(c)[0] for g in d["panels"].values() for r in g for c in r]
    lo = 1.0 if np.nanmin(vals) >= 1 else 0.25   # colour-bar range shown
    rows, cols = d["rows"], d["columns"]
    fig = plt.figure(figsize=(7.16, 4.6))
    gs = fig.add_gridspec(1, 5, width_ratios=[4, 4, 4, 4, 0.28], wspace=0.12,
                          left=0.19, right=0.93, top=0.9, bottom=0.25)
    axes = [fig.add_subplot(gs[k]) for k in range(4)]
    for k, (ax, name) in enumerate(zip(axes, d["panels"])):
        panel(ax, d["panels"][name], rows, cols, name, k == 0, hl["row"])
    row_brackets(axes[0])

    cax = fig.add_subplot(gs[4])
    sm = mpl.cm.ScalarMappable(norm=NORM, cmap=CMAP)
    ticks = [t for t in (0.25, 0.33, 0.5, 0.67, 1, 1.5, 2, 3, 5, 10) if t >= lo]
    cb = fig.colorbar(sm, cax=cax, ticks=ticks, extend="max", extendfrac=0.04,
                      boundaries=np.geomspace(lo, VMAX, 257))
    cb.ax.minorticks_off()
    cb.ax.set_yticklabels([f"{t:g}" for t in ticks])
    cb.outline.set_linewidth(0.5)
    cb.ax.tick_params(labelsize=7, width=0.5, length=2)
    cb.set_label("Incidence rate ratio vs low-intensity frontage (log scale)",
                 fontsize=7.5, labelpad=4)

    sig = (Patch(fc=CMAP(0.72), ec="none"),) + (
        (Patch(fc=CMAP(0.3), ec="none"),) if lo < 1 else ())
    handles = [sig,
               mpl.lines.Line2D([], [], ls="", marker="o", ms=2.2, color=NS_DOT),
               Patch(fc=NA_FC, ec=NA_HATCH, hatch="////", lw=0),
               Patch(fc="none", ec="#222", lw=0.9)]
    labels = ["Significant IRR ($p$ < 0.05), value shown", "Not significant",
              "Not estimated", hl["label"]]
    fig.legend(handles=handles, labels=labels, loc="lower center",
               handler_map={tuple: HandlerTuple(ndivide=None, pad=0.1)}, ncol=4, frameon=False,
               fontsize=7.2, bbox_to_anchor=(0.55, -0.045), handlelength=1.3,
               columnspacing=1.4, handletextpad=0.45)

    for ext, kw in (("pdf", {}), ("png", {"dpi": 600}),
                    ("tiff", {"dpi": 600, "pil_kwargs": {"compression": "tiff_lzw"}})):
        fig.savefig(HERE / f"{stem}.{ext}", bbox_inches="tight",
                    pad_inches=0.03, **kw)


if __name__ == "__main__":
    main(*sys.argv[1:3])
