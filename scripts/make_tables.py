#!/usr/bin/env python3
"""
Generate all manuscript and supplementary tables (CSV + LaTeX booktabs).
"""
import ast
import json
import os
from collections import OrderedDict

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAB = os.path.join(ROOT, "tables")
os.makedirs(TAB, exist_ok=True)

QUERIES = OrderedDict([
    ("S01", "point pattern analysis spatial point process methods review"),
    ("S02", "kernel density estimation hotspot mapping crime incidents"),
    ("S03", "spatial scan statistic disease cluster detection SaTScan"),
    ("S04", "Ripley's K function spatial pattern forest tree species distribution"),
    ("S05", "spatio-temporal point process earthquake ETAS self-exciting model"),
    ("S06", "network constrained point pattern analysis road traffic accidents street network"),
    ("S07", "log-Gaussian Cox process spatial epidemiology disease risk mapping"),
    ("S08", "point of interest POI spatial clustering urban vitality retail location"),
    ("S09", "wildfire ignition point pattern analysis spatial clustering"),
    ("S10", "archaeological site distribution spatial point pattern analysis settlement"),
    ("S11", "co-location quotient bivariate marked point pattern cross-K function"),
    ("S12", "deep learning neural spatio-temporal point process event prediction"),
    ("S13", "presence-only species distribution model point process MaxEnt sampling bias"),
    ("S14", "kernel density hotspot analysis health facility disease mapping Africa sub-Saharan GIS"),
])

METHOD_DEF = OrderedDict([
    ("KDE", ("Kernel density estimation",
             "Smooths event locations into a continuous intensity surface; "
             "planar, adaptive and space--time variants")),
    ("RIPLEY", ("Second-order distance statistics",
                "Ripley's $K$, $L$, pair correlation $g$, and the empty-space "
                "$F$, nearest-neighbour $G$ and $J$ functions")),
    ("NN", ("Nearest-neighbour indices",
            "Average nearest-neighbour ratio, Clark--Evans index and "
            "dispersion indices")),
    ("SCAN", ("Scan statistics",
              "Kulldorff circular, elliptic and flexibly shaped spatial and "
              "space--time scan statistics")),
    ("LISA", ("Local association on points",
              "Getis--Ord $G_i^*$ and local Moran's $I$ applied to event "
              "locations or point-derived densities")),
    ("PPM", ("Parametric point process models",
             "Inhomogeneous Poisson, Cox and log-Gaussian Cox, cluster and "
             "Gibbs processes; presence-only intensity models")),
    ("STPP", ("Spatio-temporal point processes",
              "Separable and non-separable space--time intensity models; "
              "self-exciting Hawkes and ETAS formulations")),
    ("NET", ("Network-constrained analysis",
             "Density and second-order statistics computed with shortest-path "
             "or other network metrics on linear networks")),
    ("COLOC", ("Co-location and marked patterns",
               "Cross-$K$, co-location quotient, mark correlation and "
               "multitype/bivariate summary functions")),
    ("ML", ("Machine-learning point models",
            "Neural point processes, density-based clustering, maximum-entropy "
            "and ensemble intensity learners")),
    ("OTHER", ("Other approaches",
               "Spectral, tessellation-based, fractal and graph-analytic "
               "descriptions of point configurations")),
])

DOMAIN_LABEL = OrderedDict([
    ("HEALTH", "Public health and epidemiology"),
    ("ECOL", "Ecology, forestry and biodiversity"),
    ("CRIME", "Crime and policing"),
    ("URBAN", "Urban and economic geography"),
    ("METH", "Methodological and statistical"),
    ("TRAFFIC", "Road safety and transport"),
    ("SEISM", "Seismology"),
    ("FIRE", "Wildfire"),
    ("ARCH", "Archaeology and heritage"),
    ("BIOIMG", "Cell biology and microscopy"),
    ("ENV", "Environmental exposure"),
    ("OTHER", "Other"),
])


def esc(s):
    s = str(s)
    for a, b in [("&", r"\&"), ("%", r"\%"), ("_", r"\_"), ("#", r"\#")]:
        s = s.replace(a, b)
    return s


def to_latex(df, name, caption, label, align=None, escape=True, note=None,
             fontsize=r"\footnotesize"):
    df.to_csv(os.path.join(TAB, f"{name}.csv"), index=False)
    cols = list(df.columns)
    align = align or ("l" + "r" * (len(cols) - 1))
    lines = [r"\begin{table}[htbp]", r"\centering", fontsize,
             rf"\caption{{{caption}}}", rf"\label{{{label}}}",
             rf"\begin{{tabular}}{{{align}}}", r"\toprule",
             " & ".join(esc(c) if escape else c for c in cols) + r" \\",
             r"\midrule"]
    for _, r in df.iterrows():
        lines.append(" & ".join(esc(v) if escape else str(v)
                                for v in r.tolist()) + r" \\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    if note:
        lines.append(rf"\begin{{minipage}}{{\linewidth}}\vspace{{4pt}}"
                     rf"\scriptsize {note}\end{{minipage}}")
    lines += [r"\end{table}", ""]
    with open(os.path.join(TAB, f"{name}.tex"), "w") as fh:
        fh.write("\n".join(lines))
    print("wrote", name)


def main():
    corpus = pd.read_csv(os.path.join(ROOT, "data", "corpus.csv"))
    d = pd.read_csv(os.path.join(ROOT, "data", "included.csv"))
    d["methods_list"] = d["methods_all"].map(ast.literal_eval)
    N = len(d)

    # ---------------- Table 1: search strategy --------------------------
    rows = []
    for qid, q in QUERIES.items():
        sub = corpus[corpus["q"] == qid]
        rows.append({
            "ID": qid, "Query string": q,
            "Retrieved": len(sub),
            "Included": int((sub["include"] == 1).sum()),
            "Yield (%)": f"{100*(sub['include']==1).mean():.0f}",
        })
    t1 = pd.DataFrame(rows)
    t1.loc[len(t1)] = ["Total", "", t1["Retrieved"].sum(),
                       t1["Included"].sum(),
                       f"{100*t1['Included'].sum()/t1['Retrieved'].sum():.0f}"]
    to_latex(t1, "table1_search_strategy",
             "Search strategy: query identifiers, natural-language query "
             "strings issued to the federated bibliographic index, and "
             "record yield at each stage.",
             "tab:search", align="llrrr",
             note="Searches were executed on 28 July 2026 against a federated "
                  "index spanning Semantic Scholar, PubMed, Scopus and arXiv. "
                  "Yield is the proportion of records retrieved by a query "
                  "that met all eligibility criteria; records retrieved by "
                  "more than one query are attributed to the first query that "
                  "returned them.")

    # ---------------- Table 2: eligibility criteria ---------------------
    t2 = pd.DataFrame([
        ("Population", "Studies analysing georeferenced event locations "
                       "(points) in any application field",
         "Studies analysing only areal/lattice aggregates, raster surfaces "
         "or extended (line, polygon) objects"),
        ("Concept", "Application or development of at least one point-based "
                    "spatial statistic or point process model",
         "Purely temporal point processes; accessibility, travel-time or "
         "suitability models with no point pattern statistic"),
        ("Context", "Any geography, spatial scale and time period",
         "None"),
        ("Publication type", "Peer-reviewed journal article, conference "
                             "paper, or preprint with a full abstract",
         "Books, monographs, theses, book reviews, correction notices and "
         "conference abstracts without full text"),
        ("Language", "English-language abstract available", "None"),
        ("Reporting", "Sufficient information in the record to code method "
                      "family, application domain and study area",
         "Records with no indexed abstract or with corrupted metadata"),
    ], columns=["Dimension", "Inclusion criterion", "Exclusion criterion"])
    to_latex(t2, "table2_eligibility",
             "Eligibility criteria applied at record screening.",
             "tab:elig", align="p{0.13\\linewidth}p{0.40\\linewidth}p{0.40\\linewidth}")

    # ---------------- Table 3: method taxonomy --------------------------
    rows = []
    for code, (label, definition) in METHOD_DEF.items():
        prim = d[d["method"] == code]
        anyuse = d[d["methods_list"].map(lambda s: code in s)]
        if len(anyuse) == 0:
            continue
        rows.append({
            "Method family": label,
            "Scope": definition,
            "Primary $n$": len(prim),
            "Any use $n$": len(anyuse),
            "\\% of studies": f"{100*len(anyuse)/N:.1f}",
            "Median year": int(anyuse["year"].median()),
            "Median cites": int(anyuse["cites"].median()),
            "\\% ST": f"{100*(anyuse['st']=='Y').mean():.0f}",
        })
    t3 = pd.DataFrame(rows).sort_values("Any use $n$", ascending=False)
    to_latex(t3, "table3_method_taxonomy",
             "Taxonomy of point-based method families, with usage, recency "
             "and citation profile across the 223 included studies.",
             "tab:methods",
             align="p{0.17\\linewidth}p{0.30\\linewidth}rrrrrr", escape=False,
             note="``Primary'' counts studies whose dominant analytical "
                  "approach falls in the family; ``any use'' counts every "
                  "study applying the family, so column totals exceed 223. "
                  "\\% ST is the share of studies in that family with an "
                  "explicit temporal dimension.")

    # ---------------- Table 4: method x domain --------------------------
    mrows = [c for c in METHOD_DEF if (d["method"] == c).any()]
    dcols = [c for c in DOMAIN_LABEL if (d["domain"] == c).any()]
    ct = pd.crosstab(d["method"], d["domain"]).reindex(
        index=mrows, columns=dcols, fill_value=0)
    ct.index = [METHOD_DEF[c][0] for c in ct.index]
    short = {"HEALTH": "Health", "ECOL": "Ecol.", "CRIME": "Crime",
             "URBAN": "Urban", "METH": "Meth.", "TRAFFIC": "Road",
             "SEISM": "Seism.", "FIRE": "Fire", "ARCH": "Arch.",
             "BIOIMG": "Micro.", "ENV": "Env.", "OTHER": "Other"}
    ct.columns = [short[c] for c in ct.columns]
    ct["Total"] = ct.sum(axis=1)
    ct.loc["Total"] = ct.sum(axis=0)
    t4 = ct.reset_index().rename(columns={"index": "Method family"})
    to_latex(t4, "table4_method_by_domain",
             "Cross-tabulation of primary method family by application "
             "domain (study counts).", "tab:crosstab",
             align="p{0.19\\linewidth}" + "r" * (len(t4.columns) - 1),
             fontsize=r"\scriptsize")

    # ---------------- Table 5: geography --------------------------------
    att = d[~d["country"].isin(["Not applicable", "Not specified", "Multiple"])]
    g = (att.groupby("country")
         .agg(Studies=("country", "size"),
              Region=("region", "first"),
              Income=("income_group", "first"),
              Median_year=("year", "median"))
         .sort_values("Studies", ascending=False))
    lead = att.groupby("country")["domain"].agg(
        lambda s: DOMAIN_LABEL[s.value_counts().idxmax()])
    g["Leading domain"] = lead
    g = g.head(20).reset_index()
    g["Median_year"] = g["Median_year"].astype(int)
    g.columns = ["Country", "Studies", "Region", "Income group",
                 "Median year", "Leading domain"]
    to_latex(g, "table5_country_profile",
             "Twenty most frequently studied countries, with world region, "
             "income group and leading application domain.",
             "tab:countries",
             align="lrp{0.15\\linewidth}p{0.11\\linewidth}rp{0.21\\linewidth}",
             note=f"{att['country'].nunique()} distinct countries appear across "
                  f"{len(att)} of the {N} included studies; the remainder are "
                  "methodological contributions, simulation studies or "
                  "multi-country analyses with no single case-study country.")

    # ---------------- Table 6: study characteristics ---------------------
    def pct(mask):
        return f"{int(mask.sum())} ({100*mask.mean():.1f})"

    rows = [("Total included studies", f"{N} (100.0)")]
    rows.append(("\\textit{Publication period}", ""))
    for lo, hi, lab in [(0, 2005, "1977--2005"), (2006, 2012, "2006--2012"),
                        (2013, 2019, "2013--2019"), (2020, 2030, "2020--2026")]:
        rows.append((f"\\quad {lab}", pct((d["year"] >= lo) & (d["year"] <= hi))))
    rows.append(("\\textit{Document type}", ""))
    for t in ["article", "review", "conference", "preprint"]:
        rows.append((f"\\quad {t.capitalize()}", pct(d["doc_type"] == t)))
    rows.append(("\\textit{Temporal dimension}", ""))
    rows.append(("\\quad Purely spatial", pct(d["st"] == "N")))
    rows.append(("\\quad Spatio-temporal", pct(d["st"] == "Y")))
    rows.append(("\\textit{Methodological breadth}", ""))
    rows.append(("\\quad Single method family", pct(d["n_methods"] == 1)))
    rows.append(("\\quad Two method families", pct(d["n_methods"] == 2)))
    rows.append(("\\quad Three or more", pct(d["n_methods"] >= 3)))
    rows.append(("\\textit{Geographic attribution}", ""))
    rows.append(("\\quad Single case-study country",
                 pct(~d["country"].isin(["Not applicable", "Not specified",
                                         "Multiple"]))))
    rows.append(("\\quad Multi-country", pct(d["country"] == "Multiple")))
    rows.append(("\\quad Not attributable / simulation",
                 pct(d["country"].isin(["Not applicable", "Not specified"]))))
    rows.append(("\\textit{National income group (attributable studies)}", ""))
    att2 = d[d["income_group"] != "Not attributable"]
    for gname in ["High", "Upper-middle", "Lower-middle", "Low"]:
        m = att2["income_group"] == gname
        rows.append((f"\\quad {gname} income",
                     f"{int(m.sum())} ({100*m.mean():.1f})"))
    rows.append(("\\textit{Citation impact}", ""))
    rows.append(("\\quad Median citations (IQR)",
                 f"{d['cites'].median():.0f} "
                 f"({d['cites'].quantile(.25):.0f}--{d['cites'].quantile(.75):.0f})"))
    t6 = pd.DataFrame(rows, columns=["Characteristic", "$n$ (\\%)"])
    to_latex(t6, "table6_study_characteristics",
             "Characteristics of the 223 included studies.",
             "tab:characteristics", align="p{0.55\\linewidth}r", escape=False,
             note="Percentages within the income-group block are computed over "
                  "the subset of studies attributable to a single country.")

    # ---------------- Supplementary S1 / S2 ------------------------------
    s1 = d[["authors", "year", "title", "journal", "method", "domain",
            "country", "st", "cites", "url"]].sort_values(["year", "authors"])
    s1.columns = ["Authors", "Year", "Title", "Journal", "Method family",
                  "Domain", "Study area", "Spatio-temporal", "Citations",
                  "Record URL"]
    s1.to_csv(os.path.join(TAB, "tableS1_included_studies.csv"), index=False)

    s2 = corpus[corpus["include"] == 0][
        ["authors", "year", "title", "journal", "excl"]]
    s2.columns = ["Authors", "Year", "Title", "Journal", "Reason for exclusion"]
    s2.to_csv(os.path.join(TAB, "tableS2_excluded_records.csv"), index=False)
    print("wrote tableS1_included_studies, tableS2_excluded_records")

    # summary stats consumed by the manuscript
    stats = {
        "n": N,
        "median_year": int(d["year"].median()),
        "share_2020plus": float((d["year"] >= 2020).mean()),
        "share_st": float((d["st"] == "Y").mean()),
        "share_multi": float((d["n_methods"] > 1).mean()),
        "share_ml": float(d["methods_list"].map(lambda s: "ML" in s).mean()),
        "share_ml_2020": float(d[d["year"] >= 2020]["methods_list"]
                               .map(lambda s: "ML" in s).mean()),
        "share_net": float(d["methods_list"].map(lambda s: "NET" in s).mean()),
        "n_countries": int(att["country"].nunique()),
        "top5_share": float(att["country"].value_counts()
                            .head(5).sum() / len(att)),
        "high_income_share": float((att2["income_group"] == "High").mean()),
        "low_income_share": float(att2["income_group"].isin(["Low"]).mean()),
        "africa_share": float(att["region"].isin(
            ["Sub-Saharan Africa", "Northern Africa"]).mean()),
    }
    with open(os.path.join(ROOT, "data", "summary_stats.json"), "w") as fh:
        json.dump(stats, fh, indent=2)
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
