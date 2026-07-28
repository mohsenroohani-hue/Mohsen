"""
lexicons.py
===========
Controlled vocabularies and regular-expression families used as the coding
instrument for the systematic review:

    "Trajectories of Point-Based Spatial Analysis:
     A Global Systematic, Bibliometric, Methodological, and Theoretical
     Review, 2000-2027"

Every construct used in the manuscript that is derived from the corpus is
operationalised here, once, so that the coding is fully reproducible and
auditable. Nothing in this file is data; it is the *instrument*.

Design rules
------------
1. All patterns are matched case-insensitively against a normalised
   `Title + Abstract` string (author keywords are not present in the export).
2. Patterns use word boundaries and, where a term is polysemous, an explicit
   negative context list (see NEGATIVE_CONTEXT and the DISAMBIGUATION rules).
3. Categories are non-exclusive (a study may be coded to several methods,
   domains or data sources). Counts therefore sum to more than the corpus
   size and are always reported as "share of included studies".
"""

import re

# ---------------------------------------------------------------------------
# 0.  PERIODISATION
# ---------------------------------------------------------------------------
PERIODS = [
    ("P1", "2000-2010", 2000, 2010),
    ("P2", "2011-2020", 2011, 2020),
    ("P3", "2021-2027", 2021, 2027),
]


def period_of(year):
    for code, label, lo, hi in PERIODS:
        if lo <= year <= hi:
            return code, label
    return None, None


# ---------------------------------------------------------------------------
# 1.  ELIGIBILITY:  criterion A - point-referenced units of observation
# ---------------------------------------------------------------------------
# The defining feature of point-based spatial analysis is that the elementary
# unit of observation is a discrete, georeferenced location (an "event"),
# rather than an area, a pixel, or a network link.
CRITERION_A_POINT_UNITS = {
    "point_process_object": r"\bpoint (?:process(?:es)?|pattern(?:s)?|event(?:s)?|data(?:set)?s?|location(?:s)?|observation(?:s)?|configuration(?:s)?)\b",
    "spatial_point_term": r"\bspatial point\b|\bspatio-?temporal point\b|\bmarked point\b|\bpoint-referenced\b|\bpoint referenced\b|\bpoint-level\b|\bgeoreferenced point",
    "event_locations": r"\bevent (?:location|point|coordinate)s?\b|\blocation of (?:events|cases|incidents|crimes|fires|accidents|collisions)\b|\bincident location",
    "poi": r"\bpoints? of interest\b|\bPOIs?\b",
    "occurrence_records": r"\boccurrence (?:record|point|data|location)s?\b|\bpresence-only\b|\bpresence[- ]absence (?:point|record)",
    "case_locations": r"\bgeocoded\b|\bgeocoding\b|\bcase (?:location|residence|address)|\bresidential address(?:es)?\b|\bpatient address|\bclusters? of (?:cases|infections|parasites|individuals|events|deaths)\b",
    "sample_points": r"\bsampl(?:e|ing) (?:point|site|location|station)s?\b|\bmonitoring (?:station|site|point|well)s?\b|\bsurvey point|\bborehole|\bdrill-?hole|\bcore samples?\b|\bpermanent plots?\b|\bobservation (?:station|site|point)s?\b|\bgaug(?:e|ing) stations?\b|\bmeasur(?:ement|ing) points?\b|\bstation (?:density|network|data|observation)|\bnetwork of stations\b",
    "gps_points": r"\bGPS (?:point|track|trace|fix|location|coordinate)|\btrajectory point|\bcheck-?ins?\b|\bgeo-?tagged\b|\bgeotag",
    "coordinates": r"\bx-?y coordinates?\b|\blatitude and longitude\b|\bpoint coordinates?\b",
    "point_cloud": r"\bpoint clouds?\b",
    "tree_stem_plot": r"\bstem map|\bindividual tree (?:position|location|detection)|\btree location",
    "epicentre": r"\bepicent(?:er|re)s?\b|\bhypocent(?:er|re)s?\b|\bearthquake catalog",
    # --- extensions added after the recall audit (see manuscript S3.2) ------
    "trajectory_track": r"\btrajector(?:y|ies)\b|\bAIS data\b|\bvessel track|\bship track|\bmovement (?:data|track|path)\b|\banimal movement\b|\btelemetr|\bGPS collar|\bbio-?logging\b|\bfloating car data\b",
    "survey_cluster": r"\bDHS\b|\bdemographic and health survey|\bsurvey cluster|\bcluster (?:location|coordinate)s?\b|\benumeration area\b|\bgeo-?referenced survey",
    "geolocated_records": r"\bgeo-?locat(?:ed|ion) (?:data|record|point|event)|\bgeo-?referenced (?:data|record|event|observation)|\baddress-?level\b|\bindividual-?level location",
    "incident_records": r"\b(?:crash|accident|collision|fire|crime|theft|burglar\w*|shooting|robbery|homicide|outbreak|landslide|earthquake) (?:location|site|point|coordinate|record)s?\b|\breported (?:crash|crime|incident|case)s? (?:at|in|location)",
    "detection_points": r"\bactive fire (?:detection|point|product)|\bVIIRS (?:active fire|hotspot)|\bMODIS (?:active fire|hotspot)|\blightning (?:strike|flash) (?:location|data)|\bdetection points?\b",
    "facility_sites": r"\b(?:well|borehole|facility|station|store|shop|clinic|school|hospital|charging|sensor) (?:location|site)s?\b|\bsite locations?\b|\bfacility locations?\b",
}

# Methods that are *definitionally* defined on point patterns: their presence
# is sufficient evidence that the units of observation are point-referenced,
# even when the abstract does not name the data structure explicitly.
POINT_DEFINITIVE_METHODS = {"ppa", "point_process_model", "nna",
                            "network_constrained"}

# Contexts in which even a definitive method is applied to non-point data
# (raster fields, areal aggregates), which blocks the sufficiency rule.
DEFINITIVE_BLOCKERS = r"\b(?:pixel|raster|grid cell|areal unit|choropleth|census tract-level aggregat|administrative unit)\b"

# ---------------------------------------------------------------------------
# 2.  ELIGIBILITY:  criterion B - a spatial-analytical operation
# ---------------------------------------------------------------------------
# A record is eligible only if, in addition to point-referenced units, it
# performs an explicit spatial or spatio-temporal analytical operation.
CRITERION_B_SPATIAL_OPERATION = {
    "kde": r"\bkernel densit|\bKDE\b|\bdensity surface|\bintensity (?:function|surface|estimat)",
    "ppa": r"\bpoint pattern analysis\b|\bRipley'?s? K\b|\bK-?function\b|\bpair correlation function\b|\bG-?function\b|\bF-?function\b|\bL-?function\b|\bcomplete spatial randomness\b|\bCSR\b",
    "point_process_model": r"\bpoint process (?:model|regression)|\bPoisson (?:point )?process\b|\blog-?Gaussian Cox\b|\bLGCP\b|\bCox process\b|\bHawkes process\b|\bself-?exciting\b|\bGibbs process\b|\bStrauss process\b|\bdeterminantal point process\b|\bThomas process\b|\bMatern (?:cluster|point)",
    "nna": r"\bnearest neighbou?r (?:analysis|index|distance|method|statistic)|\baverage nearest neighbou?r\b|\bNNI\b|\bnearest-?neighbou?r ratio",
    "autocorrelation": r"\bspatial autocorrelation\b|\bMoran'?s I\b|\bGeary'?s C\b|\bLISA\b|\blocal indicators? of spatial association\b|\bspatial dependence\b|\bsemivariogram\b|\bvariogram\b",
    "hotspot": r"\bhot ?spot(?:s| analysis| detection| mapping)?\b|\bGetis-?Ord\b|\bGi\*|\bcold ?spot|\bcluster detection\b|\bspatial cluster",
    "scan_statistic": r"\bscan statistic|\bSaTScan\b|\bspace-?time scan\b|\bKulldorff",
    "spatial_clustering": r"\bDBSCAN\b|\bHDBSCAN\b|\bOPTICS\b|\bST-?DBSCAN\b|\bspatial cluster(?:ing)?\b|\bdensity-?based clustering\b|\bk-?means clustering\b",
    "geostatistics": r"\bkriging\b|\bgeostatistic|\bco-?kriging\b|\bGaussian process (?:regression|model)|\bspatial interpolation\b|\bIDW\b|\binverse distance weight",
    "spatial_regression": r"\bspatial (?:lag|error|econometric|autoregressive) model|\bSAR model\b|\bgeographically weighted\b|\bGWR\b|\bMGWR\b|\bspatial regression\b|\bspatial Durbin\b|\bCAR model\b|\bconditional autoregressive\b|\bBesag",
    "network_constrained": r"\bnetwork-?constrained\b|\bnetwork kernel densit|\bnetwork K-?function\b|\bstreet network (?:analysis|kernel)|\bnetwork-?based (?:KDE|kernel|point)",
    "spatiotemporal_model": r"\bspatio-?temporal (?:model|analysis|clustering|pattern|statistic|interpolation)|\bspace-?time (?:analysis|cluster|pattern|cube|kernel)",
    "accessibility_alloc": r"\blocation-?allocation\b|\bspatial accessibilit|\bcatchment area\b|\b2SFCA\b|\bhuff model\b",
    "sdm": r"\bspecies distribution model|\bSDM\b|\bMaxEnt\b|\becological niche model|\bhabitat suitability model",
    # analysing a spatial point process/pattern is itself the analytical
    # operation, even when no named estimator appears in the abstract
    "point_pattern_framework": r"\bspatial point (?:process|pattern)(?:es|s)?\b|\bspatio-?temporal point (?:process|pattern)(?:es|s)?\b|\breplicated point pattern|\bpoint pattern (?:analysis|data|statistic)",
    # added after the recall audit: explicit spatial-pattern characterisation
    # that does not name a specific estimator. Admissible only in combination
    # with criterion A, which restricts it to point-referenced units.
    "spatial_pattern_analysis": r"\bspatial (?:pattern|distribution) (?:analysis|characteristic|feature|structure)|\bspatial heterogeneit|\bco-?location pattern|\bspatial association\b|\bdistribution pattern of\b|\bspatial (?:variation|variability) (?:of|in)\b|\bspatial structure of\b",
}

# ---------------------------------------------------------------------------
# 3.  EXCLUSION: polysemous uses of "point" and out-of-scope traditions
# ---------------------------------------------------------------------------
# These fire only when criterion A is met *solely* through a polysemous term;
# see screening.py for the precedence logic.
POLYSEMY_TRAPS = {
    "statistical_point_estimate": r"\bpoint estimat|\bpoint prediction\b|\bpoint forecast",
    "physical_point": r"\b(?:melting|boiling|freezing|dew|flash|pour|cloud|tipping|set|smoke|critical|triple|saturation) point",
    "biomedical_point": r"\bpoint mutation|\bpoint-?of-?care\b|\bacupuncture point|\btrigger point|\bpressure point|\bend ?point|\btime point|\bcut-?off point",
    "rhetorical_point": r"\bpoint of view\b|\bstarting point\b|\bpoint out\b|\bat this point\b|\bpoint to the\b|\bfocal point\b|\bvantage point\b|\bturning point\b",
    "changepoint": r"\bchange-?point (?:detection|analysis|model)",
    "engineering_point": r"\bfixed point (?:theorem|iteration)|\bpoint load\b|\bpoint source pollution\b|\bpoint-?to-?point\b|\bdecimal point\b|\baccess point\b|\bcharging point\b|\bpoint machine\b",
}

# Whole-record exclusions: research traditions that use point primitives but
# are not point-based *spatial analysis* in the sense defined in Section 2.
OUT_OF_SCOPE = {
    "slam_odometry": r"\bSLAM\b|\bsimultaneous localization and mapping\b|\bvisual odometry\b|\bloop closure\b|\bpoint cloud registration\b|\bICP algorithm\b|\bpose estimation\b",
    "pure_cv_graphics": r"\bkeypoint detection\b|\bfeature point matching\b|\bcorner detection\b|\bmesh reconstruction\b|\bsurface reconstruction from point",
    "molecular_scale": r"\bsingle-?molecule localization\b|\bSTORM imaging\b|\bPALM imaging\b|\bcryo-?EM\b|\bprotein structure\b",
    "landscape_pattern_indices": r"\blandscape (?:pattern|metric)s? (?:index|indices|analysis)\b|\bFRAGSTATS\b|\bpatch density\b|\blandscape fragmentation index",
    "non_research_item": r"^(?:erratum|correction|corrigendum|retract|editorial|preface|foreword|book review|introduction to the special|comment on|reply to|discussion of|obituary|in memoriam)",
    # --- added after the precision audit (see manuscript S3.2) -------------
    # (i) point-cloud engineering: object extraction/segmentation/denoising
    #     from LiDAR or photogrammetric clouds is a sensor-processing task,
    #     not an analysis of the spatial arrangement of georeferenced events.
    "point_cloud_engineering": r"\bPointNet\b|\bpoint cloud (?:segmentation|classification|denoising|filtering|completion|compression|extraction|gridding|semantic)|\b(?:extraction|detection|identification|reconstruction|segmentation|contouring|classification) (?:of|from|framework|method|approach|algorithm)\b.{0,80}\bpoint clouds?\b|\bsupervoxel|\bbuilding (?:extraction|segmentation|contouring)\b|\broof (?:plane|contour|segmentation)|\bpoint cloud (?:deep|neural)|\bvoxel(?:i[sz]ation|-based) (?:network|segmentation)|\bdenoising (?:algorithm|method|approach) for .{0,40}(?:LiDAR|photon)|\bphoton-?counting LiDAR\b|\bnoise photon",
    # (ii) non-geographic point patterns: the review is bounded to point
    #      events located in geographical space (Section 2.2). Point-process
    #      statistics applied to cells, molecules, materials or galaxies fall
    #      outside that boundary.
    "non_geographic_micro": r"\bin situ transcriptomic|\bspatial transcriptomic|\bgene expression\b|\bRNA\b|\bcell nucle|\btissue section\b|\bmicroscop|\bhistolog|\bpharmaceutical coating\b|\bmicrostructure of (?:the )?material|\bnanoparticle|\bcrystal(?:lit|line) (?:structure|grain)|\bgalax(?:y|ies)\b|\bcosmolog|\bastronomical (?:survey|catalog)|\bradiograph|\bmagnetic resonance imaging\b|\bMRI\b|\bCT (?:scan|image)|\btumou?r (?:region|habitat|heterogeneit)|\bemphysema\b|\bpulmonary function\b|\bretinal\b|\bin vitro\b|\bcell(?:ular)? (?:population|distribution) within|\bfMRI\b|\bfunctional magnetic resonance|\bresting[- ]state\b|\bneuroimaging\b|\bcortex\b|\bpropofol\b",
}

# ---------------------------------------------------------------------------
# 4.  METHOD FAMILIES  (analytical taxonomy, level 2 of the PBSA taxonomy)
# ---------------------------------------------------------------------------
# Level-1 classes: CLASSICAL | INFERENTIAL | GEOSTATISTICAL | NETWORK |
#                  LEARNING | REALTIME
METHODS = {
    # --- Classical descriptive point-pattern statistics ---------------------
    "Kernel density estimation": (
        "CLASSICAL",
        r"\bkernel densit|\bKDE\b|\bdensity surface\b|\bkernel smooth",
    ),
    "Ripley's K / second-order PPA": (
        "CLASSICAL",
        r"\bRipley'?s? K\b|\bK-?function\b|\bpair correlation function\b|\bL-?function\b|\bG-?function\b|\bO-?ring statistic\b|\bsecond-?order (?:analysis|statistic|propert)",
    ),
    "Nearest-neighbour analysis": (
        "CLASSICAL",
        r"\bnearest neighbou?r (?:analysis|index|distance|statistic|ratio|method)\b|\baverage nearest neighbou?r\b|\bNNI\b|\bClark-?Evans\b",
    ),
    "Quadrat / intensity analysis": (
        "CLASSICAL",
        r"\bquadrat (?:count|analysis|method)|\bintensity (?:function|estimat|surface)|\bfirst-?order (?:intensity|propert)",
    ),
    "Standard deviational ellipse / centrography": (
        "CLASSICAL",
        r"\bstandard deviational ellipse\b|\bcentrograph|\bmean cent(?:er|re)\b|\bstandard distance\b|\bdirectional distribution\b",
    ),
    # --- Inferential / statistical modelling --------------------------------
    "Spatial autocorrelation statistics": (
        "INFERENTIAL",
        r"\bspatial autocorrelation\b|\bMoran'?s I\b|\bGeary'?s C\b|\bLISA\b|\blocal indicators? of spatial association\b|\bjoin ?count",
    ),
    "Getis-Ord hotspot statistics": (
        "INFERENTIAL",
        r"\bGetis-?Ord\b|\bGi\*|\bhot ?spot analysis\b|\boptimized hot ?spot\b|\bemerging hot ?spot",
    ),
    "Space-time scan statistics": (
        "INFERENTIAL",
        r"\bscan statistic|\bSaTScan\b|\bspace-?time scan\b|\bKulldorff|\bspatial scan\b|\bprospective scan",
    ),
    "Point process models (Poisson/Cox/Hawkes)": (
        "INFERENTIAL",
        r"\bpoint process (?:model|regression|fitting)|\bPoisson (?:point )?process\b|\blog-?Gaussian Cox\b|\bLGCP\b|\bCox process\b|\bHawkes\b|\bself-?exciting\b|\bGibbs (?:point )?process\b|\bStrauss (?:process|model)\b|\bdeterminantal point process\b|\bThomas process\b|\binhomogeneous Poisson",
    ),
    "Bayesian hierarchical spatial models": (
        "INFERENTIAL",
        r"\bBayesian (?:hierarchical|spatial|spatio-?temporal|inference|model)|\bINLA\b|\bintegrated nested Laplace\b|\bMCMC\b|\bMarkov chain Monte Carlo\b|\bposterior distribution\b|\bBYM model\b|\bconditional autoregressive\b|\bCAR prior",
    ),
    "Spatial regression / GWR": (
        "INFERENTIAL",
        r"\bspatial (?:lag|error|autoregressive|econometric|Durbin) model|\bSAR model\b|\bgeographically weighted\b|\bGWR\b|\bMGWR\b|\bGTWR\b|\bspatial regression\b|\bspatial panel\b",
    ),
    "Spatial clustering algorithms": (
        "INFERENTIAL",
        r"\bDBSCAN\b|\bHDBSCAN\b|\bOPTICS algorithm\b|\bST-?DBSCAN\b|\bdensity-?based (?:spatial )?clustering\b|\bhierarchical clustering\b|\bk-?means\b|\bagglomerative clustering\b|\bSKATER\b",
    ),
    # --- Geostatistics ------------------------------------------------------
    "Kriging and variogram geostatistics": (
        "GEOSTATISTICAL",
        r"\bkriging\b|\bvariogram\b|\bsemivariogram\b|\bgeostatistic|\bco-?kriging\b|\bregression kriging\b|\bindicator kriging\b|\buniversal kriging\b",
    ),
    "Gaussian processes / NNGP": (
        "GEOSTATISTICAL",
        r"\bGaussian process\b|\bnearest neighbou?r Gaussian process\b|\bNNGP\b|\bGaussian random field\b|\bMat(?:e|é)rn covariance\b|\bpredictive process\b|\bSPDE\b",
    ),
    "Deterministic interpolation": (
        "GEOSTATISTICAL",
        r"\binverse distance weight|\bIDW\b|\bspline interpolation\b|\bnatural neighbou?r interpolation\b|\bTIN\b|\btriangulated irregular network\b|\bVoronoi\b|\bThiessen\b|\bDelaunay\b",
    ),
    # --- Network-constrained ------------------------------------------------
    "Network-constrained point analysis": (
        "NETWORK",
        r"\bnetwork-?constrained\b|\bnetwork kernel densit|\bnetwork K-?function\b|\bnetwork-?based (?:KDE|kernel|density|point)|\bstreet network kernel\b|\blinear network (?:point|analysis)|\bnetwork autocorrelation\b",
    ),
    "Graph / network representation of points": (
        "NETWORK",
        r"\bgraph neural network\b|\bGCN\b|\bgraph convolution|\bspatial graph\b|\bproximity graph\b|\bcomplex network analysis\b",
    ),
    # --- Learning-based -----------------------------------------------------
    "Classical machine learning": (
        "LEARNING",
        r"\bmachine learning\b|\brandom forest\b|\bgradient boosting\b|\bXGBoost\b|\bLightGBM\b|\bsupport vector (?:machine|regression)\b|\bSVM\b|\bboosted regression tree|\bMaxEnt\b|\bensemble model",
    ),
    "Deep learning": (
        "LEARNING",
        r"\bdeep learning\b|\bneural network\b|\bconvolutional neural\b|\bCNN\b|\bLSTM\b|\brecurrent neural\b|\btransformer (?:model|architecture|network)\b|\bautoencoder\b|\bGAN\b|\bgenerative adversarial\b|\bdeep neural\b",
    ),
    "Explainable AI / interpretable ML": (
        "LEARNING",
        r"\bexplainable (?:AI|artificial intelligence|machine learning)\b|\bXAI\b|\bSHAP\b|\bSHapley\b|\bLIME\b|\bfeature importance\b|\binterpretable (?:model|machine learning)\b|\bpartial dependence\b|\bcounterfactual explanation",
    ),
    "Geospatial foundation / LLM models": (
        "LEARNING",
        r"\bfoundation model\b|\blarge language model\b|\bLLM\b|\bGPT-?[34]\b|\bself-?supervised (?:learning|pretrain)|\bpre-?trained (?:geospatial|spatial) model|\bembedding model\b",
    ),
    # --- Real-time / streaming ---------------------------------------------
    "Real-time and streaming spatial analytics": (
        "REALTIME",
        r"\breal-?time (?:analy|monitor|detect|predict|process|mapping|tracking)|\bstreaming (?:data|analytic|algorithm)|\bonline learning\b|\bnear real-?time\b|\bearly warning system\b|\bdigital twin\b|\bedge computing\b",
    ),
    "Distributed / high-performance geocomputation": (
        "REALTIME",
        r"\bhigh-?performance computing\b|\bHPC\b|\bparallel (?:computing|algorithm|processing)\b|\bGPU (?:acceleration|computing)\b|\bcloud computing\b|\bSpark\b|\bHadoop\b|\bMapReduce\b|\bdistributed computing\b|\bscalable (?:algorithm|computation|inference)",
    ),
}

# ---------------------------------------------------------------------------
# 5.  APPLICATION DOMAINS
# ---------------------------------------------------------------------------
DOMAINS = {
    "Public health & epidemiology": r"\bepidemiolog|\bdisease\b|\bincidence\b|\bprevalence\b|\bmortalit|\bmorbidit|\bpublic health\b|\bCOVID-?19\b|\bSARS-?CoV-?2\b|\bmalaria\b|\bdengue\b|\btuberculosis\b|\bcholera\b|\bcancer\b|\bhealth outcome|\bpatients?\b|\bhospital|\bvaccin|\bepidemic|\boutbreak\b|\bschistosom|\bleishman|\bHIV\b|\binfluenza\b|\bZika\b|\bEbola\b",
    "Crime & security": r"\bcrime\b|\bcriminal|\bburglar|\brobber|\bhomicide|\btheft\b|\bpolic(?:e|ing)\b|\bviolen(?:ce|t)\b|\boffend|\bdelinquen|\bgun ?(?:shot|violence)|\bterroris|\bshooting|\bassault\b",
    "Transportation & mobility": r"\btraffic\b|\btransport|\bcrash(?:es)?\b|\bcollision|\broad accident|\bmobility\b|\bcommut|\btaxi\b|\bride-?hailing\b|\bbike-?shar|\bbicycl|\bpedestrian|\bvehicl|\btravel behaviou?r|\btransit\b|\bparking\b|\bEV charging\b",
    "Urban studies & planning": r"\burban\b|\bcity\b|\bcities\b|\bland use\b|\bbuilt environment\b|\bhousing\b|\bgentrif|\bneighbou?rhood|\bsettlement|\burbani[sz]ation\b|\bplanning\b|\bPOIs?\b|\bpoints? of interest\b|\bsmart city\b|\bmetropolitan\b",
    "Environmental monitoring & pollution": r"\bair (?:quality|pollution)\b|\bPM2\.5\b|\bPM10\b|\bpollut|\bcontaminat|\bheavy metal|\bwater quality\b|\bsoil (?:quality|contamination|property|organic)|\bemission|\bnoise (?:level|pollution|mapping)|\bgroundwater\b|\benvironmental monitoring\b",
    "Ecology & biodiversity": r"\becolog|\bbiodiversit|\bspecies\b|\bhabitat\b|\bforest\b|\btree\b|\bvegetation\b|\bwildlife\b|\banimal\b|\bplant\b|\bfishery|\bfish\b|\bbird\b|\binsect\b|\bpollinator|\bconservation\b|\bpopulation dynamics\b|\bcanopy\b",
    "Disaster risk & hazards": r"\bearthquake|\bseismic|\bflood|\blandslide|\bwildfire|\bforest fire\b|\bhazard\b|\bdisaster\b|\bdrought\b|\btsunami|\bvolcan|\bhurricane|\btyphoon|\bcyclone|\bavalanche|\bemergency (?:response|management)|\brisk assessment\b",
    "Agriculture & food systems": r"\bagricultur|\bcrop\b|\byield\b|\bfarm|\bprecision agriculture\b|\bsoil fertilit|\birrigat|\blivestock\b|\bfood securit|\bharvest|\bpest\b|\bagronom",
    "Retail & economic geography": r"\bretail\b|\bstore\b|\bshop|\bmarket area\b|\bconsumer\b|\bcommerc|\bbusiness location\b|\bfirm location\b|\brestaurant|\brestaurant|\bfranchise|\bhousing price\b|\breal estate\b|\bland value\b|\beconomic geograph",
    "Tourism & recreation": r"\btouris|\brecreation|\bvisitor|\bhotel|\battraction|\bpark visit|\btravel destination|\bAirbnb\b|\bheritage site",
    "Social media & digital society": r"\bsocial media\b|\bTwitter\b|\btweet|\bFlickr\b|\bInstagram\b|\bFoursquare\b|\bWeibo\b|\bcheck-?in|\bcrowdsourc|\bvolunteered geographic\b|\bVGI\b|\bOpenStreetMap\b|\bsocial network\b|\bgeosocial\b",
    "Energy & infrastructure": r"\benergy\b|\bpower (?:grid|plant|line)\b|\brenewable|\bsolar\b|\bwind (?:farm|turbine|energy)\b|\bpipeline|\bwell (?:location|site)|\boil and gas\b|\bmining\b|\butilit|\binfrastructure network\b",
    "Geodesy, remote sensing & earth observation": r"\bLiDAR\b|\bremote sensing\b|\bsatellite\b|\bGNSS\b|\bInSAR\b|\bphotogrammetr|\bpoint cloud\b|\bUAV\b|\bdrone\b|\bearth observation\b|\bSentinel-?[12]\b|\bLandsat\b|\bMODIS\b",
}

# ---------------------------------------------------------------------------
# 6.  DATA SOURCES
# ---------------------------------------------------------------------------
DATA_SOURCES = {
    "Official / administrative records": r"\badministrative (?:data|record)|\bcensus\b|\bofficial statistic|\bnational (?:registry|register|database|survey)|\bsurveillance (?:system|data)\b|\bhealth (?:registry|register|record)|\bpolice record|\bgovernment data",
    "Field survey & in-situ sampling": r"\bfield (?:survey|campaign|measurement|sampling|work)\b|\bin-?situ\b|\bsoil sampl|\bground(?:-| )?based measurement|\bquestionnaire\b|\bhousehold survey\b|\bplot(?:-| )level (?:data|survey)|\bfield plot",
    "Remote sensing & earth observation": r"\bremote sensing\b|\bsatellite (?:image|data|observation)|\bLandsat\b|\bMODIS\b|\bSentinel-?[12]\b|\bhyperspectral\b|\baerial (?:image|photograph)|\bUAV\b|\bdrone\b|\bInSAR\b|\bimagery\b",
    "LiDAR & 3D point clouds": r"\bLiDAR\b|\blaser scanning\b|\bALS\b|\bTLS\b|\bpoint clouds?\b|\bphotogrammetric point",
    "Volunteered geographic information": r"\bvolunteered geographic\b|\bVGI\b|\bOpenStreetMap\b|\bOSM\b|\bcitizen science\b|\bcrowd-?sourc|\bcollaborative mapping\b|\bGBIF\b|\beBird\b|\biNaturalist\b",
    "Social-media & geosocial data": r"\bsocial media\b|\bTwitter\b|\btweets?\b|\bWeibo\b|\bFlickr\b|\bInstagram\b|\bFoursquare\b|\bYelp\b|\bTripAdvisor\b|\bgeo-?tagged (?:photo|post|tweet)|\bcheck-?ins?\b",
    "Mobile phone & GPS trajectory data": r"\bmobile phone\b|\bcall detail record|\bCDR\b|\bmobile positioning\b|\bsmartphone (?:data|sensor|trace)|\bGPS (?:trajector|trace|track|data)|\btrajector(?:y|ies)\b|\bfloating car data\b|\btaxi (?:GPS|trajector)|\blocation-?based service",
    "Sensor networks & IoT": r"\bsensor network\b|\bIoT\b|\binternet of things\b|\bwireless sensor\b|\blow-?cost sensor\b|\bmonitoring network\b|\bautomatic weather station|\bseismic network\b|\btelemetr|\bGPS collar|\bbio-?logging\b",
    "POI & commercial geodatabases": r"\bpoints? of interest\b|\bPOI (?:data|dataset|database)\b|\bAMap\b|\bBaidu (?:map|POI)\b|\bGoogle (?:Places|Maps) API\b|\bcommercial (?:database|dataset)|\bbusiness registry\b",
    "Simulated / synthetic data": r"\bsimulat(?:ed|ion) (?:data|study|experiment)\b|\bsynthetic (?:data|dataset|point)|\bMonte Carlo simulation\b|\bagent-?based model",
}

# ---------------------------------------------------------------------------
# 7.  SOFTWARE ENVIRONMENTS
# ---------------------------------------------------------------------------
SOFTWARE = {
    "R (base/tidyverse)": r"\bR (?:statistical )?(?:software|package|environment|programming)\b|\bR version\b|\bCRAN\b|\bin R\b|\busing R\b|\bR language\b",
    "spatstat (R)": r"\bspatstat\b",
    "INLA / R-INLA": r"\bR-?INLA\b|\bINLA\b",
    "Python (scientific stack)": r"\bPython\b|\bscikit-?learn\b|\bsklearn\b|\bGeoPandas\b|\bPySAL\b|\bNumPy\b|\bpandas\b|\bPyTorch\b|\bTensorFlow\b|\bKeras\b",
    "ArcGIS / ArcMap / ArcGIS Pro": r"\bArcGIS\b|\bArcMap\b|\bArcInfo\b|\bESRI\b|\bArcPy\b",
    "QGIS": r"\bQGIS\b|\bQuantum GIS\b",
    "GeoDa": r"\bGeoDa\b",
    "SaTScan": r"\bSaTScan\b",
    "CrimeStat": r"\bCrimeStat\b",
    "GRASS GIS": r"\bGRASS GIS\b",
    "MATLAB": r"\bMATLAB\b",
    "Google Earth Engine": r"\bGoogle Earth Engine\b|\bGEE platform\b|\bEarth Engine\b",
    "WinBUGS / JAGS / Stan": r"\bWinBUGS\b|\bOpenBUGS\b|\bJAGS\b|\bStan\b(?! model)|\bNIMBLE\b",
    "SPSS / SAS / Stata": r"\bSPSS\b|\bSAS (?:software|9)\b|\bStata\b",
    "GS\\+ / Surfer / other geostat": r"\bGS\+\b|\bSurfer\b|\bSGeMS\b|\bIsatis\b",
}

# ---------------------------------------------------------------------------
# 8.  SPATIAL AND TEMPORAL SCALE
# ---------------------------------------------------------------------------
SPATIAL_SCALE = {
    "Micro / plot / building": r"\bplot(?:-| )scale\b|\bmicro-?scale\b|\bbuilding(?:-| )level\b|\bindoor\b|\bfield plot\b|\bquadrat\b|\bhectare plot\b|\bstand(?:-| )level\b|\bwithin-?site\b",
    "Neighbourhood / local": r"\bneighbou?rhood(?:-| )(?:level|scale)\b|\bcensus (?:tract|block)|\blocal(?:-| )scale\b|\bstreet(?:-| )(?:level|segment)\b|\bcommunity(?:-| )level\b|\bward(?:-| )level\b",
    "City / metropolitan": r"\bcity(?:-| )(?:wide|scale|level)\b|\burban (?:area|scale|region)\b|\bmetropolitan\b|\bmunicipal|\bcity of\b|\bagglomeration\b",
    "Regional / sub-national": r"\bregional(?:-| )(?:scale|level)\b|\bprovinc|\bstate(?:-| )level\b|\bcounty(?:-| )level\b|\bdistrict(?:-| )level\b|\bwatershed\b|\bbasin\b|\bcatchment\b|\bsub-?national\b",
    "National": r"\bnational(?:-| )(?:scale|level|wide)\b|\bcountry(?:-| )(?:wide|level|scale)\b|\bnationwide\b|\bacross the country\b",
    "Continental / global": r"\bglobal(?:-| )(?:scale|level)\b|\bworldwide\b|\bcontinental(?:-| )scale\b|\bpan-?European\b|\bacross Europe\b|\bglobally\b|\bmulti-?country\b|\bcross-?national\b",
}

TEMPORAL_SCALE = {
    "Cross-sectional / static": r"\bcross-?sectional\b|\bsnapshot\b|\bsingle (?:year|time point|survey)\b|\bstatic (?:analysis|pattern)\b",
    "Sub-daily / real-time": r"\breal-?time\b|\bhourly\b|\bminute-?level\b|\bsecond-?by-?second\b|\bstreaming\b|\bsub-?daily\b|\bcontinuous monitoring\b",
    "Daily to monthly": r"\bdaily\b|\bweekly\b|\bmonthly\b|\bseasonal\b|\bday-?of-?week\b|\bdiurnal\b",
    "Annual to decadal": r"\bannual\b|\byearly\b|\binter-?annual\b|\bmulti-?year\b|\bdecad(?:e|al)\b|\blong-?term (?:trend|change|monitoring)\b|\btime series\b",
    "Multi-decadal / historical": r"\bmulti-?decadal\b|\bhistorical (?:record|data|analysis)\b|\bcentur(?:y|ies)\b|\bsince 1[89]\d\d\b|\bpalaeo|\bpaleo",
}

# ---------------------------------------------------------------------------
# 9.  RIGOUR CONSTRUCTS (quality / reproducibility / ethics)
# ---------------------------------------------------------------------------
UNCERTAINTY = {
    "Statistical uncertainty reported": r"\bconfidence interval|\bcredible interval|\bstandard error|\bp-?value|\bsignificance (?:level|test)|\buncertainty (?:quantif|estimat|analysis|assessment)|\bposterior (?:uncertainty|variance)|\bprediction interval",
    "Sensitivity analysis": r"\bsensitivity analysis\b|\brobustness (?:check|test|analysis)\b|\bbandwidth (?:selection|sensitivity)\b|\bparameter sensitivity\b|\bscenario analysis\b",
    "MAUP / scale effects": r"\bmodifiable areal unit\b|\bMAUP\b|\bscale effect|\bzoning effect|\baggregation (?:effect|bias)|\bscale (?:dependence|dependency)\b|\becological fallacy\b",
    "Edge effects": r"\bedge effect|\bboundary effect|\bedge correction|\bborder effect|\btoroidal correction",
    "Positional / geocoding uncertainty": r"\bpositional (?:accuracy|uncertainty|error)\b|\bgeocoding (?:error|accuracy|uncertainty)\b|\blocational (?:error|uncertainty)\b|\bcoordinate (?:error|uncertainty)\b|\bGPS (?:error|accuracy)\b|\bspatial (?:accuracy|error)\b",
}

VALIDATION = {
    "Cross-validation / holdout": r"\bcross-?validat|\bk-?fold\b|\bleave-?one-?out\b|\bhold-?out\b|\btrain(?:ing)?[/ -](?:and )?test (?:set|split)|\bout-?of-?sample\b|\bspatial cross-?validation\b",
    "Accuracy metrics reported": r"\bRMSE\b|\bMAE\b|\bR-?squared\b|\bAUC\b|\bROC curve\b|\bkappa (?:coefficient|statistic)\b|\bprecision and recall\b|\bF1[- ]score\b|\boverall accuracy\b|\bMAPE\b",
    "Monte Carlo / simulation envelope": r"\bMonte Carlo (?:test|simulation|envelope)\b|\bsimulation envelope\b|\brandomi[sz]ation test\b|\bpermutation test\b|\bbootstrap",
    "Independent / ground-truth validation": r"\bground[- ]truth|\bindependent (?:validation|dataset|data set)\b|\bfield validation\b|\bexternal validation\b|\bvalidation (?:dataset|data set|sample|site)\b",
    "Model comparison / selection": r"\bAIC\b|\bBIC\b|\bDIC\b|\bWAIC\b|\bmodel (?:comparison|selection)\b|\blikelihood ratio test\b|\bbenchmark(?:ing|ed)? against\b",
}

REPRODUCIBILITY = {
    "Code or software shared": r"\bcode (?:is |are )?(?:available|shared|provided|released)\b|\bsource code\b|\bGitHub\b|\bGitLab\b|\bZenodo\b|\bopen-?source (?:package|tool|implementation|software)\b|\bR package\b|\bPython (?:package|library|toolbox)\b|\bfreely available (?:tool|software|package)",
    "Data availability stated": r"\bdata (?:are|is) (?:available|accessible|publicly)\b|\bopen data\b|\bpublicly available (?:data|dataset)\b|\bdata availability\b|\bdata repositor|\bFAIR (?:data|principle)",
    "Workflow / protocol formalised": r"\breproducib|\breplicab|\bworkflow\b|\bprotocol\b|\bpipeline\b|\bcontainer(?:ised|ized)\b|\bDocker\b|\bnotebook\b",
}

ETHICS_PRIVACY = {
    "Privacy / confidentiality": r"\bprivacy\b|\bconfidential|\banonymi[sz]|\bde-?identif|\bpseudonymi[sz]|\bGDPR\b|\bdata protection\b|\bgeomask|\bgeographic masking\b|\bk-?anonymity\b|\bdifferential privacy\b",
    "Ethical review / consent": r"\bethic(?:s|al) (?:approval|committee|review|board|clearance)\b|\binformed consent\b|\bIRB\b|\bethical consideration",
    "Surveillance / algorithmic bias": r"\bsurveillance (?:capital|state|concern|risk)\b|\balgorithmic bias\b|\bfairness\b|\bdiscriminat|\bpredictive policing\b|\bbias(?:ed)? (?:against|toward)\b|\bequity (?:concern|implication)\b|\bsocial justice\b",
}

# ---------------------------------------------------------------------------
# 10.  MATURITY FRAMEWORK (PB-SAM) - scoring rubric
# ---------------------------------------------------------------------------
# Each dimension is scored 0-2 from abstract-level evidence. The composite
# PB-SAM score (0-10) is an *abstract-level proxy*, not a full-text appraisal.
PBSAM_DIMENSIONS = [
    ("D1_method_specification", "Explicit, named analytical method"),
    ("D2_uncertainty", "Explicit treatment of uncertainty or error"),
    ("D3_validation", "Explicit validation or model-comparison procedure"),
    ("D4_data_transparency", "Data provenance and availability described"),
    ("D5_reproducibility", "Code, software or workflow made explicit"),
]

# ---------------------------------------------------------------------------
# 11.  DOI-PREFIX -> PUBLISHER  (deterministic registrant mapping)
# ---------------------------------------------------------------------------
DOI_PREFIX_PUBLISHER = {
    "10.1016": "Elsevier",
    "10.3390": "MDPI",
    "10.1007": "Springer Nature (Springer)",
    "10.1109": "IEEE",
    "10.1080": "Taylor & Francis",
    "10.1002": "Wiley",
    "10.1111": "Wiley",
    "10.1371": "PLOS",
    "10.1038": "Springer Nature (Nature Portfolio)",
    "10.1029": "AGU (Wiley)",
    "10.3389": "Frontiers",
    "10.1093": "Oxford University Press",
    "10.5194": "Copernicus (EGU)",
    "10.1186": "BMC / Springer Nature",
    "10.1190": "Society of Exploration Geophysicists",
    "10.1088": "IOP Publishing",
    "10.1021": "American Chemical Society",
    "10.1177": "SAGE",
    "10.1175": "American Meteorological Society",
    "10.14358": "ASPRS",
    "10.1155": "Hindawi / Wiley",
    "10.1073": "PNAS",
    "10.1126": "AAAS (Science)",
    "10.1101": "Cold Spring Harbor",
    "10.1061": "ASCE",
    "10.1145": "ACM",
    "10.1214": "Institute of Mathematical Statistics",
    "10.1198": "ASA (Taylor & Francis)",
    "10.1201": "CRC Press",
    "10.3389": "Frontiers",
    "10.4236": "Scientific Research Publishing",
    "10.1590": "SciELO",
    "10.1017": "Cambridge University Press",
    "10.1139": "Canadian Science Publishing",
    "10.1657": "INSTAAR",
    "10.2166": "IWA Publishing",
    "10.1289": "Environmental Health Perspectives",
    "10.1136": "BMJ",
    "10.1097": "Wolters Kluwer",
    "10.1183": "European Respiratory Society",
    "10.1042": "Portland Press",
    "10.5589": "Canadian Journal of Remote Sensing",
    "10.1130": "Geological Society of America",
    "10.2113": "GeoScienceWorld",
    "10.1785": "Seismological Society of America",
    "10.1046": "Wiley (legacy Blackwell)",
    "10.1023": "Springer (legacy Kluwer)",
    "10.1006": "Elsevier (legacy Academic Press)",
    "10.1067": "Elsevier (legacy Mosby)",
    "10.2307": "JSTOR",
    "10.1071": "CSIRO Publishing",
    "10.1051": "EDP Sciences",
    "10.1049": "IET",
    "10.1099": "Microbiology Society",
    "10.2478": "Sciendo / De Gruyter",
    "10.1515": "De Gruyter",
    "10.1063": "AIP Publishing",
    "10.1103": "American Physical Society",
    "10.1364": "Optica",
    "10.1105": "American Society of Plant Biologists",
    "10.1093": "Oxford University Press",
    "10.1287": "INFORMS",
    "10.1111": "Wiley",
    "10.4324": "Routledge",
    "10.1594": "PANGAEA",
    "10.5670": "Oceanography Society",
    "10.7717": "PeerJ",
    "10.1098": "The Royal Society",
    "10.1146": "Annual Reviews",
    "10.1041": "Other",
}


def compile_family(d):
    """Compile a {label: pattern} or {label: (class, pattern)} dict."""
    out = {}
    for k, v in d.items():
        pat = v[1] if isinstance(v, tuple) else v
        cls = v[0] if isinstance(v, tuple) else None
        out[k] = (cls, re.compile(pat, re.IGNORECASE))
    return out


COMPILED = {
    "critA": compile_family(CRITERION_A_POINT_UNITS),
    "critB": compile_family(CRITERION_B_SPATIAL_OPERATION),
    "traps": compile_family(POLYSEMY_TRAPS),
    "oos": compile_family(OUT_OF_SCOPE),
    "methods": compile_family(METHODS),
    "domains": compile_family(DOMAINS),
    "data_sources": compile_family(DATA_SOURCES),
    "software": compile_family(SOFTWARE),
    "spatial_scale": compile_family(SPATIAL_SCALE),
    "temporal_scale": compile_family(TEMPORAL_SCALE),
    "uncertainty": compile_family(UNCERTAINTY),
    "validation": compile_family(VALIDATION),
    "reproducibility": compile_family(REPRODUCIBILITY),
    "ethics": compile_family(ETHICS_PRIVACY),
}

METHOD_CLASS_LABELS = {
    "CLASSICAL": "Classical point-pattern statistics",
    "INFERENTIAL": "Inferential / model-based spatial statistics",
    "GEOSTATISTICAL": "Geostatistical / continuous-field methods",
    "NETWORK": "Network-constrained and graph-based methods",
    "LEARNING": "Learning-based (ML/DL/XAI) methods",
    "REALTIME": "Real-time, streaming and high-performance geocomputation",
}
