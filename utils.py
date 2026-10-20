# utils.py
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import os

def gerar_pdf_recibo(os_id, cliente_nome, moto_modelo, moto_placa, pecas, servicos, total):
    pdf_path = f"recibo_{os_id[:8]}.pdf"
    doc = SimpleDocTemplate(pdf_path, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    story = []
    
    styles = getSampleStyleSheet()
    
    # Título Principal
    titulo_style = ParagraphStyle(
        'TituloCustom',
        parent=styles['Heading1'],
        fontSize=24,
        leading=28,
        textColor=colors.HexColor('#F97316'),
        alignment=1, # Centralizado
        spaceAfter=20
    )
    
    # Subtítulos e Textos
    texto_style = styles['Normal']
    bold_style = ParagraphStyle('BoldCustom', parent=texto_style, fontName='Helvetica-Bold')
    
    # Cabeçalho do Recibo
    story.append(Paragraph("<b>🏍️ OFICINA PULSE - COMPROVANTE DE SERVIÇO</b>", titulo_style))
    story.append(Paragraph(f"<b>Ordem de Serviço (OS):</b> #{os_id[:8]}...", texto_style))
    story.append(Paragraph(f"<b>Cliente:</b> {cliente_nome}", texto_style))
    story.append(Paragraph(f"<b>Veículo:</b> {moto_modelo} | <b>Placa:</b> {moto_placa}", texto_style))
    story.append(Spacer(1, 15))
    
    # Tabela de Serviços e Valores
    dados_tabela = [[Paragraph("<b>Descrição do Serviço Executado</b>", bold_style), Paragraph("<b>Preço (R$)</b>", bold_style)]]
    
    for s in servicos:
        dados_tabela.append([Paragraph(s['nome'], texto_style), Paragraph(f"R$ {s['preco']:.2f}", texto_style)])
        
    # Linha do Total
    dados_tabela.append([Paragraph("<b>VALOR TOTAL DO RECIBO:</b>", bold_style), Paragraph(f"<b>R$ {total:.2f}</b>", bold_style)])
    
    # CORREÇÃO: Larguras especificadas perfeitamente para renderizar a tabela
    t = Table(dados_tabela, colWidths=[350, 150])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), colors.HexColor('#F3F4F6')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -2), 0.5, colors.HexColor('#E5E7EB')),
        ('LINEABOVE', (0, -1), (1, -1), 1.5, colors.HexColor('#F97316')),
    ]))
    
    story.append(t)
    story.append(Spacer(1, 30))
    story.append(Paragraph("<font color='#6B7280'>Obrigado pela preferência! Volte sempre com sua máquina em segurança.</font>", texto_style))
    
    doc.build(story)
    return pdf_path

def enviar_whatsapp_conclusao(telefone, nome, modelo, placa):
    pass
