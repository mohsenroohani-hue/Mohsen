# Mohsen

## Built-up area (NDBI) – Mazandaran, Iran – Google Earth Engine → Shapefile

Script: [`gee/ndbi_builtup_mazandaran.js`](gee/ndbi_builtup_mazandaran.js)

Maps built-up land in Mazandaran Province with the Normalized Difference
Built-up Index (NDBI) from Sentinel-2. It then turns the built-up mask into
polygons and exports them as an **ESRI Shapefile (SHP)**.

### How to run
1. Open the GEE Code Editor: https://code.earthengine.google.com
2. Create a new script and paste in the contents of `gee/ndbi_builtup_mazandaran.js`.
3. Click **Run**. The map shows the boundary, NDBI, and the built-up layer.
   The Console prints the image count and the built-up area in km² and %.
4. Open the **Tasks** tab and click **RUN** on:
   - `Mazandaran_BuiltUp_NDBI_2024_SHP`: built-up polygons (`.shp/.shx/.dbf/.prj`, zipped)
   - `Mazandaran_Boundary_SHP`: province boundary
   - `..._NDBI_TIF` / `..._Mask_TIF`: optional GeoTIFFs (UTM 39N, 20 m)
5. The files are saved to the `GEE_Mazandaran` folder in your Google Drive. Open them in QGIS or ArcGIS.

### Method
| Step | Detail |
|---|---|
| Data | Sentinel-2 L2A `COPERNICUS/S2_SR_HARMONIZED`, Apr–Oct 2024, scenes < 30 % cloud |
| Masking | Removes cloud, shadow, cirrus and snow using SCL |
| Composite | Median |
| NDBI | `(B11 − B8) / (B11 + B8)` |
| Built-up rule | `NDBI > 0` **and** `NDVI < 0.25` **and** `MNDWI < 0` |
| Cleanup | 3×3 focal mode, then removes patches smaller than 10 pixels |
| Vectorise | `reduceToVectors` at 20 m |
| SHP fields | `class`, `area_m2`, `area_ha`, `province`, `period` |

On its own, NDBI often mistakes bare soil, fallow or harvested rice paddies,
and wet surfaces for built-up land. The NDVI and MNDWI conditions reduce these
errors. Tune the parameters at the top of the script (`NDBI_THRESHOLD`,
`NDVI_MAX`, dates, `MIN_PATCH_PIXELS`). For a quick check, compare the result
with ESA WorldCover (class 50) or Google Dynamic World.

If the SHP export runs out of memory or time, set `VECTOR_SCALE` to `30`, or
raise `MIN_PATCH_PIXELS`.
