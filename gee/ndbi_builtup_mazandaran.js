/**
 * Built-up area extraction with NDBI – Mazandaran Province, Iran
 * ---------------------------------------------------------------
 * Platform : Google Earth Engine Code Editor (https://code.earthengine.google.com)
 * Data     : Sentinel-2 L2A Surface Reflectance (COPERNICUS/S2_SR_HARMONIZED)
 * Boundary : FAO GAUL 2015, level 1 (province) – "Mazandaran"
 * Output   : Built-up polygons exported to Google Drive as ESRI Shapefile (SHP)
 *            + optional GeoTIFFs of NDBI and the built-up mask.
 *
 * Index definitions
 *   NDBI  = (SWIR1 - NIR) / (SWIR1 + NIR)    -> (B11 - B8) / (B11 + B8)
 *   NDVI  = (NIR - RED)   / (NIR + RED)      -> (B8  - B4) / (B8  + B4)
 *   MNDWI = (GREEN - SWIR1)/(GREEN + SWIR1)  -> (B3  - B11)/(B3  + B11)
 *
 * Built-up rule (tunable below):
 *   NDBI > NDBI_THRESHOLD  AND  NDVI < NDVI_MAX  AND  MNDWI < MNDWI_MAX
 * NDVI/MNDWI conditions suppress the usual NDBI confusion with sparse
 * vegetation, bare soil and water (important along the Caspian coast and
 * the rice paddies of the Mazandaran lowlands).
 */

// ============================== PARAMETERS ==============================
var START_DATE      = '2024-04-01';
var END_DATE        = '2024-10-31';   // dry season -> fewer clouds, crops clearer
var MAX_CLOUD_PCT   = 30;             // scene-level cloud filter

var NDBI_THRESHOLD  = 0.0;            // NDBI > this is a built-up candidate
var NDVI_MAX        = 0.25;           // exclude vegetation
var MNDWI_MAX       = 0.0;            // exclude water

var MIN_PATCH_PIXELS = 10;            // remove patches smaller than N pixels
var ANALYSIS_SCALE  = 20;             // m; B11 native resolution is 20 m
var VECTOR_SCALE    = 20;             // m; raise to 30 if the export times out

var EXPORT_FOLDER   = 'GEE_Mazandaran';
var EXPORT_PREFIX   = 'Mazandaran_BuiltUp_NDBI_2024';
var EXPORT_RASTERS  = true;           // also export NDBI + mask GeoTIFFs

// ============================== STUDY AREA ==============================
var provinces = ee.FeatureCollection('FAO/GAUL/2015/level1')
  .filter(ee.Filter.eq('ADM0_NAME', 'Iran  (Islamic Republic of)')
    .or(ee.Filter.eq('ADM0_NAME', 'Iran (Islamic Republic of)')))
  .filter(ee.Filter.stringContains('ADM1_NAME', 'Mazandaran'));

print('Boundary features found (should be 1):', provinces.size());

var aoi = provinces.geometry();
Map.centerObject(aoi, 8);
Map.addLayer(ee.Image().paint(provinces, 0, 2), {palette: ['yellow']}, 'Mazandaran boundary');

// ============================== SENTINEL-2 ==============================
// Cloud / shadow / snow mask from the Scene Classification Layer (SCL).
function maskS2(img) {
  var scl = img.select('SCL');
  // 3 shadow, 8 cloud medium, 9 cloud high, 10 cirrus, 11 snow
  var mask = scl.neq(3).and(scl.neq(8)).and(scl.neq(9))
                .and(scl.neq(10)).and(scl.neq(11));
  return img.updateMask(mask)
            .select(['B3', 'B4', 'B8', 'B11'])
            .divide(10000)
            .copyProperties(img, ['system:time_start']);
}

var s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
  .filterBounds(aoi)
  .filterDate(START_DATE, END_DATE)
  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', MAX_CLOUD_PCT))
  .map(maskS2);

print('Sentinel-2 images used:', s2.size());

var composite = s2.median().clip(aoi);

Map.addLayer(composite, {bands: ['B4', 'B3', 'B3'], min: 0, max: 0.3}, 'S2 composite (approx. true colour)', false);
Map.addLayer(composite, {bands: ['B11', 'B8', 'B4'], min: 0, max: 0.4}, 'S2 false colour (SWIR/NIR/R)', false);

// ============================== INDICES ==============================
var ndbi  = composite.normalizedDifference(['B11', 'B8']).rename('NDBI');
var ndvi  = composite.normalizedDifference(['B8', 'B4']).rename('NDVI');
var mndwi = composite.normalizedDifference(['B3', 'B11']).rename('MNDWI');

Map.addLayer(ndbi, {min: -0.5, max: 0.3, palette: ['1a9641', 'ffffbf', 'd7191c']}, 'NDBI');
Map.addLayer(ndvi, {min: -0.2, max: 0.8, palette: ['white', 'green']}, 'NDVI', false);

// ============================== BUILT-UP MASK ==============================
var builtRaw = ndbi.gt(NDBI_THRESHOLD)
  .and(ndvi.lt(NDVI_MAX))
  .and(mndwi.lt(MNDWI_MAX));

// Light morphological smoothing + removal of tiny isolated patches.
var builtSmooth = builtRaw.focalMode({radius: 1, kernelType: 'square', units: 'pixels'});
var patchSize = builtSmooth.selfMask()
  .connectedPixelCount({maxSize: MIN_PATCH_PIXELS + 1, eightConnected: true});
var built = builtSmooth.selfMask()
  .updateMask(patchSize.gte(MIN_PATCH_PIXELS))
  .rename('built')
  .toByte()
  .clip(aoi);

Map.addLayer(built, {palette: ['red']}, 'Built-up (NDBI rule)');

// Built-up area statistics.
var builtAreaKm2 = ee.Image.pixelArea().divide(1e6).updateMask(built)
  .reduceRegion({
    reducer: ee.Reducer.sum(),
    geometry: aoi,
    scale: ANALYSIS_SCALE,
    maxPixels: 1e13,
    tileScale: 8
  }).get('area');
var aoiAreaKm2 = aoi.area(100).divide(1e6);

print('Province area (km²):', aoiAreaKm2);
print('Built-up area (km²):', builtAreaKm2);
print('Built-up share (%):', ee.Number(builtAreaKm2).divide(aoiAreaKm2).multiply(100));

// ============================== VECTORISE ==============================
var builtPolygons = built.reduceToVectors({
  geometry: aoi,
  scale: VECTOR_SCALE,
  geometryType: 'polygon',
  eightConnected: true,
  labelProperty: 'built',
  maxPixels: 1e13,
  tileScale: 16,
  bestEffort: false
}).map(function (f) {
  // Shapefile field names are limited to 10 characters.
  var area = f.geometry().area(1);
  return f.set({
    class:   'Built-up',
    area_m2: area,
    area_ha: area.divide(1e4),
    province: 'Mazandaran',
    period:  START_DATE + '/' + END_DATE
  });
});

Map.addLayer(builtPolygons.limit(2000), {color: 'ff00ff'}, 'Built-up polygons (preview, first 2000)', false);

// ============================== EXPORTS ==============================
// 1) Built-up polygons -> Shapefile (.shp/.shx/.dbf/.prj in a .zip on Drive)
Export.table.toDrive({
  collection: builtPolygons,
  description: EXPORT_PREFIX + '_SHP',
  folder: EXPORT_FOLDER,
  fileNamePrefix: EXPORT_PREFIX,
  fileFormat: 'SHP',
  selectors: ['class', 'area_m2', 'area_ha', 'province', 'period']
});

// 2) Province boundary -> Shapefile (handy for mapping in QGIS/ArcGIS)
Export.table.toDrive({
  collection: provinces.select(['ADM0_NAME', 'ADM1_NAME']),
  description: 'Mazandaran_Boundary_SHP',
  folder: EXPORT_FOLDER,
  fileNamePrefix: 'Mazandaran_Boundary',
  fileFormat: 'SHP'
});

// 3) Optional rasters -> GeoTIFF
if (EXPORT_RASTERS) {
  Export.image.toDrive({
    image: ndbi.float(),
    description: EXPORT_PREFIX + '_NDBI_TIF',
    folder: EXPORT_FOLDER,
    fileNamePrefix: EXPORT_PREFIX + '_NDBI',
    region: aoi,
    scale: ANALYSIS_SCALE,
    crs: 'EPSG:32639',          // UTM zone 39N covers Mazandaran
    maxPixels: 1e13
  });

  Export.image.toDrive({
    image: built.unmask(0).toByte(),
    description: EXPORT_PREFIX + '_Mask_TIF',
    folder: EXPORT_FOLDER,
    fileNamePrefix: EXPORT_PREFIX + '_Mask',
    region: aoi,
    scale: ANALYSIS_SCALE,
    crs: 'EPSG:32639',
    maxPixels: 1e13
  });
}

// ============================== LEGEND ==============================
var legend = ui.Panel({style: {position: 'bottom-left', padding: '8px 12px'}});
legend.add(ui.Label('Mazandaran – Built-up (NDBI)', {fontWeight: 'bold'}));
function legendRow(color, name) {
  return ui.Panel([
    ui.Label('', {backgroundColor: color, padding: '8px', margin: '0 6px 0 0'}),
    ui.Label(name, {margin: '0'})
  ], ui.Panel.Layout.Flow('horizontal'));
}
legend.add(legendRow('red', 'Built-up'));
legend.add(legendRow('yellow', 'Province boundary'));
Map.add(legend);
