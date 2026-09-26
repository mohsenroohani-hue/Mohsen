"""Trace IRR point estimates and 95% CIs from the draft forest plot
(log2 axis calibrated from tick marks; one colour per severity).

Usage: python digitize_forest_plot.py draft.png  -> forest_plot_data.json
"""
import json
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

a = np.array(Image.open(sys.argv[1]).convert("RGB")).astype(float)
ROWS = ["Mixed-use buildings", "Gas stations", "Supermarkets", "Regional shopping centers",
        "Community shopping centers", "Fast-food restaurants", "Sit-down restaurants", "Bars",
        "Hotels", "Office buildings", "Department / big-box stores", "Banks",
        "Auto sales & service", "Repair shops", "Single-tenant retail stores",
        "Parks & recreation", "Schools", "Hospitals", "Industrial"]
SEV = {"Total": (133, 180, 235), "KAB": (68, 134, 213), "KSI": (30, 85, 153),
       "Fatal": (4, 41, 97)}
OFFSETS = {"Total": -8.75, "KAB": -3.25, "KSI": 3.25, "Fatal": 8.75}  # dodge (px)
PANELS = {"Intersections": (203, 571, 387), "Segments": (593, 961, 777)}  # frame, x(IRR=1)
PX_PER_DOUBLING = 79.0
Y0, PITCH = 52.25, 30.1                              # first row centre, row pitch

cols = np.array(list(SEV.values()), float)
dist = np.sqrt(((a[:, :, None, :] - cols[None, None]) ** 2).sum(-1))
nearest = dist.argmin(-1)
sat = a.max(-1) - a.min(-1)
irr = lambda x, x1: float(2 ** ((x - x1) / PX_PER_DOUBLING))

out = {}
for pn, (xa, xb, x1) in PANELS.items():
    out[pn] = {}
    for i, lu in enumerate(ROWS):
        yc = Y0 + i * PITCH
        out[pn][lu] = {}
        for k, sev in enumerate(SEV):
            yk = int(round(yc + OFFSETS[sev]))
            isk = (nearest == k) & (dist.min(-1) < 70) & (sat > 40)
            isk[:, :xa + 2] = False; isk[:, xb - 1:] = False
            # marker: this colour above/below the line row
            band = isk[yk - 5:yk + 6].copy(); band[4:7] = False
            mcols = np.nonzero(band.sum(0) >= 2)[0]
            if len(mcols) == 0:
                continue
            groups = np.split(mcols, np.nonzero(np.diff(mcols) > 3)[0] + 1)
            gm = max(groups, key=len)
            xm = (gm.min() + gm.max()) / 2
            # CI on the line row, bridging gaps left by other markers
            xs = np.nonzero(isk[yk - 1:yk + 2].any(0))[0]
            lo = hi = int(round(xm))
            for x in xs[xs <= xm][::-1]:
                if lo - x <= 14: lo = x
            for x in xs[xs >= xm]:
                if x - hi <= 14: hi = x
            cy, cx = yk, int(round(xm))
            filled = bool(np.median(sat[cy - 1:cy + 2, cx - 1:cx + 2]) > 40)
            out[pn][lu][sev] = {
                "irr": round(irr(xm, x1), 3), "lo": round(irr(lo, x1), 3),
                "hi": round(irr(hi, x1), 3), "sig": filled,
                "lo_clipped": bool(lo <= xa + 4), "hi_clipped": bool(hi >= xb - 3)}
json.dump(out, open("forest_plot_data.json", "w"), indent=1)
