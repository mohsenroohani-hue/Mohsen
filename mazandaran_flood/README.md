# Flood susceptibility – Mazandaran, Iran (GEE, multi-model consensus)

`gee_flood_susceptibility.js` is a Google Earth Engine Code Editor script. It builds a
flood-susceptibility map for Mazandaran Province from USGS and other GEE-hosted data, using an
ensemble ("consensus") of four machine-learning models.

## Status – read this first

| Item | State |
|---|---|
| Script syntax | Checked with `node --check`. |
| Client-side JS logic | Smoke-tested against a stub of the `ee` API (catches undefined names, bad array handling). |
| **Execution in Earth Engine** | **Not done.** No EE client or credentials were available where this was written. No map, AUC, or flood count has been produced. |
| **Literature grounding** | **Not done.** The Consensus paper-search tool hit its free-usage limit (resets 1 Dec). The six criteria are the ones you specified; the dataset and band choices for each are mine and have no citations. |
| Dataset ids and API usage | Being checked against the official GEE docs; see the note at the end of this file once that is done. |

## How to run

1. Open <https://code.earthengine.google.com>, paste the script, press **Run**.
2. Work through the first-run checks below.
3. Start the exports in the **Tasks** tab. Outputs go to Drive folder `GEE_flood_Mazandaran`.

## Criteria (your six: snow, rain, river, NDVI, slope, topography)

All data come from GEE; SRTM and Landsat are USGS products.

| Criterion | Band(s) | Dataset (GEE id) | Note |
|---|---|---|---|
| Snow | `snow_freq` | `MODIS/061/MOD10A1` (2015–2023) | Share of valid days with NDSI snow cover > 40. |
| Rain | `rain_mean`, `rain_ann_max` | `UCSB-CHG/CHIRPS/DAILY` (2000–2023) | Mean annual total and mean annual maximum daily rain; ~5 km native. |
| River | `dist_river`, `stream_dens`, `hand` | `MERIT/Hydro/v1_0_1` | Streams = upstream area > 5 km² (`CFG.streamUpaKm2`). HAND = height above nearest drainage. |
| NDVI | `ndvi` | `LANDSAT/LC08/C02/T1_L2` + `LC09` (USGS), 2019–2024 median | Cloud-masked with QA_PIXEL. |
| Slope | `slope` | `USGS/SRTMGL1_003` | Degrees. |
| Topography | `elevation`, `curvature`, `twi` | `USGS/SRTMGL1_003` (+ MERIT `upa` for TWI) | Curvature is a Laplacian approximation; TWI uses a fixed 90 m cell width. |

Soil, land cover, lithology and roads are deliberately **not** predictors, since they are not in your
list. ESA WorldCover and JRC Surface Water are used only to mask permanent water.
Expect high VIF among elevation, snow, slope, HAND and TWI (snow cover tracks elevation in the
Alborz). Use `CFG.drop` after reading the VIF table.

"USGS criteria": USGS has no published flood-susceptibility rule set for Iran, so I took it to mean
GEE or USGS-hosted data. Tell me if you meant something else.

## Method

1. **Inventory** – default is the Global Flood Database (MODIS events 2000–2018, 250 m). Set
   `CFG.inventory = 'S1'` and list events in `CFG.s1Events` for Sentinel-1 change detection instead
   (thresholds are heuristics; tune them).
2. **Samples** – up to 2000 flood cells, an equal number of non-flood cells at least 1 km from any
   flood cell, permanent water excluded.
3. **Validation split** – whole ~10 km blocks go to train or test, which is stricter than a random
   split and gives less optimistic AUC.
4. **Models** – Random Forest, Gradient Tree Boost, SVM (RBF, ε-SVR), CART. All are fitted in
   regression mode on the 0/1 label, so each yields a [0,1] score.
5. **Consensus** – weighted mean score, with weight = max(AUC − 0.5, 0) normalised to 1.
   Also produced: a count of models voting "high" (>0.5) and the inter-model SD as an uncertainty layer.
6. **Classes** – equal-interval breaks at 0.2/0.4/0.6/0.8. Because training is balanced 1:1, scores are
   a *relative* ranking, not absolute flood probability.

## First-run checks (things I could not verify)

- `AOI features found` prints **1**. If 0, the GAUL name filter needs adjusting.
- `Global Flood Database events` is > 0 and `Flooded cells` is large enough to sample (hundreds+).
  MODIS flood mapping is weak under the cloudy Caspian forest, so the count may be small. If so, switch to `'S1'`.
- `Check dist_river on stream pixels` prints ≈ 0. If not, `fastDistanceTransform` semantics differ
  from what I assumed, and `dist_river` must be recomputed.
- The VIF table: drop predictors with VIF > 5–10 using `CFG.drop` (elevation, HAND and TWI are the likely culprits).
- Regression-mode `smileGradientTreeBoost`, `libsvm` (EPSILON_SVR) and `smileCart`: confirm they train without errors.
- AUC values look plausible (not ≈ 1.0, which would indicate leakage or a trivially separable inventory).

## Known limitations

- Training labels are historical flood extents, not a complete inventory. Ranking quality depends on it.
- Predictors have mixed native resolutions (5 km rain to 30 m terrain); sampling is at 250 m.
- Static factors only; no time-varying rainfall or land-use change.
- Susceptibility is not hazard (no depth, return period or exposure).

## Next step once Consensus is available again

Re-run the literature search (conditioning factors for flood susceptibility, ensemble/consensus
methods, Mazandaran studies) to confirm or revise the factor list and add proper citations.
