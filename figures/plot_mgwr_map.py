"""MGWR local-coefficient map on the shared study-area basemap (common
scale, locator, Times New Roman). Locally significant sites are filled by
their local standardized coefficient and outlined; non-significant sites are
small faded dots, so significance never depends on colour alone.

Usage: python plot_mgwr_map.py [data.json] [output_stem]
"""
import json
import sys

import matplotlib as mpl
import numpy as np
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from matplotlib.lines import Line2D

import plot_study_area_map as base

VMAX = 10
NORM = TwoSlopeNorm(0, -VMAX, VMAX)
CMAP = LinearSegmentedColormap.from_list("coef_div", [
    "#08306b", "#2171b5", "#9ecae1", "#f7f5f0", "#fcae91", "#cb181d", "#67000d"])
NS_C = "#a9a59b"


def mgwr_layer(data_file, title, subtitle):
    def make(basemap):
        d = json.loads((base.HERE / data_file).read_text())["panels"]
        # keep faded dots only on the study corridors (drops tracing noise)
        for tag, p in d.items():
            cor = np.array([pt for sg in basemap[tag]["corridor"] for pt in sg]
                           + [m[1:] for m in basemap[tag]["markers"]])
            p["ns"] = [q for q in p["ns"]
                       if ((cor - q) ** 2).sum(1).min() < 1.0]

        def layer(ax, tag):
            p = d[tag]
            ax.add_collection(mpl.collections.LineCollection(
                basemap[tag]["corridor"], colors=base.CORRIDOR, lw=0.7, alpha=0.6,
                zorder=2))
            if p["ns"]:
                x, y = zip(*p["ns"])
                ax.scatter(x, y, s=2.2, c=NS_C, lw=0, alpha=0.7, zorder=3)
            if p["sig"]:
                sig = sorted(p["sig"], key=lambda s: abs(s[2]))   # strongest on top
                x, y, v = zip(*sig)
                ax.scatter(x, y, s=15, c=v, cmap=CMAP, norm=NORM, edgecolors="#222",
                           linewidths=0.5, zorder=4)

        def legend(fig, lax):
            lax.text(0, 1, title, transform=lax.transAxes, ha="left", va="top",
                     fontsize=8.5, fontweight="bold", linespacing=1.1)
            lax.text(0, 0.8, subtitle, transform=lax.transAxes, ha="left", va="top",
                     fontsize=7.2, style="italic", color="#444", linespacing=1.1)
            pos = lax.get_position()
            cax = fig.add_axes([pos.x0 + 0.01, pos.y0 + pos.height * 0.42,
                                pos.width * 0.62, pos.height * 0.09])
            sm = mpl.cm.ScalarMappable(norm=NORM, cmap=CMAP)
            cb = fig.colorbar(sm, cax=cax, orientation="horizontal",
                              ticks=[-10, -5, 0, 5, 10], extend="both", extendfrac=0.05)
            cb.ax.set_xticklabels(["−10", "−5", "0", "5", "10"])
            cb.outline.set_linewidth(0.5)
            cb.ax.tick_params(labelsize=6.8, width=0.5, length=2)
            cb.set_label("Local standardized coefficient (capped at 97th pct.)",
                         fontsize=6.8, labelpad=2)
            h = [Line2D([], [], ls="", marker="o", ms=4.2, mfc=CMAP(0.2), mec="#222",
                        mew=0.5, label="Locally significant"),
                 Line2D([], [], ls="", marker="o", ms=1.8, mfc=NS_C, mec="none",
                        label="Not significant")]
            lax.legend(handles=h, loc="lower left", bbox_to_anchor=(0.66, 0.33),
                       frameon=False, fontsize=6.8, handletextpad=0.3,
                       labelspacing=0.35, borderaxespad=0)
        return layer, legend
    return make


if __name__ == "__main__":
    data = sys.argv[1] if len(sys.argv) > 1 else "mgwr_intercept_kab_int_data.json"
    stem = sys.argv[2] if len(sys.argv) > 2 else "mgwr_intercept_kab_int"
    meta = json.loads((base.HERE / data).read_text())
    base.main(mgwr_layer(data, meta.get("title") or "MGWR local intercept — KAB, intersections",
                         meta.get("subtitle") or "Baseline KAB risk not explained by covariates.\n"
                         "Significance: MGWR-corrected critical $t$."),
              unit="intersections", stem=stem)
