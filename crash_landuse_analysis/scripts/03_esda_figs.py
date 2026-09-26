"""Figures and maps for the ESDA layer."""
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

import common as C
import viz as V

G = {f: C.load(f) for f in ("int", "seg")}
S = {f: pd.read_pickle(C.OUT / f"esda_sites_{f}.pkl") for f in ("int", "seg")}
for f in G:
    G[f] = G[f].merge(S[f], on="SEGMENTID")
glob = pd.read_csv(C.TAB / "t_global_moran.csv")
inc = pd.read_csv(C.TAB / "t_incremental_moran.csv")
bv = pd.read_csv(C.TAB / "t_bivariate_moran.csv")
types = list(C.CRASH_TYPES)

# ------------------------------------------------------------ global Moran heatmap
fig, axs = plt.subplots(1, 2, figsize=(7.2, 4.3), sharey=True)
for ax, f in zip(axs, ("int", "seg")):
    sub = glob[glob.facility == f]
    M = sub.pivot(index="type", columns="sev", values="I_eb").reindex(index=types, columns=C.SEVERITIES)
    P = sub.pivot(index="type", columns="sev", values="p_eb").reindex(index=types, columns=C.SEVERITIES)
    im = ax.imshow(M.values, cmap=V.DIVERGING, vmin=-0.45, vmax=0.45, aspect="auto")
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            v = M.values[i, j]
            if np.isnan(v):
                ax.text(j, i, "–", ha="center", va="center", fontsize=7, color=V.MUTED)
                continue
            sig = P.values[i, j] < 0.05
            ax.text(j, i, f"{v:.2f}{'*' if sig else ''}", ha="center", va="center", fontsize=6.8,
                    color="white" if v > 0.3 else V.INK, fontweight="bold" if sig else "normal")
    ax.set_xticks(range(4))
    ax.set_xticklabels([C.SEV_LABEL[s] for s in C.SEVERITIES])
    ax.set_yticks(range(len(types)))
    ax.set_yticklabels([C.SHORT_TYPE[t] for t in types])
    ax.set_title(C.FACILITY_LABEL[f])
    ax.tick_params(length=0)
cb = fig.colorbar(im, ax=axs, shrink=0.7, pad=0.02)
cb.set_label("Moran's I (EB-standardised rate)", fontsize=7)
fig.text(0.02, -0.01, "* permutation p < 0.05 (999 permutations); – fewer than 10 crashes; "
         "k = 6 nearest-neighbour weights, row-standardised.", fontsize=6.5, color=V.INK2)
V.savefig(fig, "fig06_global_moran_heatmap.png")

# ------------------------------------------------------------ incremental autocorrelation
fig, axs = plt.subplots(1, 2, figsize=(7.2, 2.9), sharey=True)
series = [("ALL", "TOT", "All crashes – Total"), ("ALL", "KAB", "All crashes – KAB"),
          ("ALL", "KSI", "All crashes – KSI"), ("PED", "KAB", "Pedestrian – KAB")]
cols = [V.BLUE[4], V.BLUE[8], V.BLUE[12], V.CAT[1]]
for ax, f in zip(axs, ("int", "seg")):
    for (t, s, lab), c in zip(series, cols):
        d = inc[(inc.facility == f) & (inc.kind == "band") & (inc.type == t) & (inc.sev == s)]
        ax.plot(d.k_or_km, d.z, color=c, lw=2, marker="o", ms=4, label=lab,
                markeredgecolor="white", markeredgewidth=0.6)
        pk = d.loc[d.z.idxmax()]
        ax.scatter([pk.k_or_km], [pk.z], s=70, facecolor="none", edgecolor=c, lw=1.2, zorder=5)
    ax.axhline(1.96, color=V.MUTED, lw=0.8)
    ax.text(1.0, 2.3, "z = 1.96", fontsize=6.5, color=V.INK2)
    ax.set_xlabel("Distance band (km)")
    ax.set_title(C.FACILITY_LABEL[f], loc="left")
    ax.grid(axis="y")
    ax.set_axisbelow(True)
    for s_ in ("top", "right"):
        ax.spines[s_].set_visible(False)
axs[0].set_ylabel("Moran's I z-score (EB rate)")
axs[1].legend(loc="lower right", fontsize=6.5)
fig.tight_layout()
V.savefig(fig, "fig07_incremental_autocorrelation.png")

# ------------------------------------------------------------ LISA maps
lisa_order = {"Not significant": V.LISA_COLORS["Not significant"], "High-High": V.LISA_COLORS["High-High"],
              "Low-Low": V.LISA_COLORS["Low-Low"], "High-Low": V.LISA_COLORS["High-Low"],
              "Low-High": V.LISA_COLORS["Low-High"]}
gi_order = {k: V.GI_COLORS[k] for k in ["Not significant", "Cold spot 90%", "Cold spot 95%",
                                         "Cold spot 99%", "Hot spot 90%", "Hot spot 95%", "Hot spot 99%"]}
note_l = "Local Moran's I on EB-standardised rates;\nk = 6 neighbours, 999 permutations, p < 0.05."
note_g = "Getis-Ord Gi* on EB-smoothed rates;\nk = 6 binary neighbours (self included)."
maps = []
for t, s in [("ALL", "KSI"), ("ALL", "KAB"), ("ANGLE", "KAB"), ("LEFTTURN", "KAB"),
             ("REAREND", "KAB"), ("OFFROAD", "KAB"), ("PED", "KAB"), ("BIKE", "KAB"),
             ("SIDESWIPE", "KAB"), ("SINGLE", "KAB")]:
    for f in ("int", "seg"):
        kind = "point" if f == "int" else "line"
        nm = f"map_lisa_{f}_{t}_{s}.png"
        V.region_map(G[f], f"lisa_{t}_{s}", lisa_order, kind, nm,
                     f"LISA clusters — {C.CRASH_TYPES[t]}, {C.SEV_LABEL[s]}\n({C.FACILITY_LABEL[f].lower()})",
                     note=note_l)
        if (t, s) in [("ALL", "KSI"), ("ALL", "KAB"), ("PED", "KAB"), ("ANGLE", "KAB"),
                      ("REAREND", "KAB"), ("OFFROAD", "KAB")]:
            V.region_map(G[f], f"gi_{t}_{s}", gi_order, kind, f"map_gi_{f}_{t}_{s}.png",
                         f"Gi* hot/cold spots — {C.CRASH_TYPES[t]}, {C.SEV_LABEL[s]}\n({C.FACILITY_LABEL[f].lower()})",
                         note=note_g)

# ------------------------------------------------------------ local join count (fatal)
ljc_col = {"No event at site": "#d9d9d6", "Event, not clustered": V.CAT[1],
           "Significant cluster": "#9a2323"}
for f in ("int", "seg"):
    V.region_map(G[f], "ljccls_ALL_FAT", ljc_col, "point" if f == "int" else "line",
                 f"map_ljc_{f}_fatal.png",
                 f"Local join count — any fatal crash\n({C.FACILITY_LABEL[f].lower()})",
                 note="Binary: site had ≥1 fatal crash. Cluster =\nfatal site whose neighbours also had\nfatal crashes more often than chance\n(999 permutations, p < 0.05).")

# ------------------------------------------------------------ hot-spot share by corridor x crash type
rows = []
key_types = ["ALL", "ANGLE", "LEFTTURN", "REAREND", "SIDESWIPE", "OFFROAD", "PED", "BIKE",
             "HEADON", "SINGLE", "ALCOHOL"]
for f in ("int", "seg"):
    g = G[f]
    for rg, sub in g.groupby("Route_grp"):
        for t in key_types:
            col = f"gi_{t}_KAB"
            if col in sub:
                rows.append({"facility": f, "route": V.ROUTE_NAME.get(rg, rg), "type": t,
                             "share_hot": 100 * sub[col].str.startswith("Hot spot 9").mean()})
hs = pd.DataFrame(rows)
hs.to_csv(C.TAB / "t_hotspot_share_by_corridor.csv", index=False)
fig, axs = plt.subplots(1, 2, figsize=(7.4, 3.8), sharey=True)
for ax, f in zip(axs, ("int", "seg")):
    M = hs[hs.facility == f].pivot(index="route", columns="type", values="share_hot")[key_types]
    im = ax.imshow(M.values, cmap=V.SEQ_BLUE, vmin=0, vmax=80, aspect="auto")
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            v = M.values[i, j]
            ax.text(j, i, f"{v:.0f}", ha="center", va="center", fontsize=6,
                    color="white" if v > 45 else V.INK)
    ax.set_xticks(range(len(key_types)))
    ax.set_xticklabels([C.SHORT_TYPE[t] for t in key_types], rotation=60, ha="right")
    ax.set_yticks(range(len(M)))
    ax.set_yticklabels(M.index)
    ax.set_title(C.FACILITY_LABEL[f])
    ax.tick_params(length=0)
cb = fig.colorbar(im, ax=axs, shrink=0.7, pad=0.02)
cb.set_label("% of corridor sites in a Gi* hot spot (≥90%)\nKAB crash rate", fontsize=7)
V.savefig(fig, "fig10_hotspot_share_corridor.png")

# ------------------------------------------------------------ bivariate Moran heatmaps (each land use)
lus = list(C.LAND_USES)
for s in C.SEVERITIES:
    fig, axs = plt.subplots(1, 2, figsize=(7.4, 5.0), sharey=True)
    for ax, f in zip(axs, ("int", "seg")):
        sub = bv[(bv.facility == f) & (bv.sev == s)]
        M = sub.pivot(index="lu", columns="type", values="I_bv").reindex(index=lus, columns=types)
        P = sub.pivot(index="lu", columns="type", values="p_bv").reindex(index=lus, columns=types)
        im = ax.imshow(M.values, cmap=V.DIVERGING, vmin=-0.2, vmax=0.2, aspect="auto")
        for i in range(M.shape[0]):
            for j in range(M.shape[1]):
                v = M.values[i, j]
                if np.isnan(v):
                    ax.text(j, i, "–", ha="center", va="center", fontsize=5.5, color=V.MUTED)
                elif P.values[i, j] < 0.05:
                    ax.text(j, i, "●" if v > 0 else "○", ha="center", va="center", fontsize=5,
                            color=V.INK)
        ax.set_xticks(range(len(types)))
        ax.set_xticklabels([C.SHORT_TYPE[t] for t in types], rotation=60, ha="right", fontsize=6.5)
        ax.set_yticks(range(len(lus)))
        ax.set_yticklabels([C.LAND_USES[l] for l in lus], fontsize=6.5)
        ax.set_title(C.FACILITY_LABEL[f])
        ax.tick_params(length=0)
    cb = fig.colorbar(im, ax=axs, shrink=0.6, pad=0.02)
    cb.set_label(f"Bivariate Moran's I\n(land use × lag of {C.SEV_LABEL[s]} EB rate)", fontsize=7)
    fig.text(0.02, -0.02, "● positive, ○ negative spatial association, permutation p < 0.05 (499 permutations); "
             "– fewer than 10 crashes.", fontsize=6.5, color=V.INK2)
    V.savefig(fig, f"fig11_bivariate_moran_{s}.png")

# ------------------------------------------------------------ bivariate LISA atlas: one map per land use
for lu in lus:
    fig, axes, lax = V.region_axes(fig_h=4.8)
    B = V.bounds()
    for reg, ax in axes.items():
        V.draw_base(ax, reg, B)
        for f, kind in (("seg", "line"), ("int", "point")):
            col = f"bvlisa_{lu}_ALL_KSI"
            if col not in G[f]:
                continue
            sub = G[f][G[f]["region"] == reg]
            for z, (cl, c) in enumerate(lisa_order.items()):
                ss = sub[sub[col] == cl]
                if not len(ss):
                    continue
                if kind == "line":
                    ss.plot(ax=ax, color=c, linewidth=2.6 if cl != "Not significant" else 1.4,
                            zorder=3 + z)
                else:
                    ax.scatter(ss["pt"].x, ss["pt"].y, s=13 if cl != "Not significant" else 6,
                               color=c, edgecolor=V.INK if cl != "Not significant" else "white",
                               linewidth=0.35, zorder=10 + z)
    h = []
    for cl, c in lisa_order.items():
        ni = int((G["int"].get(f"bvlisa_{lu}_ALL_KSI") == cl).sum())
        ns = int((G["seg"].get(f"bvlisa_{lu}_ALL_KSI") == cl).sum())
        h.append(Line2D([0], [0], color=c, lw=3, marker="o", markersize=5, markerfacecolor=c,
                        markeredgecolor=V.INK, markeredgewidth=0.35,
                        label=f"{cl} (int {ni} / seg {ns})"))
    lax.legend(handles=h, loc="upper left", fontsize=6.5, alignment="left",
               title=f"{C.LAND_USES[lu]}\n× KSI crash rate at neighbours", title_fontsize=7.2)
    lax.text(0.0, 0.03, "Bivariate LISA (GeoDa). First term = land-use\ncount at the site; second = spatial lag of\n"
             "the EB-standardised KSI rate. Dots =\nintersections, lines = segments.",
             transform=lax.transAxes, fontsize=6.2, color=V.INK2, va="bottom")
    V.savefig(fig, f"atlas_bvlisa_{lu}.png")
print("esda figures done")
