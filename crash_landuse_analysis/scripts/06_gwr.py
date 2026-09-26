"""Multiscale geographically weighted regression (MGWR; ArcGIS Pro: Multiscale
Geographically Weighted Regression; also the stand-alone MGWR 2.2 software).

Poisson GWR on these data collapses to the minimum bandwidth because it absorbs
over-dispersion, so we follow the continuous-outcome route available in ArcGIS/MGWR:
outcome = standardised ln(Empirical-Bayes smoothed crash rate); covariates = design
controls + every land use present at >= 10% of sites (all standardised). Each covariate
gets its own bandwidth: a bandwidth close to n means the land-use effect is global
(spatially stationary); a small one means it varies locally.
"""
import warnings

import numpy as np
import pandas as pd
import statsmodels.api as sm
from esda.smoothing import Empirical_Bayes
from mgwr.gwr import GWR, MGWR
from mgwr.sel_bw import Sel_BW

import common as C

warnings.filterwarnings("ignore")
OUTCOMES = [("ALL", "KAB"), ("ALL", "TOT"), ("ALL", "KSI"), ("PED", "KAB")]
rows, fits, site = [], [], {}
for fac in ("int", "seg"):
    g = C.load(fac)
    coords = np.column_stack([g["pt"].x, g["pt"].y])
    lus = [l for l in C.LAND_USES if (g[l] > 0).mean() >= 0.10]
    ctrl = ["lanes", "speed10"] + (["int_per_mile"] if fac == "seg" else [])
    cols = ctrl + ["x_" + l for l in lus]
    X = g[cols].values.astype(float)
    Xs = (X - X.mean(0)) / X.std(0)
    out = pd.DataFrame({"SEGMENTID": g["SEGMENTID"].values})
    for t, s in OUTCOMES:
        eb = np.asarray(Empirical_Bayes(g[f"y_{t}_{s}"].values.astype(float),
                                        g["exposure"].values.astype(float)).r).ravel()
        ly = np.log(eb + eb[eb > 0].min() * 0.5)
        y = ((ly - ly.mean()) / ly.std()).reshape(-1, 1)
        sel = Sel_BW(coords, y, Xs, multi=True, kernel="bisquare", fixed=False)
        bws = sel.search(criterion="AICc")
        r = MGWR(coords, y, Xs, sel, kernel="bisquare", fixed=False).fit()
        crit = r.critical_tval()
        gsel = Sel_BW(coords, y, Xs, kernel="bisquare", fixed=False)
        gbw = gsel.search(criterion="AICc")
        rg = GWR(coords, y, Xs, gbw, kernel="bisquare", fixed=False).fit()
        ols = sm.OLS(y.ravel(), sm.add_constant(Xs)).fit()
        n, k = len(y), Xs.shape[1] + 1
        ols_aicc = ols.aic + 2 * k * (k + 1) / (n - k - 1)
        fits.append({"facility": fac, "type": t, "sev": s, "aicc_ols": ols_aicc, "r2_ols": ols.rsquared,
                     "aicc_gwr": rg.aicc, "r2_gwr": rg.R2, "bw_gwr": gbw,
                     "aicc_mgwr": r.aicc, "r2_mgwr": r.R2})
        names = ["Intercept"] + cols
        for j, nm in enumerate(names):
            b = r.params[:, j]
            tv = r.tvalues[:, j]
            sig = np.abs(tv) > crit[j]
            rows.append({"facility": fac, "type": t, "sev": s, "var": nm,
                         "bandwidth": bws[j], "bw_share": bws[j] / n,
                         "global_beta": ols.params[j], "global_p": ols.pvalues[j],
                         "mean": b.mean(), "sd": b.std(), "min": b.min(), "median": np.median(b),
                         "max": b.max(), "pct_sig_pos": 100 * np.mean(sig & (b > 0)),
                         "pct_sig_neg": 100 * np.mean(sig & (b < 0)), "crit_t": crit[j]})
            if (t, s) == ("ALL", "KAB"):
                out[f"mgwr_b_{nm}"] = b
                out[f"mgwr_sig_{nm}"] = np.where(~sig, "n.s.", np.where(b > 0, "Positive", "Negative"))
        print(fac, t, s, "bws", dict(zip(names, bws)), flush=True)
    site[fac] = out
pd.DataFrame(rows).to_csv(C.TAB / "res_mgwr_coefficients.csv", index=False)
pd.DataFrame(fits).to_csv(C.TAB / "res_mgwr_fit.csv", index=False)
pd.to_pickle(site, C.OUT / "mgwr_sites.pkl")
print("mgwr done")
