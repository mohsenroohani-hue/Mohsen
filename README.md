# Trajectories of Point-Based Spatial Analysis (2000–2027)

A systematic, bibliometric, methodological and theoretical review of point-based
spatial analysis, with a fully reproducible analysis pipeline.

**Manuscript:** [`manuscript/Trajectories_of_Point-Based_Spatial_Analysis.md`](manuscript/Trajectories_of_Point-Based_Spatial_Analysis.md)

---

## What this is

913 studies, screened from a 5,713-record Scopus export (retrieved 2026-07-28),
coded across twelve dimensions and analysed for structural change over three
periods. The review introduces an original theoretical framework —
**Point Intelligence Drift** — together with a method taxonomy, a four-regime
periodisation, a maturity framework (PB-SAM) and a reporting standard (PBSA-REP).

Every number in the manuscript is computed from the corpus by the code in
`analysis/`. Nothing is estimated, imputed or illustrative. Analyses the
evidence base cannot support (citations, authors, journals) are marked as
explicit placeholders with the procedure required to generate them.

## Reproducing the analysis

```bash
pip install pandas numpy matplotlib scikit-learn scipy networkx pycountry pyshp

python3 analysis/pipeline.py    # PRISMA screening + coding  -> data/derived/
python3 analysis/analyse.py     # all tables + results.json  -> tables/
python3 analysis/figures.py     # all 16 figures             -> figures/
```

Runs end-to-end in under three minutes on one core, with **no network access**
and no manual step.

## Layout

| Path | Contents |
|---|---|
| `manuscript/` | The article |
| `analysis/lexicons.py` | The coding instrument: every controlled vocabulary, in one place |
| `analysis/geo.py` | Affiliation-country and case-study-country resolution, with toponym disambiguation |
| `analysis/pipeline.py` | PRISMA identification, screening, eligibility, coding |
| `analysis/analyse.py` | Descriptive, bibliometric, thematic and structural analysis |
| `analysis/figures.py`, `vizstyle.py` | Figure generation and house style |
| `data/raw/` | The Scopus export as received |
| `data/derived/` | Screening ledger, coded corpus, PRISMA counts, `results.json`, audit record |
| `tables/` | 24 supplementary tables (CSV), each with an embedded source/method note |
| `figures/` | 16 publication-quality figures (300 dpi PNG) |
| `assets/naturalearth/` | Natural Earth 1:110m country polygons (public domain), for offline maps |

## Key derived artefacts

- `data/derived/records_all.csv` — every screening decision for all 5,712 screened records, with the determining rule
- `data/derived/records_included.csv` — the 913-study coded corpus
- `data/derived/screening_validation.md` — the three-round audit record: every rule change and its motivation, plus final precision and false-omission estimates
- `data/derived/results.json` — every quantity quoted in the manuscript

## Headline findings

- Digital-trace point data rise from **1.8% → 37.0%** of period output while institutional and field data fall from **10.9% → 3.2%**.
- Learning methods reach **21.4%** of recent studies, but purely classical point-pattern studies are as common now (**9.3%**) as in 2000–2010 (**12.7%**) — the field accumulates methods rather than replacing them.
- Uncertainty treatment appears in **6.2%** of abstracts, reproducibility practice in **4.5%**, ethics engagement in **3.6%** — the last *lower* than twenty years ago.
- **90 of 176** countries appear nowhere in the corpus in any role; **38 of 51** African states never appear as an author affiliation; only **9.6%** of collaborative ties are South–South.

## Caveats that bound every result

Single database (Scopus only). Abstract-only coding — all rigour figures are
lower bounds on *reporting*, not measures of practice. Single-reviewer,
rule-based screening (precision 0.90, 95% CI 0.80–0.95; false-omission rate
0.05–0.15), so the corpus is a construct-valid **sample**, not a census. No
citation, author or journal fields in the export. The theory was induced from
the same corpus that illustrates it and has not been independently tested.
See manuscript Section 8.1.

## Data sources

- Bibliographic records: Scopus (Elsevier), export dated 2026-07-28.
- Basemap: Natural Earth 1:110m cultural vectors (public domain).
