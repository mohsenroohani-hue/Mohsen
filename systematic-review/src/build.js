const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType,
  Table, TableRow, TableCell, WidthType, BorderStyle, ShadingType,
  ExternalHyperlink, PageBreak, LevelFormat, convertInchesToTwip
} = require("docx");
const fs = require("fs");
const REFS = require("./refs.js");

const FONT = "Calibri";
const BODY_SIZE = 22; // 11pt
const TITLE_SIZE = 40;

function p(text, opts = {}) {
  return new Paragraph({
    spacing: { after: 200, line: 276 },
    alignment: opts.align || AlignmentType.JUSTIFIED,
    children: [new TextRun({ text, font: FONT, size: BODY_SIZE, italics: opts.italics, bold: opts.bold })],
  });
}

function heading(text, level) {
  return new Paragraph({
    heading: level,
    spacing: { before: 320, after: 160 },
    children: [new TextRun({ text, font: FONT, bold: true })],
  });
}

function caption(text) {
  return new Paragraph({
    spacing: { before: 80, after: 240 },
    alignment: AlignmentType.LEFT,
    children: [new TextRun({ text, font: FONT, size: 20, italics: true })],
  });
}

// ---------- Title block ----------
const titleBlock = [
  new Paragraph({
    spacing: { after: 120 },
    alignment: AlignmentType.CENTER,
    children: [new TextRun({
      text: "Trajectories of Point-Based, Line-Based, and Polygon-Based Spatial Analysis:",
      font: FONT, size: TITLE_SIZE, bold: true,
    })],
  }),
  new Paragraph({
    spacing: { after: 300 },
    alignment: AlignmentType.CENTER,
    children: [new TextRun({
      text: "A Systematic Review of Methodological Evolution in GIScience",
      font: FONT, size: TITLE_SIZE, bold: true,
    })],
  }),
  new Paragraph({
    spacing: { after: 80 },
    alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "Mohsen Roohani", font: FONT, size: 24 })],
  }),
  new Paragraph({
    spacing: { after: 400 },
    alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "28 July 2026", font: FONT, size: 20, italics: true, color: "555555" })],
  }),
];

// ---------- Abstract ----------
const abstract = [
  heading("Abstract", HeadingLevel.HEADING_1),
  p("Background: Point, line, and polygon representations are the three foundational vector data models of geographic information science (GIScience), and each has spawned a distinct methodological lineage for spatial analysis. Despite this shared origin, no review has traced how these three lineages developed in parallel, diverged methodologically, and are now reconverging under data-intensive and artificial-intelligence-driven paradigms."),
  p("Objective: This systematic review synthesizes the methodological evolution — the “trajectory” — of point-based, line-based, and polygon-based spatial analysis from their statistical and cartographic origins to contemporary machine-learning-augmented practice, and identifies the cross-cutting forces driving change across all three."),
  p("Methods: Following PRISMA 2020 reporting principles adapted for a methodological rather than clinical review (Page et al., 2021), we searched the Consensus academic search engine (backed by the Semantic Scholar corpus) on 28 July 2026 using seven structured query sets spanning point pattern analysis, network and linear-referencing analysis, areal/polygon analysis, spatial autocorrelation, trajectory and movement-data mining, GIScience historiography, and geospatial artificial intelligence (GeoAI). Of 140 records identified, 68 were retained for narrative synthesis after de-duplication and relevance screening."),
  p("Results: Point-based analysis evolved from distance- and quadrat-based tests of complete spatial randomness through second-order statistics (Ripley's K, pair-correlation, G/F functions) to inhomogeneous, marked, and network-constrained point processes, and now to point processes coupled with deep generative models. Line-based analysis progressed from topological network data structures and linear referencing to complex/spatial network science, and, following the proliferation of GPS, split off a distinct trajectory-data-mining literature covering preprocessing, pattern mining, clustering, and prediction. Polygon-based analysis moved from choropleth mapping and areal-interpolation heuristics through spatial-autocorrelation statistics (Moran's I, Geary's C, local indicators) and geographically weighted regression to multiscale and machine-learning-augmented areal models, alongside a recent “polygon-native” current that rejects centroid-reduction. Across all three trajectories we identify four converging forces: open-source software ecosystems, a shift from confirmatory statistics toward computational/algorithmic inference, spatial big data, and GeoAI."),
  p("Conclusions: The three trajectories, though historically asynchronous, are converging on a shared computational and AI-augmented infrastructure while retaining data-model-specific theoretical cores that this convergence does not erase. Priority gaps include underused polygon-native methods, tighter integration of network-constrained and areal models, interpretability of GeoAI across all three geometries, and the persistent translational lag between methodological frontiers and applied practice."),
  p("Keywords: spatial analysis; point pattern analysis; network analysis; areal data; trajectory data mining; GIScience; systematic review; GeoAI", { italics: false }),
];

// ---------- Introduction ----------
const intro = [
  heading("1. Introduction", HeadingLevel.HEADING_1),
  p("Geographic information has, since the earliest digital geographic information systems (GIS), been organized around three discrete vector data models: points, lines, and polygons. This tripartite taxonomy is not merely a data-storage convenience; it has structured the development of spatial analysis itself, producing three loosely coupled methodological sub-traditions, each with its own theoretical lineage, canonical statistics, and software ecosystem (Goodchild & Haining, 2003; Schuurman, 2013, cited in the GIScience historiography reviewed below)."),
  p("Point-based spatial analysis has its roots in plant ecology and forestry's search for departures from complete spatial randomness using distance- and quadrat-based tests (Diggle, 1976, discussed in Illian et al., 2008); it matured into the modern theory of spatial point processes, with second-order summary statistics (Ripley's K, the pair-correlation function) and, later, model-based inference for inhomogeneous, marked, and multitype patterns (Møller & Waagepetersen, 2016; Baddeley, Turner & Rubak, 2015). Line-based analysis grew out of graph theory and transportation geography's concern with network topology, connectivity, and linear referencing (Curtin, 2007, 2009); the proliferation of GPS-enabled devices then catalyzed a largely separate, computer-science-driven trajectory-data-mining literature concerned with the movement paths of people, vehicles, and animals (Zheng, 2015). Polygon-based, or areal, analysis emerged from the cartographic tradition of the choropleth map and from regional science's concern with spatial dependence among aggregated units, crystallizing methodologically around Moran's I and, decades later, geographically weighted regression (Getis, 2008; Anselin, Syabri & Kho, 2005)."),
  p("Although each of these three lineages has been reviewed in relative isolation — point pattern analysis within ecology (Velázquez et al., 2016; Ben-Said, 2021), network analysis within GIScience (Curtin, 2007), areal interpolation within geography (Comber & Zeng, 2019) — no synthesis has traced them side-by-side as parallel trajectories shaped by shared external forces: the maturation of open-source scientific computing, the shift from confirmatory to computational and algorithmic inference, the arrival of spatial big data, and, most recently, geospatial artificial intelligence (GeoAI). Understanding these trajectories together matters for two reasons. First, contemporary applications increasingly require combining data models — for example, point events analyzed against a polygon-aggregated population denominator, or vehicle trajectories intersected with administrative polygons — and cross-model literacy helps prevent the kind of methodological error documented when point-based methods are applied naively to network-constrained or polygon data (Baddeley, Rakshit & Nair, 2020; Mu & Tong, 2020). Second, comparing the timing and character of methodological innovation across the three trajectories illuminates how new technologies and paradigms diffuse through GIScience as a whole, rather than through any one of its subfields in isolation (Bivand, 2022; Li, 2020)."),
  p("This review addresses five research questions: (RQ1) How has point-based spatial analysis evolved methodologically since its statistical origins? (RQ2) How has line-based, i.e. network and trajectory, spatial analysis evolved? (RQ3) How has polygon-based, i.e. areal, spatial analysis evolved? (RQ4) What cross-cutting technological and methodological forces have shaped all three trajectories, and where do they converge or diverge? (RQ5) What gaps remain at the interfaces between the three data models, and what does this imply for future methodological research?"),
];

// ---------- Methods ----------
const searchRows = [
  ["Q1", "evolution of point pattern analysis methods spatial statistics", "20"],
  ["Q2", "kernel density estimation spatial analysis review trends", "0 (rate-limited, not retried)"],
  ["Q3", "spatial point process statistics history GIS", "0 (rate-limited, not retried)"],
  ["Q4", "network spatial analysis evolution review linear referencing GIS", "20"],
  ["Q5", "polygon areal spatial data analysis review methods evolution", "20"],
  ["Q6", "history and evolution of GIScience spatial analysis geographic information science", "20"],
  ["Q7", "spatial autocorrelation Moran's I geographically weighted regression review history", "20"],
  ["Q8", "GeoAI deep learning spatial analysis trends review big data", "20"],
  ["Q9", "moving object trajectory data mining review GPS", "20"],
];

function searchTable() {
  const headerCells = ["ID", "Query string", "Records returned"].map(t => new TableCell({
    width: { size: t === "Query string" ? 60 : 20, type: WidthType.PERCENTAGE },
    shading: { type: ShadingType.CLEAR, fill: "E7E6E6" },
    children: [new Paragraph({ children: [new TextRun({ text: t, bold: true, font: FONT, size: 20 })] })],
  }));
  const rows = [new TableRow({ children: headerCells, tableHeader: true })];
  for (const [id, q, n] of searchRows) {
    rows.push(new TableRow({
      children: [
        new TableCell({ width: { size: 20, type: WidthType.PERCENTAGE }, children: [new Paragraph({ children: [new TextRun({ text: id, font: FONT, size: 20 })] })] }),
        new TableCell({ width: { size: 60, type: WidthType.PERCENTAGE }, children: [new Paragraph({ children: [new TextRun({ text: q, font: FONT, size: 20, italics: true })] })] }),
        new TableCell({ width: { size: 20, type: WidthType.PERCENTAGE }, children: [new Paragraph({ children: [new TextRun({ text: n, font: FONT, size: 20 })] })] }),
      ],
    }));
  }
  return new Table({ width: { size: 100, type: WidthType.PERCENTAGE }, rows });
}

function prismaTable() {
  const stages = [
    ["Records identified through searching (9 queries, incl. 2 failed)", "140"],
    ["Duplicate records removed (same record returned by >1 query)", "14"],
    ["Unique records screened (title / venue / abstract)", "126"],
    ["Records excluded at screening (off-topic matches, e.g., generic statistics texts whose bibliography incidentally matched search terms; narrow single-site applied studies without methodological or historical content; low-information records)", "58"],
    ["Records included in narrative synthesis", "68"],
  ];
  const rows = [new TableRow({
    children: ["PRISMA-adapted stage", "n"].map((t, i) => new TableCell({
      width: { size: i === 0 ? 80 : 20, type: WidthType.PERCENTAGE },
      shading: { type: ShadingType.CLEAR, fill: "E7E6E6" },
      children: [new Paragraph({ children: [new TextRun({ text: t, bold: true, font: FONT, size: 20 })] })],
    })), tableHeader: true,
  })];
  for (const [stage, n] of stages) {
    rows.push(new TableRow({
      children: [
        new TableCell({ width: { size: 80, type: WidthType.PERCENTAGE }, children: [new Paragraph({ children: [new TextRun({ text: stage, font: FONT, size: 20 })] })] }),
        new TableCell({ width: { size: 20, type: WidthType.PERCENTAGE }, children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: n, font: FONT, size: 20, bold: true })] })] }),
      ],
    }));
  }
  return new Table({ width: { size: 100, type: WidthType.PERCENTAGE }, rows });
}

const methods = [
  heading("2. Methods", HeadingLevel.HEADING_1),
  heading("2.1 Protocol", HeadingLevel.HEADING_2),
  p("This review was not prospectively registered; methodological/historiographic reviews of this kind fall outside the scope of clinical registries such as PROSPERO. We instead followed, to the extent applicable to a non-clinical methodological review, the reporting structure of the PRISMA 2020 statement (Page et al., 2021), covering eligibility criteria, information sources, search strategy, selection process, data extraction, and synthesis method, each reported below."),
  heading("2.2 Eligibility criteria", HeadingLevel.HEADING_2),
  p("Eligible records were peer-reviewed journal articles, conference papers, and scholarly books or book chapters that (a) present, review, compare, or historically contextualize a spatial-analytical method applied to point, line/network, or polygon/areal geographic data, or (b) provide bibliometric or historiographic evidence on the development of GIScience or one of its analytical subfields. Records were excluded where the returned title and abstract indicated only incidental or purely applied use of a method without methodological, comparative, or historical content of its own; where the match appeared to be a citation-list or back-matter artifact rather than substantive content; where no usable abstract or summary was returned; or where the record was not in English. No publication-date restriction was applied a priori, so as to capture foundational mid-twentieth-century contributions alongside 2025–2026 developments."),
  heading("2.3 Information sources", HeadingLevel.HEADING_2),
  p("Records were identified using a single discovery tool, Consensus (consensus.app), an academic search engine built on the Semantic Scholar corpus, accessed programmatically on 28 July 2026. Direct programmatic access to Scopus, Web of Science, PubMed, or IEEE Xplore was not available in the review environment. This single-source constraint is reported here in the interest of PRISMA-consistent transparency about information sources and is discussed as a limitation in Section 5."),
  heading("2.4 Search strategy", HeadingLevel.HEADING_2),
  p("Nine structured queries were run, grouped to cover each of the three spatial data models plus cross-cutting themes (GIScience historiography; GeoAI and big data). Two queries (Q2, Q3) failed due to API rate-limiting and were not retried; they are reported here rather than silently dropped, consistent with transparent search reporting. The seven successful queries returned 20 records each (the tool's per-query display maximum)."),
  searchTable(),
  caption("Table 1. Search queries executed against the Consensus/Semantic Scholar corpus on 28 July 2026."),
  heading("2.5 Selection process", HeadingLevel.HEADING_2),
  p("Records were screened in a single pass against the eligibility criteria using the title, source venue, and the abstract or summary text returned by the search tool; full text was not retrieved for any record. Screening was performed by a single reviewer (the author, assisted by an AI research agent) without independent dual screening or an inter-rater reliability statistic, a deviation from full PRISMA rigor that is noted in Section 5."),
  heading("2.6 Data extraction and synthesis", HeadingLevel.HEADING_2),
  p("For each included record, the following were extracted: first author, year, venue, primary spatial data model addressed (point, line/network, polygon/areal, or cross-cutting), and the methodological theme(s) it contributes to this review's narrative. Given the heterogeneity of included record types — empirical methods papers, narrative and systematic reviews, textbooks, and bibliometric analyses — a meta-analytic (effect-size) synthesis was not appropriate. We instead performed a narrative synthesis, organized chronologically within each of the three data-model trajectories (Sections 3.1–3.3), followed by a thematic synthesis of cross-cutting drivers of change (Section 3.4)."),
  heading("2.7 Record flow", HeadingLevel.HEADING_2),
  prismaTable(),
  caption("Table 2. PRISMA-adapted record flow. Counts reflect a single-source, abstract-level review; see Section 5 for the implications of this design."),
];

fs.writeFileSync("./partial_intro_methods.json", JSON.stringify({ ok: true }));
module.exports = { titleBlock, abstract, intro, methods, p, heading, caption };
