#!/usr/bin/env python3
"""
Build the screened corpus for the systematic review of point-based spatial analysis.

Reads data/batch_*.json (records coded at full-text/abstract screening),
performs duplicate detection on normalised titles, applies the eligibility
decisions recorded during screening, and writes:

  data/corpus.csv       all retrieved records with screening decisions
  data/included.csv     records meeting eligibility criteria
  data/prisma.json      PRISMA 2020 flow counts
"""
import json
import re
import glob
import os
from collections import Counter, OrderedDict

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")

METHOD_LABELS = OrderedDict([
    ("KDE",    "Kernel density estimation"),
    ("RIPLEY", "Distance-based second-order statistics (K, L, g, F, G, J)"),
    ("NN",     "Nearest-neighbour indices"),
    ("SCAN",   "Scan statistics"),
    ("LISA",   "Local indicators of spatial association on points"),
    ("PPM",    "Parametric point process models (Poisson, Cox, LGCP, Gibbs)"),
    ("STPP",   "Spatio-temporal / self-exciting point processes"),
    ("NET",    "Network-constrained point pattern analysis"),
    ("COLOC",  "Co-location, bivariate and marked point patterns"),
    ("ML",     "Machine-learning and neural point processes"),
    ("OTHER",  "Other"),
])

DOMAIN_LABELS = OrderedDict([
    ("HEALTH",  "Public health and epidemiology"),
    ("ECOL",    "Ecology, forestry and biodiversity"),
    ("CRIME",   "Crime and policing"),
    ("TRAFFIC", "Road safety and transport"),
    ("SEISM",   "Seismology"),
    ("FIRE",    "Wildfire"),
    ("URBAN",   "Urban and economic geography"),
    ("ARCH",    "Archaeology and heritage"),
    ("ENV",     "Environmental exposure"),
    ("BIOIMG",  "Cell biology and microscopy"),
    ("METH",    "Methodological / statistical"),
    ("OTHER",   "Other"),
])

# Broad geographic groupings used for the world map and equity analysis.
REGION = {
    "United States": "Northern America", "Canada": "Northern America",
    "United Kingdom": "Europe", "Spain": "Europe", "Italy": "Europe",
    "Germany": "Europe", "France": "Europe", "Portugal": "Europe",
    "Switzerland": "Europe", "Denmark": "Europe", "Poland": "Europe",
    "Czech Republic": "Europe", "Lithuania": "Europe", "Norway": "Europe",
    "Austria": "Europe", "Greece": "Europe",
    "China": "Eastern Asia", "Japan": "Eastern Asia",
    "South Korea": "Eastern Asia",
    "India": "Southern Asia", "Pakistan": "Southern Asia",
    "Sri Lanka": "Southern Asia", "Nepal": "Southern Asia",
    "Iran": "Western Asia", "Turkiye": "Western Asia",
    "Saudi Arabia": "Western Asia",
    "Indonesia": "South-eastern Asia", "Thailand": "South-eastern Asia",
    "Vietnam": "South-eastern Asia", "Philippines": "South-eastern Asia",
    "Brazil": "Latin America", "Argentina": "Latin America",
    "Colombia": "Latin America", "Mexico": "Latin America",
    "Peru": "Latin America", "Ecuador": "Latin America",
    "Chile": "Latin America", "Venezuela": "Latin America",
    "South Africa": "Sub-Saharan Africa", "Kenya": "Sub-Saharan Africa",
    "Nigeria": "Sub-Saharan Africa", "Ethiopia": "Sub-Saharan Africa",
    "Botswana": "Sub-Saharan Africa", "Cameroon": "Sub-Saharan Africa",
    "Benin": "Sub-Saharan Africa",
    "Tunisia": "Northern Africa", "Egypt": "Northern Africa",
    "Australia": "Oceania", "New Zealand": "Oceania",
    "Papua New Guinea": "Oceania",
}

# World Bank-style income grouping, for the research-equity analysis.
INCOME = {
    "United States": "High", "Canada": "High", "United Kingdom": "High",
    "Spain": "High", "Italy": "High", "Germany": "High", "France": "High",
    "Portugal": "High", "Switzerland": "High", "Denmark": "High",
    "Poland": "High", "Czech Republic": "High", "Lithuania": "High",
    "Norway": "High", "Austria": "High", "Greece": "High",
    "Japan": "High", "South Korea": "High", "Australia": "High",
    "New Zealand": "High", "Saudi Arabia": "High", "Chile": "High",
    "China": "Upper-middle", "Brazil": "Upper-middle",
    "Argentina": "Upper-middle", "Colombia": "Upper-middle",
    "Mexico": "Upper-middle", "Peru": "Upper-middle",
    "Turkiye": "Upper-middle", "Thailand": "Upper-middle",
    "South Africa": "Upper-middle", "Botswana": "Upper-middle",
    "Venezuela": "Upper-middle", "Ecuador": "Upper-middle",
    "Indonesia": "Lower-middle", "India": "Lower-middle",
    "Pakistan": "Lower-middle", "Vietnam": "Lower-middle",
    "Philippines": "Lower-middle", "Sri Lanka": "Lower-middle",
    "Nepal": "Lower-middle", "Iran": "Lower-middle", "Egypt": "Lower-middle",
    "Tunisia": "Lower-middle", "Kenya": "Lower-middle",
    "Nigeria": "Lower-middle", "Cameroon": "Lower-middle",
    "Papua New Guinea": "Lower-middle",
    "Ethiopia": "Low", "Benin": "Low",
}


def norm_title(t):
    """Normalise a title for duplicate detection."""
    t = t.lower()
    t = re.sub(r"[^a-z0-9 ]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def main():
    records = []
    for path in sorted(glob.glob(os.path.join(DATA, "batch_*.json"))):
        with open(path) as fh:
            records.extend(json.load(fh))

    df = pd.DataFrame(records)
    n_retrieved = len(df)

    # --- Duplicate detection on normalised titles -------------------------
    df["title_key"] = df["title"].map(norm_title)
    dup_mask = df.duplicated("title_key", keep="first")
    n_dup_auto = int(dup_mask.sum())
    df.loc[dup_mask & (df["include"] == 1), "excl"] = "Duplicate record (identical title)"
    df.loc[dup_mask, "include"] = 0
    df["auto_duplicate"] = dup_mask

    # Duplicates already flagged during manual screening (preprint/journal
    # pairs, corrections) are counted with the automatic ones.
    manual_dup = df["excl"].str.startswith("Duplicate", na=False) & ~dup_mask
    n_dup = n_dup_auto + int(manual_dup.sum())

    after_dup = n_retrieved - n_dup

    # --- Eligibility ------------------------------------------------------
    non_dup = df[~(dup_mask | manual_dup)]
    excluded = non_dup[non_dup["include"] == 0]
    included = df[df["include"] == 1].copy()

    excl_counts = Counter(excluded["excl"])

    # --- Derived fields ---------------------------------------------------
    included["method_label"] = included["method"].map(METHOD_LABELS)
    included["domain_label"] = included["domain"].map(DOMAIN_LABELS)
    included["region"] = included["country"].map(REGION).fillna("Not attributable")
    included["income_group"] = included["country"].map(INCOME).fillna("Not attributable")
    included["n_methods"] = included["methods_all"].map(len)
    included["era"] = pd.cut(
        included["year"],
        bins=[1900, 2005, 2012, 2019, 2030],
        labels=["<=2005", "2006-2012", "2013-2019", "2020-2026"],
    )

    df.drop(columns=["title_key"]).to_csv(os.path.join(DATA, "corpus.csv"), index=False)
    included.drop(columns=["title_key"]).to_csv(os.path.join(DATA, "included.csv"), index=False)

    prisma = {
        "records_retrieved": n_retrieved,
        "n_queries": int(df["q"].nunique()),
        "duplicates_removed": n_dup,
        "records_screened": after_dup,
        "records_excluded": int(len(excluded)),
        "studies_included": int(len(included)),
        "exclusion_reasons": dict(excl_counts.most_common()),
        "year_range": [int(included["year"].min()), int(included["year"].max())],
        "countries_represented": int(
            included.loc[
                ~included["country"].isin(
                    ["Not applicable", "Not specified", "Multiple"]),
                "country"].nunique()),
        "median_citations": float(included["cites"].median()),
        "spatiotemporal_share": float((included["st"] == "Y").mean()),
        "multi_method_share": float((included["n_methods"] > 1).mean()),
    }
    with open(os.path.join(DATA, "prisma.json"), "w") as fh:
        json.dump(prisma, fh, indent=2)

    print(json.dumps(prisma, indent=2))


if __name__ == "__main__":
    main()
