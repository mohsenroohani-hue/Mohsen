"""Publication-quality redraw of the joint-model forest plot: IRR (95% CI)
per establishment for all crash types, by land use and severity.

Layout ideas:
  * land uses in the same thematic groups as the other figures
  * significance emphasis: p < 0.05 estimates drawn filled and at full
    strength; non-significant estimates hollow and faded, so the few
    significant results stand out instead of competing with 150 intervals
  * severity encoded by colour ramp AND marker shape (print / CVD safe)
  * CIs beyond the axis limits end in arrowheads rather than being cut
  * Times New Roman throughout, vector PDF with embedded TrueType fonts
"""
import json
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D

from plot_irr_per_establishment import ROW_GROUPS

HERE = Path(__file__).parent

mpl.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "Times", "Liberation Serif", "Nimbus Roman"],
    "mathtext.fontset": "stix",
    "font.size": 8,
    "axes.linewidth": 0.6,
    "xtick.major.width": 0.5, "xtick.minor.width": 0.4,
    "pdf.fonttype": 42, "ps.fonttype": 42, "svg.fonttype": "none",
})

SEV = [("Total", "#86b4e3", "o", 4.2), ("KAB", "#3a7fd0", "s", 3.8),
       ("KSI", "#1d4f91", "D", 3.6), ("Fatal", "#0b2447", "^", 4.4)]
DODGE = [-0.3, -0.1, 0.1, 0.3]
XMIN, XMAX = 0.2, 5.0
NS_ALPHA = 0.38


def draw(ax, panel, rows):
    ny = len(rows)
    for i in range(ny):
        if i % 2 == 0:
            ax.axhspan(i - 0.5, i + 0.5, color="#f4f3ef", lw=0, zorder=0)
    b = 0
    for _, names in ROW_GROUPS[:-1]:
        b += len(names)
        ax.axhline(b - 0.5, color="#9a9a9a", lw=0.6, zorder=1)
    ax.axvline(1, color="#333", lw=0.8, zorder=1)
    for i, lu in enumerate(rows):
        est = panel.get(lu, {})
        if not est:
            ax.text(1, i, "not estimated", ha="center", va="center", fontsize=6.5,
                    style="italic", color="#888")
            continue
        for (sev, col, mk, ms), dy in zip(SEV, DODGE):
            e = est.get(sev)
            if not e:
                continue
            y = i + dy
            a = 1.0 if e["sig"] else NS_ALPHA
            lw = 1.25 if e["sig"] else 0.9
            lo, hi = max(e["lo"], XMIN), min(e["hi"], XMAX)
            ax.plot([lo, hi], [y, y], color=col, lw=lw, alpha=a,
                    solid_capstyle="butt", zorder=2)
            for clip, end, d in ((e["lo_clipped"], XMIN, -1), (e["hi_clipped"], XMAX, 1)):
                if clip:
                    ax.annotate("", xy=(end, y), xytext=(end / 1.12 ** d, y),
                                arrowprops=dict(arrowstyle="-|>,head_width=0.18,head_length=0.35",
                                                color=col, lw=lw, alpha=a,
                                                shrinkA=0, shrinkB=0), zorder=2)
            ax.plot(e["irr"], y, marker=mk, ms=ms, mew=0.9, zorder=3,
                    mfc=col if e["sig"] else "white", mec=col, alpha=a if not e["sig"] else 1)
    ax.set_xscale("log")
    ax.set_xlim(XMIN, XMAX); ax.set_ylim(ny - 0.5, -0.5)
    ticks = [0.25, 0.5, 1, 2, 4]
    ax.set_xticks(ticks); ax.set_xticklabels([f"{t:g}" for t in ticks])
    ax.xaxis.set_minor_formatter(mpl.ticker.NullFormatter())
    ax.xaxis.grid(True, which="major", color="#dedcd6", lw=0.5, zorder=0)
    ax.tick_params(axis="y", length=0, pad=3)
    for s in ax.spines.values():
        s.set_color("#8a8a8a")


def row_brackets(ax):
    """Group brackets placed just left of the longest land-use label."""
    fig = ax.figure
    fig.canvas.draw()
    inv = ax.transAxes.inverted()
    left = min(inv.transform(t.get_window_extent().get_points())[0, 0]
               for t in ax.get_yticklabels())
    tr = ax.get_yaxis_transform()
    b = 0
    for name, names in ROW_GROUPS:
        s, e = b, b + len(names); b = e
        x = left - 0.025
        ax.plot([x, x], [s - 0.35, e - 0.65], transform=tr, color="#555", lw=0.7,
                clip_on=False)
        ax.text(x - 0.03, (s + e - 1) / 2, name, transform=tr, ha="right",
                va="center", fontsize=6.8, style="italic", color="#333",
                linespacing=1.0)


def main():
    d = json.loads((HERE / "forest_plot_data.json").read_text())
    meta = json.loads((HERE / "irr_per_establishment_total_data.json").read_text())
    rows = [n for _, names in ROW_GROUPS for n in names]
    labels = [n + (" (per 10)" if n in meta["per10"] else "")
              + (" †" if n in meta["dagger"] else "") for n in rows]

    fig, axes = plt.subplots(1, 2, figsize=(7.16, 6.2), sharey=True,
                             gridspec_kw=dict(wspace=0.05, left=0.36, right=0.99,
                                              top=0.95, bottom=0.14))
    for ax, (panel, tag) in zip(axes, [("Intersections", "a"), ("Segments", "b")]):
        draw(ax, d["panels"][panel], rows)
        ax.set_title(f"({tag}) {panel} — all crash types", loc="left",
                     fontsize=10, fontweight="bold", pad=5)
    axes[0].set_yticks(range(len(rows)))
    axes[0].set_yticklabels(labels)
    row_brackets(axes[0])

    fig.text(0.645, 0.066, "IRR per establishment (95% CI), joint model — log scale",
             ha="center", fontsize=8)
    handles = [Line2D([], [], color=col, lw=1.25, marker=mk, ms=ms, mfc=col, mec=col,
                      label=sev) for sev, col, mk, ms in SEV]
    handles += [Line2D([], [], color="#555", lw=1.25, marker="o", ms=4, mfc="#555",
                       label="$p$ < 0.05 (filled, full strength)"),
                Line2D([], [], color="#555", lw=0.9, marker="o", ms=4, mfc="white",
                       alpha=NS_ALPHA + 0.1, label="n.s. (hollow, faded)")]
    fig.legend(handles=handles, loc="lower center", ncol=6, frameon=False,
               fontsize=7.3, bbox_to_anchor=(0.62, 0.025), handlelength=1.8,
               columnspacing=1.1, handletextpad=0.4)
    fig.text(0.62, 0.012, d["footnote"].replace("Filled = p < 0.05; hollow = n.s.; ", "")
             + ". Arrowheads: interval extends beyond the axis.",
             ha="center", fontsize=6.8, style="italic", color="#444")

    for ext, kw in (("pdf", {}), ("png", {"dpi": 600}),
                    ("tiff", {"dpi": 600, "pil_kwargs": {"compression": "tiff_lzw"}})):
        fig.savefig(HERE / f"forest_plot.{ext}", bbox_inches="tight",
                    pad_inches=0.03, **kw)


if __name__ == "__main__":
    main()
