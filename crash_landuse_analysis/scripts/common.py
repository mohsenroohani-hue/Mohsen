"""Shared definitions for the land-use x crash-type spatial analysis.

Data: Florida arterial intersections (n=489) and segments (n=334), six counties,
4-year crash totals (inferred from rate fields: CR_ALL / rate_pi_all = 4).
Geometry is WKT in NAD83 / UTM zone 17N (EPSG:26917).
"""
from pathlib import Path

import numpy as np
import pandas as pd
import geopandas as gpd
from shapely import wkt

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "outputs"
FIG = OUT / "figures"
TAB = OUT / "tables"
GIS = OUT / "gis"
for p in (FIG, TAB, GIS):
    p.mkdir(parents=True, exist_ok=True)

CRS = 26917
YEARS = 4

FILES = {
    "int": DATA / "Intersections_20251022.csv",
    "seg": DATA / "Segment_20251022.csv",
}
FACILITY_LABEL = {"int": "Intersections", "seg": "Segments"}

# Crash types modelled as dependent variables (CR_<TYPE><SEVERITY> fields).
CRASH_TYPES = {
    "ALL": "All crash types",
    "ANGLE": "Angle",
    "LEFTTURN": "Left turn",
    "RIGHTTURN": "Right turn",
    "REAREND": "Rear end",
    "SIDESWIPE": "Sideswipe",
    "HEADON": "Head on",
    "OFFROAD": "Run-off-road",
    "ROLLOVER": "Rollover",
    "SINGLE": "Single vehicle (other)",
    "PED": "Pedestrian",
    "BIKE": "Bicycle",
    "ALCOHOL": "Alcohol-involved",
}
SHORT_TYPE = {
    "ALL": "All", "ANGLE": "Angle", "LEFTTURN": "Left turn", "RIGHTTURN": "Right turn",
    "REAREND": "Rear end", "SIDESWIPE": "Sideswipe", "HEADON": "Head on",
    "OFFROAD": "Run-off-road", "ROLLOVER": "Rollover", "SINGLE": "Single veh.",
    "PED": "Pedestrian", "BIKE": "Bicycle", "ALCOHOL": "Alcohol",
}

# Severity levels (KABCO): Fatal = K, KSI = K+A, KAB = K+A+B, Total = all.
SEVERITIES = ["TOT", "KAB", "KSI", "FAT"]
SEV_LABEL = {"TOT": "Total", "KAB": "KAB", "KSI": "KSI", "FAT": "Fatal"}

LAND_USES = {
    "LU_MXDUSE": "Mixed-use buildings",
    "LU_GASSTNS": "Gas stations",
    "LU_SUPERMKTS": "Supermarkets",
    "LU_REGSHOPCNTRS": "Regional shopping centers",
    "LU_COMMSHOPCNTRS": "Community shopping centers",
    "LU_FASTFOOD": "Fast-food restaurants",
    "LU_RESTOS": "Sit-down restaurants",
    "LU_BARS": "Bars",
    "LU_HOTELS": "Hotels",
    "LU_OFFBLDGS": "Office buildings",
    "LU_DEPTSTRS": "Department / big-box stores",
    "LU_BANKINS": "Banks",
    "LU_AUTOSALSER": "Auto sales & service",
    "LU_REPAIRSTRS": "Repair shops",
    "LU_SINGLESTORE": "Single-tenant retail stores",
    "LU_PARKSREC": "Parks & recreation",
    "LU_SCHOOLS": "Schools",
    "LU_HOSPITALS": "Hospitals",
    "LU_INDUSTRIAL": "Industrial",
}
LU_SHORT = {
    "LU_MXDUSE": "Mixed use", "LU_GASSTNS": "Gas station", "LU_SUPERMKTS": "Supermarket",
    "LU_REGSHOPCNTRS": "Regional shop. ctr", "LU_COMMSHOPCNTRS": "Community shop. ctr",
    "LU_FASTFOOD": "Fast food", "LU_RESTOS": "Restaurant", "LU_BARS": "Bar",
    "LU_HOTELS": "Hotel", "LU_OFFBLDGS": "Office", "LU_DEPTSTRS": "Big-box store",
    "LU_BANKINS": "Bank", "LU_AUTOSALSER": "Auto sales/service", "LU_REPAIRSTRS": "Repair shop",
    "LU_SINGLESTORE": "Single-tenant retail", "LU_PARKSREC": "Parks/rec", "LU_SCHOOLS": "School",
    "LU_HOSPITALS": "Hospital", "LU_INDUSTRIAL": "Industrial",
}
# Large-count land uses are expressed per 10 units so IRRs are readable.
PER10 = {"LU_MXDUSE", "LU_OFFBLDGS"}

REGIONS = {
    "Tampa Bay": ["Pinellas", "Pasco", "Hillsborough"],
    "Orlando": ["Orange"],
    "Southeast Florida": ["PalmBeach", "Broward"],
}
COUNTY_FIPS = {"Pinellas": "12103", "Pasco": "12101", "Hillsborough": "12057",
               "Orange": "12095", "PalmBeach": "12099", "Broward": "12011"}


def dv(df, ctype, sev):
    """Crash count for a crash type and severity level."""
    p = f"CR_{ctype}" if ctype != "ALL" else "CR_"
    if ctype == "ALL":
        fat, a, b, allc = df["CR_FATALITY"], df["CR_INCINJ"], df["CR_NONINCINJ"], df["CR_ALL"]
    else:
        fat, a, b, allc = df[p + "FATALITY"], df[p + "INCINJ"], df[p + "NONINCINJ"], df[p + "ALL"]
    return {"FAT": fat, "KSI": fat + a, "KAB": fat + a + b, "TOT": allc}[sev].astype(int)


def load(fac):
    """Load one facility table as a GeoDataFrame with derived variables."""
    df = pd.read_csv(FILES[fac], low_memory=False)
    geom = df["geometry"].apply(wkt.loads)
    g = gpd.GeoDataFrame(df, geometry=geom, crs=CRS)
    g["region"] = g["COUNTY"].map({c: r for r, cs in REGIONS.items() for c in cs})

    # ---- dependent variables -------------------------------------------
    for t in CRASH_TYPES:
        for s in SEVERITIES:
            g[f"y_{t}_{s}"] = dv(g, t, s)

    # ---- exposure -------------------------------------------------------
    g["aadt"] = g["RN_AADT_AVG"]
    g["ln_aadt"] = np.log(g["aadt"])
    if fac == "int":
        # million entering vehicles over the study period (major-road AADT)
        g["exposure"] = g["aadt"] * 365 * YEARS / 1e6
        cross = pd.to_numeric(g["AADTCrossSt"].astype(str).str.strip(), errors="coerce")
        g["cross_missing"] = cross.isna().astype(int)
        g["ln_aadt_cross"] = np.log(cross.fillna(cross.median()))
    else:
        # 100 million vehicle-miles travelled over the study period
        g["exposure"] = g["aadt"] * g["SEGLENGTH"] * 365 * YEARS / 1e8
        g["ln_length"] = np.log(g["SEGLENGTH"])
        g["int_per_mile"] = g["RN_INT_COUNT"] / g["SEGLENGTH"]
    g["ln_exposure"] = np.log(g["exposure"])

    # ---- design & context controls -------------------------------------
    g["lanes"] = g["RN_LANES_AVG_TOT"]
    g["speed10"] = g["RN_MAXSPEED_AVG"] / 10.0
    g["raised_median"] = ((g["RN_MEDIAN_TYPE_HASRAISEDPAVED"] > 0) |
                          (g["RN_MEDIAN_TYPE_HASRAISEDVEGETATI"] > 0)).astype(int)
    g["shoulder10"] = g["RN_SHLDO_AV_TWIDTH"] / 10.0
    g["bikelane"] = (g["RN_BKLN_PC_TCOVERAGE"] > 50).astype(int)
    g["busstops"] = g["Busstops"]
    g["popden"] = g["CN_POPDEN_SQMI"] / 1000.0
    g["income"] = g["CN_MED_HH_INC"] / 10000.0

    # ---- land uses: winsorised at the 99th percentile ------------------
    for lu in LAND_USES:
        cap = np.ceil(np.nanpercentile(g[lu], 99))
        v = g[lu].clip(upper=max(cap, 1))
        g["x_" + lu] = v / 10.0 if lu in PER10 else v
    g["pt"] = g.geometry.interpolate(0.5, normalized=True)
    return g


def controls(fac, reduced=False):
    """Design / exposure / context controls. Reduced set for sparse outcomes."""
    if reduced:
        base = ["ln_aadt", "lanes", "speed10"]
        if fac == "seg":
            base.append("ln_length")
        return base
    base = ["ln_aadt", "lanes", "speed10", "raised_median", "shoulder10", "bikelane",
            "busstops", "popden", "income"]
    if fac == "int":
        base += ["ln_aadt_cross", "cross_missing"]
    else:
        base += ["ln_length", "int_per_mile"]
    return base


CONTROL_LABEL = {
    "ln_aadt": "ln(AADT, major road)", "ln_aadt_cross": "ln(AADT, cross street)",
    "cross_missing": "Cross-street AADT missing", "lanes": "Through lanes (total)",
    "speed10": "Posted speed (per 10 mph)", "raised_median": "Raised median (0/1)",
    "shoulder10": "Outside shoulder width (per 10 ft)", "bikelane": "Bike lane >50% (0/1)",
    "busstops": "Bus stops (count)", "popden": "Population density (000/sq mi)",
    "income": "Median HH income ($10k)", "ln_length": "ln(segment length, mi)",
    "int_per_mile": "Intersections per mile",
}


def region_fe(g, reduced=False):
    """County fixed effects (full) or metro-region fixed effects (reduced)."""
    if reduced:
        return pd.get_dummies(g["region"], prefix="reg", drop_first=True, dtype=float)
    return pd.get_dummies(g["COUNTY"], prefix="cty", drop_first=True, dtype=float)


# Functional land-use families used for the multivariate-clustering typology.
FAMILIES = {
    "Auto-oriented": ["LU_GASSTNS", "LU_AUTOSALSER", "LU_REPAIRSTRS"],
    "Food & drink": ["LU_FASTFOOD", "LU_RESTOS", "LU_BARS"],
    "Retail anchors": ["LU_SUPERMKTS", "LU_DEPTSTRS", "LU_REGSHOPCNTRS", "LU_COMMSHOPCNTRS"],
    "Small retail & services": ["LU_SINGLESTORE", "LU_BANKINS"],
    "Office, lodging & mixed use": ["LU_OFFBLDGS", "LU_HOTELS", "LU_MXDUSE"],
    "Civic & recreation": ["LU_SCHOOLS", "LU_PARKSREC", "LU_HOSPITALS"],
    "Industrial": ["LU_INDUSTRIAL"],
}
