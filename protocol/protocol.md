# Review protocol

**Title.** Trajectories of point-based spatial analysis: a systematic review of
methods, application domains and case-study geographies, 1977–2026

**Review type.** Systematic review of methodological practice (PRISMA 2020).

**Registration.** Not prospectively registered. This protocol was fixed before
synthesis and is published unchanged alongside the review dataset.

**Search date.** 28 July 2026.

---

## 1. Rationale

Point-based spatial analysis is applied across public health, ecology,
criminology, transport safety, seismology, wildfire science, urban geography
and archaeology. Existing reviews are domain-specific. No synthesis has tested
whether these literatures are converging on shared methodology, or mapped the
geography of the underlying evidence base.

## 2. Review questions

- **Q1** Which method families constitute point-based spatial analysis, and how
  has their relative use changed over time?
- **Q2** Do method families remain siloed within application domains, or is
  there systematic cross-domain exchange?
- **Q3** Is there evidence of methodological maturation (temporal
  explicitness, methodological breadth, uptake of statistical learning)?
- **Q4** What is the geography of the evidence base across world regions and
  national income groups?

## 3. Eligibility criteria

| Dimension | Include | Exclude |
|---|---|---|
| Population | Studies analysing georeferenced event locations (points), any field | Analyses using only areal/lattice aggregates, raster surfaces, or extended line/polygon objects |
| Concept | At least one point-based spatial statistic or point process model applied or developed | Purely temporal point processes; accessibility/travel-time/site-suitability models with no point pattern statistic |
| Context | Any geography, scale, period | — |
| Publication type | Peer-reviewed article, conference paper, or preprint with full abstract | Books, monographs, theses, book reviews, corrections, conference abstracts without full text |
| Language | English abstract available | — |
| Reporting | Enough information to code method, domain and study area | No indexed abstract; corrupted metadata |

**The decisive boundary.** A statistic must be applied to *event locations*.
Getis–Ord `G*` on municipality-level counts is excluded; the same statistic on
network segments carrying individual crash points is included. This judgement
is recorded per record so readers can re-draw the line.

## 4. Information sources and search strategy

Federated bibliographic index spanning Semantic Scholar, PubMed, Scopus and
arXiv, queried through the Consensus interface. Fourteen natural-language
queries constructed on a method × domain matrix so that every principal method
family and every principal application domain is addressed by at least one
query. Exact query strings are reported verbatim in Table 1.

**Known deviation from ideal practice.** Native Scopus / Web of Science exports
were unavailable in the execution environment (blocked by network policy), so
Boolean field-limited searching, citation chaining and reference-list
hand-searching were not performed. The corpus is therefore a large,
systematically assembled and fully documented *sample*, not an enumeration.

## 5. Selection process

1. De-duplicate on normalised titles, plus manual identification of
   preprint/journal pairs and correction notices.
2. Screen title and abstract against eligibility criteria.
3. Record an inclusion decision and a free-text exclusion reason for every
   record.

Screening was performed by a single reviewer; no duplicate independent
screening, so no inter-rater reliability statistic is available. The full
decision log is published (Supplementary Table S2).

## 6. Data extraction

| Field | Values |
|---|---|
| `authors`, `year`, `title`, `journal` | as indexed |
| `doc_type` | article, review, conference, preprint, book, thesis, abstract, correction |
| `cites` | citation count at search date |
| `method` | primary method family (single) |
| `methods_all` | every method family applied (list) |
| `domain` | application domain |
| `country` | case-study country, or Multiple / Not specified / Not applicable |
| `st` | Y/N — explicit temporal dimension |
| `include`, `excl` | eligibility decision and reason |

### Method family codes

| Code | Family |
|---|---|
| `KDE` | Kernel density estimation (planar, adaptive, space–time) |
| `RIPLEY` | Second-order distance statistics (K, L, g, F, G, J) |
| `NN` | Nearest-neighbour indices (ANN, Clark–Evans, dispersion) |
| `SCAN` | Scan statistics (circular, elliptic, flexible, space–time) |
| `LISA` | Local association on points (Getis–Ord Gi*, local Moran) |
| `PPM` | Parametric point process models (Poisson, Cox, LGCP, Gibbs) |
| `STPP` | Spatio-temporal / self-exciting processes (Hawkes, ETAS) |
| `NET` | Network-constrained point pattern analysis |
| `COLOC` | Co-location, bivariate and marked point patterns |
| `ML` | Machine-learning point models (neural PP, DBSCAN, MaxEnt) |
| `OTHER` | Spectral, tessellation, fractal, graph-analytic |

### Application domain codes

`HEALTH`, `ECOL`, `CRIME`, `TRAFFIC`, `URBAN`, `SEISM`, `FIRE`, `ARCH`,
`ENV`, `BIOIMG`, `METH` (methodological/statistical), `OTHER`.

## 7. Synthesis plan

- Annual counts, smoothed with a 3-year centred moving average.
- Compositional shares, restricted to years with ≥ 2 studies.
- Maturation indicators compared across four periods: ≤2005, 2006–2012,
  2013–2019, 2020–2026.
- Method co-occurrence as a weighted graph over `methods_all`.
- Geography summarised by country, world region and World Bank-style income
  group.

**No meta-analysis and no risk-of-bias assessment.** The review synthesises
methodological practice, not treatment effects, so pooled effect estimates and
standard RoB instruments do not apply. Structured descriptors of
methodological completeness are reported instead.

## 8. Pre-specified limitations

1. Retrieval is not exhaustive (see §4); relevance ranking likely
   over-represents recent and highly cited work.
2. Single-reviewer screening and coding.
3. Coding from titles and abstracts, not full texts — `methods_all` counts are
   lower bounds, and bandwidth / edge correction / software were not
   extractable.
4. Not prospectively registered; bibliographic records lack volume, issue,
   page and DOI fields.
