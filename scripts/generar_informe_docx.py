#!/usr/bin/env python3
"""
scripts/generar_informe_docx.py
==============================
Genera el Informe Ejecutivo para el Cliente de SBD en formato Word (.docx)
reproduciendo al 100% la estética visual, paleta cromática, tipografía y
componentes modulares de docs/MIA_Haizen_Lab.docx:
  - Márgenes: 55 pt (1.94 cm)
  - Paleta:
      Primario / Banners / Cabeceras: #0E7C7B (Teal corporativo)
      Títulos principales: #1F2A44 (Azul medianoche)
      Subtítulos y metadatos: #44546A (Azul pizarra)
      Fondos de tarjeta y filas alternas: #F2F5F7 (Gris frío suave)
      Fondo de fórmulas / ecuaciones: #1E1E2E (Pizarra oscuro)
      Fondo de destacados: #E6F3F2 (Menta suave)
      Texto general: #2B2F3A (Gris carbón oscuro)
  - Componentes:
      * Barra superior de metadatos (Tabla 1x4 sin bordes)
      * Encabezado y pie de página con línea teal y número de página
      * Banners de sección de 2 columnas (número teal + título gris)
      * Tarjetas de fases (1x2) y cajas de fórmula destacada
      * Diagrama secuencial de pipeline (Datos -> Limpieza -> Join -> Análisis -> Decisión)
      * Tablas estilizadas con bordes sutiles y padding
      * Figuras integradas con Presentación, Gráfica e Interpretación causal
      * Tabla final de checklist de verificación de rúbrica
"""

from pathlib import Path
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

# Paleta de colores oficial (idéntica a MIA_Haizen_Lab)
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
    """Aplica color de fondo a una celda."""
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)


def set_cell_margins(cell, top=60, bottom=60, left=100, right=100):
    """Aplica relleno interior (padding) a una celda en dxa."""
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
    """Configura bordes globales de tabla."""
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


def configurar_encabezado_pie(doc):
    """Configura el encabezado con borde inferior teal y pie con paginación."""
    section = doc.sections[0]
    section.top_margin = Pt(55)
    section.bottom_margin = Pt(55)
    section.left_margin = Pt(55)
    section.right_margin = Pt(55)

    # Encabezado
    header = section.header
    p_head = header.paragraphs[0]
    p_head.text = ""
    pBdr = parse_xml(
        f'<w:pBdr {nsdecls("w")}><w:bottom w:val="single" w:color="{HEX_TEAL}" w:sz="6" w:space="4"/></w:pBdr>'
    )
    tabs = parse_xml(
        f'<w:tabs {nsdecls("w")}><w:tab w:val="right" w:pos="9706"/></w:tabs>'
    )
    p_head._p.get_or_add_pPr().append(pBdr)
    p_head._p.get_or_add_pPr().append(tabs)

    r_left = p_head.add_run("Curso de Especialización en Inteligencia Artificial y Big Data")
    r_left.font.name = "Arial"
    r_left.font.size = Pt(7.5)
    r_left.font.color.rgb = RGB_SLATE

    r_right = p_head.add_run("\tHaizen Lab · SBD · Reto 0")
    r_right.font.name = "Arial"
    r_right.font.size = Pt(7.5)
    r_right.font.color.rgb = RGB_SLATE

    # Pie de página con campos dinámicos PAGE y NUMPAGES
    footer = section.footer
    p_foot = footer.paragraphs[0]
    p_foot.text = ""
    p_foot.alignment = WD_ALIGN_PARAGRAPH.CENTER

    r_f1 = p_foot.add_run("Página ")
    r_f1.font.name = "Arial"
    r_f1.font.size = Pt(8)
    r_f1.font.color.rgb = RGB_SLATE

    fld1 = parse_xml(r'<w:fldSimple %s w:instr="PAGE"/>' % nsdecls('w'))
    p_foot._p.append(fld1)

    r_f2 = p_foot.add_run(" de ")
    r_f2.font.name = "Arial"
    r_f2.font.size = Pt(8)
    r_f2.font.color.rgb = RGB_SLATE

    fld2 = parse_xml(r'<w:fldSimple %s w:instr="NUMPAGES"/>' % nsdecls('w'))
    p_foot._p.append(fld2)


def agregar_banner_seccion(doc, numero, titulo):
    """Crea el banner característico de 2 columnas: número en teal y título en gris suave."""
    t = doc.add_table(rows=1, cols=2)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t, "none", "FFFFFF", "0")

    c0 = t.rows[0].cells[0]
    c1 = t.rows[0].cells[1]
    c0.width = Pt(38.8)
    c1.width = Pt(446.5)

    set_cell_background(c0, HEX_TEAL)
    set_cell_background(c1, HEX_LIGHT_BG)
    set_cell_margins(c0, top=70, bottom=70, left=40, right=40)
    set_cell_margins(c1, top=70, bottom=70, left=120, right=100)

    p0 = c0.paragraphs[0]
    p0.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r0 = p0.add_run(str(numero))
    r0.font.name = "Arial"
    r0.font.size = Pt(13)
    r0.bold = True
    r0.font.color.rgb = RGB_WHITE

    p1 = c1.paragraphs[0]
    r1 = p1.add_run(titulo)
    r1.font.name = "Arial"
    r1.font.size = Pt(13)
    r1.bold = True
    r1.font.color.rgb = RGB_NAVY

    # Espacio tras el banner
    p_space = doc.add_paragraph()
    p_space.paragraph_format.space_before = Pt(0)
    p_space.paragraph_format.space_after = Pt(4)


def agregar_caja_formula(doc, texto_formula):
    """Crea la caja oscura destacada para fórmulas o definiciones matemáticas."""
    t = doc.add_table(rows=1, cols=1)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t, "none", "FFFFFF", "0")
    c = t.rows[0].cells[0]
    c.width = Pt(485.3)
    set_cell_background(c, HEX_DARK_BOX)
    set_cell_margins(c, top=80, bottom=80, left=120, right=120)

    p = c.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(texto_formula)
    r.font.name = "Consolas"
    r.font.size = Pt(10)
    r.font.color.rgb = RGB_WHITE

    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def agregar_tarjetas_fase(doc, tit1, txt1, tit2, txt2):
    """Crea una fila de dos tarjetas de fondo claro para contrastar fases o periodos."""
    t = doc.add_table(rows=1, cols=2)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t, "none", "FFFFFF", "0")

    for idx, (tit, txt) in enumerate([(tit1, txt1), (tit2, txt2)]):
        c = t.rows[0].cells[idx]
        c.width = Pt(242.6)
        set_cell_background(c, HEX_LIGHT_BG)
        set_cell_margins(c, top=70, bottom=70, left=100, right=100)

        p0 = c.paragraphs[0]
        p0.paragraph_format.space_after = Pt(2)
        r0 = p0.add_run(tit)
        r0.font.name = "Arial"
        r0.font.size = Pt(8)
        r0.bold = True
        r0.font.color.rgb = RGB_TEAL

        p1 = c.add_paragraph()
        p1.paragraph_format.space_after = Pt(0)
        r1 = p1.add_run(txt)
        r1.font.name = "Arial"
        r1.font.size = Pt(9.5)
        r1.font.color.rgb = RGB_BODY

    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def construir_documento():
    doc = Document()
    configurar_encabezado_pie(doc)

    # Estilo base
    normal_style = doc.styles["Normal"]
    normal_font = normal_style.font
    normal_font.name = "Arial"
    normal_font.size = Pt(10.5)
    normal_font.color.rgb = RGB_BODY
    normal_style.paragraph_format.line_spacing = 1.15
    normal_style.paragraph_format.space_after = Pt(4)

    # =========================================================================
    # BARRA SUPERIOR DE METADATOS (Tabla 1x4 idéntica a MIA)
    # =========================================================================
    t_meta = doc.add_table(rows=1, cols=4)
    t_meta.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t_meta, "none", "FFFFFF", "0")

    col_widths = [Pt(130), Pt(145), Pt(150), Pt(60)]
    meta_info = [
        ("EQUIPO", "Haizen Lab: Iñigo, Kerman y Alfred"),
        ("MÓDULO", "Sistemas de Big Data (5074) · CF Somorrostro"),
        ("CLIENTE (SIMULADO)", "Ayuntamiento de Bilbao, movilidad y sostenibilidad"),
        ("FECHA", "07/10/2026"),
    ]

    for i, (k, v) in enumerate(meta_info):
        c = t_meta.rows[0].cells[i]
        c.width = col_widths[i]
        set_cell_margins(c, top=40, bottom=60, left=40, right=40)
        p0 = c.paragraphs[0]
        p0.paragraph_format.space_after = Pt(1)
        r0 = p0.add_run(k)
        r0.font.name = "Arial"
        r0.font.size = Pt(8)
        r0.bold = True
        r0.font.color.rgb = RGB_TEAL

        p1 = c.add_paragraph()
        p1.paragraph_format.space_after = Pt(0)
        r1 = p1.add_run(v)
        r1.font.name = "Arial"
        r1.font.size = Pt(9.5)
        r1.font.color.rgb = RGB_BODY

    # Línea separadora sutil
    doc.add_paragraph().paragraph_format.space_after = Pt(4)

    # =========================================================================
    # BLOQUE DE TÍTULO PRINCIPAL
    # =========================================================================
    p_ov = doc.add_paragraph()
    p_ov.paragraph_format.space_after = Pt(2)
    r_ov = p_ov.add_run("SISTEMAS DE BIG DATA · RETO 0 «HERE WE GO»")
    r_ov.font.name = "Arial"
    r_ov.font.size = Pt(10)
    r_ov.bold = True
    r_ov.font.color.rgb = RGB_TEAL

    p_t = doc.add_paragraph()
    p_t.paragraph_format.space_after = Pt(2)
    r_t = p_t.add_run("¿Ha funcionado la Zona de Bajas Emisiones de Bilbao?")
    r_t.font.name = "Arial"
    r_t.font.size = Pt(20)
    r_t.bold = True
    r_t.font.color.rgb = RGB_NAVY

    p_sub = doc.add_paragraph()
    p_sub.paragraph_format.space_after = Pt(8)
    r_sub = p_sub.add_run("Evaluación multivariable de impacto sobre la calidad del aire y movilidad urbana (2022–2026)")
    r_sub.font.name = "Arial"
    r_sub.font.size = Pt(12)
    r_sub.font.color.rgb = RGB_SLATE

    # Objetivo del documento
    p_obj_h = doc.add_paragraph()
    p_obj_h.paragraph_format.space_after = Pt(2)
    r_obj_h = p_obj_h.add_run("Objetivo del documento")
    r_obj_h.font.name = "Arial"
    r_obj_h.font.size = Pt(12)
    r_obj_h.bold = True
    r_obj_h.font.color.rgb = RGB_NAVY

    doc.add_paragraph(
        "Se presenta el informe de consultoría ejecutiva para el Ayuntamiento de Bilbao elaborado por "
        "Haizen Lab en el módulo de Sistemas de Big Data (SBD). El documento evalúa el impacto empírico "
        "de la Zona de Bajas Emisiones (ZBE) en el distrito de Abando sobre las concentraciones horarias de NO2, "
        "aislando el efecto de la ordenanza respecto a la meteorología y las tendencias del tráfico mediante un "
        "diseño cuasiexperimental de Diferencias en Diferencias (Diff-in-Diff) y contraste con aforos vehiculares."
    )

    # =========================================================================
    # SECCIÓN 1: PROBLEMA DEL CLIENTE Y REQUISITOS
    # =========================================================================
    agregar_banner_seccion(doc, 1, "Problema del cliente y preguntas de negocio")

    doc.add_paragraph(
        "El Ayuntamiento de Bilbao implantó la ZBE en el distrito de Abando (~2 km², regulado por 27 cámaras ANPR) "
        "para reducir los contaminantes derivados del tráfico fósil. El horario de restricción abarca de lunes a viernes "
        "laborables de 7:00 a 20:00 h, desplegado en dos etapas progresivas:"
    )

    agregar_tarjetas_fase(
        doc,
        "FASE 1 · DESDE EL 15/06/2024",
        "Vehículos sin etiqueta ambiental (A / sin distintivo DGT).",
        "FASE 2 · DESDE EL 16/06/2025",
        "Restricción a distintivo B para no residentes del centro.",
    )

    doc.add_paragraph(
        "Una comparación simple de promedios antes y después incurre en sesgos críticos: el NO2 depende de la inversión "
        "térmica invernal, la lluvia y el régimen de vientos. Lo que el cliente necesita conocer es la reducción neta atribuible, "
        "controlando por la evolución de estaciones comparables fuera del perímetro:"
    )

    agregar_caja_formula(
        doc,
        "efecto neto ZBE = [NO2_post(dentro) − NO2_pre(dentro)] − [NO2_post(fuera) − NO2_pre(fuera)]"
    )

    # Tabla de preguntas de negocio P1-P5
    doc.add_paragraph("Para sustentar la toma de decisiones, se fijaron cinco preguntas de negocio priorizadas:")

    t_preg = doc.add_table(rows=6, cols=3)
    t_preg.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t_preg, "single", HEX_BORDER, "4")

    h_p = ["Pregunta", "Objetivo de negocio", "Metodología analítica"]
    for j, h in enumerate(h_p):
        c = t_preg.rows[0].cells[j]
        set_cell_background(c, HEX_TEAL)
        set_cell_margins(c, top=60, bottom=60, left=80, right=80)
        p = c.paragraphs[0]
        r = p.add_run(h)
        r.font.name = "Arial"
        r.font.size = Pt(9)
        r.bold = True
        r.font.color.rgb = RGB_WHITE

    preg_data = [
        ("P1 (Máxima)", "¿Ha bajado el NO2 dentro de la ZBE más que fuera tras el 15/06/2024?", "Modelo cuasiexperimental Diff-in-Diff frente a estaciones exteriores."),
        ("P2 (Alta)", "¿El efecto se concentra en el horario regulado (L-V 7:00-20:00)?", "Estratificación horaria activa frente a noche y fines de semana."),
        ("P3 (Alta)", "¿Se sostiene la reducción en calma atmosférica (< 2 m/s)?", "Control estratificado por régimen de viento en Monte Banderas."),
        ("P4 (Media)", "¿Existe correlación causal con el tráfico en los accesos?", "Contraste de aforos de San Mamés y red de circunvalación."),
        ("P5 (Media)", "¿Aportó la Fase 2 una reducción marginal respecto a la Fase 1?", "Contraste de medias entre etapas regulatorias independientes."),
    ]

    for r_idx, fila in enumerate(preg_data, 1):
        bg = HEX_LIGHT_BG if r_idx % 2 == 1 else "FFFFFF"
        for c_idx, val in enumerate(fila):
            c = t_preg.rows[r_idx].cells[c_idx]
            set_cell_background(c, bg)
            set_cell_margins(c, top=50, bottom=50, left=80, right=80)
            p = c.paragraphs[0]
            r = p.add_run(val)
            r.font.name = "Arial"
            r.font.size = Pt(9)
            if c_idx == 0:
                r.bold = True

    doc.add_paragraph().paragraph_format.space_after = Pt(4)

    # =========================================================================
    # SECCIÓN 2: FUENTES DE DATOS Y AUDITORÍA DE CALIDAD
    # =========================================================================
    agregar_banner_seccion(doc, 2, "Fuentes de datos y auditoría de calidad")

    doc.add_paragraph(
        "Se adquirieron y unificaron cuatro fuentes oficiales: (1) Calidad del Aire (Gobierno Vasco), con mediciones horarias "
        "en Mazarredo y Mª Díaz de Haro (dentro), Europa, Barakaldo, Basauri, Erandio y Castrejana (control exterior) y Arraiz (fondo regional); "
        "(2) Meteorología horaria (Open-Meteo), con temperatura, humedad, viento y precipitación; (3) Calendario ZBE con festivos oficiales; "
        "y (4) Aforos de tráfico de accesos (DFB) y tramos urbanos en tiempo real (Bilbao Open Data)."
    )

    t_cal = doc.add_table(rows=5, cols=2)
    t_cal.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t_cal, "single", HEX_BORDER, "4")

    h_c = ["Problema de calidad detectado", "Tratamiento técnico aplicado en el pipeline"]
    for j, h in enumerate(h_c):
        c = t_cal.rows[0].cells[j]
        set_cell_background(c, HEX_TEAL)
        set_cell_margins(c, top=60, bottom=60, left=80, right=80)
        p = c.paragraphs[0]
        r = p.add_run(h)
        r.font.name = "Arial"
        r.font.size = Pt(9)
        r.bold = True
        r.font.color.rgb = RGB_WHITE

    cal_data = [
        ("Coma decimal europea", "Conversión sistemática de strings con coma a números float64 estandarizados."),
        ("Hora 24:00 del Gobierno Vasco", "Conversión algorítmica sumando 1 día calendario a las 00:00 h correspondientes."),
        ("Desfase GMT vs. hora peninsular", "Transformación estricta a zona Europe/Madrid con horario de verano/invierno."),
        ("Valores negativos anómalos", "Filtrado de lecturas < 0 µg/m³ (0,04% de descalibración) e imputación por persistencia."),
    ]
    for r_idx, fila in enumerate(cal_data, 1):
        bg = HEX_LIGHT_BG if r_idx % 2 == 1 else "FFFFFF"
        for c_idx, val in enumerate(fila):
            c = t_cal.rows[r_idx].cells[c_idx]
            set_cell_background(c, bg)
            set_cell_margins(c, top=50, bottom=50, left=80, right=80)
            p = c.paragraphs[0]
            r = p.add_run(val)
            r.font.name = "Arial"
            r.font.size = Pt(9)
            if c_idx == 0:
                r.bold = True

    doc.add_paragraph().paragraph_format.space_after = Pt(4)

    # =========================================================================
    # SECCIÓN 3: INTEGRACIÓN Y PIPELINE DE DATOS
    # =========================================================================
    agregar_banner_seccion(doc, 3, "Integración de datos y arquitectura del pipeline")

    doc.add_paragraph(
        "El ciclo de procesamiento e integración de datos se estructuró en cinco etapas secuenciales:"
    )

    # Diagrama de bloques secuenciales (estilo MIA Tabla 6 / Tabla 17)
    t_diag = doc.add_table(rows=2, cols=9)
    t_diag.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t_diag, "none", "FFFFFF", "0")

    etapas_diag = [
        ("1. DATOS", "Series horarias crudas en InfluxDB y Open Data."),
        ("→", ""),
        ("2. LIMPIEZA", "Saneamiento de comas, hora 24:00 y valores nulos."),
        ("→", ""),
        ("3. INTEGRACIÓN", "JOIN espaciotemporal en (estacion, ts_local)."),
        ("→", ""),
        ("4. ANÁLISIS", "Modelo Diff-in-Diff y control meteorológico."),
        ("→", ""),
        ("5. DECISIÓN", "Cuadros de mando, umbrales y recomendaciones."),
    ]

    for j, (et_tit, et_desc) in enumerate(etapas_diag):
        c_h = t_diag.rows[0].cells[j]
        c_b = t_diag.rows[1].cells[j]

        if et_tit == "→":
            c_h.width = Pt(16)
            c_b.width = Pt(16)
            p_h = c_h.paragraphs[0]
            p_h.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r_arr = p_h.add_run("→")
            r_arr.font.name = "Arial"
            r_arr.font.size = Pt(12)
            r_arr.font.color.rgb = RGB_SLATE
        else:
            c_h.width = Pt(100)
            c_b.width = Pt(100)
            set_cell_background(c_h, HEX_TEAL)
            set_cell_background(c_b, HEX_LIGHT_BG)
            set_cell_margins(c_h, top=50, bottom=50, left=40, right=40)
            set_cell_margins(c_b, top=50, bottom=50, left=40, right=40)

            p_h = c_h.paragraphs[0]
            p_h.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r_th = p_h.add_run(et_tit)
            r_th.font.name = "Arial"
            r_th.font.size = Pt(8)
            r_th.bold = True
            r_th.font.color.rgb = RGB_WHITE

            p_b = c_b.paragraphs[0]
            r_tb = p_b.add_run(et_desc)
            r_tb.font.name = "Arial"
            r_tb.font.size = Pt(8)
            r_tb.font.color.rgb = RGB_BODY

    doc.add_paragraph().paragraph_format.space_after = Pt(4)

    doc.add_paragraph(
        "El JOIN espaciotemporal consolidó un dataset maestro de 332.776 registros horarios coincidentes, "
        "con 0 duplicados en la clave primaria (estacion, ts_local) y una tasa de nulos residual inferior al 1,2%."
    )

    # =========================================================================
    # SECCIÓN 4: RESULTADOS ANALÍTICOS Y EXPLORACIÓN CUASIEXPERIMENTAL
    # =========================================================================
    agregar_banner_seccion(doc, 4, "Resultados analíticos y modelo Diff-in-Diff")

    doc.add_paragraph(
        "La tabla sintética resume la evolución media del NO2 en cada estación y zona antes y después "
        "de la entrada en vigor de la ZBE (15/06/2024):"
    )

    t_res = doc.add_table(rows=7, cols=5)
    t_res.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t_res, "single", HEX_BORDER, "4")

    h_r = ["Zona / Estación", "Media Pre-ZBE", "Media Post-ZBE", "Var. Absoluta", "Var. Relativa"]
    for j, h in enumerate(h_r):
        c = t_res.rows[0].cells[j]
        set_cell_background(c, HEX_TEAL)
        set_cell_margins(c, top=60, bottom=60, left=80, right=80)
        p = c.paragraphs[0]
        r = p.add_run(h)
        r.font.name = "Arial"
        r.font.size = Pt(9)
        r.bold = True
        r.font.color.rgb = RGB_WHITE

    res_data = [
        ("Dentro ZBE (Mazarredo + Mª Díaz Haro)", "25,50 µg/m³", "21,90 µg/m³", "-3,59 µg/m³", "-14,08%"),
        ("Control Fuera (5 est. Gran Bilbao Urbano)", "18,25 µg/m³", "16,29 µg/m³", "-1,96 µg/m³", "-10,75%"),
        ("Fondo Regional (Monte Arraiz)", "8,73 µg/m³", "8,16 µg/m³", "-0,57 µg/m³", "-6,53%"),
        ("Estación Mazarredo (Interior tráfico)", "26,71 µg/m³", "22,86 µg/m³", "-3,85 µg/m³", "-14,41%"),
        ("Estación Mª Díaz de Haro (Interior urbano)", "24,28 µg/m³", "20,95 µg/m³", "-3,33 µg/m³", "-13,71%"),
        ("Estación Europa (Bilbao Norte control)", "21,30 µg/m³", "18,35 µg/m³", "-2,95 µg/m³", "-13,85%"),
    ]
    for r_idx, fila in enumerate(res_data, 1):
        bg = HEX_MINT_BG if r_idx == 1 else (HEX_LIGHT_BG if r_idx % 2 == 1 else "FFFFFF")
        for c_idx, val in enumerate(fila):
            c = t_res.rows[r_idx].cells[c_idx]
            set_cell_background(c, bg)
            set_cell_margins(c, top=50, bottom=50, left=80, right=80)
            p = c.paragraphs[0]
            r = p.add_run(val)
            r.font.name = "Arial"
            r.font.size = Pt(9)
            if c_idx == 0 or r_idx == 1:
                r.bold = True

    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    doc.add_paragraph(
        "El titular real del impacto es más modesto y preciso que la simple caída bruta antes/después (-14,08%): "
        "fuera de la ZBE el NO2 también descendió -1,96 µg/m³ (-10,75%) por meteorología favorable y renovación del parque móvil. "
        "Descontando esa inercia metropolitana, el impacto causal neto atribuible a la ZBE mediante Diferencias en Diferencias es de "
        "-1,63 µg/m³ (error estándar 0,12; t = -13,41; p-valor < 0,001), lo que representa una reducción neta en torno al "
        "-6,4% sobre la base previa de 25,50 µg/m³."
    )

    # =========================================================================
    # SECCIÓN 5: VISUALIZACIONES SELECCIONADAS E INTERPRETACIÓN CAUSAL
    # =========================================================================
    agregar_banner_seccion(doc, 5, "Visualizaciones clave e interpretación causal")

    # Figura 1: g1
    p_f1 = doc.add_paragraph()
    p_f1.paragraph_format.space_after = Pt(2)
    r_f1_t = p_f1.add_run("Figura 1: Evolución mensual del NO2 dentro vs. fuera de la ZBE (2022–2026)")
    r_f1_t.font.name = "Arial"
    r_f1_t.font.size = Pt(10.5)
    r_f1_t.bold = True
    r_f1_t.font.color.rgb = RGB_NAVY

    doc.add_paragraph(
        "• Presentación: Se compara la serie temporal agregada mensual de NO2 entre estaciones interiores (Abando: Mazarredo y Mª Díaz de Haro) "
        "y el conjunto de control exterior metropolitano del Gran Bilbao (5 estaciones), marcando el inicio de la Fase 1 (15/06/2024)."
    )
    img_g1 = DIR_IMG / "g1_evolucion_mensual_no2.png"
    if img_g1.exists():
        p_img = doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.paragraph_format.space_before = Pt(2)
        p_img.paragraph_format.space_after = Pt(2)
        doc.add_picture(str(img_g1), width=Inches(4.1))

    doc.add_paragraph(
        "• Interpretación causal: Durante 2022 y 2023 ambas series presentan picos invernales idénticos por estancamiento (> 34 µg/m³). "
        "A partir del verano de 2024, la serie interior se desacopla a la baja de forma sistemática: en el invierno 2024–2025 "
        "el pico máximo interior no superó los 28 µg/m³, reflejando un cambio estructural local independiente de la climatología regional."
    )

    # Figura 2: g2
    p_f2 = doc.add_paragraph()
    p_f2.paragraph_format.space_after = Pt(2)
    r_f2_t = p_f2.add_run("Figura 2: Modelo cuasiexperimental de Diferencias en Diferencias (Diff-in-Diff)")
    r_f2_t.font.name = "Arial"
    r_f2_t.font.size = Pt(10.5)
    r_f2_t.bold = True
    r_f2_t.font.color.rgb = RGB_NAVY

    doc.add_paragraph(
        "• Presentación: Gráfica del modelo econométrico Diff-in-Diff comparando la trayectoria real de tratamiento frente al contrafactual "
        "proyectado a partir de las estaciones de control del Gran Bilbao."
    )
    img_g2 = DIR_IMG / "g2_diff_in_diff_visual.png"
    if img_g2.exists():
        p_img = doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.paragraph_format.space_before = Pt(2)
        p_img.paragraph_format.space_after = Pt(2)
        doc.add_picture(str(img_g2), width=Inches(4.1))

    doc.add_paragraph(
        "• Interpretación causal: Sin la ordenanza, el interior de Bilbao habría descendido únicamente hasta 23,53 µg/m³ por inercia metropolitana. "
        "El valor observado cayó hasta 21,90 µg/m³. La brecha entre ambas curvas (-1,63 µg/m³, -6,4%) representa el efecto causal directo de las restricciones."
    )

    # Figura 3: g6
    p_f3 = doc.add_paragraph()
    p_f3.paragraph_format.space_after = Pt(2)
    r_f3_t = p_f3.add_run("Figura 3: Control meteorológico bajo calma atmosférica (viento < 2 m/s)")
    r_f3_t.font.name = "Arial"
    r_f3_t.font.size = Pt(10.5)
    r_f3_t.bold = True
    r_f3_t.font.color.rgb = RGB_NAVY

    doc.add_paragraph(
        "• Presentación: Comportamiento del NO2 interior y exterior aislado exclusivamente para horas de baja ventilación (< 2 m/s), "
        "donde no hay dispersión mecánica y el aire depende de las emisiones locales directas."
    )
    img_g6 = DIR_IMG / "g6_dispersion_no2_viento.png"
    if img_g6.exists():
        p_img = doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.paragraph_format.space_before = Pt(2)
        p_img.paragraph_format.space_after = Pt(2)
        doc.add_picture(str(img_g6), width=Inches(4.1))

    doc.add_paragraph(
        "• Interpretación causal: En calma atmosférica (< 2 m/s), el NO2 interior pasó de 28,10 µg/m³ a 25,47 µg/m³ en Fase 1 (-9,4%) "
        "y a 23,56 µg/m³ en Fase 2 (-16,2%), con un promedio post global de 24,35 µg/m³ (-13,4%). "
        "La ZBE es especialmente eficaz en los momentos de mayor peligro sanitario para la ciudadanía."
    )

    # Figura 4: dashboard_decision_v1
    p_f4 = doc.add_paragraph()
    p_f4.paragraph_format.space_after = Pt(2)
    r_f4_t = p_f4.add_run("Figura 4: Panel multivariable de decisión y correlación con aforos de tráfico")
    r_f4_t.font.name = "Arial"
    r_f4_t.font.size = Pt(10.5)
    r_f4_t.bold = True
    r_f4_t.font.color.rgb = RGB_NAVY

    doc.add_paragraph(
        "• Presentación: Panel integral de cuatro cuadrantes combinando concentraciones de NO2, evolución de intensidades vehiculares en el acceso "
        "principal de San Mamés (Diputación de Bizkaia) y variaciones consolidadas."
    )
    img_dash = DIR_IMG / "dashboard_decision_v1.png"
    if img_dash.exists():
        p_img = doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.paragraph_format.space_before = Pt(2)
        p_img.paragraph_format.space_after = Pt(2)
        doc.add_picture(str(img_dash), width=Inches(4.1))

    doc.add_paragraph(
        "• Interpretación causal: El acceso de San Mamés registró en 2024 un descenso acusado del -10,12% (50.127 a 45.052 veh/día). "
        "En 2025 se observó un rebote a 48.543 veh/día (+7,75% interanual), dejando la reducción neta 2023–2025 en un -3,16% (~ -3,2%). "
        "Esta evolución evidencia una disuasión inicial acusada seguida de adaptación de la flota. Asimismo, el test placebo con SO2 mostró un efecto "
        "Diff-in-Diff neutro de +0,33 µg/m³ (-3,94% bruto dentro), confirmando la especificidad vehicular."
    )

    # =========================================================================
    # SECCIÓN 6: CONCLUSIONES Y RECOMENDACIONES
    # =========================================================================
    agregar_banner_seccion(doc, 6, "Conclusiones estratégicas y recomendaciones")

    doc.add_paragraph(
        "1. Impacto neto probado pero moderado: La ZBE de Bilbao ha generado una reducción neta atribuible de -1,63 µg/m³ de NO2 "
        "(en torno al -6,4% sobre la base previa), sustancialmente menor que la caída bruta del -14% antes/después debido a la mejora general metropolitana.\n"
        "2. Eficacia protectora en episodios críticos: En situaciones de calma atmosférica e inversión térmica, la reducción "
        "alcanza entre el -9,4% y el -16,2%, disminuyendo las horas de superación de los umbrales de aviso de la OMS (25 µg/m³).\n"
        "3. Rendimientos decrecientes entre fases: La Fase 1 (sin etiqueta) concentró la mayor parte del beneficio. La Fase 2 (etiqueta B) "
        "ha mostrado una ganancia marginal reducida, coincidiendo con el rebote y estabilización del tráfico de acceso en 2025 (-3,2% neto vs 2023)."
    )

    p_lim = doc.add_paragraph()
    p_lim.paragraph_format.space_before = Pt(3)
    r_lim_t = p_lim.add_run("Cinco limitaciones metodológicas asumidas con rigor institucional:")
    r_lim_t.font.name = "Arial"
    r_lim_t.font.size = Pt(10.5)
    r_lim_t.bold = True
    r_lim_t.font.color.rgb = RGB_SLATE

    doc.add_paragraph(
        "• Representatividad espacial: Solo dos estaciones fijas oficiales en el interior de la ZBE (Mazarredo y Mª Díaz de Haro).\n"
        "• Magnitud absoluta moderada: El impacto neto (-1,63 µg/m³) es modesto frente a la variabilidad meteorológica interanual.\n"
        "• Inercia del periodo base: Los años 2022 y 2023 reflejaban aún pautas de movilidad en recuperación tras el COVID-19.\n"
        "• Factores concurrentes: Bonificaciones al transporte público, expansión ciclable y renovación vegetativa natural del parque móvil.\n"
        "• Concentración vs. emisiones: Las estaciones registran concentración en aire (µg/m³), no emisiones directas en tubo de escape."
    )

    p_rec = doc.add_paragraph()
    p_rec.paragraph_format.space_before = Pt(4)
    r_rec_t = p_rec.add_run("Recomendaciones técnicas al Ayuntamiento:")
    r_rec_t.font.name = "Arial"
    r_rec_t.font.size = Pt(10.5)
    r_rec_t.bold = True
    r_rec_t.font.color.rgb = RGB_TEAL

    doc.add_paragraph(
        "• Mantener la regulación actual y priorizar la electrificación del reparto urbano: No se aconseja un endurecimiento drástico adicional a turismos (coste socioeconómico alto con ganancia marginal decreciente); priorizar furgonetas y distribución de última milla.\n"
        "• Despliegue de sensores perimetrales: Monitorizar arterias límite (Autonomía, Sagrado Corazón, Deusto) para descartar efectos de desplazamiento de tráfico (spillover).\n"
        "• Mantenimiento del esquema horario: Preservar la vigencia de lunes a viernes de 7:00 a 20:00 h, descartando restricciones nocturnas innecesarias."
    )

    # =========================================================================
    # SECCIÓN 7: HERRAMIENTAS Y JUSTIFICACIÓN
    # =========================================================================
    agregar_banner_seccion(doc, 7, "Herramientas tecnológicas y justificación")

    t_her = doc.add_table(rows=6, cols=3)
    t_her.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t_her, "single", HEX_BORDER, "4")

    h_h = ["Tecnología", "Función en el proyecto", "Justificación técnica de selección"]
    for j, h in enumerate(h_h):
        c = t_her.rows[0].cells[j]
        set_cell_background(c, HEX_TEAL)
        set_cell_margins(c, top=50, bottom=50, left=80, right=80)
        p = c.paragraphs[0]
        r = p.add_run(h)
        r.font.name = "Arial"
        r.font.size = Pt(9)
        r.bold = True
        r.font.color.rgb = RGB_WHITE

    her_data = [
        ("Python + Pandas / Statsmodels", "ETL, limpieza y regresión cuasiexperimental.", "Procesamiento vectorizado en memoria y cálculo de errores estándar robustos a heterocedasticidad."),
        ("InfluxDB 2.9 (TSDB)", "Almacén de series temporales de alta frecuencia.", "Motor columnar TSM optimizado para consultas de tiempo y retención automatizada por bucket."),
        ("Node-RED", "Orquestador de flujos en tiempo real.", "Gestión tolerante a fallos para consultar APIs externas y conversión nativa a Line Protocol."),
        ("Grafana 11.2", "Cuadros de mando y control de acceso (RBAC).", "Soporte de consultas Flux, reglas de alerta automáticas y segregación de perfiles por equipos."),
        ("InfluxDB MCP Server", "Interfaz Model Context Protocol en solo lectura.", "Permite a agentes de lenguaje interrogar los buckets de InfluxDB mediante herramientas seguras."),
    ]
    for r_idx, fila in enumerate(her_data, 1):
        bg = HEX_LIGHT_BG if r_idx % 2 == 1 else "FFFFFF"
        for c_idx, val in enumerate(fila):
            c = t_her.rows[r_idx].cells[c_idx]
            set_cell_background(c, bg)
            set_cell_margins(c, top=45, bottom=45, left=80, right=80)
            p = c.paragraphs[0]
            r = p.add_run(val)
            r.font.name = "Arial"
            r.font.size = Pt(8.5)
            if c_idx == 0:
                r.bold = True

    doc.add_paragraph().paragraph_format.space_after = Pt(4)

    # =========================================================================
    # SECCIÓN 8: ORGANIZACIÓN Y RESPONSABILIDADES
    # =========================================================================
    agregar_banner_seccion(doc, 8, "Organización del trabajo y responsabilidades (Matriz RACI)")

    t_raci = doc.add_table(rows=4, cols=3)
    t_raci.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t_raci, "single", HEX_BORDER, "4")

    h_r = ["Miembro del equipo", "Rol en el proyecto", "Tareas principales asumidas"]
    for j, h in enumerate(h_r):
        c = t_raci.rows[0].cells[j]
        set_cell_background(c, HEX_TEAL)
        set_cell_margins(c, top=50, bottom=50, left=80, right=80)
        p = c.paragraphs[0]
        r = p.add_run(h)
        r.font.name = "Arial"
        r.font.size = Pt(9)
        r.bold = True
        r.font.color.rgb = RGB_WHITE

    raci_data = [
        ("Alfred Gabriel", "Ingeniería de datos y modelado SBD", "Pipeline de descarga (descargar_y_limpiar.py), estimación Diff-in-Diff y cuaderno Jupyter zbe_bilbao.ipynb."),
        ("Íñigo", "Calidad de datos y comunicación ejecutiva", "Control de calidad, diseño de figuras (g1 a g10), análisis de aforos y redacción del informe de 4 páginas."),
        ("Kerman", "Infraestructura BDA y DevOps", "Despliegue Docker Compose, buckets y tokens en InfluxDB, flujos Node-RED, servicio MCP y paneles Grafana."),
    ]
    for r_idx, fila in enumerate(raci_data, 1):
        bg = HEX_LIGHT_BG if r_idx % 2 == 1 else "FFFFFF"
        for c_idx, val in enumerate(fila):
            c = t_raci.rows[r_idx].cells[c_idx]
            set_cell_background(c, bg)
            set_cell_margins(c, top=45, bottom=45, left=80, right=80)
            p = c.paragraphs[0]
            r = p.add_run(val)
            r.font.name = "Arial"
            r.font.size = Pt(8.5)
            if c_idx == 0:
                r.bold = True

    doc.add_paragraph().paragraph_format.space_after = Pt(4)

    # Checklist de verificación (Tabla 3x3 idéntica a MIA Tabla 23)
    p_chk = doc.add_paragraph()
    p_chk.paragraph_format.space_before = Pt(4)
    p_chk.paragraph_format.space_after = Pt(2)
    r_chk_t = p_chk.add_run("Checklist de verificación de la rúbrica oficial (SBD / Reto 0)")
    r_chk_t.font.name = "Arial"
    r_chk_t.font.size = Pt(10.5)
    r_chk_t.bold = True
    r_chk_t.font.color.rgb = RGB_NAVY

    t_chk = doc.add_table(rows=3, cols=3)
    t_chk.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t_chk, "none", "FFFFFF", "0")

    chk_items = [
        [("☑ Contexto y 5 preguntas", "AP. 1"), ("☑ Fuentes y auditoría calidad", "AP. 2"), ("☑ Integración y pipeline", "AP. 3")],
        [("☑ Resultados analíticos", "AP. 4"), ("☑ Figuras con 3 partes", "AP. 5"), ("☑ Conclusiones y recomendaciones", "AP. 6")],
        [("☑ Justificación herramientas", "AP. 7"), ("☑ Matriz RACI y Scrum", "AP. 8"), ("☑ Servicio MCP integrado", "AP. 7")],
    ]

    for r_idx, fila in enumerate(chk_items):
        for c_idx, (t_txt, ap_txt) in enumerate(fila):
            c = t_chk.rows[r_idx].cells[c_idx]
            c.width = Pt(161.7)
            set_cell_margins(c, top=30, bottom=30, left=40, right=40)
            p = c.paragraphs[0]
            r1 = p.add_run(t_txt + "\t")
            r1.font.name = "Arial"
            r1.font.size = Pt(8.5)
            r1.bold = True
            r1.font.color.rgb = RGB_BODY
            r2 = p.add_run(ap_txt)
            r2.font.name = "Arial"
            r2.font.size = Pt(8)
            r2.font.color.rgb = RGB_TEAL

    # Conclusión final
    p_concl = doc.add_paragraph()
    p_concl.paragraph_format.space_before = Pt(6)
    p_concl.paragraph_format.space_after = Pt(2)
    r_cc = p_concl.add_run("Conclusión")
    r_cc.font.name = "Arial"
    r_cc.font.size = Pt(11)
    r_cc.bold = True
    r_cc.font.color.rgb = RGB_NAVY

    doc.add_paragraph(
        "El análisis econométrico multivariable demuestra con rigor estadístico que la ZBE de Bilbao ha alcanzado un impacto neto "
        "atribuible de -1,63 µg/m³ en la concentración interior de NO2 (-6,4% respecto a la base pre-ZBE). El sistema integrado (ETL en Pandas, series en InfluxDB, "
        "monitorización en Grafana e interfaz MCP de solo lectura) garantiza la reproducibilidad completa del estudio, facilitando "
        "que el Ayuntamiento de Bilbao base sus decisiones de movilidad en evidencias empíricas continuas, transparentes y moderadas."
    )

    # Referencias bibliográficas
    p_ref = doc.add_paragraph()
    p_ref.paragraph_format.space_before = Pt(4)
    p_ref.paragraph_format.space_after = Pt(2)
    r_rf = p_ref.add_run("Referencias")
    r_rf.font.name = "Arial"
    r_rf.font.size = Pt(11)
    r_rf.bold = True
    r_rf.font.color.rgb = RGB_NAVY

    p_r1 = doc.add_paragraph()
    r_r1 = p_r1.add_run("1. Grange, S. K., & Carslaw, D. C. (2019). Using meteorological normalisation to detect interventions in air quality time series. Science of the Total Environment, 653, 578–588.")
    r_r1.font.name = "Arial"
    r_r1.font.size = Pt(8.5)
    r_r1.font.color.rgb = RGB_SLATE

    p_r2 = doc.add_paragraph()
    r_r2 = p_r2.add_run("2. Angrist, J. D., & Pischke, J. S. (2009). Mostly Harmless Econometrics: An Empiricist's Companion. Princeton University Press.")
    r_r2.font.name = "Arial"
    r_r2.font.size = Pt(8.5)
    r_r2.font.color.rgb = RGB_SLATE

    # Guardar documento Word
    doc.save(str(RUTA_DOCX))
    print(f"[OK] Documento generado exitosamente en: {RUTA_DOCX}")


if __name__ == "__main__":
    construir_documento()
