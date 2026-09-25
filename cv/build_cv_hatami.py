"""Build the CV PDF for Yaser Hatami from publicly listed ORCID works.

Reuses the layout helpers from build_cv.py.
Usage: python3 cv/build_cv_hatami.py   (requires: pip install reportlab)
"""
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import (Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

from build_cv import (MUTED, body, bullets, contact_style, entry, name_style,
                      pub, section, small, title_style)

OUT = Path(__file__).with_name("Yaser_Hatami_CV.pdf")
NAME = "Yaser Hatami"
ME = "<b>Hatami, Y.</b>"

# (year, citation) — newest first. Sources: ORCID 0000-0002-0161-9345 and
# publisher pages for each article.
JOURNAL_ARTICLES = [
    ("2026", f"{ME}, Zali, N., &amp; Barati, N. Populist urbanism and the speculation "
             "network: Discourse, conflict, and planning monopoly in Hamadan. "
             "<i>Journal of Urban Management</i>."),
    ("2026", f"Roohani Qadikolaei, M., {ME}, Nikmard Namin, S., &amp; Soltani, A. Spatial "
             "heterogeneity in housing price-transaction ratios: A historical analysis of "
             "Tehran. <i>International Journal of Housing Markets and Analysis</i>, 19(2), "
             "426&#8211;452. doi:10.1108/IJHMA-08-2024-0118"),
    ("2025", f"{ME}, Zali, N., &amp; Barati, N. Antagonism of spatial planning and the process "
             "of urban counter-development: An empirical study in Hamadan. <i>Space and "
             "Polity</i>, 29(3), 189&#8211;213. doi:10.1080/13562576.2025.2585813"),
    ("2025", f"Roohani Qadikolaei, M., Soltani, A., Nikmard Namin, S., {ME}, &amp; Najafi, P. "
             "Explaining air pollution exceedance days through land use densities. "
             "<i>Environmental and Sustainability Indicators</i>, 26, 100691."),
    ("2025", f"{ME}, Zali, N., &amp; Barati, N. Bridging the gap in urban studies: Combining "
             "topic modeling and discourse theory in big data analysis. <i>International "
             "Journal of Urban Sciences</i>, 30(2), 294&#8211;324. "
             "doi:10.1080/12265934.2025.2504674"),
]

INTERESTS = [
    "Planning theory, discourse theory and agonistic planning",
    "Urban politics, populism and spatial governance",
    "Speculative urbanism, land-use conflict and territorial expansion",
    "Media and public discourse on urban development",
    "Computational text analysis and big data in urban studies",
    "Housing markets and environmental quality in Iranian cities",
]

METHODS = [
    ("Discourse analysis", "Post-structuralist discourse theory (Laclau &amp; Mouffe), "
                           "qualitative media analysis of large text corpora"),
    ("Computational methods", "Topic modelling, text mining and big-data analysis of "
                              "newspaper and media archives"),
    ("Quantitative analysis", "Generalised linear mixed models, spatial clustering, "
                              "land-use density indicators"),
    ("Case expertise", "Urban development conflicts in Hamadan; housing and air quality in "
                       "Tehran"),
]


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Body", 8)
    canvas.setFillColor(MUTED)
    canvas.drawString(doc.leftMargin, 10 * mm, f"{NAME} — Curriculum Vitae")
    canvas.drawRightString(A4[0] - doc.rightMargin, 10 * mm, f"Page {doc.page}")
    canvas.restoreState()


def build():
    doc = SimpleDocTemplate(str(OUT), pagesize=A4, leftMargin=18 * mm,
                            rightMargin=18 * mm, topMargin=14 * mm,
                            bottomMargin=16 * mm, title=f"{NAME} — CV", author=NAME)
    s = []
    s.append(Paragraph(NAME, name_style))
    s.append(Paragraph("Urban Planning Researcher · PhD Researcher, University of Guilan",
                       title_style))
    s.append(Spacer(1, 3))
    s.append(Paragraph(
        "Department of Urban Planning, University of Guilan, Rasht, Iran<br/>"
        "ORCID: <link href='https://orcid.org/0000-0002-0161-9345' color='#1F4E79'>"
        "0000-0002-0161-9345</link> · "
        "Google Scholar: <link href='https://scholar.google.com/citations?user=0jJpi3gAAAAJ' "
        "color='#1F4E79'>0jJpi3gAAAAJ</link>",
        contact_style))

    s += section("Profile")
    s.append(Paragraph(
        "Urban studies researcher working on planning theory, discourse analysis and spatial "
        "governance. Research examines how populist and antagonistic discourses shape urban "
        "planning conflicts and legitimise speculative development, using Hamadan (Iran) as "
        "the main case. Develops mixed methods that combine post-structuralist discourse "
        "theory with topic modelling to analyse thousands of media texts. Also contributes to "
        "quantitative studies of housing markets and air quality in Tehran. Collaborates "
        "with Dr Nader Zali (University of Guilan) and Dr Nasser Barati (Soore University, "
        "Tehran).", body))

    s += section("Education")
    s.append(entry("PhD, Urban Planning", "University of Guilan, Iran",
                   "Department of Urban Planning"))

    s += section("Research Interests")
    s.append(bullets(INTERESTS))

    s += section("Methods &amp; Skills")
    rows = [[Paragraph(f"<b>{k}</b>", body), Paragraph(v, body)] for k, v in METHODS]
    t = Table(rows, colWidths=[42 * mm, None])
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
    ]))
    s.append(t)

    s += section("Peer-Reviewed Journal Articles")
    n = len(JOURNAL_ARTICLES)
    rows = [[Paragraph(f"[{n - i}]", small), Paragraph(year, small), Paragraph(cite, pub)]
            for i, (year, cite) in enumerate(JOURNAL_ARTICLES)]
    t = Table(rows, colWidths=[9 * mm, 11 * mm, None])
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
    ]))
    s.append(t)

    s.append(Spacer(1, 6))
    s.append(Paragraph("Publication list compiled from the ORCID record 0000-0002-0161-9345.",
                       small))
    doc.build(s, onFirstPage=footer, onLaterPages=footer)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    build()
