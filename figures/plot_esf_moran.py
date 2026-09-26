"""Publication-quality redraw of the residual spatial-autocorrelation check:
Moran's I of Pearson residuals before and after eigenvector spatial
filtering (ESF), per model.

Layout ideas:
  * one panel per facility, each sorted by the pre-filter Moran's I
  * each model is an arrow from "before" to "after", so the reduction reads
    as a direction and a length; % reduction and the number of selected
    eigenvectors are tabulated at the right
  * colour-blind-safe Okabe-Ito pair (vermillion before, blue after)
  * a value beyond the axis range is drawn as a broken arrow, not dropped
  * Times New Roman throughout, vector PDF with embedded TrueType fonts
"""
import json
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

HERE = Path(__file__).parent

mpl.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "Times", "Liberation Serif", "Nimbus Roman"],
    "mathtext.fontset": "stix",
    "font.size": 8,
    "axes.linewidth": 0.6,
    "xtick.major.width": 0.5,
    "pdf.fonttype": 42, "ps.fonttype": 42, "svg.fonttype": "none",
})

BEFORE, AFTER = "#D55E00", "#0072B2"
XMAX = 0.26


def panel(ax, rows, title, tag):
    rows = sorted(rows, key=lambda r: -(r["before"] if r["before"] is not None else 9))
    n = len(rows)
    for i, r in enumerate(rows):
        if i % 2 == 0:
            ax.axhspan(i - .5, i + .5, color="#f4f3ef", lw=0, zorder=0)
        b, a = r["before"], r["after"]
        clipped = b is None
        bx = XMAX * 0.995 if clipped else b
        ax.annotate("", xy=(a, i), xytext=(bx, i),
                    arrowprops=dict(arrowstyle="-|>,head_width=0.22,head_length=0.5",
                                    color="#9a9a9a", lw=0.9, shrinkA=3.2, shrinkB=3.2),
                    zorder=2)
        ax.plot(a, i, "o", ms=4.6, color=AFTER, mec="white", mew=0.5, zorder=3)
        if clipped:
            ax.plot(bx, i, ">", ms=4.6, color=BEFORE, mec="white", mew=0.5,
                    zorder=3, clip_on=False)
            ax.text(bx - 0.004, i - 0.42, f"> {XMAX:g}", ha="right", va="bottom",
                    fontsize=5.8, color=BEFORE, style="italic")
        else:
            ax.plot(b, i, "o", ms=4.6, color=BEFORE, mec="white", mew=0.5, zorder=3)
        red = "—" if clipped else f"−{100 * (1 - a / b):.0f}%"
        ax.text(1.02, i, red, transform=ax.get_yaxis_transform(), ha="left",
                va="center", fontsize=6.6, color="#333")
        ax.text(1.25, i, f"{r['eigenvectors']}", transform=ax.get_yaxis_transform(),
                ha="center", va="center", fontsize=6.6, color="#333")
    for x, lab in ((1.02, "Change"), (1.25, "EVs")):
        ax.text(x, -1.0, lab, transform=ax.get_yaxis_transform(),
                ha="left" if x < 1.1 else "center", va="center", fontsize=6.8,
                fontweight="bold", color="#333")
    ax.axvline(0, color="#333", lw=0.7, zorder=1)
    ax.set_xlim(-0.01, XMAX); ax.set_ylim(n - .5, -1.6)
    ax.set_yticks(range(n))
    ax.set_yticklabels([f"{r['crash_type']} · {r['severity']}" for r in rows],
                       fontsize=7)
    ax.set_xticks([0, 0.05, 0.1, 0.15, 0.2, 0.25])
    ax.set_xticklabels(["0", "0.05", "0.10", "0.15", "0.20", "0.25"])
    ax.xaxis.grid(True, color="#dedcd6", lw=0.5, zorder=0)
    ax.tick_params(axis="y", length=0, pad=2)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color("#8a8a8a")
    ax.set_title(f"({tag}) {title}", loc="left", fontsize=10, fontweight="bold", pad=4)
    ax.set_xlabel("Moran’s $I$ of Pearson residuals ($k$ = 6)", fontsize=7.8)


def main():
    d = json.loads((HERE / "esf_moran_data.json").read_text())
    seg = [r for r in d["rows"] if r["facility"] == "Segments"]
    inter = [r for r in d["rows"] if r["facility"] == "Intersections"]
    fig, axes = plt.subplots(1, 2, figsize=(7.16, 5.6),
                             gridspec_kw=dict(wspace=0.7, left=0.14, right=0.88,
                                              top=0.94, bottom=0.12,
                                              height_ratios=None))
    # equal row height across panels: shrink the shorter panel
    panel(axes[0], inter, "Intersections", "a")
    panel(axes[1], seg, "Segments", "b")
    p0, p1 = axes[0].get_position(), axes[1].get_position()
    h = p1.height * (len(inter) + 1.1) / (len(seg) + 1.1)
    axes[0].set_position([p0.x0, p1.y1 - h, p0.width, h])

    handles = [Line2D([], [], ls="", marker="o", ms=5, color=BEFORE, label="Before spatial filter"),
               Line2D([], [], ls="", marker="o", ms=5, color=AFTER,
                      label="After eigenvector spatial filter (ESF)"),
               Line2D([], [], color="#9a9a9a", lw=0.9, marker=">", ms=4,
                      label="Change in residual autocorrelation")]
    fig.legend(handles=handles, loc="lower center", ncol=3, frameon=False,
               fontsize=7.4, bbox_to_anchor=(0.52, 0.0), columnspacing=1.6)
    fig.text(0.52, -0.018, "Rows sorted by pre-filter Moran’s $I$. EVs = number of "
             "eigenvectors selected.", ha="center", fontsize=6.8, style="italic",
             color="#444")

    for ext, kw in (("pdf", {}), ("png", {"dpi": 600}),
                    ("tiff", {"dpi": 600, "pil_kwargs": {"compression": "tiff_lzw"}})):
        fig.savefig(HERE / f"esf_moran.{ext}", bbox_inches="tight",
                    pad_inches=0.03, **kw)


if __name__ == "__main__":
    main()
