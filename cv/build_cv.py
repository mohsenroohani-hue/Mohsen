"""Build CV.pdf for Mohsen Roohani Qadikolaei from publicly listed ORCID works.

Usage: python3 cv/build_cv.py   (requires: pip install reportlab)
"""
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (HRFlowable, KeepTogether, ListFlowable,
                                ListItem, Paragraph, SimpleDocTemplate, Spacer,
                                Table, TableStyle)

OUT = Path(__file__).with_name("Mohsen_Roohani_Qadikolaei_CV.pdf")

FONT_DIR = "/usr/share/fonts/truetype/liberation/"
pdfmetrics.registerFont(TTFont("Body", FONT_DIR + "LiberationSans-Regular.ttf"))
pdfmetrics.registerFont(TTFont("Body-Bold", FONT_DIR + "LiberationSans-Bold.ttf"))
pdfmetrics.registerFont(TTFont("Body-Italic", FONT_DIR + "LiberationSans-Italic.ttf"))
pdfmetrics.registerFont(TTFont("Body-BoldItalic", FONT_DIR + "LiberationSans-BoldItalic.ttf"))
pdfmetrics.registerFontFamily("Body", normal="Body", bold="Body-Bold",
                              italic="Body-Italic", boldItalic="Body-BoldItalic")

ACCENT = colors.HexColor("#1F4E79")
MUTED = colors.HexColor("#555555")

name_style = ParagraphStyle("name", fontName="Body-Bold", fontSize=22, leading=26,
                            textColor=ACCENT)
title_style = ParagraphStyle("title", fontName="Body", fontSize=11.5, leading=15,
                             textColor=MUTED)
contact_style = ParagraphStyle("contact", fontName="Body", fontSize=9, leading=12,
                               textColor=MUTED)
section_style = ParagraphStyle("section", fontName="Body-Bold", fontSize=12,
                               leading=15, textColor=ACCENT, spaceBefore=10,
                               spaceAfter=2)
body = ParagraphStyle("body", fontName="Body", fontSize=9.8, leading=13.2,
                      alignment=TA_LEFT)
small = ParagraphStyle("small", parent=body, fontSize=9, leading=12,
                       textColor=MUTED)
pub = ParagraphStyle("pub", parent=body, fontSize=9.4, leading=12.6)

ME = "<b>Roohani Qadikolaei, M.</b>"

# (year, citation) — newest first. Sources: ORCID 0000-0001-8548-5606 and
# publisher pages for each DOI.
JOURNAL_ARTICLES = [
    ("2026", f"{ME}, Zali, N., &amp; Soltani, A. Who plans the city? A text mining approach "
             "to understanding power in urban governance. <i>SAGE Open</i>. "
             "doi:10.1177/21582440261461369"),
    ("2026", f"Soltani, A., Lee, C. L., Mirzaie, R., &amp; {ME} Environmental drivers of "
             "housing prices and thermal inequality using satellite imagery: A submarket "
             "approach. <i>Habitat International</i>, 167, 103628."),
    ("2026", f"{ME}, Hatami, Y., Nikmard Namin, S., &amp; Soltani, A. Spatial heterogeneity "
             "in housing price-transaction ratios: A historical analysis of Tehran. "
             "<i>International Journal of Housing Markets and Analysis</i>, 19(2), 426&#8211;452. "
             "doi:10.1108/IJHMA-08-2024-0118"),
    ("2025", f"Soltani, A., {ME}, Pojani, D., Moeini, M., &amp; Abdekhoda, K. Women&#8217;s "
             "perceived safety in public transport: Insights from the Middle East. "
             "<i>Journal of Transport Geography</i>, 129, 104413."),
    ("2025", f"{ME}, Soltani, A., Nikmard Namin, S., Hatami, Y., &amp; Najafi, P. Explaining "
             "air pollution exceedance days through land use densities. "
             "<i>Environmental and Sustainability Indicators</i>, 26, 100691."),
    ("2025", f"{ME}, Roohani Qadikolaei, F., Soltani, A., Misaghi, M., &amp; Zali, N. Distance "
             "matters: Quantifying the influence of urban land use change and development "
             "proximity on land surface temperature in Sari, Iran. "
             "<i>Ecological Indicators</i>, 174, 113386."),
    ("2025", f"Soltani, A., &amp; {ME} Shifting landscapes, escalating risks: How land use "
             "conversion shapes long-term road crash outcomes in Melbourne. "
             "<i>Future Transportation</i>, 5(2), 75."),
    ("2024", f"Soltani, A., &amp; {ME} Space-time analysis of accident frequency and the role "
             "of built environment in mitigation. <i>Transport Policy</i>, 150, 189&#8211;205."),
    ("2024", f"Soltani, A., Azmoodeh, M., &amp; {ME} Post COVID-19 transformation in the "
             "frequency and location of traffic crashes involving older adults. "
             "<i>Transportation Research Record</i>, 2678. doi:10.1177/03611981231163866"),
    ("2024", f"{ME}, Zali, N., &amp; Soltani, A. Spatiotemporal investigation of the digital "
             "divide: The case study of Iranian provinces. <i>Environment, Development and "
             "Sustainability</i>, 26(1), 869&#8211;884. doi:10.1007/s10668-022-02738-0"),
    ("2024", f"{ME}, Zali, N., &amp; Soltani, A. A systematic review and topic modelling of the "
             "concept of power in urban planning. <i>Geographical Urban Planning Research "
             "(GUPR)</i>, 12(2), 45&#8211;72."),
]

INTERESTS = [
    "Spatial and geo-statistical analysis of land use, housing and transportation data",
    "Urban governance, power relations and participatory planning",
    "Road safety and the built environment",
    "Housing markets, environmental justice and urban heat",
    "Digital divide and smart-city inequality",
    "Remote sensing (Landsat/MODIS), land surface temperature and green infrastructure",
]

METHODS = [
    ("Spatial analysis", "GIS, hotspot / cluster analysis, spatio-temporal modelling, "
                         "remote sensing (LST, NDVI)"),
    ("Statistical modelling", "Generalised linear mixed models, negative binomial and Tweedie "
                              "count models, structural equation modelling, regression"),
    ("Computational methods", "Text mining, topic modelling (LDA), systematic reviews (PRISMA)"),
    ("Design &amp; planning", "Urban and regional planning, placemaking, rural planning, AutoCAD"),
]


def section(title):
    return [Paragraph(title.upper(), section_style),
            HRFlowable(width="100%", thickness=0.8, color=ACCENT, spaceBefore=1,
                       spaceAfter=5)]


def entry(left, right, sub=None):
    rows = [[Paragraph(f"<b>{left}</b>", body), Paragraph(right, small)]]
    t = Table(rows, colWidths=[None, 60 * mm])
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
    ]))
    out = [t]
    if sub:
        out.append(Paragraph(sub, small))
    out.append(Spacer(1, 5))
    return KeepTogether(out)


def bullets(items, style=body):
    return ListFlowable(
        [ListItem(Paragraph(i, style), leftIndent=10, value="•") for i in items],
        bulletType="bullet", start="•", leftIndent=10, bulletFontSize=8,
        bulletColor=ACCENT)


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Body", 8)
    canvas.setFillColor(MUTED)
    canvas.drawString(doc.leftMargin, 10 * mm,
                      "Mohsen Roohani Qadikolaei — Curriculum Vitae")
    canvas.drawRightString(A4[0] - doc.rightMargin, 10 * mm, f"Page {doc.page}")
    canvas.restoreState()


def build():
    doc = SimpleDocTemplate(str(OUT), pagesize=A4, leftMargin=18 * mm,
                            rightMargin=18 * mm, topMargin=16 * mm,
                            bottomMargin=18 * mm,
                            title="Mohsen Roohani Qadikolaei — CV",
                            author="Mohsen Roohani Qadikolaei")
    s = []
    s.append(Paragraph("Mohsen Roohani Qadikolaei", name_style))
    s.append(Paragraph("Urban &amp; Regional Planner · PhD Researcher, University of Guilan",
                       title_style))
    s.append(Spacer(1, 3))
    s.append(Paragraph(
        "Department of Urban Planning, Faculty of Arts and Architecture, University of Guilan, "
        "Rasht, Iran<br/>"
        "ORCID: <link href='https://orcid.org/0000-0001-8548-5606' color='#1F4E79'>"
        "0000-0001-8548-5606</link> · "
        "Google Scholar: <link href='https://scholar.google.com/citations?user=PH6-EXAAAAAJ' "
        "color='#1F4E79'>PH6-EXAAAAAJ</link> · "
        "LinkedIn: <link href='https://www.linkedin.com/in/mohsen-roohani/' color='#1F4E79'>"
        "mohsen-roohani</link>",
        contact_style))

    s += section("Profile")
    s.append(Paragraph(
        "Urban and regional planning researcher specialising in spatial and geo-statistical "
        "analysis of land use, housing and transportation data. Research links the built "
        "environment to road safety, housing markets, urban heat and digital inequality, and "
        "applies computational text analysis to questions of power and governance in planning. "
        "Co-author of more than ten peer-reviewed articles in journals including "
        "<i>Transport Policy</i>, <i>Journal of Transport Geography</i>, <i>Habitat "
        "International</i>, <i>Ecological Indicators</i> and <i>Transportation Research "
        "Record</i>, in collaboration with researchers in Iran and Australia.", body))

    s += section("Education")
    s.append(entry("PhD, Urban and Regional Planning", "University of Guilan, Iran",
                   "Department of Urban Planning, Faculty of Arts and Architecture"))
    s.append(entry("MSc, Urban and Regional Planning", "Shahid Beheshti University, Iran"))

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

    s += section("Research Collaborations")
    s.append(Paragraph(
        "Ongoing collaboration with Dr Ali Soltani "
        "on road-safety and housing research using Australian (Adelaide, Melbourne) and Iranian "
        "(Tehran, Shiraz, Sari) data, and with Dr Nader Zali (University of Guilan) on urban "
        "governance, power and the digital divide.", body))

    s.append(Spacer(1, 10))
    s.append(Paragraph("Publication list compiled from the ORCID record 0000-0001-8548-5606.",
                       small))
    doc.build(s, onFirstPage=footer, onLaterPages=footer)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    build()
