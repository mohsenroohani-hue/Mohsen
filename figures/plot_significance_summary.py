"""Summary of significant per-establishment IRRs by land use and severity,
computed directly from the four irr_per_establishment_*_data.json files
(so it can never drift out of sync with the heatmaps).

Layout ideas:
  * diverging stacked bars: IRR > 1 to the right in reds, IRR < 1 to the
    left in blues (same colour semantics as the IRR heatmaps); darker shade
    = more severe crash subset (Total -> KAB -> KSI -> Fatal)
  * one land-use order shared by both panels (net count, both facilities)
  * net count printed at the end of each bar
  * Times New Roman throughout, vector PDF with embedded TrueType fonts
"""
import json
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.legend_handler import HandlerTuple
from matplotlib.patches import Patch

HERE = Path(__file__).parent

mpl.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "Times", "Liberation Serif", "Nimbus Roman"],
    "mathtext.fontset": "stix",
    "font.size": 8,
    "axes.linewidth": 0.6,
    "xtick.major.width": 0.5, "ytick.major.width": 0.5,
    "pdf.fonttype": 42, "ps.fonttype": 42, "svg.fonttype": "none",
})

SEVERITIES = [("total", "Total"), ("kab", "KAB"), ("ksi", "KSI"), ("fatal", "Fatal")]
POS = ["#fcbba1", "#fb6a4a", "#cb181d", "#67000d"]   # IRR > 1, light -> severe
NEG = ["#c6dbef", "#6baed6", "#2171b5", "#08306b"]   # IRR < 1
PANELS = [("Intersections", "a"), ("Segments", "b")]


def counts():
    """-> {panel: {land use: (pos[4], neg[4])}}"""
    out = {p: {} for p, _ in PANELS}
    for k, (sev, _) in enumerate(SEVERITIES):
        d = json.loads((HERE / f"irr_per_establishment_{sev}_data.json").read_text())
        for panel, _ in PANELS:
            for lu, r in d["panels"][panel].items():
                pos, neg = out[panel].setdefault(lu, ([0] * 4, [0] * 4))
                if r == "na":
                    continue
                for v in r.values():
                    v = float(str(v).rstrip("*"))
                    if v > 1:
                        pos[k] += 1
                    elif v < 1:
                        neg[k] += 1
    return out, d["per10"]


def main():
    c, per10 = counts()
    uses = sorted({lu for p in c.values() for lu in p}, key=lambda lu: (
        -sum(sum(c[p].get(lu, ([0] * 4, [0] * 4))[0]) - sum(c[p].get(lu, ([0] * 4, [0] * 4))[1])
             for p, _ in PANELS), lu))
    ny = len(uses)
    xmax = max(sum(v[0]) for p in c.values() for v in p.values()) + 3
    xmin = max(sum(v[1]) for p in c.values() for v in p.values()) + 2

    fig, axes = plt.subplots(1, 2, figsize=(7.16, 4.4), sharey=True,
                             gridspec_kw=dict(wspace=0.08, left=0.23, right=0.99,
                                              top=0.9, bottom=0.2))
    y = np.arange(ny)
    for ax, (panel, tag) in zip(axes, PANELS):
        ax.axvspan(-xmin, 0, color="#f3f6fa", zorder=0, lw=0)
        ax.axvspan(0, xmax, color="#fbf5f3", zorder=0, lw=0)
        for i, lu in enumerate(uses):
            pos, neg = c[panel].get(lu, ([0] * 4, [0] * 4))
            left = 0
            for k in range(4):
                if pos[k]:
                    ax.barh(i, pos[k], left=left, height=0.64, color=POS[k],
                            edgecolor="white", lw=0.6, zorder=2)
                    left += pos[k]
            right = 0
            for k in range(4):
                if neg[k]:
                    ax.barh(i, -neg[k], left=-right, height=0.64, color=NEG[k],
                            edgecolor="white", lw=0.6, zorder=2)
                    right += neg[k]
            if left:
                ax.text(left + 0.3, i, f"{left}", va="center", ha="left",
                        fontsize=6.8, color="#333")
            if right:
                ax.text(-right - 0.3, i, f"{right}", va="center", ha="right",
                        fontsize=6.8, color="#333")
        ax.axvline(0, color="#222", lw=0.8, zorder=3)
        ax.set_xlim(-xmin, xmax); ax.set_ylim(ny - 0.5, -0.5)
        ticks = [t for t in range(-20, 25, 5) if -xmin <= t <= xmax]
        ax.set_xticks(ticks); ax.set_xticklabels([str(abs(t)) for t in ticks])
        ax.xaxis.grid(True, color="white", lw=0.8, zorder=1)
        ax.tick_params(axis="y", length=0, pad=3)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        for s in ("left", "bottom"):
            ax.spines[s].set_color("#8a8a8a")
        ax.set_title(f"({tag}) {panel}", loc="left", fontsize=10,
                     fontweight="bold", pad=14)
        ax.text(0.0, 1.005, "← lower risk (IRR < 1)", transform=ax.transAxes,
                fontsize=6.8, style="italic", color="#2171b5", va="bottom")
        ax.text(1.0, 1.005, "higher risk (IRR > 1) →", transform=ax.transAxes,
                fontsize=6.8, style="italic", color="#cb181d", va="bottom", ha="right")
        ax.set_xlabel("Number of significant associations ($p$ < 0.05)", fontsize=7.8)
    axes[0].set_yticks(y)
    axes[0].set_yticklabels([lu + (" (per 10)" if lu in per10 else "") for lu in uses])

    # one entry per severity: paired swatch (IRR > 1 red | IRR < 1 blue)
    handles = [(Patch(fc=POS[k], ec="none"), Patch(fc=NEG[k], ec="none"))
               for k in range(4)]
    fig.legend(handles=handles, labels=[s for _, s in SEVERITIES], ncol=4,
               loc="lower center", bbox_to_anchor=(0.61, -0.005), frameon=False,
               fontsize=7.4, handlelength=2.4, columnspacing=1.6, handletextpad=0.5,
               handler_map={tuple: HandlerTuple(ndivide=None, pad=0.05)},
               title="Crash severity (red swatch: IRR > 1; blue swatch: IRR < 1)",
               title_fontsize=7.4)

    for ext, kw in (("pdf", {}), ("png", {"dpi": 600}),
                    ("tiff", {"dpi": 600, "pil_kwargs": {"compression": "tiff_lzw"}})):
        fig.savefig(HERE / f"significance_summary.{ext}", bbox_inches="tight",
                    pad_inches=0.03, **kw)


if __name__ == "__main__":
    main()
