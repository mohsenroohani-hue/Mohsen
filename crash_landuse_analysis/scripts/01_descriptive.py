"""Study-area maps, crash composition, land-use prevalence and collinearity."""
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

import common as C
import viz as V

G = {f: C.load(f) for f in ("int", "seg")}
allsites = pd.concat([G["int"][["COUNTY", "geometry"]], G["seg"][["COUNTY", "geometry"]]])
BOUNDS = V.region_bounds(gpd.GeoDataFrame(allsites, geometry="geometry", crs=C.CRS))
pd.to_pickle(BOUNDS, C.OUT / "region_bounds.pkl")

# ---------------------------------------------------------------- Fig 1: study area
gi, gs = G["int"], G["seg"]
fig, axes, lax = V.region_axes()
for reg, ax in axes.items():
    V.draw_base(ax, reg, BOUNDS)
    s = gs[gs["region"] == reg]
    s.plot(ax=ax, color=V.MUTED, linewidth=1.5, zorder=3)
    p = gi[gi["region"] == reg]
    ax.scatter(p["pt"].x, p["pt"].y, s=np.sqrt(p["CR_ALL"]) * 1.1, color=V.CAT[0],
               edgecolor="white", linewidth=0.4, alpha=0.9, zorder=4)
    V.label_routes(ax, s)
h = [Line2D([0], [0], color=V.MUTED, lw=1.5, label="Study segment (n = 334)")]
for v in (25, 100, 400):
    h.append(Line2D([0], [0], marker="o", color="none", markerfacecolor=V.CAT[0],
                    markeredgecolor="white", markersize=np.sqrt(np.sqrt(v) * 1.1),
                    label=f"Intersection: {v} crashes"))
lax.legend(handles=h, loc="upper left", fontsize=7, title="Study sites (4-yr crashes)",
           title_fontsize=7.5, alignment="left")
ins = lax.inset_axes([0.05, 0.0, 0.75, 0.52])
cty = V.counties()
cty.plot(ax=ins, color="#e4e3dd", edgecolor="white", linewidth=0.2)
cty[cty["id"].isin(C.COUNTY_FIPS.values())].plot(ax=ins, color=V.CAT[0])
ins.set_axis_off()
ins.set_title("Study counties", fontsize=6.5, color=V.INK2, pad=1)
V.savefig(fig, "fig01_study_area.png")

# ---------------------------------------------------------------- Fig 2: KSI maps
labs_i = ["0", "1–2", "3–4", "5+"]
cols4 = [V.BLUE[1], V.BLUE[4], V.BLUE[8], V.BLUE[12]]
gi["ksi_cls"] = pd.cut(gi["y_ALL_KSI"], [0, 1, 3, 5, 100], right=False, labels=labs_i)
V.region_map(gi, "ksi_cls", dict(zip(labs_i, cols4)), "point", "fig02a_ksi_intersections.png",
             "KSI crashes per intersection\n(4 years; count of sites)", size=12)
gs["ksi_rate"] = gs["y_ALL_KSI"] / gs["exposure"]
nz = gs.loc[gs["ksi_rate"] > 0, "ksi_rate"]
q1, q2 = nz.quantile([1 / 3, 2 / 3]).values
labs_s = ["0", f"0.1–{q1:.1f}", f"{q1:.1f}–{q2:.1f}", f">{q2:.1f}"]
gs["ksi_cls"] = pd.cut(gs["ksi_rate"], [-1, 1e-9, q1, q2, 1e9], labels=labs_s)
V.region_map(gs, "ksi_cls", dict(zip(labs_s, cols4)), "line", "fig02b_ksi_segments.png",
             "KSI crashes per 100 million VMT\n(non-zero values in terciles)")

# ---------------------------------------------------------------- Table: crash counts
rows = []
for f in ("int", "seg"):
    g = G[f]
    for t, lab in C.CRASH_TYPES.items():
        r = {"Facility": C.FACILITY_LABEL[f], "Crash type": lab}
        for s in C.SEVERITIES:
            r[C.SEV_LABEL[s]] = int(g[f"y_{t}_{s}"].sum())
        r["Sites with ≥1 KSI"] = int((g[f"y_{t}_KSI"] > 0).sum())
        r["KSI per 100 crashes"] = 100 * r["KSI"] / max(r["Total"], 1)
        r["Fatal per 1,000 crashes"] = 1000 * r["Fatal"] / max(r["Total"], 1)
        rows.append(r)
tab = pd.DataFrame(rows)
tab.to_csv(C.TAB / "t_crash_counts.csv", index=False)

# ---------------------------------------------------------------- Fig 3: severity propensity
types = [t for t in C.CRASH_TYPES if t != "ALL"]
fig, axs = plt.subplots(1, 2, figsize=(7.2, 3.4), sharey=True)
order = tab[(tab.Facility == "Intersections") & (tab["Crash type"] != "All crash types")] \
    .sort_values("KSI per 100 crashes")["Crash type"].tolist()
for ax, col, ttl in zip(axs, ["KSI per 100 crashes", "Fatal per 1,000 crashes"],
                        ["(a) KSI crashes per 100 crashes", "(b) Fatal crashes per 1,000 crashes"]):
    for k, f in enumerate(["Intersections", "Segments"]):
        sub = tab[tab.Facility == f].set_index("Crash type").loc[order]
        y = np.arange(len(order)) + (k - 0.5) * 0.28
        ax.hlines(y, 0, sub[col], color=V.GRID, lw=0.8)
        ax.scatter(sub[col], y, color=V.CAT[k], s=22, zorder=3, label=f,
                   edgecolor="white", linewidth=0.5)
    ax.set_yticks(np.arange(len(order)))
    ax.set_yticklabels(order)
    ax.set_title(ttl, loc="left")
    ax.grid(axis="x")
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
axs[0].legend(loc="lower right")
fig.tight_layout()
V.savefig(fig, "fig03_severity_propensity.png")

# ---------------------------------------------------------------- Fig 4: land-use prevalence
lus = list(C.LAND_USES)
prev = pd.DataFrame({C.FACILITY_LABEL[f]: (G[f][lus] > 0).mean() * 100 for f in G})
prev.index = [C.LAND_USES[l] for l in lus]
prev = prev.sort_values("Segments")
fig, ax = plt.subplots(figsize=(7.2, 4.4))
y = np.arange(len(prev))
for k, f in enumerate(["Intersections", "Segments"]):
    ax.barh(y + (k - 0.5) * 0.38, prev[f], height=0.36, color=V.CAT[k], label=f)
ax.set_yticks(y)
ax.set_yticklabels(prev.index)
ax.set_xlabel("Share of sites with at least one establishment (%)")
ax.grid(axis="x")
ax.set_axisbelow(True)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.axvline(5, color=V.MUTED, lw=0.8)
ax.text(5.5, -0.9, "5% — below this, estimates are imprecise", fontsize=6.5, color=V.INK2)
ax.legend(loc="lower right")
fig.tight_layout()
V.savefig(fig, "fig04_landuse_prevalence.png")
prev.round(1).to_csv(C.TAB / "t_landuse_prevalence.csv")

# ---------------------------------------------------------------- Fig 5: correlation
fig, axs = plt.subplots(1, 2, figsize=(7.4, 3.9))
for ax, f in zip(axs, ("int", "seg")):
    cm = G[f][["x_" + l for l in lus]].corr(method="spearman").to_numpy(copy=True)
    np.fill_diagonal(cm, np.nan)
    im = ax.imshow(cm, cmap=V.DIVERGING, vmin=-0.6, vmax=0.6)
    ax.set_xticks(range(len(lus)))
    ax.set_yticks(range(len(lus)))
    ax.set_xticklabels([C.LU_SHORT[l] for l in lus], rotation=90, fontsize=6)
    ax.set_yticklabels([C.LU_SHORT[l] for l in lus] if f == "int" else [], fontsize=6)
    ax.set_title(C.FACILITY_LABEL[f])
    for i in range(len(lus)):
        for j in range(len(lus)):
            if i != j and abs(cm[i, j]) >= 0.4:
                ax.text(j, i, f"{cm[i, j]:.1f}", ha="center", va="center", fontsize=4.8,
                        color="white" if abs(cm[i, j]) > 0.5 else V.INK)
cb = fig.colorbar(im, ax=axs, shrink=0.6, pad=0.02)
cb.set_label("Spearman ρ", fontsize=7)
cb.ax.tick_params(labelsize=6.5)
V.savefig(fig, "fig05_landuse_correlation.png")

# ---------------------------------------------------------------- Table: descriptives
desc = []
vars_ = [("aadt", "AADT (major road)"), ("lanes", "Through lanes (total)"),
         ("RN_MAXSPEED_AVG", "Posted speed (mph)"), ("raised_median", "Raised median (share)"),
         ("RN_SHLDO_AV_TWIDTH", "Outside shoulder width (ft)"), ("bikelane", "Bike lane >50% (share)"),
         ("busstops", "Bus stops"), ("CN_POPDEN_SQMI", "Population density (per sq mi)"),
         ("CN_MED_HH_INC", "Median household income ($)")]
for v, lab in vars_:
    r = {"Variable": lab}
    for f in ("int", "seg"):
        r[f"{C.FACILITY_LABEL[f]} mean"] = G[f][v].mean()
        r[f"{C.FACILITY_LABEL[f]} SD"] = G[f][v].std()
    desc.append(r)
r = {"Variable": "Segment length (mi)", "Intersections mean": np.nan, "Intersections SD": np.nan,
     "Segments mean": G["seg"]["SEGLENGTH"].mean(), "Segments SD": G["seg"]["SEGLENGTH"].std()}
desc.append(r)
for l in lus:
    r = {"Variable": C.LAND_USES[l] + " (count)"}
    for f in ("int", "seg"):
        r[f"{C.FACILITY_LABEL[f]} mean"] = G[f][l].mean()
        r[f"{C.FACILITY_LABEL[f]} SD"] = G[f][l].std()
    desc.append(r)
pd.DataFrame(desc).to_csv(C.TAB / "t_descriptives.csv", index=False)
print("done descriptive")
