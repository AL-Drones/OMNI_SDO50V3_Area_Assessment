"""
PDF Report Generator for Flight Area Analysis
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from io import BytesIO
from datetime import datetime
import os


def generate_pdf_report(results, analysis_output_dir, buffer_info, height):
    """
    Generate PDF report with analysis results.
    
    Args:
        results: Dictionary with population statistics for each layer
        analysis_output_dir: Path to directory containing map images
        buffer_info: Dictionary with buffer parameters
        height: Flight height in meters
    
    Returns:
        bytes: PDF file data
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
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#054750'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=14,
        textColor=colors.HexColor('#0a6b7a'),
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName='Helvetica'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#E0AB25'),
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.black,
        alignment=TA_LEFT
    )
    
    # Header with logos and title
    story.append(Paragraph("AL DRONES", title_style))
    story.append(Paragraph("Relatório de Análise de Área de Voo", subtitle_style))
    story.append(Paragraph("SwissDrones SDO 50 V3", normal_style))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(f"Data de Geração: {datetime.now().strftime('%d/%m/%Y às %H:%M')}", normal_style))
    story.append(Spacer(1, 0.8*cm))
    
    # Separator line
    story.append(Table([['']], colWidths=[16*cm], style=TableStyle([
        ('LINEABOVE', (0, 0), (-1, 0), 2, colors.HexColor('#E0AB25')),
    ])))
    story.append(Spacer(1, 0.8*cm))
    
    # Section 1: Flight Parameters
    story.append(Paragraph("1. Parâmetros de Voo", heading_style))
    story.append(Spacer(1, 0.3*cm))
    
    params_data = [
        ['Parâmetro', 'Valor'],
        ['Altura de Voo', f"{height} m"],
        ['Flight Geography Buffer', f"{buffer_info['fg_size']} m"],
        ['Contingency Volume', f"{buffer_info['cv_size']} m"],
        ['Ground Risk Buffer', f"{buffer_info['grb_size']} m"],
        ['Adjacent Area', f"{buffer_info['adj_size']} m"]
    ]
    
    params_table = Table(params_data, colWidths=[10*cm, 6*cm])
    params_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#054750')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f5f5f5')),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
    ]))
    story.append(params_table)
    story.append(Spacer(1, 1*cm))
    
    # Section 2: Population Statistics
    story.append(Paragraph("2. Estatísticas Populacionais (IBGE 2022)", heading_style))
    story.append(Spacer(1, 0.3*cm))
    
    stats_data = [
        ['Camada', 'População\nTotal', 'Área\n(km²)', 'Densidade\nMédia\n(hab/km²)', 'Densidade\nMáxima\n(hab/km²)']
    ]
    
    for layer, stat in results.items():
        stats_data.append([
            layer,
            f"{int(stat['total_pessoas']):,}".replace(',', '.'),
            f"{stat['area_km2']:.2f}",
            f"{stat['densidade_media']:.2f}",
            f"{stat['densidade_maxima']:.2f}"
        ])
    
    stats_table = Table(stats_data, colWidths=[5*cm, 2.5*cm, 2.5*cm, 3*cm, 3*cm])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#054750')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f5f5f5')),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
    ]))
    story.append(stats_table)
    story.append(Spacer(1, 0.5*cm))
    
    # Compliance analysis
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph("2.1 Análise de Conformidade", heading_style))
    story.append(Spacer(1, 0.3*cm))
    
    compliance_text = []
    
    # Check Flight Geography and Ground Risk Buffer
    for layer_name in ['Flight Geography', 'Ground Risk Buffer']:
        if layer_name in results:
            stats = results[layer_name]
            densidade = stats['densidade_maxima']
            
            if densidade > 5:
                compliance_text.append(
                    f"<b>{layer_name}:</b> <font color='red'>NÃO CONFORME</font> - "
                    f"Densidade máxima de {densidade:.1f} hab/km² excede o limite de 5 hab/km²."
                )
            elif densidade > 0:
                compliance_text.append(
                    f"<b>{layer_name}:</b> <font color='orange'>ATENÇÃO</font> - "
                    f"Densidade máxima de {densidade:.1f} hab/km². O voo sobre não anuentes é proibido."
                )
            else:
                compliance_text.append(
                    f"<b>{layer_name}:</b> <font color='green'>CONFORME</font> - "
                    f"Densidade máxima de {densidade:.1f} hab/km² dentro do limite."
                )
    
    # Check Adjacent Area
    if 'Adjacent Area' in results:
        stats = results['Adjacent Area']
        densidade = stats['densidade_media']
        
        if densidade > 50:
            compliance_text.append(
                f"<b>Adjacent Area:</b> <font color='red'>NÃO CONFORME</font> - "
                f"Densidade média de {densidade:.1f} hab/km² excede o limite de 50 hab/km²."
            )
        else:
            compliance_text.append(
                f"<b>Adjacent Area:</b> <font color='green'>CONFORME</font> - "
                f"Densidade média de {densidade:.1f} hab/km² dentro do limite."
            )
    
    for text in compliance_text:
        story.append(Paragraph(text, normal_style))
        story.append(Spacer(1, 0.2*cm))
    
    story.append(PageBreak())
    
    # Section 3: Maps
    story.append(Paragraph("3. Mapas de Densidade Populacional", heading_style))
    story.append(Spacer(1, 0.5*cm))
    
    maps = [
        ('map_flight_geography.png', '3.1 Flight Geography'),
        ('map_ground_risk_buffer.png', '3.2 Ground Risk Buffer'),
        ('map_adjacent_area.png', '3.3 Adjacent Area')
    ]
    
    for map_file, map_title in maps:
        map_path = os.path.join(analysis_output_dir, map_file)
        if os.path.exists(map_path):
            story.append(Paragraph(map_title, heading_style))
            story.append(Spacer(1, 0.3*cm))
            
            # Add image with proper sizing
            img = Image(map_path, width=16*cm, height=12*cm, kind='proportional')
            story.append(img)
            story.append(Spacer(1, 0.8*cm))
    
    # Footer
    story.append(PageBreak())
    story.append(Spacer(1, 5*cm))
    story.append(Table([['']], colWidths=[16*cm], style=TableStyle([
        ('LINEABOVE', (0, 0), (-1, 0), 1, colors.grey),
    ])))
    story.append(Spacer(1, 0.3*cm))
    
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.grey,
        alignment=TA_CENTER
    )
    
    story.append(Paragraph("AL Drones - Análise de Área de Voo", footer_style))
    story.append(Paragraph("© 2026 AL Drones - Todos os direitos reservados", footer_style))
    story.append(Paragraph("www.aldrones.com.br", footer_style))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(
        f"Este relatório foi gerado automaticamente em {datetime.now().strftime('%d/%m/%Y às %H:%M')}",
        footer_style
    ))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
