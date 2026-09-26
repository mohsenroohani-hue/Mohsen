"""Workflow diagram: analysis stages and the QGIS / ArcGIS Pro / GeoDa / R-Python tool used."""
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

import viz as V

SW = {"QGIS": V.CAT[2], "ArcGIS Pro": V.CAT[0], "GeoDa": V.CAT[1], "R / Python": V.CAT[6]}
stages = [
    ("1  Data preparation", "WKT → GeoPackage; site points & lines;\nexposure (MEV, 100 MVMT); 19 land-use counts",
     [("QGIS", "Add Delimited Text Layer (WKT)"), ("ArcGIS Pro", "Add GPKG layer; Spatial Join"), ("GeoDa", "File > Open (GPKG)")]),
    ("2  Rates & spatial weights", "Empirical-Bayes rates; k-NN (k = 6) weights;\npeak clustering distance",
     [("GeoDa", "Rates-Calculated Map; Weights Manager"), ("ArcGIS Pro", "Incremental Spatial Autocorrelation"), ("R / Python", "esda / spdep")]),
    ("3  ESDA: where does risk cluster?", "EB Moran's I, LISA, Gi*, local join count\n(fatal), bivariate Moran for each land use",
     [("GeoDa", "Moran's I (EB), LISA, Local G*, LJC"), ("ArcGIS Pro", "Hot Spot Analysis; Cluster & Outlier"), ("QGIS", "Hotspot Analysis plugin (PySAL)")]),
    ("4  Land-use context typology", "K-means on 7 land-use families\n→ 5 corridor contexts; crash profiles",
     [("GeoDa", "Clusters > K Means (or SKATER)"), ("ArcGIS Pro", "Multivariate Clustering"), ("QGIS", "Python console (core K-means clusters by location only)")]),
    ("5  Count models (core inference)", "NB2 / Firth Poisson × 13 crash types × 4 severities;\neach land use & joint; spatial filter; FDR",
     [("R / Python", "statsmodels / MASS::glm.nb (scripts here)"), ("ArcGIS Pro", "Generalized Linear Regression, Count – screening")]),
    ("6  Spatial heterogeneity", "MGWR on ln(EB rate): one bandwidth per\nland use → local vs. global effects",
     [("ArcGIS Pro", "Multiscale Geographically Weighted Regression"), ("R / Python", "mgwr / MGWR 2.2 desktop")]),
    ("7  Mapping & reporting", "LISA, Gi*, typology and MGWR maps;\nIRR heat maps; land-use atlas",
     [("QGIS", "Categorized styles; Print Layout"), ("ArcGIS Pro", "Layouts; Charts")]),
]
n = len(stages)
fig, ax = plt.subplots(figsize=(7.4, 7.0))
ax.set_xlim(0, 100)
ax.set_ylim(0, n * 14 + 6)
ax.axis("off")
for i, (title, body, tools) in enumerate(stages):
    y = (n - 1 - i) * 14 + 7
    core = title.startswith("5")
    ax.add_patch(FancyBboxPatch((1, y), 98, 11.5, boxstyle="round,pad=0.3,rounding_size=1.0",
                                facecolor="#eef4fc" if core else V.SURFACE,
                                edgecolor=V.CAT[0] if core else V.AXIS, lw=1.4 if core else 0.7))
    ax.text(2.5, y + 8.6, title, fontsize=7.6, fontweight="bold", color=V.INK, va="center")
    ax.text(2.5, y + 3.6, body, fontsize=6.3, color=V.INK2, va="center", linespacing=1.35)
    for k, (sw, tl) in enumerate(tools):
        yy = y + 9.2 - k * 3.4
        ax.add_patch(FancyBboxPatch((51, yy - 1.1), 1.8, 2.2, boxstyle="round,pad=0.1",
                                    facecolor=SW[sw], edgecolor="none"))
        ax.text(54, yy, f"{sw}: {tl}", fontsize=6.1, color=V.INK, va="center")
    if i < n - 1:
        ax.add_patch(FancyArrowPatch((12, y - 0.1), (12, y - 2.2), arrowstyle="-|>", color=V.INK2,
                                     lw=1.0, mutation_scale=8))
for k, (sw, c) in enumerate(SW.items()):
    ax.add_patch(FancyBboxPatch((2 + k * 24, 1.5), 1.8, 2.2, boxstyle="round,pad=0.1", facecolor=c, edgecolor="none"))
    ax.text(5 + k * 24, 2.6, sw, fontsize=7, color=V.INK, va="center")
V.savefig(fig, "fig00_workflow.png")
print("diagram done")
