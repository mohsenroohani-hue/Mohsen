"""Land-use context typology (GeoDa: Clusters > K Means; ArcGIS: Multivariate Clustering)
and crash-type profiles of each context."""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, calinski_harabasz_score

import common as C
import models as M
import viz as V

NAME_BY_FAMILY = {
    "Industrial": "Industrial & auto-oriented",
    "Retail anchors": "Shopping-center / big-box retail",
    "Civic & recreation": "Civic & recreation",
    "Office, lodging & mixed use": "Office, lodging & mixed use",
    "Small retail & services": "Small retail & services strip",
    "Food & drink": "Food & drink strip",
    "Auto-oriented": "Auto-oriented strip",
}
LOW = "Low-intensity frontage"
TYPO_COLOR = {LOW: "#9a9890", "Shopping-center / big-box retail": V.CAT[0],
              "Industrial & auto-oriented": V.CAT[1], "Civic & recreation": V.CAT[2],
              "Small retail & services strip": V.CAT[4], "Office, lodging & mixed use": V.CAT[6],
              "Food & drink strip": V.CAT[3], "Auto-oriented strip": V.CAT[7]}
TYPO_MARKER = {LOW: "o", "Shopping-center / big-box retail": "s", "Industrial & auto-oriented": "^",
               "Civic & recreation": "D", "Small retail & services strip": "P",
               "Office, lodging & mixed use": "v", "Food & drink strip": "X", "Auto-oriented strip": "h"}
KSEL = 5

fam = list(C.FAMILIES)
diag_rows, prof_rows, rate_rows, irr_rows = [], [], [], []
site_out = {}
G = {}
for fac in ("int", "seg"):
    g = C.load(fac)
    D = pd.DataFrame({k: g[v].sum(axis=1) for k, v in C.FAMILIES.items()}).astype(float)
    if fac == "seg":
        D = D.div(g["SEGLENGTH"], axis=0)  # establishments per mile
    D = D.clip(upper=D.quantile(0.99), axis=1)
    X = np.log1p(D.values)
    Z = (X - X.mean(0)) / X.std(0)
    for k in range(3, 9):
        km = KMeans(k, n_init=100, random_state=1).fit(Z)
        diag_rows.append({"facility": fac, "k": k, "silhouette": silhouette_score(Z, km.labels_),
                          "calinski_harabasz": calinski_harabasz_score(Z, km.labels_),
                          "smallest_cluster": np.bincount(km.labels_).min()})
    km = KMeans(KSEL, n_init=100, random_state=1).fit(Z)
    zp = pd.DataFrame(Z, columns=fam).groupby(km.labels_).mean()
    names = {}
    for c, row in zp.iterrows():
        names[c] = LOW if (row < 0.05).all() else NAME_BY_FAMILY[row.idxmax()]
    # disambiguate duplicates by second family
    seen = {}
    for c in sorted(names, key=lambda c: -zp.loc[c].max()):
        if names[c] in seen.values():
            second = zp.loc[c].sort_values(ascending=False).index[1]
            names[c] = NAME_BY_FAMILY[second]
        seen[c] = names[c]
    g["typology"] = [names[l] for l in km.labels_]
    G[fac] = g
    site_out[fac] = g[["SEGMENTID", "typology"]]
    for c in zp.index:
        for f_ in fam:
            prof_rows.append({"facility": fac, "typology": names[c], "family": f_, "z": zp.loc[c, f_],
                              "mean_count": D[km.labels_ == c][f_].mean(), "n": int((km.labels_ == c).sum())})
    # crash rates by typology
    for ty, sub in g.groupby("typology"):
        for t in C.CRASH_TYPES:
            for s in C.SEVERITIES:
                rate_rows.append({"facility": fac, "typology": ty, "type": t, "sev": s, "n": len(sub),
                                  "crashes": int(sub[f"y_{t}_{s}"].sum()),
                                  "rate": sub[f"y_{t}_{s}"].sum() / sub["exposure"].sum()})
    # adjusted IRRs relative to low-intensity frontage
    coords = np.column_stack([g["pt"].x, g["pt"].y])
    SF = M.SpatialFilter(coords)
    dums = pd.get_dummies(g["typology"], dtype=float)
    dums = dums.drop(columns=[LOW]) if LOW in dums else dums.iloc[:, 1:]
    for t in C.CRASH_TYPES:
        for s in C.SEVERITIES:
            y = g[f"y_{t}_{s}"].values
            ev = int(y.sum())
            if ev < 20:
                continue
            full = (s != "FAT") and ev >= 150
            est = "NB2" if full else "Firth"
            ctrl = C.controls(fac, reduced=not full)
            fe = C.region_fe(g, reduced=not full)
            Xb = pd.concat([pd.Series(1.0, index=g.index, name="const"), g[ctrl].astype(float), fe], axis=1)
            base = M.fit(y, Xb.values, est)
            I0, p0 = SF.moran(base["pearson"])
            evs = SF.select(base["pearson"], max_ev=10 if full else 3) if p0 < 0.05 else []
            for j in evs:
                Xb[f"ev{j}"] = SF.E[:, j]
            Xf = pd.concat([Xb, dums], axis=1)
            r = M.fit(y, Xf.values, est)
            cols = list(Xf.columns)
            for d in dums.columns:
                irr_rows.append({"facility": fac, "type": t, "sev": s, "typology": d, "events": ev,
                                 "estimator": r["est"], **M.term(r, cols.index(d))})
    print(fac, "typology done", flush=True)

pd.DataFrame(diag_rows).to_csv(C.TAB / "t_typology_kselection.csv", index=False)
prof = pd.DataFrame(prof_rows)
prof.to_csv(C.TAB / "t_typology_profiles.csv", index=False)
rates = pd.DataFrame(rate_rows)
rates.to_csv(C.TAB / "t_typology_rates.csv", index=False)
irr = pd.DataFrame(irr_rows)
irr.to_csv(C.TAB / "res_typology_irr.csv", index=False)
pd.to_pickle(site_out, C.OUT / "typology_sites.pkl")

# ---------------------------------------------------------------- figures
TYPO_SHORT = {LOW: "Low-intensity", "Shopping-center / big-box retail": "Shopping ctr / big-box",
              "Industrial & auto-oriented": "Industrial / auto", "Civic & recreation": "Civic / recreation",
              "Small retail & services strip": "Small retail strip", "Office, lodging & mixed use": "Office / lodging",
              "Food & drink strip": "Food & drink", "Auto-oriented strip": "Auto-oriented"}
fig, axs = plt.subplots(2, 1, figsize=(6.4, 5.6), gridspec_kw={"hspace": 0.35})
for ax, fac in zip(axs, ("int", "seg")):
    P = prof[prof.facility == fac].pivot(index="typology", columns="family", values="z")[fam]
    N = prof[prof.facility == fac].groupby("typology")["n"].first()
    Mn = prof[prof.facility == fac].pivot(index="typology", columns="family", values="mean_count")[fam]
    im = ax.imshow(P.values, cmap=V.DIVERGING, vmin=-2, vmax=2, aspect="auto")
    for i in range(P.shape[0]):
        for j in range(P.shape[1]):
            ax.text(j, i, f"{Mn.values[i, j]:.1f}", ha="center", va="center", fontsize=6.5,
                    color="white" if abs(P.values[i, j]) > 1.3 else V.INK)
    ax.set_xticks(range(len(fam)))
    ax.set_xticklabels(fam if fac == "seg" else [], rotation=30, ha="right", fontsize=7)
    ax.set_yticks(range(len(P)))
    ax.set_yticklabels([f"{ty} (n={N[ty]})" for ty in P.index], fontsize=7)
    ax.set_title(C.FACILITY_LABEL[fac] + (" — mean establishments per site" if fac == "int"
                                          else " — mean establishments per mile"), fontsize=8.5)
    ax.tick_params(length=0)
cb = fig.colorbar(im, ax=axs, shrink=0.6, pad=0.02)
cb.set_label("Cluster mean (z-score of log count)", fontsize=7)
V.savefig(fig, "fig12_typology_profiles.png")

for fac in ("int", "seg"):
    present = [k for k in TYPO_COLOR if k in set(G[fac]["typology"])]
    V.region_map(G[fac], "typology", {k: TYPO_COLOR[k] for k in present},
                 "point" if fac == "int" else "line", f"map_typology_{fac}.png",
                 f"Land-use context typology\n({C.FACILITY_LABEL[fac].lower()})", size=12,
                 marker_map=TYPO_MARKER)

# IRR heatmaps (typology vs low-intensity)
types = list(C.CRASH_TYPES)
for fac in ("int", "seg"):
    fig, axs = plt.subplots(1, 4, figsize=(7.4, 3.6), sharey=True)
    tys = [k for k in TYPO_COLOR if k in set(irr[irr.facility == fac]["typology"])]
    for ax, s in zip(axs, C.SEVERITIES):
        sub = irr[(irr.facility == fac) & (irr.sev == s)]
        Mv = sub.pivot(index="type", columns="typology", values="IRR").reindex(index=types, columns=tys)
        Pv = sub.pivot(index="type", columns="typology", values="p").reindex(index=types, columns=tys)
        show = np.where(Pv.values < 0.05, np.log(Mv.values.astype(float)), np.nan)
        im = ax.imshow(np.clip(show, -1.2, 1.2), cmap=V.DIVERGING, vmin=-1.2, vmax=1.2, aspect="auto")
        for i in range(Mv.shape[0]):
            for j in range(Mv.shape[1]):
                v = Mv.values[i, j]
                if np.isnan(v):
                    ax.add_patch(plt.Rectangle((j - 0.5, i - 0.5), 1, 1, facecolor="#f3f2ee", edgecolor="white", lw=0.6))
                elif Pv.values[i, j] < 0.05:
                    ax.text(j, i, f"{v:.1f}" if v < 9.95 else ">10", ha="center", va="center", fontsize=5.5,
                            color="white" if abs(np.log(v)) > 0.8 else V.INK)
                else:
                    ax.add_patch(plt.Rectangle((j - 0.5, i - 0.5), 1, 1, facecolor="#fbfbfa", edgecolor="#efeee9", lw=0.4))
        ax.set_title(C.SEV_LABEL[s])
        ax.set_xticks(range(len(tys)))
        ax.set_xticklabels([TYPO_SHORT[ty] for ty in tys], rotation=60, ha="right", fontsize=6)
        ax.set_yticks(range(len(types)))
        ax.set_yticklabels([C.SHORT_TYPE[t] for t in types], fontsize=6.5)
        ax.set_xlim(-0.5, len(tys) - 0.5)
        ax.set_ylim(len(types) - 0.5, -0.5)
        ax.tick_params(length=0)
        for s_ in ax.spines.values():
            s_.set_visible(False)
    sm_ = plt.cm.ScalarMappable(cmap=V.DIVERGING, norm=plt.Normalize(-1.2, 1.2))
    cb = fig.colorbar(sm_, ax=axs, shrink=0.75, pad=0.015)
    cb.set_ticks(np.log([0.33, 0.5, 1, 2, 3]))
    cb.set_ticklabels(["0.33", "0.5", "1", "2", "3"])
    cb.set_label("IRR vs low-intensity frontage (p < 0.05 only)", fontsize=7)
    V.savefig(fig, f"fig13_typology_irr_{fac}.png")
print("typology done")
