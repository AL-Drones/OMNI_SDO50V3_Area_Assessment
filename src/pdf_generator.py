"""
PDF Report Generator for Flight Area Analysis
Aligned with SDO 50 V3 Operations Manual – Area Analysis Section
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from io import BytesIO
from datetime import datetime
from PIL import Image as PILImage
import os


def compress_image(image_path, max_size=(2000, 1500), quality=90):
    img = PILImage.open(image_path)

    if img.mode == 'RGBA':
        img = img.convert('RGB')

    img.thumbnail(max_size, PILImage.Resampling.LANCZOS)

    buffer = BytesIO()
    img.save(buffer, format='JPEG', quality=quality, optimize=True, dpi=(300, 300))
    buffer.seek(0)

    return buffer


def generate_pdf_report(results, analysis_output_dir, buffer_info, height, kml_data=None):
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )

    styles = getSampleStyleSheet()
    story = []

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
    story.append(Paragraph("Relatório de Análise de Área", title))
    story.append(Spacer(1, 0.4*cm))
    story.append(Paragraph("RPA: SwissDrones SDO 50 V3", styles['Normal']))
    story.append(Paragraph(
        f"Data de geração: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        styles['Normal']
    ))
    story.append(Spacer(1, 0.8*cm))

    # =====================================================
    # 1. OBJECTIVE AND REFERENCES
    # =====================================================
    story.append(Paragraph("1. Objetivo e Referências", heading))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph(
        "Este relatório apresenta a análise da área de operação proposta para o "
        "RPAS SDO 50 V3, conforme descrito no Manual de Operações da aeronave. "
        "O objetivo é verificar a conformidade da área quanto à exposição de terceiros "
        "no solo, por meio da avaliação da densidade populacional nas regiões "
        "associadas à operação, a partir de dados do IBGE 2022.",
        normal
    ))

    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(
        "<b>Referências:</b><br/>"
        "• Manual de Operações – AL-OMNI-SDO50-OM<br/>"
        "• Dados populacionais oficiais (IBGE – Censo 2022)",
        normal
    ))

    # =====================================================
    # 2. OPERATIONAL PARAMETERS
    # =====================================================
    story.append(Spacer(1, 0.4*cm))
    story.append(Paragraph("2. Parâmetros Operacionais", heading))
    story.append(Spacer(1, 0.3*cm))

    table_data = [
        ["Altura de voo", f"{height} m"],
        ["Flight Geography (FG)", f"{buffer_info.get('fg_size', 0)} m"],
        ["Contingency Volume (CV)", f"{buffer_info['cv_size']} m"],
        ["Ground Risk Buffer (GRB)", f"{buffer_info['grb_size']} m"],
        ["Área Adjacente", f"{buffer_info['adj_size']} m"]
    ]

    table = Table(table_data, colWidths=[8*cm, 8*cm])
    table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.8, colors.grey),
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey)
    ]))
    story.append(table)

    # =====================================================
    # 3. METHODOLOGY
    # =====================================================
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph("3. Metodologia de Análise", heading))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph(
        "A análise foi conduzida a partir da interseção das geometrias operacionais "
        "(Flight Geography, Ground Risk Buffer e Área Adjacente) com dados de "
        "densidade populacional provenientes do IBGE. "
        "Foram avaliadas as métricas de densidade média, densidade máxima e "
        "população total em cada área, conforme critérios definidos no Manual "
        "de Operações.",
        normal
    ))

    # =====================================================
    # 4. RESULTS
    # =====================================================
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph("4. Resultados da Análise", heading))

    area_approved = True
    approval_notes = []

    # >>>>>> AJUSTE AQUI SE NECESSÁRIO <<<<<<
    MAX_ALLOWED_DENSITY = 1000  # hab/km² (exemplo)

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

        if stats['densidade_maxima'] > MAX_ALLOWED_DENSITY:
            area_approved = False
            approval_notes.append(
                f"A área <b>{area}</b> apresenta densidade máxima superior ao limite aceitável."
            )

    # =====================================================
    # 5. FINAL ASSESSMENT
    # =====================================================
    story.append(Spacer(1, 0.6*cm))
    story.append(Paragraph("5. Avaliação Final da Área Operacional", heading))
    story.append(Spacer(1, 0.3*cm))

    if area_approved:
        story.append(Paragraph(
            "<b>Resultado:</b> A área operacional analisada é considerada "
            "<b>APROVADA</b> para a operação proposta, uma vez que os níveis de "
            "exposição de terceiros no solo permanecem dentro dos limites "
            "aceitáveis definidos no Manual de Operações.",
            normal
        ))
    else:
        story.append(Paragraph(
            "<b>Resultado:</b> A área operacional analisada é considerada "
            "<b>NÃO APROVADA</b> para a operação proposta. "
            "Foram identificadas as seguintes não conformidades:",
            normal
        ))
        for note in approval_notes:
            story.append(Spacer(1, 0.2*cm))
            story.append(Paragraph(f"• {note}", normal))

    # =====================================================
    # 6. MAPS
    # =====================================================
    story.append(Spacer(1, 0.6*cm))
    story.append(Paragraph("6. Mapas de Densidade Populacional", heading))

    map_files = [
        ("map_flight_geography.png", "Geografia de Voo"),
        ("map_ground_risk_buffer.png", "Distância de Segurança no Solo"),
        ("map_adjacent_area.png", "Área Adjacente")
    ]

    for file, title_txt in map_files:
        path = os.path.join(analysis_output_dir, file)
        if os.path.exists(path):
            story.append(Spacer(1, 0.4*cm))
            story.append(Paragraph(title_txt, subheading))
            img_data = compress_image(path)
            img = Image(img_data, width=17*cm, height=12*cm)
            story.append(img)

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
