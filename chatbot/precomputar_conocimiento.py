#!/usr/bin/env python3
"""
haizelab/chatbot/precomputar_conocimiento.py
============================================
Genera la base de conocimiento estructurada (knowledge_base.json)
para el Asistente Local de HaizeLab (Reto 0).
Extrae datos reales, métricas estadísticas, infraestructura y conclusiones.
"""

from pathlib import Path
import json
import pandas as pd

DIR_BASE = Path(__file__).resolve().parent.parent
DIR_CHATBOT = Path(__file__).resolve().parent
DIR_UNIFICADOS = DIR_BASE / "datos" / "procesados" / "unificados"


def generar_base_conocimiento():
    print("[1/3] Extrayendo estadísticas numéricas reales de datasets...")

    # Cargar sintesis ejecutiva si existe
    f_sintesis = DIR_UNIFICADOS / "sintesis_ejecutiva_zbe.csv"
    stats_datos = {}
    if f_sintesis.exists():
        df_s = pd.read_csv(f_sintesis)
        stats_datos = df_s.to_dict(orient="records")

    estadisticas_clave = {
        "no2_dentro_pre": 25.50,
        "no2_dentro_post": 21.90,
        "caida_bruta_dentro_pct": -14.1,
        "caida_bruta_dentro_ug": -3.60,
        "no2_control_pre": 18.25,
        "no2_control_post": 16.29,
        "caida_control_pct": -10.8,
        "caida_control_ug": -1.96,
        "impacto_neto_diff_in_diff_ug": -1.63,
        "impacto_neto_pct": -6.4,
        "margen_error_ic95": 1.2,
        "no2_calma_pre_ug": 28.10,
        "no2_calma_post_ug": 24.35,
        "caida_calma_pct": -13.4,
        "so2_placebo_neto_ug": 0.33,
        "benceno_dentro_var_pct": 13.0,
        "trafico_san_mames_2023": 50127,
        "trafico_san_mames_2024": 45052,
        "trafico_san_mames_2025": 48543,
        "caida_trafico_san_mames_2024_pct": -10.12,
        "variacion_trafico_san_mames_2025_vs_2023_pct": -3.16,
        "rebote_trafico_san_mames_2025_vs_2024_pct": 7.75,
        "trafico_total_accesos_var_pct": 1.83,
        "horas_analizadas": 41700,
        "periodo_analisis": "Enero 2022 a Octubre 2026",
        "camaras_zbe": 27,
        "superficie_zbe_km2": 2.1,
        "horario_zbe": "Lunes a viernes de 07:00 a 20:00",
        "fase1_fecha": "15 de junio de 2024 (restricción a vehículos sin distintivo ambiental)",
        "fase2_fecha": "16 de junio de 2025 (restricción a etiqueta B de no residentes)"
    }

    print("[2/3] Compilando tópicos de conocimiento del Reto 0...")

    documentos = [
        {
            "id": "resumen_proyecto",
            "titulo": "Resumen Ejecutivo de HaizeLab y Pregunta Central",
            "categoria": "general",
            "palabras_clave": ["haizelab", "reto 0", "objetivo", "pregunta", "que es", "proyecto", "resumen", "bilbao"],
            "contenido": (
                "HaizeLab es el proyecto del Reto 0 ('HERE WE GO') del curso de Especialización en IA y Big Data del "
                "Centro de Formación Somorrostro. El objetivo principal es responder científicamente a la pregunta del Ayuntamiento "
                "de Bilbao: ¿Ha reducido la Zona de Bajas Emisiones (ZBE) en Abando los niveles de dióxido de nitrógeno (NO₂) en el centro "
                "de forma causal y directamente atribuible a la regulación? El equipo combina monitorización en tiempo real (Node-RED, "
                "InfluxDB, Grafana) y análisis econométrico multivariable (Pandas, Diff-in-Diff, HistGradientBoosting)."
            )
        },
        {
            "id": "resultado_efecto_neto",
            "titulo": "Resultado y Efecto Causal Neto de la ZBE",
            "categoria": "resultados",
            "palabras_clave": ["resultado", "ha funcionado", "efecto neto", "impacto", "reduccion", "caida", "porcentaje", "ug/m3", "no2"],
            "contenido": (
                "El veredicto institucional es: 'Efecto reductor confirmado pero moderado'. "
                "En bruto, el NO₂ en el interior de la ZBE cayó de 25,50 a 21,90 µg/m³ (-14,1%). Sin embargo, en las estaciones de control "
                "exterior del Gran Bilbao (sin restricción) el NO₂ también cayó un -10,8% (de 18,25 a 16,29 µg/m³). "
                "Aplicando el estimador causal de Diferencias en Diferencias (Diff-in-Diff), el impacto neto atribuible exclusivamente a la ZBE "
                "es de -1,63 µg/m³ de NO₂ (aproximadamente un -6,4% respecto a la línea base), con un intervalo de confianza del 95% de ±1,2 µg/m³. "
                "Atribuir todo el -14,1% a la ZBE sería un error metodológico, ya que gran parte de la mejora se debe a la meteorología favorable "
                "y a la renovación paulatina del parque automovilístico."
            )
        },
        {
            "id": "estaciones_grupos",
            "titulo": "Red de Estaciones de Monitorización y Grupos Cuasiexperimentales",
            "categoria": "metodologia",
            "palabras_clave": ["estaciones", "sensores", "mazarredo", "diaz de haro", "europa", "arraiz", "barakaldo", "basauri", "erandio", "castrejana", "grupos"],
            "contenido": (
                "Se analizaron 8 estaciones de la Red de Calidad del Aire de Euskadi divididas en 3 grupos funcionales: "
                "1) Interior ZBE (Tratadas, 2 estaciones): Mazarredo y María Díaz de Haro, ubicadas en el distrito de Abando donde rige la restricción. "
                "2) Control Metropolitano Exterior (5 estaciones): Europa (Bilbao exterior), Barakaldo, Basauri, Erandio y Castrejana (comparten clima y flota pero sin restricción). "
                "3) Fondo Rural / Referencia Limpia (1 estación): Monte Arraiz, alejada del tráfico rodado para medir el nivel de fondo regional."
            )
        },
        {
            "id": "control_meteorologico",
            "titulo": "Control Meteorológico y Régimen de Viento",
            "categoria": "meteorologia",
            "palabras_clave": ["meteo", "meteorologia", "viento", "calma", "lluvia", "temperatura", "humedad", "desestacionalizacion"],
            "contenido": (
                "Para asegurar que la bajada no se debió a días con más viento o lluvia, se utilizó meteorología horaria de Open-Meteo y se realizó "
                "una estratificación por régimen de viento. En situaciones críticas de calma atmosférica (< 2 m/s), donde no hay dispersión y el peligro "
                "para la salud pública es mayor, el NO₂ interior cayó un -13,4% (de 28,10 µg/m³ en periodo previo a 24,35 µg/m³ post-ZBE). "
                "Esto demuestra empíricamente que la ZBE ofrece protección real precisamente en los momentos donde la atmósfera está estancada."
            )
        },
        {
            "id": "aforos_trafico",
            "titulo": "Aforos y Dinámica del Tráfico Rodado",
            "categoria": "trafico",
            "palabras_clave": ["trafico", "coches", "san mames", "aforos", "vehiculos", "imd", "camaras", "accesos"],
            "contenido": (
                "Se analizaron 11 accesos a Bilbao y 81 tramos viarios (Bilbao Open Data y Diputación Foral de Bizkaia). "
                "En el acceso directo de San Mamés a la ZBE, el tráfico cayó un -10,1% en 2024 (Fase 1, pasando de 50.127 a 45.052 veh/día). "
                "En 2025 (Fase 2) se produjo un rebote parcial del +7,7% interanual (48.543 veh/día), quedando la reducción neta en un -3,2% respecto a 2023. "
                "Esto evidencia una fuerte disuasión inicial en los primeros meses con una adaptación paulatina posterior de los conductores."
            )
        },
        {
            "id": "placebo_y_robustez",
            "titulo": "Pruebas de Robustez, Placebo y Límites del Estudio",
            "categoria": "metodologia",
            "palabras_clave": ["placebo", "so2", "benceno", "limitaciones", "errores", "robustez", "validez", "sesgos"],
            "contenido": (
                "El estudio aplicó 4 pruebas de validación rigurosa: "
                "1) Horario: el efecto neto de reducción es mayor durante el horario de la norma (07:00-20:00, -2,93 µg/m³) que en horario nocturno (-0,86 µg/m³). "
                "2) Control Meteorológico: incluyendo viento, lluvia, temperatura y humedad, el efecto neto se mantiene en -1,74 µg/m³. "
                "3) Control Placebo con SO₂: el dióxido de azufre (contaminante no generado por coches ligeros) dio una variación neta neutra (+0,33 µg/m³), demostrando que el método no inventa bajadas falsas. "
                "4) Inconsistencia detectada: el Benceno subió un +13% dentro de la zona, lo cual es un hallazgo anómalo reportado con honestidad. "
                "Limitación principal: solo hay 2 estaciones dentro de la ZBE y se requiere medir en el perímetro antes de ampliar la zona."
            )
        },
        {
            "id": "infraestructura_tecnologica",
            "titulo": "Arquitectura Tecnológica de Datos en Tiempo Real",
            "categoria": "infraestructura",
            "palabras_clave": ["tecnologia", "arquitectura", "docker", "influxdb", "nodered", "grafana", "mcp", "streaming", "buckets", "tokens"],
            "contenido": (
                "La infraestructura opera mediante un stack reproducible en Docker Compose con 5 servicios integrados: "
                "- InfluxDB 2.9: Base de datos de series temporales con 4 buckets segregados por política de retención: "
                "  'aire' (infinito, histórico), 'meteo' (infinito), 'trafico' (30 días, 81 tramos cada 5m), 'aire_demo' (7 días, streaming acelerado a 5s). "
                "- Seguridad InfluxDB: 4 tokens de mínimo privilegio (nodered-write, batch-write, read-all y mcp-read-only). Ningún token subido a Git. "
                "- Node-RED 5.0: Orquestador de streaming con 3 flujos automatizados (meteo cada 15 min, tráfico cada 5 min y reproducción acelerada de NO₂ cada 5s). Protegido con adminAuth (bcryptjs). "
                "- Grafana 11.2: Cuadros de mando analíticos y ejecutivos con RBAC por roles (Viewer para directores/analistas, Editor/Admin para IT), alertas y mapa interactivo Geomap de Bilbao con el polígono ZBE. "
                "- Servidor MCP (Model Context Protocol): Servicio en puerto :5001 para consulta de series temporales por agentes de IA en solo lectura. "
                "- Proxy Gateway: Influx-Proxy en puerto :8085 con soporte para Third-Party Cookies (SameSite=None, Secure, Partitioned) para permitir integración en iframes sin bloqueo."
            )
        },
        {
            "id": "modelos_ia_mia",
            "titulo": "Modelos de Inteligencia Artificial (Módulo MIA)",
            "categoria": "ia",
            "palabras_clave": ["ia", "inteligencia artificial", "modelo", "machine learning", "gradient boosting", "lightgbm", "histgradientboosting", "difusa", "reglas"],
            "contenido": (
                "En el módulo de Modelos de Inteligencia Artificial (MIA) se contrastaron dos familias: "
                "A) Diferencias en Diferencias (Diff-in-Diff): Modelo causal cuasiexperimental de referencia. "
                "B) Gradient Boosting (HistGradientBoostingRegressor): Modelo supervisado no lineal elegido por su capacidad "
                "para capturar relaciones complejas entre velocidad/ángulo de viento, temperatura y estacionalidad sin asumir linealidad. "
                "El modelo aprende la función contrafactual en el periodo pre-ZBE (2022-2024) y predice qué niveles de NO₂ habrían ocurrido sin regulación. "
                "También se caracterizaron sistemas de lógica difusa para ventilación atmosférica, sistemas de reglas para alertas normativas (Directiva 2008/50/CE) y visión artificial (ANPR/OCR) para lectura de matrículas y distintivos ambientales."
            )
        },
        {
            "id": "equipo_scrum_roles",
            "titulo": "Equipo de Desarrollo, Metodología Scrum y Entregables",
            "categoria": "equipo",
            "palabras_clave": ["equipo", "scrum", "autores", "alfred", "inigo", "kerman", "roles", "sprints", "commits", "entregables"],
            "contenido": (
                "El equipo Haizen Lab está compuesto por tres alumnos de Especialización en IA y Big Data del Centro de Formación Somorrostro: "
                "- Alfred Gabriel (Product Owner / PIA): Docker Compose, servidor MCP, orquestación de red y gestión de ramas Git. "
                "- Iñigo Bilbao (Scrum Master / MIA): Diseño econométrico Diff-in-Diff, modelo de Machine Learning, tests de placebo y memoria MIA. "
                "- Kerman Irusta (Lead Data Engineer / BDA): Flujos de Node-RED, InfluxDB (buckets y tokens) y cuadros de mando en Grafana con RBAC. "
                "Metodología ágil: 3 sprints Scrum, Scrum Master rotatorio, daily standups de 10 min, 11 ramas (9 feature, 2 hotfix) integradas en develop mediante Pull Requests, y releases estables en main."
            )
        },
        {
            "id": "recomendaciones_ayuntamiento",
            "titulo": "Recomendaciones Oficiales al Ayuntamiento de Bilbao",
            "categoria": "conclusiones",
            "palabras_clave": ["recomendaciones", "que hacer", "ayuntamiento", "consejo", "futuro", "ampliar", "sensores"],
            "contenido": (
                "HaizeLab plantea 3 recomendaciones estratégicas al Ayuntamiento de Bilbao: "
                "1. Mantener la ZBE y su horario: la señal reductora existe y se concentra en las horas laborales de mayor tráfico. "
                "2. Instalar sensores en el perímetro antes de ampliar la zona: sin monitorización en las avenidas limítrofes (Autonomía, Sabino Arana, San Mamés) no es posible descartar el efecto derrame o desplazamiento del tráfico. "
                "3. Repetir la evaluación anualmente: la infraestructura de HaizeLab automatiza la ingesta y el pipeline de análisis, permitiendo auditar la evolución de la Fase 2 (etiqueta B) con coste marginal cero."
            )
        }
    ]

    base_completa = {
        "version": "1.0.0",
        "proyecto": "HaizeLab · Reto 0 (Centro de Formación Somorrostro)",
        "estadisticas": estadisticas_clave,
        "datos_sintesis": stats_datos,
        "documentos": documentos
    }

    f_salida = DIR_CHATBOT / "knowledge_base.json"
    with open(f_salida, "w", encoding="utf-8") as f:
        json.dump(base_completa, f, indent=2, ensure_ascii=False)

    print(f"[3/3] [OK] Base de conocimiento generada en {f_salida} ({len(documentos)} tópicos estructurados)")


if __name__ == "__main__":
    generar_base_conocimiento()
