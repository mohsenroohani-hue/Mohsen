"""Segment-typology companion to plot_study_area_map.py: same basemap,
common scale, locator and styling; road segments coloured by land-use
context typology (traced by digitize_study_area_segments.py)."""
import json

from matplotlib.collections import LineCollection
from matplotlib.lines import Line2D

import plot_study_area_map as base

# Four chromatic classes pass CVD checks (worst deutan dE 9.2); the
# low-intensity baseline is a recessive light gray with a thinner stroke,
# so it is separated by line width as well as colour.
SEG_TYPES = [  # key, label, n, colour, line width (pt)
    ("low", "Low-intensity frontage", 95, "#b3b3b3", 1.6),
    ("shop", "Shopping-center / big-box retail", 86, "#0072B2", 2.6),
    ("ind", "Industrial & auto-oriented", 57, "#D55E00", 2.6),
    ("civic", "Civic & recreation", 57, "#009E73", 2.6),
    ("office", "Office, lodging & mixed use", 39, "#5D3A9B", 2.6),
]


def segment_layer(_basemap):
    segs = json.loads((base.HERE / "study_area_segments_data.json").read_text())

    def layer(ax, tag):
        for i, (key, _, _, col, lw) in enumerate(SEG_TYPES):
            ax.add_collection(LineCollection(segs[tag][key], colors=col, lw=lw,
                                             capstyle="butt", joinstyle="round", zorder=3 + i * 0.1))

    handles = [Line2D([], [], color=col, lw=lw + 0.8, solid_capstyle="butt",
                      label=f"{lab} ($n$ = {n})")
               for _, lab, n, col, lw in SEG_TYPES]
    return layer, handles


if __name__ == "__main__":
    base.main(segment_layer, unit="segments", stem="study_area_segments_map")
