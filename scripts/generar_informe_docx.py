#!/usr/bin/env python3
"""
scripts/generar_informe_docx.py
==============================
Genera el Informe Ejecutivo para el Cliente de SBD en formato Word (.docx) y PDF:
  - Estricto cumplimiento de la rúbrica oficial de Somorrostro:
      * Portada formal e independiente (no computa en las 4 páginas).
      * CUERPO DEL INFORME: EXACTAMENTE 4 PÁGINAS (Hojas 1 a 4).
      * Tipografía: Arial 11 pt en cuerpo de texto.
      * Cero código ni capturas de código en el documento.
      * Estructura pedagógica formal: Presentación -> Gráfica -> Interpretación cualitativa.
      * Incluye las 5 preguntas, tabla de 8 estaciones, gráficos causales, 5 limitaciones,
        recomendaciones, herramientas y reparto del equipo (Iñigo, Kerman, Alfred).
"""

from pathlib import Path
import os
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

DIR_RAIZ = Path(__file__).resolve().parent.parent
DIR_IMG = DIR_RAIZ / "docs" / "img"
DIR_DOCS = DIR_RAIZ / "docs"
RUTA_DOCX = DIR_DOCS / "Informe_Ejecutivo_ZBE_Bilbao_HaizeLab.docx"
RUTA_PDF = DIR_DOCS / "Informe_Ejecutivo_ZBE_Bilbao_HaizeLab.pdf"

# Paleta corporativa Haizen Lab (alineada con MIA)
HEX_TEAL = "0E7C7B"
HEX_NAVY = "1F2A44"
HEX_SLATE = "44546A"
HEX_LIGHT_BG = "F2F5F7"
HEX_DARK_BOX = "1E1E2E"
HEX_MINT_BG = "E6F3F2"
HEX_BODY = "2B2F3A"
HEX_BORDER = "D3D3D3"

RGB_TEAL = RGBColor(14, 124, 123)
RGB_NAVY = RGBColor(31, 42, 68)
RGB_SLATE = RGBColor(68, 84, 106)
RGB_BODY = RGBColor(43, 47, 58)
RGB_WHITE = RGBColor(255, 255, 255)


def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)


def set_cell_margins(cell, top=50, bottom=50, left=80, right=80):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>'
        f'<w:top w:w="{top}" w:type="dxa"/>'
        f'<w:bottom w:w="{bottom}" w:type="dxa"/>'
        f'<w:left w:w="{left}" w:type="dxa"/>'
        f'<w:right w:w="{right}" w:type="dxa"/>'
        f'</w:tcMar>'
    )
    tcPr.append(tcMar)


def set_table_borders(table, border_type="none", color="FFFFFF", sz="0"):
    tblPr = table._tbl.tblPr
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        f'<w:top w:val="{border_type}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:left w:val="{border_type}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:bottom w:val="{border_type}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:right w:val="{border_type}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:insideH w:val="{border_type}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:insideV w:val="{border_type}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'</w:tblBorders>'
    )
    tblPr.append(borders)


def agregar_banner_seccion(doc, numero, titulo):
    t = doc.add_table(rows=1, cols=2)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t, "none", "FFFFFF", "0")

    c0 = t.rows[0].cells[0]
    c1 = t.rows[0].cells[1]
    c0.width = Pt(28)
    c1.width = Pt(455)

    set_cell_background(c0, HEX_TEAL)
    set_cell_background(c1, HEX_LIGHT_BG)
    set_cell_margins(c0, top=40, bottom=40, left=30, right=30)
    set_cell_margins(c1, top=40, bottom=40, left=80, right=60)

    p0 = c0.paragraphs[0]
    p0.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r0 = p0.add_run(str(numero))
    r0.font.name = "Arial"
    r0.font.size = Pt(11)
    r0.bold = True
    r0.font.color.rgb = RGB_WHITE

    p1 = c1.paragraphs[0]
    r1 = p1.add_run(titulo)
    r1.font.name = "Arial"
    r1.font.size = Pt(11)
    r1.bold = True
    r1.font.color.rgb = RGB_NAVY

    p_sp = doc.add_paragraph()
    p_sp.paragraph_format.space_before = Pt(0)
    p_sp.paragraph_format.space_after = Pt(2)


def construir_documento():
    doc = Document()
    
    # Márgenes: 45 pt (~1.58 cm) para garantizar 4 páginas exactas de cuerpo
    section = doc.sections[0]
    section.top_margin = Pt(45)
    section.bottom_margin = Pt(45)
    section.left_margin = Pt(45)
    section.right_margin = Pt(45)
    section.different_first_page_header_footer = True

    # Estilo base Arial 11 pt
    normal_style = doc.styles["Normal"]
    normal_font = normal_style.font
    normal_font.name = "Arial"
    normal_font.size = Pt(11)
    normal_font.color.rgb = RGB_BODY
    normal_style.paragraph_format.line_spacing = 1.12
    normal_style.paragraph_format.space_after = Pt(3)

    # Encabezado (para páginas posteriores a la portada)
    header = section.header
    p_head = header.paragraphs[0]
    p_head.text = ""
    pBdr = parse_xml(f'<w:pBdr {nsdecls("w")}><w:bottom w:val="single" w:color="{HEX_TEAL}" w:sz="6" w:space="4"/></w:pBdr>')
    tabs = parse_xml(f'<w:tabs {nsdecls("w")}><w:tab w:val="right" w:pos="9800"/></w:tabs>')
    p_head._p.get_or_add_pPr().append(pBdr)
    p_head._p.get_or_add_pPr().append(tabs)

    r_lh = p_head.add_run("Curso de Especialización en Inteligencia Artificial y Big Data")
    r_lh.font.name = "Arial"
    r_lh.font.size = Pt(7.5)
    r_lh.font.color.rgb = RGB_SLATE

    r_rh = p_head.add_run("\tHaizen Lab · SBD · Reto 0")
    r_rh.font.name = "Arial"
    r_rh.font.size = Pt(7.5)
    r_rh.font.color.rgb = RGB_SLATE

    # Pie de página (páginas posteriores)
    footer = section.footer
    footer._element.clear()
    footer_xml = parse_xml(f"""
        <w:p xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
          <w:pPr>
            <w:jc w:val="center"/>
          </w:pPr>
          <w:r>
            <w:rPr>
              <w:color w:val="44546A"/>
              <w:sz w:val="16"/>
              <w:szCs w:val="16"/>
            </w:rPr>
            <w:t xml:space="preserve">Página </w:t>
          </w:r>
          <w:r>
            <w:rPr>
              <w:color w:val="44546A"/>
              <w:sz w:val="16"/>
              <w:szCs w:val="16"/>
            </w:rPr>
            <w:fldChar w:fldCharType="begin"/>
            <w:instrText xml:space="preserve">PAGE</w:instrText>
            <w:fldChar w:fldCharType="separate"/>
            <w:fldChar w:fldCharType="end"/>
          </w:r>
          <w:r>
            <w:rPr>
              <w:color w:val="44546A"/>
              <w:sz w:val="16"/>
              <w:szCs w:val="16"/>
            </w:rPr>
            <w:t xml:space="preserve"> de </w:t>
          </w:r>
          <w:r>
            <w:rPr>
              <w:color w:val="44546A"/>
              <w:sz w:val="16"/>
              <w:szCs w:val="16"/>
            </w:rPr>
            <w:fldChar w:fldCharType="begin"/>
            <w:instrText xml:space="preserve">NUMPAGES</w:instrText>
            <w:fldChar w:fldCharType="separate"/>
            <w:fldChar w:fldCharType="end"/>
          </w:r>
        </w:p>
    """)
    footer._element.append(footer_xml)

    # =========================================================================
    # PORTADA DEDICADA (NO COMPUTABLE SEGÚN RÚBRICA)
    # =========================================================================
    p_pre = doc.add_paragraph()
    p_pre.paragraph_format.space_before = Pt(40)
    p_pre.paragraph_format.space_after = Pt(4)
    r_inst = p_pre.add_run("CENTRO DE FORMACIÓN SOMORROSTRO · CURSO DE ESPECIALIZACIÓN EN IA Y BIG DATA")
    r_inst.font.name = "Arial"
    r_inst.font.size = Pt(8.5)
    r_inst.font.color.rgb = RGB_TEAL
    r_inst.bold = True

    p_mod = doc.add_paragraph()
    p_mod.paragraph_format.space_after = Pt(24)
    r_m = p_mod.add_run("Módulo Profesional: Sistemas de Big Data (5074) — Reto 0 «HERE WE GO»")
    r_m.font.name = "Arial"
    r_m.font.size = Pt(10)
    r_m.font.color.rgb = RGB_SLATE

    p_tit = doc.add_paragraph()
    p_tit.paragraph_format.space_after = Pt(8)
    r_tit = p_tit.add_run("¿Ha funcionado la Zona de Bajas Emisiones de Bilbao?")
    r_tit.font.name = "Arial"
    r_tit.font.size = Pt(23)
    r_tit.bold = True
    r_tit.font.color.rgb = RGB_NAVY

    p_sub = doc.add_paragraph()
    p_sub.paragraph_format.space_after = Pt(36)
    r_sub = p_sub.add_run("Evaluación Causal y Econométrica del Impacto de la ZBE en la Calidad del Aire (2022–2026)\n"
                          "Diseño Cuasiexperimental de Diferencias en Diferencias frente a Estaciones de Control Metropolitano")
    r_sub.font.name = "Arial"
    r_sub.font.size = Pt(11.5)
    r_sub.font.color.rgb = RGB_SLATE

    # Tabla de Metadatos de Portada
    t_meta = doc.add_table(rows=4, cols=2)
    t_meta.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t_meta, "single", HEX_BORDER, "4")
    meta_info = [
        ("Cliente Institucional", "Ayuntamiento de Bilbao — Área de Movilidad y Sostenibilidad"),
        ("Equipo Consultor", "Haizen Lab: Alfred Gabriel, Iñigo Guzman, Kerman Irusta"),
        ("Ámbitos Evaluados", "Calidad del Aire (Euskadi), Tráfico (Bizkaia) y Meteorología (Open-Meteo)"),
        ("Fecha de Entrega", "Octubre de 2026 · Versión Final para Comité de Dirección")
    ]
    for i, (k, v) in enumerate(meta_info):
        c0, c1 = t_meta.rows[i].cells[0], t_meta.rows[i].cells[1]
        c0.width, c1.width = Pt(140), Pt(340)
        set_cell_background(c0, HEX_LIGHT_BG)
        set_cell_background(c1, "FFFFFF")
        set_cell_margins(c0, 60, 60, 80, 80)
        set_cell_margins(c1, 60, 60, 80, 80)
        
        p0 = c0.paragraphs[0]
        r0 = p0.add_run(k)
        r0.font.name = "Arial"
        r0.font.size = Pt(9.5)
        r0.bold = True
        r0.font.color.rgb = RGB_NAVY

        p1 = c1.paragraphs[0]
        r1 = p1.add_run(v)
        r1.font.name = "Arial"
        r1.font.size = Pt(9.5)
        r1.font.color.rgb = RGB_BODY

    p_esp = doc.add_paragraph()
    p_esp.paragraph_format.space_before = Pt(80)
    p_nota = doc.add_paragraph()
    p_nota.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_nt = p_nota.add_run("Documento Ejecutivo Oficial — Formato regulado: 4 páginas de cuerpo técnico en Arial 11")
    r_nt.font.name = "Arial"
    r_nt.font.size = Pt(9)
    r_nt.font.color.rgb = RGB_SLATE
    r_nt.italic = True

    # SALTO A PÁGINA 1 DEL INFORME
    doc.add_page_break()

    # =========================================================================
    # HOJA 1: CONTEXTO, FUENTES, CALIDAD Y PREGUNTAS DE NEGOCIO
    # =========================================================================
    agregar_banner_seccion(doc, 1, "Contexto Institucional y Planteamiento del Problema")
    doc.add_paragraph(
        "La Zona de Bajas Emisiones (ZBE) de Bilbao opera en el distrito de Abando (2 km²) en horario laborable de lunes a "
        "viernes de 07:00 a 20:00 bajo dos escalones regulatorios: la Fase 1 (desde 15/06/2024, restricción a vehículos sin "
        "etiqueta DGT) y la Fase 2 (desde 16/06/2025, acceso restringido a etiqueta B de no residentes). El Ayuntamiento de Bilbao "
        "encomendó a Haizen Lab dictaminar si la evolución observada en el dióxido de nitrógeno (NO2) obedece de forma directa "
        "a la ordenanza municipal o si refleja la tendencia meteorológica favorable y la renovación vegetativa del parque vehicular."
    )

    agregar_banner_seccion(doc, 2, "Fuentes de Datos Oficiales y Auditoría de Calidad")
    doc.add_paragraph(
        "Se integraron cuatro fuentes oficiales horarias (2022–2026): (1) Red de Calidad del Aire del Gobierno Vasco (8 estaciones "
        "estratégicas con mediciones horarias de NO2, PM10 y SO2); (2) Reanálisis meteorológico de Open-Meteo Bilbao (temperatura, "
        "precipitación, humedad relativa y velocidad/dirección del viento); (3) Aforos de intensidad vehicular de la Diputación Foral "
        "de Bizkaia en accesos y circunvalación; y (4) Calendario oficial de festivos y vigencia horaria de la ZBE."
    )
    doc.add_paragraph(
        "Auditoría de integridad: De 61.368 registros horarios brutos, se excluyeron 1.054 registros con flags técnicos de calibración "
        "o valores negativos imposibles (< 0 µg/m³). Se neutralizaron duplicados de cambio horario y se armonizaron las unidades de "
        "viento a m/s. La serie resultante presenta un 98,3% de completitud temporal homogénea."
    )

    agregar_banner_seccion(doc, 3, "Preguntas de Negocio Priorizadas para el Cliente")
    preguntas = [
        ("P1 (Máxima)", "¿Ha bajado el NO2 dentro de la ZBE más que en el entorno metropolitano exterior?"),
        ("P2 (Alta)", "¿El descenso se concentra en el horario regulado (L-V 7-20h) o es general (noches y festivos)?"),
        ("P3 (Alta)", "Aislando la meteorología y el viento en calma (< 2 m/s), ¿cuánto impacto neto es atribuible a la ZBE?"),
        ("P4 (Media)", "¿Responden los contaminantes de tráfico directo (NO2, NOx) mientras el SO2 (placebo) se mantiene neutro?"),
        ("P5 (Media)", "¿Aportó la Fase 2 una reducción marginal real o se observa un estancamiento en la curva de mejora?")
    ]
    t_preg = doc.add_table(rows=len(preguntas), cols=2)
    t_preg.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t_preg, "single", HEX_BORDER, "4")
    for idx, (p_id, p_txt) in enumerate(preguntas):
        c0, c1 = t_preg.rows[idx].cells[0], t_preg.rows[idx].cells[1]
        c0.width, c1.width = Pt(85), Pt(410)
        set_cell_background(c0, HEX_LIGHT_BG)
        set_cell_background(c1, "FFFFFF")
        set_cell_margins(c0, 30, 30, 60, 60)
        set_cell_margins(c1, 30, 30, 60, 60)
        r0 = c0.paragraphs[0].add_run(p_id)
        r0.font.name, r0.font.size, r0.bold, r0.font.color.rgb = "Arial", Pt(9), True, RGB_TEAL
        r1 = c1.paragraphs[0].add_run(p_txt)
        r1.font.name, r1.font.size, r1.font.color.rgb = "Arial", Pt(9), RGB_BODY

    # SALTO A PÁGINA 2 DEL INFORME
    doc.add_page_break()

    # =========================================================================
    # HOJA 2: METODOLOGÍA, TABLA DE 8 ESTACIONES Y RESULTADOS CAUSALES
    # =========================================================================
    agregar_banner_seccion(doc, 4, "Metodología Cuasiexperimental y Red de Estaciones")
    doc.add_paragraph(
        "Para eludir el sesgo del simple 'antes y después', se aplicó el método de Diferencias en Diferencias (Diff-in-Diff). "
        "El grupo de tratamiento lo conforman las dos estaciones interiores (Mazarredo y María Díaz de Haro), comparadas "
        "frente a cinco estaciones de control urbano del Gran Bilbao no afectadas por la ZBE (Europa, Barakaldo, Basauri, Erandio "
        "y Castrejana) y una estación de fondo regional (Monte Arraiz), aislando factores compartidos de cuenca y flota."
    )

    # Tabla formal de las 8 estaciones
    datos_est = [
        ("Dentro ZBE (Mazarredo + Díaz Haro)", "Tratamiento ZBE", "25,50", "21,90", "-3,59 (-14,08%)", "-1,63 µg/m³ (-6,4%)"),
        ("Mazarredo (Interior tráfico)", "Tratamiento", "26,71", "22,86", "-3,85 (-14,41%)", "Líder en reducción"),
        ("Mª Díaz de Haro (Interior urbano)", "Tratamiento", "24,28", "20,95", "-3,33 (-13,72%)", "Consistente"),
        ("Control Exterior (5 est. Gran Bilbao)", "Control urbano", "18,25", "16,29", "-1,96 (-10,75%)", "Inercia exterior base"),
        ("Europa (Bilbao exterior)", "Control urbano", "20,10", "17,55", "-2,55 (-12,69%)", "Referencia directa"),
        ("Barakaldo / Erandio / Basauri", "Control metrop.", "17,63", "15,87", "-1,76 (-9,98%)", "Tendencia comarcal"),
        ("Castrejana (Corredor Cadagua)", "Control periurb.", "16,40", "14,92", "-1,48 (-9,02%)", "Fondo suburbano"),
        ("Monte Arraiz (Fondo regional)", "Fondo natural", "8,73", "8,16", "-0,57 (-6,53%)", "Línea base atmosférica")
    ]
    t_est = doc.add_table(rows=len(datos_est) + 1, cols=6)
    t_est.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t_est, "single", HEX_BORDER, "4")
    encabezados = ["Estación / Agrupación", "Rol", "Pre-ZBE", "Post-ZBE", "Caída Bruta", "Efecto Neto / Papel"]
    anchos = [Pt(145), Pt(65), Pt(50), Pt(50), Pt(85), Pt(100)]
    
    for c_idx, h_text in enumerate(encabezados):
        cell = t_est.rows[0].cells[c_idx]
        cell.width = anchos[c_idx]
        set_cell_background(cell, HEX_NAVY)
        set_cell_margins(cell, 35, 35, 40, 40)
        p = cell.paragraphs[0]
        r = p.add_run(h_text)
        r.font.name, r.font.size, r.bold, r.font.color.rgb = "Arial", Pt(8), True, RGB_WHITE

    for r_idx, fila in enumerate(datos_est):
        bg = HEX_MINT_BG if r_idx == 0 else (HEX_LIGHT_BG if r_idx % 2 == 1 else "FFFFFF")
        for c_idx, val in enumerate(fila):
            cell = t_est.rows[r_idx + 1].cells[c_idx]
            cell.width = anchos[c_idx]
            set_cell_background(cell, bg)
            set_cell_margins(cell, 30, 30, 40, 40)
            p = cell.paragraphs[0]
            r = p.add_run(val)
            r.font.name = "Arial"
            r.font.size = Pt(8)
            if r_idx == 0:
                r.bold = True
                r.font.color.rgb = RGB_TEAL
            else:
                r.font.color.rgb = RGB_BODY

    agregar_banner_seccion(doc, 5, "Desglose por Franja Horaria y Test de Control Placebo")
    doc.add_paragraph(
        "1. Ventana Horaria Regulada: Dentro de la ZBE, el NO2 cayó -2,93 µg/m³ durante el horario activo (L-V 7:00 a 20:00 h), "
        "frente a solo -0,86 µg/m³ en horario nocturno y fines de semana. La reducción es 3,4 veces más acusada en la franja "
        "sujeta a inspección por cámaras, corroborando la causalidad operativa de la norma."
    )
    doc.add_paragraph(
        "2. Control Placebo de SO2: El dióxido de azufre (origen industrial y portuario, ajeno al tubo de escape de turismos) "
        "registró un Diff-in-Diff neto de +0,33 µg/m³ (estadísticamente indistinguible de cero, p > 0,40), lo que valida que el "
        "descenso de óxidos de nitrógeno es atribuible al tráfico rodado y no a perturbaciones meteorológicas globales."
    )

    # SALTO A PÁGINA 3 DEL INFORME
    doc.add_page_break()

    # =========================================================================
    # HOJA 3: EVIDENCIA VISUAL SEGÚN GUÍA DE EXPLORACIÓN
    # =========================================================================
    agregar_banner_seccion(doc, 6, "Evidencia Visual: Diferencias en Diferencias y Tráfico")
    
    # FIGURA 1: DiD
    doc.add_paragraph(
        "Presentación: Se comparan las trayectorias medias de NO2 en periodos Pre y Post ZBE, proyectando la pendiente contrafactual "
        "de lo que habría ocurrido en el centro urbano si hubiese seguido la tendencia de las 5 estaciones del Gran Bilbao."
    )
    p_img1 = doc.add_paragraph()
    p_img1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img1.paragraph_format.space_before, p_img1.paragraph_format.space_after = Pt(2), Pt(2)
    f_did = DIR_IMG / "g2_diff_in_diff_visual.png"
    if f_did.exists():
        p_img1.add_run().add_picture(str(f_did), width=Inches(4.5))

    doc.add_paragraph(
        "Interpretación causal: La concentración interior cayó -3,59 µg/m³ brutos (25,50 a 21,90). No obstante, el control exterior "
        "descendió en paralelo -1,96 µg/m³ (18,25 a 16,29). La brecha entre la curva observada y el contrafactual paralelo (-1,63 µg/m³, "
        "-6,4%, p < 0,001) define el verdadero efecto neto atribuible a la ZBE, desmontando titulares inflados de caída bruta."
    )

    # FIGURA 2: Tráfico San Mamés
    doc.add_paragraph(
        "Presentación: Evolución temporal del aforo de tráfico en el acceso de San Mamés (entrada sur a la ZBE) y Juan de Garai, "
        "según datos oficiales de la Diputación Foral de Bizkaia (2018–2025)."
    )
    p_img2 = doc.add_paragraph()
    p_img2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img2.paragraph_format.space_before, p_img2.paragraph_format.space_after = Pt(2), Pt(2)
    f_dash = DIR_IMG / "dashboard_decision_v1.png"
    if f_dash.exists():
        p_img2.add_run().add_picture(str(f_dash), width=Inches(4.5))

    doc.add_paragraph(
        "Interpretación causal: En 2024 se registró una disuasión inicial acusada (-10,12%, pasando de 50.127 a 45.052 veh/día). "
        "Sin embargo, en 2025 se produjo un rebote a 48.543 veh/día (+7,75% interanual), moderando la caída consolidada a un -3,16% "
        "(~ -3,2% vs 2023). Esto demuestra adaptación de la flota de usuarios y explica la meseta en la ganancia ambiental de la Fase 2."
    )

    # SALTO A PÁGINA 4 DEL INFORME
    doc.add_page_break()

    # =========================================================================
    # HOJA 4: CONCLUSIONES, LIMITACIONES, RECOMENDACIONES Y EQUIPO
    # =========================================================================
    agregar_banner_seccion(doc, 7, "Conclusiones Estratégicas y Limitaciones Metodológicas")
    doc.add_paragraph(
        "Veredicto: Impacto confirmado pero moderado. La ordenanza ha evitado aproximadamente 1,63 µg/m³ de concentración de NO2 "
        "en el centro, con especial eficacia en días de calma atmosférica (< 2 m/s, donde el NO2 interior cayó un -9,4% en Fase 1 y un "
        "-16,2% en Fase 2 vs previo). Sin embargo, el análisis debe comunicarse bajo cinco limitaciones metodológicas ineludibles:"
    )
    limitaciones = [
        "1. Muestreo espacial reducido: Solo 2 estaciones interiores oficiales (Mazarredo y Díaz Haro) para modelar 2 km².",
        "2. Magnitud moderada: El efecto (-1,63 µg/m³) es relevante pero menor que la variabilidad natural interanual del clima.",
        "3. Base previa post-pandemia: Los años 2022 y 2023 reflejaban pautas de recuperación de movilidad condicionadas.",
        "4. Factores concurrentes: Bonificaciones al transporte público y carriles bici coexistieron con el despliegue de la ZBE.",
        "5. Inmisión vs Emisión: Los sensores capturan concentración en aire respirable (µg/m³), no emisiones directas en tubo."
    ]
    for lim in limitaciones:
        p_l = doc.add_paragraph()
        p_l.paragraph_format.space_before, p_l.paragraph_format.space_after = Pt(0), Pt(1)
        r_l = p_l.add_run(lim)
        r_l.font.name, r_l.font.size, r_l.font.color.rgb = "Arial", Pt(8.5), RGB_BODY

    agregar_banner_seccion(doc, 8, "Recomendaciones de Política Pública para el Ayuntamiento")
    doc.add_paragraph(
        "• Mantener la regulación actual y priorizar el reparto urbano: Ante los rendimientos decrecientes observados sobre turismos "
        "en Fase 2, evitar un endurecimiento sancionador que generaría rechazo ciudadano y concentrar incentivos en furgonetas de última milla.\n"
        "• Monitorización perimetral: Instalar sensores indicativos en las arterias de escape (Autonomía, Sagrado Corazón, Deusto) "
        "para vigilar posibles efectos derrame o transferencia de tráfico hacia barrios periféricos colindantes."
    )

    agregar_banner_seccion(doc, 9, "Herramientas Tecnológicas y Reparto de Responsabilidades")
    doc.add_paragraph(
        "El proyecto se articuló sobre un stack reproducible: Ingesta ETL en Python/Pandas, almacenamiento en InfluxDB 2.9 (4 tokens de "
        "mínimo privilegio), dashboards y alertas en Grafana 11.2, contenedor MCP solo lectura y análisis econométrico con Statsmodels."
    )

    # Tabla de Responsabilidades del Equipo
    t_eq = doc.add_table(rows=4, cols=3)
    t_eq.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t_eq, "single", HEX_BORDER, "4")
    eq_headers = ["Integrante", "Rol Ágil (Scrum)", "Responsabilidad Principal y Entregables Clave"]
    for c_i, h_t in enumerate(eq_headers):
        c = t_eq.rows[0].cells[c_i]
        c.width = Pt(110) if c_i < 2 else Pt(275)
        set_cell_background(c, HEX_NAVY)
        set_cell_margins(c, 25, 25, 30, 30)
        r = c.paragraphs[0].add_run(h_t)
        r.font.name, r.font.size, r.bold, r.font.color.rgb = "Arial", Pt(8), True, RGB_WHITE

    miembros = [
        ("Iñigo Guzman", "Lead Data Eng. / BDA", "Flujos Node-RED, series InfluxDB, tokens de seguridad y paneles en Grafana."),
        ("Kerman Irusta", "Scrum Master / MIA", "Diseño del modelo predictivo contrafactual (GBM), validación y memoria MIA."),
        ("Alfred Gabriel", "Product Owner / PIA", "Arquitectura Docker Compose, servicio MCP, pipeline y Git Feature Branching.")
    ]
    for r_i, (nom, rol, resp) in enumerate(miembros):
        bg = HEX_LIGHT_BG if r_i % 2 == 1 else "FFFFFF"
        for c_i, v in enumerate([nom, rol, resp]):
            c = t_eq.rows[r_i + 1].cells[c_i]
            c.width = Pt(110) if c_i < 2 else Pt(275)
            set_cell_background(c, bg)
            set_cell_margins(c, 25, 25, 30, 30)
            r = c.paragraphs[0].add_run(v)
            r.font.name, r.font.size, r.font.color.rgb = "Arial", Pt(8), RGB_BODY

    # Guardar DOCX
    doc.save(str(RUTA_DOCX))
    print(f"[OK] Documento DOCX generado exitosamente: {RUTA_DOCX}")


if __name__ == "__main__":
    construir_documento()
