"""Figures and summary tables from the count models."""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle

import common as C
import viz as V

S = pd.read_csv(C.TAB / "res_single_landuse.csv")
J = pd.read_csv(C.TAB / "res_joint_landuse.csv")
D = pd.read_csv(C.TAB / "res_model_diagnostics.csv")
LUS = list(C.LAND_USES)
TYPES = list(C.CRASH_TYPES)
G = {f: C.load(f) for f in ("int", "seg")}
PREV = {f: (G[f][LUS] > 0).mean() for f in G}


def lu_label(lu, fac=None):
    lab = C.LAND_USES[lu] + (" (per 10)" if lu in C.PER10 else "")
    if fac is not None and PREV[fac][lu] < 0.05:
        lab += " †"
    return lab


# ------------------------------------------------------------------ IRR heatmaps (one at a time)
def heat(ax, fac, sev, ylabels=True):
    d = S[(S.facility == fac) & (S.sev == sev)]
    est = d[d.estimator.isin(["NB2", "Firth-Poisson"])]
    M = est.pivot(index="lu", columns="type", values="IRR").reindex(index=LUS, columns=TYPES)
    P = est.pivot(index="lu", columns="type", values="p").reindex(index=LUS, columns=TYPES)
    Q = est.pivot(index="lu", columns="type", values="q").reindex(index=LUS, columns=TYPES)
    ev = D[(D.facility == fac) & (D.sev == sev)].set_index("type")["events"].reindex(TYPES)
    show = np.where(P.values < 0.05, np.log(M.values.astype(float)), np.nan)
    ax.set_facecolor("white")
    ax.imshow(np.clip(show, -1.1, 1.1), cmap=V.DIVERGING, vmin=-1.1, vmax=1.1, aspect="auto")
    for i, lu in enumerate(LUS):
        for j, t in enumerate(TYPES):
            v, p, q = M.values[i, j], P.values[i, j], Q.values[i, j]
            if np.isnan(v):
                ax.add_patch(Rectangle((j - 0.5, i - 0.5), 1, 1, facecolor="#f3f2ee", edgecolor="white", lw=0.6))
                continue
            if p < 0.05:
                txt = f"{v:.2f}" if v < 9.95 else ">10"
                ax.text(j, i, txt, ha="center", va="center", fontsize=5.2,
                        color="white" if abs(np.log(v)) > 0.75 else V.INK,
                        fontweight="bold" if q < 0.10 else "normal")
                if q < 0.10:
                    ax.add_patch(Rectangle((j - 0.46, i - 0.46), 0.92, 0.92, fill=False,
                                           edgecolor=V.INK, lw=0.8))
            else:
                ax.add_patch(Rectangle((j - 0.5, i - 0.5), 1, 1, facecolor="#fbfbfa", edgecolor="#efeee9", lw=0.4))
    ax.set_xticks(range(len(TYPES)))
    ax.set_xticklabels([f"{C.SHORT_TYPE[t]} ({int(ev[t])})" for t in TYPES], rotation=65, ha="right", fontsize=6)
    ax.set_yticks(range(len(LUS)))
    ax.set_yticklabels([lu_label(l, fac) for l in LUS] if ylabels else [], fontsize=6.3)
    ax.set_xlim(-0.5, len(TYPES) - 0.5)
    ax.set_ylim(len(LUS) - 0.5, -0.5)
    ax.tick_params(length=0)
    for s_ in ax.spines.values():
        s_.set_visible(False)
    ax.set_title(C.FACILITY_LABEL[fac])


for sev in C.SEVERITIES:
    fig, axs = plt.subplots(1, 2, figsize=(7.4, 5.6), sharey=False,
                            gridspec_kw={"wspace": 0.05})
    heat(axs[0], "int", sev, True)
    heat(axs[1], "seg", sev, False)
    sm_ = plt.cm.ScalarMappable(cmap=V.DIVERGING, norm=plt.Normalize(-1.1, 1.1))
    cb = fig.colorbar(sm_, ax=axs, shrink=0.5, pad=0.015)
    cb.set_ticks(np.log([0.4, 0.6, 1, 1.6, 2.5]))
    cb.set_ticklabels(["0.4", "0.6", "1", "1.6", "2.5"])
    cb.set_label("Incidence rate ratio\n(per establishment)", fontsize=7)
    V.savefig(fig, f"fig14_irr_single_{sev}.png")

# ------------------------------------------------------------------ joint heatmaps (appendix)
Sj = S.copy()
for sev in C.SEVERITIES:
    S = J.assign(estimator=J.estimator)  # reuse the heat() function on joint results
    S = S[S.sev == sev]
    if not len(S):
        continue
    fig, axs = plt.subplots(1, 2, figsize=(7.4, 5.6), gridspec_kw={"wspace": 0.05})
    heat(axs[0], "int", sev, True)
    heat(axs[1], "seg", sev, False)
    V.savefig(fig, f"figA_irr_joint_{sev}.png")
S = Sj

# ------------------------------------------------------------------ summary: which land uses exacerbate risk
rows = []
for lu in LUS:
    for fac in ("int", "seg"):
        for sev in C.SEVERITIES:
            d = S[(S.lu == lu) & (S.facility == fac) & (S.sev == sev) & S.estimator.isin(["NB2", "Firth-Poisson"])]
            pos = d[(d.p < 0.05) & (d.IRR > 1)]
            neg = d[(d.p < 0.05) & (d.IRR < 1)]
            rows.append({"lu": lu, "facility": fac, "sev": sev, "n_pos": len(pos), "n_neg": len(neg),
                         "pos_types": ", ".join(C.SHORT_TYPE[t] + ("*" if q < 0.10 else "")
                                                for t, q in zip(pos.type, pos.q) if t != "ALL"),
                         "all_types_sig": bool(((d.type == "ALL") & (d.p < 0.05) & (d.IRR > 1)).any()),
                         "neg_types": ", ".join(C.SHORT_TYPE[t] for t in neg.type if t != "ALL")})
summ = pd.DataFrame(rows)
summ.to_csv(C.TAB / "t_landuse_exacerbation_summary.csv", index=False)

tot = summ.groupby("lu")[["n_pos", "n_neg"]].sum()
order = (tot["n_pos"] - tot["n_neg"]).sort_values().index.tolist()
fig, axs = plt.subplots(1, 2, figsize=(7.4, 4.6), sharey=True, gridspec_kw={"wspace": 0.08})
for ax, fac in zip(axs, ("int", "seg")):
    y = np.arange(len(order))
    left_p = np.zeros(len(order))
    left_n = np.zeros(len(order))
    for sev in C.SEVERITIES:
        sub = summ[(summ.facility == fac) & (summ.sev == sev)].set_index("lu").reindex(order)
        ax.barh(y, sub.n_pos, left=left_p, color=V.SEV_COLOR[sev], height=0.7,
                edgecolor="white", linewidth=0.8, label=C.SEV_LABEL[sev])
        ax.barh(y, -sub.n_neg, left=-left_n, color=V.SEV_COLOR[sev], height=0.7,
                edgecolor="white", linewidth=0.8, alpha=0.45)
        left_p += sub.n_pos.values
        left_n += sub.n_neg.values
    ax.axvline(0, color=V.INK2, lw=0.8)
    ax.set_yticks(y)
    ax.set_yticklabels([C.LAND_USES[l] for l in order], fontsize=6.8)
    ax.set_title(C.FACILITY_LABEL[fac], pad=12)
    ax.set_xlabel("Number of significant associations (p < 0.05)", fontsize=6.8)
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{abs(v):.0f}"))
    ax.text(0.02, 1.0, "← lower risk", transform=ax.transAxes, fontsize=6.3, color=V.INK2, va="bottom")
    ax.text(0.98, 1.0, "higher risk →", transform=ax.transAxes, fontsize=6.3, color=V.INK2, va="bottom", ha="right")
    ax.grid(axis="x")
    ax.set_axisbelow(True)
    for s_ in ("top", "right"):
        ax.spines[s_].set_visible(False)
axs[1].legend(loc="lower right", title="Severity (solid = IRR>1,\nfaded = IRR<1)", title_fontsize=6.5, fontsize=6.5)
V.savefig(fig, "fig15_landuse_risk_profile.png")

# ------------------------------------------------------------------ joint forest plot: all crash types
fig, axs = plt.subplots(1, 2, figsize=(7.4, 5.6), sharey=True, gridspec_kw={"wspace": 0.06})
off = {"TOT": -0.3, "KAB": -0.1, "KSI": 0.1, "FAT": 0.3}
for ax, fac in zip(axs, ("int", "seg")):
    d = J[(J.facility == fac) & (J.type == "ALL")]
    for sev in C.SEVERITIES:
        dd = d[d.sev == sev].set_index("lu").reindex(LUS)
        y = np.arange(len(LUS)) + off[sev]
        lo = np.clip(dd["lo"], 0.2, 5)
        hi = np.clip(dd["hi"], 0.2, 5)
        ax.hlines(y, lo, hi, color=V.SEV_COLOR[sev], lw=1.1)
        sig = dd["p"] < 0.05
        ax.scatter(np.clip(dd["IRR"][sig], 0.2, 5), y[sig.values], marker=V.SEV_MARKER[sev], s=22,
                   color=V.SEV_COLOR[sev], edgecolor="white", linewidth=0.5, zorder=4)
        ax.scatter(np.clip(dd["IRR"][~sig], 0.2, 5), y[~sig.values], marker=V.SEV_MARKER[sev], s=20,
                   facecolor="white", edgecolor=V.SEV_COLOR[sev], linewidth=0.9, zorder=4)
    ax.axvline(1, color=V.INK2, lw=0.8)
    ax.set_xscale("log")
    ax.set_xlim(0.2, 5)
    ax.set_xticks([0.25, 0.5, 1, 2, 4])
    ax.set_xticklabels(["0.25", "0.5", "1", "2", "4"])
    ax.xaxis.set_minor_formatter(plt.NullFormatter())
    ax.set_yticks(range(len(LUS)))
    ax.set_yticklabels([lu_label(l, fac) for l in LUS], fontsize=6.5)
    ax.set_ylim(len(LUS) - 0.5, -0.5)
    ax.set_title(C.FACILITY_LABEL[fac] + " — all crash types")
    ax.set_xlabel("IRR (95% CI), joint model")
    ax.grid(axis="x")
    ax.set_axisbelow(True)
    for i in range(0, len(LUS), 2):
        ax.axhspan(i - 0.5, i + 0.5, color="#f6f5f1", zorder=0)
h = [Line2D([0], [0], marker=V.SEV_MARKER[s], color=V.SEV_COLOR[s], lw=1.1, markersize=5,
            label=C.SEV_LABEL[s]) for s in C.SEVERITIES]
fig.legend(handles=h, loc="lower center", ncol=4, bbox_to_anchor=(0.5, -0.02), fontsize=7,
           title="Filled = p<0.05; hollow = n.s.; Fatal uses Firth-penalised Poisson", title_fontsize=6.5)
V.savefig(fig, "fig16_joint_forest_all.png")

# ------------------------------------------------------------------ land-use value added (design vs design+LU)
dd = D.dropna(subset=["d_aic_landuse"])
fig, axs = plt.subplots(1, 2, figsize=(7.2, 4.0), sharey=True)
for ax, fac in zip(axs, ("int", "seg")):
    sub = dd[dd.facility == fac]
    Mv = sub.pivot(index="type", columns="sev", values="d_aic_landuse").reindex(index=TYPES, columns=C.SEVERITIES)
    Pv = sub.pivot(index="type", columns="sev", values="p_LR_landuse").reindex(index=TYPES, columns=C.SEVERITIES)
    R1 = sub.pivot(index="type", columns="sev", values="mcfadden_design").reindex(index=TYPES, columns=C.SEVERITIES)
    R2 = sub.pivot(index="type", columns="sev", values="mcfadden_joint").reindex(index=TYPES, columns=C.SEVERITIES)
    im = ax.imshow(np.clip(Mv.values.astype(float), -30, 30), cmap=V.DIVERGING, vmin=-30, vmax=30, aspect="auto")
    for i in range(Mv.shape[0]):
        for j in range(Mv.shape[1]):
            v = Mv.values[i, j]
            if np.isnan(v):
                ax.add_patch(Rectangle((j - 0.5, i - 0.5), 1, 1, facecolor="#f3f2ee", edgecolor="white"))
                continue
            star = "*" if Pv.values[i, j] < 0.05 else ""
            ax.text(j, i, f"{v:+.0f}{star}\n{100*(R2.values[i, j]-R1.values[i, j]):.1f} pts",
                    ha="center", va="center", fontsize=5.4, color="white" if abs(v) > 20 else V.INK)
    ax.set_xticks(range(4))
    ax.set_xticklabels([C.SEV_LABEL[s] for s in C.SEVERITIES])
    ax.set_yticks(range(len(TYPES)))
    ax.set_yticklabels([C.SHORT_TYPE[t] for t in TYPES])
    ax.set_title(C.FACILITY_LABEL[fac])
    ax.tick_params(length=0)
cb = fig.colorbar(im, ax=axs, shrink=0.7, pad=0.02)
cb.set_label("ΔAIC (design-only − design + land use)\npositive = land use improves the model", fontsize=6.8)
fig.text(0.01, -0.03, "Top line: ΔAIC (* likelihood-ratio test of all land uses jointly, p < 0.05). "
         "Bottom line: gain in McFadden pseudo-R² (percentage points). Grey: joint model not estimated.",
         fontsize=6.3, color=V.INK2)
V.savefig(fig, "fig17_landuse_value_added.png")

# ------------------------------------------------------------------ residual spatial autocorrelation
dd = D.dropna(subset=["resid_I_before"]).copy()
dd["label"] = dd["facility"].map({"int": "Int", "seg": "Seg"}) + " · " + dd["type"].map(C.SHORT_TYPE) + " · " + dd["sev"].map(C.SEV_LABEL)
dd = dd[dd.n_eigvec > 0].sort_values(["facility", "resid_I_before"])
fig, ax = plt.subplots(figsize=(7.2, 6.4))
y = np.arange(len(dd))
ax.hlines(y, dd.resid_I_after, dd.resid_I_before, color=V.GRID, lw=1.5)
ax.scatter(dd.resid_I_before, y, color=V.CAT[1], s=18, label="Before spatial filter", zorder=3)
ax.scatter(dd.resid_I_after, y, color=V.CAT[0], s=18, label="After spatial filter (ESF)", zorder=3)
for yi, n in zip(y, dd.n_eigvec):
    ax.text(0.245, yi, f"{int(n)}", fontsize=5.5, color=V.INK2, va="center")
ax.text(0.245, len(dd) + 0.2, "EVs", fontsize=6, color=V.INK2)
ax.set_yticks(y)
ax.set_yticklabels(dd.label, fontsize=5.8)
ax.set_xlabel("Moran's I of Pearson residuals (k = 6)")
ax.axvline(0, color=V.INK2, lw=0.8)
ax.set_xlim(-0.02, 0.26)
ax.grid(axis="x")
ax.set_axisbelow(True)
ax.legend(loc="lower right")
for s_ in ("top", "right"):
    ax.spines[s_].set_visible(False)
V.savefig(fig, "fig18_residual_moran_esf.png")

# ------------------------------------------------------------------ land-use atlas forest plots
off = {"TOT": -0.3, "KAB": -0.1, "KSI": 0.1, "FAT": 0.3}
for lu in LUS:
    fig, axs = plt.subplots(1, 2, figsize=(7.2, 3.6), sharey=True, gridspec_kw={"wspace": 0.05})
    for ax, fac in zip(axs, ("int", "seg")):
        d = S[(S.lu == lu) & (S.facility == fac) & S.estimator.isin(["NB2", "Firth-Poisson"])]
        for sev in C.SEVERITIES:
            dd = d[d.sev == sev].set_index("type").reindex(TYPES)
            yy = np.arange(len(TYPES)) + off[sev]
            ok = dd["IRR"].notna().values
            lo = np.clip(dd["lo"], 0.1, 10)
            hi = np.clip(dd["hi"], 0.1, 10)
            ax.hlines(yy[ok], lo[ok], hi[ok], color=V.SEV_COLOR[sev], lw=1)
            sig = (dd["p"] < 0.05).values & ok
            ax.scatter(np.clip(dd["IRR"], 0.1, 10)[sig], yy[sig], marker=V.SEV_MARKER[sev], s=20,
                       color=V.SEV_COLOR[sev], edgecolor="white", linewidth=0.4, zorder=4)
            ns = ok & ~sig
            ax.scatter(np.clip(dd["IRR"], 0.1, 10)[ns], yy[ns], marker=V.SEV_MARKER[sev], s=16,
                       facecolor="white", edgecolor=V.SEV_COLOR[sev], linewidth=0.8, zorder=4)
        ax.axvline(1, color=V.INK2, lw=0.8)
        ax.set_xscale("log")
        ax.set_xlim(0.1, 10)
        ax.set_xticks([0.2, 0.5, 1, 2, 5])
        ax.set_xticklabels(["0.2", "0.5", "1", "2", "5"])
        ax.xaxis.set_minor_formatter(plt.NullFormatter())
        ax.set_yticks(range(len(TYPES)))
        ax.set_yticklabels([C.SHORT_TYPE[t] for t in TYPES], fontsize=6.8)
        ax.set_ylim(len(TYPES) - 0.5, -0.5)
        for i in range(0, len(TYPES), 2):
            ax.axhspan(i - 0.5, i + 0.5, color="#f6f5f1", zorder=0)
        prev = 100 * PREV[fac][lu]
        ttl = f"{C.FACILITY_LABEL[fac]} (present at {prev:.0f}% of sites)"
        if not len(d):
            ax.text(1, len(TYPES) / 2, "too rare to model", ha="center", color=V.MUTED)
        ax.set_title(ttl, fontsize=8)
        ax.set_xlabel("IRR per establishment" + (" ×10" if lu in C.PER10 else "") + " (95% CI)", fontsize=7)
        ax.grid(axis="x")
        ax.set_axisbelow(True)
    h = [Line2D([0], [0], marker=V.SEV_MARKER[s], color=V.SEV_COLOR[s], lw=1, markersize=5,
                label=C.SEV_LABEL[s]) for s in C.SEVERITIES]
    fig.legend(handles=h, loc="upper center", ncol=5, bbox_to_anchor=(0.5, 0.0), fontsize=7,
               title="filled = p < 0.05, hollow = not significant", title_fontsize=6.5)
    fig.suptitle(C.LAND_USES[lu], fontsize=9.5, fontweight="bold", color=V.INK, y=1.0)
    V.savefig(fig, f"atlas_forest_{lu}.png")
print("model figs done")
