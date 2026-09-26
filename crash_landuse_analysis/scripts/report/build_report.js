// Builds outputs/Crash_LandUse_Spatial_Analysis_Report.docx
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, AlignmentType, HeadingLevel, TableOfContents, Footer, Header,
  PageNumber, PageOrientation, LevelFormat, BorderStyle,
} = require("docx");
const H = require("./helpers");
const { P, H1, H1nb, H2, H3, bullets, numbered, figure, table, pageBreak, callout, DATA } = H;
const S = require("./sections");

const PORTRAIT = { size: { width: 12240, height: 15840 }, margin: { top: 1440, right: 1440, bottom: 1300, left: 1440 } };
const LANDSCAPE = { size: { width: 12240, height: 15840, orientation: PageOrientation.LANDSCAPE },
  margin: { top: 1080, right: 1080, bottom: 1080, left: 1080 } };

const footer = new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [
  new TextRun({ text: "Land use × crash type × severity — spatial analysis   |   page ", size: 16, color: "898781" }),
  new TextRun({ children: [PageNumber.CURRENT], size: 16, color: "898781" }),
] })] });

const titlePage = [
  new Paragraph({ spacing: { before: 2400, after: 200 }, children: [new TextRun({ text: "Land Use and the Geography of Crash Types and Severity on Florida Arterials", bold: true, size: 44, color: "0D366B" })] }),
  new Paragraph({ spacing: { after: 400 }, children: [new TextRun({ text: "Which spatial methods fit the data, how to run them in QGIS, ArcGIS Pro and GeoDa, and what they show — separate results for Fatal, KSI, KAB and Total crashes, for every land use and crash type", size: 26, color: "52514E" })] }),
  new Paragraph({ border: { bottom: { style: BorderStyle.SINGLE, size: 12, color: "2A78D6", space: 4 } }, children: [] }),
  P("**Study units:** 489 arterial intersections and 334 arterial segments on ten corridors in six Florida counties (Pinellas, Pasco, Hillsborough, Orange, Palm Beach, Broward); four years of crashes.", { before: 300 }),
  P("**Dependent variables:** 12 crash types (angle, left turn, right turn, rear end, sideswipe, head on, run-off-road, rollover, single vehicle, pedestrian, bicycle; plus alcohol-involved) and all crashes, each at four severity levels (Fatal = K, KSI = K+A, KAB = K+A+B, Total)."),
  P("**Explanatory focus:** 19 land uses counted at each site, analysed one at a time and jointly, net of exposure, roadway design and neighbourhood context."),
  P("**Deliverables:** this report; an Excel workbook with every estimate; a GeoPackage and GeoDa weights files ready for QGIS / ArcGIS Pro / GeoDa; reproducible Python scripts.", { after: 600 }),
  P("Analysis date: 26 September 2026", { run: { color: "898781" } }),
  pageBreak(),
  new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("Contents")] }),
  new TableOfContents("Contents", { hyperlink: true, headingStyleRange: "1-2" }),
  P("(In Word: right-click the table of contents and choose Update Field to refresh page numbers.)", { run: { size: 16, color: "898781" } }),
];

const doc = new Document({
  creator: "Claude Code",
  title: "Land use and crash type × severity: spatial analysis",
  features: { updateFields: true },
  styles: {
    default: { document: { run: { font: "Calibri", size: 21, color: "1F1F1F" } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 32, bold: true, font: "Calibri", color: "0D366B" },
        paragraph: { spacing: { before: 240, after: 160 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 26, bold: true, font: "Calibri", color: "1C5CAB" },
        paragraph: { spacing: { before: 240, after: 120 }, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 22, bold: true, font: "Calibri", color: "1F1F1F" },
        paragraph: { spacing: { before: 180, after: 80 }, outlineLevel: 2 } },
    ],
  },
  numbering: { config: [
    { reference: "bullets", levels: [
      { level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 270 } } } },
      { level: 1, format: LevelFormat.BULLET, text: "–", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 1080, hanging: 270 } } } },
    ] },
    { reference: "numbers", levels: [
      { level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 300 } } } },
    ] },
  ] },
  sections: [
    { properties: { page: PORTRAIT }, children: titlePage },
    { properties: { page: PORTRAIT }, footers: { default: footer }, children: S.main() },
    { properties: { page: LANDSCAPE }, footers: { default: footer }, children: S.appendixTables() },
    { properties: { page: PORTRAIT }, footers: { default: footer }, children: S.appendixAtlas() },
  ],
});

const out = path.resolve(__dirname, "..", "..", "outputs", "Crash_LandUse_Spatial_Analysis_Report.docx");
Packer.toBuffer(doc).then((buf) => { fs.writeFileSync(out, buf); const stable = H.saveRegistry(); console.log("written", out, "xref stable:", stable); });
