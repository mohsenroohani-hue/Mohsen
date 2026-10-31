#!/usr/bin/env python3
"""Built-up areas of Mazandaran (Iran) from the Normalized Difference Built-up Index (NDBI).

Input : USGS Landsat Collection 2 Level-2 (surface reflectance) scenes downloaded from
        USGS EarthExplorer (extracted folders or the original .tar bundles).
Output: ESRI Shapefile of built-up polygons, plus the NDBI / NDVI / built-up GeoTIFFs.

    NDBI = (SWIR1 - NIR) / (SWIR1 + NIR)
        Landsat 8/9 : SWIR1 = SR_B6, NIR = SR_B5
        Landsat 4-7 : SWIR1 = SR_B5, NIR = SR_B4

Every scene is resampled (nearest neighbour) onto one common 30 m UTM grid, cloud / shadow /
snow / fill pixels are masked with QA_PIXEL, and the per-pixel mean of all clear observations
is used, so scenes from different dates and UTM zones combine into one province-wide layer.

Usage:
    python ndbi_mazandaran.py --scenes data/landsat --boundary data/mazandaran.shp --out out
"""
import argparse
import json
import re
import sys
import tarfile
import unicodedata
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
import requests
from affine import Affine
from rasterio import features
from rasterio.enums import Resampling
from rasterio.transform import from_origin
from rasterio.warp import reproject, transform_bounds
from scipy import ndimage
from shapely.geometry import shape

# sensor prefix -> (red, nir, swir1) Level-2 surface-reflectance band numbers
SENSOR_BANDS = {
    "LC08": (4, 5, 6), "LC09": (4, 5, 6),                       # OLI / OLI-2
    "LE07": (3, 4, 5), "LT05": (3, 4, 5), "LT04": (3, 4, 5),    # ETM+ / TM
}
FILE_RE = re.compile(
    r"^(?P<id>(?P<sensor>L[CET]\d{2})_L2S[PR]_\d{6}_\d{8}_\d{8}_\d{2}_\w{2})_(?P<band>SR_B\d|QA_PIXEL)\.TIF$",
    re.IGNORECASE,
)
QA_BAD_BITS = 0b111111          # fill, dilated cloud, cirrus, cloud, cloud shadow, snow
SR_SCALE, SR_OFFSET = 2.75e-5, -0.2   # Collection 2 Level-2 surface-reflectance scaling
NODATA = -9999.0
STRIP_ROWS = 1024               # rows processed at a time, keeps memory modest


# ----------------------------------------------------------------------------- input discovery
def find_scenes(root: Path, workdir: Path) -> dict:
    """Return {scene_id: {'sensor': str, 'SR_B5': Path, ..., 'QA_PIXEL': Path}}."""
    for tar in sorted(root.rglob("*.tar")):
        target = workdir / tar.stem
        if not target.exists():
            print(f"extracting {tar.name} ...")
            target.mkdir(parents=True)
            with tarfile.open(tar) as tf:
                tf.extractall(target, filter="data")
    scenes: dict = {}
    for search_root in (root, workdir):
        for f in search_root.rglob("*"):
            m = FILE_RE.match(f.name) if f.is_file() else None
            if m and m["sensor"].upper() in SENSOR_BANDS:
                s = scenes.setdefault(m["id"].upper(), {"sensor": m["sensor"].upper()})
                s[m["band"].upper()] = f
    complete = {}
    for sid, s in scenes.items():
        red, nir, swir = SENSOR_BANDS[s["sensor"]]
        need = [f"SR_B{red}", f"SR_B{nir}", f"SR_B{swir}", "QA_PIXEL"]
        missing = [b for b in need if b not in s]
        if missing:
            print(f"skipping {sid}: missing {', '.join(missing)}", file=sys.stderr)
        else:
            complete[sid] = s
    return complete


# ----------------------------------------------------------------------------- boundary
def _norm(text) -> str:
    return re.sub(r"[^a-z]", "", unicodedata.normalize("NFKD", str(text)).encode("ascii", "ignore").decode().lower())


def fetch_boundary(dest: Path) -> Path:
    """Download the Iran ADM1 (province) layer from geoBoundaries (CC BY 4.0)."""
    try:
        meta = requests.get("https://www.geoboundaries.org/api/current/gbOpen/IRN/ADM1/", timeout=60)
        meta.raise_for_status()
        meta = meta.json()
        meta = meta[0] if isinstance(meta, list) else meta
        data = requests.get(meta["gjDownloadURL"], timeout=300)
        data.raise_for_status()
    except (requests.RequestException, KeyError, ValueError) as exc:
        raise SystemExit(f"Could not download the province boundary ({type(exc).__name__}). "
                         "Download Mazandaran from GADM / geoBoundaries / Natural Earth and pass it with --boundary.")
    dest.write_bytes(data.content)
    return dest


def load_boundary(path: Path, name: str, crs):
    gdf = gpd.read_file(path)
    if name:
        wanted = _norm(name)
        hit = gdf.drop(columns="geometry").apply(
            lambda row: any(isinstance(v, str) and wanted in _norm(v) for v in row), axis=1)
        if not hit.any():
            raise SystemExit(f"No feature in {path} matches {name!r}. Columns: {list(gdf.columns)}")
        gdf = gdf[hit]
    if gdf.crs is None:
        raise SystemExit(f"{path} has no CRS; add one (e.g. .prj) before use.")
    return gdf.to_crs(crs).geometry.union_all()


# ----------------------------------------------------------------------------- grid + scene reading
def make_grid(geom, res: float):
    """Common grid aligned to the Landsat pixel lattice (corners at res/2 + k*res)."""
    minx, miny, maxx, maxy = geom.bounds
    half = res / 2
    minx = np.floor((minx - half) / res) * res + half
    maxy = np.ceil((maxy - half) / res) * res + half
    width = int(np.ceil((maxx - minx) / res))
    height = int(np.ceil((maxy - miny) / res))
    return from_origin(minx, maxy, res, res), height, width


def read_strip(src, transform, crs, rows, width, fill):
    """Resample band 1 of an open raster onto a strip of the common grid; `fill` where there is no data."""
    dst = np.full((rows, width), fill, dtype=np.uint16)
    reproject(rasterio.band(src, 1), dst, dst_transform=transform, dst_crs=crs,
              resampling=Resampling.nearest, dst_nodata=fill)
    return dst


def accumulate_scene(scene, crs, transform, height, width, inside, ndbi_sum, ndvi_sum, count):
    """Add one scene's clear-sky NDBI / NDVI into the running sums. Returns clear-pixel count."""
    red_n, nir_n, swir_n = SENSOR_BANDS[scene["sensor"]]
    paths = {k: scene[k] for k in (f"SR_B{red_n}", f"SR_B{nir_n}", f"SR_B{swir_n}", "QA_PIXEL")}
    clear_total = 0
    srcs = {k: rasterio.open(p) for k, p in paths.items()}
    try:
        ref = srcs["QA_PIXEL"]
        l, b, r, t = transform_bounds(ref.crs, crs, *ref.bounds)
        gx0, gy0 = transform.c, transform.f
        gx1, gy1 = gx0 + width * transform.a, gy0 + height * transform.e
        if r < gx0 or l > gx1 or t < gy1 or b > gy0:
            return 0  # scene footprint does not touch the province grid
        for r0 in range(0, height, STRIP_ROWS):
            rows = min(STRIP_ROWS, height - r0)
            if not inside[r0:r0 + rows].any():
                continue
            tr = transform * Affine.translation(0, r0)
            red = read_strip(srcs[f"SR_B{red_n}"], tr, crs, rows, width, 0)
            nir = read_strip(srcs[f"SR_B{nir_n}"], tr, crs, rows, width, 0)
            swir = read_strip(srcs[f"SR_B{swir_n}"], tr, crs, rows, width, 0)
            qa = read_strip(srcs["QA_PIXEL"], tr, crs, rows, width, 1)  # 1 = fill bit
            ok = ((qa & QA_BAD_BITS) == 0) & (red > 0) & (nir > 0) & (swir > 0) & (inside[r0:r0 + rows] > 0)
            if not ok.any():
                continue
            red_f = red.astype("float32") * SR_SCALE + SR_OFFSET
            nir_f = nir.astype("float32") * SR_SCALE + SR_OFFSET
            swir_f = swir.astype("float32") * SR_SCALE + SR_OFFSET
            d_bi, d_vi = swir_f + nir_f, nir_f + red_f
            ok &= (d_bi > 0) & (d_vi > 0)
            with np.errstate(divide="ignore", invalid="ignore"):
                ndbi = np.where(ok, (swir_f - nir_f) / d_bi, 0).astype("float32")
                ndvi = np.where(ok, (nir_f - red_f) / d_vi, 0).astype("float32")
            sl = slice(r0, r0 + rows)
            ndbi_sum[sl] += ndbi
            ndvi_sum[sl] += ndvi
            count[sl] += ok.astype("int16")
            clear_total += int(ok.sum())
    finally:
        for s in srcs.values():
            s.close()
    return clear_total


# ----------------------------------------------------------------------------- outputs
def write_tif(path, array, transform, crs, dtype, nodata):
    profile = dict(driver="GTiff", height=array.shape[0], width=array.shape[1], count=1, dtype=dtype,
                   crs=crs, transform=transform, nodata=nodata, compress="deflate", tiled=True,
                   blockxsize=256, blockysize=256, BIGTIFF="IF_SAFER")
    if dtype == "float32":
        profile["predictor"] = 3
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(array.astype(dtype), 1)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scenes", required=True, type=Path, help="folder with Landsat C2 L2 scenes / .tar bundles")
    bg = ap.add_mutually_exclusive_group(required=True)
    bg.add_argument("--boundary", type=Path, help="Mazandaran polygon (shp / geojson / gpkg ...)")
    bg.add_argument("--fetch-boundary", action="store_true", help="download Iran provinces from geoBoundaries")
    ap.add_argument("--boundary-name", default="Mazandaran",
                    help="keep only features whose attributes contain this name; '' keeps all (default: Mazandaran)")
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--crs", default="EPSG:32639", help="processing / shapefile CRS (default UTM 39N)")
    ap.add_argument("--resolution", type=float, default=30.0)
    ap.add_argument("--threshold", type=float, default=0.0, help="built-up where NDBI > threshold (default 0)")
    ap.add_argument("--ndvi-max", type=float, default=None,
                    help="optional: also require NDVI < this value (e.g. 0.2) to suppress vegetation / paddy noise")
    ap.add_argument("--min-pixels", type=int, default=9, help="drop clumps smaller than this many pixels (default 9)")
    ap.add_argument("--min-obs", type=int, default=1, help="clear observations required per pixel (default 1)")
    a = ap.parse_args(argv)

    a.out.mkdir(parents=True, exist_ok=True)
    scenes = find_scenes(a.scenes, a.out / "_extracted")
    if not scenes:
        raise SystemExit(f"No complete Landsat C2 L2 scenes found under {a.scenes}")
    print(f"{len(scenes)} scene(s): " + ", ".join(sorted(scenes)))

    boundary = a.boundary
    if a.fetch_boundary:
        boundary = fetch_boundary(a.out / "iran_adm1.geojson")
    geom = load_boundary(boundary, a.boundary_name, a.crs)
    transform, height, width = make_grid(geom, a.resolution)
    inside = features.rasterize([(geom, 1)], out_shape=(height, width), transform=transform,
                                fill=0, dtype="uint8")
    print(f"grid {width} x {height} px @ {a.resolution:g} m, province area "
          f"{inside.sum() * a.resolution ** 2 / 1e6:,.0f} km2")

    ndbi_sum = np.zeros((height, width), "float32")
    ndvi_sum = np.zeros((height, width), "float32")
    count = np.zeros((height, width), "int16")
    used = {}
    for sid, scene in sorted(scenes.items()):
        n = accumulate_scene(scene, a.crs, transform, height, width, inside, ndbi_sum, ndvi_sum, count)
        used[sid] = n
        print(f"  {sid}: {n:,} clear px inside province" if n else f"  {sid}: no overlap / no clear px")

    valid = (count >= a.min_obs) & (inside > 0)
    if not valid.any():
        raise SystemExit("No clear observations inside the province; check scene coverage and cloud cover.")
    with np.errstate(divide="ignore", invalid="ignore"):
        ndbi = np.where(valid, ndbi_sum / np.maximum(count, 1), NODATA).astype("float32")
        ndvi = np.where(valid, ndvi_sum / np.maximum(count, 1), NODATA).astype("float32")
    del ndbi_sum, ndvi_sum

    builtup = valid & (ndbi > a.threshold)
    if a.ndvi_max is not None:
        builtup &= ndvi < a.ndvi_max
    builtup = features.sieve(builtup.astype("uint8"), size=a.min_pixels, connectivity=4).astype(bool)

    write_tif(a.out / "ndbi_mean.tif", ndbi, transform, a.crs, "float32", NODATA)
    write_tif(a.out / "ndvi_mean.tif", ndvi, transform, a.crs, "float32", NODATA)
    write_tif(a.out / "clear_obs_count.tif", count, transform, a.crs, "int16", 0)
    write_tif(a.out / "builtup_mask.tif", builtup.astype("uint8"), transform, a.crs, "uint8", 255)

    labels, n = ndimage.label(builtup, structure=ndimage.generate_binary_structure(2, 1))
    if n == 0:
        raise SystemExit("No built-up pixels at this threshold; try a lower --threshold.")
    ids = np.arange(1, n + 1)
    npix = np.bincount(labels.ravel(), minlength=n + 1)[1:]
    ndbi_mean = ndimage.mean(ndbi, labels, ids)
    ndvi_mean = ndimage.mean(ndvi, labels, ids)
    geoms = {int(v): shape(g) for g, v in features.shapes(
        labels.astype("int32"), mask=labels > 0, transform=transform, connectivity=4)}
    gdf = gpd.GeoDataFrame(
        {"ID": ids, "N_PIX": npix, "AREA_HA": np.round(npix * a.resolution ** 2 / 1e4, 3),
         "NDBI_MEAN": np.round(ndbi_mean, 4), "NDVI_MEAN": np.round(ndvi_mean, 4)},
        geometry=[geoms[i] for i in ids], crs=a.crs)

    tag = re.sub(r"\W", "", a.crs.lower())
    shp_main = a.out / f"mazandaran_builtup_ndbi_{tag}.shp"
    shp_wgs = a.out / "mazandaran_builtup_ndbi_wgs84.shp"
    gdf.to_file(shp_main, driver="ESRI Shapefile", encoding="UTF-8")
    gdf.to_crs("EPSG:4326").to_file(shp_wgs, driver="ESRI Shapefile", encoding="UTF-8")

    province_km2 = float(inside.sum()) * a.resolution ** 2 / 1e6
    built_km2 = float(builtup.sum()) * a.resolution ** 2 / 1e6
    summary = {
        "scenes": used, "ndbi_threshold": a.threshold, "ndvi_max": a.ndvi_max,
        "min_pixels": a.min_pixels, "min_obs": a.min_obs, "crs": a.crs,
        "province_km2": round(province_km2, 1), "clear_coverage_pct": round(100 * valid.sum() / inside.sum(), 2),
        "builtup_km2": round(built_km2, 2), "builtup_pct": round(100 * built_km2 / province_km2, 3),
        "polygons": int(n),
    }
    (a.out / "summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))
    print(f"wrote {shp_main}\nwrote {shp_wgs}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
