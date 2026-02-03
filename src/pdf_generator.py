from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors

from io import BytesIO
from PIL import Image as PILImage
from datetime import datetime


# =====================================================
# Image preparation (HIGH RES – 300 DPI)
# =====================================================
def prepare_image_for_pdf(image_path, target_width_cm, dpi=300, quality=90):
    img = PILImage.open(image_path)

    if img.mode == 'RGBA':
        img = img.convert('RGB')

    target_width_px = int((target_width_cm / 2.54) * dpi)

    w, h = img.size
    scale = target_width_px / w
    new_size = (target_width_px, int(h * scale))

    img = img.resize(new_size, PILImage.Resampling.LANCZOS)

    buffer = BytesIO()
    img.save(buffer, format='JPEG', quality=quality, subsampling=0)
    buffer.seek(0)

    return buffer


# =====================================================
# Styled info box
# =====================================================
def info_box(text, bg_color, border_color, style):
    return Table(
        [[Paragraph(text, style)]],
        colWidths=[16 * cm],
        style=TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), bg_color),
            ('BOX', (0, 0), (-1, -1), 2, border_color),
            ('PADDING', (0, 0), (-1, -1), 12),
        ])
    )


# =====================================================
# Main PDF generator
# =====================================================
def generate_pdf_report(
    results,
    analysis_output_dir,
    buffer_info,
    height,
    kml_data=None
):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Title'],
        fontSize=20,
        textColor=colors.HexColor('#054750'),
        spaceAfter=20
    )

    heading_style = ParagraphStyle(
        'HeadingStyle',
        parent=styles['Heading2'],
        fontSize=15,
        textColor=colors.HexColor('#054750'),
        spaceBefore=18,
        spaceAfter=10
    )

    normal_style = ParagraphStyle(
        'NormalStyle',
        parent=styles['Normal'],
        fontSize=10,
        leading=14
    )

    small_style = ParagraphStyle(
        'SmallStyle',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.grey
    )

    elements = []

    # =================================================
    # Cover
    # =================================================
    elements.append(Paragraph("Relatório de Análise de Densidade Populacional", title_style))
    elements.append(Paragraph(f"<b>Aeronave:</b> {rpa_name}", normal_style))
    elements.append(Paragraph(f"<b>Área de Operação:</b> {operation_area}", normal_style))
    elements.append(Paragraph(
        f"<b>Data:</b> {datetime.now().strftime('%d/%m/%Y')}", normal_style)
    )
    elements.append(Spacer(1, 2 * cm))
    elements.append(Paragraph(
        "Este relatório apresenta a análise de densidade populacional na área "
        "de operação proposta, com base em dados geoespaciais e critérios de "
        "segurança operacional aplicáveis a operações RPAS.",
        normal_style
    ))

    elements.append(PageBreak())

    # =================================================
    # Executive Summary
    # =================================================
    elements.append(Paragraph("Resumo Executivo", heading_style))

    summary_text = (
        "<b>Conclusões Principais:</b><br/>"
        "• A densidade populacional foi avaliada para diferentes buffers operacionais<br/>"
        "• Os valores máximos e médios permanecem compatíveis com operações RPAS<br/>"
        "• A operação proposta pode ser conduzida respeitando as restrições estabelecidas"
    )

    elements.append(
        info_box(
            summary_text,
            bg_color=colors.whitesmoke,
            border_color=colors.HexColor('#054750'),
            style=normal_style
        )
    )

    elements.append(Spacer(1, 0.8 * cm))

    # =================================================
    # Statistics Table
    # =================================================
    table_data = [
        [
            "Camada",
            "População Total",
            "Área (km²)",
            "Densidade Média (hab/km²)",
            "Densidade Máxima (hab/km²)"
        ]
    ]

    for layer, stat in results.items():
        table_data.append([
            layer,
            int(stat['total_pessoas']),
            round(stat['area_km2'], 2),
            round(stat['densidade_media'], 2),
            round(stat['densidade_maxima'], 2)
        ])

    stats_table = Table(
        table_data,
        colWidths=[4 * cm, 3 * cm, 3 * cm, 3.5 * cm, 3.5 * cm]
    )

    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#054750')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
    ]))

    elements.append(stats_table)
    elements.append(PageBreak())

    # =================================================
    # Maps Section
    # =================================================
    elements.append(Paragraph("Mapas e Evidências", heading_style))

    for layer, map_path in maps.items():
        elements.append(Paragraph(f"<b>{layer}</b>", normal_style))
        elements.append(Spacer(1, 0.3 * cm))

        img_buffer = prepare_image_for_pdf(
            map_path,
            target_width_cm=15,
            dpi=300
        )

        img = Image(
            img_buffer,
            width=15 * cm,
            height=11.25 * cm
        )

        elements.append(img)
        elements.append(Spacer(1, 0.4 * cm))
        elements.append(Paragraph(
            "Mapa gerado a partir de dados geoespaciais públicos para análise "
            "de densidade populacional na área de interesse.",
            small_style
        ))
        elements.append(PageBreak())

    # =================================================
    # Build PDF
    # =================================================
    doc.build(elements)
