"""MGWR figures: covariate-specific bandwidths and local coefficient maps."""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.colors import TwoSlopeNorm

import common as C
import viz as V

M = pd.read_csv(C.TAB / "res_mgwr_coefficients.csv")
site = pd.read_pickle(C.OUT / "mgwr_sites.pkl")
LAB = {"Intercept": "Intercept (baseline risk)", "lanes": "Through lanes", "speed10": "Posted speed",
       "int_per_mile": "Intersections per mile"}
LAB.update({"x_" + k: v for k, v in C.LAND_USES.items()})
OUTS = [("ALL", "TOT"), ("ALL", "KAB"), ("ALL", "KSI"), ("PED", "KAB")]
OCOL = {("ALL", "TOT"): V.SEV_COLOR["TOT"], ("ALL", "KAB"): V.SEV_COLOR["KAB"],
        ("ALL", "KSI"): V.SEV_COLOR["KSI"], ("PED", "KAB"): V.CAT[1]}
OMK = {("ALL", "TOT"): "o", ("ALL", "KAB"): "s", ("ALL", "KSI"): "D", ("PED", "KAB"): "^"}

fig, axs = plt.subplots(1, 2, figsize=(7.4, 4.6), sharey=True, gridspec_kw={"wspace": 0.06})
names = [n for n in ["Intercept", "lanes", "speed10", "int_per_mile"] + ["x_" + l for l in C.LAND_USES]
         if (M["var"] == n).any()]
for ax, fac in zip(axs, ("int", "seg")):
    for k, (t, s) in enumerate(OUTS):
        d = M[(M.facility == fac) & (M.type == t) & (M.sev == s)].set_index("var").reindex(names)
        y = np.arange(len(names)) + (k - 1.5) * 0.17
        ok = d["bw_share"].notna().values
        ax.scatter(100 * d["bw_share"][ok], y[ok], marker=OMK[(t, s)], s=20, color=OCOL[(t, s)],
                   edgecolor="white", linewidth=0.4, zorder=3,
                   label=f"{C.SHORT_TYPE[t]} – {C.SEV_LABEL[s]}")
    ax.axvline(100, color=V.INK2, lw=0.8)
    ax.axvspan(0, 25, color="#fbe9e7", zorder=0)
    ax.text(12.5, -0.9, "local", ha="center", fontsize=6.5, color=V.INK2)
    ax.text(88, -0.9, "global", ha="center", fontsize=6.5, color=V.INK2)
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels([LAB.get(n, n) for n in names], fontsize=6.8)
    ax.set_ylim(len(names) - 0.4, -1.3)
    ax.set_xlim(0, 104)
    ax.set_xlabel("Bandwidth (% of sites per local model)")
    ax.set_title(C.FACILITY_LABEL[fac])
    ax.grid(axis="x")
    ax.set_axisbelow(True)
    for s_ in ("top", "right"):
        ax.spines[s_].set_visible(False)
axs[1].legend(loc="lower left", fontsize=6.5, title="Outcome: ln(EB rate)", title_fontsize=6.5)
V.savefig(fig, "fig19_mgwr_bandwidths.png")


def cont_map(fac, var, fname, title):
    g = C.load(fac).merge(site[fac], on="SEGMENTID")
    col, sig = f"mgwr_b_{var}", f"mgwr_sig_{var}"
    vals = g[col].values
    # robust colour limits: a few unstable local estimates must not wash out the scale
    lim = float(np.nanpercentile(np.abs(vals), 97))
    norm = TwoSlopeNorm(vcenter=0, vmin=-lim, vmax=lim)
    fig, axes, lax = V.region_axes()
    B = V.bounds()
    bg = V.segs_bg()
    for reg, ax in axes.items():
        V.draw_base(ax, reg, B, segs=bg[bg["region"] == reg] if fac == "int" else None)
        sub = g[g["region"] == reg]
        if fac == "int":
            s_ = sub[sub[sig] != "n.s."]
            n_ = sub[sub[sig] == "n.s."]
            ax.scatter(n_["pt"].x, n_["pt"].y, c=n_[col], cmap=V.DIVERGING, norm=norm, s=9,
                       edgecolor="white", linewidth=0.3, zorder=4, alpha=0.55)
            ax.scatter(s_["pt"].x, s_["pt"].y, c=s_[col], cmap=V.DIVERGING, norm=norm, s=16,
                       edgecolor=V.INK, linewidth=0.4, zorder=5)
        else:
            sub.plot(ax=ax, column=col, cmap=V.DIVERGING, norm=norm, linewidth=2.6, zorder=4)
    sm_ = plt.cm.ScalarMappable(cmap=V.DIVERGING, norm=norm)
    cax = lax.inset_axes([0.05, 0.62, 0.8, 0.06])
    cb = fig.colorbar(sm_, cax=cax, orientation="horizontal")
    cb.set_label("Local std. coefficient (capped at 97th pct.)", fontsize=6.5)
    cb.ax.tick_params(labelsize=6.5)
    lax.text(0.0, 0.95, title, transform=lax.transAxes, fontsize=7.5, fontweight="bold", va="top", color=V.INK)
    note = ("Outline = locally significant (MGWR-corrected\ncritical t); faded = not significant."
            if fac == "int" else "Outcome: ln(EB KAB rate), standardised.")
    lax.text(0.0, 0.42, note, transform=lax.transAxes, fontsize=6.3, color=V.INK2, va="top")
    V.savefig(fig, fname)


for fac in ("int", "seg"):
    cont_map(fac, "Intercept", f"fig20_mgwr_intercept_{fac}.png",
             f"MGWR local intercept — baseline\nKAB risk not explained by covariates\n({C.FACILITY_LABEL[fac].lower()})")
    d = M[(M.facility == fac) & (M.type == "ALL") & (M.sev == "KAB") & (M["var"].str.startswith("x_"))]
    d = d.sort_values("bw_share")
    for _, r in d.head(2).iterrows():
        if r.bw_share < 0.6:
            cont_map(fac, r["var"], f"fig21_mgwr_{fac}_{r['var'][2:]}.png",
                     f"MGWR local effect — {LAB[r['var']]}\n(bandwidth {int(r.bandwidth)} sites; "
                     f"{C.FACILITY_LABEL[fac].lower()})")
print("mgwr figs done")
