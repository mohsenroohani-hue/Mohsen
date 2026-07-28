#!/usr/bin/env python3
"""
Generate all figures and maps for the systematic review.

Outputs 600 dpi PNG plus vector PDF into figures/.
Colour slots follow a CVD-validated categorical order (blue, orange, aqua,
yellow, magenta, green, violet) with a neutral grey reserved for "Other";
magnitude encodings use a single-hue blue sequential ramp.
"""
import ast
import json
import os
from collections import Counter
from itertools import combinations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyArrowPatch, Rectangle
from matplotlib.colors import LinearSegmentedColormap, Normalize
import networkx as nx
import matplotlib.patheffects as pe

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG = os.path.join(ROOT, "figures")
os.makedirs(FIG, exist_ok=True)

# --- design tokens ---------------------------------------------------------
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK2 = "#52514e"
INK3 = "#8a8985"
GRID = "#e6e5e1"
CAT = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100",
       "#e87ba4", "#008300", "#4a3aa7"]
NEUTRAL = "#b4b3ae"
SEQ = ["#cde2fb", "#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec", "#5598e7",
       "#3987e5", "#2a78d6", "#256abf", "#1c5cab", "#184f95", "#104281",
       "#0d366b"]
BLUES = LinearSegmentedColormap.from_list("seqblue", SEQ)

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE,
    "font.family": "DejaVu Sans", "font.size": 8,
    "axes.edgecolor": INK3, "axes.linewidth": 0.6,
    "axes.labelcolor": INK, "axes.titlesize": 10, "axes.titleweight": "bold",
    "axes.titlelocation": "left", "axes.titlecolor": INK,
    "xtick.color": INK2, "ytick.color": INK2,
    "xtick.labelsize": 7.5, "ytick.labelsize": 7.5,
    "legend.frameon": False, "legend.fontsize": 7.5,
    "grid.color": GRID, "grid.linewidth": 0.6,
})

METHOD_SHORT = {
    "PPM": "Point process models", "KDE": "Kernel density",
    "RIPLEY": "Second-order (K/g)", "ML": "Machine learning",
    "SCAN": "Scan statistics", "NET": "Network-constrained",
    "STPP": "Spatio-temporal", "COLOC": "Co-location/marked",
    "NN": "Nearest neighbour", "LISA": "Local autocorrelation",
    "OTHER": "Other",
}
DOMAIN_SHORT = {
    "HEALTH": "Public health", "ECOL": "Ecology", "CRIME": "Crime",
    "URBAN": "Urban geography", "METH": "Methodological",
    "TRAFFIC": "Road safety", "SEISM": "Seismology", "FIRE": "Wildfire",
    "ARCH": "Archaeology", "BIOIMG": "Microscopy", "ENV": "Environment",
    "OTHER": "Other",
}


def save(fig, name):
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(FIG, f"{name}.{ext}"), dpi=600,
                    bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)
    print("wrote", name)


def tidy(ax, grid_axis="y"):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(INK3)
    ax.grid(True, axis=grid_axis, zorder=0)
    ax.set_axisbelow(True)


# ===========================================================================
# Figure 1 — PRISMA 2020 flow diagram
# ===========================================================================
def fig_prisma(prisma):
    fig, ax = plt.subplots(figsize=(7.4, 6.4))
    fig.subplots_adjust(left=0.005, right=0.995, top=0.945, bottom=0.005)
    ax.set_xlim(0, 10.4)
    ax.set_ylim(0.9, 12.35)
    ax.axis("off")

    def box(x, y, w, h, text, fc=SURFACE, ec=INK3, fs=8, weight="normal"):
        ax.add_patch(Rectangle((x, y), w, h, facecolor=fc, edgecolor=ec,
                               linewidth=0.9, zorder=2))
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
                fontsize=fs, color=INK, zorder=3, linespacing=1.55,
                fontweight=weight)

    def stage(y, label):
        ax.text(0.05, y, label, fontsize=8.5, fontweight="bold", color=INK2,
                ha="left", va="center")

    def arrow(x1, y1, x2, y2):
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>",
                                     mutation_scale=10, linewidth=0.9,
                                     color=INK2, zorder=1))

    er = prisma["exclusion_reasons"]

    def n(*keys):
        return sum(v for k, v in er.items()
                   if any(kk.lower() in k.lower() for kk in keys))

    not_pp = n("no point pattern statistic", "areal", "not point pattern",
               "no point process formulation", "off-topic",
               "extended (line/polygon)", "purely temporal",
               "not point locations", "not geographic point pattern")
    pub_type = n("book", "thesis", "dissertation", "abstract", "correction",
                 "data descriptor")
    insuff = n("no abstract", "metadata corrupted")
    other_ex = prisma["records_excluded"] - not_pp - pub_type - insuff

    MX, MW = 1.55, 5.15          # main column
    MC = MX + MW / 2
    SX, SW = 7.0, 3.3            # side column

    stage(11.45, "Identification")
    box(MX, 10.75, MW, 1.40,
        "Records identified through federated\n"
        "bibliographic search (Consensus: Semantic\n"
        "Scholar, PubMed, Scopus, arXiv)\n"
        f"{prisma['n_queries']} structured queries  ·  n = {prisma['records_retrieved']}",
        fc="#eef4fd", fs=7.8)
    arrow(MC, 10.75, MC, 9.85)
    box(SX, 9.95, SW, 0.72,
        f"Duplicate records removed\nn = {prisma['duplicates_removed']}",
        fc="#f4f3f0", fs=7.5)
    ax.add_patch(FancyArrowPatch((MC, 10.31), (SX, 10.31), arrowstyle="-|>",
                                 mutation_scale=10, linewidth=0.9,
                                 color=INK2, zorder=1))

    stage(9.35, "Screening")
    box(MX, 8.95, MW, 0.85,
        "Records screened on title and abstract\n"
        f"n = {prisma['records_screened']}", fc="#eef4fd", fs=7.8)
    arrow(MC, 8.95, MC, 8.05)

    stage(7.60, "Eligibility")
    box(MX, 7.15, MW, 0.90,
        "Records assessed against eligibility criteria\n"
        f"n = {prisma['records_screened']}", fc="#eef4fd", fs=7.8)

    excl_lines = [
        f"Records excluded  ·  n = {prisma['records_excluded']}",
        "",
        f"No point-based statistic applied to",
        f"event locations   n = {not_pp}",
        "",
        "Ineligible publication type",
        f"(book, thesis, abstract)   n = {pub_type}",
        "",
        "Insufficient or corrupted",
        f"bibliographic record   n = {insuff}",
    ]
    if other_ex:
        excl_lines += ["", f"Other reasons   n = {other_ex}"]
    box(SX, 3.30, SW, 3.35, "\n".join(excl_lines), fc="#f4f3f0", fs=7.2)
    arrow(MC, 7.15, MC, 3.05)
    ax.add_patch(FancyArrowPatch((MC, 4.98), (SX, 4.98), arrowstyle="-|>",
                                 mutation_scale=10, linewidth=0.9,
                                 color=INK2, zorder=1))

    stage(2.25, "Included")
    box(MX, 1.35, MW, 1.65,
        f"Studies included in the synthesis\nn = {prisma['studies_included']}\n\n"
        f"{prisma['year_range'][0]}–{prisma['year_range'][1]}  ·  "
        f"{prisma['countries_represented']} case-study countries\n"
        f"{prisma['spatiotemporal_share']*100:.0f}% spatio-temporal  ·  "
        f"{prisma['multi_method_share']*100:.0f}% multi-method",
        fc="#dcebfc", weight="bold", fs=7.8)

    fig.suptitle("Figure 1. PRISMA 2020 flow of identification, screening and inclusion",
                 fontsize=9.5, x=0.01, ha="left", y=0.985, fontweight="bold")
    save(fig, "fig01_prisma_flow")


# ===========================================================================
# Figure 2 — temporal trajectory of method families
# ===========================================================================
def fig_trajectory(d):
    top = ["KDE", "RIPLEY", "PPM", "SCAN", "STPP", "NET", "ML"]
    order = top + ["Other"]
    colors = dict(zip(top, CAT))
    colors["Other"] = NEUTRAL

    d = d.copy()
    d["grp"] = d["method"].where(d["method"].isin(top), "Other")
    yrs = np.arange(1993, 2027)
    mat = pd.crosstab(d["year"], d["grp"]).reindex(yrs, fill_value=0)
    for c in order:
        if c not in mat:
            mat[c] = 0
    mat = mat[order]
    smooth = mat.rolling(3, center=True, min_periods=1).mean()

    fig, axes = plt.subplots(2, 1, figsize=(7.2, 6.4),
                             gridspec_kw={"height_ratios": [1.25, 1]})

    ax = axes[0]
    ax.stackplot(yrs, [smooth[c].values for c in order],
                 colors=[colors[c] for c in order], edgecolor=SURFACE,
                 linewidth=0.7, zorder=2)
    tidy(ax)
    ax.set_xlim(1993, 2026)
    ax.set_ylabel("Included studies per year\n(3-year moving average)")
    ax.set_title("a  Absolute growth of point-based spatial analysis, by method family")

    # panel b: composition share, shown only where the annual base is adequate
    ax = axes[1]
    tot = smooth[order].sum(axis=1)
    ok = tot >= 2.0
    first = int(yrs[np.argmax(ok.values)])
    share = (smooth[order].div(tot.replace(0, np.nan), axis=0) * 100).fillna(0)
    m = yrs >= first
    ax.stackplot(yrs[m], [share[c].values[m] for c in order],
                 colors=[colors[c] for c in order], edgecolor=SURFACE,
                 linewidth=0.7, zorder=2)
    tidy(ax)
    ax.set_xlim(1993, 2026)
    ax.set_ylim(0, 100)
    ax.set_ylabel("Share of published studies (%)")
    ax.set_xlabel("Publication year")
    ax.axvspan(1993, first, color="#f4f3f0", zorder=1, lw=0)
    ax.text((1993 + first) / 2, 50, "fewer than\n2 studies/yr", ha="center",
            va="center", fontsize=6.8, color=INK3, style="italic")
    ax.set_title(f"b  Compositional shift: relative share of each family (from {first})")
    handles = [plt.Rectangle((0, 0), 1, 1, color=colors[c]) for c in order]
    fig.legend(handles, [METHOD_SHORT.get(c, c) for c in order], ncol=4,
               loc="lower center", bbox_to_anchor=(0.5, -0.035),
               handlelength=1.0, columnspacing=1.4, labelcolor=INK2)
    fig.tight_layout(rect=(0, 0.055, 1, 1))
    save(fig, "fig02_method_trajectory")


# ===========================================================================
# Figure 3 — method x domain heatmap
# ===========================================================================
def fig_heatmap(d):
    rows = ["KDE", "RIPLEY", "NN", "SCAN", "LISA", "PPM", "STPP", "NET",
            "COLOC", "ML"]
    cols = ["HEALTH", "ECOL", "CRIME", "TRAFFIC", "URBAN", "SEISM", "FIRE",
            "ARCH", "METH"]
    ct = pd.crosstab(d["method"], d["domain"]).reindex(index=rows, columns=cols,
                                                       fill_value=0)
    fig, ax = plt.subplots(figsize=(7.2, 4.7))
    im = ax.imshow(ct.values, cmap=BLUES, aspect="auto",
                   norm=Normalize(0, ct.values.max()))
    ax.set_xticks(range(len(cols)),
                  [DOMAIN_SHORT[c] for c in cols], rotation=35, ha="right")
    ax.set_yticks(range(len(rows)), [METHOD_SHORT[r] for r in rows])
    for i in range(len(rows)):
        for j in range(len(cols)):
            v = ct.values[i, j]
            if v == 0:
                continue
            ax.text(j, i, str(v), ha="center", va="center", fontsize=7.5,
                    color="#ffffff" if v > ct.values.max() * 0.55 else INK,
                    fontweight="bold")
    ax.set_xticks(np.arange(-.5, len(cols), 1), minor=True)
    ax.set_yticks(np.arange(-.5, len(rows), 1), minor=True)
    ax.grid(which="minor", color=SURFACE, linewidth=1.6)
    ax.tick_params(which="minor", length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    cb = fig.colorbar(im, ax=ax, shrink=0.75, pad=0.02)
    cb.set_label("Number of included studies", fontsize=7.5, color=INK2)
    cb.outline.set_visible(False)
    cb.ax.tick_params(labelsize=7)
    ax.set_title("Figure 3. Primary method family by application domain\n"
                 "(cell values are study counts; n = %d)" % len(d),
                 fontsize=9.5, pad=10)
    save(fig, "fig03_method_domain_heatmap")


# ===========================================================================
# Figure 4 — world grid cartogram of case-study countries
# ===========================================================================
TILE = {
    # (col, row) — schematic world grid, west→east, north→south
    "Canada": (2, 0), "Norway": (9, 0),
    "United States": (2, 1), "United Kingdom": (7, 1), "Denmark": (8, 1),
    "Poland": (10, 1), "Lithuania": (11, 1),
    "France": (7, 2), "Germany": (9, 2), "Czech Republic": (10, 2),
    "Japan": (17, 2), "South Korea": (16, 2),
    "Portugal": (6, 3), "Spain": (7, 3), "Switzerland": (8, 3),
    "Austria": (9, 3), "Italy": (9, 4), "Greece": (10, 4),
    "Turkiye": (11, 3), "China": (15, 3), "Iran": (12, 4),
    "Mexico": (1, 4), "Tunisia": (8, 5), "Egypt": (10, 5),
    "Saudi Arabia": (11, 5), "Pakistan": (13, 4), "Nepal": (14, 4),
    "India": (13, 5), "Sri Lanka": (13, 6),
    "Venezuela": (3, 5), "Colombia": (2, 5), "Ecuador": (2, 6),
    "Peru": (2, 7), "Brazil": (4, 6), "Chile": (2, 8), "Argentina": (3, 8),
    "Nigeria": (8, 6), "Benin": (7, 6), "Cameroon": (9, 6),
    "Ethiopia": (10, 6), "Kenya": (10, 7), "Botswana": (9, 8),
    "South Africa": (9, 9),
    "Vietnam": (15, 5), "Thailand": (14, 5), "Philippines": (16, 5),
    "Indonesia": (15, 6), "Papua New Guinea": (17, 6),
    "Australia": (16, 8), "New Zealand": (18, 9),
}
ISO3 = {
    "Canada": "CAN", "Norway": "NOR", "United States": "USA",
    "United Kingdom": "GBR", "Denmark": "DNK", "Poland": "POL",
    "Lithuania": "LTU", "France": "FRA", "Germany": "DEU",
    "Czech Republic": "CZE", "Japan": "JPN", "South Korea": "KOR",
    "Portugal": "PRT", "Spain": "ESP", "Switzerland": "CHE",
    "Austria": "AUT", "Italy": "ITA", "Greece": "GRC", "Turkiye": "TUR",
    "China": "CHN", "Iran": "IRN", "Mexico": "MEX", "Tunisia": "TUN",
    "Egypt": "EGY", "Saudi Arabia": "SAU", "Pakistan": "PAK",
    "Nepal": "NPL", "India": "IND", "Sri Lanka": "LKA",
    "Venezuela": "VEN", "Colombia": "COL", "Ecuador": "ECU", "Peru": "PER",
    "Brazil": "BRA", "Chile": "CHL", "Argentina": "ARG", "Nigeria": "NGA",
    "Benin": "BEN", "Cameroon": "CMR", "Ethiopia": "ETH", "Kenya": "KEN",
    "Botswana": "BWA", "South Africa": "ZAF", "Vietnam": "VNM",
    "Thailand": "THA", "Philippines": "PHL", "Indonesia": "IDN",
    "Papua New Guinea": "PNG", "Australia": "AUS", "New Zealand": "NZL",
}


def fig_map(d):
    counts = (d[~d["country"].isin(["Not applicable", "Not specified", "Multiple"])]
              ["country"].value_counts())
    fig, ax = plt.subplots(figsize=(7.4, 4.6))
    vmax = counts.max()
    norm = Normalize(0, vmax ** 0.5)

    for country, (c, r) in TILE.items():
        if country not in ISO3:
            continue
        v = int(counts.get(country, 0))
        if v == 0:
            continue
        col = BLUES(norm(v ** 0.5))
        ax.add_patch(Rectangle((c, -r), 0.92, 0.92, facecolor=col,
                               edgecolor=SURFACE, linewidth=1.4, zorder=2))
        lum = 0.299 * col[0] + 0.587 * col[1] + 0.114 * col[2]
        tc = "#ffffff" if lum < 0.6 else INK
        ax.text(c + 0.46, -r + 0.58, ISO3[country], ha="center", va="center",
                fontsize=6.6, fontweight="bold", color=tc, zorder=3)
        ax.text(c + 0.46, -r + 0.27, str(v), ha="center", va="center",
                fontsize=6.2, color=tc, zorder=3)

    ax.set_xlim(0.6, 19.7)
    ax.set_ylim(-9.6, 1.4)
    ax.set_aspect("equal")
    ax.axis("off")

    # region annotations
    for label, (x, y) in {"Americas": (2.5, 1.0), "Europe": (8.8, 1.0),
                          "Africa": (6.1, -5.6), "Asia": (15.0, 1.0),
                          "Oceania": (18.4, -7.5)}.items():
        ax.text(x, y, label, fontsize=7.5, color=INK3, fontweight="bold",
                ha="center")

    sm = plt.cm.ScalarMappable(cmap=BLUES, norm=Normalize(0, vmax))
    cb = fig.colorbar(sm, ax=ax, shrink=0.6, pad=0.01, aspect=18)
    cb.set_label("Included studies", fontsize=7.5, color=INK2)
    cb.outline.set_visible(False)
    cb.ax.tick_params(labelsize=7)

    ax.set_title("Figure 4. Geography of case studies in point-based spatial analysis\n"
                 f"Grid cartogram: one tile per country ({len(counts)} countries; "
                 f"tiles positioned schematically, shading on a square-root scale)",
                 fontsize=9.5, pad=8)
    save(fig, "fig04_country_cartogram")


# ===========================================================================
# Figure 5 — research equity: region and income group
# ===========================================================================
def fig_equity(d):
    att = d[d["region"] != "Not attributable"]
    fig, axes = plt.subplots(1, 2, figsize=(7.4, 4.0),
                             gridspec_kw={"width_ratios": [1.15, 1]})

    ax = axes[0]
    r = att["region"].value_counts().sort_values()
    ax.barh(range(len(r)), r.values, color=CAT[0], height=0.62, zorder=2)
    ax.set_yticks(range(len(r)), r.index)
    for i, v in enumerate(r.values):
        ax.text(v + 0.5, i, str(v), va="center", fontsize=7.5, color=INK2)
    tidy(ax, "x")
    ax.set_xlabel("Included studies")
    ax.set_title("a  Case studies by world region")

    ax = axes[1]
    inc = ["High", "Upper-middle", "Lower-middle", "Low"]
    doms = ["HEALTH", "ECOL", "CRIME", "TRAFFIC", "URBAN", "Other"]
    dd = att.copy()
    dd["dgrp"] = dd["domain"].where(dd["domain"].isin(doms[:-1]), "Other")
    ct = pd.crosstab(dd["income_group"], dd["dgrp"]).reindex(
        index=inc, columns=doms, fill_value=0)
    pct = ct.div(ct.sum(axis=1), axis=0) * 100
    left = np.zeros(len(inc))
    cols = CAT[:5] + [NEUTRAL]
    for j, dm in enumerate(doms):
        ax.barh(range(len(inc)), pct[dm].values, left=left, color=cols[j],
                height=0.62, zorder=2, edgecolor=SURFACE, linewidth=1.2)
        for i, v in enumerate(pct[dm].values):
            if v >= 12:
                ax.text(left[i] + v / 2, i, f"{v:.0f}", ha="center",
                        va="center", fontsize=6.8, color="#ffffff",
                        fontweight="bold")
        left += pct[dm].values
    ax.set_yticks(range(len(inc)),
                  [f"{g}\n(n={int(ct.loc[g].sum())})" for g in inc])
    ax.set_xlim(0, 100)
    ax.set_xlabel("Share of studies in income group (%)")
    tidy(ax, "x")
    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in cols]
    ax.legend(handles, [DOMAIN_SHORT.get(x, x) for x in doms], ncol=3,
              loc="upper center", bbox_to_anchor=(0.5, -0.18),
              handlelength=1.0, labelcolor=INK2)
    ax.set_title("b  Application domain by national income group")
    fig.suptitle("Figure 5. Geographic and economic distribution of the evidence base",
                 fontsize=9.5, x=0.055, ha="left", y=1.02, fontweight="bold")
    save(fig, "fig05_equity")


# ===========================================================================
# Figure 6 — method co-occurrence network
# ===========================================================================
def fig_network(d):
    ms = d["methods_all"].map(ast.literal_eval)
    node_n = Counter(m for lst in ms for m in set(lst))
    edges = Counter()
    for lst in ms:
        for a, b in combinations(sorted(set(lst)), 2):
            edges[(a, b)] += 1
    edges = {k: v for k, v in edges.items() if v >= 3}

    G = nx.Graph()
    for m, c in node_n.items():
        if m == "OTHER":
            continue
        G.add_node(m, n=c)
    for (a, b), w in edges.items():
        if a in G and b in G:
            G.add_edge(a, b, w=w)

    # deterministic circular layout, ordered from classical to contemporary
    ring = [m for m in ["NN", "RIPLEY", "KDE", "SCAN", "LISA", "PPM",
                        "STPP", "NET", "COLOC", "ML"] if m in G]
    ang = {m: np.pi / 2 - 2 * np.pi * i / len(ring) for i, m in enumerate(ring)}
    pos = {m: np.array([np.cos(a), np.sin(a)]) for m, a in ang.items()}
    fig, ax = plt.subplots(figsize=(6.8, 5.6))
    wmax = max(nx.get_edge_attributes(G, "w").values())
    for a, b, dta in G.edges(data=True):
        ax.plot([pos[a][0], pos[b][0]], [pos[a][1], pos[b][1]],
                color="#c9c8c3", linewidth=0.4 + 3.4 * dta["w"] / wmax,
                zorder=1, solid_capstyle="round")
    nmax = max(nx.get_node_attributes(G, "n").values())
    radius = {}
    for m, dta in G.nodes(data=True):
        s = 260 + 2100 * dta["n"] / nmax
        radius[m] = np.sqrt(s / np.pi)
        ax.scatter(*pos[m], s=s, color=CAT[0], edgecolor=SURFACE,
                   linewidth=1.8, zorder=2)
        ax.scatter(*pos[m], s=s, facecolor="none", edgecolor="#184f95",
                   linewidth=0.5, zorder=3)
        ax.annotate(str(dta["n"]), pos[m], ha="center", va="center",
                    fontsize=7, color="#ffffff", fontweight="bold", zorder=4)
    # labels sit outside the ring, anchored away from the circle centre
    for m in ring:
        a = ang[m]
        off = radius[m] + 8
        ha = "left" if np.cos(a) > 0.15 else ("right" if np.cos(a) < -0.15
                                              else "center")
        va = "bottom" if np.sin(a) > 0.15 else ("top" if np.sin(a) < -0.15
                                                else "center")
        ax.annotate(METHOD_SHORT[m], pos[m], textcoords="offset points",
                    xytext=(np.cos(a) * off, np.sin(a) * off),
                    ha=ha, va=va, fontsize=7.4, color=INK,
                    fontweight="bold", zorder=5)
    ax.axis("off")
    ax.set_aspect("equal")
    ax.set_xlim(-1.72, 1.72)
    ax.set_ylim(-1.42, 1.42)
    ax.set_title("Figure 6. Co-occurrence of method families within individual studies\n"
                 "Node size and inset value = studies using the method; edge width = studies\n"
                 "combining the pair (edges shown where n ≥ 3)", fontsize=9.5, pad=8)
    save(fig, "fig06_method_network")


# ===========================================================================
# Figure 7 — methodological maturity indicators over time
# ===========================================================================
def fig_maturity(d):
    fig, axes = plt.subplots(1, 3, figsize=(7.4, 3.4))
    eras = ["<=2005", "2006-2012", "2013-2019", "2020-2026"]
    lab = ["≤2005", "2006–12", "2013–19", "2020–26"]
    dd = d.dropna(subset=["era"]).copy()
    dd["era"] = dd["era"].astype(str)

    panels = [
        ("Spatio-temporal analysis", lambda g: (g["st"] == "Y").mean() * 100, CAT[0]),
        ("Two or more method families", lambda g: (g["n_methods"] > 1).mean() * 100, CAT[1]),
        ("Machine-learning component",
         lambda g: g["methods_all"].map(lambda s: "ML" in s).mean() * 100, CAT[2]),
    ]
    for ax, (title, fn, col) in zip(axes, panels):
        vals = [fn(dd[dd["era"] == e]) if (dd["era"] == e).any() else 0 for e in eras]
        ns = [int((dd["era"] == e).sum()) for e in eras]
        ax.bar(range(4), vals, color=col, width=0.62, zorder=2)
        for i, (v, nn) in enumerate(zip(vals, ns)):
            ax.text(i, v + 2.5, f"{v:.0f}%", ha="center", fontsize=7.5,
                    color=INK, fontweight="bold")
        ax.set_xticks(range(4), [f"{l}\nn={n}" for l, n in zip(lab, ns)],
                      fontsize=6.4)
        ax.set_ylim(0, 100)
        tidy(ax)
        ax.set_title(title, fontsize=8.2, loc="center")
    axes[0].set_ylabel("Share of studies in period (%)")
    fig.suptitle("Figure 7. Methodological maturation of point-based spatial analysis",
                 fontsize=9.5, x=0.02, ha="left", y=1.0, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    save(fig, "fig07_maturity")


# ===========================================================================
# Figure 8 — domain trajectories
# ===========================================================================
def fig_domain_traj(d):
    doms = ["HEALTH", "ECOL", "CRIME", "TRAFFIC", "URBAN", "SEISM", "FIRE", "ARCH"]
    fig, axes = plt.subplots(2, 4, figsize=(7.4, 3.8), sharex=True, sharey=True)
    yrs = np.arange(1995, 2027)
    for ax, dm, col in zip(axes.ravel(), doms, CAT + [NEUTRAL]):
        s = (d[d["domain"] == dm]["year"].value_counts()
             .reindex(yrs, fill_value=0)
             .rolling(5, center=True, min_periods=1).mean())
        ax.fill_between(yrs, s.values, color=col, alpha=0.9, zorder=2, lw=0)
        ax.plot(yrs, s.values, color=col, linewidth=1.2, zorder=3)
        ax.set_title(f"{DOMAIN_SHORT[dm]} (n={int((d['domain']==dm).sum())})",
                     fontsize=7.6)
        tidy(ax)
        ax.set_xlim(1995, 2026)
        ax.set_xticks([2000, 2010, 2020])
    axes[0, 0].set_ylabel("Studies / yr")
    axes[1, 0].set_ylabel("Studies / yr")
    fig.suptitle("Figure 8. Domain-specific adoption trajectories (5-year moving average)",
                 fontsize=9.5, x=0.045, ha="left", y=1.03, fontweight="bold")
    fig.tight_layout()
    save(fig, "fig08_domain_trajectories")


def main():
    d = pd.read_csv(os.path.join(ROOT, "data", "included.csv"))
    with open(os.path.join(ROOT, "data", "prisma.json")) as fh:
        prisma = json.load(fh)
    fig_prisma(prisma)
    fig_trajectory(d)
    fig_heatmap(d)
    fig_map(d)
    fig_equity(d)
    fig_network(d)
    fig_maturity(d)
    fig_domain_traj(d)


if __name__ == "__main__":
    main()
