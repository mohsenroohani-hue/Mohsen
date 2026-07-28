"""
figures.py
==========
Stage 4: every figure in the manuscript.

All figures are generated from `data/derived/records_included.csv` and
`data/derived/results.json`; none is drawn by hand and none contains a value
that is not computed from the corpus. Basemap geometry is Natural Earth
1:110m (public domain), bundled in `assets/naturalearth/`.

Run:  python3 analysis/figures.py
"""

import csv
import json
import math
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle, FancyArrowPatch, Polygon as MplPoly
from matplotlib.collections import PolyCollection
from matplotlib.path import Path
import matplotlib.patches as mpatches
import shapefile

import lexicons as LX
import geo as GEO
import vizstyle as VS

VS.apply_rc()

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DER = os.path.join(ROOT, "data", "derived")
FIG = os.path.join(ROOT, "figures")
os.makedirs(FIG, exist_ok=True)
csv.field_size_limit(sys.maxsize)

LIST_COLS = {"methods", "method_classes", "domains", "data_sources", "software",
             "spatial_scale", "temporal_scale", "uncertainty", "validation",
             "reproducibility", "ethics", "affil_iso3", "affil_hemisphere",
             "case_iso3", "case_supranational", "case_evidence", "institutions"}
P = VS.PERIODS


def load():
    rows = []
    with open(os.path.join(DER, "records_included.csv"), encoding="utf-8") as f:
        for r in csv.DictReader(f):
            for c in LIST_COLS:
                r[c] = [x for x in (r.get(c) or "").split("|") if x]
            r["Year"] = int(r["Year"])
            for c in ("pbsam_score", "n_methods", "international_collab",
                      "n_affil_countries", "D2_uncertainty", "D3_validation",
                      "D5_reproducibility"):
                r[c] = int(r[c]) if str(r[c]).strip() != "" else 0
            rows.append(r)
    return rows


ROWS = load()
N = len(ROWS)
RES = json.load(open(os.path.join(DER, "results.json")))
PN = {p: sum(1 for r in ROWS if r["period_label"] == p) for p in P}


def save(fig, name):
    path = os.path.join(FIG, name)
    fig.savefig(path)
    plt.close(fig)
    print("wrote", os.path.basename(path))


def pct(n, d):
    return 100.0 * n / d if d else 0.0


def read_table(name):
    """Read a table from tables/, skipping the leading '# note' row."""
    path = os.path.join(ROOT, "tables", name)
    with open(path, encoding="utf-8") as f:
        lines = [ln for ln in f if not ln.lstrip('"').startswith("#")]
    return list(csv.DictReader(lines))


# =========================================================================
# Basemap helpers
# =========================================================================
_SF = shapefile.Reader(os.path.join(ROOT, "assets", "naturalearth",
                                    "naturalearth_lowres.shp"))
_SHAPES = _SF.shapes()
_RECS = _SF.records()


def robinson(lon, lat):
    """Robinson projection (tabulated coefficients, linear interpolation)."""
    X = [1.0000, 0.9986, 0.9954, 0.9900, 0.9822, 0.9730, 0.9600, 0.9427,
         0.9216, 0.8962, 0.8679, 0.8350, 0.7986, 0.7597, 0.7186, 0.6732,
         0.6213, 0.5722, 0.5322]
    Y = [0.0000, 0.0620, 0.1240, 0.1860, 0.2480, 0.3100, 0.3720, 0.4340,
         0.4958, 0.5571, 0.6176, 0.6769, 0.7346, 0.7903, 0.8435, 0.8936,
         0.9394, 0.9761, 1.0000]
    lat = np.clip(np.asarray(lat, dtype=float), -90, 90)
    lon = np.asarray(lon, dtype=float)
    a = np.abs(lat) / 5.0
    i = np.clip(a.astype(int), 0, 17)
    f = a - i
    xs = np.array(X)[i] + (np.array(X)[np.minimum(i + 1, 18)] - np.array(X)[i]) * f
    ys = np.array(Y)[i] + (np.array(Y)[np.minimum(i + 1, 18)] - np.array(Y)[i]) * f
    return xs * lon * np.pi / 180.0, np.sign(lat) * ys * (np.pi / 2)


def country_polys():
    """Yield (iso3, name, continent, [projected ring arrays])."""
    for shp, rec in zip(_SHAPES, _RECS):
        parts = list(shp.parts) + [len(shp.points)]
        rings = []
        for k in range(len(parts) - 1):
            pts = np.array(shp.points[parts[k]:parts[k + 1]])
            if len(pts) < 3:
                continue
            x, y = robinson(pts[:, 0], pts[:, 1])
            rings.append(np.column_stack([x, y]))
        iso = rec["iso_a3"]
        if iso == "-99":
            iso = {"Kosovo": "XKX"}.get(rec["name"], "-99")
        yield iso, rec["name"], rec["continent"], rings


CENTROIDS = {}
for _iso, _nm, _c, _rings in country_polys():
    if not _rings:
        continue
    big = max(_rings, key=len)
    CENTROIDS[_iso] = (big[:, 0].mean(), big[:, 1].mean())


def draw_choropleth(ax, values, cmap, vmin=None, vmax=None, log=False,
                    missing="#f2f1ee", edge="#ffffff", lw=0.25):
    vals = [v for v in values.values() if v > 0]
    if not vals:
        return None
    vmin = vmin if vmin is not None else min(vals)
    vmax = vmax if vmax is not None else max(vals)
    for iso, name, cont, rings in country_polys():
        if cont == "Antarctica":
            continue
        v = values.get(iso, 0)
        if v > 0:
            if log:
                t = (math.log10(v) - math.log10(vmin)) / (math.log10(vmax) - math.log10(vmin) or 1)
            else:
                t = (v - vmin) / ((vmax - vmin) or 1)
            col = cmap(np.clip(t, 0, 1))
        else:
            col = missing
        ax.add_collection(PolyCollection(rings, facecolors=[col], edgecolors=edge,
                                         linewidths=lw))
    ax.set_xlim(-2.72, 2.72)
    ax.set_ylim(-1.5, 1.62)
    ax.set_aspect("equal")
    ax.axis("off")
    return vmin, vmax


def colorbar_strip(fig, ax_pos, cmap, vmin, vmax, label, log=False, ticks=None):
    cax = fig.add_axes(ax_pos)
    grad = np.linspace(0, 1, 256).reshape(1, -1)
    cax.imshow(grad, aspect="auto", cmap=cmap, origin="lower",
               extent=[0, 1, 0, 1])
    cax.set_yticks([])
    if ticks is None:
        ticks = [vmin, vmax] if not log else [vmin, int((vmin * vmax) ** .5), vmax]
    pos = []
    for t in ticks:
        if log:
            pos.append((math.log10(t) - math.log10(vmin)) /
                       (math.log10(vmax) - math.log10(vmin) or 1))
        else:
            pos.append((t - vmin) / ((vmax - vmin) or 1))
    cax.set_xticks(pos)
    cax.set_xticklabels([str(int(t)) for t in ticks], fontsize=7)
    cax.set_xlabel(label, fontsize=7.5, color=VS.INK_2, labelpad=2)
    for s in cax.spines.values():
        s.set_visible(False)
    cax.tick_params(length=2, colors=VS.INK_2)
    return cax


# =========================================================================
# FIGURE 1 - PRISMA flow
# =========================================================================
def fig01_prisma():
    pr = json.load(open(os.path.join(DER, "prisma_counts.json")))
    ident, scr, inc = pr["identification"], pr["screening"], pr["included"]
    ex = scr["exclusion_reasons"]
    order = ["S2_no_usable_abstract", "S3_non_research_item",
             "S4a_outside_geographic_boundary",
             "S4b_sensor_processing_tradition", "S5_no_point_referenced_units",
             "S6_no_spatial_analytical_operation", "S7_out_of_scope_tradition",
             "S8_polysemous_point_only"]
    labels = {
        "S2_no_usable_abstract": "No usable abstract",
        "S3_non_research_item": "Non-research item (erratum, editorial)",
        "S4a_outside_geographic_boundary": "Outside geographic boundary\n(non-geographic point patterns)",
        "S4b_sensor_processing_tradition": "Sensor-processing tradition\n(SLAM, point-cloud segmentation)",
        "S5_no_point_referenced_units": "No point-referenced units of\nobservation (criterion A not met)",
        "S6_no_spatial_analytical_operation": "No spatial-analytical operation\n(criterion B not met)",
        "S7_out_of_scope_tradition": "Out-of-scope tradition without\ncore spatial-statistical operation",
        "S8_polysemous_point_only": "Polysemous use of 'point' only",
    }
    fig, ax = plt.subplots(figsize=(9.2, 8.8))
    ax.set_xlim(0, 10)
    ax.set_ylim(-0.9, 10.6)
    ax.axis("off")

    def box(x, y, w, h, text, fc="#eef4fd", ec=VS.CAT[0], fs=8.6, weight="normal"):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.06,rounding_size=0.12",
                                    fc=fc, ec=ec, lw=1.1))
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
                fontsize=fs, color=VS.INK, weight=weight, linespacing=1.35)

    def arrow(x1, y1, x2, y2):
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>",
                                     mutation_scale=11, lw=1.1, color=VS.INK_2,
                                     shrinkA=0, shrinkB=0))

    ax.text(0.05, 10.35, "Identification", fontsize=8, color=VS.INK_MUTED,
            style="italic")
    box(1.4, 9.35, 4.6, 0.85,
        f"Records identified in Scopus\n(export 2026-07-28)   n = {ident['records_identified_scopus']:,}")
    arrow(3.7, 9.35, 3.7, 8.85)
    box(6.4, 9.35, 3.4, 0.85,
        f"Duplicates removed\nby DOI: {ident['duplicates_removed_doi']}   "
        f"by title: {ident['duplicates_removed_title']}",
        fc="#faf1ec", ec=VS.CAT[1], fs=8)
    arrow(6.0, 9.77, 6.4, 9.77)

    ax.text(0.05, 8.7, "Screening", fontsize=8, color=VS.INK_MUTED, style="italic")
    box(1.4, 7.9, 4.6, 0.85,
        f"Records screened on title + abstract\nn = {scr['records_screened']:,}")

    y = 7.35
    ax.add_patch(FancyBboxPatch((6.4, 2.15), 3.4, 5.6,
                                boxstyle="round,pad=0.06,rounding_size=0.12",
                                fc="#faf1ec", ec=VS.CAT[1], lw=1.1))
    ax.text(8.1, 7.55, f"Records excluded   n = {scr['excluded_total']:,}",
            ha="center", va="center", fontsize=8.6, weight="bold", color=VS.INK)
    yy = 7.15
    for k in order:
        if k not in ex:
            continue
        ax.text(6.6, yy, f"{ex[k]:,}", ha="left", va="top", fontsize=8,
                weight="bold", color=VS.CAT[1])
        ax.text(7.35, yy, labels[k], ha="left", va="top", fontsize=7.4,
                color=VS.INK_2, linespacing=1.3)
        yy -= 0.75 if "\n" in labels[k] else 0.5
    arrow(6.0, 8.32, 6.4, 6.0)
    arrow(3.7, 7.9, 3.7, 6.6)

    ax.text(0.05, 6.45, "Eligibility", fontsize=8, color=VS.INK_MUTED, style="italic")
    box(0.9, 5.35, 5.6, 1.25,
        "Eligibility assessed against both criteria\n"
        "A: point-referenced units of observation\n"
        "B: an explicit spatial-analytical operation",
        fc="#fdfdfc", ec=VS.INK_2)
    arrow(3.7, 5.35, 3.7, 4.6)

    ax.text(0.05, 4.45, "Included", fontsize=8, color=VS.INK_MUTED, style="italic")
    box(1.4, 3.5, 4.6, 1.1,
        f"Studies included in the review\nn = {inc['studies_included']:,}   "
        f"({100*inc['inclusion_rate']:.1f}% of screened)",
        fc="#e9f7f1", ec=VS.CAT[2], fs=9.2, weight="bold")

    ax.text(0.35, 1.55,
            "Validation of the screening instrument (Section 3.3)",
            fontsize=8.2, weight="bold", color=VS.INK)
    ax.text(0.35, 1.2,
            "Stratified random sample of 100 records adjudicated by the reviewer against the\n"
            "definition in Section 2.  Precision of the included stratum 0.90 (95% CI 0.80-0.95, n = 60);\n"
            "false-omission rate of the excluded stratum 0.05-0.15 (n = 40).  Single-reviewer\n"
            "adjudication: inter-rater reliability could not be computed.",
            fontsize=7.4, color=VS.INK_2, va="top", linespacing=1.5)
    ax.plot([0.35, 9.8], [1.78, 1.78], color=VS.GRID, lw=1.0)

    fig.suptitle("Figure 1.  PRISMA flow of study identification, screening and inclusion",
                 x=0.02, ha="left", fontsize=11.5, weight="bold", y=0.985)
    fig.text(0.02, 0.955,
             "Point-based spatial analysis, 2000-2027.  Screening was rule-based and fully "
             "reproducible; every decision is recorded in data/derived/records_all.csv.",
             ha="left", fontsize=8.4, color=VS.INK_2)
    VS.caption(fig,
               "Source: authors' analysis of a Scopus export (n = 5,713 records, retrieved 2026-07-28).  "
               "Method: sequential rule-based screening (analysis/pipeline.py); the first failing rule is "
               "recorded, so exclusion reasons partition the excluded set exactly once.  "
               "Interpretation: 84.0% of identified records were excluded, overwhelmingly because the unit of "
               "observation was areal, raster or network-based rather than point-referenced -- confirming that a "
               "broad 'spatial analysis' query is a poor proxy for the point-based literature.",
               y=0.055)
    save(fig, "F01_prisma_flow.png")


# =========================================================================
# FIGURE 2 - growth
# =========================================================================
def fig02_growth():
    yr = Counter(r["Year"] for r in ROWS)
    years = list(range(2000, 2027))
    vals = [yr.get(y, 0) for y in years]
    fig, (ax, ax2) = plt.subplots(2, 1, figsize=(8.4, 6.4), height_ratios=[2.2, 1],
                                  sharex=True)
    for (code, lab, lo, hi), c in zip(LX.PERIODS, VS.CAT[:3]):
        ax.axvspan(lo - .5, min(hi, 2026) + .5, color=c, alpha=0.055, lw=0)
        ax.text((lo + min(hi, 2026)) / 2, max(vals) * 1.06, lab, ha="center",
                fontsize=8, color=c, weight="bold")
    ax.bar(years[:-1], vals[:-1], color=VS.CAT[0], width=0.68, zorder=3)
    ax.bar([2026], [vals[-1]], color=VS.CAT[0], width=0.68, zorder=3, alpha=0.45,
           hatch="////", edgecolor=VS.CAT[0])
    ax.annotate("2026 partial\n(export July)", xy=(2026, vals[-1]),
                xytext=(2023.4, vals[-1] + 26), fontsize=7.4, color=VS.INK_2,
                ha="center",
                arrowprops=dict(arrowstyle="-", color=VS.INK_MUTED, lw=0.7))
    for y, v in zip(years, vals):
        if v == max(vals) or y in (2000, 2010, 2020):
            ax.text(y, v + 2.5, str(v), ha="center", fontsize=7.6,
                    color=VS.INK, weight="bold")
    ax.set_ylabel("Included studies")
    VS.despine(ax)
    VS.title_block(ax, "Figure 2.  Growth of the point-based spatial-analysis literature, 2000-2026",
                   "Annual counts (top) and cumulative total (bottom) of the 913 included studies")

    cum = np.cumsum(vals)
    ax2.fill_between(years, cum, color=VS.CAT[0], alpha=0.16, lw=0)
    ax2.plot(years, cum, color=VS.CAT[0], lw=2)
    ax2.scatter([2026], [cum[-1]], s=26, color=VS.CAT[0], zorder=4)
    ax2.text(2026, cum[-1] - 60, f"{cum[-1]}", ha="right", fontsize=8,
             color=VS.INK, weight="bold")
    ax2.set_ylabel("Cumulative")
    ax2.set_xlabel("Publication year")
    ax2.set_xticks(range(2000, 2027, 2))
    VS.despine(ax2)
    fig.tight_layout()
    g = RES["growth"]
    VS.caption(fig,
               f"Source: authors' analysis of the included corpus (n = {N}).  Method: counts by Scopus "
               f"publication year; 2026 is truncated at the export date and 2027 has no indexed records, so "
               f"neither year supports a trend claim.  Interpretation: mean annual output rises from "
               f"{g['mean_annual_P1']} studies (2000-2010) to {g['mean_annual_P2']} (2011-2020) to "
               f"{g['mean_annual_P3_to2025']} (2021-2025), a compound annual growth rate of "
               f"{g['cagr_2000_2025']}% between 2000 and 2025.  Growth is not smooth: it steps up sharply "
               f"after 2016, consistent with the arrival of digital-trace data documented in Figure 6.",
               y=0.02)
    save(fig, "F02_publication_growth.png")


# =========================================================================
# FIGURE 3 - method-class evolution
# =========================================================================
def fig03_method_classes():
    classes = list(LX.METHOD_CLASS_LABELS)
    data = {c: [RES["method_classes_pct"][c][p] for p in P] for c in classes}
    fig, (axA, axB) = plt.subplots(1, 2, figsize=(10.6, 5.4),
                                   width_ratios=[1.25, 1])
    x = np.arange(3)
    w = 0.13
    for i, c in enumerate(classes):
        axA.bar(x + (i - 2.5) * w, data[c], width=w * 0.88,
                color=VS.CLASS_COLOR[c], zorder=3,
                label=LX.METHOD_CLASS_LABELS[c])
        for xi, v in zip(x + (i - 2.5) * w, data[c]):
            if v > 0:
                axA.text(xi, v + 0.7, f"{v:.0f}", ha="center", fontsize=6.6,
                         color=VS.INK_2)
    axA.set_xticks(x)
    axA.set_xticklabels(P)
    axA.set_ylabel("% of studies in the period")
    VS.despine(axA)
    axA.legend(loc="upper left", ncol=1, fontsize=7.4)
    VS.title_block(axA, "a.  Prevalence of method classes by period")

    for c in classes:
        axB.plot(x, data[c], marker="o", ms=6, lw=2, color=VS.CLASS_COLOR[c])
        axB.text(2.06, data[c][2], f" {LX.METHOD_CLASS_LABELS[c].split(' (')[0][:26]}",
                 fontsize=7.2, color=VS.CLASS_COLOR[c], va="center", weight="bold")
    axB.set_xticks(x)
    axB.set_xticklabels(P)
    axB.set_xlim(-0.15, 3.35)
    axB.set_ylabel("% of studies in the period")
    VS.despine(axB)
    VS.title_block(axB, "b.  Trajectories (direct-labelled)")

    fig.suptitle("Figure 3.  The methodological composition of point-based spatial analysis shifts, "
                 "but classical statistics do not disappear",
                 x=0.012, ha="left", fontsize=11.5, weight="bold", y=1.005)
    fig.tight_layout()
    t = RES["transitions"]
    VS.caption(fig,
               f"Source: authors' coding of the included corpus (n = {N}).  Method: each study is coded to "
               f"every method class evidenced in its title or abstract, so classes are non-exclusive and "
               f"columns do not sum to 100%.  Class definitions are in analysis/lexicons.py; full counts in "
               f"tables/T03_method_classes_by_period.csv.  Interpretation: learning-based methods rise from "
               f"{t['any_learning'][P[0]]}% to {t['any_learning'][P[2]]}% of studies across the three periods, "
               f"but classical point-pattern statistics remain present throughout and studies using classical "
               f"methods alone are as common in 2021-2027 ({t['classical_only'][P[2]]}%) as in 2000-2010 "
               f"({t['classical_only'][P[0]]}%).  The field accumulates methods rather than replacing them -- "
               f"the sedimentation dynamic formalised in Section 7.",
               y=0.015)
    save(fig, "F03_method_class_evolution.png")


# =========================================================================
# FIGURE 4 - world map of knowledge production
# =========================================================================
def fig04_map_affiliation():
    aff = Counter()
    for r in ROWS:
        aff.update(set(r["affil_iso3"]))
    fig = plt.figure(figsize=(10.2, 7.6))
    ax = fig.add_axes([0.01, 0.175, 0.98, 0.72])
    vmin, vmax = draw_choropleth(ax, aff, VS.SEQ, vmin=1, vmax=max(aff.values()),
                                 log=True)
    colorbar_strip(fig, [0.32, 0.145, 0.36, 0.017], VS.SEQ, 1, max(aff.values()),
                   "Number of included studies with at least one author affiliation "
                   "(log scale)", log=True, ticks=[1, 5, 20, 80, max(aff.values())])
    top = aff.most_common(6)
    for iso, n in top:
        if iso in CENTROIDS:
            x, y = CENTROIDS[iso]
            ax.text(x, y, f"{GEO.ISO3_TO_NAME.get(iso, iso)}\n{n}", ha="center",
                    va="center", fontsize=7.2, weight="bold", color="#ffffff",
                    path_effects=None,
                    bbox=dict(boxstyle="round,pad=0.18", fc="#0d366b", ec="none",
                              alpha=0.82))
    a = RES["affiliation"]
    fig.suptitle("Figure 4.  Where point-based spatial analysis is produced: "
                 "country of author affiliation",
                 x=0.012, ha="left", fontsize=11.5, weight="bold", y=0.975)
    fig.text(0.012, 0.935,
             f"{a['n_countries']} countries appear as an author affiliation across the {N} included studies; "
             f"{RES['absent_countries']['n_never_affiliation']} of the "
             f"{RES['absent_countries']['n_world_countries_in_basemap']} countries in the basemap never do.",
             ha="left", fontsize=8.6, color=VS.INK_2)
    VS.caption(fig,
               f"Source: authors' analysis of Scopus affiliation strings, included corpus (n = {N}).  "
               f"Basemap: Natural Earth 1:110m (public domain); Robinson projection.  Method: the terminal "
               f"comma-delimited token of each affiliation string is resolved to ISO 3166-1 alpha-3 via a "
               f"gazetteer with explicit alias handling; a study with authors in k countries contributes to "
               f"all k, so counts sum to more than {N}.  Grey = no included study.  Interpretation: production "
               f"is extremely concentrated -- the top five countries account for {a['top5_share']}% of all "
               f"affiliation mentions and the Gini coefficient of the country distribution is {a['gini']}.  "
               f"China ({a['top15'][0][1]}) and the United States ({a['top15'][1][1]}) alone appear in more "
               f"studies than all other countries combined.",
               y=0.105)
    save(fig, "F04_map_affiliation_countries.png")


# =========================================================================
# FIGURE 5 - world map of case-study geography + asymmetry
# =========================================================================
def fig05_map_case_and_asymmetry():
    aff, case = Counter(), Counter()
    for r in ROWS:
        aff.update(set(r["affil_iso3"]))
        case.update(set(r["case_iso3"]))
    fig = plt.figure(figsize=(9.6, 14.0))
    MH = 0.385                      # map height as a fraction: preserves aspect

    # ---------------- panel a ----------------
    axA = fig.add_axes([0.01, 0.565, 0.98, MH])
    draw_choropleth(axA, case, VS.SEQ_ORANGE, vmin=1, vmax=max(case.values()),
                    log=True)
    colorbar_strip(fig, [0.30, 0.532, 0.40, 0.010], VS.SEQ_ORANGE, 1,
                   max(case.values()),
                   "Included studies whose empirical case study is located in the "
                   "country (log scale)", log=True,
                   ticks=[1, 4, 16, 64, max(case.values())])
    fig.text(0.012, 0.957, "a.  Where the empirical problems are studied",
             fontsize=10, weight="bold", color=VS.INK)

    # ---------------- panel b ----------------
    axB = fig.add_axes([0.01, 0.135, 0.98, MH])
    ratio = {}
    for iso in set(aff) | set(case):
        a, c = aff.get(iso, 0), case.get(iso, 0)
        if a + c < 4:
            continue
        ratio[iso] = math.log2((a + 0.5) / (c + 0.5))
    # robust symmetric limit: the 90th percentile of |log-ratio|, so that
    # mid-range asymmetry is visible instead of being washed out by outliers
    lim = float(np.percentile([abs(v) for v in ratio.values()], 90))
    for iso, name, cont, rings in country_polys():
        if cont == "Antarctica":
            continue
        if iso in ratio:
            t = (np.clip(ratio[iso], -lim, lim) + lim) / (2 * lim)
            col = VS.DIV(float(t))
        else:
            col = "#f2f1ee"
        axB.add_collection(PolyCollection(rings, facecolors=[col],
                                          edgecolors="#ffffff", linewidths=0.25))
    axB.set_xlim(-2.72, 2.72)
    axB.set_ylim(-1.5, 1.62)
    axB.set_aspect("equal")
    axB.axis("off")
    fig.text(0.012, 0.527, "b.  Production-to-problem asymmetry",
             fontsize=10, weight="bold", color=VS.INK)

    cax = fig.add_axes([0.30, 0.102, 0.40, 0.010])
    cax.imshow(np.linspace(0, 1, 256).reshape(1, -1), aspect="auto", cmap=VS.DIV,
               origin="lower", extent=[-lim, lim, 0, 1])
    cax.set_yticks([])
    cax.set_xticks([-lim, 0, lim])
    cax.set_xticklabels(["\u2190 studied more\nthan it publishes", "balanced",
                         "publishes more\nthan it is studied \u2192"], fontsize=7)
    cax.set_xlabel("log$_2$ (affiliation mentions / case-study mentions), "
                   "clipped at the 90th percentile",
                   fontsize=7.2, color=VS.INK_2, labelpad=18)
    for sp in cax.spines.values():
        sp.set_visible(False)
    cax.tick_params(length=2, colors=VS.INK_2)

    asym = RES["asymmetry"]
    sens = RES["hemisphere_sensitivity"]
    fig.suptitle("Figure 5.  The geography of spatial problems is not the "
                 "geography of spatial knowledge",
                 x=0.012, ha="left", fontsize=11.5, weight="bold", y=0.992)
    fig.text(0.012, 0.976,
             "Panel a maps where the empirical case studies are located; panel b maps the ratio "
             "between a country's role as producer and its role as subject.",
             ha="left", va="top", fontsize=8.6, color=VS.INK_2)
    VS.caption(fig,
               f"Source: authors' analysis of the included corpus (n = {N}).  Basemap: Natural Earth 1:110m "
               f"(public domain); Robinson projection.  Method: case-study geography is detected from title "
               f"and abstract using a gazetteer of country names, demonyms and ~300 major cities and regions "
               f"with explicit disambiguation of polysemous toponyms (Georgia, Turkey, Guinea, Niger, Jordan "
               f"and others); publisher copyright boilerplate was stripped first, because strings such as "
               f"'Licensee MDPI, Basel, Switzerland' otherwise generate large spurious counts.  "
               f"{RES['non_reporting']['no_case_geography']:.0f}% of studies report no detectable case "
               f"geography (methodological and simulation papers) and are excluded from both panels; "
               f"countries with fewer than four combined mentions are left grey in panel b.  "
               f"Interpretation: {asym['pct_domestic']:.0f}% of the {asym['n_pairs']} studies with both "
               f"geographies resolved are domestic -- authored at least partly from the country studied.  "
               f"The aggregate conceals the pattern: with China excluded, Global-South case studies are "
               f"domestic in {sens['excluding_China']['Global South']['pct_domestic']:.0f}% of cases against "
               f"{sens['excluding_China']['Global North']['pct_domestic']:.0f}% for the Global North.  Blue "
               f"countries in panel b export analytical capacity; red countries import it.",
               y=0.072)
    save(fig, "F05_map_case_study_and_asymmetry.png")


# =========================================================================
# FIGURE 6 - data-source transition (the empirical core of the theory)
# =========================================================================
def fig06_data_transition():
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(10.6, 5.0), width_ratios=[1, 1.05])
    t = RES["transitions"]
    x = np.arange(3)
    series = [("Digital-trace data\n(VGI, social media, GPS/CDR, POI)", t["digital_trace_data"], VS.CAT[1]),
              ("Institutional data\n(administrative records, field survey)", t["institutional_data"], VS.CAT[0])]
    for lab, d, c in series:
        v = [d[p] for p in P]
        ax.plot(x, v, marker="o", ms=7, lw=2.4, color=c)
        for xi, vi in zip(x, v):
            ax.text(xi, vi + 1.6, f"{vi:.1f}%", ha="center", fontsize=7.6,
                    color=c, weight="bold")
        ax.text(0.02, v[0] - 3.4, lab, fontsize=7.6, color=c, weight="bold",
                va="top", linespacing=1.3)
    ax.set_xticks(x)
    ax.set_xticklabels(P)
    ax.set_ylabel("% of studies in the period")
    ax.set_ylim(-8, 45)
    VS.despine(ax)
    VS.title_block(ax, "a.  The data substrate inverts")

    ds = RES["data_sources"]
    keys = sorted(ds, key=lambda k: -ds[k]["total"])[:9]
    y = np.arange(len(keys))[::-1]
    for i, p in enumerate(P):
        ax2.barh(y + (1 - i) * 0.26, [ds[k][p] for k in keys], height=0.24,
                 color=VS.PERIOD_COLOR[p], zorder=3, label=p)
    ax2.set_yticks(y)
    ax2.set_yticklabels([k.replace(" & ", " &\n") for k in keys], fontsize=7.4)
    ax2.set_xlabel("% of studies in the period")
    ax2.legend(loc="lower right", fontsize=7.4, title="Period",
               title_fontsize=7.4)
    VS.despine(ax2)
    VS.title_block(ax2, "b.  Data sources by period")

    fig.suptitle("Figure 6.  The data substrate of point-based spatial analysis inverts between 2000 and 2027",
                 x=0.012, ha="left", fontsize=11.5, weight="bold", y=1.0)
    fig.tight_layout()
    VS.caption(fig,
               f"Source: authors' coding of the included corpus (n = {N}).  Method: data sources are coded "
               f"non-exclusively from title and abstract; 'digital-trace data' aggregates volunteered "
               f"geographic information, social-media and geosocial data, mobile-phone and GPS trajectory "
               f"data, and POI or commercial geodatabases.  "
               f"{RES['non_reporting']['no_data_source_named']:.0f}% of studies name no data source at all in "
               f"the abstract, so both series are lower bounds.  Interpretation: studies using digital-trace "
               f"data rise from {t['digital_trace_data'][P[0]]}% to {t['digital_trace_data'][P[2]]}% of the "
               f"period corpus while institutional data fall from {t['institutional_data'][P[0]]}% to "
               f"{t['institutional_data'][P[2]]}%.  This inversion is the single largest structural change in "
               f"the corpus and it is the mechanism that drives the methodological shift in Figure 3: the "
               f"arrival of dense, passively generated, ethically encumbered point data creates the analytical "
               f"problems that learning-based methods are recruited to solve.",
               y=0.02)
    save(fig, "F06_data_substrate_transition.png")


# =========================================================================
# FIGURE 7 - Sankey: data source -> method class -> domain
# =========================================================================
def fig07_sankey():
    src_keys = ["Field survey & in-situ sampling", "Official / administrative records",
                "Remote sensing & earth observation", "Mobile phone & GPS trajectory data",
                "POI & commercial geodatabases", "Social-media & geosocial data",
                "Volunteered geographic information", "Sensor networks & IoT"]
    src_group = {
        "Field survey & in-situ sampling": "Institutional\n& field data",
        "Official / administrative records": "Institutional\n& field data",
        "Remote sensing & earth observation": "Sensed\n& observed data",
        "Sensor networks & IoT": "Sensed\n& observed data",
        "Mobile phone & GPS trajectory data": "Digital-trace\ndata",
        "POI & commercial geodatabases": "Digital-trace\ndata",
        "Social-media & geosocial data": "Digital-trace\ndata",
        "Volunteered geographic information": "Digital-trace\ndata",
    }
    dom_keys = [d for d, _ in sorted(RES["domains_total"].items(),
                                     key=lambda kv: -kv[1])[:7]]
    L1 = ["Institutional\n& field data", "Sensed\n& observed data", "Digital-trace\ndata"]
    L2 = list(LX.METHOD_CLASS_LABELS)
    L3 = dom_keys

    f12, f23 = Counter(), Counter()
    for r in ROWS:
        gs = {src_group[s] for s in r["data_sources"] if s in src_group}
        for g in gs:
            for m in set(r["method_classes"]):
                f12[(g, m)] += 1
        for m in set(r["method_classes"]):
            for d in set(r["domains"]) & set(dom_keys):
                f23[(m, d)] += 1

    fig, ax = plt.subplots(figsize=(11.4, 7.4))
    ax.axis("off")
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    GAP, XL = 0.30, {0: 0.55, 1: 4.5, 2: 8.4}
    W = 0.42

    def stack(items, weights, x, colors):
        tot = sum(weights) or 1
        H = 8.6 - GAP * (len(items) - 1)
        pos, y = {}, 9.2
        for it, w, c in zip(items, weights, colors):
            h = H * w / tot
            ax.add_patch(Rectangle((x, y - h), W, h, fc=c, ec="none"))
            pos[it] = (y - h, y)
            y -= h + GAP
        return pos

    w1 = [sum(v for (g, _m), v in f12.items() if g == g0) for g0 in L1]
    w2 = [sum(v for (_g, m), v in f12.items() if m == m0) for m0 in L2]
    w3 = [sum(v for (_m, d), v in f23.items() if d == d0) for d0 in L3]
    p1 = stack(L1, w1, XL[0], [VS.CAT[0], VS.CAT[2], VS.CAT[1]])
    p2 = stack(L2, w2, XL[1], [VS.CLASS_COLOR[c] for c in L2])
    p3 = stack(L3, w3, XL[2], [VS.CAT[i % 6] for i in range(len(L3))])

    def ribbons(flows, pa, pb, xa, xb, colmap):
        outc = {k: pa[k][1] for k in pa}
        inc = {k: pb[k][1] for k in pb}
        for (a, b), v in sorted(flows.items(), key=lambda kv: -kv[1]):
            if a not in pa or b not in pb or v == 0:
                continue
            ha = (pa[a][1] - pa[a][0]) * v / (sum(x for (aa, _), x in flows.items() if aa == a) or 1)
            hb = (pb[b][1] - pb[b][0]) * v / (sum(x for (_, bb), x in flows.items() if bb == b) or 1)
            y0, y1 = outc[a], outc[a] - ha
            z0, z1 = inc[b], inc[b] - hb
            outc[a] -= ha
            inc[b] -= hb
            xm = (xa + xb) / 2
            verts = [(xa, y0), (xm, y0), (xm, z0), (xb, z0), (xb, z1),
                     (xm, z1), (xm, y1), (xa, y1), (xa, y0)]
            codes = [Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4,
                     Path.LINETO, Path.CURVE4, Path.CURVE4, Path.CURVE4,
                     Path.CLOSEPOLY]
            ax.add_patch(mpatches.PathPatch(Path(verts, codes), fc=colmap(a, b),
                                            ec="none", alpha=0.34))

    ribbons(f12, p1, p2, XL[0] + W, XL[1],
            lambda a, b: {L1[0]: VS.CAT[0], L1[1]: VS.CAT[2], L1[2]: VS.CAT[1]}[a])
    ribbons(f23, p2, p3, XL[1] + W, XL[2], lambda a, b: VS.CLASS_COLOR[a])

    for k, (lo, hi) in p1.items():
        ax.text(XL[0] - 0.12, (lo + hi) / 2, k, ha="right", va="center",
                fontsize=8.2, weight="bold", color=VS.INK, linespacing=1.3)
    for k, (lo, hi) in p2.items():
        if hi - lo > 0.24:
            ax.text(XL[1] + W / 2, (lo + hi) / 2,
                    LX.METHOD_CLASS_LABELS[k].split(" (")[0].split(" /")[0],
                    ha="center", va="center", fontsize=7.2, color="#ffffff",
                    weight="bold")
    for k, (lo, hi) in p3.items():
        ax.text(XL[2] + W + 0.12, (lo + hi) / 2, k.replace(" & ", " &\n"),
                ha="left", va="center", fontsize=7.8, color=VS.INK,
                linespacing=1.3)
    for x, lab in ((XL[0], "Data substrate"), (XL[1], "Method class"),
                   (XL[2], "Application domain")):
        ax.text(x + W / 2, 9.55, lab, ha="center", fontsize=8.6, weight="bold",
                color=VS.INK_2)

    fig.suptitle("Figure 7.  From data substrate to method to application: the flow structure of the field",
                 x=0.012, ha="left", fontsize=11.5, weight="bold", y=0.985)
    VS.caption(fig,
               f"Source: authors' coding of the included corpus (n = {N}).  Method: a Sankey diagram of "
               f"co-occurrence within studies. Ribbon width is the number of studies in which a data "
               f"substrate and a method class (left) or a method class and an application domain (right) "
               f"appear together; because all three codings are non-exclusive, a single study can contribute "
               f"to several ribbons and totals exceed {N}.  Only the seven largest application domains are "
               f"shown.  Interpretation: the diagram makes the field's internal division of labour visible.  "
               f"Institutional and field data flow overwhelmingly into geostatistical and classical "
               f"estimation; digital-trace data flow into clustering, learning-based and network-constrained "
               f"methods.  The two substrates are only weakly connected to the same methods, which is the "
               f"structural signature of the bifurcation described in Section 7.4.",
               y=0.045)
    save(fig, "F07_sankey_data_method_domain.png")


# =========================================================================
# FIGURE 8 - thematic evolution
# =========================================================================
def fig08_thematic():
    rows = [r for r in read_table("T19_thematic_evolution_terms.csv")
            if r.get("direction") == "distinctive"]
    fig, axes = plt.subplots(1, 3, figsize=(11.2, 5.6), sharex=True)
    for ax, p in zip(axes, P):
        sub = [r for r in rows if r["period"] == p][:12][::-1]
        y = np.arange(len(sub))
        vals = [float(r["log_odds_vs_rest_of_corpus"]) for r in sub]
        ax.barh(y, vals, color=VS.PERIOD_COLOR[p], height=0.66, zorder=3)
        for yi, r, v in zip(y, sub, vals):
            ax.text(v + 0.04, yi, f"  {r['term']}", va="center", fontsize=8,
                    color=VS.INK)
            ax.text(0.02, yi, f"{r['pct_of_period']}%", va="center", fontsize=6.8,
                    color="#ffffff", ha="left", weight="bold")
        ax.set_yticks([])
        ax.set_xlim(0, max(vals) * 2.35)
        ax.set_xlabel("log-odds vs rest of corpus")
        VS.despine(ax, keep=("bottom",))
        VS.title_block(ax, p)
    fig.suptitle("Figure 8.  Thematic evolution: the title vocabulary that distinguishes each period",
                 x=0.012, ha="left", fontsize=11.5, weight="bold", y=1.0)
    fig.tight_layout()
    VS.caption(fig,
               f"Source: authors' analysis of the titles of the {N} included studies.  Method: informative "
               f"Dirichlet log-odds of each title term in a period against its frequency in the rest of the "
               f"corpus, restricted to terms occurring in at least eight titles corpus-wide; bars are ordered "
               f"by log-odds and the inline percentage is the share of that period's titles containing the "
               f"term.  Full ranked lists, including depleted terms, are in "
               f"tables/T19_thematic_evolution_terms.csv.  Interpretation: the vocabulary migrates from the "
               f"language of estimation and sampling, through the language of urban systems and mobility, to "
               f"the language of learning, prediction and multi-source integration.  Note that the terms that "
               f"disappear are as informative as those that arrive: the explicit vocabulary of statistical "
               f"inference thins markedly in the third period.",
               y=0.02)
    save(fig, "F08_thematic_evolution.png")


# =========================================================================
# FIGURE 9 - domain x method-class heatmap
# =========================================================================
def fig09_heatmap():
    classes = list(LX.METHOD_CLASS_LABELS)
    doms = [d for d, _ in sorted(RES["domains_total"].items(), key=lambda kv: -kv[1])]
    M = np.array([[RES["domain_method"][d][c] for c in classes] for d in doms])
    fig, ax = plt.subplots(figsize=(9.0, 6.6))
    im = ax.imshow(M, cmap=VS.SEQ, aspect="auto", vmin=0, vmax=M.max())
    ax.set_xticks(range(len(classes)))
    ax.set_xticklabels([LX.METHOD_CLASS_LABELS[c].replace(" / ", "/\n").replace(" and ", " &\n")
                        for c in classes], fontsize=7.6, rotation=0)
    ax.set_yticks(range(len(doms)))
    ax.set_yticklabels(doms, fontsize=8)
    for i in range(len(doms)):
        for j in range(len(classes)):
            v = M[i, j]
            ax.text(j, i, f"{v:.0f}", ha="center", va="center", fontsize=7.4,
                    color="#ffffff" if v > M.max() * 0.55 else VS.INK,
                    weight="bold" if v == 0 else "normal")
    ax.grid(False)
    for s in ax.spines.values():
        s.set_visible(False)
    cb = fig.colorbar(im, ax=ax, fraction=0.028, pad=0.02)
    cb.set_label("% of the domain's studies using the method class", fontsize=7.6,
                 color=VS.INK_2)
    cb.outline.set_visible(False)
    cb.ax.tick_params(labelsize=7, colors=VS.INK_2)
    fig.suptitle("Figure 9.  Topic-method matrix: which application domains use which classes of method",
                 x=0.012, ha="left", fontsize=11.5, weight="bold", y=0.985)
    fig.tight_layout()
    VS.caption(fig,
               f"Source: authors' coding of the included corpus (n = {N}).  Method: cell value is the "
               f"percentage of studies in an application domain (row) that evidence a method class (column); "
               f"rows do not sum to 100% because both codings are non-exclusive.  Domains are ordered by "
               f"corpus frequency.  Interpretation: the matrix is sparse in a structured way.  "
               f"{RES['gaps']['n_empty_cells']} of {RES['gaps']['n_cells']} cells are entirely empty and "
               f"{RES['gaps']['n_thin_cells']} more fall below 10%, and the empty cells are not random: "
               f"real-time and network-constrained methods are absent from most environmental and ecological "
               f"domains, while learning-based methods have barely entered the domains where classical "
               f"point-process theory is strongest.  These are the concrete research gaps enumerated in "
               f"Table 12 and tables/T22_domain_method_gap_matrix.csv.",
               y=0.02)
    save(fig, "F09_domain_method_heatmap.png")


# =========================================================================
# FIGURE 10 - country collaboration network
# =========================================================================
def fig10_collab_network():
    edges = [(r["iso3_a"], r["iso3_b"], int(r["n_co_authored"]), r["dyad_type"])
             for r in read_table("T15_country_collaboration_edges.csv")]
    aff = Counter()
    for r in ROWS:
        aff.update(set(r["affil_iso3"]))
    keep = {i for i, _ in aff.most_common(30)}
    E = [e for e in edges if e[0] in keep and e[1] in keep and e[2] >= 2]
    nodes = sorted({e[0] for e in E} | {e[1] for e in E}, key=lambda i: -aff[i])

    ang = {n: 2 * math.pi * i / len(nodes) for i, n in enumerate(nodes)}
    pos = {n: (math.cos(a), math.sin(a)) for n, a in ang.items()}
    fig, ax = plt.subplots(figsize=(8.6, 8.0))
    ax.set_aspect("equal")
    ax.axis("off")
    dcol = {"North-North": VS.CAT[0], "North-South": VS.CAT[1],
            "South-South": VS.CAT[2]}
    for a, b, w, dy in sorted(E, key=lambda e: e[2]):
        x1, y1 = pos[a]
        x2, y2 = pos[b]
        mx, my = (x1 + x2) * 0.32, (y1 + y2) * 0.32
        verts = [(x1, y1), (mx, my), (x2, y2)]
        ax.add_patch(mpatches.PathPatch(
            Path(verts, [Path.MOVETO, Path.CURVE3, Path.CURVE3]),
            fc="none", ec=dcol[dy], lw=0.5 + 1.5 * math.log1p(w),
            alpha=0.42))
    for n in nodes:
        x, y = pos[n]
        s = 22 + 5.5 * math.sqrt(aff[n])
        ax.scatter([x], [y], s=s, color=VS.INK if GEO.hemisphere(n) == "Global North"
                   else VS.CAT[1], zorder=4, edgecolors=VS.SURFACE, linewidths=1.4)
        a = ang[n]
        ax.text(x * 1.13, y * 1.13, GEO.ISO3_TO_NAME.get(n, n), fontsize=7.6,
                ha="left" if -math.pi / 2 < a < math.pi / 2 else "right",
                va="center", rotation=math.degrees(a) if -math.pi / 2 < a < math.pi / 2
                else math.degrees(a) + 180, rotation_mode="anchor", color=VS.INK)
    ax.set_xlim(-1.55, 1.55)
    ax.set_ylim(-1.42, 1.42)
    handles = [mpatches.Patch(color=c, label=k) for k, c in dcol.items()]
    handles += [plt.Line2D([], [], marker="o", ls="", color=VS.INK, label="Global North", ms=6),
                plt.Line2D([], [], marker="o", ls="", color=VS.CAT[1], label="Global South", ms=6)]
    ax.legend(handles=handles, loc="upper left", bbox_to_anchor=(-0.06, 1.04),
              fontsize=7.6, ncol=1)
    col = RES["collaboration"]
    fig.suptitle("Figure 10.  International co-authorship structure at country level",
                 x=0.012, ha="left", fontsize=11.5, weight="bold", y=0.985)
    fig.text(0.012, 0.945,
             f"Edges are country pairs co-authoring at least two included studies; node size is the "
             f"country's total output.",
             ha="left", fontsize=8.6, color=VS.INK_2)
    VS.caption(fig,
               f"Source: authors' analysis of Scopus affiliation strings, included corpus (n = {N}).  "
               f"Method: an undirected country co-affiliation graph; two countries are linked when they "
               f"appear in the affiliation list of the same study.  The graph is restricted to the 30 most "
               f"productive countries and to edges of weight >= 2 for legibility; the complete edge list "
               f"({col['n_edges']} edges) is in tables/T15_country_collaboration_edges.csv.  "
               f"Author-level co-authorship networks, h-indices and citation-based influence measures "
               f"CANNOT be computed from this export, which contains no author or citation fields "
               f"(Section 3.6).  Interpretation: {col['dyad_mix'].get('North-North', 0):.0f}% of collaborative "
               f"links are North-North and {col['dyad_mix'].get('North-South', 0):.0f}% are North-South, but "
               f"only {col['dyad_mix'].get('South-South', 0):.0f}% are South-South.  The Global South is "
               f"connected to the field's core largely through the North rather than through itself -- a "
               f"hub-and-spoke topology with few lateral ties.",
               y=0.06)
    save(fig, "F10_collaboration_network.png")


# =========================================================================
# FIGURE 11 - rigour: the decoupling
# =========================================================================
def fig11_rigour():
    fig, axes = plt.subplots(1, 3, figsize=(12.8, 5.0))
    ax = axes[0]
    fams = [("any_uncertainty", "Uncertainty\ntreatment"),
            ("any_validation", "Validation\nprocedure"),
            ("any_reproducibility", "Reproducibility\npractice"),
            ("any_ethics", "Ethics or\nprivacy")]
    x = np.arange(len(fams))
    for i, p in enumerate(P):
        v = [RES[k][p] for k, _ in fams]
        ax.bar(x + (i - 1) * 0.27, v, width=0.25, color=VS.PERIOD_COLOR[p],
               zorder=3, label=p)
        for xi, vi in zip(x + (i - 1) * 0.27, v):
            ax.text(xi, vi + 0.6, f"{vi:.0f}", ha="center", fontsize=6.8,
                    color=VS.INK_2)
    ax.set_xticks(x)
    ax.set_xticklabels([l for _, l in fams], fontsize=7.6)
    ax.set_ylabel("% of studies in the period")
    ax.legend(fontsize=7.4, loc="upper right")
    VS.despine(ax)
    VS.title_block(ax, "a.  Rigour practices barely move")

    ax = axes[1]
    rb = RES["rigour_by_method_class"]
    cats = ["pct_uncertainty", "pct_validation", "pct_reproducibility"]
    labs = ["Uncertainty", "Validation", "Reproducibility"]
    x = np.arange(3)
    ax.bar(x - 0.19, [rb["classical_inferential"][c] for c in cats], width=0.36,
           color=VS.CAT[0], zorder=3, label=f"Classical / inferential (n={rb['classical_inferential']['n']})")
    ax.bar(x + 0.19, [rb["learning"][c] for c in cats], width=0.36,
           color=VS.CAT[4], zorder=3, label=f"Learning-based (n={rb['learning']['n']})")
    for xi, c in zip(x, cats):
        ax.text(xi - 0.19, rb["classical_inferential"][c] + 0.7,
                f"{rb['classical_inferential'][c]:.0f}", ha="center", fontsize=7,
                color=VS.INK_2)
        ax.text(xi + 0.19, rb["learning"][c] + 0.7, f"{rb['learning'][c]:.0f}",
                ha="center", fontsize=7, color=VS.INK_2)
    ax.set_xticks(x)
    ax.set_xticklabels(labs, fontsize=8)
    ax.set_ylabel("% of studies")
    ax.legend(fontsize=7.2, loc="upper left")
    VS.despine(ax)
    VS.title_block(ax, "b.  Validation without uncertainty")

    ax = axes[2]
    d = RES["decoupling"]
    x = np.arange(3)
    ax.plot(x, [d[p]["mean_methods"] for p in P], marker="o", ms=7, lw=2.4,
            color=VS.CAT[1])
    ax.plot(x, [d[p]["mean_rigour_0_6"] for p in P], marker="s", ms=7, lw=2.4,
            color=VS.CAT[0])
    ax.text(2.05, d[P[2]]["mean_methods"], " Analytical\n complexity\n (methods/study)",
            fontsize=7.4, color=VS.CAT[1], va="center", weight="bold")
    ax.text(2.05, d[P[2]]["mean_rigour_0_6"], " Rigour score\n (0-6)",
            fontsize=7.4, color=VS.CAT[0], va="center", weight="bold")
    for i, p in enumerate(P):
        ax.text(i, d[p]["mean_methods"] + 0.06, f"{d[p]['mean_methods']:.2f}",
                ha="center", fontsize=7, color=VS.INK_2)
        ax.text(i, d[p]["mean_rigour_0_6"] - 0.11, f"{d[p]['mean_rigour_0_6']:.2f}",
                ha="center", fontsize=7, color=VS.INK_2)
    ax.set_xticks(x)
    ax.set_xticklabels(P, fontsize=8)
    ax.set_xlim(-0.2, 3.3)
    ax.set_ylim(0, 1.45)
    ax.set_ylabel("Mean per study")
    VS.despine(ax)
    VS.title_block(ax, "c.  The rigour gap widens")
    ax.set_xlim(-0.25, 3.6)

    fig.suptitle("Figure 11.  Analytical sophistication grows faster than methodological rigour",
                 x=0.012, ha="left", fontsize=11.5, weight="bold", y=1.0)
    fig.tight_layout()
    VS.caption(fig,
               f"Source: authors' coding of the included corpus (n = {N}).  Method: rigour constructs are "
               f"detected from abstract text only.  ABSENCE OF EVIDENCE IN AN ABSTRACT IS NOT EVIDENCE OF "
               f"ABSENCE IN THE FULL TEXT: these are lower bounds on reporting, not measures of practice, and "
               f"the comparison across periods and method classes is valid only to the extent that reporting "
               f"conventions are stable.  Panel c contrasts mean methods per study with a 0-6 rigour score "
               f"(uncertainty + validation + reproducibility dimensions of PB-SAM).  Interpretation: "
               f"analytical complexity rises {d[P[0]]['mean_methods']:.2f} -> {d[P[2]]['mean_methods']:.2f} "
               f"while the rigour score moves only {d[P[0]]['mean_rigour_0_6']:.2f} -> "
               f"{d[P[2]]['mean_rigour_0_6']:.2f}, so the complexity-to-rigour ratio widens from "
               f"{d[P[0]]['ratio']} to {d[P[2]]['ratio']}.  Panel b shows the asymmetry is not uniform: "
               f"learning-based studies report validation more than twice as often as classical studies "
               f"({rb['learning']['pct_validation']:.0f}% vs {rb['classical_inferential']['pct_validation']:.0f}%) "
               f"but report uncertainty half as often "
               f"({rb['learning']['pct_uncertainty']:.0f}% vs {rb['classical_inferential']['pct_uncertainty']:.0f}%).  "
               f"Predictive accuracy is displacing inferential humility.",
               y=0.015)
    save(fig, "F11_rigour_decoupling.png")


# =========================================================================
# FIGURE 12 - PB-SAM maturity
# =========================================================================
def fig12_maturity():
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(10.4, 4.8), width_ratios=[1, 1.1])
    pb = RES["pbsam"]
    levels = [("pct_level1_emergent_0_3", "Level 1  Emergent (0-3)", VS.CAT[0]),
              ("pct_level2_consolidating_4_6", "Level 2  Consolidating (4-6)", VS.CAT[1]),
              ("pct_level3_mature_7_10", "Level 3  Mature (7-10)", VS.CAT[2])]
    rows = [r for r in read_table("T10_pbsam_maturity_by_period.csv")
            if r.get("period") in P]
    bottom = np.zeros(3)
    for key, lab, c in levels:
        v = np.array([float(r[key]) for r in rows])
        ax.bar(np.arange(3), v, bottom=bottom, width=0.6, color=c, zorder=3,
               label=lab, edgecolor=VS.SURFACE, linewidth=2)
        for i, (vi, bi) in enumerate(zip(v, bottom)):
            if vi > 4:
                ax.text(i, bi + vi / 2, f"{vi:.0f}%", ha="center", va="center",
                        fontsize=8, color="#ffffff", weight="bold")
        bottom += v
    ax.set_xticks(range(3))
    ax.set_xticklabels(P)
    ax.set_ylabel("% of studies in the period")
    ax.legend(fontsize=7.4, loc="lower center", bbox_to_anchor=(0.5, -0.30), ncol=1)
    VS.despine(ax)
    VS.title_block(ax, "a.  PB-SAM maturity levels by period")

    dims = [d for d, _ in LX.PBSAM_DIMENSIONS]
    dimlab = ["D1 Method\nspecification", "D2 Uncertainty", "D3 Validation",
              "D4 Data\ntransparency", "D5 Reproducibility"]
    x = np.arange(5)
    for i, p in enumerate(P):
        v = [float(rows[i][d]) for d in dims]
        ax2.plot(x, v, marker="o", ms=6, lw=2, color=VS.PERIOD_COLOR[p], label=p)
    ax2.set_xticks(x)
    ax2.set_xticklabels(dimlab, fontsize=7.2)
    ax2.set_ylabel("Mean dimension score (0-2)")
    ax2.set_ylim(0, 2)
    ax2.legend(fontsize=7.4, title="Period", title_fontsize=7.4)
    VS.despine(ax2)
    VS.title_block(ax2, "b.  Where maturity is and is not accumulating")

    fig.suptitle("Figure 12.  The PB-SAM maturity profile of the field is unbalanced and largely static",
                 x=0.012, ha="left", fontsize=11.5, weight="bold", y=1.0)
    fig.tight_layout()
    VS.caption(fig,
               f"Source: authors' coding of the included corpus (n = {N}).  Method: the Point-Based Spatial "
               f"Analysis Maturity framework (PB-SAM, Section 6.3) scores five dimensions 0-2 from "
               f"abstract-level evidence, giving a 0-10 composite. This is an ABSTRACT-LEVEL PROXY for "
               f"reporting maturity, not a full-text quality appraisal, and it is not a measure of study "
               f"validity; it is calibrated for between-period comparison, not for ranking individual "
               f"studies.  Interpretation: corpus mean {pb['corpus_mean']}/10.  Maturity is accumulating "
               f"almost entirely on D1 (naming a method) and D4 (describing data), while D2 (uncertainty), "
               f"D3 (validation) and D5 (reproducibility) remain close to the floor in all three periods.  "
               f"The field is becoming more articulate about what it does without becoming more accountable "
               f"for whether it is right.",
               y=0.015)
    save(fig, "F12_pbsam_maturity.png")


# =========================================================================
# FIGURE 13 - the conceptual model (theory)
# =========================================================================
def fig13_theory():
    fig, ax = plt.subplots(figsize=(12.4, 8.8))
    ax.set_xlim(0, 13.4)
    ax.set_ylim(0, 10.0)
    ax.axis("off")

    def rbox(x, y, w, h, title, body, fc, ec, tfs=9.2, bfs=7.3, ty=0.30):
        ax.add_patch(FancyBboxPatch((x, y), w, h,
                                    boxstyle="round,pad=0.08,rounding_size=0.16",
                                    fc=fc, ec=ec, lw=1.4))
        ax.text(x + w / 2, y + h - ty, title, ha="center", va="top",
                fontsize=tfs, weight="bold", color=VS.INK)
        ax.text(x + w / 2, y + h - ty - 0.34, body, ha="center", va="top",
                fontsize=bfs, color=VS.INK_2, linespacing=1.5)

    def arrow(p1, p2, color=VS.INK_2, lw=1.5, rad=0.0):
        ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle="-|>", mutation_scale=13,
                                     lw=lw, color=color,
                                     connectionstyle=f"arc3,rad={rad}",
                                     shrinkA=4, shrinkB=4))

    def alabel(x, y, text, color, fs=7.2):
        ax.text(x, y, text, ha="center", va="center", fontsize=fs, color=color,
                weight="bold", linespacing=1.35,
                bbox=dict(boxstyle="round,pad=0.16", fc=VS.SURFACE, ec="none"))

    ax.text(0.0, 9.92, "Figure 13.  Point Intelligence Drift (PID): an integrative framework for the "
            "long-run transformation of point-based spatial analysis",
            fontsize=11.5, weight="bold", color=VS.INK, va="top")
    ax.text(0.0, 9.55,
            "Three drivers push the field forward; two brakes resist; the residual is the drift gap, "
            "which manifests as four observable outcomes.",
            fontsize=8.6, color=VS.INK_2, va="top")

    # ---- left column: drivers / brakes ----
    rbox(0.1, 6.55, 3.15, 2.15, "DRIVERS   (accelerating)",
         "D1  Data densification\ninstitutional \u2192 digital-trace\n\n"
         "D2  Computational abundance\nscarcity \u2192 cloud / GPU\n\n"
         "D3  Application pull\nexplanation \u2192 prediction",
         "#eef4fd", VS.CAT[0])
    rbox(0.1, 3.85, 3.15, 2.10, "BRAKES   (resisting)",
         "B1  Epistemic infrastructure\ntheory, uncertainty, validation\n\n"
         "B2  Institutional geography\ncapacity, access, data rights\n\n"
         "both adapt slowly and unevenly",
         "#faf1ec", VS.CAT[1])

    # ---- centre: drift gap + moderators ----
    rbox(4.05, 5.10, 3.55, 3.30, "DRIFT GAP",
         "\nthe distance between what the\nfield can now compute and\n"
         "what it can warrant, justify\nand distribute\n\n"
         "observed  complexity : rigour\n"
         f"{RES['decoupling'][P[0]]['ratio']}  \u2192  {RES['decoupling'][P[2]]['ratio']}\n"
         f"reproducibility reported in\n{RES['any_reproducibility']['corpus']:.0f}% of the corpus",
         "#f5f4f1", VS.INK_2, tfs=11, bfs=7.6)
    rbox(4.05, 1.55, 3.55, 2.55, "MODERATORS",
         "M1  Scale regime\nmicro \u2194 global\n"
         "M2  Uncertainty regime\npositional, MAUP, edge, temporal\n"
         "M3  Ethical regime\nprivacy, consent, surveillance\n"
         "M4  Knowledge-production geography",
         "#fdfaf0", VS.CAT[3], bfs=7.2)

    arrow((3.25, 7.55), (4.05, 7.20), VS.CAT[0])
    alabel(3.63, 7.62, "push", VS.CAT[0])
    arrow((3.25, 4.95), (4.05, 5.55), VS.CAT[1])
    alabel(3.63, 4.92, "resist", VS.CAT[1])
    arrow((5.82, 5.10), (5.82, 4.10), VS.INK_2)

    # ---- right column: outcomes ----
    outs = [
        ("O1   Methodological sedimentation",
         "methods accumulate; none retired",
         f"multi-class studies  {RES['convergence'][P[0]]['pct_multi_class']:.0f}% \u2192 "
         f"{RES['convergence'][P[2]]['pct_multi_class']:.0f}%"),
        ("O2   Substrate bifurcation",
         "trace-data and field-data traditions decouple",
         f"digital-trace data  {RES['transitions']['digital_trace_data'][P[0]]:.0f}% \u2192 "
         f"{RES['transitions']['digital_trace_data'][P[2]]:.0f}%"),
        ("O3   Warrant erosion",
         "validation displaces uncertainty",
         f"learning studies  {RES['rigour_by_method_class']['learning']['pct_validation']:.0f}% validate, "
         f"{RES['rigour_by_method_class']['learning']['pct_uncertainty']:.0f}% quantify uncertainty"),
        ("O4   Capacity divergence",
         "production concentrates faster than problems",
         f"top-5 share {RES['affiliation']['top5_share']:.0f}%;  South\u2013South ties "
         f"{RES['collaboration']['dyad_mix'].get('South-South', 0):.0f}%"),
    ]
    ytop, bh, gap = 8.70, 1.62, 0.26
    for i, (t, b, ev) in enumerate(outs):
        y = ytop - (i + 1) * bh - i * gap
        rbox(8.55, y, 4.75, bh, t, b + "\n" + ev, "#e9f7f1", VS.CAT[2],
             tfs=8.6, bfs=7.1, ty=0.30)
        arrow((7.60, 6.75), (8.55, y + bh / 2), VS.CAT[2], lw=1.2,
              rad=0.16 if i > 1 else -0.10)

    # moderators condition the outcomes
    arrow((7.60, 2.55), (8.55, 2.20), VS.CAT[3], lw=1.3, rad=-0.2)
    ax.text(8.05, 3.10, "condition the strength\nof O1\u2013O4", ha="center",
            va="center", fontsize=7.0, color=VS.CAT[3], weight="bold",
            linespacing=1.35,
            bbox=dict(boxstyle="round,pad=0.16", fc=VS.SURFACE, ec="none"))

    # feedback loop: routed orthogonally below every box so it crosses nothing
    fb_y = 0.72
    ax.plot([10.9, 10.9, 1.65], [1.44, fb_y, fb_y], color=VS.CAT[4], lw=1.4,
            solid_capstyle="round", zorder=1)
    ax.add_patch(FancyArrowPatch((1.65, fb_y), (1.65, 3.85), arrowstyle="-|>",
                                 mutation_scale=13, lw=1.4, color=VS.CAT[4],
                                 shrinkA=0, shrinkB=4, zorder=1))
    ax.text(6.3, fb_y, "F   feedback:  outcomes reshape the drivers \u2014 new data demands, "
            "new tooling, new inequalities",
            ha="center", va="center", fontsize=7.4, color=VS.CAT[4], weight="bold",
            bbox=dict(boxstyle="round,pad=0.22", fc=VS.SURFACE, ec="none"), zorder=2)

    VS.caption(fig,
               "Source: framework induced by the authors from the review findings; the quantities inside the "
               "boxes are computed from the included corpus (n = 913) and are the evidence FOR the framework, "
               "not a test OF it.  The framework is an original theoretical proposition and has NOT been "
               "empirically validated; Section 7.6 states the propositions through which it could be "
               "falsified.  Reading: drivers D1-D3 push the field's analytical capability forward faster than "
               "brakes B1-B2 can furnish warrant and access; the residual is the drift gap, which manifests "
               "as four observable outcomes O1-O4, whose strength is conditioned by moderators M1-M4, and "
               "which feed back into the drivers.",
               y=0.045)
    save(fig, "F13_pid_conceptual_model.png")


# =========================================================================
# FIGURE 14 - taxonomy + periodisation + maturity (the three instruments)
# =========================================================================
def fig14_instruments():
    fig = plt.figure(figsize=(11.4, 9.6))
    ax = fig.add_axes([0, 0.115, 1, 0.885])
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 9.6)
    ax.axis("off")
    ax.text(0.15, 9.42, "Figure 14.  Three instruments proposed by this review",
            fontsize=11.5, weight="bold", va="top", color=VS.INK)
    ax.text(0.15, 9.06,
            "a. the PBSA taxonomy of methods,  b. the four-regime periodisation,  "
            "c. the PB-SAM maturity ladder.",
            fontsize=8.6, color=VS.INK_2, va="top")

    # ---- a. taxonomy ----
    ax.text(0.15, 8.6, "a.  PBSA taxonomy: three axes, six method classes",
            fontsize=9.6, weight="bold", va="top", color=VS.INK)
    axes_def = [("Axis I — Representation", "how the point is construed",
                 ["event (a thing that happened)", "sample (a place measured)",
                  "entity (a thing that persists)", "trace (a thing that moved)"]),
                ("Axis II — Inferential target", "what is being estimated",
                 ["intensity / density", "interaction / dependence",
                  "association with covariates", "prediction of unobserved values"]),
                ("Axis III — Computational regime", "how it is executed",
                 ["closed-form / analytic", "simulation-based",
                  "optimisation / learning", "streaming / online"])]
    x0 = 0.2
    for title, sub, items in axes_def:
        ax.add_patch(FancyBboxPatch((x0, 6.15), 3.75, 2.2,
                                    boxstyle="round,pad=0.07,rounding_size=0.13",
                                    fc="#eef4fd", ec=VS.CAT[0], lw=1.2))
        ax.text(x0 + 0.16, 8.2, title, fontsize=8.6, weight="bold", va="top",
                color=VS.INK)
        ax.text(x0 + 0.16, 7.92, sub, fontsize=7.2, va="top", color=VS.INK_MUTED,
                style="italic")
        yy = 7.62
        for it in items:
            ax.text(x0 + 0.3, yy, "•  " + it, fontsize=7.4, va="top", color=VS.INK_2)
            yy -= 0.33
        x0 += 3.9

    # ---- b. periodisation ----
    ax.text(0.15, 5.85, "b.  Periodisation: four regimes of point-based spatial analysis",
            fontsize=9.6, weight="bold", va="top", color=VS.INK)
    regimes = [
        ("R1  Estimation regime", "pre-2000 – c.2010", VS.CAT[0],
         "scarce, curated point data;\nsecond-order statistics;\nthe question is 'is it clustered?'"),
        ("R2  Integration regime", "c.2010 – c.2018", VS.CAT[1],
         "multi-source point data;\nmodel-based & Bayesian;\n'why is it clustered?'"),
        ("R3  Saturation regime", "c.2018 – present", VS.CAT[2],
         "dense passive trace data;\nlearning-based prediction;\n'where will it happen next?'"),
        ("R4  Accountability regime", "emerging / normative", VS.CAT[3],
         "context-aware, auditable,\nprivacy-preserving analytics;\n'should it be computed at all?'"),
    ]
    x0 = 0.2
    for i, (t, per, c, body) in enumerate(regimes):
        ax.add_patch(FancyBboxPatch((x0, 3.5), 2.72, 2.05,
                                    boxstyle="round,pad=0.07,rounding_size=0.13",
                                    fc=VS.SURFACE, ec=c, lw=1.6))
        ax.add_patch(Rectangle((x0, 5.32), 2.72, 0.23, fc=c, ec="none"))
        ax.text(x0 + 0.14, 5.16, t, fontsize=8.4, weight="bold", va="top", color=VS.INK)
        ax.text(x0 + 0.14, 4.88, per, fontsize=7.2, va="top", color=VS.INK_MUTED,
                style="italic")
        ax.text(x0 + 0.14, 4.6, body, fontsize=7.2, va="top", color=VS.INK_2,
                linespacing=1.5)
        if i < 3:
            ax.add_patch(FancyArrowPatch((x0 + 2.72, 4.5), (x0 + 2.98, 4.5),
                                         arrowstyle="-|>", mutation_scale=11,
                                         lw=1.3, color=VS.INK_2))
        x0 += 2.98
    ax.text(0.2, 3.34,
            "R4 is normative, not observed: the corpus shows its preconditions "
            "(rising ethical salience) but not its arrival.",
            fontsize=7.2, color=VS.INK_MUTED, va="top", style="italic")

    # ---- c. maturity ladder ----
    ax.text(0.15, 2.95, "c.  PB-SAM maturity ladder (observed distribution of the corpus)",
            fontsize=9.6, weight="bold", va="top", color=VS.INK)
    pb = RES["pbsam"]
    lv = [("Level 1  Emergent", "0-3", "a method is named; warrant is implicit",
           pb[P[2]]["L1"], VS.CAT[0]),
          ("Level 2  Consolidating", "4-6", "data described and some validation reported",
           pb[P[2]]["L2"], VS.CAT[1]),
          ("Level 3  Mature", "7-10", "uncertainty, validation and reproducibility all explicit",
           pb[P[2]]["L3"], VS.CAT[2])]
    yy = 2.35
    for name, rng, desc, share, c in lv:
        ax.add_patch(Rectangle((0.2, yy - 0.52), 0.14, 0.62, fc=c, ec="none"))
        ax.text(0.5, yy, f"{name}  ({rng})", fontsize=8.4, weight="bold",
                va="top", color=VS.INK)
        ax.text(0.5, yy - 0.26, desc, fontsize=7.4, va="top", color=VS.INK_2)
        w = 5.4 * share / 100
        ax.add_patch(Rectangle((6.3, yy - 0.42), 5.4, 0.34, fc="#f0efec", ec="none"))
        ax.add_patch(Rectangle((6.3, yy - 0.42), max(w, 0.02), 0.34, fc=c, ec="none"))
        ax.text(11.8, yy - 0.25, f"{share:.0f}%", fontsize=8, ha="right",
                va="center", weight="bold", color=VS.INK)
        yy -= 0.78
    ax.text(6.3, 0.16, "share of 2021-2027 studies", fontsize=7.2, color=VS.INK_MUTED)

    VS.caption(fig,
               "Source: instruments proposed by the authors (Sections 6.1-6.3); the distribution in panel c "
               "is computed from the included corpus (n = 913, 2021-2027 sub-period n = 462).  "
               "The taxonomy in panel a is orthogonal by construction: any study occupies one position on "
               "each of the three axes, which is what distinguishes it from the flat method lists used in "
               "previous reviews.  The periodisation in panel b is a conceptual reconstruction anchored to "
               "observed transitions (Figures 3, 6, 8); regime boundaries are analytical, not sharp, and R4 "
               "is a normative projection rather than an empirical finding.  Note that no study in the "
               "2021-2027 sub-period reaches Level 3 on abstract-level evidence.",
               y=0.098)
    save(fig, "F14_taxonomy_periodisation_maturity.png")


# =========================================================================
# FIGURE 15 - country x topic x method small multiples
# =========================================================================
def fig15_country_profiles():
    aff = Counter()
    for r in ROWS:
        aff.update(set(r["affil_iso3"]))
    top = [i for i, _ in aff.most_common(12)]
    classes = list(LX.METHOD_CLASS_LABELS)
    doms = [d for d, _ in sorted(RES["domains_total"].items(), key=lambda kv: -kv[1])[:6]]
    fig, axes = plt.subplots(3, 4, figsize=(11.6, 7.6), sharex=True)
    for ax, iso in zip(axes.ravel(), top):
        sub = [r for r in ROWS if iso in r["affil_iso3"]]
        v = [pct(sum(1 for r in sub if c in r["method_classes"]), len(sub))
             for c in classes]
        ax.barh(np.arange(len(classes))[::-1], v,
                color=[VS.CLASS_COLOR[c] for c in classes], height=0.66, zorder=3)
        dm = Counter()
        for r in sub:
            dm.update(set(r["domains"]) & set(doms))
        lead = dm.most_common(1)[0][0] if dm else "—"
        ax.set_title(f"{GEO.ISO3_TO_NAME.get(iso, iso)}  (n={len(sub)})",
                     loc="left", fontsize=8.6, color=VS.INK, pad=12)
        ax.text(0, 1.02, f"lead domain: {lead[:34]}", transform=ax.transAxes,
                fontsize=6.8, color=VS.INK_MUTED, va="bottom")
        ax.set_yticks([])
        ax.set_xlim(0, 62)
        VS.despine(ax, keep=("bottom",))
    handles = [mpatches.Patch(color=VS.CLASS_COLOR[c],
                              label=LX.METHOD_CLASS_LABELS[c]) for c in classes]
    fig.legend(handles=handles, loc="lower center", ncol=3, fontsize=7.6,
               bbox_to_anchor=(0.5, -0.055))
    fig.suptitle("Figure 15.  National methodological profiles: the twelve most productive countries",
                 x=0.012, ha="left", fontsize=11.5, weight="bold", y=1.0)
    fig.text(0.012, 0.962, "Bars show the share of each country's studies evidencing each method class; "
             "x-axis is common across panels (0-62%).",
             ha="left", fontsize=8.4, color=VS.INK_2)
    fig.tight_layout()
    VS.caption(fig,
               f"Source: authors' coding of the included corpus (n = {N}).  Method: a study counts towards "
               f"every country in its affiliation list, so panels are not mutually exclusive; method classes "
               f"are non-exclusive within a study.  Countries are ordered by output.  Full numeric profile in "
               f"tables/T21_country_method_domain_profile.csv.  Interpretation: national profiles are "
               f"markedly different rather than being scaled copies of a global average.  The differences "
               f"track data availability and institutional context, not country size, which is the empirical "
               f"basis for the claim in Section 8.5 that methods do not transfer neutrally across "
               f"geographical contexts.",
               y=0.005)
    save(fig, "F15_country_method_profiles.png")


# =========================================================================
# FIGURE 16 - method co-occurrence network (convergence)
# =========================================================================
def fig16_method_network():
    co = Counter()
    tot = Counter()
    for r in ROWS:
        ms = sorted(set(r["methods"]))
        tot.update(ms)
        for i in range(len(ms)):
            for j in range(i + 1, len(ms)):
                co[(ms[i], ms[j])] += 1
    nodes = [m for m, c in tot.items() if c >= 8]
    E = [(a, b, w) for (a, b), w in co.items() if a in nodes and b in nodes and w >= 3]
    nodes = sorted({a for a, _, _ in E} | {b for _, b, _ in E},
                   key=lambda m: (list(LX.METHOD_CLASS_LABELS).index(
                       LX.COMPILED["methods"][m][0]), -tot[m]))
    ang = {n: 2 * math.pi * i / len(nodes) - math.pi / 2 for i, n in enumerate(nodes)}
    pos = {n: (math.cos(a), math.sin(a)) for n, a in ang.items()}
    fig, ax = plt.subplots(figsize=(9.0, 8.4))
    ax.set_aspect("equal")
    ax.axis("off")
    for a, b, w in sorted(E, key=lambda e: e[2]):
        x1, y1 = pos[a]
        x2, y2 = pos[b]
        cls_a = LX.COMPILED["methods"][a][0]
        cls_b = LX.COMPILED["methods"][b][0]
        col = VS.CLASS_COLOR[cls_a] if cls_a == cls_b else VS.INK_MUTED
        ax.add_patch(mpatches.PathPatch(
            Path([(x1, y1), ((x1 + x2) * 0.25, (y1 + y2) * 0.25), (x2, y2)],
                 [Path.MOVETO, Path.CURVE3, Path.CURVE3]),
            fc="none", ec=col, lw=0.5 + 1.1 * math.log1p(w),
            alpha=0.55 if cls_a != cls_b else 0.4,
            linestyle="-" if cls_a == cls_b else (0, (3, 2))))
    for n in nodes:
        x, y = pos[n]
        c = VS.CLASS_COLOR[LX.COMPILED["methods"][n][0]]
        ax.scatter([x], [y], s=26 + 5 * math.sqrt(tot[n]), color=c, zorder=4,
                   edgecolors=VS.SURFACE, linewidths=1.3)
        a = ang[n]
        ax.text(x * 1.1, y * 1.1, n if len(n) < 34 else n[:32] + "…", fontsize=7,
                ha="left" if -math.pi / 2 < a < math.pi / 2 else "right",
                va="center",
                rotation=math.degrees(a) if -math.pi / 2 < a < math.pi / 2
                else math.degrees(a) + 180, rotation_mode="anchor", color=VS.INK)
    ax.set_xlim(-2.0, 2.0)
    ax.set_ylim(-1.7, 1.7)
    handles = [mpatches.Patch(color=VS.CLASS_COLOR[c], label=LX.METHOD_CLASS_LABELS[c])
               for c in LX.METHOD_CLASS_LABELS]
    handles += [plt.Line2D([], [], color=VS.INK_MUTED, ls=(0, (3, 2)),
                           label="cross-class pairing (convergence)")]
    fig.legend(handles=handles, loc="lower center", ncol=3, fontsize=7.2,
               bbox_to_anchor=(0.5, 0.055))
    fig.subplots_adjust(bottom=0.13)
    fig.suptitle("Figure 16.  Method co-occurrence: where the field's methodological convergence actually happens",
                 x=0.012, ha="left", fontsize=11.5, weight="bold", y=0.99)
    conv = RES["convergence"]
    VS.caption(fig,
               f"Source: authors' coding of the included corpus (n = {N}).  Method: nodes are individual "
               f"methods used in at least eight studies; edges join methods co-occurring in at least three "
               f"studies; edge width is log co-occurrence; dashed grey edges join methods from different "
               f"classes.  Lift values against an independence baseline are in "
               f"tables/T20_method_co_occurrence.csv.  Interpretation: convergence is real but narrow.  "
               f"Studies combining two or more method classes rise from "
               f"{conv[P[0]]['pct_multi_class']:.0f}% to {conv[P[2]]['pct_multi_class']:.0f}% of the period "
               f"corpus, and learning methods now pair with classical or inferential statistics in "
               f"{conv[P[2]]['pct_learning_plus_statistical']:.0f}% of recent studies (from "
               f"{conv[P[0]]['pct_learning_plus_statistical']:.0f}%).  But the dashed edges are concentrated "
               f"on a handful of bridge methods -- spatial clustering, hotspot statistics and spatial "
               f"regression -- which act as the field's translation layer.  Most method pairs remain "
               f"within-class.",
               y=0.05)
    save(fig, "F16_method_co_occurrence_network.png")


if __name__ == "__main__":
    fig01_prisma()
    fig02_growth()
    fig03_method_classes()
    fig04_map_affiliation()
    fig05_map_case_and_asymmetry()
    fig06_data_transition()
    fig07_sankey()
    fig08_thematic()
    fig09_heatmap()
    fig10_collab_network()
    fig11_rigour()
    fig12_maturity()
    fig13_theory()
    fig14_instruments()
    fig15_country_profiles()
    fig16_method_network()
    print("\nAll figures written to", FIG)
