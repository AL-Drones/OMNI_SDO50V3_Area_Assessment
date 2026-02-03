"""
PDF Report Generator for Flight Area Analysis
Aligned with SDO 50 V3 Operations Manual – Area Analysis Section
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from io import BytesIO
from datetime import datetime
from PIL import Image as PILImage
import os


def compress_image(image_path, max_size=(2400, 1800), quality=92):
    img = PILImage.open(image_path)

    if img.mode == 'RGBA':
        img = img.convert('RGB')

    img.thumbnail(max_size, PILImage.Resampling.LANCZOS)

    buffer = BytesIO()
    img.save(
        buffer,
        format='JPEG',
        quality=quality,
        optimize=True,
        dpi=(300, 300)
    )
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

    result_ok = ParagraphStyle(
        'ResultOK', styles['Normal'],
        fontSize=14,
        textColor=colors.green,
        alignment=TA_CENTER,
        spaceAfter=10
    )

    result_nok = ParagraphStyle(
        'ResultNOK', styles['Normal'],
        fontSize=14,
        textColor=colors.red,
        alignment=TA_CENTER,
        spaceAfter=10
    )

    # =====================================================
    # CAPA
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
    # 1. OBJETIVO E REFERÊNCIAS
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
    # 2. PARÂMETROS OPERACIONAIS
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
        ('GRID', (0, 0), (-1, -1), 0.8, colors.grey),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey)
    ]))
    story.append(table)

    # =====================================================
    # 3. METODOLOGIA
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
    # 4. RESULTADOS
    # =====================================================
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph("4. Resultados da Análise", heading))

    area_aprovada = True
    notas_nao_conformidade = []

    LIMITES = {
        "Flight Geography": {"tipo": "máxima", "valor": 5},
        "Ground Risk Buffer": {"tipo": "máxima", "valor": 5},
        "Área Adjacente": {"tipo": "média", "valor": 50}
    }

    for area, stats in results.items():
        story.append(Spacer(1, 0.3*cm))
        story.append(Paragraph(area, subheading))

        limite = LIMITES.get(area)

        if limite["tipo"] == "máxima":
            densidade = stats["densidade_maxima"]
            criterio_txt = "Densidade máxima"
        else:
            densidade = stats["densidade_media"]
            criterio_txt = "Densidade média"

        story.append(Paragraph(
            f"<b>{criterio_txt} calculada:</b> {densidade:.2f} hab/km²<br/>"
            f"<b>Limite aceitável:</b> {limite['valor']} hab/km²<br/>"
            f"<b>População total:</b> {int(stats['total_pessoas'])} habitantes<br/>"
            f"<b>Área analisada:</b> {stats['area_km2']:.2f} km²",
            normal
        ))

        if densidade > limite["valor"]:
            area_aprovada = False
            notas_nao_conformidade.append(
                f"A área <b>{area}</b> excede o limite aceitável de densidade populacional."
            )

    # =====================================================
    # 5. AVALIAÇÃO FINAL
    # =====================================================
    story.append(Spacer(1, 0.6*cm))
    story.append(Paragraph("5. Avaliação Final da Área Operacional", heading))
    story.append(Spacer(1, 0.4*cm))

    if area_aprovada:
        story.append(Paragraph("ÁREA OPERACIONAL APROVADA", result_ok))
        story.append(Paragraph(
            "A área operacional analisada atende aos critérios de exposição de terceiros "
            "no solo definidos no Manual de Operações do SDO 50 V3 e é considerada "
            "adequada para a operação proposta.",
            normal
        ))
    else:
        story.append(Paragraph("ÁREA OPERACIONAL NÃO APROVADA", result_nok))
        story.append(Paragraph(
            "A área operacional analisada não atende aos critérios estabelecidos no "
            "Manual de Operações. As seguintes não conformidades foram identificadas:",
            normal
        ))
        for nota in notas_nao_conformidade:
            story.append(Spacer(1, 0.2*cm))
            story.append(Paragraph(f"• {nota}", normal))

    # =====================================================
    # 6. MAPAS
    # =====================================================
    story.append(PageBreak())
    story.append(Paragraph("6. Mapas de Densidade Populacional", heading))

    mapas = [
        ("map_flight_geography.png", "Flight Geography"),
        ("map_ground_risk_buffer.png", "Ground Risk Buffer"),
        ("map_adjacent_area.png", "Área Adjacente")
    ]

    for idx, (arquivo, titulo) in enumerate(mapas):
        caminho = os.path.join(analysis_output_dir, arquivo)
        if os.path.exists(caminho):
            story.append(Spacer(1, 0.3*cm))
            story.append(Paragraph(titulo, subheading))
            story.append(Spacer(1, 0.3*cm))

            img_data = compress_image(caminho)
            img = Image(img_data, width=17*cm, height=12.5*cm)
            story.append(img)

            if idx < len(mapas) - 1:
                story.append(PageBreak())

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
