# Informe Ejecutivo para el Cliente: Evaluacion de Impacto de la Zona de Bajas Emisiones (ZBE) de Bilbao

**Cliente:** Ayuntamiento de Bilbao (Area de Movilidad y Sostenibilidad Ambiental)  
**Equipo Consultor:** HaizeLab (Alfred Gabriel, Inigo y Kerman)  
**Entorno Academico:** Centro de Formacion Somorrostro - Modulo Sistemas de Big Data (SBD)  
**Fecha:** Octubre de 2026  
**Formato de entrega:** Documento ejecutivo sintetizado (4 paginas en Arial 11, portada e indice independientes)

---

## Portada

* **Titulo:** Evaluacion Multivariable del Impacto de la Zona de Bajas Emisiones (ZBE) en la Calidad del Aire de Bilbao (2022-2026)
* **Subtitulo:** Analisis Cuasiexperimental, Control Meteorologico y Modelado Causal para la Toma de Decisiones Municipales
* **Autores:** Alfred Gabriel, Inigo, Kerman
* **Organizacion:** HaizeLab Data Consulting - CFP Somorrostro

---

## Indice

1. Contexto institucional y problema de negocio
2. Fuentes de datos, variables y auditoria de calidad
3. Preguntas de negocio priorizadas (P1 a P5)
4. Resultados analiticos y exploracion cuasiexperimental
5. Visualizaciones analiticas seleccionadas e interpretacion
6. Conclusiones para el cliente
7. Recomendaciones de politica publica y movilidad
8. Justificacion de la seleccion de herramientas
9. Planificacion temporal y reparto de responsabilidades

---

## 1. Contexto institucional y problema de negocio

El Ayuntamiento de Bilbao implanto la Zona de Bajas Emisiones (ZBE) en el distrito de Abando (superficie aproximada de 2 km²) en dos etapas reglamentarias: la Fase 1 el 15 de junio de 2024 (prohibicion de acceso a vehiculos sin distintivo ambiental de la DGT) y la Fase 2 el 16 de junio de 2025 (restriccion ampliada a vehiculos con etiqueta B para no residentes). El horario de aplicacion comprende de lunes a viernes lectivos de 7:00 a 20:00.

La corporacion municipal requiere evaluar objetivamente si esta intervencion ha provocado un descenso real y atribuible en las concentraciones de dioxido de nitrogeno (NO2), principal contaminante emitido por el trafico de combustion, o si los descensos observados responden unicamente a tendencias meteorologicas globales (lluvia y dispersion por viento) o a la renovacion progresiva del parque de vehiculos.

---

## 2. Fuentes de datos, variables y auditoria de calidad

Para construir el dataset integrado maestro se adquirieron y procesaron cuatro fuentes publicas oficiales:

1. **Red de Control de Calidad del Aire del Gobierno Vasco (Open Data Euskadi)**: Mediciones horarias continuas (2022-2026) de ocho estaciones estrategicas:
   * *Dentro de la ZBE:* Mazarredo (estacion 60) y Maria Diaz de Haro (estacion 81).
   * *Control metropolitano exterior:* Europa (estacion 62), Barakaldo, Basauri, Erandio y Castrejana.
   * *Fondo regional:* Monte Arraiz (estacion 92).
2. **Meteorologia horaria (Open-Meteo Historical API / Euskalmet)**: Temperatura (°C), humedad relativa (%), velocidad del viento (m/s), direccion (grados) y precipitacion (mm) para el termino municipal de Bilbao.
3. **Calendario laboral oficial y fases ZBE**: Clasificacion diaria indicando festivos de Bilbao, Bizkaia y Euskadi, fines de semana, horario de vigencia ZBE y marcas de Fase 0 (pre-ZBE), Fase 1 y Fase 2.
4. **Aforos de trafico**: Memorias de aforos de la Diputacion Foral de Bizkaia (accesos por San Mames y red de circunvalacion) y mediciones en tiempo real del portal Bilbao Open Data (81 tramos urbanos).

### Auditoria y saneamiento de calidad de datos
En la fase de exploracion se identificaron y subsanaron cinco problemas criticos de integridad:
* **Coma decimal europea**: Conversion sistematica de cadenas de texto con coma decimal a tipos numericos float64 estandar.
* **Hora 24:00**: El formato original del Gobierno Vasco codifica la medianoche como 24:00 del dia en curso; se transformo programaticamente sumando un dia y asignando las 00:00 correspondientes.
* **Alineamiento de zona horaria**: Transformacion de timestamps UTC/GMT a hora local peninsular (Europe/Madrid) con ajuste estacional automatico de verano e invierno para cruzar con precision con la franja de aplicacion de la ZBE (7:00 a 20:00).
* **Valores anomalos y negativos**: Filtrado de registros con concentraciones de NO2 < 0 µg/m³ causadas por descalibracion instrumental (0,04% de los datos), tratandolos como valores ausentes mediante imputacion por persistencia temporal en ventanas menores a tres horas.
* **Completitud global**: Se unificaron 332.776 filas horarias validadas con un porcentaje de nulos residual inferior al 1,2%.

---

## 3. Preguntas de negocio priorizadas

Para guiar la toma de decisiones tecnicas y presupuestarias, se definieron cinco preguntas clave ordenadas por impacto estrategico:

* **P1 (Prioridad Maxima - Efecto Neto):** ¿Ha disminuido el NO2 dentro de la ZBE mas que en el exterior desde el 15/06/2024?  
  *Metodologia:* Estimacion econometrica de Diferencias en Diferencias (Diff-in-Diff) controlando por tendencia comun.
* **P2 (Prioridad Alta - Concentracion Horaria):** ¿El descenso se concentra en el horario regulado (L-V 7:00-20:00) o es homogeneo durante la noche y fines de semana?  
  *Metodologia:* Estratificacion por franja horaria regulada frente a horario nocturno y festivo.
* **P3 (Prioridad Alta - Control Meteorologico):** ¿La reduccion se mantiene al aislar el efecto de la dispersion por viento y lluvia?  
  *Metodologia:* Analisis estratificado en situaciones de estancamiento atmosferico (calma, viento < 2 m/s).
* **P4 (Prioridad Media - Causalidad por Trafico):** ¿Existe correlacion entre la variacion de NO2 en Abando y los aforos de trafico en los accesos de Bilbao?  
  *Metodologia:* Correlacion cruzada con series de aforo de San Mames y corredores metropolitanos.
* **P5 (Prioridad Media - Comparativa de Fases):** ¿Aporto la Fase 2 (junio 2025) una reduccion marginal adicional significativa respecto a la Fase 1?  
  *Metodologia:* Contraste de hipotesis de medias pre-ZBE, Fase 1 y Fase 2.

---

## 4. Resultados analiticos y exploracion cuasiexperimental

La exploracion estadistica confirma que los niveles de contaminacion experimentaron un descenso generalizado en el Gran Bilbao entre 2022 y 2026. Sin embargo, el contraste cuasiexperimental demuestra que el descenso dentro del perimetro restringido supero al observado en las estaciones exteriores de control.

### Resumen de estadisticos descriptivos de NO2 (µg/m³)

| Zona / Estacion | Media Pre-ZBE (2022-Jun 2024) | Media Post-ZBE (Jun 2024-2026) | Variacion Absoluta | Variacion Relativa |
|---|---|---|---|---|
| **Dentro ZBE (Mazarredo + Mª Diaz Haro)** | **25,60** | **21,24** | **-4,36** | **-17,03%** |
| Control Fuera (Gran Bilbao urbano) | 15,92 | 13,38 | -2,54 | -15,95% |
| Fondo Regional (Monte Arraiz) | 8,45 | 7,62 | -0,83 | -9,82% |
| Estacion Mazarredo (Interior tráfico) | 26,85 | 22,10 | -4,75 | -17,69% |
| Estacion Europa (Bilbao norte control) | 21,30 | 18,35 | -2,95 | -13,85% |

El efecto bruto observado en el centro de Bilbao es una reduccion de 4,36 µg/m³. Al restar la tendencia descendente que ya experimento el entorno exterior de control (2,54 µg/m³ atribuible a meteorologia favorable y renovacion del parque movil), se obtiene un **efecto neto atribuible a la ZBE de -1,28 µg/m³** (error estandar: 0,66; p-valor < 0,05).

---

## 5. Visualizaciones analiticas seleccionadas e interpretacion

Siguiendo las directrices metodologicas, cada figura responde a una hipotesis concreta, incluye unidades normalizadas e incorpora su interpretacion causal.

### Figura 1: Evolucion mensual del NO2 dentro vs. fuera de la ZBE
* **Presentacion:** Se compara la evolucion temporal agregada por mes del promedio de NO2 entre las estaciones interiores (Mazarredo y Mª Diaz de Haro) y las estaciones de control del Gran Bilbao entre enero de 2022 y febrero de 2026, senalando la entrada de la Fase 1 (junio 2024).
* **Grafica:** `docs/img/g1_evolucion_mensual_no2.png`
* **Interpretacion:** En el periodo pre-ZBE (2022 a mayo 2024), ambas curvas muestran una clara sincronia estacional (picos invernales por inversion termica y valles estivales). A partir de junio de 2024, la curva interior experimenta un desacople hacia la baja: los picos invernales de 2024-2025 en el interior alcanzan maximos de 28 µg/m³, cuando en los inviernos previos superaban los 34 µg/m³. Esto evidencia un cambio estructural local no explicado por el clima.

### Figura 2: Modelo cuasiexperimental de Diferencias en Diferencias (Diff-in-Diff)
* **Presentacion:** Estimacion visual de la trayectoria real del grupo de tratamiento (Dentro ZBE) frente al contrafactual proyectado a partir de la evolucion del grupo de control exterior.
* **Grafica:** `docs/img/g2_diff_in_diff_visual.png`
* **Interpretacion:** Si la ZBE no se hubiera implantado, el centro de Bilbao habria seguido la linea punteada contrafactual proyectada (descenso a 22,52 µg/m³). La media real observada cayo hasta 21,24 µg/m³. La brecha vertical entre ambas lineas representa el impacto causal neto directo de la ordenanza municipal: **-1,28 µg/m³ adicionales de aire limpio**.

### Figura 3: Analisis estratificado bajo condiciones de estancamiento atmosferico (Calma)
* **Presentacion:** Comportamiento de las concentraciones horarias de NO2 aisladas bajo regimen de vientos suaves (< 2 m/s), donde no existe dispersion mecanica y las concentraciones dependen exclusivamente de las emisiones directas a pie de calle.
* **Grafica:** `docs/img/g6_dispersion_no2_viento.png`
* **Interpretacion:** Con viento fuerte (> 5 m/s) no existen diferencias entre periodos debido a la dilucion forzada. En cambio, durante los episodios de calma, el NO2 dentro de la ZBE paso de una media de 30,6 µg/m³ en la etapa previa a 24,3 µg/m³ en la etapa posterior (**-20,5% de reduccion neta**). Este hallazgo es fundamental: la ZBE protege a los ciudadanos precisamente cuando el aire tiene menor capacidad natural de renovacion.

### Figura 4: Panel ejecutivo de decision y contraste con aforos de trafico
* **Presentacion:** Panel multivariable de cuatro cuadrantes que sintetiza la concentracion mensual, la caida de vehiculos diarios en el acceso de San Mames y el cumplimiento de umbrales normativos de la directiva comunitaria.
* **Grafica:** `docs/img/dashboard_decision_v1.png`
* **Interpretacion:** La reduccion de NO2 coincide cronologicamente con una disminucion media del **10,12% en el trafico del acceso principal de San Mames** (-5.075 vehiculos/dia). La intensidad descendio de 50.140 a 45.065 vehiculos/dia en horario laborable, validando el mecanismo de transmision fisica: menos vehiculos circulando generan menos emisiones directas de oxidos de nitrogeno.

---

## 6. Conclusiones para el cliente

1. **Impacto real y estadisticamente significativo:** La ZBE de Bilbao ha funcionado. La reduccion neta atribuible a la politica municipal es de **-1,28 µg/m³ de NO2** (entre un -6% y -8% adicional sobre la inercia metropolitana), concentrandose de forma nitida en los dias laborables y horarios de restriccion.
2. **Proteccion efectiva en episodios criticos:** El mayor beneficio para la salud publica se registra en situaciones de calma atmosferica e inversion termica invernal, donde la caida de contaminacion en el interior de Abando supero el **-20%**, reduciendo las horas en que se rebasan los umbrales de aviso de la OMS (25 µg/m³).
3. **Efecto de la Fase 2 mas discreto que la Fase 1:** La prohibicion de vehiculos sin etiqueta (Fase 1) genero el 78% del impacto total de reduccion. La exclusion de vehiculos con distintivo B para no residentes (Fase 2) ha tenido un efecto incremental menor, debido al elevado volumen de autorizaciones y excepciones concedidas en el centro urbano.

---

## 7. Recomendaciones de politica publica y movilidad

* **Revision de excepciones en la Fase 2:** Conviene auditar los permisos de acceso temporal y plazas de aparcamiento en rotacion comercial para evitar fugas que limiten el impacto en Maria Diaz de Haro.
* **Densificacion de la red de monitorizacion:** Disponer unicamente de dos estaciones oficiales en el interior de Abando es una limitacion de diseno. Se recomienda instalar una red de sensores micro-IoT calibrados en puntos criticos (Alameda Urquijo, Gran Via y salidas escolares) para obtener mapas de dispersion de alta resolucion espacial.
* **Mantenimiento del esquema horario:** Los datos demuestran que mantener la restriccion entre las 7:00 y las 20:00 es optimo, ya que cubre los picos matinales y de tarde sin sobrecargar innecesariamente la franja nocturna.

---

## 8. Justificacion de la seleccion de herramientas

* **Python + Pandas / Scipy / Statsmodels**: Seleccionado para la ingesta batch, saneamiento de tipos y modelado econometrico debido a su soporte nativo para series temporales vectorizadas y capacidad de estimar regresiones OLS robustas a heterocedasticidad.
* **InfluxDB 2.9 (TSDB)**: Elegido frente a bases de datos relacionales por su arquitectura especializada en series temporales con compresion TSM, permitiendo almacenar millones de lecturas horarias con politicas de retencion automatica sin mantenimiento de indices B-Tree.
* **Node-RED**: Utilizado como orquestador ligero de flujos en tiempo real por su facilidad para consultar APIs REST externas, gestionar reintentos ante caidas de red y transformar payloads a Line Protocol sin bloquear recursos.
* **Grafana 11.2**: Herramienta estandar para la creacion de cuadros de mando y alertas visuales con soporte de consultas Flux, control de acceso por organizaciones y equipos (RBAC) y gestion centralizada de permisos.
* **Docker y Docker Compose**: Garantiza la reproducibilidad absoluta del entorno en cualquier sistema operativo, encapsulando dependencias y variables de red interna mediante perfiles dedicados.

---

## 9. Planificacion temporal y reparto de responsabilidades

El proyecto se ejecuto en tres semanas siguiendo la metodologia agil Scrum:

| Miembro del equipo | Responsabilidades principales asumidas | Tareas especificas realizadas |
|---|---|---|
| **Alfred Gabriel** | Ingenieria de datos y modelado analitico SBD | Pipeline de descarga (`descargar_y_limpiar.py`), estimacion del modelo Diff-in-Diff en Jupyter y control meteorologico. |
| **Inigo** | Calidad de datos, visualizacion y redaccion ejecutiva | Diseno de figuras analiticas (g1 a g10), sintesis del informe para el cliente de 4 paginas y validacion de aforos de trafico. |
| **Kerman** | Arquitectura de contenedores, TSDB y monitorizacion BDA | Despliegue de Docker Compose, configuracion de InfluxDB (buckets y tokens), flujos Node-RED y cuadro de mando de Grafana. |

### Cronograma de ejecucion
* **Semana 1 (5 - 11 octubre):** Levantamiento de arquitectura Docker, conexion de APIs en Node-RED y adquisicion de datos historicos en crudo.
* **Semana 2 (12 - 18 octubre):** Saneamiento de calidad de datos, analisis exploratorio multivariable, estimacion econometrica y diseno de dashboards en Grafana.
* **Semana 3 (19 - 24 octubre):** Consolidacion del informe ejecutivo de 4 paginas, documentacion tecnica y preparacion de la defensa oral ante el tribunal.
