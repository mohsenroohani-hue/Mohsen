/*******************************************************************************
 * Flood susceptibility modelling for Mazandaran Province, Iran
 * Multi-model CONSENSUS (ensemble) in Google Earth Engine - Code Editor script
 *
 * STATUS: written without Earth Engine access. NOT yet executed. Run it in the
 * Code Editor (https://code.earthengine.google.com) and work through the
 * "first-run checks" in README.md before trusting any output.
 *
 * Workflow
 *   1. AOI                : FAO GAUL level-1 boundary of Mazandaran
 *   2. Flood inventory    : Global Flood Database (MODIS, 2000-2018)  or
 *                           Sentinel-1 SAR change detection for events you list
 *   3. Criteria (6)       : Snow (MODIS), Rain (CHIRPS), River (MERIT Hydro),
 *                           NDVI (USGS Landsat 8/9), Slope + Topography (USGS SRTM)
 *   4. Samples            : balanced flood / non-flood points, spatial-block
 *                           train/test split (reduces optimistic bias of a
 *                           purely random split)
 *   5. Models             : Random Forest, Gradient Tree Boost, SVM (RBF), CART
 *   6. CONSENSUS          : AUC-weighted mean probability + model-agreement
 *                           count + inter-model spread (uncertainty)
 *   7. Outputs            : map layers, 5-class susceptibility, Drive exports
 ******************************************************************************/

// ============================== 0. PARAMETERS ================================
var CFG = {
  inventory: 'GFD',            // 'GFD' (default) | 'S1'
  // Used only when inventory === 'S1'. Fill with real events; dates are YYYY-MM-DD.
  // Example shape: {refStart:'2019-02-01', refEnd:'2019-03-01', start:'2019-03-20', end:'2019-04-05'}
  s1Events: [],
  s1VvThreshDb: -16,           // open-water backscatter threshold (heuristic)
  s1DiffThreshDb: -3,          // after-before decrease threshold (heuristic)
  s1MinFraction: 0.2,          // share of 10 m flooded pixels inside a 250 m cell

  sampleScale: 250,            // m, matches the Global Flood Database grid
  mapScale: 100,               // m, resolution of exported susceptibility maps
  nonFloodBufferM: 1000,       // non-flood points must be > this far from flood
  maxPointsPerClass: 2000,
  blockDeg: 0.1,               // spatial-block size for the hold-out split (~10 km)
  testFraction: 0.3,
  seed: 42,

  streamUpaKm2: 5,             // MERIT upstream-area threshold defining "streams"
  rainYears: [2000, 2023],
  snowDates: ['2015-01-01', '2024-01-01'],   // MODIS daily snow cover period
  ndviYears: ['2019-01-01', '2024-12-31'],

  // Predictors to leave out after inspecting the VIF table (VIF > 5-10), e.g. ['elevation']
  drop: [],

  highVoteProb: 0.5,           // a model "votes high" above this probability
  exportFolder: 'GEE_flood_Mazandaran'
};

// ================================= 1. AOI ====================================
var aoiFc = ee.FeatureCollection('FAO/GAUL/2015/level1')
  .filter(ee.Filter.stringContains('ADM0_NAME', 'Iran'))
  .filter(ee.Filter.stringContains('ADM1_NAME', 'Mazandaran'));
print('AOI features found (expect 1):', aoiFc.size());
var aoi = aoiFc.geometry();
Map.centerObject(aoi, 8);
Map.addLayer(ee.Image().byte().paint(aoiFc, 1, 2), {palette: 'black'}, 'Mazandaran', true);

// ======================= 2. CONDITIONING FACTORS =============================
// --- SLOPE + TOPOGRAPHY: USGS SRTM 1 arc-second --------------------------------
var dem = ee.Image('USGS/SRTMGL1_003').select('elevation');
var slope = ee.Terrain.slope(dem).rename('slope');                  // degrees
var curvature = dem.convolve(ee.Kernel.laplacian8({normalize: false}))
  .rename('curvature');                                              // Laplacian curvature (approx.)

// --- RIVER (+ topographic wetness): MERIT Hydro (90 m) -------------------------
var merit = ee.Image('MERIT/Hydro/v1_0_1');
var upa = merit.select('upa');                                       // upstream area, km2
var hand = merit.select('hnd').rename('hand');                       // height above nearest drainage, m
var tanB = slope.multiply(Math.PI / 180).tan().max(0.001);
var sca = upa.multiply(1e6).divide(90);                              // specific catchment area, m2/m
var twi = sca.divide(tanB).max(1).log().rename('twi');               // topographic wetness index (approx.)
var streams = upa.gt(CFG.streamUpaKm2).selfMask();
var distRiver = streams.unmask(0).fastDistanceTransform(512)         // squared pixel distance
  .sqrt().multiply(ee.Image.pixelArea().sqrt())                      // -> metres
  .rename('dist_river');
var streamDens = streams.unmask(0)
  .reduceNeighborhood({reducer: ee.Reducer.mean(), kernel: ee.Kernel.circle({radius: 2000, units: 'meters'})})
  .rename('stream_dens');

// --- SNOW: MODIS Terra daily snow cover (MOD10A1 v061) -------------------------
// Share of valid (non-cloud, non-flag) days with NDSI snow cover > 40.
var snowFreq = ee.ImageCollection('MODIS/061/MOD10A1')
  .filterDate(CFG.snowDates[0], CFG.snowDates[1]).select('NDSI_Snow_Cover')
  .map(function (img) { return img.gt(40).updateMask(img.lte(100)); })   // >100 = flag values
  .mean().rename('snow_freq');

// --- RAIN: CHIRPS daily ---------------------------------------------------------
var y0 = CFG.rainYears[0], y1 = CFG.rainYears[1];
var chirps = ee.ImageCollection('UCSB-CHG/CHIRPS/DAILY')
  .filterDate(y0 + '-01-01', (y1 + 1) + '-01-01').select('precipitation');
var rainMean = chirps.sum().divide(y1 - y0 + 1).rename('rain_mean');
var rainAnnMax = ee.ImageCollection(ee.List.sequence(y0, y1).map(function (y) {
  return chirps.filter(ee.Filter.calendarRange(y, y, 'year')).max();
})).mean().rename('rain_ann_max');                                   // mean annual-maximum daily rainfall

// --- NDVI: USGS Landsat 8/9 Collection 2 Level 2 -------------------------------
function landsatNdvi(img) {
  var qa = img.select('QA_PIXEL');
  var clear = qa.bitwiseAnd(1 << 1).eq(0)      // dilated cloud
    .and(qa.bitwiseAnd(1 << 3).eq(0))          // cloud
    .and(qa.bitwiseAnd(1 << 4).eq(0));         // cloud shadow
  var nir = img.select('SR_B5').multiply(0.0000275).add(-0.2);
  var red = img.select('SR_B4').multiply(0.0000275).add(-0.2);
  return nir.subtract(red).divide(nir.add(red)).rename('ndvi').updateMask(clear);
}
var ndvi = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2')
  .merge(ee.ImageCollection('LANDSAT/LC09/C02/T1_L2'))
  .filterBounds(aoi).filterDate(CFG.ndviYears[0], CFG.ndviYears[1])
  .map(landsatNdvi).median().rename('ndvi');

// --- Water mask (NOT a predictor): excluded from sampling and from the final map
var lc = ee.ImageCollection('ESA/WorldCover/v200').first().select('Map');
var gsw = ee.Image('JRC/GSW1_4/GlobalSurfaceWater').select('occurrence').unmask(0);
var permWater = gsw.gt(90).or(lc.eq(80));
var notWater = permWater.not();

// Predictors = the six requested criteria (some have more than one band):
//   Snow: snow_freq | Rain: rain_mean, rain_ann_max | River: dist_river, stream_dens, hand
//   NDVI: ndvi | Slope: slope | Topography: elevation, curvature, twi
var allBands = ['snow_freq', 'rain_mean', 'rain_ann_max', 'dist_river', 'stream_dens', 'hand',
  'ndvi', 'slope', 'elevation', 'curvature', 'twi'];
var bands = allBands.filter(function (b) { return CFG.drop.indexOf(b) === -1; });

var predictors = ee.Image.cat([
  snowFreq, rainMean, rainAnnMax, distRiver, streamDens, hand,
  ndvi, slope, dem.rename('elevation'), curvature, twi
]).select(bands).toFloat();

// Self-check: distance to river must be ~0 on stream pixels.
print('Check dist_river on stream pixels (expect ~0):',
  distRiver.updateMask(streams).reduceRegion({
    reducer: ee.Reducer.mean(), geometry: aoi, scale: 500, maxPixels: 1e9, bestEffort: true, tileScale: 4}));

// Standardise (needed by SVM; harmless for tree models).
var stats = predictors.reduceRegion({
  reducer: ee.Reducer.mean().combine({reducer2: ee.Reducer.stdDev(), sharedInputs: true}),
  geometry: aoi, scale: 500, maxPixels: 1e9, bestEffort: true, tileScale: 4
});
var meanImg = ee.Dictionary.fromLists(bands, bands.map(function (b) { return stats.get(b + '_mean'); })).toImage(bands);
var sdImg = ee.Dictionary.fromLists(bands, bands.map(function (b) { return stats.get(b + '_stdDev'); })).toImage(bands);
var predNorm = predictors.subtract(meanImg).divide(sdImg.max(1e-6));

// ========================= 3. FLOOD INVENTORY ================================
var flood;   // 1 = flooded, 0 = not; fixed 250 m grid
if (CFG.inventory === 'GFD') {
  var gfd = ee.ImageCollection('GLOBAL_FLOOD_DB/MODIS_EVENTS/V1').filterBounds(aoi);
  print('Global Flood Database events intersecting Mazandaran:', gfd.size());
  var gfdFlooded = gfd.select('flooded').max().unmask(0).eq(1);
  var gfdPerm = gfd.select('jrc_perm_water').max().unmask(0).eq(1);
  flood = gfdFlooded.and(gfdPerm.not()).rename('flood');
} else if (CFG.inventory === 'S1') {
  if (CFG.s1Events.length === 0) {
    throw new Error("inventory 'S1' needs at least one entry in CFG.s1Events.");
  }
  var s1col = ee.ImageCollection('COPERNICUS/S1_GRD').filterBounds(aoi)
    .filter(ee.Filter.eq('instrumentMode', 'IW'))
    .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))
    .select('VV');
  var perEvent = CFG.s1Events.map(function (ev) {
    var before = s1col.filterDate(ev.refStart, ev.refEnd).mean().focalMedian(30, 'circle', 'meters');
    var after = s1col.filterDate(ev.start, ev.end).mean().focalMedian(30, 'circle', 'meters');
    return after.lt(CFG.s1VvThreshDb).and(after.subtract(before).lt(CFG.s1DiffThreshDb))
      .updateMask(hand.lt(15)).updateMask(slope.lt(5)).updateMask(notWater)
      .unmask(0).rename('flood');
  });
  flood = ee.ImageCollection.fromImages(perEvent).max()
    .reproject({crs: 'EPSG:4326', scale: 10})
    .reduceResolution({reducer: ee.Reducer.mean(), maxPixels: 1024})
    .gte(CFG.s1MinFraction).rename('flood');
} else {
  throw new Error("CFG.inventory must be 'GFD' or 'S1'.");
}
flood = flood.reproject({crs: 'EPSG:4326', scale: CFG.sampleScale}).toInt();
Map.addLayer(flood.selfMask().clip(aoi), {palette: 'blue'}, 'Flood inventory', false);
print('Flooded cells in AOI (' + CFG.sampleScale + ' m):',
  flood.reduceRegion({reducer: ee.Reducer.sum(), geometry: aoi, scale: CFG.sampleScale,
    maxPixels: 1e9, tileScale: 4}).get('flood'));

// ============================ 4. SAMPLING ====================================
var nearFlood = flood.focalMax({radius: CFG.nonFloodBufferM, units: 'meters'});
var label = flood.updateMask(flood.eq(1).or(nearFlood.eq(0))).updateMask(notWater).rename('flood');

var sampled = label.addBands(predNorm).addBands(ee.Image.pixelLonLat()).stratifiedSample({
  numPoints: 0, classBand: 'flood', region: aoi, scale: CFG.sampleScale,
  classValues: [0, 1], classPoints: [CFG.maxPointsPerClass, CFG.maxPointsPerClass],
  seed: CFG.seed, tileScale: 4, geometries: true
});
var pos = sampled.filter(ee.Filter.eq('flood', 1));
var neg = sampled.filter(ee.Filter.eq('flood', 0))
  .randomColumn('r', CFG.seed).sort('r').limit(pos.size());      // balance 1:1
var pts = pos.merge(neg);
print('Flood / non-flood points after balancing:', pos.size(), neg.size());

// Spatial-block hold-out: every ~10 km block is wholly train or wholly test.
pts = pts.map(function (f) {
  var bx = ee.Number(f.get('longitude')).divide(CFG.blockDeg).floor();
  var by = ee.Number(f.get('latitude')).divide(CFG.blockDeg).floor();
  var u = bx.multiply(12.9898).add(by.multiply(78.233)).sin().multiply(43758.5453).abs().mod(1);
  return f.set('u', u);
});
var train = pts.filter(ee.Filter.gte('u', CFG.testFraction));
var test = pts.filter(ee.Filter.lt('u', CFG.testFraction));
print('Train / test points:', train.size(), test.size());

// ---- Multicollinearity: correlation matrix and VIF on the training points ----
var covArr = ee.Array(train.reduceColumns({
  reducer: ee.Reducer.covariance(), selectors: bands
}).get('array'));
var sd = covArr.matrixDiagonal().sqrt();
var corr = covArr.divide(sd.matrixMultiply(sd.transpose()));
var vif = corr.matrixInverse().matrixDiagonal().project([0]);
print('VIF per predictor (drop > 5-10 via CFG.drop):',
  ee.Dictionary.fromLists(bands, vif.toList()));

// ============================= 5. MODELS =====================================
// All learners are fitted in REGRESSION mode on the 0/1 label, so each returns a
// flood-likelihood score in [0, 1] that can be averaged across models.
var learners = {
  rf: ee.Classifier.smileRandomForest({numberOfTrees: 500, minLeafPopulation: 2, bagFraction: 0.632, seed: CFG.seed}),
  gbt: ee.Classifier.smileGradientTreeBoost({numberOfTrees: 300, shrinkage: 0.05, samplingRate: 0.7,
    maxNodes: 20, loss: 'LeastSquares', seed: CFG.seed}),
  svm: ee.Classifier.libsvm({svmType: 'EPSILON_SVR', kernelType: 'RBF', gamma: 1 / bands.length, cost: 10}),
  cart: ee.Classifier.smileCart({maxNodes: 40, minLeafPopulation: 5})
};
var names = Object.keys(learners);
var models = {};
names.forEach(function (k) {
  models[k] = learners[k].setOutputMode('REGRESSION')
    .train({features: train, classProperty: 'flood', inputProperties: bands});
});

print('Random Forest variable importance:', ee.Dictionary(models.rf.explain().get('importance')));

// ============================ 6. VALIDATION ==================================
var scored = test;
names.forEach(function (k) {
  scored = scored.classify(models[k], 'p_' + k).map(function (f) {
    return f.set('p_' + k, ee.Number(f.get('p_' + k)).max(0).min(1));
  });
});

function aucOf(fc, prop) {
  var P = fc.filter(ee.Filter.eq('flood', 1)), N = fc.filter(ee.Filter.eq('flood', 0));
  var nP = P.size(), nN = N.size();
  var ts = ee.List.sequence(0, 1.01, 0.01);
  var roc = ts.map(function (t) {
    t = ee.Number(t);
    return ee.List([
      N.filter(ee.Filter.gte(prop, t)).size().divide(nN),          // FPR
      P.filter(ee.Filter.gte(prop, t)).size().divide(nP)           // TPR
    ]);
  });
  var area = ee.List.sequence(0, ts.size().subtract(2)).map(function (i) {
    i = ee.Number(i);
    var a = ee.List(roc.get(i)), b = ee.List(roc.get(i.add(1)));
    return ee.Number(a.get(0)).subtract(ee.Number(b.get(0)))
      .multiply(ee.Number(a.get(1)).add(ee.Number(b.get(1)))).divide(2);
  });
  return ee.Number(area.reduce(ee.Reducer.sum()));
}

var aucs = {};
names.forEach(function (k) { aucs[k] = aucOf(scored, 'p_' + k); });

// AUC-weighted consensus: weight = max(AUC - 0.5, 0), normalised to sum to 1.
var rawW = names.map(function (k) { return ee.Number(aucs[k]).subtract(0.5).max(0); });
var wSum = ee.Number(rawW.reduce(function (a, b) { return ee.Number(a).add(b); }, 0)).max(1e-6);
var weights = {};
names.forEach(function (k, i) { weights[k] = rawW[i].divide(wSum); });

scored = scored.map(function (f) {
  var s = ee.Number(0);
  names.forEach(function (k) { s = s.add(ee.Number(f.get('p_' + k)).multiply(weights[k])); });
  return f.set('p_consensus', s);
});
var aucConsensus = aucOf(scored, 'p_consensus');

var perfDict = {};
names.forEach(function (k) { perfDict['AUC_' + k] = aucs[k]; perfDict['w_' + k] = weights[k]; });
perfDict.AUC_consensus = aucConsensus;
print('Spatial-block hold-out performance (AUC) and consensus weights:', ee.Dictionary(perfDict));

// ===================== 7. SUSCEPTIBILITY MAPS (CONSENSUS) ====================
var probImgs = names.map(function (k) {
  return predNorm.classify(models[k]).max(0).min(1).rename('p_' + k);
});
var consensus = ee.Image(0);
names.forEach(function (k, i) { consensus = consensus.add(probImgs[i].multiply(weights[k])); });
consensus = consensus.rename('consensus_prob').updateMask(notWater);

var allP = ee.Image.cat(probImgs);
var agreement = allP.gt(CFG.highVoteProb).reduce(ee.Reducer.sum())
  .rename('models_high').updateMask(notWater);                       // 0..N models voting "high"
var spread = allP.reduce(ee.Reducer.stdDev()).rename('model_sd').updateMask(notWater);

// Equal-interval classes on a balanced-sample probability: treat as RELATIVE ranking.
var suscClass = ee.Image(1).where(consensus.gt(0.2), 2).where(consensus.gt(0.4), 3)
  .where(consensus.gt(0.6), 4).where(consensus.gt(0.8), 5)
  .updateMask(consensus.mask()).rename('susceptibility_class');

var pal = ['1a9641', 'a6d96a', 'ffffbf', 'fdae61', 'd7191c'];
Map.addLayer(consensus.clip(aoi), {min: 0, max: 1, palette: pal}, 'Consensus flood probability');
Map.addLayer(suscClass.clip(aoi), {min: 1, max: 5, palette: pal}, 'Susceptibility class (1 very low - 5 very high)', false);
Map.addLayer(agreement.clip(aoi), {min: 0, max: names.length, palette: ['ffffff', '9ecae1', '08519c']},
  'Number of models voting high', false);
Map.addLayer(spread.clip(aoi), {min: 0, max: 0.35, palette: ['ffffff', 'fdae6b', '7f2704']},
  'Inter-model SD (uncertainty)', false);

// Area per class
print('Area per susceptibility class (km2):', ee.Image.pixelArea().divide(1e6).addBands(suscClass)
  .reduceRegion({reducer: ee.Reducer.sum().group({groupField: 1, groupName: 'class'}),
    geometry: aoi, scale: 250, maxPixels: 1e10, bestEffort: true, tileScale: 4}));

// ================================ 8. EXPORTS =================================
function exportImg(img, name) {
  Export.image.toDrive({image: img.toFloat().clip(aoi), description: name, folder: CFG.exportFolder,
    fileNamePrefix: name, region: aoi, scale: CFG.mapScale, crs: 'EPSG:4326', maxPixels: 1e10});
}
exportImg(consensus, 'Mazandaran_flood_consensus_prob');
exportImg(suscClass, 'Mazandaran_flood_susceptibility_class');
exportImg(agreement, 'Mazandaran_flood_models_high');
exportImg(spread, 'Mazandaran_flood_model_sd');
Export.table.toDrive({collection: scored.select(['flood', 'u'].concat(names.map(function (k) { return 'p_' + k; }), ['p_consensus'])),
  description: 'Mazandaran_flood_test_scores', folder: CFG.exportFolder, fileFormat: 'CSV'});
Export.table.toDrive({collection: pts, description: 'Mazandaran_flood_sample_points',
  folder: CFG.exportFolder, fileFormat: 'CSV'});
