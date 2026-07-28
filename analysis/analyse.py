"""
analyse.py
==========
Stage 3 of the review: descriptive, bibliometric, thematic and structural
analysis of the included corpus, plus the derived indices that the manuscript's
theoretical argument rests on.

Outputs every table in `tables/` as CSV and a machine-readable digest of all
numbers quoted in the manuscript (`data/derived/results.json`).

Run:  python3 analysis/analyse.py
"""

import csv
import json
import math
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lexicons as LX
import geo as GEO

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DER = os.path.join(ROOT, "data", "derived")
TAB = os.path.join(ROOT, "tables")
os.makedirs(TAB, exist_ok=True)

csv.field_size_limit(sys.maxsize)
LIST_COLS = {"methods", "method_classes", "domains", "data_sources", "software",
             "spatial_scale", "temporal_scale", "uncertainty", "validation",
             "reproducibility", "ethics", "affil_iso3", "affil_hemisphere",
             "case_iso3", "case_supranational", "case_evidence", "institutions"}
PERIOD_ORDER = ["2000-2010", "2011-2020", "2021-2027"]


def load():
    rows = []
    with open(os.path.join(DER, "records_included.csv"), encoding="utf-8") as f:
        for r in csv.DictReader(f):
            for c in LIST_COLS:
                r[c] = [x for x in (r.get(c) or "").split("|") if x]
            r["Year"] = int(r["Year"])
            for c in ("pbsam_score", "n_methods", "international_collab",
                      "has_case_geography", "n_affil_countries",
                      "D1_method_specification", "D2_uncertainty",
                      "D3_validation", "D4_data_transparency",
                      "D5_reproducibility"):
                r[c] = int(r[c]) if str(r[c]).strip() != "" else 0
            rows.append(r)
    return rows


def write_table(name, header, rows, note=""):
    path = os.path.join(TAB, name)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if note:
            w.writerow([f"# {note}"])
        w.writerow(header)
        w.writerows(rows)
    return path


def pct(n, d):
    return round(100.0 * n / d, 1) if d else 0.0


def by_period(rows, key_fn):
    """{period: Counter} for a list-valued or scalar key function."""
    out = {p: Counter() for p in PERIOD_ORDER}
    for r in rows:
        v = key_fn(r)
        if v is None:
            continue
        if isinstance(v, list):
            out[r["period_label"]].update(v)
        else:
            out[r["period_label"]][v] += 1
    return out


def cagr(v0, v1, years):
    if v0 <= 0 or years <= 0:
        return None
    return round(((v1 / v0) ** (1.0 / years) - 1) * 100, 2)


def shannon(counter):
    tot = sum(counter.values())
    if tot == 0:
        return 0.0
    return round(-sum((c / tot) * math.log(c / tot) for c in counter.values() if c), 3)


def gini(values):
    v = sorted(values)
    n = len(v)
    if n == 0 or sum(v) == 0:
        return 0.0
    cum = sum((2 * (i + 1) - n - 1) * x for i, x in enumerate(v))
    return round(cum / (n * sum(v)), 3)


def main():
    rows = load()
    N = len(rows)
    R = {"corpus_size": N}
    period_n = Counter(r["period_label"] for r in rows)
    R["period_n"] = {p: period_n[p] for p in PERIOD_ORDER}

    # =====================================================================
    # T1  Publication growth
    # =====================================================================
    yr = Counter(r["Year"] for r in rows)
    years = sorted(yr)
    cum = 0
    t1 = []
    for y in years:
        cum += yr[y]
        t1.append([y, yr[y], cum, LX.period_of(y)[1]])
    write_table("T01_publication_growth.csv",
                ["year", "n_studies", "cumulative", "period"], t1,
                "Included studies per publication year. 2026 is a partial "
                "year (export date 2026-07-28); 2027 has no indexed records.")
    R["growth"] = {"per_year": {str(y): yr[y] for y in years},
                   "cagr_2000_2025": cagr(yr[2000], yr[2025], 25),
                   "mean_annual_P1": round(sum(yr[y] for y in range(2000, 2011)) / 11, 1),
                   "mean_annual_P2": round(sum(yr[y] for y in range(2011, 2021)) / 10, 1),
                   "mean_annual_P3_to2025": round(sum(yr[y] for y in range(2021, 2026)) / 5, 1)}

    # =====================================================================
    # T2  Method families by period
    # =====================================================================
    mp = by_period(rows, lambda r: r["methods"])
    t2 = []
    for m, (cls, _pat) in LX.COMPILED["methods"].items():
        tot = sum(mp[p][m] for p in PERIOD_ORDER)
        if tot == 0:
            continue
        row = [m, LX.METHOD_CLASS_LABELS[cls]]
        for p in PERIOD_ORDER:
            row += [mp[p][m], pct(mp[p][m], period_n[p])]
        row += [tot, pct(tot, N)]
        t2.append(row)
    t2.sort(key=lambda x: -x[-2])
    write_table("T02_methods_by_period.csv",
                ["method", "method_class"] +
                [f"{p}_{s}" for p in PERIOD_ORDER for s in ("n", "pct_of_period")] +
                ["total_n", "pct_of_corpus"], t2,
                "Method prevalence. Categories are non-exclusive; percentages "
                "are shares of studies in the period, not of method mentions.")
    R["methods_total"] = {r[0]: r[-2] for r in t2}
    R["methods_by_period_pct"] = {r[0]: {PERIOD_ORDER[i]: r[3 + 2 * i] for i in range(3)}
                                  for r in t2}

    # method classes
    mcp = by_period(rows, lambda r: r["method_classes"])
    t2b = []
    for cls, lab in LX.METHOD_CLASS_LABELS.items():
        row = [cls, lab]
        for p in PERIOD_ORDER:
            row += [mcp[p][cls], pct(mcp[p][cls], period_n[p])]
        t2b.append(row)
    write_table("T03_method_classes_by_period.csv",
                ["class_code", "class_label"] +
                [f"{p}_{s}" for p in PERIOD_ORDER for s in ("n", "pct_of_period")],
                t2b, "Level-1 classes of the PBSA method taxonomy.")
    R["method_classes_pct"] = {cls: {p: pct(mcp[p][cls], period_n[p])
                                     for p in PERIOD_ORDER}
                               for cls in LX.METHOD_CLASS_LABELS}

    # =====================================================================
    # T4  Application domains by period
    # =====================================================================
    dp = by_period(rows, lambda r: r["domains"])
    t4 = []
    for d in LX.DOMAINS:
        tot = sum(dp[p][d] for p in PERIOD_ORDER)
        row = [d]
        for p in PERIOD_ORDER:
            row += [dp[p][d], pct(dp[p][d], period_n[p])]
        row += [tot, pct(tot, N)]
        t4.append(row)
    t4.sort(key=lambda x: -x[-2])
    write_table("T04_domains_by_period.csv",
                ["application_domain"] +
                [f"{p}_{s}" for p in PERIOD_ORDER for s in ("n", "pct_of_period")] +
                ["total_n", "pct_of_corpus"], t4, "Application-domain prevalence.")
    R["domains_total"] = {r[0]: r[-2] for r in t4}
    R["domains_by_period_pct"] = {r[0]: {PERIOD_ORDER[i]: r[2 + 2 * i] for i in range(3)}
                                  for r in t4}

    # =====================================================================
    # T5  Data sources / T6 software / T7 scales
    # =====================================================================
    for fam, fname, label in (("data_sources", "T05_data_sources_by_period.csv", "data_source"),
                              ("software", "T06_software_by_period.csv", "software_environment"),
                              ("spatial_scale", "T07_spatial_scale_by_period.csv", "spatial_scale"),
                              ("temporal_scale", "T08_temporal_scale_by_period.csv", "temporal_scale")):
        bp = by_period(rows, lambda r, f=fam: r[f])
        keys = set()
        for p in PERIOD_ORDER:
            keys |= set(bp[p])
        tt = []
        for k in sorted(keys):
            tot = sum(bp[p][k] for p in PERIOD_ORDER)
            row = [k]
            for p in PERIOD_ORDER:
                row += [bp[p][k], pct(bp[p][k], period_n[p])]
            row += [tot, pct(tot, N)]
            tt.append(row)
        tt.sort(key=lambda x: -x[-2])
        write_table(fname, [label] +
                    [f"{p}_{s}" for p in PERIOD_ORDER for s in ("n", "pct_of_period")] +
                    ["total_n", "pct_of_corpus"], tt)
        R[fam] = {r[0]: {"total": r[-2], "pct": r[-1],
                         **{PERIOD_ORDER[i]: r[2 + 2 * i] for i in range(3)}} for r in tt}

    # silence / non-reporting
    R["non_reporting"] = {
        "no_software_named": pct(sum(1 for r in rows if not r["software"]), N),
        "no_data_source_named": pct(sum(1 for r in rows if not r["data_sources"]), N),
        "no_spatial_scale_named": pct(sum(1 for r in rows if not r["spatial_scale"]), N),
        "no_case_geography": pct(sum(1 for r in rows if not r["has_case_geography"]), N),
    }

    # =====================================================================
    # T9  Rigour: uncertainty, validation, reproducibility, ethics
    # =====================================================================
    t9 = []
    for fam in ("uncertainty", "validation", "reproducibility", "ethics"):
        bp = by_period(rows, lambda r, f=fam: r[f])
        keys = set()
        for p in PERIOD_ORDER:
            keys |= set(bp[p])
        for k in sorted(keys):
            row = [fam, k]
            for p in PERIOD_ORDER:
                row += [bp[p][k], pct(bp[p][k], period_n[p])]
            tot = sum(bp[p][k] for p in PERIOD_ORDER)
            row += [tot, pct(tot, N)]
            t9.append(row)
    write_table("T09_rigour_constructs_by_period.csv",
                ["construct_family", "construct"] +
                [f"{p}_{s}" for p in PERIOD_ORDER for s in ("n", "pct_of_period")] +
                ["total_n", "pct_of_corpus"], t9,
                "Abstract-level evidence of rigour practices. Absence of "
                "evidence in an abstract is not evidence of absence in the "
                "full text; see Section 8.1.")
    R["rigour"] = {f"{r[0]}::{r[1]}": {"pct_corpus": r[-1],
                                       **{PERIOD_ORDER[i]: r[3 + 2 * i] for i in range(3)}}
                   for r in t9}

    # any-of summaries
    for fam in ("uncertainty", "validation", "reproducibility", "ethics"):
        R[f"any_{fam}"] = {p: pct(sum(1 for r in rows
                                      if r["period_label"] == p and r[fam]),
                                  period_n[p]) for p in PERIOD_ORDER}
        R[f"any_{fam}"]["corpus"] = pct(sum(1 for r in rows if r[fam]), N)

    # =====================================================================
    # T10  PB-SAM maturity
    # =====================================================================
    t10 = []
    for p in PERIOD_ORDER:
        sub = [r for r in rows if r["period_label"] == p]
        row = [p, len(sub), round(sum(r["pbsam_score"] for r in sub) / len(sub), 2)]
        for d, _lab in LX.PBSAM_DIMENSIONS:
            row.append(round(sum(r[d] for r in sub) / len(sub), 2))
        dist = Counter(r["pbsam_score"] for r in sub)
        row += [pct(sum(v for k, v in dist.items() if k <= 3), len(sub)),
                pct(sum(v for k, v in dist.items() if 4 <= k <= 6), len(sub)),
                pct(sum(v for k, v in dist.items() if k >= 7), len(sub))]
        t10.append(row)
    write_table("T10_pbsam_maturity_by_period.csv",
                ["period", "n", "mean_PBSAM_0_10"] +
                [d for d, _ in LX.PBSAM_DIMENSIONS] +
                ["pct_level1_emergent_0_3", "pct_level2_consolidating_4_6",
                 "pct_level3_mature_7_10"], t10,
                "PB-SAM is an abstract-level proxy for methodological "
                "maturity, not a full-text quality appraisal.")
    R["pbsam"] = {r[0]: {"mean": r[2], "L1": r[-3], "L2": r[-2], "L3": r[-1],
                         **{LX.PBSAM_DIMENSIONS[i][0]: r[3 + i] for i in range(5)}}
                  for r in t10}
    R["pbsam"]["corpus_mean"] = round(sum(r["pbsam_score"] for r in rows) / N, 2)

    # =====================================================================
    # T11  Affiliation countries (knowledge production)
    # =====================================================================
    aff = Counter()
    aff_p = by_period(rows, lambda r: r["affil_iso3"])
    for r in rows:
        aff.update(r["affil_iso3"])
    t11 = []
    for iso, n in aff.most_common():
        t11.append([iso, GEO.ISO3_TO_NAME.get(iso, iso), GEO.hemisphere(iso), n,
                    pct(n, N), aff_p["2000-2010"][iso], aff_p["2011-2020"][iso],
                    aff_p["2021-2027"][iso]])
    write_table("T11_affiliation_countries.csv",
                ["iso3", "country", "hemisphere", "n_studies", "pct_of_corpus",
                 "n_2000_2010", "n_2011_2020", "n_2021_2027"], t11,
                "Country of author affiliation (knowledge production). A study "
                "with authors in k countries contributes to all k.")
    R["affiliation"] = {
        "n_countries": len(aff),
        "top15": [[GEO.ISO3_TO_NAME.get(i, i), n, pct(n, N)] for i, n in aff.most_common(15)],
        "gini": gini(list(aff.values())),
        "top5_share": pct(sum(n for _, n in aff.most_common(5)), sum(aff.values())),
        "top10_share": pct(sum(n for _, n in aff.most_common(10)), sum(aff.values())),
        "north_studies": sum(1 for r in rows if any(GEO.hemisphere(i) == "Global North" for i in r["affil_iso3"])),
        "south_studies": sum(1 for r in rows if any(GEO.hemisphere(i) == "Global South" for i in r["affil_iso3"])),
    }

    # =====================================================================
    # T12  Case-study countries (where the problem is)
    # =====================================================================
    case = Counter()
    case_p = by_period(rows, lambda r: r["case_iso3"])
    for r in rows:
        case.update(r["case_iso3"])
    t12 = []
    for iso, n in case.most_common():
        t12.append([iso, GEO.ISO3_TO_NAME.get(iso, iso), GEO.hemisphere(iso), n,
                    pct(n, N), case_p["2000-2010"][iso], case_p["2011-2020"][iso],
                    case_p["2021-2027"][iso]])
    write_table("T12_case_study_countries.csv",
                ["iso3", "country", "hemisphere", "n_studies", "pct_of_corpus",
                 "n_2000_2010", "n_2011_2020", "n_2021_2027"], t12,
                "Country of the empirical case study, detected from title and "
                "abstract. Studies without a detectable case geography "
                "(methodological or simulation papers) are excluded.")
    R["case_study"] = {
        "n_countries": len(case),
        "top15": [[GEO.ISO3_TO_NAME.get(i, i), n, pct(n, N)] for i, n in case.most_common(15)],
        "gini": gini(list(case.values())),
        "with_case_geography": sum(1 for r in rows if r["has_case_geography"]),
    }

    # =====================================================================
    # T13  Production/problem asymmetry
    # =====================================================================
    pairs = [r for r in rows if r["case_primary"] and r["affil_iso3"]]
    t13 = []
    allc = set(list(aff) + list(case))
    for iso in sorted(allc, key=lambda i: -(aff[i] + case[i])):
        a, c = aff[iso], case[iso]
        if a + c < 5:
            continue
        ratio = round(a / c, 2) if c else None
        dom = sum(1 for r in pairs if r["case_primary"] == iso and iso in r["affil_iso3"])
        ext = sum(1 for r in pairs if r["case_primary"] == iso and iso not in r["affil_iso3"])
        t13.append([iso, GEO.ISO3_TO_NAME.get(iso, iso), GEO.hemisphere(iso),
                    a, c, ratio, dom, ext,
                    pct(dom, dom + ext) if (dom + ext) else ""])
    write_table("T13_production_problem_asymmetry.csv",
                ["iso3", "country", "hemisphere", "n_as_affiliation",
                 "n_as_case_study", "production_to_problem_ratio",
                 "n_domestic_studies", "n_externally_authored_studies",
                 "pct_domestic"], t13,
                "Production-to-problem ratio > 1 indicates a country that "
                "produces more point-based spatial analysis than it is the "
                "subject of; < 1 indicates the reverse.")
    dom_n = sum(1 for r in pairs if r["domestic_research"] == "1")
    ext_n = sum(1 for r in pairs if str(r["extractive_pattern"]) == "1")
    R["asymmetry"] = {
        "n_pairs": len(pairs),
        "pct_domestic": pct(dom_n, len(pairs)),
        "pct_externally_authored": pct(len(pairs) - dom_n, len(pairs)),
        "n_south_case_north_only_authors": ext_n,
        "pct_south_case_north_only_authors": pct(ext_n, len(pairs)),
    }
    south_cases = [r for r in pairs if r["case_hemisphere"] == "Global South"]
    north_cases = [r for r in pairs if r["case_hemisphere"] == "Global North"]
    R["asymmetry"]["south_cases_n"] = len(south_cases)
    R["asymmetry"]["north_cases_n"] = len(north_cases)
    R["asymmetry"]["pct_domestic_south"] = pct(
        sum(1 for r in south_cases if r["domestic_research"] == "1"), len(south_cases))
    R["asymmetry"]["pct_domestic_north"] = pct(
        sum(1 for r in north_cases if r["domestic_research"] == "1"), len(north_cases))

    # =====================================================================
    # T14  International collaboration
    # =====================================================================
    t14 = []
    for p in PERIOD_ORDER:
        sub = [r for r in rows if r["period_label"] == p]
        ic = sum(1 for r in sub if r["international_collab"])
        t14.append([p, len(sub), ic, pct(ic, len(sub)),
                    round(sum(r["n_affil_countries"] for r in sub) / len(sub), 2)])
    write_table("T14_international_collaboration.csv",
                ["period", "n_studies", "n_international", "pct_international",
                 "mean_affiliation_countries"], t14)
    R["collaboration"] = {r[0]: {"pct_international": r[3], "mean_countries": r[4]}
                          for r in t14}

    # country co-authorship edges
    edges = Counter()
    for r in rows:
        cs = sorted(set(r["affil_iso3"]))
        for i in range(len(cs)):
            for j in range(i + 1, len(cs)):
                edges[(cs[i], cs[j])] += 1
    t14b = [[a, b, GEO.ISO3_TO_NAME.get(a, a), GEO.ISO3_TO_NAME.get(b, b), w,
             "North-North" if GEO.hemisphere(a) == GEO.hemisphere(b) == "Global North"
             else ("South-South" if GEO.hemisphere(a) == GEO.hemisphere(b) == "Global South"
                   else "North-South")]
            for (a, b), w in edges.most_common()]
    write_table("T15_country_collaboration_edges.csv",
                ["iso3_a", "iso3_b", "country_a", "country_b", "n_co_authored",
                 "dyad_type"], t14b,
                "Country-level co-authorship edges derived from affiliation "
                "strings. Author-level networks are not derivable from this "
                "export (no author field).")
    dyad = Counter(e[5] for e in t14b for _ in range(e[4]))
    R["collaboration"]["dyad_mix"] = {k: pct(v, sum(dyad.values())) for k, v in dyad.items()}
    R["collaboration"]["n_edges"] = len(t14b)

    # =====================================================================
    # T16  Publishers
    # =====================================================================
    pub = Counter(r["publisher"] for r in rows)
    pub_p = by_period(rows, lambda r: r["publisher"])
    t16 = [[k, v, pct(v, N), pub_p["2000-2010"][k], pub_p["2011-2020"][k],
            pub_p["2021-2027"][k]] for k, v in pub.most_common()]
    write_table("T16_publishers.csv",
                ["publisher", "n_studies", "pct_of_corpus", "n_2000_2010",
                 "n_2011_2020", "n_2021_2027"], t16,
                "Publisher derived deterministically from the DOI registrant "
                "prefix. Journal-level analysis is not possible from this "
                "export (no source-title field); see Section 3.6.")
    R["publishers"] = {"top10": t16[:10], "n_distinct_prefixes":
                       len(set(r["doi_prefix"] for r in rows))}

    # =====================================================================
    # T17  Institutions
    # =====================================================================
    inst = Counter()
    for r in rows:
        inst.update(set(r["institutions"]))
    t17 = [[k, v, pct(v, N)] for k, v in inst.most_common(60)]
    write_table("T17_institutions.csv",
                ["institution_string", "n_studies", "pct_of_corpus"], t17,
                "Institutions extracted heuristically from affiliation "
                "strings; name variants are NOT disambiguated, so counts are "
                "lower bounds. See Section 3.6.")
    R["institutions"] = {"top15": t17[:15], "n_distinct_strings": len(inst)}

    # =====================================================================
    # T18  Topic x method matrix
    # =====================================================================
    tm = defaultdict(Counter)
    for r in rows:
        for d in r["domains"]:
            tm[d].update(r["method_classes"])
    classes = list(LX.METHOD_CLASS_LABELS)
    t18 = []
    for d in sorted(tm, key=lambda k: -sum(tm[k].values())):
        dn = sum(1 for r in rows if d in r["domains"])
        row = [d, dn] + [tm[d][c] for c in classes] + [pct(tm[d][c], dn) for c in classes]
        t18.append(row)
    write_table("T18_domain_by_method_class.csv",
                ["application_domain", "n_studies"] +
                [f"n_{c}" for c in classes] + [f"pct_{c}" for c in classes], t18,
                "Coupling between application domains and method classes.")
    R["domain_method"] = {r[0]: {classes[i]: r[2 + len(classes) + i]
                                 for i in range(len(classes))} for r in t18}

    # =====================================================================
    # T19  Thematic evolution: distinctive terms per period (log-odds)
    # =====================================================================
    import re
    STOP = set("""the a an and or of in on for with to from by is are was were be been being
    this that these those we our their its it as at using use used based study studies
    results result show shows shown propose proposed method methods approach approaches
    data analysis analyses model models new can may also more most other such than then
    which while within between about into over under during both each two three however
    thus therefore both when where how what not no but if because via due paper article
    research well high low large small different various several many much some all one
    first second third significant significantly among across through after before""".split())
    tok = re.compile(r"[a-z][a-z\-]{3,}")

    def terms(r):
        t = (r["Title"] or "").lower()
        return [w for w in tok.findall(t) if w not in STOP]

    per_terms = {p: Counter() for p in PERIOD_ORDER}
    for r in rows:
        per_terms[r["period_label"]].update(set(terms(r)))
    total_terms = Counter()
    for p in PERIOD_ORDER:
        total_terms.update(per_terms[p])
    t19 = []
    for p in PERIOD_ORDER:
        np_ = period_n[p]
        scored = []
        for w, c in per_terms[p].items():
            if total_terms[w] < 8:
                continue
            other = total_terms[w] - c
            other_n = N - np_
            p1 = (c + 0.5) / (np_ + 1)
            p0 = (other + 0.5) / (other_n + 1)
            lo = math.log(p1 / (1 - p1)) - math.log(p0 / (1 - p0))
            scored.append((round(lo, 3), w, c, round(100 * c / np_, 1)))
        scored.sort(reverse=True)
        for lo, w, c, sh in scored[:25]:
            t19.append([p, w, c, sh, lo, "distinctive"])
        for lo, w, c, sh in scored[-15:]:
            t19.append([p, w, c, sh, lo, "depleted"])
    write_table("T19_thematic_evolution_terms.csv",
                ["period", "term", "n_titles", "pct_of_period",
                 "log_odds_vs_rest_of_corpus", "direction"], t19,
                "Title terms that most distinguish each period from the rest "
                "of the corpus (informative Dirichlet log-odds, min. 8 "
                "occurrences corpus-wide).")
    R["thematic_terms"] = {p: [x[1] for x in t19 if x[0] == p and x[5] == "distinctive"][:15]
                           for p in PERIOD_ORDER}

    # =====================================================================
    # T20  Method co-occurrence (convergence evidence)
    # =====================================================================
    co = Counter()
    for r in rows:
        ms = sorted(set(r["methods"]))
        for i in range(len(ms)):
            for j in range(i + 1, len(ms)):
                co[(ms[i], ms[j])] += 1
    mtot = Counter()
    for r in rows:
        mtot.update(set(r["methods"]))
    t20 = []
    for (a, b), w in co.most_common(80):
        exp = mtot[a] * mtot[b] / N
        t20.append([a, b, w, round(exp, 1), round(w / exp, 2) if exp else "",
                    LX.METHOD_CLASS_LABELS[LX.COMPILED["methods"][a][0]],
                    LX.METHOD_CLASS_LABELS[LX.COMPILED["methods"][b][0]]])
    write_table("T20_method_co_occurrence.csv",
                ["method_a", "method_b", "n_co_occurring", "expected_if_independent",
                 "lift", "class_a", "class_b"], t20,
                "Method pairs observed within the same study. Lift > 1 "
                "indicates methodological convergence beyond chance.")
    # cross-class convergence over time
    conv = {}
    for p in PERIOD_ORDER:
        sub = [r for r in rows if r["period_label"] == p]
        multi = sum(1 for r in sub if len(set(r["method_classes"])) >= 2)
        learn_stat = sum(1 for r in sub if "LEARNING" in r["method_classes"]
                         and ({"CLASSICAL", "INFERENTIAL", "GEOSTATISTICAL"} & set(r["method_classes"])))
        conv[p] = {"pct_multi_class": pct(multi, len(sub)),
                   "pct_learning_plus_statistical": pct(learn_stat, len(sub)),
                   "mean_methods_per_study": round(sum(r["n_methods"] for r in sub) / len(sub), 2)}
    R["convergence"] = conv

    # =====================================================================
    # T21  Country x method-class and country x domain
    # =====================================================================
    cm = defaultdict(Counter)
    cd = defaultdict(Counter)
    for r in rows:
        for iso in set(r["affil_iso3"]):
            cm[iso].update(r["method_classes"])
            cd[iso].update(r["domains"])
    top_countries = [i for i, _ in aff.most_common(25)]
    t21 = []
    for iso in top_countries:
        n = aff[iso]
        t21.append([iso, GEO.ISO3_TO_NAME.get(iso, iso), GEO.hemisphere(iso), n] +
                   [pct(cm[iso][c], n) for c in classes] +
                   [max(cd[iso], key=cd[iso].get) if cd[iso] else "",
                    round(shannon(cd[iso]), 3)])
    write_table("T21_country_method_domain_profile.csv",
                ["iso3", "country", "hemisphere", "n_studies"] +
                [f"pct_{c}" for c in classes] +
                ["dominant_domain", "domain_shannon_diversity"], t21,
                "Methodological and thematic profile of the 25 most "
                "productive affiliation countries.")

    # =====================================================================
    # T22  Research gaps: empty and thin cells of the domain x method matrix
    # =====================================================================
    t22 = []
    for d in LX.DOMAINS:
        dn = sum(1 for r in rows if d in r["domains"])
        if dn == 0:
            continue
        for c in classes:
            n = tm[d][c]
            t22.append([d, dn, LX.METHOD_CLASS_LABELS[c], n, pct(n, dn),
                        "empty" if n == 0 else ("thin" if pct(n, dn) < 10 else "populated")])
    write_table("T22_domain_method_gap_matrix.csv",
                ["application_domain", "domain_n", "method_class", "n", "pct_of_domain",
                 "gap_status"], t22,
                "Cells flagged 'empty' or 'thin' identify method-application "
                "combinations that the corpus barely covers.")
    R["gaps"] = {"n_empty_cells": sum(1 for x in t22 if x[5] == "empty"),
                 "n_thin_cells": sum(1 for x in t22 if x[5] == "thin"),
                 "n_cells": len(t22)}

    # =====================================================================
    # T23  Included-studies register (supplementary)
    # =====================================================================
    reg = []
    for r in sorted(rows, key=lambda x: (x["Year"], x["rec_id"])):
        reg.append([r["rec_id"], r["Year"], r["period_label"], r["Title"], r["DOI"],
                    r["publisher"], ";".join(r["affil_iso3"]), r["case_primary"],
                    ";".join(r["method_classes"]), ";".join(r["methods"][:4]),
                    ";".join(r["domains"][:3]), ";".join(r["data_sources"][:3]),
                    ";".join(r["software"][:3]), r["pbsam_score"]])
    write_table("T23_included_studies_register.csv",
                ["rec_id", "year", "period", "title", "doi", "publisher",
                 "affiliation_iso3", "case_study_iso3", "method_classes",
                 "methods", "domains", "data_sources", "software",
                 "pbsam_score"], reg,
                "Full register of the 916 included studies.")

    # =====================================================================
    # Structural transition statistics used in the theory section
    # =====================================================================
    def share(pred, p):
        sub = [r for r in rows if r["period_label"] == p]
        return pct(sum(1 for r in sub if pred(r)), len(sub))

    R["transitions"] = {
        "classical_only": {p: share(lambda r: set(r["method_classes"]) == {"CLASSICAL"}, p)
                           for p in PERIOD_ORDER},
        "any_learning": {p: share(lambda r: "LEARNING" in r["method_classes"], p)
                         for p in PERIOD_ORDER},
        "any_realtime": {p: share(lambda r: "REALTIME" in r["method_classes"], p)
                         for p in PERIOD_ORDER},
        "any_network": {p: share(lambda r: "NETWORK" in r["method_classes"], p)
                        for p in PERIOD_ORDER},
        "digital_trace_data": {p: share(lambda r: bool({"Social-media & geosocial data",
                                                        "Mobile phone & GPS trajectory data",
                                                        "Volunteered geographic information",
                                                        "POI & commercial geodatabases"} & set(r["data_sources"])), p)
                               for p in PERIOD_ORDER},
        "institutional_data": {p: share(lambda r: bool({"Official / administrative records",
                                                        "Field survey & in-situ sampling"} & set(r["data_sources"])), p)
                               for p in PERIOD_ORDER},
        "open_tooling": {p: share(lambda r: bool({"R (base/tidyverse)", "spatstat (R)",
                                                  "Python (scientific stack)", "QGIS",
                                                  "GRASS GIS", "GeoDa", "INLA / R-INLA"} & set(r["software"])), p)
                         for p in PERIOD_ORDER},
        "proprietary_tooling": {p: share(lambda r: bool({"ArcGIS / ArcMap / ArcGIS Pro", "MATLAB",
                                                         "SPSS / SAS / Stata"} & set(r["software"])), p)
                                for p in PERIOD_ORDER},
    }

    # decoupling index: gap between analytical complexity and rigour
    R["decoupling"] = {}
    for p in PERIOD_ORDER:
        sub = [r for r in rows if r["period_label"] == p]
        complexity = sum(r["n_methods"] for r in sub) / len(sub)
        rigour = sum(r["D2_uncertainty"] + r["D3_validation"] + r["D5_reproducibility"]
                     for r in sub) / len(sub)
        R["decoupling"][p] = {"mean_methods": round(complexity, 2),
                              "mean_rigour_0_6": round(rigour, 2),
                              "ratio": round(complexity / rigour, 2) if rigour else None}

    # learning-method rigour comparison
    lrn = [r for r in rows if "LEARNING" in r["method_classes"]]
    cls_ = [r for r in rows if "CLASSICAL" in r["method_classes"] or "INFERENTIAL" in r["method_classes"]]
    R["rigour_by_method_class"] = {
        "learning": {"n": len(lrn),
                     "pct_uncertainty": pct(sum(1 for r in lrn if r["uncertainty"]), len(lrn)),
                     "pct_validation": pct(sum(1 for r in lrn if r["validation"]), len(lrn)),
                     "pct_reproducibility": pct(sum(1 for r in lrn if r["reproducibility"]), len(lrn)),
                     "mean_pbsam": round(sum(r["pbsam_score"] for r in lrn) / len(lrn), 2)},
        "classical_inferential": {"n": len(cls_),
                                  "pct_uncertainty": pct(sum(1 for r in cls_ if r["uncertainty"]), len(cls_)),
                                  "pct_validation": pct(sum(1 for r in cls_ if r["validation"]), len(cls_)),
                                  "pct_reproducibility": pct(sum(1 for r in cls_ if r["reproducibility"]), len(cls_)),
                                  "mean_pbsam": round(sum(r["pbsam_score"] for r in cls_) / len(cls_), 2)},
    }

    # hemisphere method profiles
    R["hemisphere_profile"] = {}
    for hem in ("Global North", "Global South"):
        sub = [r for r in rows if hem in r["affil_hemisphere"]]
        R["hemisphere_profile"][hem] = {
            "n": len(sub),
            "mean_pbsam": round(sum(r["pbsam_score"] for r in sub) / len(sub), 2),
            "pct_learning": pct(sum(1 for r in sub if "LEARNING" in r["method_classes"]), len(sub)),
            "pct_classical": pct(sum(1 for r in sub if "CLASSICAL" in r["method_classes"]), len(sub)),
            "pct_reproducibility": pct(sum(1 for r in sub if r["reproducibility"]), len(sub)),
            "pct_uncertainty": pct(sum(1 for r in sub if r["uncertainty"]), len(sub)),
            "pct_international": pct(sum(1 for r in sub if r["international_collab"]), len(sub)),
        }

    # =====================================================================
    # Sensitivity: China dominates the Global-South stratum, so all
    # North/South contrasts are recomputed with China removed.
    # =====================================================================
    def hemi_block(subset, label):
        pairs_s = [r for r in subset if r["case_primary"] and r["affil_iso3"]]
        out = {"n_studies": len(subset), "n_pairs": len(pairs_s)}
        for hem in ("Global North", "Global South"):
            sub = [r for r in subset if hem in r["affil_hemisphere"]]
            cases = [r for r in pairs_s if r["case_hemisphere"] == hem]
            out[hem] = {
                "n_producing": len(sub),
                "n_as_case": len(cases),
                "pct_domestic": pct(sum(1 for r in cases if r["domestic_research"] == "1"),
                                    len(cases)) if cases else None,
                "mean_pbsam": round(sum(r["pbsam_score"] for r in sub) / len(sub), 2) if sub else None,
                "pct_learning": pct(sum(1 for r in sub if "LEARNING" in r["method_classes"]), len(sub)) if sub else None,
                "pct_reproducibility": pct(sum(1 for r in sub if r["reproducibility"]), len(sub)) if sub else None,
            }
        return {label: out}

    R["hemisphere_sensitivity"] = {}
    R["hemisphere_sensitivity"].update(hemi_block(rows, "all_studies"))
    no_cn = [r for r in rows if "CHN" not in r["affil_iso3"] and r["case_primary"] != "CHN"]
    R["hemisphere_sensitivity"].update(hemi_block(no_cn, "excluding_China"))

    # regional representation (Natural Earth continents via ISO3 lookup)
    CONTINENT = {}
    try:
        import shapefile
        sf = shapefile.Reader(os.path.join(ROOT, "assets", "naturalearth",
                                           "naturalearth_lowres.shp"))
        for rec in sf.records():
            CONTINENT[rec["iso_a3"]] = rec["continent"]
    except Exception:
        pass
    reg_aff, reg_case = Counter(), Counter()
    for iso, n in aff.items():
        reg_aff[CONTINENT.get(iso, "Unmapped")] += n
    for iso, n in case.items():
        reg_case[CONTINENT.get(iso, "Unmapped")] += n
    t24 = [[k, reg_aff[k], pct(reg_aff[k], sum(reg_aff.values())),
            reg_case[k], pct(reg_case[k], sum(reg_case.values()))]
           for k in sorted(set(reg_aff) | set(reg_case), key=lambda x: -reg_aff[x])]
    write_table("T24_regional_representation.csv",
                ["region", "n_affiliation_mentions", "pct_affiliation",
                 "n_case_study_mentions", "pct_case_study"], t24,
                "Continental aggregation of affiliation and case-study "
                "geography (Natural Earth continents).")
    R["regional"] = {r[0]: {"aff_pct": r[2], "case_pct": r[4]} for r in t24}

    # countries entirely absent from the corpus
    world_iso = set(CONTINENT) - {"-99", ""}
    R["absent_countries"] = {
        "n_world_countries_in_basemap": len(world_iso),
        "n_never_affiliation": len(world_iso - set(aff)),
        "n_never_case_study": len(world_iso - set(case)),
        "n_never_either": len(world_iso - set(aff) - set(case)),
        "african_countries_in_basemap": sum(1 for i in world_iso if CONTINENT.get(i) == "Africa"),
        "african_never_affiliation": sum(1 for i in world_iso
                                         if CONTINENT.get(i) == "Africa" and i not in aff),
    }

    with open(os.path.join(DER, "results.json"), "w") as f:
        json.dump(R, f, indent=2)
    print(json.dumps({k: R[k] for k in
                      ["corpus_size", "period_n", "growth", "non_reporting",
                       "convergence", "decoupling", "asymmetry"]}, indent=2)[:4000])
    print("\nTables written to", TAB)
    return R


if __name__ == "__main__":
    main()
