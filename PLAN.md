# Project plan — systematic review: trajectories of point-based spatial analysis

**Branch:** `claude/spatial-analysis-systematic-review-txgysx`
**Target:** cross-domain methodological systematic review, Q1 journal IF>10.
**Deliverable (user-selected):** manuscript in LaTeX + Word, with all tables, figures and maps generated from a real corpus.

## Hard constraints discovered
- OpenAlex / Crossref / PubMed E-utilities / Semantic Scholar / arXiv APIs are **blocked**
  by the session egress policy (403 on CONNECT). WebFetch also 403s on them.
- Therefore the corpus is built from the **Consensus MCP federated search**
  (Semantic Scholar + PubMed + Scopus + arXiv). This must be stated honestly in
  Methods and Limitations; do NOT claim a Scopus/WoS export.

## Retrieval design (search matrix)
Method families x application domains. Query IDs S01..Snn recorded in each record.

Method codes: KDE, RIPLEY (K/L/g/F/G/J), NN, SCAN, LISA (Gi*/Moran on points),
PPM (Poisson/Cox/LGCP/Gibbs), STPP (spatio-temporal/Hawkes/ETAS), NET
(network-constrained), COLOC (co-location/bivariate/marked), ML, OTHER.

Domain codes: CRIME, TRAFFIC, HEALTH, ECOL, SEISM, FIRE, URBAN, ARCH, GEOHAZ,
ENV, METH, BIOIMG.

## Query log
| ID | Query string |
|----|--------------|
| S01 | point pattern analysis spatial point process methods review |
| S02 | kernel density estimation hotspot mapping crime incidents |
| S03 | spatial scan statistic disease cluster detection SaTScan |
| S04 | Ripley's K function spatial pattern forest tree species |
| S05 | spatio-temporal point process earthquake ETAS self-exciting |
| S06 | network constrained point pattern analysis road traffic accidents |
| S07 | log-Gaussian Cox process spatial epidemiology disease risk |
| S08 | point of interest POI spatial clustering urban vitality |
| S09 | wildfire ignition point pattern analysis spatial |
| S10 | archaeological site location spatial point pattern |
| S11 | Getis-Ord Gi hotspot analysis point events |
| S12 | DBSCAN density-based clustering spatial points |
| S13 | co-location quotient bivariate point pattern |
| S14 | deep learning neural point process spatiotemporal events |
| S15 | landslide inventory point spatial statistics |
| S16 | species distribution presence-only point process model |
| S17 | geographically weighted regression point events |
| S18 | space-time scan statistic COVID-19 clusters |
| S19 | crime spatial analysis Africa developing countries |
| S20 | point pattern analysis China urban |
| S21 | Hawkes process crime prediction self-exciting |
| S22 | spatial accessibility health facilities point analysis |
| S23 | air pollution monitoring station spatial point analysis |
| S24 | marked point pattern mark correlation function |

## Pipeline
1. `data/batch_*.json`  — raw coded records, one file per 2-3 searches (persists across compaction)
2. `scripts/build_corpus.py` — merge, dedupe (title normalisation), apply eligibility, emit `data/corpus.csv`
3. `scripts/make_figures.py` — all figures + maps -> `figures/`
4. `scripts/make_tables.py` — all tables -> `tables/` (LaTeX + CSV)
5. `manuscript/main.tex` -> PDF; pandoc -> `manuscript/main.docx`

## Status — COMPLETE

- [x] 14 searches (S01–S14), 278 raw records coded into data/batch_01..12.json
- [x] corpus build: 274 screened, 51 excluded, **223 included**
- [x] 8 figures + maps (600 dpi PNG + vector PDF)
- [x] 6 main tables + 2 supplementary tables (CSV + LaTeX)
- [x] references.bib (276 entries) generated from the corpus
- [x] manuscript/main.tex and manuscript/main.docx
- [x] protocol/protocol.md
- [ ] Author to complete: Boolean Scopus/WoS re-run, DOI completion,
      second-reviewer audit of the 51 exclusions (see README)
