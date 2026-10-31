# Mohsen

## Built-up areas of Mazandaran (Iran) from NDBI — USGS Landsat → Shapefile

`ndbi_mazandaran.py` turns USGS Landsat Collection 2 Level-2 surface-reflectance scenes into a
province-wide **NDBI** (Normalized Difference Built-up Index) layer and exports the built-up area as an
**ESRI Shapefile**.

```
NDBI = (SWIR1 - NIR) / (SWIR1 + NIR)      Landsat 8/9: (B6 - B5)/(B6 + B5)    Landsat 4-7: (B5 - B4)/(B5 + B4)
```

### 1. Get the data from USGS EarthExplorer
1. Sign in at <https://earthexplorer.usgs.gov> (free USGS/ERS account).
2. Area of interest: the Mazandaran boundary. Date range: one consistent season (see caveats). Additional
   Criteria: land cloud cover, e.g. < 20 %.
3. Data set: *Landsat → Landsat Collection 2 Level-2 → Landsat 8-9 OLI/TIRS C2 L2* (Landsat 4-7 C2 L2 also works).
4. Download the **Product Bundle** (`.tar`) of every scene touching the province, or at least `SR_B4`, `SR_B5`,
   `SR_B6` and `QA_PIXEL` of each. Put them all in one folder (e.g. `data/landsat/`); `.tar` files are unpacked
   automatically.
5. A Mazandaran polygon (GADM, geoBoundaries or Natural Earth, level ADM1) — or let the script try
   `--fetch-boundary`.

### 2. Run
```bash
pip install -r requirements.txt
python ndbi_mazandaran.py --scenes data/landsat --boundary data/mazandaran.shp --out out
```
Useful options: `--threshold 0` (built-up where NDBI > value), `--ndvi-max 0.2` (also require low NDVI),
`--min-pixels 9` (drop clumps smaller than this), `--min-obs 1`, `--crs EPSG:32639`, `--resolution 30`,
`--boundary-name Mazandaran` (pick the province out of a multi-province file).

### Outputs (`out/`)
| File | Content |
|---|---|
| `mazandaran_builtup_ndbi_epsg32639.shp` | built-up polygons, UTM 39N (fields `ID, N_PIX, AREA_HA, NDBI_MEAN, NDVI_MEAN`) |
| `mazandaran_builtup_ndbi_wgs84.shp` | same polygons in WGS84 |
| `ndbi_mean.tif`, `ndvi_mean.tif` | per-pixel mean of all clear observations (nodata −9999) |
| `builtup_mask.tif`, `clear_obs_count.tif` | classification mask and number of clear scenes per pixel |
| `summary.json` | scenes used, clear coverage, built-up km² and % of province |

How it works: every scene is resampled (nearest neighbour) onto one 30 m UTM 39N grid, so scenes from
different paths/rows and UTM zones (Mazandaran straddles the 39N/40N boundary) combine; `QA_PIXEL`
masks fill, cloud, dilated cloud, cirrus, cloud shadow and snow; the mean of the clear NDBI values is
thresholded, small clumps are removed, and the mask is polygonised.

### Caveats
* **NDBI alone over-detects built-up land**: bare/fallow soil, dry fields and sand give positive NDBI too,
  while the humid, often cloudy Caspian lowlands make clear scenes scarce. Use scenes from one season, check
  `clear_obs_count.tif`, and consider `--ndvi-max`. The result is a 30 m *built-up proxy*, not building
  footprints, and has not been validated against reference data.
* Polygons are pixel-aligned (stair-stepped) and holes smaller than `--min-pixels` are filled by the sieve.

### Status
Tested end to end only on a **synthetic** two-scene dataset (two UTM zones, `.tar` input, cloud masking,
sieve, name filtering): it reproduced the known ground truth. It has **not** yet been run on real
USGS imagery, and `--fetch-boundary` (geoBoundaries download) is untested — the sandbox this was written
in could not reach USGS, geoBoundaries or GADM.
