"""Trace coloured road segments from the draft segment-typology map into
panel-local km coordinates (same panels/scales as digitize_study_area_map.py;
the basemap is shared with study_area_map_data.json)."""
import json
import sys

import numpy as np
from PIL import Image
from scipy import ndimage
from skimage.morphology import skeletonize

SRC = sys.argv[1] if len(sys.argv) > 1 else "segments_map_draft.png"
a = np.array(Image.open(SRC).convert("RGB")).astype(int)
H, W, _ = a.shape

CLS = {"low": ((154, 152, 144), 24), "shop": ((42, 120, 214), 60),
       "ind": ((235, 104, 52), 55), "civic": ((27, 175, 122), 55),
       "office": ((74, 58, 167), 50)}
PANELS = {"tampa": ((17, 398, 49, 704), 6.9), "orlando": ((419, 720, 38, 261), 5.2),
          "se": ((737, 925, 123, 631), 4.0)}   # interior box (px), px per km
IGN = [(320, 375, 180, 200), (83, 145, 510, 530), (588, 640, 93, 110),
       (360, 390, 82, 158), (690, 710, 50, 80), (905, 925, 150, 208),
       (35, 115, 640, 680), (430, 495, 225, 258), (740, 795, 575, 612)]
ign = np.zeros((H, W), bool)
for x0, x1, y0, y1 in IGN:
    ign[y0:y1, x0:x1] = True

out = {}
for pn, ((x0, x1, y0, y1), ppk) in PANELS.items():
    sl = (slice(y0, y1 + 1), slice(x0, x1 + 1))
    km = lambda x, y: [round(float((x - x0) / ppk), 3), round(float((y1 - y) / ppk), 3)]
    out[pn] = {}
    for k, (c, t) in CLS.items():
        m = (np.sqrt(((a[sl] - np.array(c)) ** 2).sum(2)) < t) & ~ign[sl]
        lab, n = ndimage.label(m, structure=np.ones((3, 3)))
        sz = ndimage.sum(m, lab, range(1, n + 1))
        m = np.isin(lab, [i + 1 for i, v in enumerate(sz) if v >= 4])
        lab, n = ndimage.label(m, structure=np.ones((3, 3)))
        segs = []  # one polyline per traced dash / run
        for i in range(1, n + 1):
            comp = lab == i
            yy, xx = np.nonzero(comp)
            sk = skeletonize(comp)
            S = set(zip(*np.nonzero(sk)))
            if len(S) < 6:   # short dash: straight line along principal axis
                P = np.c_[xx, yy].astype(float); c0 = P.mean(0)
                v = np.linalg.svd(P - c0)[2][0]; t = (P - c0) @ v
                ends = [c0 + t.min() * v, c0 + t.max() * v]
                if np.hypot(*(ends[1] - ends[0])) < 1:
                    ends = [c0 - [0, .5], c0 + [0, .5]]
                segs.append([km(x + x0, y + y0) for x, y in ends])
                continue
            nb = lambda q: [(q[0] + dy, q[1] + dx) for dy in (-1, 0, 1)
                            for dx in (-1, 0, 1) if (dy, dx) != (0, 0)
                            and (q[0] + dy, q[1] + dx) in S]
            while S:  # walk the skeleton from an end point, greedy chain
                ends = [q for q in S if len(nb(q)) <= 1]
                q = ends[0] if ends else next(iter(S))
                path = [q]; S.discard(q)
                while True:
                    nxt = [r for r in nb(q)]
                    if not nxt:
                        break
                    q = min(nxt, key=lambda r: abs(r[0] - q[0]) + abs(r[1] - q[1]))
                    path.append(q); S.discard(q)
                if len(path) >= 2:
                    pts = np.array([(x, y) for y, x in path], np.float32).reshape(-1, 1, 2)
                    import cv2
                    pts = cv2.approxPolyDP(pts, 0.8, False)[:, 0, :]
                    segs.append([km(x + x0, y + y0) for x, y in pts])
        out[pn][k] = segs
        print(pn, k, len(segs))
json.dump(out, open("study_area_segments_data.json", "w"))
