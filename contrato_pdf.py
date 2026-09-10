#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Geração de PDF do Contrato
Compatível com Windows, Linux e macOS.
"""

import os
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor, black
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

PRIMARY = HexColor("#1a365d")
GRAY = HexColor("#4a5568")

# ---------------------------------------------------------------------------
# Fontes: tenta encontrar TTF no sistema; se não achar, usa Helvetica (padrão)
# ---------------------------------------------------------------------------
def _registrar_fontes():
    """
    Retorna (fonte_normal, fonte_bold, fonte_italic).
    Tenta DejaVu / Arial / Liberation; senão usa Helvetica embutida.
    """
    candidatos = {
        "normal": [
            # Linux
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
            # Windows
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/Arial.ttf",
            "C:/Windows/Fonts/calibri.ttf",
            "C:/Windows/Fonts/Calibri.ttf",
            # macOS
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/Library/Fonts/Arial.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
        ],
        "bold": [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/Arialbd.ttf",
            "C:/Windows/Fonts/calibrib.ttf",
            "C:/Windows/Fonts/Calibrib.ttf",
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            "/Library/Fonts/Arial Bold.ttf",
        ],
        "italic": [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Italic.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSansOblique.ttf",
            "C:/Windows/Fonts/ariali.ttf",
            "C:/Windows/Fonts/Ariali.ttf",
            "C:/Windows/Fonts/calibrii.ttf",
            "/System/Library/Fonts/Supplemental/Arial Italic.ttf",
            "/Library/Fonts/Arial Italic.ttf",
        ],
    }

    nomes = {"normal": None, "bold": None, "italic": None}

    for estilo, paths in candidatos.items():
        for path in paths:
            if os.path.isfile(path):
                try:
                    nome_interno = "AppFont-%s" % estilo
                    pdfmetrics.registerFont(TTFont(nome_interno, path))
                    nomes[estilo] = nome_interno
                    break
                except Exception:
                    continue

    # Fallback: fontes embutidas do ReportLab (funcionam em qualquer SO)
    if not nomes["normal"]:
        nomes["normal"] = "Helvetica"
    if not nomes["bold"]:
        nomes["bold"] = "Helvetica-Bold"
    if not nomes["italic"]:
        nomes["italic"] = "Helvetica-Oblique"

    return nomes["normal"], nomes["bold"], nomes["italic"]


FONT, FONT_BOLD, FONT_ITALIC = _registrar_fontes()


def format_currency(value):
    try:
        return "R$ {:,.2f}".format(float(value)).replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"


def format_date(date_str):
    if not date_str:
        return "____/____/________"
    try:
        if "-" in str(date_str):
            d = datetime.strptime(str(date_str)[:10], "%Y-%m-%d")
            return d.strftime("%d/%m/%Y")
        return str(date_str)
    except Exception:
        return str(date_str)


def gerar_pdf_contrato(contrato, output_path=None):
    """
    Gera o PDF do contrato a partir dos dados unidos das tabelas.
    """
    if output_path is None:
        output_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "static",
            "contrato_%s.pdf" % str(contrato.get("numero", "sem_numero")).replace("/", "-"),
        )

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=1.8 * cm,
        bottomMargin=1.8 * cm,
    )

    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="Titulo",
        fontName=FONT_BOLD,
        fontSize=16,
        leading=20,
        alignment=TA_CENTER,
        textColor=PRIMARY,
        spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        name="Subtitulo",
        fontName=FONT,
        fontSize=11,
        leading=14,
        alignment=TA_CENTER,
        textColor=GRAY,
        spaceAfter=12,
    ))
    styles.add(ParagraphStyle(
        name="Secao",
        fontName=FONT_BOLD,
        fontSize=11,
        leading=14,
        textColor=PRIMARY,
        spaceBefore=12,
        spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        name="Corpo",
        fontName=FONT,
        fontSize=10,
        leading=14,
        alignment=TA_JUSTIFY,
        textColor=black,
        spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        name="Parte",
        fontName=FONT,
        fontSize=9.5,
        leading=13,
        alignment=TA_LEFT,
        textColor=black,
        spaceAfter=3,
    ))
    styles.add(ParagraphStyle(
        name="Assinatura",
        fontName=FONT,
        fontSize=9,
        leading=12,
        alignment=TA_CENTER,
        textColor=black,
    ))
    styles.add(ParagraphStyle(
        name="Rodape",
        fontName=FONT,
        fontSize=8,
        alignment=TA_CENTER,
        textColor=GRAY,
    ))

    story = []

    # Cabeçalho
    story.append(Paragraph("CONTRATO DE PRESTAÇÃO DE SERVIÇOS", styles["Titulo"]))
    story.append(Paragraph("Nº %s" % contrato.get("numero", "—"), styles["Subtitulo"]))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceAfter=12))

    story.append(Paragraph(
        "Pelo presente instrumento particular, as partes abaixo qualificadas resolvem celebrar o presente "
        "<b>Contrato de Prestação de Serviços</b>, que se regerá pelas cláusulas e condições seguintes:",
        styles["Corpo"],
    ))

    # CONTRATANTE
    story.append(Paragraph("1. DO CONTRATANTE", styles["Secao"]))
    ct_end = "%s, %s" % (
        contrato.get("contratante_logradouro") or "",
        contrato.get("contratante_numero") or "s/n",
    )
    if contrato.get("contratante_bairro"):
        ct_end += " - %s" % contrato["contratante_bairro"]
    ct_end += ", %s / %s" % (
        contrato.get("contratante_cidade") or "",
        contrato.get("contratante_uf") or "",
    )
    if contrato.get("contratante_cep"):
        ct_end += " - CEP %s" % contrato["contratante_cep"]

    story.append(Paragraph(
        "<b>Nome / Razão Social:</b> %s" % (contrato.get("contratante_nome") or "________________"),
        styles["Parte"],
    ))
    story.append(Paragraph(
        "<b>CPF / CNPJ:</b> %s" % (contrato.get("contratante_doc") or "________________"),
        styles["Parte"],
    ))
    story.append(Paragraph("<b>Endereço:</b> %s" % ct_end, styles["Parte"]))
    story.append(Paragraph(
        "<b>E-mail:</b> %s &nbsp;&nbsp;&nbsp; <b>Telefone:</b> %s"
        % (
            contrato.get("contratante_email") or "________________",
            contrato.get("contratante_celular") or "________________",
        ),
        styles["Parte"],
    ))

    # CONTRATADO
    story.append(Paragraph("2. DO CONTRATADO", styles["Secao"]))
    cd_end = "%s, %s" % (
        contrato.get("contratado_logradouro") or "",
        contrato.get("contratado_numero") or "s/n",
    )
    if contrato.get("contratado_bairro"):
        cd_end += " - %s" % contrato["contratado_bairro"]
    cd_end += ", %s / %s" % (
        contrato.get("contratado_cidade") or "",
        contrato.get("contratado_uf") or "",
    )
    if contrato.get("contratado_cep"):
        cd_end += " - CEP %s" % contrato["contratado_cep"]

    story.append(Paragraph(
        "<b>Nome / Razão Social:</b> %s" % (contrato.get("contratado_nome") or "________________"),
        styles["Parte"],
    ))
    story.append(Paragraph(
        "<b>CPF / CNPJ:</b> %s" % (contrato.get("contratado_doc") or "________________"),
        styles["Parte"],
    ))
    story.append(Paragraph("<b>Endereço:</b> %s" % cd_end, styles["Parte"]))
    story.append(Paragraph(
        "<b>E-mail:</b> %s &nbsp;&nbsp;&nbsp; <b>Telefone:</b> %s"
        % (
            contrato.get("contratado_email") or "________________",
            contrato.get("contratado_celular") or "________________",
        ),
        styles["Parte"],
    ))

    # Objeto
    story.append(Paragraph("3. DO OBJETO", styles["Secao"]))
    story.append(Paragraph(
        "O presente contrato tem por objeto: <b>%s</b>."
        % (contrato.get("objeto") or "________________"),
        styles["Corpo"],
    ))
    if contrato.get("setor_nome"):
        texto_setor = "Setor responsável: <b>%s</b>" % contrato["setor_nome"]
        if contrato.get("setor_responsavel"):
            texto_setor += " — Responsável: %s" % contrato["setor_responsavel"]
        story.append(Paragraph(texto_setor, styles["Parte"]))

    # Valor e Vigência
    story.append(Paragraph("4. DO VALOR E DA VIGÊNCIA", styles["Secao"]))
    story.append(Paragraph(
        "Vigência: de <b>%s</b> até <b>%s</b> (<b>%s mês(es)</b>)."
        % (
            format_date(contrato.get("data_inicio")),
            format_date(contrato.get("data_fim")),
            contrato.get("quantidade_meses") or "—",
        ),
        styles["Corpo"],
    ))
    story.append(Paragraph(
        "Valor mensal: <b>%s</b>." % format_currency(contrato.get("valor_mensal", 0)),
        styles["Corpo"],
    ))
    story.append(Paragraph(
        "Valor total do presente contrato: <b>%s</b>." % format_currency(contrato.get("valor", 0)),
        styles["Corpo"],
    ))

    # Obrigações
    story.append(Paragraph("5. DAS OBRIGAÇÕES DAS PARTES", styles["Secao"]))
    story.append(Paragraph(
        "<b>5.1.</b> O CONTRATADO se obriga a executar os serviços com zelo, diligência e observância "
        "às normas técnicas aplicáveis, mantendo sigilo sobre informações a que tiver acesso.",
        styles["Corpo"],
    ))
    story.append(Paragraph(
        "<b>5.2.</b> O CONTRATANTE se obriga a fornecer as informações e condições necessárias "
        "à execução dos serviços, bem como efetuar o pagamento nas condições pactuadas.",
        styles["Corpo"],
    ))

    # Rescisão
    story.append(Paragraph("6. DA RESCISÃO", styles["Secao"]))
    story.append(Paragraph(
        "O presente contrato poderá ser rescindido por qualquer das partes, mediante comunicação "
        "por escrito com antecedência mínima de 30 (trinta) dias, ou imediatamente em caso de "
        "descumprimento de qualquer cláusula.",
        styles["Corpo"],
    ))

    # Disposições gerais
    story.append(Paragraph("7. DAS DISPOSIÇÕES GERAIS", styles["Secao"]))
    story.append(Paragraph(
        "As partes elegem o foro da comarca do CONTRATANTE para dirimir quaisquer dúvidas "
        "oriundas do presente contrato, com renúncia a qualquer outro, por mais privilegiado que seja.",
        styles["Corpo"],
    ))

    if contrato.get("observacoes"):
        story.append(Paragraph("8. OBSERVAÇÕES", styles["Secao"]))
        story.append(Paragraph(str(contrato["observacoes"]), styles["Corpo"]))

    # Local e data
    story.append(Spacer(1, 16))
    cidade = contrato.get("contratante_cidade") or "________________"
    story.append(Paragraph(
        "%s, %s." % (cidade, format_date(datetime.now().strftime("%Y-%m-%d"))),
        styles["Corpo"],
    ))

    # Assinaturas
    story.append(Spacer(1, 30))
    assinatura_data = [[
        Paragraph(
            "_________________________________<br/><b>CONTRATANTE</b><br/>%s<br/>CPF/CNPJ: %s"
            % (
                contrato.get("contratante_nome") or "",
                contrato.get("contratante_doc") or "",
            ),
            styles["Assinatura"],
        ),
        Paragraph(
            "_________________________________<br/><b>CONTRATADO</b><br/>%s<br/>CPF/CNPJ: %s"
            % (
                contrato.get("contratado_nome") or "",
                contrato.get("contratado_doc") or "",
            ),
            styles["Assinatura"],
        ),
    ]]
    t = Table(assinatura_data, colWidths=[8.5 * cm, 8.5 * cm])
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ]))
    story.append(t)

    story.append(Spacer(1, 20))
    story.append(Paragraph(
        "Documento gerado em %s — Sistema de Controle de Contratos"
        % datetime.now().strftime("%d/%m/%Y %H:%M"),
        styles["Rodape"],
    ))

    doc.build(story)
    return output_path


def gerar_pdf_consulta(contratos, filtros=None, output_path=None):
    """
    Gera PDF com a lista de contratos da consulta (filtros aplicados).
    """
    if output_path is None:
        output_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "static",
            "consulta_contratos_%s.pdf" % datetime.now().strftime("%Y%m%d_%H%M%S"),
        )
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="TituloConsulta", fontName=FONT_BOLD, fontSize=14, leading=18,
        alignment=TA_CENTER, textColor=PRIMARY, spaceAfter=8,
    ))
    styles.add(ParagraphStyle(
        name="FiltroInfo", fontName=FONT, fontSize=9, leading=12,
        alignment=TA_LEFT, textColor=GRAY, spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        name="Celula", fontName=FONT, fontSize=8, leading=10, textColor=black,
    ))
    styles.add(ParagraphStyle(
        name="CelulaBold", fontName=FONT_BOLD, fontSize=8, leading=10, textColor=black,
    ))
    styles.add(ParagraphStyle(
        name="RodapeConsulta", fontName=FONT, fontSize=8, alignment=TA_CENTER, textColor=GRAY,
    ))

    story = []
    story.append(Paragraph("RELATÓRIO DE CONSULTA DE CONTRATOS", styles["TituloConsulta"]))
    story.append(Paragraph(
        "Emitido em %s" % datetime.now().strftime("%d/%m/%Y %H:%M"),
        styles["FiltroInfo"],
    ))

    filtros = filtros or {}
    partes = []
    if filtros.get("status"):
        partes.append("Status: %s" % filtros["status"])
    if filtros.get("setor_nome"):
        partes.append("Setor: %s" % filtros["setor_nome"])
    preset_labels = {
        "vencidos": "Já vencidos",
        "mes": "Vencem neste mês",
        "30": "Próximos 30 dias",
        "60": "Próximos 60 dias",
        "90": "Próximos 90 dias",
    }
    if filtros.get("vencimento_preset"):
        partes.append("Vencimento: %s" % preset_labels.get(filtros["vencimento_preset"], filtros["vencimento_preset"]))
    if filtros.get("vencimento_de"):
        partes.append("Vencimento de: %s" % format_date(filtros["vencimento_de"]))
    if filtros.get("vencimento_ate"):
        partes.append("Vencimento até: %s" % format_date(filtros["vencimento_ate"]))
    if partes:
        story.append(Paragraph("Filtros: %s" % " | ".join(partes), styles["FiltroInfo"]))
    else:
        story.append(Paragraph("Filtros: nenhum (todos os contratos)", styles["FiltroInfo"]))

    story.append(Paragraph("Total de registros: <b>%d</b>" % len(contratos), styles["FiltroInfo"]))
    story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY, spaceAfter=10, spaceBefore=6))

    if not contratos:
        story.append(Paragraph("Nenhum contrato encontrado com os filtros informados.", styles["FiltroInfo"]))
    else:
        header = [
            Paragraph("<b>Número</b>", styles["CelulaBold"]),
            Paragraph("<b>Contratante</b>", styles["CelulaBold"]),
            Paragraph("<b>Contratado</b>", styles["CelulaBold"]),
            Paragraph("<b>Setor</b>", styles["CelulaBold"]),
            Paragraph("<b>Vencimento</b>", styles["CelulaBold"]),
            Paragraph("<b>Status</b>", styles["CelulaBold"]),
            Paragraph("<b>Valor Total</b>", styles["CelulaBold"]),
        ]
        rows = [header]
        total_geral = 0.0
        for c in contratos:
            try:
                total_geral += float(c.get("valor") or 0)
            except Exception:
                pass
            rows.append([
                Paragraph(str(c.get("numero") or "—"), styles["Celula"]),
                Paragraph(str(c.get("contratante_nome") or "—")[:28], styles["Celula"]),
                Paragraph(str(c.get("contratado_nome") or "—")[:28], styles["Celula"]),
                Paragraph(str(c.get("setor_nome") or "—")[:16], styles["Celula"]),
                Paragraph(format_date(c.get("data_fim")), styles["Celula"]),
                Paragraph(str(c.get("status") or "—"), styles["Celula"]),
                Paragraph(format_currency(c.get("valor", 0)), styles["Celula"]),
            ])

        col_widths = [2.4*cm, 3.6*cm, 3.6*cm, 2.4*cm, 2.2*cm, 1.8*cm, 2.5*cm]
        tabela = Table(rows, colWidths=col_widths, repeatRows=1)
        tabela.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), HexColor("#edf2f7")),
            ("GRID", (0, 0), (-1, -1), 0.4, HexColor("#cbd5e0")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        story.append(tabela)
        story.append(Spacer(1, 12))
        story.append(Paragraph(
            "Valor total dos contratos listados: <b>%s</b>" % format_currency(total_geral),
            styles["FiltroInfo"],
        ))

    story.append(Spacer(1, 16))
    story.append(Paragraph(
        "Sistema de Controle de Contratos — Relatório de consulta",
        styles["RodapeConsulta"],
    ))

    doc.build(story)
    return output_path
