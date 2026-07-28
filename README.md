# Trajectories of point-based spatial analysis — systematic review

A complete, reproducible systematic review of **point-based spatial analysis**
across nine application domains: manuscript (LaTeX + Word), 8 publication-grade
figures including a world map, 6 main tables, 2 supplementary tables, the full
screening dataset, and the code that generates all of it.

**223 included studies · 1977–2026 · 49 case-study countries · 14 structured queries**

---

## What's here

```
manuscript/   main.tex          full IMRaD manuscript (LaTeX source)
              main.docx         Word version, generated from main.tex
              references.bib    276 entries, generated from the corpus
figures/      fig01..fig08      600 dpi PNG + vector PDF
tables/       table1..table6    CSV + LaTeX booktabs
              tableS1, tableS2  supplementary (all included / all excluded records)
data/         batch_01..12.json raw coded records, one file per search batch
              corpus.csv        all 278 retrieved records with screening decisions
              included.csv      the 223 included studies
              prisma.json       PRISMA flow counts
              summary_stats.json
protocol/     protocol.md       pre-synthesis protocol and coding frame
scripts/      build_corpus.py   merge → dedupe → screen → corpus.csv
              make_figures.py   all figures and maps
              make_tables.py    all tables + summary statistics
              make_bib.py       references.bib from the corpus
              make_docx.py      main.tex → main.docx
```

## Reproducing everything

```bash
pip install pandas numpy matplotlib networkx python-docx
python3 scripts/build_corpus.py     # → data/corpus.csv, included.csv, prisma.json
python3 scripts/make_figures.py     # → figures/
python3 scripts/make_tables.py      # → tables/
python3 scripts/make_bib.py         # → manuscript/references.bib
python3 scripts/make_docx.py        # → manuscript/main.docx
```

To build the PDF (needs a TeX installation — not present in the environment
this was produced in):

```bash
cd manuscript && pdflatex main && bibtex main && pdflatex main && pdflatex main
```

## Figures

| # | Figure | Content |
|---|---|---|
| 1 | `fig01_prisma_flow` | PRISMA 2020 flow diagram |
| 2 | `fig02_method_trajectory` | Growth and compositional shift by method family |
| 3 | `fig03_method_domain_heatmap` | Method × domain heatmap |
| 4 | `fig04_country_cartogram` | **World map** — grid cartogram of case-study countries |
| 5 | `fig05_equity` | Region and income-group distribution |
| 6 | `fig06_method_network` | Method co-occurrence graph |
| 7 | `fig07_maturity` | Maturation indicators across four periods |
| 8 | `fig08_domain_trajectories` | Per-domain adoption curves |

Colours use a CVD-validated categorical order and a single-hue sequential blue
ramp; the palette was checked with a colourblind-separation validator before use.

**On the map (Figure 4).** No country-boundary dataset was reachable from the
build environment (Natural Earth and all bibliographic/geodata APIs are blocked
by network policy), and `cartopy` / `geopandas` bundled datasets were
unavailable. The map is therefore a **grid cartogram** — one labelled tile per
country, positioned schematically. This is a deliberate choice with a real
advantage: all 49 countries stay legible, including the 30 represented by a
single study, which a conventional choropleth would render nearly invisible. To
switch to a projected choropleth, drop a Natural Earth shapefile in and replace
`fig_map()` in `scripts/make_figures.py`.

## Headline findings

- Parametric **point process models** are now the most-used family (73 studies,
  33%), having overtaken **kernel density estimation** (66, 30%) after ~2015.
- **75%** of studies combine two or more method families.
- **Machine-learning** components: absent before 2006 → 26% of studies since 2020.
- **Network-constrained** formulations appear in 13% of studies.
- Only **37%** model an explicit temporal dimension.
- Five countries supply **54%** of country-attributable studies; low-income
  countries supply **1.2%** (n = 2); Africa supplies **6.1%**.

---

## Read this before submitting

Three things are genuinely incomplete, and they are yours to close.

**1. Retrieval was not exhaustive.** Scopus, Web of Science, OpenAlex, Crossref
and PubMed E-utilities were all blocked by the execution environment's network
policy. Records came from a federated index (Semantic Scholar + PubMed + Scopus
+ arXiv) via natural-language queries, with no Boolean field-limited searching,
no citation chaining and no reference-list hand-searching. The manuscript states
this plainly in Methods and Limitations and frames the corpus as a documented
*sample* rather than an enumeration. **For a Q1 submission, re-run the searches
as Boolean queries in Scopus/WoS and merge the exports.** The pipeline is built
to absorb that: add new records to `data/` in the same JSON schema and re-run
`build_corpus.py` — every figure, table and number regenerates.

**2. Reference records lack volume, issue, pages and DOI.** The retrieval index
does not expose them. `references.bib` carries author, title, year, venue and a
resolvable record URL. Run the `.bib` through a DOI-completion tool (or Zotero)
before submission.

**3. Screening was single-reviewer.** No duplicate independent screening, so no
κ statistic. Every decision and its reason is published per record in
`tables/tableS2_excluded_records.csv`, so a second reviewer can audit the 51
exclusions quickly — the cheapest path to a defensible reliability statement.

## On the IF > 10 target

Worth being direct: a *cross-domain methodological* review of point pattern
analysis has no natural home at IF > 10. The field's own leading journals sit
lower — *IJGIS* (~4–5), *Spatial Statistics*, *Computers, Environment and Urban
Systems* (~8) — and the IF > 10 venues are domain-committed, not
method-committed. Realistic options, in order:

| Journal | ~IF | What it needs from this draft |
|---|---|---|
| *Earth-Science Reviews* | ~12 | Lead with earth/environmental domains (seismology, wildfire, geohazard); trim crime/urban |
| *Information Fusion* | ~14 | Reframe around fusing heterogeneous point data streams and the statistics↔learning hybrid |
| *Sustainable Cities and Society* | ~10.5 | Reframe around urban safety/health applications and policy implications |
| *ISPRS J. Photogrammetry & RS* | ~12 | Needs a substantive remote-sensing/EO framing this corpus does not currently have |
| *Computers, Environment and Urban Systems* | ~8 | Best true fit as written — takes it essentially as-is |

As written, the draft is closest to *Computers, Environment and Urban Systems*
or *IJGIS*. Reaching IF > 10 means committing to one domain framing and
rebalancing the corpus toward it — an editorial decision, not a formatting
change. Impact factors above are approximate and should be checked against the
current JCR before you commit.
