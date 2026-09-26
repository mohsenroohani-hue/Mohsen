// Shared docx-js helpers for the report.
const fs = require("fs");
const path = require("path");
const {
  Paragraph, TextRun, HeadingLevel, AlignmentType, ImageRun, Table, TableRow, TableCell,
  WidthType, ShadingType, BorderStyle, VerticalAlign, PageBreak,
} = require("docx");

const ROOT = path.resolve(__dirname, "..", "..");
const FIG = path.join(ROOT, "outputs", "figures");
const DATA = JSON.parse(fs.readFileSync(path.join(ROOT, "outputs", "report_data.json"), "utf8"));

const FONT = "Calibri";
const INK = "1F1F1F";
const INK2 = "52514E";
const ACCENT = "1C5CAB";
const HDR_FILL = "DCE8F7";
const ALT_FILL = "F6F5F1";
const BORDER = { style: BorderStyle.SINGLE, size: 4, color: "C3C2B7" };

let figNo = 0;
let tabNo = 0;
// two-pass cross-references: numbers from the previous build pass
const REG_PATH = path.join(ROOT, "outputs", ".xref_registry.json");
const PREV = fs.existsSync(REG_PATH) ? JSON.parse(fs.readFileSync(REG_PATH, "utf8")) : {};
const REG = {};
function F(label) { return `Figure ${PREV["fig:" + label] ?? "?"}`; }
function T(label) { return `Table ${PREV["tab:" + label] ?? "?"}`; }
function saveRegistry() { fs.writeFileSync(REG_PATH, JSON.stringify(REG, null, 1)); return JSON.stringify(REG) === JSON.stringify(PREV); }

// **bold**, *italic* inline markup -> TextRuns
function runs(text, base = {}) {
  const out = [];
  // literal asterisks in statistic names (Gi*, G*) are not markup
  text = text.replace(/Gi\*/g, "Gi\u2217").replace(/\bG\*/g, "G\u2217");
  const re = /(\*\*(?!\s)[^*]+?(?<!\s)\*\*|\*(?![\s*])[^*]+?(?<![\s*])\*)/g;
  let last = 0;
  let m;
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) out.push(new TextRun({ text: text.slice(last, m.index), ...base }));
    const tok = m[0];
    if (tok.startsWith("**")) out.push(new TextRun({ text: tok.slice(2, -2), bold: true, ...base }));
    else out.push(new TextRun({ text: tok.slice(1, -1), italics: true, ...base }));
    last = m.index + tok.length;
  }
  if (last < text.length) out.push(new TextRun({ text: text.slice(last), ...base }));
  return out;
}

function P(text, opts = {}) {
  return new Paragraph({
    children: runs(text, opts.run || {}),
    spacing: { after: opts.after ?? 120, before: opts.before ?? 0, line: opts.line ?? 276 },
    alignment: opts.align || AlignmentType.LEFT,
    keepNext: opts.keepNext,
  });
}

function H1(text) {
  return new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(text)], pageBreakBefore: true });
}
function H1nb(text) {
  return new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(text)] });
}
function H2(text, pageBreakBefore = false) {
  return new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun(text)], keepNext: true, pageBreakBefore });
}
function H3(text) {
  return new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun(text)], keepNext: true });
}

function bullets(items, level = 0) {
  return items.map((t) => new Paragraph({
    numbering: { reference: "bullets", level },
    children: runs(t),
    spacing: { after: 60, line: 264 },
  }));
}

let numInstance = 0;
function numbered(items) {
  numInstance += 1;
  const inst = numInstance;
  return items.map((t) => new Paragraph({
    numbering: { reference: "numbers", level: 0, instance: inst },
    children: runs(t),
    spacing: { after: 60, line: 264 },
  }));
}

function pngSize(file) {
  const b = fs.readFileSync(file);
  return { w: b.readUInt32BE(16), h: b.readUInt32BE(20) };
}

// widthIn: display width in inches
function figure(name, caption, widthIn = 6.5, maxHeightIn = 8.2) {
  const file = path.join(FIG, name);
  if (!fs.existsSync(file)) {
    return [P(`[missing figure: ${name}]`)];
  }
  figNo += 1;
  REG["fig:" + name] = figNo;
  const { w, h } = pngSize(file);
  let wpx = widthIn * 96;
  let hpx = wpx * (h / w);
  if (hpx > maxHeightIn * 96) {
    hpx = maxHeightIn * 96;
    wpx = hpx * (w / h);
  }
  return [
    new Paragraph({
      alignment: AlignmentType.CENTER,
      keepNext: true,
      spacing: { before: 120, after: 60 },
      children: [new ImageRun({
        type: "png", data: fs.readFileSync(file),
        transformation: { width: Math.round(wpx), height: Math.round(hpx) },
        altText: { title: `Figure ${figNo}`, description: caption.replace(/\*/g, ""), name: name },
      })],
    }),
    new Paragraph({
      spacing: { after: 200 },
      children: [new TextRun({ text: `Figure ${figNo}. `, bold: true, size: 18, color: INK }),
        ...runs(caption, { size: 18, color: INK2 })],
    }),
  ];
}

function cell(text, width, opts = {}) {
  return new TableCell({
    width: { size: width, type: WidthType.DXA },
    shading: opts.fill ? { fill: opts.fill, type: ShadingType.CLEAR, color: "auto" } : undefined,
    margins: { top: 40, bottom: 40, left: 70, right: 70 },
    verticalAlign: VerticalAlign.CENTER,
    columnSpan: opts.span,
    children: [new Paragraph({
      alignment: opts.align || AlignmentType.LEFT,
      spacing: { after: 0, line: 240 },
      children: [new TextRun({ text: String(text), size: opts.size || 16, bold: opts.bold, color: opts.color || INK })],
    })],
  });
}

// header: array of strings (or array of arrays for multi-row header: [{text, span}])
function table(caption, header, rows, widths, opts = {}) {
  tabNo += 1;
  if (opts.label) REG["tab:" + opts.label] = tabNo;
  const total = widths.reduce((a, b) => a + b, 0);
  const size = opts.size || 16;
  const hdrRows = (Array.isArray(header[0]) ? header : [header]).map((hr) => new TableRow({
    tableHeader: true,
    children: (() => {
      let col = 0;
      return hr.map((h) => {
        const t = typeof h === "string" ? { text: h } : h;
        const span = t.span || 1;
        const w = widths.slice(col, col + span).reduce((a, b) => a + b, 0);
        col += span;
        return cell(t.text, w, { fill: HDR_FILL, bold: true, size, span: span > 1 ? span : undefined,
          align: col - span === 0 ? AlignmentType.LEFT : AlignmentType.CENTER });
      });
    })(),
  }));
  const body = rows.map((r, i) => new TableRow({
    cantSplit: true,
    children: r.map((v, j) => cell(v, widths[j], {
      size,
      fill: opts.zebra !== false && i % 2 === 1 ? ALT_FILL : undefined,
      align: j === 0 || (opts.leftCols || []).includes(j) ? AlignmentType.LEFT : AlignmentType.CENTER,
      bold: (opts.boldFirst && j === 0),
    })),
  }));
  const out = [];
  out.push(new Paragraph({
    keepNext: true,
    spacing: { before: 160, after: 80 },
    children: [new TextRun({ text: `Table ${tabNo}. `, bold: true, size: 18, color: INK }),
      ...runs(caption, { size: 18, color: INK2 })],
  }));
  out.push(new Table({
    width: { size: total, type: WidthType.DXA },
    columnWidths: widths,
    borders: { top: BORDER, bottom: BORDER, left: BORDER, right: BORDER,
      insideHorizontal: BORDER, insideVertical: BORDER },
    rows: [...hdrRows, ...body],
  }));
  if (opts.note) out.push(P(opts.note, { run: { size: 15, color: INK2 }, before: 60, after: 200 }));
  else out.push(new Paragraph({ spacing: { after: 160 }, children: [] }));
  return out;
}

function pageBreak() {
  return new Paragraph({ children: [new PageBreak()] });
}

function callout(title, lines) {
  // single-cell shaded box for key messages
  const w = 9360;
  return [new Table({
    width: { size: w, type: WidthType.DXA },
    columnWidths: [w],
    borders: { top: { style: BorderStyle.SINGLE, size: 12, color: ACCENT }, bottom: BORDER,
      left: BORDER, right: BORDER, insideHorizontal: BORDER, insideVertical: BORDER },
    rows: [new TableRow({ children: [new TableCell({
      width: { size: w, type: WidthType.DXA },
      shading: { fill: "EEF4FC", type: ShadingType.CLEAR, color: "auto" },
      margins: { top: 100, bottom: 100, left: 160, right: 160 },
      children: [
        new Paragraph({ spacing: { after: 80 }, children: [new TextRun({ text: title, bold: true, color: ACCENT, size: 21 })] }),
        ...lines.map((t) => new Paragraph({ numbering: { reference: "bullets", level: 0 }, spacing: { after: 50, line: 260 }, children: runs(t, { size: 19 }) })),
      ],
    })] })],
  }), new Paragraph({ spacing: { after: 160 }, children: [] })];
}

module.exports = { F, T, saveRegistry, P, H1, H1nb, H2, H3, bullets, numbered, figure, table, pageBreak, callout, runs, DATA, FONT, INK, INK2, ACCENT, FIG };
