/*
 * md_to_docx.js
 * Converts the review manuscript (Markdown) into a submission-ready .docx,
 * including headings, tables, lists, code blocks and the 16 figures.
 *
 *   node analysis/md_to_docx.js manuscript/<file>.md manuscript/<file>.docx
 */
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, Table, TableRow,
  TableCell, WidthType, ShadingType, AlignmentType, BorderStyle, PageBreak,
  ImageRun, PageOrientation,
} = require("docx");

const SRC = process.argv[2];
const OUT = process.argv[3];
const ROOT = path.dirname(path.dirname(path.resolve(SRC)));

// US Letter, 1 inch margins
const PAGE_W = 12240, MARGIN = 1440;
const CONTENT_W = PAGE_W - 2 * MARGIN;   // 9360 DXA

const lines = fs.readFileSync(SRC, "utf8").split("\n");

/* ---------- inline formatting ------------------------------------------- */
function runs(text, base = {}) {
  const out = [];
  // tokenise **bold**, *italic*, `code`
  const re = /(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)/g;
  let last = 0, m;
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) out.push(new TextRun({ text: text.slice(last, m.index), ...base }));
    const tok = m[0];
    if (tok.startsWith("**")) {
      out.push(new TextRun({ text: tok.slice(2, -2), bold: true, ...base }));
    } else if (tok.startsWith("`")) {
      out.push(new TextRun({ text: tok.slice(1, -1), font: "Courier New", size: 18, ...base }));
    } else {
      out.push(new TextRun({ text: tok.slice(1, -1), italics: true, ...base }));
    }
    last = m.index + tok.length;
  }
  if (last < text.length) out.push(new TextRun({ text: text.slice(last), ...base }));
  return out.length ? out : [new TextRun({ text: "", ...base })];
}

/* ---------- table builder ------------------------------------------------ */
function splitRow(line) {
  return line.trim().replace(/^\|/, "").replace(/\|$/, "").split("|").map((c) => c.trim());
}

function buildTable(block) {
  const header = splitRow(block[0]);
  const body = block.slice(2).map(splitRow);       // skip the --- separator
  const n = header.length;
  const colW = Math.floor(CONTENT_W / n);
  const widths = Array(n).fill(colW);
  widths[n - 1] = CONTENT_W - colW * (n - 1);      // must sum exactly

  const cell = (txt, isHeader) =>
    new TableCell({
      width: { size: widths[0], type: WidthType.DXA },
      shading: isHeader
        ? { type: ShadingType.CLEAR, fill: "EEEEEE" }
        : undefined,
      margins: { top: 60, bottom: 60, left: 90, right: 90 },
      children: [new Paragraph({
        spacing: { before: 0, after: 0 },
        children: runs(txt, { size: 17, bold: isHeader || undefined }),
      })],
    });

  const mkRow = (cells, isHeader) =>
    new TableRow({
      tableHeader: isHeader,
      children: cells.map((c, i) =>
        new TableCell({
          width: { size: widths[i], type: WidthType.DXA },
          shading: isHeader ? { type: ShadingType.CLEAR, fill: "EEEEEE" } : undefined,
          margins: { top: 60, bottom: 60, left: 90, right: 90 },
          children: [new Paragraph({
            spacing: { before: 0, after: 0 },
            children: runs(c, { size: 17, bold: isHeader || undefined }),
          })],
        })),
    });

  return new Table({
    columnWidths: widths,
    width: { size: CONTENT_W, type: WidthType.DXA },
    rows: [mkRow(header, true), ...body.map((r) => mkRow(r, false))],
  });
}

/* ---------- main walk ---------------------------------------------------- */
const children = [];
let i = 0;
while (i < lines.length) {
  const line = lines[i];

  // fenced code
  if (/^```/.test(line)) {
    i++;
    const buf = [];
    while (i < lines.length && !/^```/.test(lines[i])) buf.push(lines[i++]);
    i++;
    buf.forEach((t) =>
      children.push(new Paragraph({
        spacing: { before: 0, after: 0 },
        shading: { type: ShadingType.CLEAR, fill: "F5F5F5" },
        children: [new TextRun({ text: t || " ", font: "Courier New", size: 16 })],
      })));
    children.push(new Paragraph({ text: "", spacing: { after: 120 } }));
    continue;
  }

  // table
  if (/^\s*\|/.test(line) && i + 1 < lines.length && /^\s*\|[\s:|-]+\|?\s*$/.test(lines[i + 1])) {
    const blk = [];
    while (i < lines.length && /^\s*\|/.test(lines[i])) blk.push(lines[i++]);
    children.push(buildTable(blk));
    children.push(new Paragraph({ text: "", spacing: { after: 160 } }));
    continue;
  }

  // horizontal rule
  if (/^---+\s*$/.test(line)) {
    children.push(new Paragraph({
      spacing: { before: 120, after: 120 },
      border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: "BBBBBB" } },
      children: [new TextRun("")],
    }));
    i++;
    continue;
  }

  // headings
  const h = /^(#{1,4})\s+(.*)$/.exec(line);
  if (h) {
    const lvl = h[1].length;
    const map = { 1: HeadingLevel.TITLE, 2: HeadingLevel.HEADING_1,
                  3: HeadingLevel.HEADING_2, 4: HeadingLevel.HEADING_3 };
    children.push(new Paragraph({
      heading: map[lvl],
      spacing: { before: lvl <= 2 ? 320 : 220, after: 120 },
      keepNext: true,
      children: runs(h[2]),
    }));
    i++;
    continue;
  }

  // blockquote
  if (/^>\s?/.test(line)) {
    children.push(new Paragraph({
      spacing: { before: 120, after: 120 },
      indent: { left: 360 },
      border: { left: { style: BorderStyle.SINGLE, size: 12, color: "888888", space: 8 } },
      children: runs(line.replace(/^>\s?/, ""), { italics: true }),
    }));
    i++;
    continue;
  }

  // list items
  const ul = /^[-*]\s+(.*)$/.exec(line);
  const ol = /^(\d+)\.\s+(.*)$/.exec(line);
  if (ul || ol) {
    children.push(new Paragraph({
      spacing: { before: 40, after: 40 },
      indent: { left: 400, hanging: 220 },
      children: runs((ol ? `${ol[1]}.  ` : "•  ") + (ul ? ul[1] : ol[2])),
    }));
    i++;
    continue;
  }

  // blank
  if (!line.trim()) { i++; continue; }

  // paragraph
  children.push(new Paragraph({
    spacing: { before: 60, after: 120, line: 276 },
    alignment: AlignmentType.JUSTIFIED,
    children: runs(line),
  }));
  i++;
}

/* ---------- figure gallery ---------------------------------------------- */
children.push(new Paragraph({ children: [new PageBreak()] }));
children.push(new Paragraph({
  heading: HeadingLevel.HEADING_1,
  spacing: { after: 160 },
  children: runs("Figures"),
}));
children.push(new Paragraph({
  spacing: { after: 200 },
  children: runs("Each figure carries its title, legend, data source, method note and analytical " +
    "interpretation in-figure. 300 dpi source files are in figures/."),
}));

const figDir = path.join(ROOT, "figures");
const figs = fs.readdirSync(figDir).filter((f) => f.endsWith(".png")).sort();
const sizeOf = (buf) => ({ w: buf.readUInt32BE(16), h: buf.readUInt32BE(20) });  // PNG IHDR
for (const f of figs) {
  const buf = fs.readFileSync(path.join(figDir, f));
  const { w, h } = sizeOf(buf);
  const maxW = 620, maxH = 820;                    // points, inside Letter margins
  let dw = maxW, dh = Math.round((h / w) * maxW);
  if (dh > maxH) { dh = maxH; dw = Math.round((w / h) * maxH); }
  children.push(new Paragraph({
    spacing: { before: 120, after: 60 },
    alignment: AlignmentType.CENTER,
    children: [new ImageRun({ type: "png", data: buf, transformation: { width: dw, height: dh } })],
  }));
  children.push(new Paragraph({
    spacing: { after: 200 },
    alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: f, size: 15, color: "777777" })],
  }));
  children.push(new Paragraph({ children: [new PageBreak()] }));
}

/* ---------- assemble ----------------------------------------------------- */
const doc = new Document({
  creator: "Systematic review pipeline",
  title: "Trajectories of Point-Based Spatial Analysis, 2000-2027",
  styles: {
    default: {
      document: { run: { font: "Times New Roman", size: 22 } },
    },
    paragraphStyles: [
      { id: "Title", name: "Title", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 36, bold: true, font: "Times New Roman", color: "000000" },
        paragraph: { spacing: { after: 240 } } },
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 28, bold: true, font: "Times New Roman", color: "000000" } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 24, bold: true, font: "Times New Roman", color: "000000" } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 22, bold: true, italics: true, font: "Times New Roman", color: "000000" } },
    ],
  },
  sections: [{
    properties: {
      page: {
        size: { width: PAGE_W, height: 15840, orientation: PageOrientation.PORTRAIT },
        margin: { top: MARGIN, bottom: MARGIN, left: MARGIN, right: MARGIN },
      },
    },
    children,
  }],
});

Packer.toBuffer(doc).then((b) => {
  fs.writeFileSync(OUT, b);
  console.log(`wrote ${OUT} (${(b.length / 1e6).toFixed(1)} MB, ${figs.length} figures)`);
});
