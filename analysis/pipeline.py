"""
pipeline.py
===========
Stage 1-2 of the review: PRISMA identification/screening/eligibility, and
multi-dimensional coding of the included corpus.

Inputs   : data/raw/scopus_export_2026-07-28.csv
Outputs  : data/derived/records_all.csv      (every identified record + decision)
           data/derived/records_included.csv (analytic corpus, fully coded)
           data/derived/prisma_counts.json   (PRISMA flow numbers)
           data/derived/screening_audit.csv  (stratified sample for adjudication)

Run:  python3 analysis/pipeline.py
"""

import csv
import json
import os
import re
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import lexicons as LX
import geo as GEO

csv.field_size_limit(sys.maxsize)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw", "scopus_export_2026-07-28.csv")
DERIVED = os.path.join(ROOT, "data", "derived")
os.makedirs(DERIVED, exist_ok=True)

NO_ABSTRACT = re.compile(r"\[no abstract available\]", re.I)

# ---------------------------------------------------------------------------
# Abstract cleaning
# ---------------------------------------------------------------------------
# 96.8% of Scopus abstracts in this export carry a publisher copyright or
# licence statement appended to the abstract text. Those statements name
# corporate domiciles ("Licensee MDPI, Basel, Switzerland";
# "Springer-Verlag Berlin Heidelberg"; "Informa UK Limited") which, if left in
# place, are detected by the case-study gazetteer and produce large spurious
# counts for Switzerland, Germany and the United Kingdom. All boilerplate is
# therefore removed before any coding or text analysis.
_COPYRIGHT = re.compile(
    r"(?:©|\(c\)\s|Copyright\s*(?:©|\(c\))).*$", re.I | re.S)
_LICENCE_TAIL = re.compile(
    r"(?:This (?:article|work) is (?:an )?open[- ]access.*$"
    r"|Licensee MDPI.*$"
    r"|All rights reserved\.?\s*$"
    r"|Published by Elsevier.*$"
    r"|This is an open access article.*$)", re.I | re.S)


def clean_abstract(a):
    """Strip publisher copyright/licence boilerplate from an abstract."""
    if not a:
        return ""
    a = _COPYRIGHT.sub("", a)
    a = _LICENCE_TAIL.sub("", a)
    return a.strip()


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def norm_title(t):
    return re.sub(r"[^a-z0-9]+", " ", (t or "").lower()).strip()


def match_family(family, text):
    """Return the list of labels in a compiled family that match `text`."""
    return [lab for lab, (_cls, pat) in LX.COMPILED[family].items()
            if pat.search(text)]


def count_family(family, text):
    """Return {label: n_matches}."""
    return {lab: len(pat.findall(text))
            for lab, (_cls, pat) in LX.COMPILED[family].items()
            if pat.search(text)}


# ---------------------------------------------------------------------------
# 1. IDENTIFICATION
# ---------------------------------------------------------------------------
def load_records():
    with open(RAW, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    for i, r in enumerate(rows):
        r["rec_id"] = f"R{i + 1:05d}"
        r["Year"] = int(r["Year"]) if str(r["Year"]).strip().isdigit() else None
    return rows


# ---------------------------------------------------------------------------
# 2. SCREENING + ELIGIBILITY
# ---------------------------------------------------------------------------
def screen(rec):
    """Return (decision, reason, evidence dict).

    decision in {"include", "exclude"}.
    Screening is sequential; the FIRST failing rule is recorded as the reason,
    so exclusion reasons partition the excluded set exactly once.
    """
    title = (rec.get("Title") or "").strip()
    abstract = clean_abstract(rec.get("Abstract"))
    text = f"{title}. {abstract}"
    low = text.lower()

    ev = {}

    # S1 - year in scope
    if rec["Year"] is None or not (2000 <= rec["Year"] <= 2027):
        return "exclude", "S1_out_of_period", ev

    # S2 - abstract available (required for coding)
    if not abstract or NO_ABSTRACT.search(abstract) or len(abstract) < 120:
        return "exclude", "S2_no_usable_abstract", ev

    # S3 - non-research document type (detected from title stem)
    for lab, (_c, pat) in LX.COMPILED["oos"].items():
        if lab == "non_research_item" and pat.search(title.lower()):
            return "exclude", "S3_non_research_item", ev

    # S4 - out-of-scope research tradition (boundary conditions, Section 2.2)
    oos_hits = [lab for lab, (_c, pat) in LX.COMPILED["oos"].items()
                if lab != "non_research_item" and pat.search(text)]
    ev["oos"] = oos_hits

    b_pre = match_family("critB", text)
    a_pre = match_family("critA", text)

    # (a) Non-geographic point patterns and molecular-scale work fall outside
    #     the review's definitional boundary. Exception: methodological papers
    #     that develop point-process machinery and merely *illustrate* it on a
    #     non-geographic example are retained, because the methodological
    #     contribution belongs to the field (audit correction, Section 3.3).
    if {"non_geographic_micro", "molecular_scale"} & set(oos_hits):
        method_paper = bool(set(b_pre) & LX.POINT_DEFINITIVE_METHODS)
        if not method_paper:
            return "exclude", "S4a_outside_geographic_boundary", ev

    # (b) Sensor-processing traditions (SLAM, point-cloud segmentation,
    #     computer vision) are excluded UNLESS the record also applies a
    #     definitional point-pattern method or analyses located events -
    #     this rescue clause retains, e.g., forest studies that derive stem
    #     locations from LiDAR and then analyse their spatial arrangement.
    if {"slam_odometry", "pure_cv_graphics", "point_cloud_engineering",
            "landscape_pattern_indices"} & set(oos_hits):
        rescue_methods = set(b_pre) & LX.POINT_DEFINITIVE_METHODS
        rescue_units = set(a_pre) & {"case_locations", "incident_records",
                                     "occurrence_records", "tree_stem_plot",
                                     "epicentre", "poi", "event_locations"}
        if not (rescue_methods or rescue_units):
            return "exclude", "S4b_sensor_processing_tradition", ev

    # S5 - criterion A: point-referenced units of observation
    a_hits = match_family("critA", text)
    ev["critA"] = a_hits
    traps = match_family("traps", text)
    ev["traps"] = traps
    strong_a = [h for h in a_hits if h != "point_cloud"]

    # criterion B is evaluated up-front so that both criteria are auditable
    # for every screened record, including those excluded at S5.
    b_hits = match_family("critB", text)
    ev["critB"] = b_hits

    # S5b - sufficiency rule: methods that are definitionally defined on point
    # patterns establish criterion A on their own, unless an explicit raster or
    # areal-unit context blocks the inference.
    definitive = set(b_hits) & LX.POINT_DEFINITIVE_METHODS
    blocked = bool(re.search(LX.DEFINITIVE_BLOCKERS, low))
    a_satisfied = bool(a_hits) or (bool(definitive) and not blocked)
    ev["definitive"] = sorted(definitive) if (definitive and not blocked) else []
    if not a_satisfied:
        return "exclude", "S5_no_point_referenced_units", ev

    # S6 - criterion B: an explicit spatial-analytical operation
    if not b_hits:
        return "exclude", "S6_no_spatial_analytical_operation", ev

    # S7 - out-of-scope traditions dominate and no core spatial-statistical
    #      operation is present
    core_b = {"kde", "ppa", "point_process_model", "nna", "autocorrelation",
              "hotspot", "scan_statistic", "geostatistics", "spatial_regression",
              "network_constrained", "spatial_clustering"}
    if oos_hits and not (set(b_hits) & core_b):
        return "exclude", "S7_out_of_scope_tradition", ev

    # S8 - polysemy-only inclusion guard
    if strong_a == [] and "point_cloud" in a_hits and not (set(b_hits) & core_b):
        return "exclude", "S8_polysemous_point_only", ev

    return "include", "included", ev


# ---------------------------------------------------------------------------
# 3. CODING (included records only)
# ---------------------------------------------------------------------------
def code_record(rec):
    title = (rec.get("Title") or "").strip()
    abstract = clean_abstract(rec.get("Abstract"))
    text = f"{title}. {abstract}"
    out = {}

    # --- period ---
    pc, pl = LX.period_of(rec["Year"])
    out["period_code"], out["period_label"] = pc, pl

    # --- methods ---
    methods = match_family("methods", text)
    out["methods"] = methods
    classes = sorted({LX.COMPILED["methods"][m][0] for m in methods})
    out["method_classes"] = classes
    out["n_methods"] = len(methods)

    # --- domains / data / software / scales ---
    out["domains"] = match_family("domains", text)
    out["data_sources"] = match_family("data_sources", text)
    out["software"] = match_family("software", text)
    out["spatial_scale"] = match_family("spatial_scale", text)
    out["temporal_scale"] = match_family("temporal_scale", text)

    # --- rigour constructs ---
    out["uncertainty"] = match_family("uncertainty", text)
    out["validation"] = match_family("validation", text)
    out["reproducibility"] = match_family("reproducibility", text)
    out["ethics"] = match_family("ethics", text)

    # --- PB-SAM maturity score (abstract-level proxy, 0-10) ---
    d1 = 2 if len(methods) >= 2 else (1 if methods else 0)
    d2 = 2 if len(out["uncertainty"]) >= 2 else (1 if out["uncertainty"] else 0)
    d3 = 2 if len(out["validation"]) >= 2 else (1 if out["validation"] else 0)
    d4 = 2 if len(out["data_sources"]) >= 2 else (1 if out["data_sources"] else 0)
    d5 = 2 if len(out["reproducibility"]) >= 2 else (1 if out["reproducibility"] else 0)
    out.update(D1_method_specification=d1, D2_uncertainty=d2,
               D3_validation=d3, D4_data_transparency=d4,
               D5_reproducibility=d5)
    out["pbsam_score"] = d1 + d2 + d3 + d4 + d5

    # --- geography of production ---
    aff_iso, n_aff = GEO.parse_affiliation_countries(rec.get("Affiliations"))
    out["affil_iso3"] = aff_iso
    out["n_affiliation_strings"] = n_aff
    out["n_affil_countries"] = len(aff_iso)
    out["international_collab"] = int(len(aff_iso) > 1)
    out["affil_hemisphere"] = sorted({GEO.hemisphere(i) for i in aff_iso})
    out["institutions"] = GEO.parse_affiliation_institutions(rec.get("Affiliations"))

    # --- geography of the empirical problem ---
    case_iso, supra, ev_kinds = GEO.detect_case_study_countries(text)
    out["case_iso3"] = case_iso
    out["case_supranational"] = supra
    out["case_evidence"] = ev_kinds
    out["has_case_geography"] = int(bool(case_iso or supra))

    # --- production/problem alignment ---
    if case_iso and aff_iso:
        primary_case = case_iso[0]
        out["case_primary"] = primary_case
        out["domestic_research"] = int(primary_case in aff_iso)
        out["case_hemisphere"] = GEO.hemisphere(primary_case)
        out["extractive_pattern"] = int(
            GEO.hemisphere(primary_case) == "Global South"
            and all(GEO.hemisphere(a) == "Global North" for a in aff_iso))
    else:
        out["case_primary"] = ""
        out["domestic_research"] = ""
        out["case_hemisphere"] = ""
        out["extractive_pattern"] = ""

    # --- publisher (deterministic DOI-registrant mapping) ---
    doi = (rec.get("DOI") or "").strip()
    prefix = doi.split("/")[0] if "/" in doi else ""
    out["doi_prefix"] = prefix
    out["publisher"] = LX.DOI_PREFIX_PUBLISHER.get(prefix, "Other / unmapped registrant")

    out["abstract_len"] = len(abstract)
    return out


# ---------------------------------------------------------------------------
# 4. MAIN
# ---------------------------------------------------------------------------
LIST_FIELDS = ["methods", "method_classes", "domains", "data_sources",
               "software", "spatial_scale", "temporal_scale", "uncertainty",
               "validation", "reproducibility", "ethics", "affil_iso3",
               "affil_hemisphere", "case_iso3", "case_supranational",
               "case_evidence", "institutions"]


def main():
    records = load_records()
    n_identified = len(records)

    # --- de-duplication -----------------------------------------------------
    seen_doi, seen_title = {}, {}
    dup_doi = dup_title = 0
    for r in records:
        doi = (r.get("DOI") or "").strip().lower()
        nt = norm_title(r.get("Title"))
        if doi and doi in seen_doi:
            r["_dup"] = "duplicate_doi"
            dup_doi += 1
        elif nt and nt in seen_title:
            r["_dup"] = "duplicate_title"
            dup_title += 1
        else:
            r["_dup"] = ""
            if doi:
                seen_doi[doi] = r["rec_id"]
            if nt:
                seen_title[nt] = r["rec_id"]

    unique = [r for r in records if not r["_dup"]]

    # --- screening ----------------------------------------------------------
    reasons = Counter()
    included = []
    for r in unique:
        dec, reason, ev = screen(r)
        r["_decision"] = dec
        r["_reason"] = reason
        r["_critA"] = "|".join(ev.get("critA", []))
        r["_critB"] = "|".join(ev.get("critB", []))
        r["_traps"] = "|".join(ev.get("traps", []))
        r["_oos"] = "|".join(ev.get("oos", []))
        r["_definitive"] = "|".join(ev.get("definitive", []))
        reasons[reason] += 1
        if dec == "include":
            included.append(r)

    # --- coding -------------------------------------------------------------
    for r in included:
        r.update(code_record(r))

    # --- write all-records ledger ------------------------------------------
    with open(os.path.join(DERIVED, "records_all.csv"), "w", newline="",
              encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["rec_id", "year", "title", "doi", "duplicate_flag",
                    "decision", "exclusion_reason", "criterionA_evidence",
                    "criterionB_evidence", "polysemy_traps", "out_of_scope",
                    "definitive_method_route"])
        for r in records:
            w.writerow([r["rec_id"], r["Year"], r["Title"], r["DOI"],
                        r["_dup"], r.get("_decision", "not_screened"),
                        r.get("_reason", "removed_before_screening"),
                        r.get("_critA", ""), r.get("_critB", ""),
                        r.get("_traps", ""), r.get("_oos", ""),
                        r.get("_definitive", "")])

    # --- write included corpus ---------------------------------------------
    base_cols = ["rec_id", "Year", "period_code", "period_label", "Title",
                 "DOI", "Link", "publisher", "doi_prefix",
                 "n_affiliation_strings", "n_affil_countries",
                 "international_collab", "case_primary", "case_hemisphere",
                 "domestic_research", "extractive_pattern", "n_methods",
                 "pbsam_score", "D1_method_specification", "D2_uncertainty",
                 "D3_validation", "D4_data_transparency", "D5_reproducibility",
                 "has_case_geography", "abstract_len"]
    cols = base_cols + LIST_FIELDS
    with open(os.path.join(DERIVED, "records_included.csv"), "w", newline="",
              encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for r in included:
            row = []
            for c in cols:
                v = r.get(c, "")
                row.append("|".join(v) if isinstance(v, list) else v)
            w.writerow(row)

    # --- PRISMA counts ------------------------------------------------------
    prisma = {
        "identification": {
            "records_identified_scopus": n_identified,
            "export_date": "2026-07-28",
            "duplicates_removed_doi": dup_doi,
            "duplicates_removed_title": dup_title,
            "records_after_deduplication": len(unique),
        },
        "screening": {
            "records_screened": len(unique),
            "excluded_total": len(unique) - len(included),
            "exclusion_reasons": dict(reasons),
        },
        "included": {
            "studies_included": len(included),
            "inclusion_rate": round(len(included) / len(unique), 4),
        },
        "year_range_included": [min(r["Year"] for r in included),
                                max(r["Year"] for r in included)],
    }
    with open(os.path.join(DERIVED, "prisma_counts.json"), "w") as f:
        json.dump(prisma, f, indent=2)

    # --- stratified audit sample for manual adjudication -------------------
    import random
    random.seed(20260728)
    inc_sample = random.sample(included, min(60, len(included)))
    exc = [r for r in unique if r["_decision"] == "exclude"]
    exc_sample = random.sample(exc, min(60, len(exc)))
    with open(os.path.join(DERIVED, "screening_audit.csv"), "w", newline="",
              encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["stratum", "rec_id", "year", "decision", "reason",
                    "title", "critA", "critB", "abstract_head"])
        for strat, sample in (("included", inc_sample), ("excluded", exc_sample)):
            for r in sample:
                w.writerow([strat, r["rec_id"], r["Year"], r["_decision"],
                            r["_reason"], r["Title"], r.get("_critA", ""),
                            r.get("_critB", ""),
                            clean_abstract(r.get("Abstract"))[:420]])

    print(json.dumps(prisma, indent=2))
    print("\nIncluded per period:",
          dict(Counter(r["period_label"] for r in included)))
    print("Included per year:",
          dict(sorted(Counter(r["Year"] for r in included).items())))
    return prisma


if __name__ == "__main__":
    main()
