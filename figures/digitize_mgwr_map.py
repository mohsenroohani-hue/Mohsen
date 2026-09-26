"""Trace the MGWR local-intercept map (same panels / scales as the
study-area map): locally significant sites are outlined circles whose fill
encodes the local standardized coefficient; non-significant sites are
faint dots. Usage: python digitize_mgwr_map.py draft.png [out.json]"""
import json
import sys

import cv2
import numpy as np
from PIL import Image
from scipy import ndimage

a = np.array(Image.open(sys.argv[1]).convert("RGB")).astype(float)
out_path = sys.argv[2] if len(sys.argv) > 2 else "mgwr_intercept_data.json"
g = a.mean(2)

# colour bar: x 432..673 at y 435; -10 at x=437, +10 at x=668
cx = np.arange(433, 673)
lut = a[430:440, 433:673].mean(0)
vals = (cx - 552.5) / 11.55

PANELS = {"tampa": ((17, 398, 49, 704), 6.9), "orlando": ((419, 720, 38, 261), 5.2),
          "se": ((737, 925, 123, 631), 4.0)}
IGN = [(320, 375, 180, 200), (83, 145, 510, 530), (588, 640, 93, 110),
       (360, 390, 82, 158), (690, 710, 50, 80), (905, 925, 150, 208),
       (35, 115, 640, 680), (430, 495, 225, 258), (740, 795, 575, 612),
       (737, 780, 318, 352)]   # title text spilling into the SE panel

gray8 = np.uint8(np.clip(g, 0, 255))
out = {}
for pn, ((x0, x1, y0, y1), ppk) in PANELS.items():
    km = lambda x, y: [round(float((x - x0) / ppk), 3), round(float((y1 - y) / ppk), 3)]
    sub = gray8[y0:y1, x0:x1]
    circ = cv2.HoughCircles(cv2.GaussianBlur(sub, (3, 3), 0), cv2.HOUGH_GRADIENT,
                            dp=1, minDist=3, param1=60, param2=9,
                            minRadius=3, maxRadius=6)
    sig = []
    if circ is not None:
        for x, y, r in circ[0]:
            X, Y = x + x0, y + y0
            if any(ax0 <= X <= ax1 and ay0 <= Y <= ay1 for ax0, ax1, ay0, ay1 in IGN):
                continue
            ring = g[int(Y) - int(r) - 1:int(Y) + int(r) + 2,
                     int(X) - int(r) - 1:int(X) + int(r) + 2]
            if (ring < 90).sum() < 6:            # needs a dark outline
                continue
            if not (x0 + 6 < X < x1 - 6 and y0 + 6 < Y < y1 - 6):
                continue
            yy, xx = np.mgrid[int(Y) - 3:int(Y) + 4, int(X) - 3:int(X) + 4]
            inner = np.hypot(yy - Y, xx - X) <= max(r - 1.8, 1.5)
            px = a[yy[inner], xx[inner]]
            px = px[px.mean(1) > 60]                 # drop outline pixels
            if len(px) == 0:
                continue
            fill = np.median(px, 0)
            v = float(vals[np.argmin(((lut - fill) ** 2).sum(1))])
            sig.append(km(X, Y) + [round(v, 2)])
    # dense chains of saturated fills (heavily overlapping circles): sample
    # the skeleton of the filled area every 3 px
    from skimage.morphology import skeletonize
    sat = (a[y0:y1, x0:x1].max(2) - a[y0:y1, x0:x1].min(2))
    filled = ndimage.binary_opening((sat > 60) & (g[y0:y1, x0:x1] < 200), iterations=1)
    filled[:6] = filled[-6:] = False; filled[:, :6] = filled[:, -6:] = False
    for ax0, ax1, ay0, ay1 in IGN:
        filled[max(ay0 - y0, 0):max(ay1 - y0, 0), max(ax0 - x0, 0):max(ax1 - x0, 0)] = False
    sk = np.argwhere(skeletonize(filled))
    taken = [((q[0] * ppk) + x0, y1 - q[1] * ppk) for q in sig]
    for yy_, xx_ in sk[np.lexsort((sk[:, 1], sk[:, 0]))]:
        X, Y = xx_ + x0, yy_ + y0
        if any((X - tx) ** 2 + (Y - ty) ** 2 < 9 for tx, ty in taken):
            continue
        fill = np.median(a[Y - 1:Y + 2, X - 1:X + 2].reshape(-1, 3), 0)
        v = float(vals[np.argmin(((lut - fill) ** 2).sum(1))])
        sig.append(km(X, Y) + [round(v, 2)])
        taken.append((X, Y))
    # faint (non-significant) dots: slightly darker than land, low contrast
    land = np.array([244, 243, 239])
    dd = np.sqrt(((a[y0:y1, x0:x1] - land) ** 2).sum(2))
    faint = (dd > 8) & (dd < 60) & (g[y0:y1, x0:x1] > 150)
    water = np.sqrt(((a[y0:y1, x0:x1] - [227, 235, 242]) ** 2).sum(2)) < 10
    white = a[y0:y1, x0:x1].min(2) >= 248
    faint &= ~ndimage.binary_dilation(water | white, iterations=1)
    lab, n = ndimage.label(faint)
    cs = ndimage.center_of_mass(faint, lab, range(1, n + 1))
    sz = ndimage.sum(faint, lab, range(1, n + 1))
    ns = [km(x + x0, y + y0) for (y, x), s in zip(cs, sz) if 2 <= s <= 60]
    # drop faint dots that sit under significant circles
    ns = [p for p in ns if all((p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2 > (4 / ppk) ** 2
                               for q in sig)]
    out[pn] = {"sig": sig, "ns": ns}
    print(pn, "significant", len(sig), "faint", len(ns),
          "coef range", (min(s[2] for s in sig), max(s[2] for s in sig)) if sig else None)
json.dump({"note": "Traced from the draft MGWR map. 'sig' = [x_km, y_km, local std. coefficient] "
           "for locally significant sites (fill colour read off the colour bar, +/-0.5); "
           "'ns' = [x_km, y_km] for faded, non-significant sites (values not recoverable). "
           "Overlapping circles are under-counted.", "title": "", "panels": out},
          open(out_path, "w"), indent=1)
