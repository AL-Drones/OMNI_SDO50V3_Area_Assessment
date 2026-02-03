"""
PDF Report Generator for Flight Area Analysis
Aligned with SDO 50 V3 Operations Manual – Area Analysis Section
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from io import BytesIO
from datetime import datetime
from PIL import Image as PILImage
import os


def compress_image(image_path, max_size=(2000, 1500), quality=90):
    """
    Compress image while preserving resolution for technical review.
    """
    img = PILImage.open(image_path)

    if img.mode == 'RGBA':
        img = img.convert('RGB')

    img.thumbnail(max_size, PILImage.Resampling.LANCZOS)

    buffer = BytesIO()
    img.save(buffer, format='JPEG', quality=quality, optimize=True, dpi=(300, 300))
    buffer.seek(0)

    return buffer


def generate_pdf_report(results, analysis_output_dir, buffer_info, height, kml_data=None):
    """
    Generate PDF report for operational area analysis,
    aligned with the SDO 50 V3 Operations Manual.
    """

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )

    story = []
    styles = getSampleStyleSheet()

    title = ParagraphStyle(
        'Title', styles['Heading1'],
        alignment=TA_CENTER,
        fontSize=22,
        textColor=colors.HexColor('#054750')
    )

    heading = ParagraphStyle(
        'Heading', styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#E0AB25')
    )

    subheading = ParagraphStyle(
        'SubHeading', styles['Heading3'],
        fontSize=13,
        textColor=colors.HexColor('#054750')
    )

    normal = ParagraphStyle(
        'Normal', styles['Normal'],
        fontSize=10,
        alignment=TA_JUSTIFY
    )

    # =====================================================
    # COVER
    # =====================================================
    story.append(Paragraph("Relatório de Análise de Área Operacional", title))
    story.append(Spacer(1, 0.4*cm))
    story.append(Paragraph("RPA: SwissDrones SDO 50 V3", styles['Normal']))
    story.append(Paragraph(
        f"Data de geração: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        styles['Normal']
    ))
    story.append(PageBreak())

    # =====================================================
    # 1. OBJECTIVE AND REFERENCES
    # =====================================================
    story.append(Paragraph("1. Objetivo e Referências", heading))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph(
        "Este relatório apresenta a análise da área operacional proposta para o "
        "SDO 50 V3, conforme descrito no Manual de Operações da aeronave. "
        "O objetivo é verificar a conformidade da área quanto à presença de terceiros "
        "no solo, por meio da avaliação da densidade populacional nas regiões "
        "associadas à operação.",
        normal
    ))

    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(
        "<b>Referências:</b><br/>"
        "• Manual de Operações – AL-OMNI-SDO50<br/>"
        "• Regulamentos aplicáveis da ANAC para RPAS Classe 3<br/>"
        "• Dados populacionais oficiais (IBGE 2022)",
        normal
    ))

    # =====================================================
    # 2. OPERATIONAL PARAMETERS
    # =====================================================
    story.append(Spacer(1, 0.4*cm))
    story.append(Paragraph("2. Parâmetros Operacionais", heading))

    table_data = [
        ["Altura de voo", f"{height} m"],
        ["Flight Geography", f"{buffer_info.get('fg_size', 0)} m"],
        ["Contingency Volume (CV)", f"{buffer_info['cv_size']} m"],
        ["Ground Risk Buffer (GRB)", f"{buffer_info['grb_size']} m"],
        ["Área Adjacente", f"{buffer_info['adj_size']} m"]
    ]

    table = Table(table_data, colWidths=[8*cm, 8*cm])
    table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 1, colors.grey),
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey)
    ]))
    story.append(table)

    story.append(PageBreak())

    # =====================================================
    # 3. METHODOLOGY
    # =====================================================
    story.append(Paragraph("3. Metodologia de Análise", heading))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph(
        "A análise foi realizada com base na interseção das geometrias operacionais "
        "com dados de densidade populacional do IBGE (Censo 2022). "
        "Foram avaliadas as métricas de densidade média e máxima para cada área, "
        "em conformidade com os critérios definidos no Manual de Operações.",
        normal
    ))

    # =====================================================
    # 4. RESULTS AND COMPLIANCE
    # =====================================================
    story.append(Spacer(1, 0.4*cm))
    story.append(Paragraph("4. Resultados da Análise", heading))

    for area, stats in results.items():
        story.append(Spacer(1, 0.3*cm))
        story.append(Paragraph(area, subheading))
        story.append(Paragraph(
            f"Densidade média: {stats['densidade_media']:.2f} hab/km²<br/>"
            f"Densidade máxima: {stats['densidade_maxima']:.2f} hab/km²<br/>"
            f"População total: {int(stats['total_pessoas'])} habitantes<br/>"
            f"Área: {stats['area_km2']:.2f} km²",
            normal
        ))

    story.append(PageBreak())

    # =====================================================
    # 5. MAPS
    # =====================================================
    story.append(Paragraph("5. Mapas de Densidade Populacional", heading))
    story.append(Spacer(1, 0.3*cm))

    map_files = [
        ("map_flight_geography.png", "Flight Geography"),
        ("map_ground_risk_buffer.png", "Ground Risk Buffer"),
        ("map_adjacent_area.png", "Adjacent Area")
    ]

    for file, title in map_files:
        path = os.path.join(analysis_output_dir, file)
        if os.path.exists(path):
            story.append(Spacer(1, 0.3*cm))
            story.append(Paragraph(title, subheading))
            img_data = compress_image(path)
            img = Image(img_data, width=17*cm, height=12*cm)
            story.append(img)
            story.append(PageBreak())

    # =====================================================
    # FOOTER
    # =====================================================
    story.append(Paragraph(
        "Relatório gerado automaticamente – AL Drones",
        ParagraphStyle('Footer', styles['Normal'], alignment=TA_CENTER, fontSize=9)
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
