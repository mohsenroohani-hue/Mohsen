const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType,
  ExternalHyperlink, UnderlineType, convertInchesToTwip, PageNumber, Footer,
} = require("docx");
const fs = require("fs");
const REFS = require("./refs.js");
const { titleBlock, abstract, intro, methods, heading, p } = require("./build.js");
const { results, discussion, limitations, conclusion } = require("./build2.js");

const FONT = "Calibri";

function referenceParagraph([label, text, url]) {
  // Split citation text at the first ". " after the year-parenthesis to bold nothing;
  // just render as hanging-indent paragraph, with hyperlink wrapping full text if url present.
  const runOrLink = url
    ? new ExternalHyperlink({
        link: url,
        children: [new TextRun({ text, font: FONT, size: 20, color: "1155CC", underline: { type: UnderlineType.SINGLE } })],
      })
    : new TextRun({ text, font: FONT, size: 20 });
  return new Paragraph({
    indent: { left: convertInchesToTwip(0.5), hanging: convertInchesToTwip(0.5) },
    spacing: { after: 140, line: 264 },
    children: [runOrLink],
  });
}

const referencesSection = [
  heading("References", HeadingLevel.HEADING_1),
  p("Full bibliographic details (volume, issue, and page numbers) were not consistently returned by the search tool; where available they are included above. Each entry below is hyperlinked to its record on the Consensus academic search platform (consensus.app), used as the discovery tool for this review (see Section 2.3), for reader verification.", { italics: true }),
  ...REFS.map(referenceParagraph),
];

const doc = new Document({
  styles: {
    default: {
      document: { run: { font: FONT, size: 22 } },
      heading1: { run: { font: FONT, bold: true, size: 30, color: "1F3864" }, paragraph: { spacing: { before: 360, after: 180 } } },
      heading2: { run: { font: FONT, bold: true, size: 26, color: "2E5395" }, paragraph: { spacing: { before: 280, after: 140 } } },
    },
  },
  sections: [
    {
      properties: {
        page: {
          size: { width: 12240, height: 15840 }, // US Letter
          margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 },
        },
      },
      footers: {
        default: new Footer({
          children: [new Paragraph({
            alignment: AlignmentType.CENTER,
            children: [new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 18 })],
          })],
        }),
      },
      children: [
        ...titleBlock,
        ...abstract,
        ...intro,
        ...methods,
        ...results,
        ...discussion,
        ...limitations,
        ...conclusion,
        ...referencesSection,
      ],
    },
  ],
});

Packer.toBuffer(doc).then((buffer) => {
  fs.writeFileSync("./Trajectories_of_Spatial_Analysis_Systematic_Review.docx", buffer);
  console.log("Written.");
});
