"""Collect the tables used in the Word report into one JSON file."""
import json

import numpy as np
import pandas as pd

import common as C

T = C.TAB
out = {}
LUS = list(C.LAND_USES)
TYPES = list(C.CRASH_TYPES)


def star(p, q=None):
    if p is None or not np.isfinite(p):
        return ""
    s = "**" if p < 0.01 else ("*" if p < 0.05 else "")
    return s


def fmt_irr(v, p):
    if v is None or not np.isfinite(v):
        return "–"
    txt = f"{v:.2f}" if v < 9.95 else ">10"
    if v < 0.005:
        txt = "<0.01"
    return txt + star(p)


# ---- crash counts
cc = pd.read_csv(T / "t_crash_counts.csv")
rows = []
for t in TYPES:
    r = [C.CRASH_TYPES[t]]
    for f in ("Intersections", "Segments"):
        d = cc[(cc.Facility == f) & (cc["Crash type"] == C.CRASH_TYPES[t])].iloc[0]
        r += [f"{int(d[s]):,}" for s in ("Total", "KAB", "KSI", "Fatal")]
    rows.append(r)
out["tab_counts"] = rows

# ---- descriptives
de = pd.read_csv(T / "t_descriptives.csv")
rows = []
for _, d in de.iterrows():
    def ms(m, s):
        if not np.isfinite(m):
            return "–"
        if abs(m) >= 1000:
            return f"{m:,.0f} ({s:,.0f})"
        return f"{m:.2f} ({s:.2f})"
    rows.append([d["Variable"], ms(d["Intersections mean"], d["Intersections SD"]),
                 ms(d["Segments mean"], d["Segments SD"])])
out["tab_desc"] = rows

# ---- land-use exacerbation summary
su = pd.read_csv(T / "t_landuse_exacerbation_summary.csv").fillna("")
rows = []
for lu in LUS:
    r = [C.LAND_USES[lu]]
    for s in C.SEVERITIES:
        parts = []
        for f, lab in (("int", "I"), ("seg", "S")):
            d = su[(su.lu == lu) & (su.facility == f) & (su.sev == s)].iloc[0]
            txt = d["pos_types"]
            if d["all_types_sig"]:
                txt = ("ALL" + (", " + txt if txt else ""))
            parts.append(f"{lab}: {txt if txt else '—'}")
        r.append(" | ".join(parts))
    rows.append(r)
out["tab_exacerbation"] = rows

# ---- joint model (all crash types)
J = pd.read_csv(T / "res_joint_landuse.csv")
rows = []
for lu in LUS:
    r = [C.LAND_USES[lu] + (" (×10)" if lu in C.PER10 else "")]
    for f in ("int", "seg"):
        for s in C.SEVERITIES:
            d = J[(J.facility == f) & (J.type == "ALL") & (J.sev == s) & (J.lu == lu)]
            r.append(fmt_irr(d["IRR"].iloc[0], d["p"].iloc[0]) if len(d) else "–")
    rows.append(r)
out["tab_joint_all"] = rows

# ---- joint model controls (all crash types)
JC = pd.read_csv(T / "res_joint_controls.csv")
vars_ = ["ln_aadt", "ln_aadt_cross", "lanes", "speed10", "raised_median", "shoulder10", "bikelane",
         "busstops", "popden", "income", "ln_length", "int_per_mile"]
rows = []
for v in vars_:
    r = [C.CONTROL_LABEL[v]]
    for f in ("int", "seg"):
        for s in C.SEVERITIES:
            d = JC[(JC.facility == f) & (JC.type == "ALL") & (JC.sev == s) & (JC["var"] == v)]
            r.append(fmt_irr(d["IRR"].iloc[0], d["p"].iloc[0]) if len(d) else "–")
    rows.append(r)
out["tab_joint_controls"] = rows

# ---- diagnostics (appendix)
D = pd.read_csv(T / "res_model_diagnostics.csv")
rows = []
for _, d in D.iterrows():
    if not str(d["estimator"]).startswith(("NB2", "Firth")):
        continue
    rows.append([C.FACILITY_LABEL[d.facility][:3] + ".", C.SHORT_TYPE[d.type], C.SEV_LABEL[d.sev],
                 f"{int(d.events):,}", "NB2" if d.estimator == "NB2" else "Firth",
                 f"{d.alpha_or_phi:.2f}", f"{d.resid_I_before:.3f}{star(d.resid_p_before)}",
                 f"{int(d.n_eigvec)}", f"{d.resid_I_after:.3f}{star(d.resid_p_after)}",
                 "–" if not np.isfinite(d.get("d_aic_landuse", np.nan)) else f"{d.d_aic_landuse:+.1f}",
                 "–" if not np.isfinite(d.get("p_LR_landuse", np.nan)) else f"{d.p_LR_landuse:.3f}"])
out["tab_diag"] = rows

# ---- one-at-a-time IRR tables (appendix)
S = pd.read_csv(T / "res_single_landuse.csv")
for f in ("int", "seg"):
    for s in C.SEVERITIES:
        d = S[(S.facility == f) & (S.sev == s)]
        types = [t for t in TYPES if d[(d.type == t) & d.estimator.isin(["NB2", "Firth-Poisson"])].shape[0]]
        rows = []
        for lu in LUS:
            r = [C.LU_SHORT[lu] + (" ×10" if lu in C.PER10 else "")]
            for t in types:
                x = d[(d.type == t) & (d.lu == lu)]
                if not len(x) or x.estimator.iloc[0] not in ("NB2", "Firth-Poisson"):
                    r.append("n/a")
                else:
                    r.append(fmt_irr(x["IRR"].iloc[0], x["p"].iloc[0]))
            rows.append(r)
        out[f"tab_single_{f}_{s}"] = {"header": [C.SHORT_TYPE[t] for t in types], "rows": rows}

# ---- typology
pr = pd.read_csv(T / "t_typology_profiles.csv")
ra = pd.read_csv(T / "t_typology_rates.csv")
rows = []
for f in ("int", "seg"):
    for ty, sub in pr[pr.facility == f].groupby("typology"):
        top = sub.sort_values("z", ascending=False)
        top = [x for x, z in zip(top.family, top.z) if z > 0.3][:3]
        rr = ra[(ra.facility == f) & (ra.typology == ty)]
        def rt(t, s):
            return rr[(rr.type == t) & (rr.sev == s)]["rate"].iloc[0]
        rows.append([C.FACILITY_LABEL[f], ty, str(int(sub.n.iloc[0])), ", ".join(top) if top else "below average on all families",
                     f"{rt('ALL', 'TOT'):.2f}", f"{rt('ALL', 'KAB'):.3f}", f"{rt('ALL', 'KSI'):.3f}",
                     f"{rt('PED', 'KSI'):.4f}"])
out["tab_typology"] = rows

# ---- MGWR
mp = T / "res_mgwr_coefficients.csv"
if mp.exists():
    M = pd.read_csv(mp)
    F = pd.read_csv(T / "res_mgwr_fit.csv")
    rows = []
    names = ["Intercept", "lanes", "speed10", "int_per_mile"] + ["x_" + l for l in LUS]
    lab = {"Intercept": "Intercept (baseline risk)", "lanes": "Through lanes", "speed10": "Posted speed",
           "int_per_mile": "Intersections per mile"}
    for nm in names:
        if not (M["var"] == nm).any():
            continue
        r = [lab.get(nm, C.LAND_USES.get(nm[2:], nm))]
        for f in ("int", "seg"):
            d = M[(M.facility == f) & (M.type == "ALL") & (M.sev == "KAB") & (M["var"] == nm)]
            if not len(d):
                r += ["–", "–", "–"]
                continue
            d = d.iloc[0]
            n = 489 if f == "int" else 334
            r += [f"{int(d.bandwidth)} ({100 * d.bw_share:.0f}%)", f"{d['median']:+.2f} [{d['min']:+.2f}, {d['max']:+.2f}]",
                  f"{d.pct_sig_pos:.0f} / {d.pct_sig_neg:.0f}"]
        rows.append(r)
    out["tab_mgwr"] = rows
    rows = []
    for _, d in F.iterrows():
        rows.append([C.FACILITY_LABEL[d.facility], f"{C.SHORT_TYPE[d.type]} – {C.SEV_LABEL[d.sev]}",
                     f"{d.r2_ols:.2f}", f"{d.aicc_ols:.0f}", f"{d.r2_gwr:.2f}", f"{d.aicc_gwr:.0f}",
                     f"{d.r2_mgwr:.2f}", f"{d.aicc_mgwr:.0f}"])
    out["tab_mgwr_fit"] = rows
    # bandwidth matrix (all outcomes) for appendix
    rows = []
    for nm in names:
        if not (M["var"] == nm).any():
            continue
        r = [lab.get(nm, C.LAND_USES.get(nm[2:], nm))]
        for f in ("int", "seg"):
            for t, s in (("ALL", "TOT"), ("ALL", "KAB"), ("ALL", "KSI"), ("PED", "KAB")):
                d = M[(M.facility == f) & (M.type == t) & (M.sev == s) & (M["var"] == nm)]
                r.append(str(int(d.bandwidth.iloc[0])) if len(d) else "–")
        rows.append(r)
    out["tab_mgwr_bw"] = rows

# ---- robustness of joint effects
rp = T / "res_robustness_joint.csv"
if rp.exists():
    R = pd.read_csv(rp)
    rows = []
    for lu in R["lu"].unique():
        r = [C.LAND_USES[lu] + (" (×10)" if lu in C.PER10 else "")]
        for f in ("int", "seg"):
            for t, s in (("ALL", "TOT"), ("ALL", "KSI"), ("PED", "KAB")):
                for spec in ("main", "route_fe", "no_esf"):
                    d = R[(R.facility == f) & (R.type == t) & (R.sev == s) & (R.lu == lu) & (R.spec == spec)]
                    r.append(fmt_irr(d["IRR"].iloc[0], d["p"].iloc[0]) if len(d) else "–")
        rows.append(r)
    out["tab_robust"] = rows

json.dump(out, open(C.OUT / "report_data.json", "w"), indent=1, ensure_ascii=False)
print("report data written", list(out))
