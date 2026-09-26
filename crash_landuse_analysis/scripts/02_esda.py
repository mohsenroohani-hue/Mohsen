"""Exploratory spatial data analysis (the GeoDa / ArcGIS Pro spatial-statistics layer).

* Global Moran's I on Empirical-Bayes standardised crash rates (GeoDa: Moran's I with
  EB rate; ArcGIS: Spatial Autocorrelation) for every crash type x severity.
* Incremental spatial autocorrelation (ArcGIS: Incremental Spatial Autocorrelation).
* Local Moran (LISA) cluster maps on EB rates (GeoDa: Univariate Local Moran with EB
  rate; ArcGIS: Cluster and Outlier Analysis).
* Getis-Ord Gi* hot spots on EB-smoothed rates (ArcGIS: Hot Spot Analysis; GeoDa: Local G*).
* Local join counts for rare binary outcomes - any fatal crash (GeoDa: Univariate
  Local Join Count).
* Bivariate Moran's I and bivariate LISA for EVERY land use against every crash type
  (GeoDa: Bivariate Moran / Bivariate Local Moran).
"""
import warnings

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from libpysal.weights import KNN, DistanceBand
import esda
from esda.smoothing import Empirical_Bayes

import common as C
import viz as V

warnings.filterwarnings("ignore")
rng_seed = 20251022
K = 6
PERM = 999

LISA_LAB = {1: "High-High", 2: "Low-High", 3: "Low-Low", 4: "High-Low"}


def weights(g, k=K):
    coords = np.column_stack([g["pt"].x, g["pt"].y])
    w = KNN.from_array(coords, k=k)
    w.transform = "r"
    wb = KNN.from_array(coords, k=k)
    wb.transform = "b"
    return w, wb, coords


def eb_rate(e, b):
    return np.asarray(Empirical_Bayes(np.asarray(e, float), np.asarray(b, float)).r).ravel()


def lisa_classes(lm, alpha=0.05):
    lab = np.array([LISA_LAB[q] for q in lm.q], dtype=object)
    lab[lm.p_sim >= alpha] = "Not significant"
    return lab


def gi_classes(z):
    out = np.full(len(z), "Not significant", dtype=object)
    for thr, conf in ((1.645, "90%"), (1.96, "95%"), (2.576, "99%")):
        out[z >= thr] = f"Hot spot {conf}"
        out[z <= -thr] = f"Cold spot {conf}"
    return out


site_out = {}
glob_rows = []
bv_rows = []
inc_rows = []

for fac in ("int", "seg"):
    g = C.load(fac)
    w, wb, coords = weights(g)
    b = g["exposure"].values
    site = pd.DataFrame({"SEGMENTID": g["SEGMENTID"].values})

    # ---------------- global Moran's I on EB rates: every type x severity
    for t in C.CRASH_TYPES:
        for s in C.SEVERITIES:
            e = g[f"y_{t}_{s}"].values
            if e.sum() < 10:
                continue
            m = esda.Moran_Rate(e, b, w, adjusted=True, permutations=PERM)
            mc = esda.Moran(e, w, permutations=PERM)
            glob_rows.append({"facility": fac, "type": t, "sev": s, "events": int(e.sum()),
                              "I_eb": m.I, "z_eb": m.z_sim, "p_eb": m.p_sim,
                              "I_count": mc.I, "p_count": mc.p_sim})

    # ---------------- sensitivity to k
    for k in (4, 6, 8, 10):
        wk, _, _ = weights(g, k)
        for t, s in (("ALL", "KSI"), ("ALL", "KAB"), ("ALL", "TOT")):
            m = esda.Moran_Rate(g[f"y_{t}_{s}"].values, b, wk, adjusted=True, permutations=PERM)
            inc_rows.append({"facility": fac, "kind": "knn", "k_or_km": k, "type": t, "sev": s,
                             "I": m.I, "z": m.z_sim, "p": m.p_sim})

    # ---------------- incremental spatial autocorrelation (distance bands)
    for km in np.arange(1, 10.5, 1.0):
        wd = DistanceBand.from_array(coords, threshold=km * 1000, binary=True, silence_warnings=True)
        if len(wd.islands) > 0.2 * len(g):
            continue
        wd.transform = "r"
        for t, s in (("ALL", "TOT"), ("ALL", "KAB"), ("ALL", "KSI"), ("ANGLE", "KAB"),
                     ("REAREND", "KAB"), ("PED", "KAB"), ("OFFROAD", "KAB")):
            m = esda.Moran_Rate(g[f"y_{t}_{s}"].values, b, wd, adjusted=True, permutations=199)
            inc_rows.append({"facility": fac, "kind": "band", "k_or_km": km, "type": t, "sev": s,
                             "I": m.I, "z": m.z_norm, "p": m.p_norm})

    # ---------------- LISA + Gi* on key measures
    key = [("ALL", "TOT"), ("ALL", "KAB"), ("ALL", "KSI"), ("ANGLE", "KAB"), ("LEFTTURN", "KAB"),
           ("RIGHTTURN", "TOT"), ("REAREND", "KAB"), ("SIDESWIPE", "KAB"), ("OFFROAD", "KAB"),
           ("PED", "KAB"), ("BIKE", "KAB"), ("HEADON", "KAB"), ("SINGLE", "KAB"),
           ("ALCOHOL", "KAB")]
    for t, s in key:
        e = g[f"y_{t}_{s}"].values
        lm = esda.Moran_Local_Rate(e, b, w, adjusted=True, permutations=PERM, seed=rng_seed)
        site[f"eb_{t}_{s}"] = eb_rate(e, b)
        site[f"lisa_{t}_{s}"] = lisa_classes(lm)
        site[f"lisap_{t}_{s}"] = lm.p_sim
        gl = esda.G_Local(site[f"eb_{t}_{s}"].values, wb, star=True, transform="B",
                          permutations=PERM, seed=rng_seed)
        site[f"giz_{t}_{s}"] = gl.Zs
        site[f"gi_{t}_{s}"] = gi_classes(gl.Zs)

    # ---------------- local join count: any fatal / any pedestrian KSI crash
    for t, s in (("ALL", "FAT"), ("PED", "KSI"), ("ALL", "KSI")):
        yb = (g[f"y_{t}_{s}"].values > 0).astype(int)
        ljc = esda.Join_Counts_Local(connectivity=wb, permutations=PERM, seed=rng_seed).fit(yb)
        lab = np.where(yb == 0, "No event at site",
                       np.where(np.asarray(ljc.p_sim) < 0.05, "Significant cluster",
                                "Event, not clustered"))
        site[f"ljc_{t}_{s}"] = ljc.LJC
        site[f"ljcp_{t}_{s}"] = ljc.p_sim
        site[f"ljccls_{t}_{s}"] = lab

    # ---------------- bivariate Moran: each land use x each crash type x severity
    for lu in C.LAND_USES:
        x = g["x_" + lu].values.astype(float)
        if x.std() == 0:
            continue
        for t in C.CRASH_TYPES:
            for s in C.SEVERITIES:
                e = g[f"y_{t}_{s}"].values
                if e.sum() < 10:
                    continue
                y = eb_rate(e, b)
                mbv = esda.Moran_BV(x, y, w, permutations=499)
                r = np.corrcoef(x, y)[0, 1]
                bv_rows.append({"facility": fac, "lu": lu, "type": t, "sev": s, "I_bv": mbv.I,
                                "z_bv": mbv.z_sim, "p_bv": mbv.p_sim, "r_insitu": r})
        # bivariate LISA: land use at site vs KSI / KAB rate at neighbours
        for t, s in (("ALL", "KSI"), ("ALL", "KAB")):
            y = eb_rate(g[f"y_{t}_{s}"].values, b)
            lbv = esda.Moran_Local_BV(x, y, w, permutations=PERM, seed=rng_seed)
            site[f"bvlisa_{lu}_{t}_{s}"] = lisa_classes(lbv)

    site_out[fac] = site
    site.to_pickle(C.OUT / f"esda_sites_{fac}.pkl")
    print(fac, "esda done")

glob = pd.DataFrame(glob_rows)
glob.to_csv(C.TAB / "t_global_moran.csv", index=False)
pd.DataFrame(bv_rows).to_csv(C.TAB / "t_bivariate_moran.csv", index=False)
pd.DataFrame(inc_rows).to_csv(C.TAB / "t_incremental_moran.csv", index=False)
print("saved")
