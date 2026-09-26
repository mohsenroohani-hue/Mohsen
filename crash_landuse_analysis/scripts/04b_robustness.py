"""Robustness of the joint land-use effects: county FE + spatial filter (main) vs
corridor (route) FE + spatial filter vs county FE without spatial filter."""
import numpy as np
import pandas as pd

import common as C
import models as M

KEY = ["LU_GASSTNS", "LU_COMMSHOPCNTRS", "LU_FASTFOOD", "LU_SINGLESTORE", "LU_SUPERMKTS",
       "LU_AUTOSALSER", "LU_HOTELS", "LU_BANKINS", "LU_OFFBLDGS", "LU_INDUSTRIAL"]
rows = []
for fac in ("int", "seg"):
    g = C.load(fac)
    SF = M.SpatialFilter(np.column_stack([g["pt"].x, g["pt"].y]))
    keep = [lu for lu in C.LAND_USES if (g["x_" + lu] > 0).sum() >= 5]
    for t, s in (("ALL", "TOT"), ("ALL", "KAB"), ("ALL", "KSI"), ("PED", "KAB")):
        y = g[f"y_{t}_{s}"].values
        ctrl = C.controls(fac)
        const = pd.Series(1.0, index=g.index, name="const")
        specs = {
            "main": pd.get_dummies(g["COUNTY"], prefix="cty", drop_first=True, dtype=float),
            "route_fe": pd.get_dummies(g["Route_grp"], prefix="rt", drop_first=True, dtype=float),
            "no_esf": pd.get_dummies(g["COUNTY"], prefix="cty", drop_first=True, dtype=float),
        }
        for name, fe in specs.items():
            Xb = pd.concat([const, g[ctrl].astype(float), fe], axis=1)
            if name != "no_esf":
                base = M.fit(y, Xb.values, "NB2")
                I0, p0 = SF.moran(base["pearson"])
                evs = SF.select(base["pearson"], max_ev=10) if p0 < 0.05 else []
                for j in evs:
                    Xb[f"ev{j}"] = SF.E[:, j]
            Xj = pd.concat([Xb, g[["x_" + l for l in keep]].astype(float)], axis=1)
            r = M.fit(y, Xj.values, "NB2")
            cols = list(Xj.columns)
            for lu in KEY:
                if lu in keep:
                    rows.append({"facility": fac, "type": t, "sev": s, "spec": name, "lu": lu,
                                 **M.term(r, cols.index("x_" + lu))})
        print(fac, t, s, flush=True)
pd.DataFrame(rows).to_csv(C.TAB / "res_robustness_joint.csv", index=False)
print("robustness done")
