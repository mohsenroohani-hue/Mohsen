"""Crash-type x severity count models: one land use at a time AND all land uses jointly.

For every facility (intersections, segments), crash type (13) and severity level
(Total, KAB, KSI, Fatal):
  1. base model = exposure + design + context controls + county (or region) fixed effects
  2. residual Moran's I; if significant, Moran eigenvectors are selected on the residuals
     and added to every model for that outcome (eigenvector spatial filtering, ESF)
  3. one-land-use-at-a-time models: base + ESF + land use j   (j = 1..19)
  4. joint model: base + ESF + all land uses; compared with the design-only model
Estimator: NB2 with the full control set when the outcome has >= 150 crashes and is not
Fatal; otherwise Firth-penalised (quasi-)Poisson with a reduced control set (outcomes
with < 20 crashes are not modelled).
"""
import numpy as np
import pandas as pd
from scipy import stats

import common as C
import models as M

single, joint, diag, jctrl = [], [], [], []
LUS = list(C.LAND_USES)

for fac in ("int", "seg"):
    g = C.load(fac)
    coords = np.column_stack([g["pt"].x, g["pt"].y])
    SF = M.SpatialFilter(coords)
    n = len(g)
    for t in C.CRASH_TYPES:
        for s in C.SEVERITIES:
            y = g[f"y_{t}_{s}"].values
            ev = int(y.sum())
            rec = {"facility": fac, "type": t, "sev": s, "events": ev,
                   "sites_with_event": int((y > 0).sum())}
            if ev < 20:
                rec["estimator"] = "not modelled (<20 crashes)"
                diag.append(rec)
                continue
            full = (s != "FAT") and ev >= 150
            est = "NB2" if full else "Firth"
            ctrl = C.controls(fac, reduced=not full)
            fe = C.region_fe(g, reduced=not full)
            Xb = pd.concat([pd.Series(1.0, index=g.index, name="const"), g[ctrl].astype(float), fe], axis=1)
            base = M.fit(y, Xb.values, est)
            I0, p0 = SF.moran(base["pearson"])
            evs = SF.select(base["pearson"], max_ev=10 if full else 3) if p0 < 0.05 else []
            Xs = Xb.copy()
            for j in evs:
                Xs[f"ev{j}"] = SF.E[:, j]
            base_s = M.fit(y, Xs.values, est)
            I1, p1 = SF.moran(base_s["pearson"])
            rec.update({"estimator": base_s["est"], "controls": "full + county FE" if full else "reduced + region FE",
                        "alpha_or_phi": base_s.get("alpha") if full else base_s.get("phi"),
                        "resid_I_before": I0, "resid_p_before": p0, "n_eigvec": len(evs),
                        "resid_I_after": I1, "resid_p_after": p1, "aic_design": M.aic(base_s)})

            # ---- one land use at a time
            for lu in LUS:
                x = g["x_" + lu].values.astype(float)
                if (x > 0).sum() < 5:
                    single.append({"facility": fac, "type": t, "sev": s, "lu": lu, "events": ev,
                                   "estimator": "too rare (<5 sites)"})
                    continue
                X = np.column_stack([Xs.values, x])
                r = M.fit(y, X, est)
                tt = M.term(r, X.shape[1] - 1)
                lr = 2 * (r["llf"] - base_s["llf"]) if r["est"] == "NB2" else np.nan
                single.append({"facility": fac, "type": t, "sev": s, "lu": lu, "events": ev,
                               "estimator": r["est"], "n_eigvec": len(evs), **tt,
                               "LR": lr, "p_LR": stats.chi2.sf(lr, 1) if np.isfinite(lr) else np.nan,
                               "d_aic": M.aic(base_s) - M.aic(r)})

            # ---- joint model (all land uses)
            if full or ev >= 100:
                keep = [lu for lu in LUS if (g["x_" + lu] > 0).sum() >= 5]
                Xj = pd.concat([Xs, g[["x_" + l for l in keep]].astype(float)], axis=1)
                rj = M.fit(y, Xj.values, est)
                cols = list(Xj.columns)
                for lu in keep:
                    joint.append({"facility": fac, "type": t, "sev": s, "lu": lu, "events": ev,
                                  "estimator": rj["est"], **M.term(rj, cols.index("x_" + lu))})
                for c in ctrl + list(fe.columns):
                    jctrl.append({"facility": fac, "type": t, "sev": s, "var": c, **M.term(rj, cols.index(c))})
                if rj["est"] == "NB2":
                    jctrl.append({"facility": fac, "type": t, "sev": s, "var": "alpha (NB2 dispersion)",
                                  "beta": rj["alpha"]})
                lr = 2 * (rj["llf"] - base_s["llf"])
                Ij, pj = SF.moran(rj["pearson"])
                rec.update({"aic_joint": M.aic(rj), "d_aic_landuse": M.aic(base_s) - M.aic(rj),
                            "LR_landuse": lr, "df_landuse": len(keep),
                            "p_LR_landuse": stats.chi2.sf(lr, len(keep)),
                            "resid_I_joint": Ij, "resid_p_joint": pj,
                            "llf_design": base_s["llf"], "llf_joint": rj["llf"]})
                # deviance-style share: how much of the design model's log-likelihood gap
                # to the saturated-ish null does land use add (McFadden-type)
                null = M.fit(y, np.ones((n, 1)), est)
                rec["mcfadden_design"] = 1 - base_s["llf"] / null["llf"]
                rec["mcfadden_joint"] = 1 - rj["llf"] / null["llf"]
            diag.append(rec)
        print(fac, t, "done", flush=True)

S = pd.DataFrame(single)
S["q"] = np.nan
for (f, s), idx in S.groupby(["facility", "sev"]).groups.items():
    S.loc[idx, "q"] = M.bh_fdr(S.loc[idx, "p"].values)
S.to_csv(C.TAB / "res_single_landuse.csv", index=False)
J = pd.DataFrame(joint)
J["q"] = np.nan
for (f, s), idx in J.groupby(["facility", "sev"]).groups.items():
    J.loc[idx, "q"] = M.bh_fdr(J.loc[idx, "p"].values)
J.to_csv(C.TAB / "res_joint_landuse.csv", index=False)
pd.DataFrame(jctrl).to_csv(C.TAB / "res_joint_controls.csv", index=False)
pd.DataFrame(diag).to_csv(C.TAB / "res_model_diagnostics.csv", index=False)
print("models done")
