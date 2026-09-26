// Report content.
const { PageBreak, Paragraph } = require("docx");
const H = require("./helpers");
const { P, H1, H1nb, H2, H3, bullets, numbered, figure, table, pageBreak, callout, DATA, F, T } = H;

const LU_ORDER = [
  ["LU_MXDUSE", "Mixed-use buildings"], ["LU_GASSTNS", "Gas stations"], ["LU_SUPERMKTS", "Supermarkets"],
  ["LU_REGSHOPCNTRS", "Regional shopping centers"], ["LU_COMMSHOPCNTRS", "Community shopping centers"],
  ["LU_FASTFOOD", "Fast-food restaurants"], ["LU_RESTOS", "Sit-down restaurants"], ["LU_BARS", "Bars"],
  ["LU_HOTELS", "Hotels"], ["LU_OFFBLDGS", "Office buildings"], ["LU_DEPTSTRS", "Department / big-box stores"],
  ["LU_BANKINS", "Banks"], ["LU_AUTOSALSER", "Auto sales & service"], ["LU_REPAIRSTRS", "Repair shops"],
  ["LU_SINGLESTORE", "Single-tenant retail stores"], ["LU_PARKSREC", "Parks & recreation"], ["LU_SCHOOLS", "Schools"],
  ["LU_HOSPITALS", "Hospitals"], ["LU_INDUSTRIAL", "Industrial"],
];

// ------------------------------------------------------------------ 1 executive summary
function execSummary() {
  return [
    H1nb("1  Executive summary"),
    P("This report takes the approach used in the earlier study of vulnerable-road-user (VRU) crashes and land use and extends it to every crash type and to four severity levels. For each land use it asks whether the presence of that land use at an intersection or along a segment is associated with more (or fewer) crashes of a given type, after accounting for traffic exposure, roadway design and neighbourhood context — and whether those associations cluster in space. Separate models were estimated for Fatal, KSI, KAB and Total crashes, as requested."),
    ...callout("Which spatial methods fit these data", [
      "**GeoDa** is the best tool for the exploratory layer: it is the only one of the three that computes Moran's I and LISA directly on **Empirical-Bayes (EB) crash rates** (essential when exposure varies and many sites have zero KSI or fatal crashes), and it has **local join counts** for rare binary outcomes such as “site had a fatal crash”, plus **bivariate LISA** to screen each land use against each crash type.",
      "**ArcGIS Pro** adds **Incremental Spatial Autocorrelation** (to find the clustering scale), **Hot Spot Analysis (Gi*)** with FDR correction, **Multivariate Clustering** for land-use typologies and **Multiscale GWR (MGWR)** to test whether land-use effects vary across metros.",
      "**QGIS** is best for data preparation (the WKT geometry loads directly), cartography and plugin-based hot-spot mapping; attribute clustering and regression are run from its Python console or R provider.",
      "**None of the three GIS packages can estimate the core crash-type × severity models properly**: crash counts are over-dispersed and fatal/KSI counts by crash type are sparse, so negative-binomial and penalised (Firth) count models are needed. These were run in Python (scripts supplied) and the results were brought back into the GIS layers for mapping.",
    ]),
    ...callout("What the analysis shows", [
      "**Crash risk clusters.** EB-rate Moran's I is significant for almost every crash type at Total and KAB levels, strongest on segments (I = 0.43 for all KAB crashes) and for rear-end, angle and pedestrian crashes; clustering peaks at a corridor scale of about **6–8 km**. Fatal crashes cluster weakly, but **26 segments and 9 intersections sit in significant pedestrian-KSI clusters**.",
      "**Land uses associated with more crashes after controlling for exposure, design and context.** The land uses that recur most often are **gas stations**, **community shopping centers**, **fast-food restaurants**, **single-tenant retail**, **supermarkets**, **auto sales & service** and, for pedestrians, **hotels**. For example, each gas station at an intersection is associated with 35% more angle crashes, 47% more pedestrian KAB crashes and 78% more pedestrian KSI crashes. Each fast-food restaurant is associated with 53% more fatal crashes, and each auto dealership or service outlet on a segment with 12% more fatal crashes.",
      "**Severity matters.** Land uses that generate turning traffic and short trips raise vehicle-to-vehicle crashes (angle, turning, sideswipe) mainly at Total and KAB levels. At KSI and Fatal levels the land-use signal concentrates on **pedestrians**, run-off-road/single-vehicle and bicycle crashes. For pedestrian KSI crashes, adding the land-use variables improves model AIC by 14 points at intersections and 36 points on segments.",
      "**Context typology.** Intersections in the *shopping-center / big-box retail* context have 2.1 times the total crash rate and 8 times the pedestrian KSI rate of *low-intensity frontage*. After adjustment, their pedestrian KSI incidence is 6.7 times higher (95% CI 2.4–18.8).",
      "**Some land uses are associated with fewer crashes**: office buildings (fewer KSI), industrial frontage (fewer total and rear-end crashes), sit-down restaurants (fewer severe left-turn crashes at intersections) and schools (fewer head-on crashes).",
      "**Spatial effects are handled.** Eigenvector spatial filtering removed most of the residual spatial autocorrelation. The land-use effects hold when each corridor is compared only with itself (corridor fixed effects). In MGWR, baseline risk varies locally, but 78 of 104 land-use slopes are global and only 3 are local. The land-use findings are therefore not an artefact of one corridor or one metro.",
    ]),
    P(`The design variables available in the file (lanes, median type, shoulder width, bike lane, posted speed) had weaker and less consistent associations than exposure and land use (${T("controls")}), and the land-use effects persist after controlling for them. This is consistent with the hypothesis that severe crashes cluster by land-use type and do not only follow roadway design.`),
  ];
}

// ------------------------------------------------------------------ 2 data
function dataSection() {
  const counts = DATA.tab_counts;
  return [
    H1("2  Research question, data and variables"),
    H2("2.1  Research question and hypotheses"),
    P("**Question.** Which land uses exacerbate crash risk for different crash types, and do these relationships differ by severity (Fatal, KSI, KAB, Total)?"),
    ...bullets([
      "**H1 – clustering:** crash rates of each type are spatially clustered along the corridors rather than randomly distributed.",
      "**H2 – land use:** net of exposure and roadway design, the presence of specific land uses (particularly auto-oriented and retail uses that generate frequent turning movements, driveway activity and pedestrian trips) is associated with higher incidence of specific crash types.",
      "**H3 – severity gradient:** the land uses associated with severe outcomes (KSI, fatal) differ from those associated with total crash frequency. Severe outcomes should concentrate in crash types involving pedestrians and high-energy conflicts.",
      "**H4 – stationarity:** land-use effects are broadly similar across the three metropolitan areas (tested with MGWR).",
    ]),
    H2("2.2  Study units and geography"),
    P("The intersection file contains 489 intersection influence areas (≈500 ft / 0.095 mi of the major road) and the segment file 334 mid-block segments (mean length 0.53 mi, range 0.20–2.60 mi). Both lie on ten principal arterials in three metro areas: Tampa Bay (US 19, Alt US 19, SR 580), Orlando (Colonial Dr/SR 50, SR 600) and Southeast Florida (Military Trail, Lake Worth Rd, Oakland Park Blvd, Sunrise Blvd, University Dr). Geometry is stored as WKT in NAD83 / UTM zone 17N (EPSG:26917). Crash totals cover four years. The period was inferred from the rate fields (CR_ALL ÷ rate_pi_all = 4)."),
    ...figure("fig01_study_area.png", "Study area: the ten arterial corridors, 334 segments (grey) and 489 intersections (circles sized by 4-year total crashes)."),
    ...figure("fig02a_ksi_intersections.png", "KSI (fatal + incapacitating-injury) crashes per intersection, 4 years."),
    ...figure("fig02b_ksi_segments.png", "Segment KSI crash rate per 100 million vehicle-miles travelled (VMT)."),
    H2("2.3  Dependent variables: crash type × severity"),
    P("Each crash type was modelled at four nested severity levels built from the KABCO fields: **Fatal** (K), **KSI** (K + A, killed or seriously injured), **KAB** (K + A + B) and **Total** (all crashes including possible-injury and property-damage-only). Alcohol-involved crashes are a contributing-factor category rather than a collision type, but they were kept as a supplementary outcome because of the hypothesised link with bars and restaurants. Animal, *other* and *unknown* crashes were not modelled separately; they are included in *All crash types*."),
    ...table("Crash counts by type and severity (4 years).",
      [[{ text: "Crash type" }, { text: "Intersections (n = 489)", span: 4 }, { text: "Segments (n = 334)", span: 4 }],
        ["", "Total", "KAB", "KSI", "Fatal", "Total", "KAB", "KSI", "Fatal"]],
      counts, [2160, 900, 900, 900, 900, 900, 900, 900, 900],
      { note: "KSI = fatal + incapacitating injury; KAB = KSI + non-incapacitating injury. Outcomes with fewer than 20 crashes were not modelled (e.g., fatal angle, rear-end and sideswipe crashes)." }),
    P(`Severity propensity differs sharply by crash type (${F("fig03_severity_propensity.png")}). Pedestrian crashes are the most severe: 22% of pedestrian crashes at intersections and 35% on segments are KSI, and 59 (intersections) and 153 (segments) of every 1,000 pedestrian crashes are fatal. Rear-end and sideswipe crashes are frequent but rarely severe. This is why the land-use signal differs by severity level.`),
    ...figure("fig03_severity_propensity.png", "Severity propensity by crash type: (a) KSI crashes per 100 crashes; (b) fatal crashes per 1,000 crashes."),
    H2("2.4  Land uses and control variables"),
    P(`The 19 land-use variables are counts of establishments at each site. Their prevalence varies widely (${F("fig04_landuse_prevalence.png")}). Single-tenant retail and office buildings are present at most sites, whereas regional shopping centers, bars, repair shops and hospitals occur at fewer than 5% of intersections. For these rare land uses the estimates are imprecise and are flagged (†) throughout. Counts were winsorised at the 99th percentile to limit the leverage of a few extreme sites. Mixed-use and office buildings are expressed per 10 establishments. Correlations between land uses are modest (mostly |ρ| < 0.4; ${F("fig05_landuse_correlation.png")}), so they can be modelled individually and jointly.`),
    ...figure("fig04_landuse_prevalence.png", "Share of sites with at least one establishment of each land use."),
    ...figure("fig05_landuse_correlation.png", "Spearman correlations among the 19 land-use counts (values shown where |ρ| ≥ 0.4).", 6.5),
    P("**Controls.** Every model includes exposure (ln AADT of the major road; ln cross-street AADT with a missing-data flag at intersections; ln segment length and intersections per mile on segments), roadway design (total through lanes, posted speed, raised median, outside shoulder width, bike lane coverage), context (bus stops, population density, median household income) and county fixed effects. Sparse outcomes use a reduced set (see §3.5)."),
    ...table("Descriptive statistics — mean (SD).", ["Variable", "Intersections", "Segments"], DATA.tab_desc, [4360, 2500, 2500]),
  ];
}

// ------------------------------------------------------------------ 3 method fit
function methodSection() {
  const rows = [
    ["Is crash risk clustered, and at what scale?", "Global Moran's I on EB-standardised rates; incremental autocorrelation", "Exposure varies 15-fold and many sites have zero KSI/fatal crashes; EB standardisation stops low-volume sites dominating", "Python console (esda)", "Spatial Autocorrelation; Incremental Spatial Autocorrelation", "Moran's I with EB Rate; Spatial Correlogram", "Core"],
    ["Where are high-risk clusters and outliers?", "Local Moran (LISA) on EB rates", "Separates High-High clusters from High-Low outliers (a risky site among safe neighbours)", "Hotspot Analysis plugin (on eb_ fields)", "Cluster and Outlier Analysis (Anselin Local Moran's I)", "Local Moran's I with EB Rate", "Core"],
    ["Where are hot and cold spots?", "Getis-Ord Gi* on EB-smoothed rates, FDR option", "Agency-friendly hot/cold-spot maps; confidence bins", "Hotspot Analysis plugin", "Hot Spot Analysis (Getis-Ord Gi*)", "Local G*", "Core"],
    ["Do fatal crashes cluster?", "Local join count (binary)", "Fatal crashes are 0/1 at most sites; join counts are designed for rare binary events", "—", "(no direct tool)", "Univariate Local Join Count", "Recommended"],
    ["Is each land use spatially associated with crash risk?", "Bivariate Moran & bivariate LISA; Local Bivariate Relationships", "Screens 19 land uses × 13 crash types quickly and maps co-location", "—", "Local Bivariate Relationships; Bivariate Spatial Association (Lee's L)", "Bivariate (Local) Moran's I", "Exploratory"],
    ["Which land-use contexts exist?", "K-means / multivariate clustering on land-use families; SKATER for contiguous zones", "Turns 19 sparse counts into interpretable contexts", "Python console (core K-means clusters by location only)", "Multivariate Clustering; Spatially Constrained Multivariate Clustering", "K Means; SKATER; REDCAP", "Recommended"],
    ["How much does each land use change each crash type at each severity?", "NB2 count models + exposure, design controls, fixed effects; Firth-penalised Poisson for sparse outcomes; FDR", "Counts are over-dispersed; fatal/KSI by type are sparse; GIS regression tools cannot fit NB or penalised models", "Processing R Provider or Python console (scripts supplied)", "Python Notebook (GLR “Count” = Poisson only; screening)", "— (continuous outcomes only)", "Core inference"],
    ["Is there residual spatial dependence?", "Residual Moran's I; eigenvector spatial filtering (ESF); LM lag/error tests", "Crash rates cluster at 6–8 km; ignoring it overstates precision", "Python console", "Spatial Autocorrelation on a residual field", "OLS + LM diagnostics; Spatial Lag / Error on ln(EB rate)", "Core (diagnostic)"],
    ["Do land-use effects vary across metros?", "MGWR on ln(EB rate)", "Gives each land use its own bandwidth, so local and global effects can be told apart", "— (MGWR 2.2 / Python)", "Multiscale Geographically Weighted Regression", "—", "Recommended"],
    ["Where is crash density highest along the network?", "Network kernel density (NKDE)", "Needs individual crash points, which this site-level file does not contain", "SANET / spNetwork", "SANET toolbox", "—", "Future"],
    ["Are clusters emerging over time?", "Space-time cube; Emerging Hot Spot Analysis", "Needs crash dates", "—", "Create Space Time Cube; Emerging Hot Spot Analysis", "—", "Future"],
    ["Are crash types co-located with specific establishments?", "Colocation quotient", "Needs point locations of crashes and businesses", "—", "Colocation Analysis", "Co-location Join Count", "Future"],
  ];
  return [
    H1("3  Which spatial analysis methods fit these data?"),
    H2("3.1  Data characteristics that drive the choice of method"),
    ...bullets([
      "**Units are network sites, not areas.** Intersections are points (influence areas) and segments are lines along ten corridors. Contiguity weights (Queen/Rook) do not apply; **k-nearest-neighbour or distance-band weights** on site mid-points do. The corridors sit in three metros up to 250 km apart, so k-NN (k = 6) keeps every site connected to its own corridor without creating islands. The results were checked with k = 4, 8 and 10.",
      "**Outcomes are counts with very unequal exposure.** AADT ranges from 5,600 to 85,600 and segment length from 0.2 to 2.6 miles. Raw counts mostly map traffic volume. Exploratory statistics should therefore use **Empirical-Bayes (EB) standardised rates** (exposure = million entering vehicles at intersections, 100 million VMT on segments), and models should include exposure.",
      "**Over-dispersion and sparsity.** Total and KAB counts are over-dispersed (NB2 α ≈ 0.1–0.8), which rules out Poisson inference and OLS. Many type-specific fatal and KSI outcomes have 20–150 events, where ordinary maximum likelihood is biased or separates. These call for **penalised (Firth) estimation** or Bayesian shrinkage.",
      "**Many land uses × crash types × severities.** 19 land uses × 13 outcomes × 4 severities × 2 facility types gives 1,976 combinations, of which 1,440 had enough crashes to estimate, so **false-discovery-rate control** is needed to separate robust signals from chance.",
      "**Spatial dependence and heterogeneity.** Clustering (§4) means model residuals are likely autocorrelated (handled by spatial filtering), and three metro areas raise the question of whether effects are stationary (handled by MGWR).",
    ]),
    H2("3.2  Method-fit matrix"),
    ...table("Recommended methods, why they fit these data, and where to run them.",
      ["Question", "Method", "Why it fits", "QGIS", "ArcGIS Pro", "GeoDa", "Role"],
      rows, [1250, 1400, 1850, 1150, 1450, 1250, 800], { size: 14, leftCols: [1, 2, 3, 4, 5] }),
    H2("3.3  Methods to avoid (or defer) with these data"),
    ...bullets([
      "**Planar kernel density (QGIS Heatmap, ArcGIS Kernel Density) of site totals:** it spreads risk into off-network space and ignores exposure. Use it for display only, or use network KDE once crash points are available.",
      "**OLS, or GeoDa spatial lag/error models, on raw counts:** these violate the count distribution. Use GeoDa regressions only for Lagrange-multiplier diagnostics on ln(EB rate).",
      "**Poisson GWR (ArcGIS GWR, model type Count):** with over-dispersed crash counts it collapsed to the minimum bandwidth here (48 neighbours) because the local intercepts absorb the extra-Poisson variation. MGWR on ln(EB rate) is more robust (§7).",
      "**Optimized Hot Spot Analysis on raw counts:** it finds high-volume corridors rather than high-risk sites. Run hot-spot tools on EB rates.",
    ]),
    H2("3.4  Workflow"),
    ...figure("fig00_workflow.png", "Analysis workflow and the software used at each stage. Stage 5 (count models) is the core inference and is run outside the GIS; every other stage has a native GeoDa and/or ArcGIS Pro tool.", 6.3),
    H2("3.5  Model specification"),
    P("For site *i*, crash type *t* and severity *s*, the expected count is modelled as"),
    P("ln E[y_its] = β0 + β1 ln(AADT_i) + γ′·Design_i + δ′·Context_i + County_i + Σ_k θ_k·E_ik + λ·LandUse_ij", { align: "center", run: { italics: true } }),
    P("where Design and Context are the controls listed in §2.4, E_ik are Moran eigenvectors selected for that outcome, and λ is the land-use effect, reported as an incidence rate ratio (IRR = e^λ, per establishment). Two versions were estimated:"),
    ...bullets([
      "**One land use at a time** (19 models per outcome). This gives the total association of each land use and is directly comparable to the per-land-use results of the VRU paper. It was run for every land use, crash type and severity, as requested.",
      "**Joint model** with all land uses entered together. This gives the association of each land use holding the others constant, and allows an overall test of whether land use adds explanatory power beyond design (likelihood-ratio test and ΔAIC against the design-only model).",
    ]),
    P("**Estimator rules.** NB2 negative binomial with the full control set and county fixed effects is used when an outcome has at least 150 crashes and is not Fatal. Otherwise — all Fatal models and sparse type-specific KSI/KAB outcomes with 20–149 crashes — a **Firth-penalised Poisson** model (Firth, 1993) is used, with quasi-Poisson standard errors to allow for over-dispersion, a reduced control set (ln AADT, lanes, speed, ln length for segments) and metro-region fixed effects. Outcomes with fewer than 20 crashes are not modelled."),
    P("**Spatial filtering.** For each outcome the Pearson residuals of the design-only model were tested for spatial autocorrelation (k = 6). If significant, eigenvectors of the doubly-centred k-NN connectivity matrix (MC ≥ 0.25 λmax) were added by forward selection until residual Moran's I was no longer significant (maximum 10, or 3 for sparse outcomes; Griffith, 2003). The same eigenvectors enter every land-use model for that outcome."),
    P("**Multiple testing.** Benjamini–Hochberg false-discovery-rate q-values were computed across all land-use × crash-type tests within each facility × severity family. The heat maps show both p < 0.05 and q < 0.10."),
  ];
}

// ------------------------------------------------------------------ 4 ESDA
function esdaSection() {
  return [
    H1("4  Where does crash risk cluster? Exploratory spatial analysis"),
    H2("4.1  Global clustering by crash type and severity"),
    P("Global Moran's I on EB-standardised rates (Assunção & Reis, 1999) is positive and significant for all crashes at every severity level, including fatal crashes (intersections I = 0.05; segments I = 0.15). Clustering is stronger on segments (I = 0.43 for Total and KAB) than at intersections (I = 0.16–0.21). By crash type, rear-end (segments KAB I = 0.40), angle (segments Total I = 0.41), pedestrian (segments KAB I = 0.30) and bicycle crashes (intersections Total I = 0.36) cluster most. At intersections, severe sideswipe, head-on and right-turn crashes show no clustering, so their risk is more site-specific."),
    ...figure("fig06_global_moran_heatmap.png", "Global Moran's I of EB-standardised crash rates by crash type and severity (k = 6 nearest neighbours, 999 permutations)."),
    H2("4.2  Scale of clustering"),
    P(`The incremental analysis (the equivalent of ArcGIS *Incremental Spatial Autocorrelation*) shows that the z-score rises to a peak at about **6–7 km for intersections and 8 km for segments**, then levels off (${F("fig07_incremental_autocorrelation.png")}). Risk therefore clusters at the scale of corridor sections a few miles long, the scale at which land-use patterns such as commercial strips change. The k-NN results are robust to the choice of k (Moran's I for KAB = 0.20–0.21 at intersections for k = 4–10).`),
    ...figure("fig07_incremental_autocorrelation.png", "Incremental spatial autocorrelation: Moran's I z-score of EB rates by distance band. Circles mark the peak distance."),
    H2("4.3  Local clusters and outliers (LISA)"),
    P("Local Moran's I on EB rates identifies 31 High-High and 50 Low-Low intersections for KSI crashes, plus 12 High-Low outliers — isolated high-risk intersections that a cluster map alone would miss. On segments there are 33 High-High and 68 Low-Low KSI segments. High-High KSI clusters concentrate on Colonial Drive in Orlando, the Military Trail / Lake Worth Road area in Palm Beach County, and the Oakland Park–Sunrise–University Drive grid in Broward County."),
    ...figure("map_lisa_int_ALL_KSI.png", "LISA cluster map — KSI crashes, intersections (EB rate, p < 0.05).", 6.3),
    ...figure("map_lisa_seg_ALL_KSI.png", "LISA cluster map — KSI crashes, segments (EB rate, p < 0.05).", 6.3),
    H2("4.4  Hot and cold spots (Getis-Ord Gi*)"),
    P("Gi* on EB-smoothed KAB rates identifies 60 hot-spot intersections (18 at 99% confidence) and 70 hot-spot segments (40 at 99%). Pedestrian KAB hot spots (82 intersections, 40 of them at 99%) are more extensive than the all-crash hot spots, which is consistent with the stronger land-use signal for pedestrian crashes reported in §6."),
    ...figure("map_gi_int_ALL_KAB.png", "Gi* hot and cold spots — KAB crashes, intersections.", 6.3),
    ...figure("map_gi_seg_ALL_KAB.png", "Gi* hot and cold spots — KAB crashes, segments.", 6.3),
    ...figure("map_gi_int_PED_KAB.png", "Gi* hot and cold spots — pedestrian KAB crashes, intersections.", 6.3),
    H2("4.5  Fatal crashes: local join counts"),
    P("Because most sites have zero or one fatal crash, the fatal outcome was analysed as a binary variable with the local join count statistic (Anselin & Li, 2019), available in GeoDa. Fatal crashes are dispersed: only 1 intersection and 6 segments are significant fatal clusters. **Pedestrian KSI crashes do cluster** — 9 intersections and 26 segments sit in significant clusters — so for the most severe outcomes the spatial concentration comes from pedestrian crashes."),
    ...figure("map_ljc_seg_fatal.png", "Local join count — segments with a fatal crash whose neighbours also had fatal crashes.", 6.3),
    H2("4.6  Crash-type hot spots by corridor"),
    P(`Summarising the Gi* results by corridor (${F("fig10_hotspot_share_corridor.png")}) shows that each corridor has its own crash-type signature. Colonial Drive intersections are hot spots for rear-end (52% of sites) and all KAB crashes (48%). Lake Worth Road is a hot spot for alcohol-involved crashes (79% of intersections, 58% of segments). Oakland Park Boulevard is a hot spot for single-vehicle crashes (70% of intersections). Sunrise Boulevard is a hot spot for pedestrian crashes (44% of intersections) and all KAB crashes on segments (59%). US 19 is a hot spot for bicycle crashes (39% of intersections). These signatures point to corridor-specific land-use mixes, which §5 and §6 examine directly.`),
    ...figure("fig10_hotspot_share_corridor.png", "Share of each corridor's sites that are Gi* hot spots (≥90% confidence) for each crash type (KAB rates)."),
    H2("4.7  Spatial co-location of each land use with crash risk"),
    P(`Bivariate Moran's I measures whether sites with more of a land use are surrounded by sites with higher crash rates. Run for every land use against every crash type (${F("fig11_bivariate_moran_KAB.png")}; other severities in Appendix C), it shows the strongest positive co-location on segments for **supermarkets** (significant for 9 crash types, e.g., angle I = 0.19), **community shopping centers** (8 types, angle I = 0.19) and **gas stations** (alcohol-involved I = 0.19, single-vehicle 0.16, run-off-road 0.14). At intersections, **auto sales & service** co-locates most often with elevated crash rates (6 types, strongest for pedestrian crashes, I = 0.12). Appendix B maps the bivariate LISA for every land use.`),
    ...figure("fig11_bivariate_moran_KAB.png", "Bivariate Moran's I between each land use and the spatial lag of each crash type's KAB rate.", 6.5),
  ];
}

// ------------------------------------------------------------------ 5 typology
function typologySection() {
  return [
    H1("5  Land-use contexts: a corridor typology"),
    P("To move from 19 individual land uses to planning-relevant contexts, the counts were grouped into seven functional families (auto-oriented; food & drink; retail anchors; small retail & services; office, lodging & mixed use; civic & recreation; industrial) and clustered with K-means on standardised log counts (per site at intersections, per mile on segments). This is the GeoDa *Clusters › K Means* or ArcGIS *Multivariate Clustering* workflow. Five clusters gave interpretable contexts; the pseudo-F and silhouette statistics for k = 3–8 are in the Excel workbook."),
    ...figure("fig12_typology_profiles.png", "Land-use profile of each context. Colours are cluster-mean z-scores; labels are mean establishments per site (intersections) or per mile (segments)."),
    ...table("Land-use contexts and their crash rates (intersections per million entering vehicles; segments per 100 million VMT).",
      ["Facility", "Context", "n", "Defining land-use families", "Total rate", "KAB rate", "KSI rate", "Ped. KSI rate"],
      DATA.tab_typology, [1150, 1900, 450, 2360, 900, 850, 850, 900], { size: 15, leftCols: [1, 3] }),
    P("Shopping-center / big-box contexts have the highest crash rates at every severity. At intersections, the total crash rate is 2.5 per million entering vehicles, compared with 1.2 at low-intensity frontage; the KSI rate is 0.045 against 0.025; and the pedestrian KSI rate is 8 times higher. The segment pattern is the same (347 against 178 crashes per 100 MVMT; pedestrian KSI 2.2 against 0.6)."),
    ...figure("map_typology_int.png", "Land-use context typology — intersections.", 6.3),
    ...figure("map_typology_seg.png", "Land-use context typology — segments.", 6.3),
    H2("5.1  Adjusted crash-type profiles of each context"),
    P("Count models with the same controls, fixed effects and spatial filters as §6, with the context as the explanatory variable (reference = low-intensity frontage), confirm that the differences are not explained by traffic volume or design. At intersections, shopping-center / big-box contexts have 1.43 times the total crashes, 1.99 times the angle crashes and 1.91 times the right-turn crashes of low-intensity frontage. Their pedestrian crashes are 2.8 times higher (Total), 2.4 times (KAB) and 6.7 times (KSI). Every non-residential context has 5.6–6.7 times the pedestrian KSI incidence. On segments, shopping-center contexts have 7.0 times the single-vehicle KSI crashes and 4.1 times the pedestrian fatal crashes, and industrial/auto-oriented and civic contexts also have elevated pedestrian fatality incidence (IRR 3.7 each). Office / lodging / mixed-use segments have *fewer* run-off-road KAB crashes (IRR 0.43), plausibly reflecting lower operating speeds."),
    ...figure("fig13_typology_irr_int.png", "Adjusted incidence rate ratios of each context relative to low-intensity frontage — intersections (p < 0.05 shown)."),
    ...figure("fig13_typology_irr_seg.png", "Adjusted incidence rate ratios of each context relative to low-intensity frontage — segments (p < 0.05 shown)."),
  ];
}

// ------------------------------------------------------------------ 6 models
function modelSection() {
  return [
    H1("6  Which land uses exacerbate which crash types? Count models"),
    H2("6.1  How to read the heat maps"),
    P(`${F("fig14_irr_single_TOT.png")}–${F("fig14_irr_single_FAT.png").replace("Figure ", "")} show one cell per land use × crash type. Each cell is a separate model containing all controls, fixed effects and spatial eigenvectors plus that single land use. Red cells mean more crashes per additional establishment (IRR > 1); blue cells mean fewer. Only associations with p < 0.05 are coloured and labelled, and **boxed bold cells remain significant after false-discovery-rate correction** (q < 0.10). These are the most robust findings. Pale grey cells were not modelled (fewer than 20 crashes, or the land use present at fewer than 5 sites). The number of crashes in each outcome is shown in brackets under each column.`),
    H2("6.2  Total crashes"),
    P("At the Total level, **gas stations, community shopping centers, single-tenant retail, banks and fast-food restaurants** are associated with more crashes across many types. Each additional gas station at an intersection is associated with 17% more total crashes (IRR 1.17, 95% CI 1.06–1.29), 35% more angle crashes and 31% more right-turn crashes. Each additional community shopping center is associated with 26% more angle crashes, 21% more left-turn crashes and 45% more pedestrian crashes. Banks are associated specifically with **turning** crashes (right-turn IRR 1.23; left-turn 1.16 at intersections; 1.23–1.26 on segments), consistent with drive-through and driveway access. Industrial frontage is associated with fewer total and rear-end crashes (IRR 0.90 and 0.87)."),
    ...figure("fig14_irr_single_TOT.png", "Land use × crash type IRRs — Total crashes (one land use per model)."),
    H2("6.3  KAB (injury) crashes"),
    P("At the KAB level the land-use signal narrows. Pedestrian injury crashes are elevated with gas stations (IRR 1.47), community shopping centers (1.43) and hotels (1.83) at intersections. On segments, **supermarkets** are associated with injury crashes of many types: right-turn (IRR 2.26), rollover (2.38), sideswipe (1.45), left-turn (1.35) and pedestrian (1.33). Sit-down restaurants are associated with fewer left-turn injury crashes at intersections (IRR 0.68)."),
    ...figure("fig14_irr_single_KAB.png", "Land use × crash type IRRs — KAB crashes."),
    H2("6.4  KSI (killed or seriously injured) crashes"),
    P("At the KSI level, the strongest and most FDR-robust associations involve **pedestrians**. Pedestrian KSI crashes are elevated with gas stations at intersections (IRR 1.78, CI 1.39–2.27) and on segments (1.75), supermarkets on segments (1.47), hotels on segments (1.26 per hotel) and auto sales & service on segments (1.10 per outlet). Gas stations are also associated with severe angle crashes at intersections (1.61). Fast-food restaurants are associated with severe run-off-road (1.48), single-vehicle (1.60), bicycle (1.58) and pedestrian (1.28) crashes. Office buildings are associated with fewer KSI crashes (IRR 0.68 per 10 buildings at intersections; 0.88 on segments)."),
    ...figure("fig14_irr_single_KSI.png", "Land use × crash type IRRs — KSI crashes."),
    H2("6.5  Fatal crashes"),
    P("Fatal outcomes could be modelled for all crash types combined and for left-turn, pedestrian, run-off-road (segments) and alcohol-involved crashes (segments). Using Firth-penalised estimation: **fast-food restaurants** at intersections are associated with more fatal crashes (IRR 1.53, CI 1.20–1.96) and more fatal pedestrian crashes (1.75). **Single-tenant retail** is associated with more fatal crashes (1.20 per store). **Auto sales & service** on segments is associated with more fatal crashes (1.12 per outlet, q < 0.001), fatal pedestrian crashes (1.18) and fatal left-turn crashes (1.14). **Gas stations** (fatal pedestrian 1.97 on segments), **hotels** (1.36) and **supermarkets** (1.54) complete the picture."),
    ...figure("fig14_irr_single_FAT.png", "Land use × crash type IRRs — Fatal crashes (Firth-penalised Poisson)."),
    H2("6.6  Land-use risk profiles"),
    P(`${F("fig15_landuse_risk_profile.png")} counts, for each land use, the crash-type outcomes with significantly higher (right) or lower (left) incidence, stacked by severity. ${T("exacerbation")} lists the crash types. Gas stations, single-tenant retail, community shopping centers and fast food (intersections) and auto sales & service and supermarkets (segments) have the broadest and most severe risk profiles. Office, industrial and sit-down restaurant land uses lean protective.`),
    ...figure("fig15_landuse_risk_profile.png", "Number of crash-type outcomes with significantly higher (solid, right) or lower (faded, left) incidence for each land use, by severity."),
    ...table("Crash types with significantly higher incidence (IRR > 1, p < 0.05) for each land use. I = intersections, S = segments; ALL = all crash types combined; * also significant after FDR correction (q < 0.10).",
      ["Land use", "Total", "KAB", "KSI", "Fatal"], DATA.tab_exacerbation, [1700, 2450, 1950, 1700, 1560],
      { size: 13, leftCols: [1, 2, 3, 4], label: "exacerbation" }),
    H2("6.7  Joint models: all land uses together"),
    P(`When all land uses enter together (${F("fig16_joint_forest_all.png")}, ${T("joint")}), the core findings persist. At intersections, gas stations and community shopping centers remain associated with more total, KAB and KSI crashes (IRRs 1.13–1.18), and fast food with more fatal crashes (1.47). On segments, auto sales & service is significant at every severity level (IRR 1.04–1.08), and supermarkets for Total (1.13), KAB (1.15) and fatal crashes (1.41). The joint models also show that offices and industrial frontage are associated with fewer severe crashes when the other land uses are held constant.`),
    P(`**Robustness to corridor design.** If corridor-wide design standards (cross-section, signal spacing, access policy) drove both land use and crashes, the land-use effects would shrink once each corridor is compared only with itself. Replacing county fixed effects with corridor (route) fixed effects, or dropping the spatial filter, leaves the main associations essentially unchanged (${T("robust")} in Appendix A). Examples: community shopping centers and all KSI crashes at intersections, 1.18 (county effects) against 1.15 (corridor effects); gas stations and pedestrian KAB crashes, 1.46 against 1.41; hotels and pedestrian KAB crashes, 1.89 against 1.90; auto sales & service and all KSI crashes on segments, 1.08 against 1.07.`),
    ...figure("fig16_joint_forest_all.png", "Joint-model IRRs (95% CI) of each land use for all crash types, by severity."),
    ...table("Joint-model IRRs for all crash types combined (* p < 0.05, ** p < 0.01; –, land use too rare to include).",
      [[{ text: "Land use" }, { text: "Intersections", span: 4 }, { text: "Segments", span: 4 }],
        ["", "Total", "KAB", "KSI", "Fatal", "Total", "KAB", "KSI", "Fatal"]],
      DATA.tab_joint_all, [2560, 850, 850, 850, 850, 850, 850, 850, 850], { size: 15, label: "joint" }),
    H2("6.8  Does land use add explanatory power beyond design?"),
    P(`${F("fig17_landuse_value_added.png")} compares each joint model with its design-only counterpart. Land use improves the fit (positive ΔAIC and significant likelihood-ratio test) for **Total crashes of most types** (all crashes +28 AIC points at intersections and +28 on segments; angle, right-turn, rear-end and sideswipe crashes), for **pedestrian crashes** (intersections: Total +33, KAB +24, KSI +14; segments KSI +36) and for **fatal crashes** (segments +27). For vehicle-only KAB and KSI outcomes, adding all 19 land uses at once is penalised by AIC even when individual land uses are significant. For those outcomes the evidence comes from specific land uses rather than from land use as a block.`),
    ...figure("fig17_landuse_value_added.png", "Improvement in model fit from adding land use to the design-only model: ΔAIC (top) and gain in McFadden pseudo-R² (bottom)."),
    P(`${T("controls")} reports the design and context controls from the joint models for all crash types. Exposure dominates (ln AADT, cross-street AADT, segment length). Among design variables, wider outside shoulders at intersections are associated with more total crashes (IRR 1.20 per 10 ft), bike-lane corridors with fewer total crashes (0.85), and higher posted speed on segments with fewer crashes per VMT (0.78 per 10 mph), reflecting less-urban, lower-conflict segments. Lanes and median type are not significant once land use and exposure are controlled.`),
    ...table("Design and context controls in the joint models, all crash types (IRR; * p < 0.05, ** p < 0.01).",
      [[{ text: "Variable" }, { text: "Intersections", span: 4 }, { text: "Segments", span: 4 }],
        ["", "Total", "KAB", "KSI", "Fatal", "Total", "KAB", "KSI", "Fatal"]],
      DATA.tab_joint_controls, [2560, 850, 850, 850, 850, 850, 850, 850, 850],
      { size: 15, label: "controls", note: "Fatal models use the reduced control set (ln AADT, lanes, speed, ln length) and metro-region fixed effects. County fixed effects are omitted from the table." }),
    H2("6.9  Spatial diagnostics"),
    P(`Before filtering, residual Moran's I reached 0.28 (segments, all KAB crashes). Adding up to 10 Moran eigenvectors brought residual autocorrelation to 0.10 or below for every outcome, and to non-significant levels for most (${F("fig18_residual_moran_esf.png")}; ${T("diag")} in Appendix A). Because the eigenvectors are chosen per outcome and held fixed across the 19 land-use models, land-use effects are not inflated by unmodelled spatial clustering.`),
    ...figure("fig18_residual_moran_esf.png", "Residual Moran's I before and after eigenvector spatial filtering, for outcomes where filtering was applied (number of eigenvectors at right)."),
  ];
}

// ------------------------------------------------------------------ 7 MGWR
function mgwrSection() {
  const out = [H1("7  Do land-use effects vary across the region? MGWR")];
  out.push(P("MGWR (Fotheringham et al., 2017) fits a separate local regression at every site but lets each covariate choose its own spatial scale (bandwidth). A bandwidth close to the number of sites means the effect is **global**, the same everywhere. A small bandwidth means it is **local**. The outcome is the standardised ln(EB rate). Covariates are lanes, posted speed (and intersections per mile on segments) plus every land use present at at least 10% of sites. Local significance uses the multiple-testing-corrected critical t of da Silva & Fotheringham (2016)."));
  out.push(...(S_MGWR_TEXT()));
  out.push(...figure("fig19_mgwr_bandwidths.png", "MGWR bandwidths (as % of sites) for each covariate and outcome. Values near 100% indicate a global (stationary) effect."));
  if (DATA.tab_mgwr) {
    out.push(...table("MGWR results for all KAB crashes: bandwidth (number of neighbours and % of sites), median [min, max] local standardised coefficient, and % of sites with a significant positive / negative local effect.",
      [[{ text: "Covariate" }, { text: "Intersections", span: 3 }, { text: "Segments", span: 3 }],
        ["", "Bandwidth", "Local coef. median [range]", "% sig + / –", "Bandwidth", "Local coef. median [range]", "% sig + / –"]],
      DATA.tab_mgwr, [2160, 1000, 1700, 700, 1000, 1700, 700], { size: 14, label: "mgwr" }));
    out.push(...table("Model fit: global OLS vs GWR vs MGWR (standardised ln EB rate).",
      ["Facility", "Outcome", "R² OLS", "AICc OLS", "R² GWR", "AICc GWR", "R² MGWR", "AICc MGWR"],
      DATA.tab_mgwr_fit, [1300, 1800, 780, 900, 780, 900, 800, 1080], { size: 15, label: "mgwrfit" }));
  }
  for (const f of ["int", "seg"]) {
    out.push(...figure(`fig20_mgwr_intercept_${f}.png`, `MGWR local intercept for KAB crashes — ${f === "int" ? "intersections" : "segments"}. Red areas have higher baseline risk than the covariates explain.`, 6.3));
  }
  const fs = require("fs");
  const path = require("path");
  const extra = fs.readdirSync(H.FIG).filter((n) => n.startsWith("fig21_mgwr_")).sort();
  for (const n of extra) {
    const fac = n.includes("_int_") ? "intersections" : "segments";
    const lu = n.replace(/fig21_mgwr_(int|seg)_/, "").replace(".png", "");
    const name = (LU_ORDER.find((x) => x[0] === lu) || [lu, lu])[1];
    out.push(...figure(n, `MGWR local effect of ${name.toLowerCase()} on the KAB crash rate — ${fac}.`, 6.3));
  }
  return out;
}
let S_MGWR_TEXT = () => [
  P(`**Fit.** MGWR fits much better than both a global model and single-bandwidth GWR (${T("mgwrfit")}). For all KAB crashes, R² rises from 0.16 (OLS) and 0.28 (GWR) to 0.49 at intersections, and from 0.26 and 0.37 to 0.62 on segments, with correspondingly lower AICc. Most of the gain comes from the **local intercept** (bandwidth 44 sites for Total crashes at intersections and for Total, KAB and KSI crashes on segments). Baseline risk varies from one corridor section to the next in ways the covariates do not capture. This is the same structure that the Moran eigenvectors absorb in the count models.`),
  P("**Land-use effects are mostly global.** Of the 44 land-use slopes estimated at intersections (11 land uses × 4 outcomes), 33 have a bandwidth of at least 90% of sites, which means one coefficient applies to every metro area. Nine are regional (25–90%) and only two are local (under 25%). On segments, 45 of 60 slopes are global, 14 regional and one local. This supports pooling the three metro areas in the count models."),
  ...bullets([
    "For KAB crashes at intersections, the community-shopping-center effect is positive at every site (local standardised coefficients 0.03–0.27) and significant at 67% of sites. The fast-food effect is global and significant at 56% of sites. The sit-down-restaurant effect is negative and significant at 44% of sites.",
    "On segments, supermarkets have a global positive effect (significant at 40% of sites) and office buildings a global negative effect (31% of sites).",
    "The regional or local slopes are for gas stations (intersection KAB; segment Total and KAB), community shopping centers (segment Total; intersection pedestrian KAB), fast food (intersection pedestrian KAB) and schools (segment Total). Posted speed is also local at intersections.",
    "**Caution:** the local gas-station coefficients at intersections are unstable. Some local windows contain almost no gas stations, so the estimates range from −27.9 to 1.3, and only 7% of sites are locally significant. Treat that surface as inconclusive and rely on the global count-model estimate for gas stations.",
  ]),
];

// ------------------------------------------------------------------ 8 synthesis
function synthesisSection() {
  return [
    H1("8  Synthesis: land use by land use"),
    P("Combining the ESDA, typology and model evidence, the land uses fall into four groups. The Land-Use Atlas (Appendix B) gives the full crash-type × severity profile and bivariate LISA map for each land use."),
    H3("Consistent risk-exacerbating land uses"),
    ...bullets([
      "**Gas stations** — the most consistent land use across both facilities and all severities. Associated with more angle, turning, sideswipe and pedestrian crashes; pedestrian KSI (1.75–1.78) and pedestrian fatal (1.64–1.97) incidence are elevated at intersections and on segments. The mechanism is likely multiple wide driveways, frequent turning, and pedestrians walking to convenience stores.",
      "**Community shopping centers** — angle, left-turn and right-turn crashes (IRR 1.21–1.26 at intersections), pedestrian crashes (1.43–1.45), KSI crashes of all types (1.20) and fatal left-turn crashes (1.78). Robust in the joint models.",
      "**Fast-food restaurants** — a severity story: modest effects on Total crashes, but strong associations with fatal (1.53) and pedestrian fatal (1.75) crashes and severe run-off-road, single-vehicle and bicycle crashes at intersections.",
      "**Auto sales & service** — on segments, significant at every severity level in the joint model, with the most robust fatal associations (all fatal 1.12, pedestrian fatal 1.18, both q < 0.01). This is a per-outlet effect, and these uses often cluster in long auto-oriented strips.",
      "**Supermarkets** (segments) — injury crashes of many types and pedestrian KSI and fatal crashes. Co-location is strongest for angle and left-turn crashes (bivariate Moran).",
      "**Single-tenant retail** — small per-store effects (≈ +5–10% per store) that add up along strip frontage, including fatal crashes (1.20 per store at intersections).",
    ]),
    H3("Pedestrian-specific land uses"),
    ...bullets([
      "**Hotels** — pedestrian crashes at every severity (intersections Total 1.74, KAB 1.83; segments KSI 1.26, fatal 1.36).",
      "**Mixed-use buildings** — fatal and pedestrian fatal crashes on segments (per 10 buildings: 2.00 and 2.28), but estimates are imprecise.",
    ]),
    H3("Access-related, lower-severity land uses"),
    ...bullets([
      "**Banks** — turning crashes (left- and right-turn Total 1.16–1.26) without a severity signal.",
      "**Department / big-box stores** — right-turn and bicycle crashes (intersections) and rear-end KSI (segments); rare land use, wide intervals.",
    ]),
    H3("Protective or neutral land uses"),
    ...bullets([
      "**Office buildings** — fewer KSI crashes (0.68 per 10 at intersections; 0.88 on segments) and fewer run-off-road crashes, consistent with lower-speed employment areas.",
      "**Industrial frontage** — fewer total and rear-end crashes, perhaps reflecting fewer driveways per mile and lower traffic turnover.",
      "**Sit-down restaurants, schools, parks** — fewer severe left-turn / angle crashes (restaurants) and head-on crashes (schools); parks show no consistent association.",
      "**Regional shopping centers, bars, repair shops, hospitals** — too rare in this sample for reliable inference (flagged †).",
    ]),
    P("**Implication.** The land uses associated with severe outcomes attract short, frequent, turning-intensive trips and pedestrian activity on high-volume arterials: fuel, fast food, convenience retail, auto services and hotels. Safe-System countermeasures could be targeted by land-use context: access management and driveway consolidation at gas stations and shopping centers; protected pedestrian crossings and speed management near hotels, supermarkets and fast food; and treatments for severe run-off-road and single-vehicle crashes on fast-food and auto-oriented strips."),
  ];
}

// ------------------------------------------------------------------ 9 software workflows
function softwareSection() {
  const files = [
    ["outputs/gis/crash_landuse_spatial.gpkg", "GeoPackage (EPSG:26917) with intersections_points, intersections_lines, segments_points, segments_lines and florida_counties. Every site carries the 52 crash counts (13 types × 4 severities), the 19 land uses, controls, exposure, EB rates, LISA/Gi*/join-count classes, bivariate-LISA classes for each land use, the typology and MGWR local coefficients."],
    ["outputs/gis/*_knn6.gal", "GeoDa weights files (k = 6, ID = SEGMENTID) — load in Weights Manager."],
    ["outputs/gis/*_points_with_results.csv", "The same attributes as CSV with a WKT point column."],
    ["outputs/gis/data_dictionary.csv", "Field descriptions."],
    ["outputs/tables/crash_landuse_results.xlsx", "Every estimate: 1,440 one-land-use-at-a-time IRRs, joint models, controls, diagnostics, typology, ESDA and MGWR tables."],
    ["scripts/01_… to 11_….py", "Reproducible Python pipeline (descriptive, ESDA, typology, count models, MGWR, export)."],
  ];
  const geoda = [
    ["1", "File › Open › crash_landuse_spatial.gpkg (layer intersections_points)", "Use the point layers in GeoDa; repeat everything for segments_points."],
    ["2", "Tools › Weights Manager › Create › Distance Weight › k-Nearest neighbors", "ID = SEGMENTID, k = 6 (or Load intersections_knn6.gal). Sensitivity: k = 4, 8."],
    ["3", "Space › Moran's I with EB Rate", "Event = y_<TYPE>_<SEV> (e.g. y_PED_KSI); Base = exposure; Randomization 999."],
    ["4", "Space › Spatial Correlogram", "Variable = eb_ALL_KAB; distance bins up to 10 km to find the clustering scale."],
    ["5", "Space › Local Moran's I with EB Rate", "Cluster + significance maps; Significance filter 0.05 (optionally FDR); 999 permutations; Save results."],
    ["6", "Space › Local G*", "Variable = eb_ALL_KAB or eb_PED_KAB; hot/cold spots."],
    ["7", "Table › Calculator: fatal_any = y_ALL_FAT > 0; then Space › Univariate Local Join Count", "Rare binary outcomes (fatal, pedestrian KSI)."],
    ["8", "Space › Bivariate Moran's I and Bivariate Local Moran's I", "X = LU_<land use> (count), Y = EB rate of a crash type. Repeat for each of the 19 land uses."],
    ["9", "Clusters › K Means (or SKATER / REDCAP for contiguous corridor zones)", "Variables = the 7 land-use family indices (log, standardise = Z); k = 5; inspect between/total SS; Save cluster; Map › Unique Values."],
    ["10", "Regression › Classic (with weights) → Spatial Lag / Spatial Error", "Y = ln(eb_ALL_KAB); use the LM-Lag / LM-Error diagnostics to choose a spatial specification. GeoDa cannot fit count models, so use it for diagnostics only."],
  ];
  const arc = [
    ["1", "Map › Add Data › crash_landuse_spatial.gpkg; then Feature Class To Geodatabase", "Coordinate system NAD 1983 UTM Zone 17N (WKID 26917)."],
    ["2", "Spatial Statistics › Generate Spatial Weights Matrix", "Conceptualization = K nearest neighbors, 6; Row standardization → .swm."],
    ["3", "Spatial Statistics › Incremental Spatial Autocorrelation", "Field = eb_ALL_KAB; start 1,000 m, increment 1,000 m, 10 distances; the peak (≈6–8 km) is the Gi* distance."],
    ["4", "Spatial Autocorrelation (Global Moran's I)", "Run on eb_<TYPE>_<SEV> fields with the .swm file."],
    ["5", "Hot Spot Analysis (Getis-Ord Gi*)", "Input field = eb_ALL_KAB, eb_PED_KAB …; K nearest neighbors (6) or fixed distance at the incremental peak; Apply False Discovery Rate correction = checked."],
    ["6", "Cluster and Outlier Analysis (Anselin Local Moran's I)", "Same fields; 999 permutations; FDR checked. Map the COType field (HH, LL, HL, LH)."],
    ["7", "Multivariate Clustering", "Analysis fields = land-use family indices; Clustering method = K means; number of clusters blank to get the pseudo-F chart, then 5."],
    ["8", "Local Bivariate Relationships", "Dependent = eb rate of a crash type; explanatory = one land use; repeat per land use to map positive/negative/complex local relationships."],
    ["9", "Generalized Linear Regression (Model type = Count)", "Poisson only, with no over-dispersion term. Use for quick screening and residual mapping, not inference."],
    ["10", "Multiscale Geographically Weighted Regression", "Model type = Continuous; dependent = ln(eb_ALL_KAB); explanatory = lanes, speed, land uses with ≥10% prevalence; Neighborhood = Number of neighbors, Golden search; Scale data = checked."],
    ["11", "Python Notebook (Analysis › Python › New Notebook)", "Run scripts/04_models.py for the NB2 / Firth models (install statsmodels via Package Manager)."],
  ];
  const qgis = [
    ["1", "Layer › Add Layer › Add Delimited Text Layer", "File = Intersections CSV; Geometry definition = Well known text (WKT); field = geometry; CRS = EPSG:26917. (Or simply open the GeoPackage.)"],
    ["2", "Processing › Vector geometry › Centroids (or Points along geometry)", "Mid-points of intersection influence lines and segments for point-based statistics."],
    ["3", "Field Calculator", "exposure = \"RN_AADT_AVG\"*365*4/1e6 (intersections) or *\"SEGLENGTH\"/1e8 (segments); crude rate = y_ALL_KSI / exposure. EB rates are pre-computed in eb_ fields."],
    ["4", "Plugins › Hotspot Analysis (requires PySAL)", "Gi* and Local Moran on eb_ fields; k-NN or distance-band weights matching the 6–8 km scale."],
    ["5", "Symbology › Categorized", "Style lisa_*, gi_*, typology and bvlisa_* fields with the colour conventions used in this report (HH red, LL blue, HL orange, LH light blue, n.s. grey)."],
    ["6", "Processing › Network analysis › Service area (from layer) + Join attributes by location (summary)", "To rebuild land-use counts in network buffers (e.g., 0.25 mi) from a business / parcel point layer."],
    ["7", "Plugins › Processing R Provider, or Python Console", "Run MASS::glm.nb / statsmodels NB2 models (scripts supplied); core K-means in QGIS clusters by location only, so use sklearn for attribute clustering."],
    ["8", "Project › New Print Layout (Atlas)", "Map, legend, scale bar, north arrow; use Atlas to page through corridors or counties."],
  ];
  return [
    H1("9  Running the analysis in GeoDa, ArcGIS Pro and QGIS"),
    H2("9.1  Files supplied"),
    ...table("Files supplied with this report.", ["File", "Contents"], files, [3000, 6360], { size: 15, leftCols: [1] }),
    H2("9.2  GeoDa (1.22) — exploratory spatial data analysis"),
    ...table("GeoDa steps.", ["#", "Menu path", "Settings for these data"], geoda, [400, 3900, 5060], { size: 15, leftCols: [1, 2] }),
    H2("9.3  ArcGIS Pro (3.x) — hot spots, clustering and MGWR"),
    ...table("ArcGIS Pro steps (Spatial Statistics toolbox unless noted).", ["#", "Tool", "Settings for these data"], arc, [400, 3500, 5460], { size: 15, leftCols: [1, 2] }),
    H2("9.4  QGIS (3.34 LTR or later) — preparation and cartography"),
    ...table("QGIS steps.", ["#", "Menu path / tool", "Settings for these data"], qgis, [400, 3500, 5460], { size: 15, leftCols: [1, 2] }),
    H2("9.5  R / Python for the count models"),
    P("The count models are the one component that must run outside the GIS. In R, the equivalent of the supplied Python pipeline is MASS::glm.nb for NB2, logistf-style penalisation (e.g., the brglm2 package for Poisson bias reduction) for sparse outcomes, spdep::SpatialFiltering or spatialreg::ME for eigenvector spatial filtering, and p.adjust(method = \"BH\") for FDR. Results can be joined back to the GeoPackage on SEGMENTID for mapping in QGIS or ArcGIS."),
  ];
}

// ------------------------------------------------------------------ 10 limitations
function limitsSection() {
  return [
    H1("10  Limitations and next steps"),
    H2("10.1  Limitations"),
    ...bullets([
      "**Cross-sectional associations, not causal effects.** Land uses locate where traffic and pedestrians already are. Exposure controls, fixed effects and spatial filters reduce but cannot remove this confounding. Pedestrian volumes in particular are unobserved.",
      "**Land-use measurement.** Counts are within the site's influence area. Effects may operate at larger distances (e.g., the 6–8 km clustering scale), and counts do not capture driveway numbers or building size.",
      "**Sparse fatal outcomes.** Fatal models are limited to all crashes and a few crash types. Firth estimates are less biased but have wide intervals; FDR-significant fatal results (auto sales & service, fast food, hotels) are the most credible.",
      "**Multiple testing.** 1,440 one-land-use-at-a-time associations were estimated, so about 5% of the p < 0.05 cells are expected by chance. Use the boxed (FDR) cells and patterns that repeat across severities and facilities.",
      "**Four-year period, ten corridors.** Results describe principal arterials in six Florida counties and may not transfer to other road classes.",
    ]),
    H2("10.2  More sophisticated next steps"),
    ...bullets([
      "**Multivariate Bayesian count model.** Model all crash types × severities jointly (multivariate Poisson-lognormal) with correlated site random effects and a CAR/BYM2 spatial term, e.g., in R-INLA, brms or Stan. This borrows strength across crash types and makes fatal-by-type estimates possible through partial pooling.",
      "**Random-parameters negative binomial** to let land-use effects vary across sites (unobserved heterogeneity), complementing MGWR.",
      "**Crash-level and business-level point data** would enable network kernel density, colocation quotients (ArcGIS Colocation Analysis) and distance-decay land-use buffers (e.g., 250 ft, 0.25 mi, 0.5 mi) built with network service areas.",
      "**Driveway and access-point inventories** to test whether the gas-station, fast-food and shopping-center effects operate through access density.",
      "**Space-time analysis** (Emerging Hot Spot Analysis) once crash dates are attached.",
    ]),
    H1("References"),
    ...[
      "Anselin, L. (1995). Local indicators of spatial association—LISA. *Geographical Analysis*, 27(2), 93–115.",
      "Anselin, L., & Li, X. (2019). Operational local join count statistics for cluster detection. *Journal of Geographical Systems*, 21(2), 189–210.",
      "Assunção, R. M., & Reis, E. A. (1999). A new proposal to adjust Moran's I for population density. *Statistics in Medicine*, 18(16), 2147–2162.",
      "Benjamini, Y., & Hochberg, Y. (1995). Controlling the false discovery rate: a practical and powerful approach to multiple testing. *Journal of the Royal Statistical Society B*, 57(1), 289–300.",
      "da Silva, A. R., & Fotheringham, A. S. (2016). The multiple testing issue in geographically weighted regression. *Geographical Analysis*, 48(3), 233–247.",
      "Dumbaugh, E., & Rae, R. (2009). Safe urban form: revisiting the relationship between community design and traffic safety. *Journal of the American Planning Association*, 75(3), 309–329.",
      "Dumbaugh, E., & Li, W. (2011). Designing for the safety of pedestrians, cyclists, and motorists in urban environments. *Journal of the American Planning Association*, 77(1), 69–88.",
      "Firth, D. (1993). Bias reduction of maximum likelihood estimates. *Biometrika*, 80(1), 27–38.",
      "Fotheringham, A. S., Yang, W., & Kang, W. (2017). Multiscale geographically weighted regression (MGWR). *Annals of the American Association of Geographers*, 107(6), 1247–1265.",
      "Getis, A., & Ord, J. K. (1992). The analysis of spatial association by use of distance statistics. *Geographical Analysis*, 24(3), 189–206.",
      "Griffith, D. A. (2003). *Spatial Autocorrelation and Spatial Filtering*. Springer.",
      "Lord, D., & Mannering, F. (2010). The statistical analysis of crash-frequency data: a review and assessment of methodological alternatives. *Transportation Research Part A*, 44(5), 291–305.",
      "Okabe, A., & Sugihara, K. (2012). *Spatial Analysis Along Networks*. Wiley.",
    ].map((t) => P(t, { run: { size: 19 } })),
  ];
}

// ------------------------------------------------------------------ appendices
function appendixTables() {
  const out = [H1nb("Appendix A  Full model tables")];
  out.push(P("IRR per additional establishment (per 10 for mixed-use and office buildings) from the one-land-use-at-a-time models. * p < 0.05, ** p < 0.01; n/a = land use present at fewer than 5 sites. Confidence intervals, q-values and estimator details for every cell are in the Excel workbook (sheet IRR_each_LU_single)."));
  const sevLab = { TOT: "Total", KAB: "KAB", KSI: "KSI", FAT: "Fatal" };
  for (const f of ["int", "seg"]) {
    for (const s of ["TOT", "KAB", "KSI", "FAT"]) {
      const t = DATA[`tab_single_${f}_${s}`];
      if (!t || !t.header.length) continue;
      const n = t.header.length;
      const first = 1900;
      const w = Math.floor((13680 - first) / n);
      const widths = [first, ...Array(n).fill(w)];
      out.push(...table(`${f === "int" ? "Intersections" : "Segments"} — ${sevLab[s]} crashes: IRR of each land use for each crash type.`,
        ["Land use", ...t.header], t.rows, widths, { size: 14 }));
    }
  }
  out.push(...table("Model diagnostics for every estimated outcome: estimator, over-dispersion (NB2 α or quasi-Poisson φ), residual Moran's I before and after spatial filtering, and land-use block test (ΔAIC and LR p) from the joint model.",
    ["Fac.", "Crash type", "Severity", "Crashes", "Estimator", "α / φ", "Resid. I before", "# EVs", "Resid. I after", "ΔAIC (LU)", "p (LR, LU)"],
    DATA.tab_diag, [700, 1400, 1000, 1000, 1000, 900, 1500, 800, 1500, 1300, 1300], { size: 14, label: "diag" }));
  if (DATA.tab_robust) {
    const sub = ["County FE", "Corridor FE", "No ESF"];
    out.push(...table("Robustness of joint-model land-use IRRs: main specification (county fixed effects + spatial filter) vs corridor (route) fixed effects + spatial filter vs county fixed effects without spatial filter (* p < 0.05, ** p < 0.01).",
      [[{ text: "Land use" }, { text: "Intersections — All Total", span: 3 }, { text: "All KSI", span: 3 }, { text: "Ped. KAB", span: 3 },
        { text: "Segments — All Total", span: 3 }, { text: "All KSI", span: 3 }, { text: "Ped. KAB", span: 3 }],
       ["", ...sub, ...sub, ...sub, ...sub, ...sub, ...sub]],
      DATA.tab_robust, [2160, ...Array(18).fill(640)], { size: 13, label: "robust" }));
  }
  if (DATA.tab_mgwr_bw) {
    out.push(...table("MGWR bandwidths (number of neighbours) by covariate and outcome.",
      [[{ text: "Covariate" }, { text: "Intersections (n = 489)", span: 4 }, { text: "Segments (n = 334)", span: 4 }],
        ["", "All Total", "All KAB", "All KSI", "Ped KAB", "All Total", "All KAB", "All KSI", "Ped KAB"]],
      DATA.tab_mgwr_bw, [3280, 1300, 1300, 1300, 1300, 1300, 1300, 1300, 1300], { size: 15 }));
  }
  return out;
}

function appendixAtlas() {
  const out = [H1nb("Appendix B  Land-use atlas: every land use, every crash type, every severity")];
  out.push(P("For each land use, the upper figure shows the IRR (95% CI) for every crash type at the four severity levels from the one-land-use-at-a-time models (filled symbols p < 0.05). The lower map shows the bivariate LISA between the land-use count at each site and the KSI crash rate at neighbouring sites (GeoDa Bivariate Local Moran). High-High sites (red) have more of that land use and are surrounded by high KSI risk."));
  LU_ORDER.forEach(([lu, name], i) => {
    out.push(H2(name, i > 0));
    out.push(...figure(`atlas_forest_${lu}.png`, `${name}: incidence rate ratios by crash type and severity.`, 6.3, 3.25));
    out.push(...figure(`atlas_bvlisa_${lu}.png`, `${name}: bivariate LISA with the KSI crash rate (dots = intersections, lines = segments).`, 5.3, 3.6));
  });
  out.push(H1("Appendix C  Additional maps and figures"));
  const types = [["ANGLE", "angle"], ["LEFTTURN", "left-turn"], ["REAREND", "rear-end"], ["OFFROAD", "run-off-road"], ["PED", "pedestrian"], ["BIKE", "bicycle"], ["SIDESWIPE", "sideswipe"], ["SINGLE", "single-vehicle"]];
  out.push(H2("C.1  LISA cluster maps by crash type (KAB)"));
  for (const [t, lab] of types) {
    out.push(...figure(`map_lisa_int_${t}_KAB.png`, `LISA clusters — ${lab} KAB crashes, intersections.`, 5.8));
    out.push(...figure(`map_lisa_seg_${t}_KAB.png`, `LISA clusters — ${lab} KAB crashes, segments.`, 5.8));
  }
  out.push(H2("C.2  Additional hot-spot and join-count maps"));
  out.push(...figure("map_gi_int_ALL_KSI.png", "Gi* hot and cold spots — KSI crashes, intersections.", 5.8));
  out.push(...figure("map_gi_seg_ALL_KSI.png", "Gi* hot and cold spots — KSI crashes, segments.", 5.8));
  out.push(...figure("map_gi_seg_PED_KAB.png", "Gi* hot and cold spots — pedestrian KAB crashes, segments.", 5.8));
  out.push(...figure("map_ljc_int_fatal.png", "Local join count — intersections with fatal crashes.", 5.8));
  out.push(H2("C.3  Bivariate Moran's I for other severity levels"));
  for (const [s, lab] of [["TOT", "Total"], ["KSI", "KSI"], ["FAT", "Fatal"]]) {
    out.push(...figure(`fig11_bivariate_moran_${s}.png`, `Bivariate Moran's I between each land use and each crash type's ${lab} EB rate.`));
  }
  out.push(H2("C.4  Joint-model heat maps (all land uses entered together)"));
  for (const [s, lab] of [["TOT", "Total"], ["KAB", "KAB"], ["KSI", "KSI"], ["FAT", "Fatal"]]) {
    out.push(...figure(`figA_irr_joint_${s}.png`, `Joint-model IRRs — ${lab} crashes (coloured p < 0.05; boxed FDR q < 0.10; grey = joint model not estimated).`));
  }
  return out;
}

function main() {
  return [
    ...execSummary(), ...dataSection(), ...methodSection(), ...esdaSection(), ...typologySection(),
    ...modelSection(), ...mgwrSection(), ...synthesisSection(), ...softwareSection(), ...limitsSection(),
  ];
}

module.exports = { main, appendixTables, appendixAtlas, setMgwrText: (f) => { S_MGWR_TEXT = f; } };
