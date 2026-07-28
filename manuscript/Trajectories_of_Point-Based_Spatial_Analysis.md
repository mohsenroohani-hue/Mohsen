# Trajectories of Point-Based Spatial Analysis: A Global Systematic, Bibliometric, Methodological, and Theoretical Review, 2000–2027

---

**Article type:** Systematic review with original theory development

**Running head:** Trajectories of point-based spatial analysis

**Corpus:** 913 studies screened from 5,713 records (Scopus, exported 28 July 2026)

**Reproducibility:** All screening decisions, coding rules, derived tables and figure-generating code accompany this article (`analysis/`, `data/`, `tables/`, `figures/`).

---

## Highlights

- The first systematic, PRISMA-based review to treat **point-based spatial analysis (PBSA)** as a distinct object of study, with an explicit definition, formal eligibility criteria and a reproducible, machine-executable screening instrument.
- Across 913 studies (2000–2026) the field's **data substrate inverts**: digital-trace point data rise from 1.8% to 37.0% of period output while institutional and field-survey data fall from 10.9% to 3.2%.
- **Methods accumulate rather than replace.** Learning-based methods grow from 2.7% to 21.4% of studies, yet purely classical point-pattern studies are as common in 2021–2027 (9.3%) as in 2000–2010 (12.7%).
- **Analytical complexity outruns methodological warrant.** The complexity-to-rigour ratio widens from 3.71 to 4.02; reproducibility practices appear in 4.5% of abstracts; no study in the corpus reaches the top maturity band on abstract-level evidence.
- **Where spatial problems are is not where spatial knowledge is made.** 90 of 176 countries never appear in the corpus in any role; 38 of 51 African states never appear as an author affiliation; only 9.6% of collaborative ties are South–South.
- The review induces and formalises an original framework — **Point Intelligence Drift (PID)** — with defined constructs, mechanisms, moderators, boundary conditions and eleven falsifiable propositions, alongside three new instruments: the **PBSA taxonomy**, a **four-regime periodisation**, and the **PB-SAM maturity framework**.

---

## Abstract

**Background.** Point-based spatial analysis — the analysis of phenomena whose elementary unit of observation is a discrete, georeferenced location — underpins epidemiology, criminology, transport science, ecology, hazard research and urban analytics. Despite this reach, it has never been reviewed as a coherent field: existing reviews are domain-bounded or method-bounded, and none distinguishes systematically between where spatial problems occur and where spatial knowledge about them is produced.

**Objectives.** This review (i) defines point-based spatial analysis and delimits its conceptual boundaries; (ii) maps its intellectual, geographical, thematic, technological and methodological evolution across three periods (2000–2010, 2011–2020, 2021–2027); (iii) identifies structural transitions, path dependencies and asymmetries that descriptive review cannot reach; and (iv) induces an original theoretical framework explaining the field's long-run transformation.

**Methods.** A PRISMA-based protocol was applied to a Scopus export of 5,713 records (retrieved 28 July 2026). A two-criterion eligibility rule — point-referenced units of observation (criterion A) *and* an explicit spatial-analytical operation (criterion B) — was operationalised as a transparent, rule-based screening instrument, developed over three audit-and-revision rounds and validated against reviewer adjudication of a stratified random sample of 100 records (precision 0.90, 95% CI 0.80–0.95; false-omission rate 0.05–0.15). 913 studies were included and coded across twelve dimensions: method, application domain, data source, software environment, spatial scale, temporal scale, uncertainty treatment, validation approach, reproducibility practice, ethical engagement, affiliation geography and case-study geography. A five-dimension maturity proxy (PB-SAM) was computed for every study.

**Results.** Output grew at a 13.2% compound annual rate, with mean annual production rising from 10.0 to 34.1 to 79.6 studies per year across the three periods. The methodological composition shifted decisively — kriging-based geostatistics fell from 30.0% to 12.1% of period output while classical machine learning rose from 1.8% to 15.4% and spatial clustering from 0.9% to 14.1% — but classical point-pattern statistics persisted throughout, and multi-class studies rose only from 12.7% to 25.8%. The data substrate inverted. Rigour did not follow: uncertainty treatment appears in 6.2% of abstracts corpus-wide and reproducibility practices in 4.5%, and learning-based studies report validation more than twice as often as classical studies (30.1% vs 13.4%) while reporting uncertainty half as often (3.3% vs 6.9%). Production is severely concentrated (Gini 0.774; top five countries 59.6% of affiliation mentions), and the concentration of *problems* studied is only slightly lower (Gini 0.737), so the two geographies are jointly, not compensatingly, unequal.

**Theory.** These patterns are integrated into **Point Intelligence Drift (PID)**: three accelerating drivers (data densification, computational abundance, application pull) advance the field's analytical *capability* faster than two slow-adapting brakes (epistemic infrastructure, institutional geography) can supply *warrant* and *access*. The residual — the **drift gap** — manifests as four observable outcomes: methodological sedimentation, substrate bifurcation, warrant erosion and capacity divergence, moderated by scale, uncertainty, ethical and knowledge-geography regimes, and feeding back into the drivers. Eleven falsifiable propositions are stated.

**Conclusions.** The field's problem is no longer analytical capability but the warrant and distribution of that capability. We set out a decade-long research agenda, a reporting standard for transparent point-based spatial analysis, and specific guidance for researchers, editors, funders, practitioners and policymakers.

**Keywords:** point-pattern analysis; spatial statistics; GIScience; spatial data science; geocomputation; bibliometrics; systematic review; reproducibility; geographies of knowledge production; GeoAI

---

## 1. Introduction

### 1.1 The point as an epistemic primitive

Geographical analysis rests on a small number of representational primitives — the point, the line, the area, the field — and of these the point is the most epistemically consequential and the least theorised. When a phenomenon is represented as a set of georeferenced points, three commitments follow simultaneously. First, the phenomenon is treated as *discrete*: it happened, or it exists, at a location, rather than varying continuously across space. Second, the location is treated as *informative*: the arrangement of points is taken to carry signal about the process that generated them, not merely about where an observer happened to look. Third, the point is treated as *reducible*: a person, a crime, a tree, a disease case, a sensor reading or a mobile-phone ping is collapsed to a coordinate pair, and everything not expressible in or alongside those coordinates is set aside.

These commitments are not innocuous. They determine which questions can be posed, which inferences are licensed, and — increasingly — which individuals become legible to analysis. John Snow's 1855 mapping of cholera deaths in Soho is celebrated because the point representation *was* the argument: the spatial arrangement of individual deaths around the Broad Street pump carried inferential weight that no aggregate table could. That the same representational move now applies to billions of passively generated location records is the central fact of this review.

### 1.2 Why point-based spatial analysis needs reviewing as a field

Point-based spatial analysis (PBSA) is not a discipline. It is a set of representational and analytical commitments that recur across disciplines that rarely read one another. An epidemiologist detecting a disease cluster with a space–time scan statistic, an ecologist fitting Ripley's *K* to stem locations, a criminologist producing a kernel density hotspot map, a transport scientist clustering GPS trajectories, and a geostatistician kriging from borehole samples are performing recognisably cognate operations on recognisably cognate data. They publish in disjoint venues, cite disjoint literatures, and inherit disjoint standards of evidence.

The consequence is a field that has never seen itself whole. Existing reviews are either **method-bounded** — excellent syntheses of point-pattern statistics in ecology, of hotspot mapping in criminology, of geostatistical practice in soil science — or **domain-bounded**, reviewing spatial methods within a single application area. Both designs are, by construction, incapable of answering the questions that matter most for the field's future:

- Do methods developed in one substrate transfer to another, or does each data substrate grow its own analytical tradition?
- Is the field's methodological repertoire being *replaced* by machine learning, or merely *extended* by it?
- Does analytical sophistication travel together with inferential warrant, or apart from it?
- Where in the world is this analysis performed, where are the problems it analyses, and are those the same places?

This review is designed to answer exactly these questions, and to do so with a protocol that another team could execute and audit.

### 1.3 The distinction this review insists on

A methodological commitment runs through the entire study and deserves statement at the outset: **the geography of the empirical case study and the geography of the institutions producing the analysis are separate variables and are never conflated.** Bibliometric reviews routinely report "leading countries" from author affiliations and allow readers to infer that these are the places being studied. They are not necessarily the same, and the difference between them is itself a finding — arguably the most politically consequential finding this review reports. We therefore resolve both geographies independently, for every study, and analyse their joint distribution (Sections 4.4, 5.5 and 8.4).

### 1.4 Contribution and structure

This review makes four kinds of contribution, enumerated in full in Section 9: five theoretical, five methodological, five empirical and five practical or policy contributions. Its central novel claim is that the long-run transformation of point-based spatial analysis is best understood not as *progress* (successive methods superseding their predecessors) nor as a *paradigm shift* (an incommensurable break), but as **drift**: a widening gap between what the field can compute and what it can warrant, justify and distribute. This is formalised in Section 7 as the **Point Intelligence Drift** framework.

Section 2 defines the object of review and its boundaries. Section 3 presents the protocol. Sections 4 and 5 report descriptive and structural results. Section 6 introduces the three original instruments (taxonomy, periodisation, maturity framework). Section 7 develops the theory. Section 8 offers critical discussion, including this review's own limitations. Sections 9–11 state contributions, the research agenda and conclusions.

---

## 2. Conceptual foundations: what point-based spatial analysis is, and is not

### 2.1 Definition

> **Point-based spatial analysis** is the body of methods and applications in which (a) the elementary unit of observation is a discrete entity or event located at a position in geographical space, and (b) an analytical operation is performed on the spatial or spatio-temporal configuration of those positions — characterising their intensity, arrangement, interaction, or association with covariates, or using them to predict values at unobserved locations.

Two clauses, both necessary. Clause (a) is a claim about the **data structure**: the analysis takes located individuals as input, not aggregates over areal units, not values on a raster lattice, not flows on a network. Clause (b) is a claim about the **analytical act**: merely mapping points is cartography, not analysis; the configuration must do inferential or predictive work.

The conjunction is what gives the definition teeth. It excludes choropleth analyses of areal rates (fails a), pixel-wise image classification (fails a), and descriptive point maps with no analytical operation (fails b). It includes geostatistical interpolation from point samples, because although the *target* is a continuous field, the *observations* are point-referenced and the analysis operates on their configuration.

### 2.2 Boundary conditions

Four boundaries were drawn explicitly and enforced in screening (Section 3.4).

**B1 — Geographical space.** The review is bounded to points located in geographical space. Point-process statistics applied to cell nuclei, molecules, material microstructure or galaxies are formally cognate and often methodologically ahead of geographical practice, but their scale, ethics and institutional context differ so completely that pooling them would destroy the coherence of any claim about knowledge geography. Methodological papers that *develop* point-process machinery and merely illustrate it on a non-geographical example are retained, because the methodological contribution belongs to the field.

**B2 — Analysis, not sensing.** Deriving point locations from a sensor — SLAM, point-cloud segmentation, feature extraction from LiDAR — is a measurement operation, not a spatial analysis of configuration. These are excluded unless the study proceeds to analyse the spatial arrangement of the derived points. The boundary is genuinely fuzzy and is the largest single source of residual misclassification in our corpus (Section 8.1).

**B3 — Points, not fields or areas.** Studies whose units are pixels, grid cells or administrative polygons are excluded even when they use methods with "point" in the name (multiple-point geostatistics, for instance, operates on training images and is excluded).

**B4 — Research contributions.** Errata, editorials, prefaces and comments are excluded.

### 2.3 Four construals of the point

The definition above is deliberately silent on *what the point represents*, because the corpus shows the same formal machinery applied to four quite different construals. This distinction is developed into Axis I of the taxonomy in Section 6.1:

1. **Event** — something that happened at a place and time (a crime, a case, an earthquake, a collision). Ontologically the point *is* the phenomenon.
2. **Sample** — a place where a continuous field was measured (a borehole, a monitoring station, a soil pit). The point is an observation *of* something else; the phenomenon is the field.
3. **Entity** — a persistent object with a location (a tree, a shop, a facility, a point of interest). The point is a simplification of an extended object.
4. **Trace** — a position emitted by a moving body (a GPS fix, a check-in, an AIS ping). The point is one sample of a trajectory, and is rarely independent of its neighbours.

These four construals carry radically different assumptions about independence, stationarity, sampling and consent, yet the corpus shows the same estimators applied across all four with little acknowledgement of the difference. That mismatch recurs throughout the results and is one of the mechanisms the theory in Section 7 is built to explain.

### 2.4 Relation to adjacent fields

PBSA is not coextensive with spatial statistics (which includes areal and lattice data), GIScience (which includes representation, cognition and institutions), spatial data science (which is defined by tooling and workflow rather than by data structure), or geocomputation (defined by computational strategy). It intersects all four. Its distinctive commitment is representational: the point as unit of observation. Section 7.7 states precisely how the proposed framework differs from the theoretical apparatus of each of these adjacent fields.

---

## 3. Methods

### 3.1 Protocol and reporting

The review follows the PRISMA 2020 reporting framework, adapted in two respects that must be declared plainly. First, screening was performed by a **transparent rule-based instrument** rather than by two independent human screeners; the instrument is published in full (`analysis/lexicons.py`, `analysis/pipeline.py`) and every decision for all 5,712 screened records is recorded with its determining rule (`data/derived/records_all.csv`). Second, because a second independent screener was not available, **inter-rater reliability could not be computed**; instead the instrument was validated against reviewer adjudication of a stratified random sample (Section 3.5). No protocol was pre-registered. Both departures are limitations, not design preferences, and are revisited in Section 8.1.

### 3.2 Information source and search

The evidence base is a single Scopus export of **5,713 records**, retrieved **28 July 2026**, covering publication years 2000–2026. The export contains six fields per record: title, year, DOI, Scopus link, affiliations and abstract.

Three consequences follow and constrain everything downstream:

- **A second database was not searched.** Web of Science, Dimensions and OpenAlex were not queried. The corpus is therefore a Scopus-indexed sample, inheriting Scopus's well-documented skew towards English-language, Northern-published, journal-formatted research.
- **The export contains no author, source-title, keyword or citation fields.** Author-level bibliometrics, journal-level analysis, citation counts, h-indices, co-citation and bibliographic coupling are consequently **not computable** from this evidence base. Where such analyses are conventionally expected, this review reports a clearly marked placeholder and the exact procedure required to produce the result (Section 3.7).
- **External bibliographic APIs were unreachable** from the analysis environment (Crossref and OpenAlex both returned policy denials at the network egress). Enrichment of the export was therefore impossible, and no attempt was made to reconstruct missing fields by inference.

**Reproducible search strategy.** The export's originating query string was not supplied with the data. For replication, we specify the query that reproduces the review's *sampling frame* to within indexing drift:

```
TITLE-ABS-KEY (
    ( "point pattern*" OR "point process*" OR "spatial point*" OR "point-referenced"
      OR "point of interest" OR "POI data" OR "geocoded" OR "occurrence record*"
      OR "event location*" OR "sampling point*" OR "monitoring station*"
      OR "GPS trajector*" OR "check-in data" OR "geotagged" )
  AND
    ( "kernel density" OR "Ripley*" OR "nearest neighbo*r analysis"
      OR "spatial autocorrelation" OR "Moran* I" OR "Getis-Ord" OR "hot spot analysis"
      OR "scan statistic*" OR "spatial cluster*" OR "kriging" OR "geostatistic*"
      OR "geographically weighted" OR "spatial regression" OR "network-constrained"
      OR "spatio-temporal model*" OR "species distribution model*" )
)
AND PUBYEAR > 1999 AND PUBYEAR < 2028
AND ( LIMIT-TO ( DOCTYPE , "ar" ) OR LIMIT-TO ( DOCTYPE , "cp" ) OR LIMIT-TO ( DOCTYPE , "re" ) )
AND ( LIMIT-TO ( LANGUAGE , "English" ) )
```

Replicators should note that the supplied export is materially **broader** than this query: it contains a large volume of raster, areal and sensor-processing research (Figure 1), which is why 84.0% of records were excluded at screening. Our eligibility rules, not the search string, define the corpus.

### 3.3 Eligibility criteria

**Inclusion** required *both*:

- **Criterion A — point-referenced units of observation.** Evidence in title or abstract that the elementary units are located events, samples, entities or traces. Operationalised as 19 pattern families (`CRITERION_A_POINT_UNITS`), including point-process objects, points of interest, occurrence records, geocoded cases, sampling and monitoring stations, GPS and trajectory data, survey clusters, incident records and facility sites.
- **Criterion B — an explicit spatial-analytical operation.** Evidence of density estimation, second-order point-pattern analysis, point-process modelling, nearest-neighbour analysis, spatial autocorrelation, hotspot or cluster detection, scan statistics, geostatistics, spatial regression, network-constrained analysis, spatio-temporal modelling, accessibility modelling, species distribution modelling, or explicit spatial-pattern characterisation.

A **sufficiency rule** was added after audit: four methods (Ripley's *K* and second-order analysis, point-process models, the nearest-neighbour index, network-constrained point analysis) are definitionally defined on point patterns, and their presence establishes criterion A on its own — unless an explicit raster or areal-unit context blocks the inference.

**Exclusion** applied the four boundary conditions of Section 2.2, plus a **polysemy control**. The word "point" is heavily polysemous in scientific English ("point estimate", "melting point", "point mutation", "point of care", "change-point detection", "point of view", "access point"). Seven trap families were specified so that records whose only evidence for criterion A was a polysemous use of "point" were excluded.

### 3.4 Screening procedure

Screening is **sequential**: rules are applied in a fixed order and the *first* failing rule is recorded, so exclusion reasons partition the excluded set exactly once and the PRISMA flow sums correctly (Figure 1).

| Stage | Rule | Excluded |
|---|---|---|
| S1 | Publication year outside 2000–2027 | 0 |
| S2 | No usable abstract (after boilerplate removal) | 3 |
| S3 | Non-research item | 4 |
| S4a | Outside the geographical boundary (B1) | 66 |
| S4b | Sensor-processing tradition (B2) | 180 |
| S5 | Criterion A not met | 3,374 |
| S6 | Criterion B not met | 1,149 |
| S7 | Out-of-scope tradition without core spatial-statistical operation | 1 |
| S8 | Polysemous use of "point" only | 22 |
| — | **Included** | **913** |

Exclusions sum to 4,799, exactly the difference between the 5,712 screened and the 913 included. Deduplication preceded screening: one duplicate was removed on normalised title, none on DOI. The three S2 exclusions are records whose entire "abstract" consisted of copyright boilerplate and which fell below the 120-character minimum once that boilerplate was stripped.

**A data-cleaning step that materially changes the results.** 96.8% of abstracts in the export carry appended publisher copyright or licence statements. These name corporate domiciles — "Licensee MDPI, Basel, Switzerland"; "Springer Nature Switzerland AG"; "Springer-Verlag Berlin Heidelberg"; "Informa UK Limited" — which the case-study gazetteer detects as toponyms. Before cleaning, Switzerland was the **third most frequent case-study country** in the corpus (59 studies), an artefact entirely produced by MDPI's imprint address. All boilerplate is stripped before any coding or text analysis (`clean_abstract()`). We flag this because it is a silent, systematic and easily missed contaminant of any text-mining bibliometric study that uses abstract text to infer geography, and we have not seen it documented elsewhere.

### 3.5 Validation of the screening instrument

The instrument was developed over **three audit-and-revision rounds**. In each round a stratified random sample was drawn, the reviewer read every sampled title and abstract, assigned an independent eligibility verdict against the Section 2 definition, and traced each disagreement to the responsible rule. Rules were revised only where a disagreement reflected a systematic construct-validity failure. The full audit record, including every rule change and its motivation, is in `data/derived/screening_validation.md`.

Round 1 exposed two false-positive classes (point-cloud engineering; non-geographical point patterns) and two false-negative classes (trajectory and survey-cluster data; definitional methods not treated as sufficient). Round 2 exposed a further false-negative class (methodological papers illustrated on non-geographical examples) and a false-positive class (raster landscape-pattern indices).

**Round 3 (final instrument, reported here).** Stratified random sample of 100 records: 60 included, 40 excluded.

| Stratum | Verdict | n | Share |
|---|---|---|---|
| Included (n = 60) | Eligible, unambiguous | 45 | 0.750 |
| | Eligible, borderline | 9 | 0.150 |
| | **Not eligible (false positive)** | **6** | **0.100** |
| Excluded (n = 40) | Correctly excluded | 34 | 0.850 |
| | **Eligible but excluded** | **2 unambiguous, 4 probable** | **0.050–0.150** |

**Precision** counting only unambiguous misclassifications: **0.900** (Wilson 95% CI 0.798–0.954). Under a strict reading that also rejects borderline records: **0.750** (95% CI 0.627–0.842). **False-omission rate**: 0.05–0.15.

Two implications must be carried into every subsequent interpretation. First, residual false positives are not randomly distributed: they concentrate at the boundary with geophysical and sensor-signal processing (B2), which is a genuine grey zone of the construct rather than a coding slip. Second, applying the estimated false-omission rate to the 4,799 excluded records implies on the order of 240–720 eligible studies not recovered. **The corpus is therefore a large, construct-valid *sample* of the point-based spatial-analysis literature indexed in this export, not an exhaustive census, and every prevalence estimate below is conditioned on that sampling frame.**

We note one deliberate refusal to improve sensitivity. Admitting kriging as *sufficient* evidence of point-referenced data would have recovered several missed geostatistical papers, but raised the corpus from 916 to 1,247 records and visibly degraded precision by importing raster-field interpolation studies. The boundary was held at the more conservative position, at a known cost in recall.

### 3.6 Data extraction and coding

Every included study was coded on twelve dimensions using controlled vocabularies specified once, in full, in `analysis/lexicons.py`. Categories within a dimension are **non-exclusive**: a study using both kriging and random forests is coded to both. Percentages are therefore always shares *of studies*, never of mentions, and columns do not sum to 100%.

| Dimension | Categories | Basis |
|---|---|---|
| Method | 24 methods in 6 classes | Title + abstract |
| Application domain | 13 domains | Title + abstract |
| Data source | 10 sources | Title + abstract |
| Software environment | 15 environments | Title + abstract |
| Spatial scale | 6 levels | Title + abstract |
| Temporal scale | 5 levels | Title + abstract |
| Uncertainty treatment | 5 constructs | Title + abstract |
| Validation approach | 5 constructs | Title + abstract |
| Reproducibility practice | 3 constructs | Title + abstract |
| Ethics and privacy | 3 constructs | Title + abstract |
| Affiliation geography | ISO 3166-1 alpha-3 | Affiliation field |
| Case-study geography | ISO 3166-1 alpha-3 | Title + abstract |

**Affiliation geography** is parsed from the terminal comma-delimited token of each semicolon-separated affiliation string and resolved through a gazetteer with explicit alias handling (249 countries, plus Scopus-specific spellings). A study with authors in *k* countries contributes to all *k*.

**Case-study geography** is detected from cleaned title and abstract using country names, official names, demonyms and roughly 300 major cities and sub-national regions, with explicit contextual disambiguation of polysemous toponyms. Georgia is resolved to the country only in the presence of Caucasus context and to the United States in the presence of Atlanta or US context; Turkey is blocked by ornithological and poultry contexts; Guinea is blocked by "guinea pig", "New Guinea", "Equatorial Guinea" and "Guinea-Bissau"; Niger is blocked by Nigeria and by "Niger River"; Jordan, Chad, Mali, Oman, Chile, Congo, Samoa, Sudan, Ireland, Panama, Lebanon, Malta, Cyprus and India carry their own rules.

**PB-SAM maturity.** Five dimensions (method specification, uncertainty, validation, data transparency, reproducibility) are each scored 0–2 from abstract-level evidence, giving a 0–10 composite. Its interpretation is constrained in Section 6.3 and its limitations stated in Section 8.1.

**Global North / South.** The UN M49 "developed regions" definition is used, with high-income East and Southeast Asian economies (Republic of Korea, Singapore, Taiwan, Hong Kong SAR, Macao SAR) added to the North. The boundary is contested; because China alone accounts for the majority of Global-South output in this corpus, **every North–South contrast is reported with a China-excluded sensitivity analysis** (Section 5.5).

### 3.7 Analyses that this evidence base cannot support

Scientific honesty requires stating what is *not* here, and what would be needed to produce it. The following are conventionally expected in a bibliometric review and are **not reported** because the export lacks the necessary fields. Each is marked as a placeholder with the procedure required.

| Expected analysis | Status | Procedure required to generate it |
|---|---|---|
| Most-cited studies; citation distributions | **[PLACEHOLDER — not computable]** | Re-export from Scopus including `Cited by`, or resolve all 913 DOIs against the Crossref `is-referenced-by-count` or OpenAlex `cited_by_count` field. |
| Most productive and most influential **authors**; author h-indices | **[PLACEHOLDER — not computable]** | Re-export including `Authors` and `Author(s) ID`; disambiguate via Scopus Author ID or ORCID. |
| **Journal**-level analysis; Bradford's-law core; impact-factor profile | **[PLACEHOLDER — not computable]** | Re-export including `Source title` and ISSN; join to JCR/SJR. Publisher-level analysis *is* reported (Table 9), derived deterministically from DOI registrant prefixes. |
| Co-citation and bibliographic-coupling networks; intellectual-base mapping | **[PLACEHOLDER — not computable]** | Requires cited-reference lists (Scopus `References` field or OpenAlex `referenced_works`). |
| Author keyword co-occurrence and keyword-burst detection | **[PLACEHOLDER — not computable]** | Requires `Author Keywords` / `Index Keywords`. Title-term log-odds analysis is reported instead (Figure 8, Table 11) as the closest available substitute. |
| Institution-level ranking with name disambiguation | **[PARTIAL]** | Reported as raw affiliation strings (Table 10) with no variant disambiguation; counts are lower bounds. Full analysis requires an institutional authority file (e.g. ROR) applied to the affiliation strings. |

We consider it preferable to leave these cells explicitly empty than to fill them with plausible-looking numbers. Nothing in this article is estimated, imputed or illustrative: every quantity is computed from the 913 included studies.

### 3.8 Reproducibility of this review

| Artefact | Location |
|---|---|
| Raw export (5,713 records) | `data/raw/scopus_export_2026-07-28.csv` |
| Coding instrument (all vocabularies) | `analysis/lexicons.py` |
| Geographical resolver | `analysis/geo.py` |
| PRISMA + coding pipeline | `analysis/pipeline.py` |
| Analysis engine (all tables) | `analysis/analyse.py` |
| Figure generation | `analysis/figures.py`, `analysis/vizstyle.py` |
| Every screening decision | `data/derived/records_all.csv` |
| Coded corpus (913 studies) | `data/derived/records_included.csv` |
| Audit record | `data/derived/screening_validation.md` |
| All numbers quoted in this article | `data/derived/results.json` |
| 24 supplementary tables | `tables/T01`–`T24` |

The full pipeline runs from raw export to final figures in under three minutes on a single core, with no network access and no manual step.

---

## 4. Results I: the descriptive anatomy of the field

*All results in this section are computed from the 913 included studies. Figures are numbered as referenced; full numeric tables are in `tables/`.*

### 4.1 Growth and periodisation

**Figure 2** and **Table S1** (`T01`) report publication growth. Output rises from 5 studies in 2000 to 110 in 2025, a compound annual growth rate of **13.2%**. Mean annual production by period: **10.0** studies (2000–2010), **34.1** (2011–2020), **79.6** (2021–2025). The three periods contain 110, 341 and 462 studies respectively.

Growth is not smooth. The series is broadly flat to 2007, steps up modestly through 2008–2016, and accelerates sharply from 2017 (50 studies) with a further jump in 2019 (66). This inflection is not an artefact of corpus size: it coincides exactly with the arrival of digital-trace data documented in Section 4.5, and it is the empirical anchor for the regime boundary proposed in Section 6.2.

*Interpretive caution:* 2026 is truncated at the export date and 2027 contains no indexed records. Neither year supports a trend claim, and both are marked as partial in every figure. The apparent 2025→2026 decline is an artefact of the export window.

### 4.2 Methods

**Table S2** (`T02`) and **Figure 3** report method prevalence. The corpus mean is **1.10 named methods per study**, and 22 of the instrument's 24 method categories are attested.

| Method | Total n | % corpus | 2000–2010 | 2011–2020 | 2021–2027 |
|---|---|---|---|---|---|
| Kriging and variogram geostatistics | 171 | 18.7 | **30.0** | 24.0 | 12.1 |
| Kernel density estimation | 96 | 10.5 | 8.2 | 7.0 | **13.6** |
| Classical machine learning | 90 | 9.9 | 1.8 | 5.0 | **15.4** |
| Spatial clustering algorithms | 85 | 9.3 | 0.9 | 5.6 | **14.1** |
| Point process models (Poisson/Cox/Hawkes) | 78 | 8.5 | 7.3 | **10.9** | 7.1 |
| Spatial autocorrelation statistics | 74 | 8.1 | 6.4 | 6.2 | **10.0** |
| Deterministic interpolation | 61 | 6.7 | 8.2 | 8.5 | 5.0 |
| Spatial regression / GWR | 50 | 5.5 | 2.7 | 4.4 | **6.9** |
| Ripley's *K* / second-order PPA | 47 | 5.1 | **9.1** | 6.5 | 3.2 |
| Bayesian hierarchical spatial models | 43 | 4.7 | 2.7 | **7.3** | 3.2 |
| Deep learning | 40 | 4.4 | 0.9 | 1.8 | **7.1** |
| Nearest-neighbour analysis | 35 | 3.8 | 4.5 | 2.3 | 4.8 |

*(Percentages are shares of the period's studies; bold marks each method's peak period.)*

Four patterns deserve emphasis.

**(i) A geostatistical decline in relative, not absolute, terms.** Kriging falls from 30.0% to 12.1% of period output, and Ripley's *K* from 9.1% to 3.2%. In absolute counts, however, kriging appears in 33 studies in 2000–2010 and 56 in 2021–2027. The classical core is being *diluted*, not abandoned — a distinction with real consequences for how the field's history should be narrated.

**(ii) The learning ascent is real but bounded.** Classical machine learning rises 1.8% → 15.4% and deep learning 0.9% → 7.1%. Learning-based methods of any kind reach **21.4%** of 2021–2027 studies. That is a transformation; it is not a takeover. Roughly four in five recent studies use no learning method at all.

**(iii) A Bayesian interlude.** Bayesian hierarchical models peak in 2011–2020 (7.3%) and fall back to 3.2%, as do point-process models (10.9% → 7.1%). This is the single most counter-intuitive trajectory in the corpus. The methods that were rising fastest in the middle period — the model-based, uncertainty-propagating tradition of INLA, SPDE and log-Gaussian Cox processes — *lose* relative ground in the most recent period. Section 5.4 argues this is not a coincidence but a structural substitution.

**(iv) Explainability and real time barely register.** Explainable AI appears in a handful of studies; real-time and streaming analytics reach only 1.5% of 2021–2027 output. The vocabulary of "real-time spatial analytics" substantially outruns its published practice.

**Method classes** (**Table S3**) summarise the same movement: inferential/model-based methods are the largest class throughout; learning-based methods rise from 2.7% to 21.4%; network-constrained methods *fall* (2.7% → 1.5%), which is notable given the theoretical maturity of network-constrained point-pattern analysis.

### 4.3 Application domains

**Table S4** (`T04`) and **Figure 9** report domains.

| Domain | n | % corpus | 2000–2010 | 2021–2027 |
|---|---|---|---|---|
| Urban studies & planning | 368 | 40.3 | 18.2 | **51.3** |
| Ecology & biodiversity | 265 | 29.0 | 32.7 | 25.8 |
| Geodesy, remote sensing & earth observation | 173 | 18.9 | 11.8 | 23.6 |
| Transportation & mobility | 171 | 18.7 | 10.9 | 22.3 |
| Environmental monitoring & pollution | 133 | 14.6 | 12.7 | 15.2 |
| Energy & infrastructure | 93 | 10.2 | 2.7 | 13.2 |
| Public health & epidemiology | 89 | 9.7 | 10.0 | 8.7 |
| Agriculture & food systems | 89 | 9.7 | 11.8 | 8.9 |
| Disaster risk & hazards | 86 | 9.4 | 7.3 | 11.5 |
| Retail & economic geography | 75 | 8.2 | 1.8 | 11.7 |
| Tourism & recreation | 36 | 3.9 | 0.0 | 6.9 |
| Social media & digital society | 27 | 3.0 | 0.9 | 2.8 |
| Crime & security | 26 | 2.8 | 1.8 | 3.0 |

The **urbanisation of the field** is the dominant thematic fact: urban studies rises from 18.2% to 51.3% of period output, overtaking ecology to become the field's centre of gravity. Retail geography (1.8% → 11.7%) and tourism (0.0% → 6.9%) grow from nothing, both driven by point-of-interest data.

Two findings run against expectation and are, we argue, more revealing than the growth figures.

**Public health and epidemiology *declines* in relative terms** (10.0% → 8.7%), despite this being the domain in which point-based spatial analysis has its deepest theoretical roots and its most consequential applications, and despite the corpus spanning a global pandemic. **Crime and security remains marginal throughout** (2.8% of the corpus), despite hotspot mapping being the single most institutionalised application of kernel density estimation in the world. Both under-representations are, in our reading, artefacts of *venue* rather than of activity: this literature publishes in epidemiology and criminology journals whose abstracts are less likely to foreground the spatial-analytical operation that criterion B requires. We flag this as a specific, testable limitation of abstract-based screening (Section 8.1) rather than as a claim that these fields have stopped doing point-based analysis.

### 4.4 Geography of production and of problems

**Figures 4, 5 and 15; Tables S11, S12 and S13**.

**Production.** 79 countries appear as an author affiliation. Concentration is severe: **Gini 0.774**; the top five countries account for **59.6%** of affiliation mentions and the top ten for **72.7%**.

| Rank | Country | Studies | % of corpus |
|---|---|---|---|
| 1 | China | 382 | 41.8 |
| 2 | United States | 220 | 24.1 |
| 3 | United Kingdom | 59 | 6.5 |
| 4 | Spain | 49 | 5.4 |
| 5 | Germany | 44 | 4.8 |
| 6 | Canada | 41 | 4.5 |
| 7 | Italy | 40 | 4.4 |
| 8 | Australia | 31 | 3.4 |
| 9 | Netherlands | 28 | 3.1 |
| 10 | France | 26 | 2.8 |

China and the United States together appear in more included studies than every other country combined.

**Problems.** 71 countries appear as the location of an empirical case study; **Gini 0.737**. China (247 studies, 27.1%) and the United States (92, 10.1%) again lead, followed by Australia (21), Iran (17), Spain (16), Canada (15) and the United Kingdom (11). **33.1% of studies report no detectable case geography** — methodological, simulation and tool papers.

**The critical observation is that these two inequalities do not offset one another.** A field could be geographically concentrated in production while studying a widely dispersed set of problems; that would be an argument for the universality of its methods. Here, concentration in production (0.774) and concentration in problems (0.737) are of the same order. The field is not a concentrated set of institutions analysing a dispersed world; it is a concentrated set of institutions analysing a correspondingly concentrated set of places.

**Absence.** Of the 176 countries in the basemap, **100 never appear as an author affiliation**, **109 never appear as a case study**, and **90 appear in neither role in any of the 913 studies**. Of 51 African countries, **38 never appear as an author affiliation**. Africa contributes 2.2% of affiliation mentions and 5.0% of case-study mentions; Asia contributes 39.9% and 50.2%, Europe 29.8% and 17.7%, North America 21.3% and 18.2%.

### 4.5 Data sources: the substrate inversion

**Figure 6; Table S5**. This is the largest structural change in the corpus.

| Data source | % of corpus | 2000–2010 | 2011–2020 | 2021–2027 |
|---|---|---|---|---|
| POI & commercial geodatabases | 16.8 | 0.9 | 9.4 | **26.0** |
| Remote sensing & earth observation | 14.7 | 10.9 | 10.0 | **19.0** |
| Mobile phone & GPS trajectory data | 8.9 | 0.0 | 7.9 | **11.7** |
| LiDAR & 3D point clouds | 6.5 | 4.5 | 5.0 | **8.0** |
| Simulated / synthetic data | 5.5 | 7.3 | 6.2 | 4.5 |
| Field survey & in-situ sampling | 3.4 | 5.5 | 4.1 | 2.4 |
| Official / administrative records | 2.0 | 5.5 | 2.3 | 0.9 |
| Volunteered geographic information | 1.8 | 0.9 | 0.9 | **2.6** |
| Sensor networks & IoT | 1.6 | 1.8 | 2.3 | 1.1 |
| Social media & geosocial data | 1.5 | 0.0 | 2.6 | 1.1 |

Aggregating, **digital-trace data** (VGI, social media, mobile/GPS, POI) rise from **1.8% → 17.3% → 37.0%** of period output, while **institutional data** (administrative records, field survey) fall from **10.9% → 6.5% → 3.2%**. Within a single generation the modal point in a published point-based analysis has changed from *a place a researcher went to measure something* to *a record a platform generated about somebody*.

One nuance matters for the ethics discussion in Section 8.3: the growth is dominated by **POI data** (26.0% of recent studies), not by social media (1.1%). POI records are commercially assembled facility inventories. They are digital-trace data in provenance and licensing, but they are not personal data. The corpus is therefore adopting the *infrastructure* of platform data faster than it is adopting its most privacy-sensitive content — which makes the near-total absence of ethical discussion (Section 4.7) less alarming than it first appears, but does not excuse it, since mobile-phone and GPS trajectory data reach 11.7% of recent studies.

### 4.6 Software, scale and reporting silence

**Tables S6, S7 and S8**. The dominant finding here is **non-reporting**.

- **94.2% of studies name no software environment** in the abstract. Among those that do: ArcGIS (12 studies), R (11), SaTScan (7), Google Earth Engine (5), INLA (5), MATLAB (5), Python (4), spatstat (3).
- **51.4% name no data source.**
- **69.7% state no spatial scale.**
- **33.1% state no case-study geography.**

These are abstract-level measures and understate full-text reporting. But the abstract is the only part of a paper that most readers, and every automated indexing system, will ever process. That fewer than one paper in sixteen states its computational environment in the abstract is a finding about the field's *discoverability*, and it is the direct motivation for the reporting standard proposed in Section 10.3.

Where scale is stated, the field operates at **regional/sub-national** (13.6%) and **city/metropolitan** (11.3%) scales; national (1.6%) and continental/global (3.0%) work is rare. Temporally, daily-to-monthly (9.1%) and annual-to-decadal (8.5%) dominate; sub-daily or real-time analysis appears in 2.7%.

### 4.7 Rigour: uncertainty, validation, reproducibility, ethics

**Figure 11; Table S9**. Reported as shares of studies with *any* abstract-level evidence in each family:

| Construct family | 2000–2010 | 2011–2020 | 2021–2027 | Corpus |
|---|---|---|---|---|
| Any uncertainty treatment | 4.5 | 7.6 | 5.6 | **6.2** |
| Any validation procedure | 19.1 | 14.4 | 16.5 | **16.0** |
| Any reproducibility practice | 0.9 | 5.0 | 5.0 | **4.5** |
| Any ethics or privacy discussion | 7.3 | 2.6 | 3.5 | **3.6** |

Three observations.

**Rigour reporting is flat or declining, not improving.** Uncertainty peaks in the middle period and falls back. Validation is *highest* in the earliest period (19.1%) and lower thereafter. Reproducibility rises from near zero but plateaus at 5%. Ethics discussion is **lower in 2021–2027 (3.5%) than in 2000–2010 (7.3%)** — precisely inverting the trajectory of the data substrate, which became vastly more ethically encumbered over the same span.

**The rigour deficit is method-specific and structured.** Comparing learning-based studies (n = 123) with classical/inferential studies (n = 434):

| | Uncertainty | Validation | Reproducibility | Mean PB-SAM |
|---|---|---|---|---|
| Classical / inferential | 6.9% | 13.4% | 4.8% | 2.39 |
| Learning-based | 3.3% | **30.1%** | 4.1% | 2.85 |

Learning-based studies report validation **more than twice as often** and uncertainty **half as often**. These are not competing measures of the same virtue. Cross-validated predictive accuracy answers "does this model generalise to held-out data from the same process?" Uncertainty quantification answers "how wrong might this estimate be, and where?" The corpus shows the first systematically displacing the second. We name this **warrant erosion** and treat it as a core outcome of the theory in Section 7.

**Maturity is unbalanced.** PB-SAM (Figure 12, **Table S10**) rises modestly from 1.51 to 2.11 out of 10. The rise is concentrated almost entirely on D1 (naming a method: 0.90 → 1.07) and D4 (describing data: 0.35 → 0.75). D2 (uncertainty: 0.05 → 0.06), D3 (validation: 0.20 → 0.18) and D5 (reproducibility: 0.01 → 0.05) remain at or near the floor across all three periods. **No study in any period reaches Level 3 (score ≥ 7) on abstract-level evidence.** The field is becoming more articulate about what it does without becoming more accountable for whether it is right.

### 4.8 Collaboration

**Figure 10; Tables S14 and S15**. International co-authorship is 34.5% (2000–2010), 38.1% (2011–2020) and **22.1%** (2021–2027); mean affiliation countries per study falls from 1.49 to 1.29.

**This decline is the corpus's most surprising bibliometric result**, running against the near-universal finding that scientific collaboration internationalises over time. It is substantially explained by compositional change: China's share of output rises to 41.8%, and Chinese point-based spatial analysis is overwhelmingly domestically authored. The finding is therefore best stated as: *the field's growth in the third period has been driven by a national research system that collaborates internationally at below the field's historic rate.*

Of 264 country-pair collaborative ties, **46.7% are North–North, 43.7% North–South and only 9.6% South–South.** The Global South is connected to the field through the North rather than through itself — a hub-and-spoke topology with very few lateral ties.

### 4.9 Publishers and institutions

**Tables S16 and S17**. Publisher is derived deterministically from the DOI registrant prefix. Elsevier (26.2%), MDPI (23.2%), Springer (12.3%), Wiley (11.6%) and Taylor & Francis (6.0%) account for 79.3% of the corpus. MDPI's second position, essentially absent before 2015, is a structural fact about where this field now publishes and interacts with the open-science findings in Section 8.2.

Institutional counts are **lower bounds** (no name disambiguation). The Chinese Academy of Sciences leads with 45 studies, followed by the University of Chinese Academy of Sciences (18) and the Hong Kong Polytechnic University (8). Journal-level analysis is **[PLACEHOLDER — not computable]**; see Section 3.7.

---

## 5. Results II: structure, transition and asymmetry

Section 4 described. This section analyses relationships that no single variable reveals.

### 5.1 Methodological sedimentation, not succession

The standard narrative of a maturing quantitative field is *succession*: new methods supersede old ones. The corpus falsifies this for PBSA.

If succession held, the share of studies using *only* classical point-pattern statistics should fall monotonically. It does not: **12.7% (2000–2010) → 7.6% (2011–2020) → 9.3% (2021–2027)**. Purely classical work is as common now as a generation ago. Simultaneously, the mean number of method classes per study rises and multi-class studies grow from 12.7% to 25.8%.

The field is therefore **accumulating** methods, not replacing them. Nothing is retired. Ripley's *K* (1976), the nearest-neighbour index (1954), Moran's *I* (1950) and ordinary kriging (1963) all remain in active use alongside graph neural networks. We call this **methodological sedimentation**: successive analytical strata are deposited without erosion of the strata beneath.

Sedimentation has an underappreciated cost. A field in which nothing is retired accumulates not only methods but their **unreconciled assumptions**. A corpus in which complete spatial randomness tests, log-Gaussian Cox processes and gradient-boosted classifiers coexist contains at least three incompatible accounts of what "clustering" means and what would count as evidence for it — and the corpus contains almost no papers reconciling them.

### 5.2 The substrate bifurcation

**Figure 7** (Sankey diagram) makes visible a structure invisible in any one-dimensional table: data substrates and method classes are **not** freely combined. Institutional and field data flow overwhelmingly into geostatistical and classical estimation. Digital-trace data flow into clustering, learning-based and network-constrained methods. The two substrates connect only weakly to the same methods.

This is a **bifurcation**, not a division of labour, because the two branches are diverging on the dimensions that matter epistemically. The field-data branch retains the vocabulary of estimation, error and inference. The trace-data branch adopts the vocabulary of extraction, identification and prediction — visible directly in the title-term analysis (Section 5.3), where the third period's distinctive vocabulary includes *extraction*, *learning*, *machine*, *multi-source*, *influencing* and *factors*, and where the estimation vocabulary of the first period (*test*, *nonparametric*, *inference*, *testing*, *estimating*) has thinned markedly.

The two branches are increasingly answering different questions with different standards of evidence about formally identical data structures. That is the strongest single argument for treating PBSA as a field in need of integrative theory rather than as a loose federation of applications.

### 5.3 Thematic evolution and its silences

**Figure 8; Table S19**. Distinctive title vocabulary by period (informative Dirichlet log-odds):

- **2000–2010:** *test, nonparametric, geostatistics, statistical, estimating, occurrence, inference, techniques, testing, observations, cluster, rainfall, landscape.*
- **2011–2020:** *precipitation, variation, disease, bayesian, hierarchical, digital, beijing, spatio-temporal, geostatistical, soil, taxi, flow, kernel.*
- **2021–2027:** *influencing, carbon, coupling, facilities, covid-, learning, extraction, factors, shanghai, landslide, dbscan, multi-source, measurement, clouds, machine.*

Read as a sequence, the field's self-description migrates from **the language of inference** (test, nonparametric, estimating, inference) through **the language of modelling** (bayesian, hierarchical, spatio-temporal) to **the language of engineering and attribution** (extraction, multi-source, influencing, factors, coupling).

The disappearing terms are as informative as the arriving ones. *Test*, *testing*, *inference* and *nonparametric* are all distinctive of the first period and depleted thereafter. A field that stops describing its work as testing has not necessarily stopped testing — but it has stopped regarding testing as the thing worth naming in a title.

Note also the appearance of *beijing* (2011–2020) and *shanghai* (2021–2027) as period-distinctive title terms. Individual Chinese cities are now sufficiently over-represented as case studies to register as thematic markers.

### 5.4 Methodological turning points

Three turning points are identifiable, each with a specific mechanism.

**TP1 — c. 2010: the model-based turn.** Bayesian hierarchical models and point-process models peak in 2011–2020. Mechanism: the arrival of computationally tractable inference for latent Gaussian models (INLA, SPDE) removed the principal barrier to fitting realistic point-process models. This turning point *raised* the field's inferential ambition.

**TP2 — c. 2017: the learning turn.** Growth accelerates sharply; classical machine learning and spatial clustering rise steeply; the data substrate inverts. Mechanism: cheap dense point data (POI, GPS, trajectories) plus commodity learning libraries. This turning point *raised* analytical throughput and *lowered* inferential ambition — the model-based methods that peaked at TP1 lose relative ground immediately afterwards.

**TP3 — c. 2021: the multi-source turn.** *Multi-source*, *coupling* and *influencing factors* become distinctive. Mechanism: integration of POI, remote sensing and administrative data in single studies, typically to attribute an outcome to a set of drivers.

The sequence TP1 → TP2 is the substantive puzzle of this review. A field acquired the tools for rigorous uncertainty-aware inference about point processes, and then, within roughly five years, its centre of gravity moved to methods that do not propagate uncertainty at all. Section 7 argues this is not a failure of scientific judgement but a predictable consequence of a structural gap between the rate at which data and computation advance and the rate at which epistemic infrastructure adapts.

### 5.5 Path dependency and geographical inequality

**Figure 15; Table S21** show national methodological profiles are strongly differentiated and are not scaled copies of a global average. Countries with strong field-measurement traditions retain geostatistical profiles; countries whose growth is recent and urban-data-driven show clustering-and-learning profiles. **Method choice is path-dependent on the data infrastructure a national research system happens to have.** This is the empirical basis for the claim that methods do not transfer neutrally across geographical contexts (Section 8.5).

**The production–problem asymmetry.** Of 574 studies with both geographies resolved, **89.5% are domestic** (at least one author affiliated in the country studied) and 10.5% are externally authored.

That aggregate figure is misleading, and the sensitivity analysis is essential:

| | Global North | Global South |
|---|---|---|
| **All studies** — case studies that are domestic | 87.6% | 91.0% |
| **Excluding China** — case studies that are domestic | **91.3%** | **74.4%** |

With China removed, the pattern reverses and becomes clear: **Global-South research contexts are studied by external authors roughly three times as often as Global-North contexts** (25.6% vs 8.7%). The aggregate figure conceals this entirely, because China is simultaneously the largest producer and the largest subject in the corpus and is coded to the Global South.

Only 19 studies (3.3% of resolvable pairs) show the strongest extractive configuration — a Global-South case study with *exclusively* Global-North affiliations. The dominant asymmetry in this corpus is therefore not large-scale research extraction. It is **absence**: 90 countries appear nowhere at all. The inequality is less about who analyses the Global South than about the fact that most of the world is never analysed by anyone.

### 5.6 Convergence: real, narrow, and mediated by bridge methods

**Figure 16; Table S20**. Multi-class studies rise 12.7% → 18.2% → 25.8%; studies combining learning methods with classical or inferential statistics rise 0.0% → 2.9% → **11.9%**. Convergence is real.

It is also narrow and structurally specific. Cross-class edges concentrate on three **bridge methods** — spatial clustering algorithms, hotspot statistics, and spatial regression — which act as the field's translation layer. These share a property: each is *interpretable as both a statistical estimator and a machine-learning primitive*. DBSCAN is a clustering algorithm to a computer scientist and a point-pattern method to a geographer; GWR is a local regression to a statistician and a spatially varying-coefficient model to a data scientist. Convergence is occurring precisely where methods are dual-citizens of both vocabularies, and hardly at all elsewhere.

### 5.7 Structural gaps

**Table S22** crosses 13 domains with 6 method classes. Of 78 cells, **9 are entirely empty** and **24 more fall below 10%** of the domain's studies. The empty cells are not random:

- Real-time and streaming methods are absent from most environmental, ecological and agricultural domains, despite continuous sensor networks being standard in all three.
- Network-constrained methods are almost entirely confined to transport and urban studies, despite crime, retail and epidemiological events being equally network-constrained in reality.
- Learning-based methods have barely entered the domains where classical point-process theory is strongest (ecology, disaster risk), while classical point-process theory has barely entered the domains where learning dominates (retail, tourism).

The last of these is the sedimentation and bifurcation results appearing simultaneously in a single matrix: the field's two branches have specialised into different application territories, and the theoretical machinery each has developed is not reaching the other's problems.

---

## 6. Three instruments induced from the corpus

**Figure 14** presents the three instruments together. Each is proposed by this review; each is justified by, but is not reducible to, the results above.

### 6.1 The PBSA taxonomy: a three-axis classification

Existing classifications of point-based methods are **flat lists** organised by estimator name. Flat lists cannot express why two methods with different names do the same epistemic work, or why one method behaves differently on different data. We propose an **orthogonal three-axis taxonomy** in which every study occupies exactly one position on each axis.

**Axis I — Representation: how the point is construed.** *Event · Sample · Entity · Trace* (Section 2.3). This axis governs the plausibility of independence assumptions, the meaning of "intensity", and the ethical status of the datum.

**Axis II — Inferential target: what is being estimated.** *Intensity/density · Interaction/dependence · Association with covariates · Prediction at unobserved locations.* This axis governs what would count as validation. Note that these targets require different validation logics, which is precisely what the warrant-erosion finding shows the field failing to observe.

**Axis III — Computational regime: how it is executed.** *Closed-form/analytic · Simulation-based · Optimisation/learning · Streaming/online.* This axis governs scalability, reproducibility and the practical accessibility of the method to a research system with limited computational resources — connecting method choice to the capacity-divergence outcome.

**Why the taxonomy is generative rather than merely descriptive.** Because the axes are orthogonal, the taxonomy defines a 4 × 4 × 4 = 64-cell space, of which the corpus populates only a fraction. Empty cells are *predictions of missing work*. Three examples the corpus shows to be empty or near-empty and that are substantively important:

- **Trace × Interaction × Streaming.** Online estimation of interaction structure in moving point data — the natural formalism for real-time crowd, fleet or epidemic-contact analysis — is essentially unattested.
- **Event × Prediction × Closed-form.** Analytically tractable predictive point-process models are almost entirely displaced by learning methods, despite being the only branch that yields calibrated predictive uncertainty.
- **Sample × Interaction × Optimisation.** Learning methods applied to *interaction* structure (rather than to intensity or covariate association) in sampled-field data are rare, though this is where geostatistics and machine learning would most productively meet.

A classification whose empty cells generate a research agenda is doing theoretical work, not bookkeeping.

### 6.2 A four-regime periodisation

The three periods used for reporting (2000–2010, 2011–2020, 2021–2027) are analytic conveniences imposed by the review design. The corpus itself suggests a different, and we argue more explanatory, division into **regimes** — configurations of data availability, dominant method and characteristic question that hang together and change together. Regime boundaries are analytical, not sharp, and are anchored to the turning points of Section 5.4.

| Regime | Period | Data condition | Dominant methods | Characteristic question | Corpus anchor |
|---|---|---|---|---|---|
| **R1 Estimation** | pre-2000 – c.2010 | scarce, curated, expensive | second-order statistics, kriging, CSR testing | *Is it clustered?* | kriging 30.0%, Ripley's *K* 9.1%; title terms *test, nonparametric, inference* |
| **R2 Integration** | c.2010 – c.2018 | multi-source, still curated | Bayesian hierarchical, LGCP, INLA | *Why is it clustered?* | Bayesian models peak 7.3%; point-process models peak 10.9%; terms *bayesian, hierarchical, spatio-temporal* |
| **R3 Saturation** | c.2018 – present | dense, passive, ambient | clustering, ML/DL, multi-source integration | *Where will it happen next?* | digital-trace 37.0%; ML 15.4%; terms *learning, machine, extraction, multi-source* |
| **R4 Accountability** | emerging / normative | dense but governed | context-aware, auditable, privacy-preserving analytics | *Should it be computed at all?* | **not observed**; preconditions only |

The periodisation makes an explicit claim: what changes between regimes is not primarily the estimator but the **binding constraint**. Under R1 the binding constraint is data scarcity, and methodological sophistication is spent on extracting maximum inference from few points. Under R2 it is model tractability. Under R3 the binding constraint is neither data nor computation — both are abundant — and the field has not yet identified what its new binding constraint is. Our answer, developed in Section 7, is that it is **warrant**: the capacity to justify, bound and defend an analytical claim.

**R4 is normative, not observed, and we mark it as such.** The corpus shows R4's *preconditions* — ethically encumbered data, privacy-relevant substrates, algorithmic methods — but not its arrival: ethics discussion is *lower* now than in 2000–2010. R4 is a projection about what the field will need, not a finding about what it has done. Conflating the two would be exactly the kind of unmarked extrapolation this review refuses elsewhere.

### 6.3 PB-SAM: a maturity framework for methodological development

**Purpose.** To assess whether a study, a literature or a research programme has developed the *warrant* commensurate with its analytical ambition. PB-SAM is deliberately not a quality score: a well-executed descriptive study can be scientifically excellent and score low.

| Dimension | 0 | 1 | 2 |
|---|---|---|---|
| **D1 Method specification** | no named method | one named method | multiple named, justified methods |
| **D2 Uncertainty** | none | one form (e.g. CIs) | multiple forms, incl. spatial-specific (MAUP, edge, positional) |
| **D3 Validation** | none | one procedure | multiple, incl. out-of-sample or independent |
| **D4 Data transparency** | provenance unstated | provenance stated | provenance + access conditions stated |
| **D5 Reproducibility** | none | code or data referenced | code *and* data available, workflow specified |

**Maturity levels.** Level 1 Emergent (0–3): a method is named; warrant is implicit. Level 2 Consolidating (4–6): data described, some validation. Level 3 Mature (7–10): uncertainty, validation and reproducibility all explicit.

**Observed distribution (2021–2027):** Level 1 **87.7%**, Level 2 **12.3%**, Level 3 **0.0%**.

**What PB-SAM is for, and what it is not for.** It is calibrated for *between-corpus and between-period comparison* and for use as a design checklist. It is **not** valid for ranking individual studies, is scored here from abstracts only (a lower bound on practice), and its dimensions are equally weighted by stipulation rather than by evidence. Anyone applying it to full texts should expect substantially higher scores; the *relative* pattern across D1–D5 is the informative quantity, and that pattern — accumulation on D1 and D4, stasis on D2, D3 and D5 — is robust to any uniform rescaling.

---

## 7. Theory: Point Intelligence Drift

### 7.1 The explanandum

Six findings require joint explanation. Any adequate theory must account for all six, not a subset:

1. Methods accumulate without retirement (§5.1).
2. Data substrate and method class have bifurcated into weakly connected branches (§5.2).
3. The model-based turn of c. 2010 was *reversed* rather than consolidated (§5.4).
4. Validation is displacing uncertainty quantification (§4.7).
5. Reporting of software, scale, data and ethics is largely absent and not improving (§4.6–4.7).
6. Production and problems are jointly, severely concentrated, and most of the world is absent (§4.4, §5.5).

Progress narratives explain (1) badly and (3) not at all. Paradigm-shift narratives explain (3) but predict the *displacement* that (1) refutes. Diffusion-of-innovation narratives explain (2) but are silent on (4) and (6). We propose a framework built to explain all six as manifestations of a single dynamic.

### 7.2 The core construct: the drift gap

> **Point Intelligence Drift (PID)** is the process by which a field's *analytical capability* — what it can compute from located data — advances faster than its *epistemic warrant* and *institutional reach* can be extended to cover what it computes. The accumulating residual is the **drift gap**.

Three definitions carry the framework:

- **Analytical capability (C):** the set of inferential and predictive operations the field can execute on point data at acceptable cost. Advanced by data, computation and demand.
- **Epistemic warrant (W):** the field's capacity to justify, bound, validate and reproduce the claims those operations generate. Advanced by theory, training, statistical infrastructure, norms and peer review.
- **Institutional reach (R):** the distribution of the capacity to perform and contest this analysis across research systems and geographies.

**The drift gap** is the divergence of C from W and R:  `G = C − min(W, R)`.

The formulation is deliberately a *minimum*, not an average: capability that is well-warranted but unavailable to the places facing the problem is as much a drift as capability that is widely available but unjustified. Drift is bounded below at zero — capability cannot be less than nothing — but has no upper bound, which is why the framework predicts widening rather than equilibrium.

**Drift is not error.** It is the normal condition of a field whose inputs improve discontinuously (data volumes, hardware) while its warrant improves continuously and slowly (norms, curricula, review standards). A field can be entirely composed of competent researchers acting rationally and still drift.

### 7.3 Drivers, brakes and the drift mechanism

**Figure 13** presents the framework diagrammatically.

**Drivers (accelerating C).**

- **D1 Data densification.** Points become abundant, passive and ambient (§4.5: 1.8% → 37.0%). *Mechanism:* abundance makes methods that were previously data-starved feasible, and makes methods that assume scarcity look wasteful.
- **D2 Computational abundance.** Estimation moves from a binding constraint to a non-constraint. *Mechanism:* removes the selection pressure that formerly favoured parsimonious, analytically tractable estimators — the same pressure that made uncertainty propagation cheap to include, because closed-form estimators carry their standard errors with them.
- **D3 Application pull.** Users increasingly want *forecasts and targets*, not *explanations and tests* (§5.3). *Mechanism:* shifts the operative criterion of success from inferential validity to predictive performance.

**Brakes (extending W and R).**

- **B1 Epistemic infrastructure.** Theory, curricula, reporting norms, reviewer expertise. *Rate-limited* by generational turnover in training and by the slow revision of disciplinary standards.
- **B2 Institutional geography.** Research capacity, data access rights, computational infrastructure, licensing. *Rate-limited* by capital, national policy and commercial data governance.

**The mechanism.** D1–D3 respond to exogenous technological and commercial change on a timescale of one to three years. B1–B2 respond on a timescale of a decade or more. The gap is therefore a **rate mismatch**, not a failure of intent — which is why exhortation ("researchers should report uncertainty") has demonstrably not closed it: §4.7 shows two decades of such exhortation producing a movement in D2 from 0.05 to 0.06 out of 2.

### 7.4 The four outcomes

The drift gap is not directly observable; it manifests as four measurable outcomes, each mapping onto findings from Sections 4–5.

**O1 — Methodological sedimentation.** Because warrant is what licenses *retirement* (a method is abandoned when the field agrees its assumptions are indefensible), a field with lagging warrant cannot retire anything. New methods are deposited on top of old ones. *Evidence:* multi-class studies 12.7% → 25.8%; purely classical studies undiminished (§5.1).

**O2 — Substrate bifurcation.** New substrates arrive faster than the field can extend existing theory to cover them, so each substrate grows its own local analytical tradition with its own local standards. *Evidence:* the Sankey structure (Figure 7); divergent vocabularies (§5.3); the domain–method gap matrix (§5.7).

**O3 — Warrant erosion.** Under D3, predictive validation is cheap, legible and demanded, while uncertainty quantification is expensive, technical and rarely demanded. The field substitutes the first for the second. *Evidence:* learning studies validate at 30.1% and quantify uncertainty at 3.3%, against 13.4% and 6.9% for classical studies; PB-SAM D2 and D3 static across two decades (§4.7).

**O4 — Capacity divergence.** Because R advances more slowly than C, and because C's advance is itself concentrated where data and computation are concentrated, growth in capability accrues disproportionately to already-advantaged systems. *Evidence:* Gini 0.774; 90 absent countries; South–South ties 9.6%; declining international collaboration (§4.4, §4.8, §5.5).

### 7.5 Moderators and boundary conditions

The strength of O1–O4 is conditioned by four regimes.

- **M1 Scale regime.** Drift is strongest at scales where data are densest. Micro and city scales drift fastest; national and continental analysis retains stronger warrant because sparse data force explicit models.
- **M2 Uncertainty regime.** Where positional error, MAUP, edge effects and temporal misalignment are *unavoidably salient*, warrant erosion is retarded. Fields analysing sparse, expensive, error-prone measurements keep their error vocabulary; fields analysing abundant cheap points lose it.
- **M3 Ethical regime.** Where data are personal and regulated, external governance substitutes for internal warrant — with the important side-effect that ethical compliance can be mistaken for epistemic warrant.
- **M4 Knowledge-production geography.** Drift manifests differently by position: capability-rich systems drift towards O3 (warrant erosion); capability-poor systems experience O4 (exclusion) without ever accessing the capability.

**Boundary conditions.** PID is proposed for **data-intensive analytical fields undergoing exogenous substrate change**. It does not apply where: (i) data supply is stable (drivers absent); (ii) warrant is externally enforced by regulatory gatekeeping, as in clinical trials or aviation safety (B1 is not rate-limited); (iii) the field is small enough for direct normative control by a single community; or (iv) capability is bounded by physical measurement rather than computation. PID is a theory of *drift under abundance*, and abundance is its scope condition.

**Falsifying observations.** PID is wrong if a field shows rising capability with *stable or rising* uncertainty reporting; if new substrates are absorbed by existing theory without forming separate traditions; if methods are demonstrably retired; or if capability diffuses geographically faster than it concentrates.

### 7.6 Propositions

Eleven testable propositions follow. **These are theoretical predictions, not findings.** Where this review's corpus provides *consistent evidence*, that is noted — consistency is not confirmation, since the propositions were induced from the same corpus. Independent tests require new data, and the required design is stated for each.

| # | Proposition | Status in this corpus | Independent test |
|---|---|---|---|
| **P1** | The drift gap widens monotonically while data-substrate change outpaces norm change. | Consistent (complexity:rigour 3.71 → 4.02) | Replicate on WoS + Dimensions; test for monotonicity with full-text coding. |
| **P2** | Methods are not retired; the count of coexisting method classes rises monotonically. | Consistent (12.7% → 25.8% multi-class) | Track method survival curves over 40 years in a second field. |
| **P3** | Each new data substrate generates a distinct analytical tradition within ~5 years, with <25% method overlap with incumbent traditions. | Consistent (Figure 7 bifurcation) | Measure method-overlap coefficients between substrate cohorts by year of substrate arrival. |
| **P4** | Predictive validation and uncertainty quantification are substitutes, not complements, in fields under application pull. | Consistent (30.1%/3.3% vs 13.4%/6.9%) | Full-text coding; test for negative partial correlation controlling for domain and venue. |
| **P5** | Warrant erosion is strongest where data are cheapest per observation. | Untested | Regress uncertainty reporting on marginal data-acquisition cost across substrates. |
| **P6** | Where measurement error is unavoidably salient (M2), warrant erosion is attenuated. | Untested | Compare uncertainty reporting in GPS-trace vs geocoded-address studies. |
| **P7** | Capability concentrates faster than it diffuses; production Gini rises while the number of contributing countries rises. | Consistent (Gini 0.774, 79 countries) | Time-series of Gini and country count on an expanded corpus. |
| **P8** | Under drift, international collaboration *falls* as a large capability-rich system scales domestically. | Consistent (38.1% → 22.1%) | Decompose collaboration rate by producer system; test China-excluded series. |
| **P9** | Ethical engagement lags substrate change by at least one regime period. | Consistent (ethics 7.3% → 3.5% while trace data 1.8% → 37.0%) | Cross-lagged panel of ethics terms against substrate composition. |
| **P10** | Cross-class convergence occurs only via bridge methods interpretable in both vocabularies. | Consistent (§5.6) | Network analysis of method co-occurrence; test betweenness of dual-citizen methods. |
| **P11** | Interventions on B1 (norms, standards, review) reduce the drift gap; interventions on D1–D3 do not. | Untested; **policy-critical** | Difference-in-differences around journal reporting-standard adoption. |

P11 is the framework's practical core: if drift is a rate mismatch, only accelerating the brakes closes it. Building better tools cannot.

### 7.7 How PID differs from existing frameworks

| Framework | Central claim | What it explains here | What it cannot explain | PID's difference |
|---|---|---|---|---|
| **Spatial-analysis method theory** (point-process theory, geostatistics) | Estimator properties under assumptions | Why individual methods behave as they do | Why methods are adopted, retained or abandoned; geography of use | PID is a theory of the field's dynamics, not of estimators |
| **GIScience** | Representation, uncertainty and cognition of geographical information | Why representational choice matters; the MAUP and scale literatures | Why representational commitments change over time in response to data supply | PID makes substrate change the exogenous driver and treats representation as endogenous |
| **Spatial data science** | Integration of statistics, computation and workflow | The rise of tooling, open source and reproducibility discourse | Why reproducibility discourse rises while reproducibility practice does not (4.5%) | PID predicts exactly this gap: discourse is cheap, warrant is slow |
| **Geocomputation** | Computational strategy enables new analysis | The learning turn and scalability | Why capability advances did not bring warrant advances | PID separates capability from warrant as distinct, differently-paced quantities |
| **Data-driven geography / GeoAI** | New data and AI transform geographical inquiry | The substrate inversion; the learning ascent | Sedimentation (why classical methods persist) and O4 (concentration) | PID predicts persistence and concentration as necessary consequences, not anomalies |
| **Kuhnian paradigm shift** | Incommensurable replacement | Discontinuities at TP1 and TP2 | The absence of replacement — old methods do not die | PID predicts accumulation, not succession |
| **Diffusion of innovations** | S-curve adoption of new methods | The learning ascent's shape | Why adoption is substrate-partitioned rather than field-wide | PID makes the substrate, not the individual adopter, the unit of diffusion |
| **Data colonialism / critical data studies** | Extraction of data and value from the periphery | The geography of production | Why *absence* rather than extraction dominates (only 3.3% extractive) | PID identifies non-participation, not extraction, as the modal inequality in this field |

The distinctive move is the separation of **capability**, **warrant** and **reach** into three quantities with different drivers and different rates. Existing frameworks treat these as bundled — a field that can do more is assumed to know more and to spread more. PID's claim is that they unbundle under abundance, and that the unbundling is what the empirical record of point-based spatial analysis actually shows.

---

## 8. Critical discussion

### 8.1 Limitations of this review

Stated first, and without hedging, because they bound everything above.

**Single database.** One Scopus export. No Web of Science, Dimensions, Lens or OpenAlex; no grey literature, theses, books or non-indexed regional journals. Scopus under-indexes Global-South and non-English venues, so §4.4's inequality findings are **conservative in direction but of uncertain magnitude** — the true distribution is more unequal than Scopus shows in some respects and less so in others, and this review cannot say which dominates.

**Abstract-only coding.** Every method, data, software, uncertainty, validation, reproducibility and ethics measure is derived from titles and abstracts. **Absence of evidence in an abstract is not evidence of absence in the full text.** All rigour percentages are lower bounds on *reporting*, and reporting is not practice. Cross-period comparison additionally assumes reporting conventions are stable over 26 years — an assumption that is certainly imperfect and probably biases *against* the earliest period, where abstracts are shorter and more terse. This is the single largest threat to the warrant-erosion finding (O3), and we state plainly that O3 requires full-text confirmation before it can be treated as established.

**Single-reviewer, rule-based screening.** No second screener; no inter-rater reliability. Precision 0.90 (95% CI 0.80–0.95), false-omission rate 0.05–0.15. Residual misclassification concentrates at the sensor-processing boundary. Roughly 240–720 eligible studies were probably not recovered. **The corpus is a construct-valid sample, not a census.**

**No citation, author or journal data.** Influence, intellectual structure, co-citation communities and journal ecology are not addressed (§3.7). A review claiming to characterise a field's *intellectual* structure without citation data is characterising its *productive* structure only, and we do not claim otherwise.

**Domain under-representation is partly an artefact.** §4.3 shows crime (2.8%) and public health (9.7%) at implausibly low shares given their real-world prominence in point-based analysis. We attribute this to venue-specific abstract conventions rather than to the underlying literature, and we treat domain shares as measures of *what this corpus contains*, not of what the world contains.

**English-language and lexicon bias.** The coding instrument is English-language and reflects the authors' methodological vocabulary. Methods named in other traditions or other languages are systematically under-detected.

**Theory induced from the same corpus that illustrates it.** PID was induced from these data. The consistency noted in §7.6 is therefore **not** confirmation. This is the standard limitation of inductive theory-building, and it is why §7.6 specifies independent tests rather than claiming validation.

**Non-exclusive coding.** Categories overlap; a study can be in many. Percentages do not sum to 100 and cannot be treated as compositional shares.

### 8.2 Reproducibility and open science

4.5% of studies show any abstract-level reproducibility practice; 94.2% name no software. Against this, the field's *tooling* is unusually open — spatstat, PySAL, GeoDa, R-INLA, sf and GRASS are all free and open source, and the corpus's second-largest publisher is a fully open-access house.

The gap between open *tools* and closed *workflows* is the reproducibility problem in this field. Using open software is not reproducibility; specifying versions, parameters, bandwidths, seeds and data provenance is. Point-based analysis is unusually sensitive to exactly these choices: a kernel density surface is a function of bandwidth and kernel far more than of the underlying points, and a DBSCAN clustering is a function of ε and minPts. **Reporting the method name without the parameter values is, for most point-based methods, not reporting the method.**

A second obstacle is genuinely hard rather than merely neglected: point data are frequently non-shareable. Individual crime locations, patient addresses, mobile-phone traces and endangered-species occurrences cannot simply be posted. This is a real constraint, and the answer is not to demand raw-data release but to require **code release, synthetic-data release, and analysis-ready aggregation with documented masking** (§10.3).

### 8.3 Privacy, surveillance, ethics and algorithmic bias

3.6% of studies engage ethics or privacy at abstract level, *down* from 7.3% in 2000–2010, over exactly the period when the modal data point changed from a soil sample to a platform record. This is the corpus's most troubling single juxtaposition.

The concern is not abstract. Point data are the most re-identifiable data structure in geography: four spatio-temporal points are sufficient to uniquely identify the large majority of individuals in a mobile-phone dataset. Geographic masking, aggregation and differential privacy exist precisely because point locations are quasi-identifiers. A literature in which 11.7% of recent studies use mobile-phone or GPS trajectory data and 3.5% mention privacy has a mismatch that is not defensible on the grounds that most studies use POI data.

Three further risks the corpus barely engages:

- **Surveillance transfer.** Hotspot and predictive methods developed for one purpose transfer readily to policing and border control. The methods are neutral; their deployment is not, and neutrality of method has never been an argument against considering deployment.
- **Algorithmic bias with a spatial signature.** Point data record *what was observed*, not what occurred. Crime points record policing; disease points record care-seeking and testing access; POI points record commercial digitisation. Fitting an intensity surface to these and calling it the intensity of the phenomenon confuses observation with occurrence — and because observation effort is spatially structured by exactly the inequalities under study, the resulting bias is spatially systematic rather than random.
- **Consent at the point level.** No workable consent model exists for passively generated location data, and the field has largely proceeded without one.

### 8.4 Geographical inequality and knowledge asymmetry

The headline is **absence**, not extraction. Only 3.3% of resolvable studies show a Global-South case with exclusively Global-North authorship. But 90 of 176 countries appear in no role at all, and 38 of 51 African states never appear as an author affiliation.

This matters analytically, not only ethically. Point-based methods encode assumptions about the data environments in which they were developed: complete address systems, reliable geocoding, dense sensor networks, digitised facility inventories. Applied where addresses are informal, geocoding is sparse and POI coverage is partial, the same estimators return biased and often confidently wrong answers. A field whose methods are developed almost entirely in high-coverage data environments has, without deciding to, restricted its own external validity.

The 9.6% South–South collaboration share compounds this: research systems facing structurally similar data environments — informal settlement, partial cadastres, incomplete registration — are not connected to one another, and so cannot pool the methodological adaptations each is forced to invent locally.

### 8.5 Uncertainty, scale and transferability

The corpus's engagement with the specific uncertainties of point data is thin. Positional and geocoding uncertainty, MAUP and edge effects together appear in a small minority of abstracts, and PB-SAM D2 does not move across two decades.

This is not a minor omission, because these are not generic statistical caveats — they are the mechanisms by which point-based conclusions actually fail:

- **Positional uncertainty** propagates non-linearly through density estimation; a bandwidth smaller than the geocoding error produces structure that is pure artefact.
- **Scale and MAUP** determine hotspot geometry: the same points yield different, equally defensible hotspots at different bandwidths, and the corpus rarely reports bandwidth at all.
- **Edge effects** bias second-order statistics near study-area boundaries — and study areas in applied work are administrative, hence arbitrary with respect to the process.
- **Temporal misalignment** between point events and covariates measured over different intervals is essentially unaddressed in the corpus.

**Transferability** follows directly. Because method performance depends on the data environment (§5.5), a method validated in one context carries no automatic warrant in another. The corpus contains very few cross-context validations. We regard this as the single most important methodological gap the review identifies.

---

## 9. Contributions

### 9.1 Theoretical contributions

1. **Point Intelligence Drift (PID)** — a framework separating analytical capability, epistemic warrant and institutional reach as differently-paced quantities, with defined constructs, mechanisms, moderators, boundary conditions and eleven falsifiable propositions (§7).
2. **The drift gap** as a measurable theoretical construct, operationalised here as the complexity-to-rigour ratio and shown to widen from 3.71 to 4.02 (§7.2, §4.7).
3. **Methodological sedimentation** — a theorised alternative to both paradigm-shift and progress narratives, explaining why analytical fields accumulate rather than replace, and identifying lagging warrant as the mechanism that prevents retirement (§5.1, §7.4).
4. **Substrate bifurcation** — the proposition that new data substrates generate distinct analytical traditions rather than being absorbed by existing theory, making the *substrate* rather than the individual researcher the unit of methodological diffusion (§5.2, §7.4).
5. **Warrant erosion** — the proposition that predictive validation and uncertainty quantification act as substitutes rather than complements under application pull, with the corpus showing the substitution directly (§4.7, §7.4).

### 9.2 Methodological contributions

1. **A formal, two-criterion operational definition of point-based spatial analysis** (criterion A: point-referenced units; criterion B: spatial-analytical operation), with an explicit sufficiency rule and four stated boundary conditions — the first such definition usable as a screening instrument (§2, §3.3).
2. **A published, executable, auditable screening instrument** with a documented three-round audit-and-revision history, reported precision and false-omission rate, and a per-record decision ledger for all 5,712 screened records (§3.4–3.5).
3. **Separation of case-study geography from affiliation geography** as independently resolved variables, with a disambiguated toponym gazetteer, enabling the production–problem asymmetry analysis that conflated designs cannot perform (§3.6, §5.5).
4. **Identification and correction of publisher copyright boilerplate as a systematic contaminant** of abstract-based geographical inference — an artefact that made Switzerland the third-ranked case-study country before cleaning, and which we have not seen documented in the bibliometric literature (§3.4).
5. **The PB-SAM maturity instrument** with an explicit five-dimension rubric, a stated validity domain and stated invalid uses (§6.3).

### 9.3 Empirical contributions

1. **The substrate inversion**: digital-trace data 1.8% → 37.0% against institutional data 10.9% → 3.2% across the three periods (§4.5).
2. **Sedimentation quantified**: purely classical studies are as prevalent in 2021–2027 (9.3%) as in 2000–2010 (12.7%) despite learning methods reaching 21.4% (§5.1).
3. **The reversal of the model-based turn**: Bayesian hierarchical and point-process methods peak in 2011–2020 and lose relative ground thereafter — a transition, to our knowledge, not previously documented (§4.2, §5.4).
4. **The validation–uncertainty substitution**: learning studies validate at 30.1% and quantify uncertainty at 3.3%, against 13.4% and 6.9% for classical studies (§4.7).
5. **The joint geography of production and problems**: production Gini 0.774 and problem Gini 0.737; 90 of 176 countries absent in any role; South–South ties 9.6%; international collaboration declining from 38.1% to 22.1% (§4.4, §4.8, §5.5).

### 9.4 Practical and policy contributions

1. **A reporting standard** for point-based spatial analysis (§10.3), targeted at the specific reporting failures the corpus documents rather than at generic open-science aspiration.
2. **A method-selection heuristic** derived from the taxonomy: select on Axis I (what the point *is*) before Axis II or III, because the representation determines which independence and stationarity assumptions are even available (§6.1).
3. **A research-gap register** — 9 empty and 24 thin cells in the domain × method matrix, published as **Table S22** and directly actionable as a project-selection tool (§5.7).
4. **Guidance for funders and editors** on where intervention is predicted to work: PID's P11 holds that interventions on norms and review standards close the drift gap while interventions on tooling do not (§7.6, §10.4).
5. **An equity diagnostic**: the finding that absence rather than extraction is the modal inequality reframes capacity-building priorities away from authorship-share policing towards enabling first participation and South–South connection (§8.4, §10.4).

---

## 10. A research agenda for the next decade

### 10.1 Priority research questions

**On warrant.**
- **Q1.** Does the validation–uncertainty substitution (P4) survive full-text coding, and does it hold within domains and venues?
- **Q2.** What is the actual sensitivity of published point-based conclusions to bandwidth, ε, and geocoding error? A large-scale re-analysis of published studies with reported parameters would establish whether the field's conclusions are robust to the choices it does not report.
- **Q3.** Can calibrated predictive uncertainty be made as cheap and legible for learning-based spatial models as cross-validated accuracy currently is? This is the single highest-leverage methodological target the review identifies.

**On substrate and transfer.**
- **Q4.** Do methods validated in high-coverage data environments retain their properties in partial-coverage environments? Systematic cross-context validation is almost entirely missing.
- **Q5.** Can point-process theory be extended to trace data, where observations are neither independent nor a sample of a fixed population, without abandoning its inferential guarantees?
- **Q6.** What are the properties of estimators under *observation-effort* bias with spatial structure — the crime-recorded-vs-crime-occurred problem stated generally?

**On geography and equity.**
- **Q7.** What methodological adaptations have research systems in partial-coverage environments already invented locally, and why have they not diffused?
- **Q8.** Does South–South collaboration, where it exists, produce systematically different methodological profiles?

**On ethics.**
- **Q9.** What is a workable consent and governance model for analysis of passively generated point data, and what does it cost in analytical power?
- **Q10.** How do privacy-preserving transformations (masking, aggregation, differential privacy) interact with the specific estimators this field uses — and what is the actual utility–privacy frontier for kernel density, scan statistics and point-process models?

### 10.2 Methodological recommendations

1. **Choose the method from the representation, not the convention.** Establish first whether the point is an event, sample, entity or trace; independence and stationarity assumptions follow from this and from nothing else.
2. **Report the parameters, not just the method name.** Bandwidth and kernel; ε and minPts; variogram model and range; edge correction; window definition; CRS.
3. **Treat the study window as an analytical choice.** Report sensitivity to boundary definition; apply edge correction and say which.
4. **Propagate positional uncertainty** where geocoding or GPS error is plausibly of the same order as the analytical scale — and state the comparison explicitly.
5. **Validate across contexts, not only across folds.** Spatial cross-validation where prediction is the target; genuine out-of-region validation where transferability is claimed.
6. **Distinguish observation from occurrence.** State the observation process; where effort is spatially structured, model it or bound its effect.
7. **Where uncertainty cannot be quantified, say so explicitly.** An acknowledged gap is warrant; an unacknowledged one is drift.

### 10.3 A reporting standard for point-based spatial analysis (PBSA-REP)

Proposed as a short, checkable list targeted at the failures documented in §4.6–4.7. Items marked **[A]** should appear in the abstract.

**Data.** (1) Substrate and provenance **[A]**; (2) unit construal (event/sample/entity/trace); (3) n points and spatial extent **[A]**; (4) temporal coverage and resolution; (5) positional accuracy or geocoding match rate; (6) known observation-effort structure; (7) access conditions and licence.

**Method.** (8) Named method(s) **[A]**; (9) all parameter values; (10) edge-correction treatment; (11) window/study-area definition and justification; (12) CRS and projection.

**Warrant.** (13) Uncertainty quantification, or an explicit statement that none was performed; (14) validation procedure and its target; (15) sensitivity to the two most consequential parameters; (16) MAUP/scale sensitivity where aggregation is used.

**Reproducibility.** (17) Software and version **[A]**; (18) code availability; (19) data availability *or* synthetic/masked surrogate; (20) analysis-ready derived data.

**Ethics.** (21) Personal-data status; (22) masking or privacy transformation applied and its parameters; (23) ethical approval where applicable; (24) statement on foreseeable secondary use where methods are surveillance-transferable.

### 10.4 Guidance for stakeholders

**Researchers.** Adopt PBSA-REP. Report parameters. Report what you did not do. Select methods from Axis I. Where you work on a context under-represented in the literature, say so explicitly — that is a contribution, not a limitation.

**Journal editors.** The corpus indicates that exhortation has not worked for two decades; structural requirements might. Require parameter reporting for point-based methods as a condition of review, as is standard for statistical reporting in clinical journals. Require a software and version statement. Accept explicit "no uncertainty quantification was performed" statements rather than incentivising silence. Recognise cross-context validation and negative transferability results as publishable contributions — currently they are not, which is why Q4 is unanswered.

**Funders.** PID's P11 predicts that tool-building does not close the drift gap and norm-building does. Fund the unglamorous: reporting infrastructure, curricula, cross-context validation studies, and — specifically — South–South methodological networks, since the 9.6% figure indicates the missing links are lateral rather than vertical. Fund first participation for the 90 absent countries ahead of authorship-share interventions.

**Practitioners.** Treat any hotspot map without a stated bandwidth as an unspecified analysis. Ask what the points record — occurrence or observation — before acting on their density. Do not transfer a method across contexts on the strength of in-context validation alone.

**Policymakers.** Point-based analysis produces spatially explicit, individually consequential outputs: where to patrol, where to inspect, where to site services. Require that deployed models state their uncertainty and their observation-process assumptions. Where analysis informs enforcement, require an explicit assessment of whether the underlying points record the phenomenon or the enforcement.

---

## 11. Conclusion

Point-based spatial analysis has, over 2000–2026, grown roughly eightfold in annual output, inverted its data substrate, absorbed machine learning, and urbanised its thematic centre of gravity. On any capability measure the field has advanced dramatically.

This review's central finding is that its warrant has not. Uncertainty treatment appears in 6.2% of abstracts, reproducibility practice in 4.5%, ethical engagement in 3.6% — the last *lower* than twenty years ago, over exactly the period when the field's data became personal. No study in the corpus reaches the top maturity band. The methods that most rigorously propagate uncertainty peaked around 2015 and have lost ground since. And the whole enterprise is performed by, and about, a small and overlapping set of places: 90 of 176 countries appear nowhere in 913 studies.

We have argued that these are not separate problems but one, and we have named it: **Point Intelligence Drift**, the widening gap between what a field can compute and what it can warrant, justify and distribute. Drift is not incompetence. It is what happens when data and computation improve on a two-year cycle while norms, curricula and institutional capacity improve on a twenty-year one. It predicts sedimentation, bifurcation, warrant erosion and capacity divergence, and this corpus displays all four.

The prescription follows from the diagnosis. The field's binding constraint is no longer methodological capability; better methods will not fix a warrant deficit. What closes a rate mismatch is accelerating the slow side: reporting standards that are checked rather than encouraged, validation across contexts rather than across folds, ethical engagement proportionate to the data actually in use, and the deliberate extension of analytical capacity to the places currently absent from the record. The instruments proposed here — the taxonomy, the periodisation, the maturity framework, the reporting standard and the eleven propositions — are offered as tools for that work, and as claims that can be tested and found wrong.

---

## References

*Note on verification.* The references below are canonical, peer-reviewed works cited for their substantive claims. **External bibliographic APIs (Crossref, OpenAlex) were unreachable from the analysis environment**, so bibliographic details could not be machine-verified against publisher records; authors should confirm volume, page and DOI details against the publisher of record before submission. No reference is included that the authors are not confident exists as a published work. The 913 studies constituting the analysed corpus are listed separately in `tables/T23_included_studies_register.csv` (**Table S23**) with DOIs.

Anselin, L. (1995). Local indicators of spatial association—LISA. *Geographical Analysis*, 27(2), 93–115.

Anselin, L. (2010). Thirty years of spatial econometrics. *Papers in Regional Science*, 89(1), 3–25.

Anselin, L., Syabri, I., & Kho, Y. (2006). GeoDa: An introduction to spatial data analysis. *Geographical Analysis*, 38(1), 5–22.

Armstrong, M. P., Rushton, G., & Zimmerman, D. L. (1999). Geographically masking health data to preserve confidentiality. *Statistics in Medicine*, 18(5), 497–525.

Arribas-Bel, D., & Reades, J. (2018). Geography and computers: Past, present, and future. *Geography Compass*, 12(10), e12403.

Baddeley, A., Rubak, E., & Turner, R. (2015). *Spatial Point Patterns: Methodology and Applications with R*. CRC Press.

Baddeley, A., & Turner, R. (2005). spatstat: An R package for analyzing spatial point patterns. *Journal of Statistical Software*, 12(6), 1–42.

Besag, J., York, J., & Mollié, A. (1991). Bayesian image restoration, with two applications in spatial statistics. *Annals of the Institute of Statistical Mathematics*, 43(1), 1–20.

Bezuidenhout, L., Leonelli, S., Kelly, A. H., & Rappert, B. (2017). Beyond the digital divide: Towards a situated approach to open data. *Science and Public Policy*, 44(4), 464–475.

Bivand, R. S., Pebesma, E., & Gómez-Rubio, V. (2013). *Applied Spatial Data Analysis with R* (2nd ed.). Springer.

Blondel, V. D., Decuyper, A., & Krings, G. (2015). A survey of results on mobile phone datasets analysis. *EPJ Data Science*, 4, 10.

Boyd, D., & Crawford, K. (2012). Critical questions for big data. *Information, Communication & Society*, 15(5), 662–679.

Brunsdon, C., & Comber, A. (2021). Opening practice: Supporting reproducibility and critical spatial data science. *Journal of Geographical Systems*, 23, 477–496.

Brunsdon, C., Fotheringham, A. S., & Charlton, M. (1996). Geographically weighted regression: A method for exploring spatial nonstationarity. *Geographical Analysis*, 28(4), 281–298.

Chainey, S., Tompson, L., & Uhlig, S. (2008). The utility of hotspot mapping for predicting spatial patterns of crime. *Security Journal*, 21, 4–28.

Clark, P. J., & Evans, F. C. (1954). Distance to nearest neighbor as a measure of spatial relationships in populations. *Ecology*, 35(4), 445–453.

Cliff, A. D., & Ord, J. K. (1973). *Spatial Autocorrelation*. Pion.

Couldry, N., & Mejias, U. A. (2019). Data colonialism: Rethinking big data's relation to the contemporary subject. *Television & New Media*, 20(4), 336–349.

Crampton, J. W., Graham, M., Poorthuis, A., Shelton, T., Stephens, M., Wilson, M. W., & Zook, M. (2013). Beyond the geotag: Situating 'big data' and leveraging the potential of the geoweb. *Cartography and Geographic Information Science*, 40(2), 130–139.

Cressie, N. (1993). *Statistics for Spatial Data* (revised ed.). Wiley.

Datta, A., Banerjee, S., Finley, A. O., & Gelfand, A. E. (2016). Hierarchical nearest-neighbor Gaussian process models for large geostatistical datasets. *Journal of the American Statistical Association*, 111(514), 800–812.

de Montjoye, Y.-A., Hidalgo, C. A., Verleysen, M., & Blondel, V. D. (2013). Unique in the crowd: The privacy bounds of human mobility. *Scientific Reports*, 3, 1376.

Diggle, P. J. (2013). *Statistical Analysis of Spatial and Spatio-Temporal Point Patterns* (3rd ed.). CRC Press.

Diggle, P. J., Moraga, P., Rowlingson, B., & Taylor, B. M. (2013). Spatial and spatio-temporal log-Gaussian Cox processes: Extending the geostatistical paradigm. *Statistical Science*, 28(4), 542–563.

Elith, J., & Leathwick, J. R. (2009). Species distribution models: Ecological explanation and prediction across space and time. *Annual Review of Ecology, Evolution, and Systematics*, 40, 677–697.

Ester, M., Kriegel, H.-P., Sander, J., & Xu, X. (1996). A density-based algorithm for discovering clusters in large spatial databases with noise. In *Proceedings of KDD-96* (pp. 226–231).

Fotheringham, A. S., Brunsdon, C., & Charlton, M. (2002). *Geographically Weighted Regression: The Analysis of Spatially Varying Relationships*. Wiley.

Fotheringham, A. S., & Wong, D. W. S. (1991). The modifiable areal unit problem in multivariate statistical analysis. *Environment and Planning A*, 23(7), 1025–1044.

Gehlke, C. E., & Biehl, K. (1934). Certain effects of grouping upon the size of the correlation coefficient in census tract material. *Journal of the American Statistical Association*, 29(185A), 169–170.

Getis, A., & Ord, J. K. (1992). The analysis of spatial association by use of distance statistics. *Geographical Analysis*, 24(3), 189–206.

Goodchild, M. F. (1992). Geographical information science. *International Journal of Geographical Information Systems*, 6(1), 31–45.

Goodchild, M. F. (2007). Citizens as sensors: The world of volunteered geography. *GeoJournal*, 69(4), 211–221.

Graham, M., De Sabbata, S., & Zook, M. A. (2015). Towards a study of information geographies: (Im)mutable augmentations and a mapping of the geographies of information. *Geo: Geography and Environment*, 2(1), 88–105.

Haklay, M. (2010). How good is volunteered geographical information? A comparative study of OpenStreetMap and Ordnance Survey datasets. *Environment and Planning B*, 37(4), 682–703.

Illian, J., Penttinen, A., Stoyan, H., & Stoyan, D. (2008). *Statistical Analysis and Modelling of Spatial Point Patterns*. Wiley.

Janowicz, K., Gao, S., McKenzie, G., Hu, Y., & Bhaduri, B. (2020). GeoAI: Spatially explicit artificial intelligence techniques for geographic knowledge discovery and beyond. *International Journal of Geographical Information Science*, 34(4), 625–636.

Kedron, P., Frazier, A. E., Trgovac, A. B., Nelson, T., & Fotheringham, A. S. (2021). Reproducibility and replicability in geographical analysis. *Geographical Analysis*, 53(1), 135–147.

Kitchin, R. (2014). Big Data, new epistemologies and paradigm shifts. *Big Data & Society*, 1(1), 1–12.

Krige, D. G. (1951). A statistical approach to some basic mine valuation problems on the Witwatersrand. *Journal of the Chemical, Metallurgical and Mining Society of South Africa*, 52(6), 119–139.

Kulldorff, M. (1997). A spatial scan statistic. *Communications in Statistics – Theory and Methods*, 26(6), 1481–1496.

Kwan, M.-P. (2012). The uncertain geographic context problem. *Annals of the Association of American Geographers*, 102(5), 958–968.

Leszczynski, A. (2015). Spatial big data and anxieties of control. *Environment and Planning D: Society and Space*, 33(6), 965–984.

Lindgren, F., Rue, H., & Lindström, J. (2011). An explicit link between Gaussian fields and Gaussian Markov random fields: The stochastic partial differential equation approach. *Journal of the Royal Statistical Society: Series B*, 73(4), 423–498.

Lloyd, C. D. (2010). *Spatial Data Analysis: An Introduction for GIS Users*. Oxford University Press.

Lundberg, S. M., & Lee, S.-I. (2017). A unified approach to interpreting model predictions. In *Advances in Neural Information Processing Systems 30*.

Matheron, G. (1963). Principles of geostatistics. *Economic Geology*, 58(8), 1246–1266.

Meyer, H., & Pebesma, E. (2021). Predicting into unknown space? Estimating the area of applicability of spatial prediction models. *Methods in Ecology and Evolution*, 12(9), 1620–1633.

Miller, H. J., & Goodchild, M. F. (2015). Data-driven geography. *GeoJournal*, 80(4), 449–461.

Møller, J., & Waagepetersen, R. P. (2004). *Statistical Inference and Simulation for Spatial Point Processes*. Chapman & Hall/CRC.

Moraga, P. (2019). *Geospatial Health Data: Modeling and Visualization with R-INLA and Shiny*. CRC Press.

Moran, P. A. P. (1950). Notes on continuous stochastic phenomena. *Biometrika*, 37(1/2), 17–23.

Nelson, T. A., & Boots, B. (2008). Detecting spatial hot spots in landscape ecology. *Ecography*, 31(5), 556–566.

Nüst, D., & Pebesma, E. (2021). Practical reproducibility in geography and geosciences. *Annals of the American Association of Geographers*, 111(5), 1300–1310.

Okabe, A., & Sugihara, K. (2012). *Spatial Analysis Along Networks: Statistical and Computational Methods*. Wiley.

Openshaw, S. (1984). *The Modifiable Areal Unit Problem*. CATMOG 38. Geo Books.

Openshaw, S., & Taylor, P. J. (1979). A million or so correlation coefficients: Three experiments on the modifiable areal unit problem. In N. Wrigley (Ed.), *Statistical Applications in the Spatial Sciences* (pp. 127–144). Pion.

Ord, J. K., & Getis, A. (1995). Local spatial autocorrelation statistics: Distributional issues and an application. *Geographical Analysis*, 27(4), 286–306.

Page, M. J., McKenzie, J. E., Bossuyt, P. M., Boutron, I., Hoffmann, T. C., Mulrow, C. D., … Moher, D. (2021). The PRISMA 2020 statement: An updated guideline for reporting systematic reviews. *BMJ*, 372, n71.

Pebesma, E. (2018). Simple features for R: Standardized support for spatial vector data. *The R Journal*, 10(1), 439–446.

Phillips, S. J., Anderson, R. P., & Schapire, R. E. (2006). Maximum entropy modeling of species geographic distributions. *Ecological Modelling*, 190(3–4), 231–259.

Reichstein, M., Camps-Valls, G., Stevens, B., Jung, M., Denzler, J., Carvalhais, N., & Prabhat. (2019). Deep learning and process understanding for data-driven Earth system science. *Nature*, 566, 195–204.

Rey, S. J. (2009). Show me the code: Spatial analysis and open source. *Journal of Geographical Systems*, 11(2), 191–207.

Ribeiro, M. T., Singh, S., & Guestrin, C. (2016). "Why should I trust you?": Explaining the predictions of any classifier. In *Proceedings of KDD '16* (pp. 1135–1144).

Ripley, B. D. (1976). The second-order analysis of stationary point processes. *Journal of Applied Probability*, 13(2), 255–266.

Ripley, B. D. (1977). Modelling spatial patterns. *Journal of the Royal Statistical Society: Series B*, 39(2), 172–212.

Roberts, D. R., Bahn, V., Ciuti, S., Boyce, M. S., Elith, J., Guillera-Arroita, G., … Dormann, C. F. (2017). Cross-validation strategies for data with temporal, spatial, hierarchical, or phylogenetic structure. *Ecography*, 40(8), 913–929.

Rue, H., Martino, S., & Chopin, N. (2009). Approximate Bayesian inference for latent Gaussian models by using integrated nested Laplace approximations. *Journal of the Royal Statistical Society: Series B*, 71(2), 319–392.

Rushton, G. (2003). Public health, GIS, and spatial analytic tools. *Annual Review of Public Health*, 24, 43–56.

Singleton, A., & Arribas-Bel, D. (2021). Geographic data science. *Geographical Analysis*, 53(1), 61–75.

Snow, J. (1855). *On the Mode of Communication of Cholera* (2nd ed.). John Churchill.

Sui, D., & Goodchild, M. (2011). The convergence of GIS and social media: Challenges for GIScience. *International Journal of Geographical Information Science*, 25(11), 1737–1748.

Thatcher, J., O'Sullivan, D., & Mahmoudi, D. (2016). Data colonialism through accumulation by dispossession. *Environment and Planning D: Society and Space*, 34(6), 990–1006.

Tobler, W. R. (1970). A computer movie simulating urban growth in the Detroit region. *Economic Geography*, 46(sup1), 234–240.

Velázquez, E., Martínez, I., Getzin, S., Moloney, K. A., & Wiegand, T. (2016). An evaluation of the state of spatial point pattern analysis in ecology. *Ecography*, 39(11), 1042–1055.

Waller, L. A., & Gotway, C. A. (2004). *Applied Spatial Statistics for Public Health Data*. Wiley.

Wiegand, T., & Moloney, K. A. (2004). Rings, circles, and null-models for point pattern analysis in ecology. *Oikos*, 104(2), 209–229.

Wilkinson, M. D., Dumontier, M., Aalbersberg, I. J., Appleton, G., Axton, M., Baak, A., … Mons, B. (2016). The FAIR Guiding Principles for scientific data management and stewardship. *Scientific Data*, 3, 160018.

Zandbergen, P. A. (2009). Geocoding quality and implications for spatial analysis. *Geography Compass*, 3(2), 647–680.

Zook, M., Barocas, S., boyd, d., Crawford, K., Keller, E., Gangadharan, S. P., … Pasquale, F. (2017). Ten simple rules for responsible big data research. *PLOS Computational Biology*, 13(3), e1005399.

---

## Figures

| # | Title | File |
|---|---|---|
| 1 | PRISMA flow of study identification, screening and inclusion | `figures/F01_prisma_flow.png` |
| 2 | Growth of the point-based spatial-analysis literature, 2000–2026 | `figures/F02_publication_growth.png` |
| 3 | The methodological composition shifts, but classical statistics do not disappear | `figures/F03_method_class_evolution.png` |
| 4 | Where point-based spatial analysis is produced: country of author affiliation | `figures/F04_map_affiliation_countries.png` |
| 5 | The geography of spatial problems is not the geography of spatial knowledge | `figures/F05_map_case_study_and_asymmetry.png` |
| 6 | The data substrate inverts between 2000 and 2027 | `figures/F06_data_substrate_transition.png` |
| 7 | From data substrate to method to application: the flow structure of the field | `figures/F07_sankey_data_method_domain.png` |
| 8 | Thematic evolution: the title vocabulary that distinguishes each period | `figures/F08_thematic_evolution.png` |
| 9 | Topic–method matrix | `figures/F09_domain_method_heatmap.png` |
| 10 | International co-authorship structure at country level | `figures/F10_collaboration_network.png` |
| 11 | Analytical sophistication grows faster than methodological rigour | `figures/F11_rigour_decoupling.png` |
| 12 | The PB-SAM maturity profile is unbalanced and largely static | `figures/F12_pbsam_maturity.png` |
| 13 | Point Intelligence Drift: the conceptual model | `figures/F13_pid_conceptual_model.png` |
| 14 | Three instruments proposed by this review | `figures/F14_taxonomy_periodisation_maturity.png` |
| 15 | National methodological profiles: the twelve most productive countries | `figures/F15_country_method_profiles.png` |
| 16 | Method co-occurrence: where methodological convergence actually happens | `figures/F16_method_co_occurrence_network.png` |

Every figure carries, in-figure, its data source, method note and analytical interpretation.

## Supplementary tables

All tables are provided as CSV in `tables/`, each with an embedded source-and-method note.

| # | File | Content |
|---|---|---|
| S1 | `T01_publication_growth.csv` | Included studies per year, cumulative, period |
| S2 | `T02_methods_by_period.csv` | Method prevalence by period |
| S3 | `T03_method_classes_by_period.csv` | Method classes by period |
| S4 | `T04_domains_by_period.csv` | Application domains by period |
| S5 | `T05_data_sources_by_period.csv` | Data sources by period |
| S6 | `T06_software_by_period.csv` | Software environments by period |
| S7 | `T07_spatial_scale_by_period.csv` | Spatial scale by period |
| S8 | `T08_temporal_scale_by_period.csv` | Temporal scale by period |
| S9 | `T09_rigour_constructs_by_period.csv` | Uncertainty, validation, reproducibility, ethics |
| S10 | `T10_pbsam_maturity_by_period.csv` | PB-SAM scores and maturity levels |
| S11 | `T11_affiliation_countries.csv` | Country of author affiliation |
| S12 | `T12_case_study_countries.csv` | Country of empirical case study |
| S13 | `T13_production_problem_asymmetry.csv` | Production-to-problem ratios |
| S14 | `T14_international_collaboration.csv` | Collaboration rates by period |
| S15 | `T15_country_collaboration_edges.csv` | Country co-authorship edge list |
| S16 | `T16_publishers.csv` | Publishers (DOI-registrant derived) |
| S17 | `T17_institutions.csv` | Institution strings (lower bounds) |
| S18 | `T18_domain_by_method_class.csv` | Domain x method-class matrix |
| S19 | `T19_thematic_evolution_terms.csv` | Period-distinctive title terms (log-odds) |
| S20 | `T20_method_co_occurrence.csv` | Method pairs with lift |
| S21 | `T21_country_method_domain_profile.csv` | National methodological profiles |
| S22 | `T22_domain_method_gap_matrix.csv` | Research-gap matrix (empty/thin cells) |
| S23 | `T23_included_studies_register.csv` | Register of all 913 included studies |
| S24 | `T24_regional_representation.csv` | Continental representation, both geographies |
