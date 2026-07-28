"""
vizstyle.py
===========
House style for every figure in the review. One place, so that all figures
read as a single system.

Palette provenance
------------------
Categorical slots and the sequential ramp are the validated reference palette
(six checks: lightness band, chroma floor, CVD separation, normal-vision
floor, contrast, ordering). Validator output for the sets actually used:

  6 adjacent slots (stacks, bars, lines)
      worst adjacent CVD dE 9.1 (protan), worst adjacent normal-vision dE 19.6
  3 all-pairs slots (scatter, choropleth overlays)
      worst all-pairs CVD dE 9.2, worst all-pairs normal-vision dE 24.0

Three light-surface slots (aqua, yellow, magenta) sit below 3:1 contrast, so
the *relief rule* applies: every figure that uses them ships visible direct
labels, and the full numeric table for every figure is available as a CSV in
`tables/`.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

# --- surfaces & ink -------------------------------------------------------
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
INK_MUTED = "#8a8880"
GRID = "#e6e5e1"

# --- categorical slots (fixed order, never cycled) ------------------------
CAT = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300"]
CAT_ALL_PAIRS = CAT[:3]          # cap for all-pairs forms

# --- sequential (single hue, light -> dark) -------------------------------
SEQ_STEPS = ["#cde2fb", "#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec", "#5598e7",
             "#3987e5", "#2a78d6", "#256abf", "#1c5cab", "#184f95", "#104281",
             "#0d366b"]
SEQ = LinearSegmentedColormap.from_list("pbsa_seq", SEQ_STEPS)
SEQ_ORANGE = LinearSegmentedColormap.from_list(
    "pbsa_seq2", ["#fde3d6", "#f9b894", "#f18e5c", "#eb6834", "#c14f24", "#8f3917"])

# --- diverging (two hues + neutral gray midpoint) -------------------------
DIV = LinearSegmentedColormap.from_list(
    "pbsa_div", ["#0d366b", "#2a78d6", "#9ec5f4", "#f0efec",
                 "#f0a3a3", "#d03b3b", "#7d1f1f"])

# --- period identity (used consistently across all figures) ---------------
PERIODS = ["2000-2010", "2011-2020", "2021-2027"]
PERIOD_COLOR = {"2000-2010": CAT[0], "2011-2020": CAT[1], "2021-2027": CAT[2]}

# --- method-class identity ------------------------------------------------
CLASS_COLOR = {
    "CLASSICAL": "#2a78d6",
    "INFERENTIAL": "#eb6834",
    "GEOSTATISTICAL": "#1baf7a",
    "NETWORK": "#eda100",
    "LEARNING": "#e87ba4",
    "REALTIME": "#008300",
}

FIGDPI = 300


def apply_rc():
    plt.rcParams.update({
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "savefig.facecolor": SURFACE,
        "font.family": "DejaVu Sans",
        "font.size": 9,
        "axes.titlesize": 11,
        "axes.titleweight": "bold",
        "axes.labelsize": 9,
        "axes.labelcolor": INK_2,
        "axes.edgecolor": GRID,
        "axes.linewidth": 0.8,
        "axes.grid": True,
        "grid.color": GRID,
        "grid.linewidth": 0.6,
        "xtick.color": INK_2,
        "ytick.color": INK_2,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "legend.frameon": False,
        "legend.fontsize": 8,
        "text.color": INK,
        "figure.dpi": 110,
        "savefig.dpi": FIGDPI,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.25,
    })


def despine(ax, keep=("left", "bottom")):
    for s in ("top", "right", "left", "bottom"):
        ax.spines[s].set_visible(s in keep)
    ax.set_axisbelow(True)


def caption(fig, text, y=-0.02):
    """Source / method note rendered inside the figure, as journals require."""
    fig.text(0.01, y, text, ha="left", va="top", fontsize=7, color=INK_MUTED,
             wrap=True)


def title_block(ax, title, subtitle=None):
    ax.set_title(title, loc="left", pad=14 if subtitle else 8, color=INK)
    if subtitle:
        ax.text(0, 1.02, subtitle, transform=ax.transAxes, ha="left",
                va="bottom", fontsize=8.5, color=INK_2)
