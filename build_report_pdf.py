"""Render the evidence-based Markdown report and page images for visual review."""
import html
import re
import sys
from pathlib import Path

import pypdfium2 as pdfium
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle

root = Path(__file__).parent
out = root / "output/pdf"
out.mkdir(parents=True, exist_ok=True)
pdfmetrics.registerFont(TTFont("Chinese", r"C:\Windows\Fonts\simsun.ttc", subfontIndex=0))
body = ParagraphStyle("Body", fontName="Chinese", fontSize=10.5, leading=17,
                      spaceAfter=7, wordWrap="CJK", allowWidows=0, allowOrphans=0)
title = ParagraphStyle("Title", parent=body, fontSize=20, leading=29, spaceAfter=16)
heading = ParagraphStyle("Heading", parent=body, fontSize=14, leading=22,
                         spaceBefore=12, spaceAfter=8, keepWithNext=True)
caption = ParagraphStyle("Caption", parent=body, fontSize=9, leading=14, alignment=TA_CENTER)
cellstyle = ParagraphStyle("Cell", parent=body, fontSize=8.5, leading=13, spaceAfter=0)

def text(value):
    value = html.escape(value)
    value = re.sub(r"\*\*(.+?)\*\*", r"\1", value)
    value = re.sub(r"`([^`]+)`", r"\1", value)
    value = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r'<link href="\2" color="#145b86">\1</link>', value)
    if "<link " not in value:
        value = re.sub(r"https?://[^\s<>]+", lambda m: '<link href="' + m[0] + '" color="#145b86">' + m[0] + '</link>', value)
    return value

final = "--final" in sys.argv
source = (root / ("report.md" if final else "report_draft.md")).read_text(encoding="utf-8").splitlines()
story = []
index = 0
while index < len(source):
    line = source[index].strip()
    index += 1
    if not line:
        continue
    if line.startswith("# "):
        title_text = text(line[2:]).replace("与局部重编码方法", "<br/>与局部重编码方法")
        story.append(Paragraph(title_text, title))
    elif line.startswith("### "):
        story.append(Paragraph(text(line[4:]), heading))
    elif line.startswith("## "):
        story.append(Paragraph(text(line[3:]), heading))
    elif line.startswith("!["):
        match = re.match(r"!\[([^]]*)\]\(([^)]+)\)", line)
        image = Image(str(root / match[2]))
        factor = min(165 * mm / image.imageWidth, 95 * mm / image.imageHeight)
        image.drawWidth = image.imageWidth * factor
        image.drawHeight = image.imageHeight * factor
        before_image = Spacer(1, 8)
        before_image.keepWithNext = True
        image.keepWithNext = True
        story.extend([before_image, image, Paragraph(text(match[1]), caption), Spacer(1, 8)])
    elif line.startswith("|"):
        tablelines = [line]
        while index < len(source) and source[index].strip().startswith("|"):
            tablelines.append(source[index].strip())
            index += 1
        data = [[Paragraph(text(cell.strip()), cellstyle) for cell in row.strip("|").split("|")]
                for row in tablelines if not re.fullmatch(r"[| :\-]+", row)]
        table = Table(data, colWidths=[165 * mm / len(data[0])] * len(data[0]), repeatRows=1,
                      hAlign="LEFT")
        table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8eef2")),
                                   ("LINEBELOW", (0, 0), (-1, 0), .5, colors.HexColor("#64748b")),
                                   ("LINEBELOW", (0, 1), (-1, -1), .2, colors.HexColor("#cbd5e1")),
                                   ("VALIGN", (0, 0), (-1, -1), "TOP"),
                                   ("TOPPADDING", (0, 0), (-1, -1), 6),
                                   ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
        story.extend([table, Spacer(1, 10)])
    elif line == r"\[":
        while index < len(source) and source[index].strip() != r"\]":
            index += 1
        index += 1
        story.append(Paragraph("D(p) = H3(p, rc)；P(p) = Parent(H3(p, rf), rc)", body))
    else:
        story.append(Paragraph(text(line), body))

def footer(canvas, document):
    canvas.setFont("Chinese", 8)
    canvas.drawString(22 * mm, 13 * mm, "jinchenying  H3 跨分辨率聚合研究")
    canvas.drawRightString(188 * mm, 13 * mm, str(document.page))

path = out / ("H3_course_report.pdf" if final else "H3_report_working.pdf")
doc = SimpleDocTemplate(str(path), pagesize=A4, rightMargin=22 * mm, leftMargin=22 * mm,
                        topMargin=20 * mm, bottomMargin=22 * mm, title="H3 跨分辨率聚合中的边界归属偏差与局部重编码方法",
                        author="jinchenying")
doc.build(story, onFirstPage=footer, onLaterPages=footer)
pages = root / ("tmp/pdf_final_review" if final else "tmp/pdf_review")
pages.mkdir(parents=True, exist_ok=True)
pdf = pdfium.PdfDocument(path)
for number, page in enumerate(pdf):
    page.render(scale=1.5).to_pil().save(pages / f"page-{number + 1:02}.png")
print(path, "pages", len(pdf))
