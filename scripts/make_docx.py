#!/usr/bin/env python3
"""
Render manuscript/main.tex to manuscript/main.docx.

Converts the specific LaTeX subset used by this manuscript (sections, inline
emphasis, itemize/enumerate, figures, \\input-ed tables, \\citep/\\ref) so that
the Word version is generated from the same source as the LaTeX version and
cannot drift from it.
"""
import os
import re
import csv

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt, Inches, RGBColor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAN = os.path.join(ROOT, "manuscript")
FIG = os.path.join(ROOT, "figures")
TAB = os.path.join(ROOT, "tables")

# --------------------------------------------------------------- bibliography
def load_bib():
    txt = open(os.path.join(MAN, "references.bib")).read()
    out = {}
    for m in re.finditer(r"@(\w+)\{([^,]+),(.*?)\n\}", txt, re.S):
        kind, key, body = m.groups()
        fields = dict(re.findall(r"(\w+)\s*=\s*\{(.*?)\}(?=,\s*\n|\s*$)",
                                 body, re.S))
        out[key] = {k: re.sub(r"\s+", " ", v).strip()
                    for k, v in fields.items()}
        out[key]["_type"] = kind
    return out


BIB = load_bib()


def surname(author_field):
    first = author_field.split(" and ")[0].strip()
    parts = first.split()
    # entries are stored as "Surname Initials"; drop a trailing initial block
    if len(parts) > 1 and re.fullmatch(r"[A-Z]{1,3}", parts[-1]):
        parts = parts[:-1]
    return " ".join(parts) or first


def cite_text(keys):
    out = []
    for k in keys:
        e = BIB.get(k)
        if not e:
            out.append(k)
            continue
        a = e.get("author", "")
        n = len([x for x in a.split(" and ") if x.strip()])
        s = surname(a)
        if "others" in a or n > 2:
            s += " et al."
        elif n == 2:
            s += " & " + surname(a.split(" and ")[1])
        out.append(f"{s} {e.get('year','')}")
    return "(" + "; ".join(out) + ")"


def bib_string(key):
    e = BIB[key]
    a = e.get("author", "").replace(" and others", " et al.")
    a = ", ".join(x.strip() for x in a.split(" and "))
    venue = (e.get("journal") or e.get("booktitle") or e.get("publisher")
             or e.get("school") or e.get("howpublished") or "")
    url = ""
    mu = re.search(r"\\url\{(.*?)\}", e.get("note", ""))
    if mu:
        url = mu.group(1)
    return f"{a} ({e.get('year','')}). {e.get('title','')}. {venue}. {url}"


# ------------------------------------------------------------- inline parsing
def clean_tex(s):
    s = s.replace("~", " ")
    s = re.sub(r"\\label\{[^}]*\}", "", s)
    s = re.sub(r"\\%", "%", s)
    s = re.sub(r"\\&", "&", s)
    s = re.sub(r"\\_", "_", s)
    s = re.sub(r"\\#", "#", s)
    s = re.sub(r"\\times", "x", s)
    s = re.sub(r"\\geq", "\u2265", s)
    s = re.sub(r"\\leq", "\u2264", s)
    s = re.sub(r"\\rightarrow", "\u2192", s)
    s = re.sub(r"\\itemsep\s*[\d.]*pt", "", s)
    s = re.sub(r"\\(?:maketitle|noindent|centering|small)\b", "", s)
    s = re.sub(r"\\vspace\*?\{[^}]*\}", "", s)
    s = s.replace("---", "\u2014").replace("--", "\u2013")
    s = s.replace("``", "\u201c").replace("''", "\u201d")
    s = re.sub(r"\$([^$]*)\$", lambda m: re.sub(r"[\\{}^]", "", m.group(1)), s)
    return s


TOKEN = re.compile(
    r"\\(?:citep|cite)\{([^}]*)\}"
    r"|\\(textbf|emph|textit|texttt)\{([^{}]*)\}"
    r"|\\ref\{([^}]*)\}")


def add_runs(par, text, refs, base_size=10.5):
    text = clean_tex(text)
    pos = 0
    for m in TOKEN.finditer(text):
        if m.start() > pos:
            par.add_run(text[pos:m.start()])
        if m.group(1) is not None:                       # citation
            par.add_run(cite_text([k.strip() for k in m.group(1).split(",")]))
        elif m.group(2) is not None:                     # styled span
            r = par.add_run(m.group(3))
            if m.group(2) == "textbf":
                r.bold = True
            elif m.group(2) in ("emph", "textit"):
                r.italic = True
            else:
                r.font.name = "Consolas"
        else:                                            # cross-reference
            par.add_run(refs.get(m.group(4), "?"))
        pos = m.end()
    par.add_run(text[pos:])
    for r in par.runs:
        r.font.size = Pt(base_size)


# ------------------------------------------------------------------- tables
def read_table_csv(name):
    path = os.path.join(TAB, name + ".csv")
    with open(path, newline="") as fh:
        return list(csv.reader(fh))


TABLE_CAPTIONS = {}


def add_table(doc, texname, number, refs):
    tex = open(os.path.join(TAB, texname + ".tex")).read()
    cap = re.search(r"\\caption\{(.*?)\}\n", tex, re.S)
    lab = re.search(r"\\label\{(.*?)\}", tex)
    note = re.search(r"\\scriptsize (.*?)\\end\{minipage\}", tex, re.S)
    caption = clean_tex(re.sub(r"\s+", " ", cap.group(1))) if cap else ""
    if lab:
        refs[lab.group(1)] = str(number)

    p = doc.add_paragraph()
    r = p.add_run(f"Table {number}. ")
    r.bold = True
    r.font.size = Pt(9.5)
    r2 = p.add_run(caption)
    r2.font.size = Pt(9.5)

    rows = read_table_csv(texname)
    t = doc.add_table(rows=len(rows), cols=len(rows[0]))
    t.style = "Table Grid"
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            cell = t.cell(i, j)
            cell.text = ""
            par = cell.paragraphs[0]
            run = par.add_run(clean_tex(re.sub(r"\\[a-zA-Z]+", "", val)))
            run.font.size = Pt(7.5)
            if i == 0:
                run.bold = True
    if note:
        p = doc.add_paragraph()
        r = p.add_run("Note: " + clean_tex(re.sub(r"\s+", " ", note.group(1))))
        r.font.size = Pt(8)
        r.italic = True
    doc.add_paragraph()


# -------------------------------------------------------------------- driver
def prepass(body):
    """Assign figure and table numbers to labels."""
    refs, fign, tabn = {}, 0, 0
    for m in re.finditer(r"\\begin\{figure\}(.*?)\\end\{figure\}"
                         r"|\\input\{\.\./tables/(\w+)\.tex\}", body, re.S):
        if m.group(1) is not None:
            fign += 1
            lab = re.search(r"\\label\{(.*?)\}", m.group(1))
            if lab:
                refs[lab.group(1)] = str(fign)
        else:
            tabn += 1
            tex = open(os.path.join(TAB, m.group(2) + ".tex")).read()
            lab = re.search(r"\\label\{(.*?)\}", tex)
            if lab:
                refs[lab.group(1)] = str(tabn)
    return refs


def main():
    src = open(os.path.join(MAN, "main.tex")).read()
    body = src.split(r"\begin{document}")[1].split(r"\end{document}")[0]

    title = re.search(r"\\title\{\\textbf\{(.*?)\}\}", src, re.S).group(1)
    author = re.search(r"\\author\[1\]\{(.*?)\}", src).group(1)
    affil = re.search(r"\\affil\[1\]\{\\small (.*?)\}", src).group(1)

    refs = prepass(body)

    doc = Document()
    st = doc.styles["Normal"]
    st.font.name = "Calibri"
    st.font.size = Pt(10.5)
    for s in doc.sections:
        s.left_margin = s.right_margin = Inches(1.0)
        s.top_margin = s.bottom_margin = Inches(1.0)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(clean_tex(re.sub(r"\s+", " ", title)))
    r.bold = True
    r.font.size = Pt(15)
    for txt, sz in ((author, 11), (affil, 9.5)):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        rr = p.add_run(clean_tex(txt))
        rr.font.size = Pt(sz)
        if sz < 10:
            rr.italic = True
    doc.add_paragraph()

    fign = tabn = 0
    i = 0
    # split the body into structural blocks
    blocks = re.split(r"(\\(?:sub)?section\*?\{[^}]*\}"
                      r"|\\begin\{figure\}.*?\\end\{figure\}"
                      r"|\\begin\{(?:itemize|enumerate)\}.*?"
                      r"\\end\{(?:itemize|enumerate)\}"
                      r"|\\input\{\.\./tables/\w+\.tex\}"
                      r"|\\clearpage|\\newpage|\\bibliography\{\w+\})",
                      body, flags=re.S)

    for blk in blocks:
        if not blk or not blk.strip():
            continue
        b = blk.strip()

        m = re.match(r"\\(sub)?section\*?\{(.*?)\}$", b, re.S)
        if m:
            lvl = 2 if m.group(1) else 1
            doc.add_heading(clean_tex(m.group(2)), level=lvl)
            continue

        if b.startswith(r"\begin{figure}"):
            fign += 1
            img = re.search(r"\\includegraphics\[[^\]]*\]\{(.*?)\}", b)
            cap = re.search(r"\\caption\{(.*?)\}\s*\\label", b, re.S)
            if img:
                png = os.path.join(FIG, img.group(1).replace(".pdf", ".png"))
                if os.path.exists(png):
                    doc.add_picture(png, width=Inches(6.3))
                    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
            p = doc.add_paragraph()
            r = p.add_run(f"Figure {fign}. ")
            r.bold = True
            r.font.size = Pt(9.5)
            if cap:
                add_runs(p, re.sub(r"\s+", " ", cap.group(1)), refs, 9.5)
            doc.add_paragraph()
            continue

        m = re.match(r"\\begin\{(itemize|enumerate)\}(.*)\\end\{\1\}$", b, re.S)
        if m:
            inner = re.sub(r"\\itemsep\s*[\d.]*pt", "", m.group(2))
            style = ("List Bullet" if m.group(1) == "itemize"
                     else "List Number")
            for item in re.split(r"\\item", inner)[1:]:
                if not item.strip():
                    continue
                p = doc.add_paragraph(style=style)
                add_runs(p, item.strip(), refs)
            continue

        m = re.match(r"\\input\{\.\./tables/(\w+)\.tex\}$", b)
        if m:
            tabn += 1
            add_table(doc, m.group(1), tabn, refs)
            continue

        if b.startswith(r"\bibliography"):
            doc.add_heading("References", level=1)
            used = set()
            for c in re.findall(r"\\citep?\{([^}]*)\}", body):
                used |= {k.strip() for k in c.split(",")}
            for k in sorted(used, key=lambda k: (surname(BIB[k].get("author", "")),
                                                 BIB[k].get("year", ""))):
                p = doc.add_paragraph()
                p.paragraph_format.left_indent = Inches(0.3)
                p.paragraph_format.first_line_indent = Inches(-0.3)
                r = p.add_run(bib_string(k))
                r.font.size = Pt(9)
            continue

        if b in (r"\clearpage", r"\newpage"):
            doc.add_page_break()
            continue

        for para in re.split(r"\n\s*\n", b):
            para = para.strip()
            if not para or para.startswith("%"):
                continue
            p = doc.add_paragraph()
            p.paragraph_format.space_after = Pt(6)
            add_runs(p, re.sub(r"\s+", " ", para), refs)

    out = os.path.join(MAN, "main.docx")
    doc.save(out)
    print(f"wrote {out}  ({fign} figures, {tabn} tables)")


if __name__ == "__main__":
    main()
