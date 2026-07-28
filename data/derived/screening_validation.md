# Screening-instrument validation record

**Review:** *Trajectories of Point-Based Spatial Analysis, 2000–2027*
**Instrument:** `analysis/lexicons.py` + `analysis/pipeline.py` (locked version)
**Adjudicator:** single reviewer (the review author). No second independent
screener was available; this is recorded as a limitation in the manuscript
(Section 8.1) and inter-rater reliability could therefore **not** be computed.

## Procedure

The rule-based screener was developed iteratively in three audit-and-revision
rounds. In each round a stratified random sample was drawn from the screened
corpus (included / excluded strata), the reviewer read the title and abstract
of every sampled record, and assigned an independent eligibility verdict
against the definition in Section 2 of the manuscript. Disagreements between
the reviewer verdict and the algorithmic decision were traced to the
responsible rule, and the rule was revised only where the disagreement
reflected a *systematic* construct-validity failure (not a one-off).

## Round 1 (initial instrument, 660 included)

Sample: 40 included + 34 excluded.
Systematic failures identified:

| # | Failure mode | Direction | Correction applied |
|---|---|---|---|
| 1 | Point-cloud object extraction / segmentation coded as point-pattern analysis | false positive | added `point_cloud_engineering` boundary rule (S4b) with a rescue clause |
| 2 | Non-geographic point patterns (cell biology, materials science, astronomy) | false positive | added `non_geographic_micro` boundary rule (S4a) |
| 3 | Trajectory, AIS and survey-cluster point data not recognised as point-referenced | false negative | extended criterion A (`trajectory_track`, `survey_cluster`, `incident_records`, `detection_points`, `facility_sites`) |
| 4 | Definitional point-pattern methods not treated as sufficient evidence of point data | false negative | added the criterion-A sufficiency rule (S5b) |

## Round 2 (733 included)

Sample: 60 included + 60 excluded.
Reviewer verdicts: 58/60 sampled included records judged eligible
(2 unambiguous false positives: a biomedical-imaging point pattern and a
LiDAR roof-contour extraction study). 5/60 sampled excluded records judged
eligible (false-omission rate 8.3%), attributable to:

| # | Failure mode | Direction | Correction applied |
|---|---|---|---|
| 5 | Methodological point-process papers excluded because they *illustrate* on a non-geographic example | false negative | S4a exception for papers applying a definitional point-pattern method |
| 6 | Point-referenced studies characterising spatial variation without naming an estimator | false negative | added `spatial_pattern_analysis` to criterion B |
| 7 | Borehole / permanent-plot / measurement-point vocabulary missing | false negative | extended `sample_points` |
| 8 | Raster landscape-pattern-index studies admitted | false positive | added `landscape_pattern_indices` boundary rule |

## Round 3 (final instrument, 916 included) — reported in the manuscript

Sample: 60 included + 40 excluded (stratified random, seeds recorded in
`analysis/pipeline.py` and in the commands used to draw the batches).

**Precision (positive predictive value) of the included stratum**

| Verdict | n | Share |
|---|---|---|
| Eligible (unambiguous) | 45 | 0.750 |
| Eligible (borderline, retained on balance) | 9 | 0.150 |
| **Not eligible (unambiguous false positive)** | **6** | **0.100** |

- Precision counting only unambiguous misclassifications: **0.900**
  (Wilson 95% CI 0.798–0.954, n = 60).
- Precision under a strict reading that also rejects all borderline
  records: **0.750** (Wilson 95% CI 0.627–0.842).

Residual false positives cluster at one boundary: **geophysical and
sensor-signal processing** that operates on located measurements
(LiDAR road-crack detection, microseismic source location, plant
phenotyping from point clouds). This is a genuine grey zone of the
construct, not a coding slip, and is discussed in Section 8.1.

**False-omission rate of the excluded stratum**

| Verdict | n | Share |
|---|---|---|
| Correctly excluded | 34 | 0.850 |
| **Eligible but excluded (false negative)** | 2 unambiguous + 4 probable | 0.050–0.150 |

Unambiguous false negatives were a multi-Gaussian-kriging uncertainty study
and a spatio-temporal point-pattern clustering study; both were traced to
criterion-A vocabulary gaps. The `spatio-temporal point pattern` gap was
corrected; the kriging gap was **deliberately not** corrected, because
admitting kriging as sufficient evidence of point-referenced data raised the
included corpus from 916 to 1,247 records and visibly degraded precision by
importing raster-field interpolation studies. The boundary was therefore held
at the more conservative position, at a known cost in sensitivity.

## Net effect on the reported corpus

Applying the estimated precision to the analytic corpus implies roughly
824 (0.900 × 916) unambiguously eligible studies; applying the estimated
false-omission rate to the 4,796 excluded records implies on the order of
240–720 eligible studies not recovered. **The corpus should therefore be read
as a large, construct-valid *sample* of the point-based spatial-analysis
literature indexed in this export, not as an exhaustive census.** All
prevalence estimates in the manuscript are conditioned on this sampling frame.
