# Land use × crash type × severity — spatial analysis

This folder analyses how 19 land uses relate to 13 crash outcomes on Florida arterials
(489 intersections, 334 segments; 4 years of crashes). Each outcome is analysed at four
severity levels (Fatal, KSI, KAB, Total). The main deliverable is the Word report
`outputs/Crash_LandUse_Spatial_Analysis_Report.docx`.

## Contents

| Path | What it is |
|---|---|
| `outputs/Crash_LandUse_Spatial_Analysis_Report.docx` | Full report: method-fit matrix for QGIS / ArcGIS Pro / GeoDa, ESDA maps, typology, count models, MGWR, step-by-step tool workflows, land-use atlas |
| `outputs/tables/crash_landuse_results.xlsx` | Every estimate (one-land-use-at-a-time and joint IRRs, controls, diagnostics, ESDA, typology, MGWR) |
| `outputs/tables/*.csv` | The same tables as CSV |
| `outputs/figures/` | All figures and maps (PNG) |
| `outputs/gis/` *(not committed)* | GeoPackage, GeoDa `.gal` weights, CSV with WKT and a data dictionary. Regenerate it locally with `08_export.py` |
| `scripts/` | Reproducible pipeline |

## Re-running

Copy `Intersections_20251022.csv` and `Segment_20251022.csv` into `data/`. The Florida county
boundaries (`data/fl_counties.gpkg`, included) come from the `us-atlas` npm package (Census
cartographic boundaries, 1:10m). Then run:

```bash
pip install pandas numpy scipy statsmodels geopandas shapely libpysal esda mgwr scikit-learn matplotlib openpyxl
cd scripts
python 01_descriptive.py   # study-area maps, crash composition, land-use prevalence
python 02_esda.py          # EB Moran's I, incremental SA, LISA, Gi*, join counts, bivariate Moran (every land use)
python 03_esda_figs.py
python 04_models.py        # NB2 / Firth-Poisson x 13 crash types x 4 severities, each land use + joint, ESF, FDR
python 05_typology.py      # K-means land-use contexts + adjusted crash profiles
python 06_gwr.py           # MGWR on ln(EB rate) (about 50 min)
python 07_model_figs.py
python 09_workflow_diagram.py
python 11_mgwr_figs.py
python 08_export.py        # GeoPackage / GeoDa weights / Excel workbook
python 10_report_data.py
cd report && NODE_PATH=<path to node_modules with docx> node build_report.js && node build_report.js  # two passes for cross-references
```
