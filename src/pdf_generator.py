from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER
from reportlab.lib import colors


def generate_pdf_report(
    rpa_name,
    operation_area,
    maps,
    results,
    kml_data=None
):
    """
    Generates a PDF report in memory and returns it as bytes.
    """

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    elements = []

    # Title
    title = Paragraph(
        f"<b>Ground Risk and Population Assessment Report</b><br/>{rpa_name}",
        styles['Title']
    )
    elements.append(title)
    elements.append(Spacer(1, 20))

    # Operation area
    elements.append(Paragraph(
        f"<b>Operation Area:</b> {operation_area}",
        styles['Normal']
    ))
    elements.append(Spacer(1, 16))

    # Results table
    table_data = [["Metric", "Value"]]
    for key, value in results.items():
        table_data.append([str(key), str(value)])

    table = Table(table_data, hAlign="LEFT")
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 20))

    # Maps
    for layer_name, image_path in maps.items():
        elements.append(Paragraph(f"<b>{layer_name}</b>", styles['Heading2']))
        elements.append(Spacer(1, 8))
        elements.append(Image(image_path, width=400, height=300))
        elements.append(Spacer(1, 20))

    doc.build(elements)

    buffer.seek(0)
    return buffer.getvalue()
