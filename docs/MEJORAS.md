# Registro de mejoras

Cada entrada sigue el formato: **ID → comentario literal → qué se ha cambiado → dónde → por qué**.
Las cifras citadas salen de `resultados/resultados.json` (ejecución del notebook en la rama `fix/pipeline-unico`).

---

## Fase 1 · Un solo pipeline y una sola fuente de cifras

### EV-10
- **Comentario:** «Posibles inconsistencias entre los datos limpios y los datos en crudo.»
- **Qué se ha cambiado:**
  - Se elimina el pipeline B (`scripts/`, `datos/`, `salida/` y los servicios `analisis` y `visualizar`). Daba otras cifras (DiD −1,81 frente a −1,63) porque mezclaba medias diarias con datos horarios, agregaba de otra forma y usaba otro viento.
  - Se corrigen cuatro errores del pipeline A que hacían que el dato limpio no coincidiera con el crudo (ver «Errores encontrados y corregidos»).
  - Nueva tabla crudo frente a limpio por estación: 336.480 filas crudas, 0 con fecha no válida, 0 repetidas, 336.480 limpias; 3.861 quedan fuera por ser posteriores al 30/09/2026 y 332.619 entran en el análisis.
- **Dónde:** `ingesta/descargar_y_limpiar.py` (`limpiar_calidad_aire`, `limpiar_meteorologia`, `integrar_datasets`); notebook, sección 3.1; `docker-compose.yml`; `Dockerfile`.
- **Por qué:** con un solo pipeline y una tabla que cuadra fila a fila, cualquier cifra se puede rastrear desde el fichero oficial hasta el resultado.

### EV-07
- **Comentario:** «Presentar con más claridad los resultados de las comprobaciones y verificar que las cifras de calidad y cobertura del informe coinciden con las obtenidas al ejecutar el código.»
- **Qué se ha cambiado:**
  - Sección 3.1 «Comprobación crudo frente a limpio»: filas por estación, filas quitadas y motivo, media de NO₂ en crudo y en limpio, y una frase por estación que explica la diferencia. Ejemplo: en Basauri la media pasa de 19,54 a 19,56 µg/m³ al quitar 35 valores negativos.
  - Las cifras de calidad y cobertura se guardan en `resultados/resultados.json` (bloque `calidad_datos`), para que el informe las lea de ahí y no se escriban a mano.
  - Los negativos son 71 valores, el 0,021 % de las filas (los documentos decían 0,04 %).
- **Dónde:** notebook, secciones 3.1 y 7; `resultados/resultados.json`.
- **Por qué:** el informe citaba cifras de calidad que no salían del código.

### SBD-05
- **Comentario:** «"completitud temporal superior al 98,8 %" — ¿Qué significa esto? ¿De dónde sale este dato?»
- **Qué se ha cambiado:** se define y se calcula. Completitud = horas con un dato válido de NO₂ ÷ horas que debería haber en el periodo (41.615 por estación, del 01/01/2022 00:00 al 30/09/2026 23:00, hora de Madrid). Total: 96,66 %. Por estación va de 91,98 % (Mª Díaz de Haro) a 99,07 % (Erandio). La meteorología tiene el 100 %.
- **Dónde:** notebook, sección 3.2; `resultados.json` → `calidad_datos.completitud_no2_*`.
- **Por qué:** el 98,8 % no salía de ningún cálculo. Ahora la cifra tiene definición, tabla y celda de origen. El informe se corrige en la fase 3.

### SBD-04
- **Comentario:** «"se armonizaron las unidades meteorológicas" — ¿en qué sentido?»
- **Qué se ha cambiado:**
  - Open-Meteo entrega el viento en km/h (lo declara la propia API y se guarda en `data/raw/meteorologia/open_meteo_unidades.json`). El análisis lo usa en m/s: m/s = km/h ÷ 3,6.
  - Antes la conversión dependía de una condición (`si el máximo > 40`); ahora se hace siempre.
  - El notebook lo comprueba: viento medio 8,85 km/h en crudo y 2,46 m/s en limpio; el cociente es 3,6.
  - La hora de la meteo también se pasa de GMT a hora de Madrid (ver «Errores encontrados»).
  - Esto resuelve también la discrepancia del MIA: el notebook usa m/s, no km/h. El documento del MIA se corrige en la fase 4.
- **Dónde:** `ingesta/descargar_y_limpiar.py` (`descargar_meteorologia`, `limpiar_meteorologia`); notebook, sección 3.3; `resultados.json` → `viento`.
- **Por qué:** «armonizar» no decía qué se había hecho. Ahora se dice qué unidad pasa a cuál, con la cifra.

### EV-08 (parcial; se completa en la fase 2)
- **Comentario:** (sin comentario; nivel «integración básica con poca justificación o comprobación»).
- **Qué se ha cambiado:**
  - El cruce aire-meteo se hace por la hora GMT, que es única. La hora local, en cambio, repite la 02:00 el día del cambio de hora de octubre.
  - Se imprimen las filas antes y después de cada JOIN (332.619 → 332.619 → 332.619; retención del 100 %, antes 99,82 %).
  - Los duplicados por estación y hora GMT son 0.
- **Dónde:** `ingesta/descargar_y_limpiar.py` (`integrar_datasets`); notebook, celda «8. Ejecución del JOIN integrado».
- **Por qué:** antes se perdían 600 filas en el cruce porque la meteo terminaba antes que el aire. Además, el cruce emparejaba horas distintas (ver «Errores encontrados»).

---

## Errores encontrados y corregidos en la fase 1

Estos errores no venían en las correcciones; se encontraron en el diagnóstico (`docs/DIAGNOSTICO.md`). El equipo decidió corregirlos aunque cambien cifras ya presentadas.

| Error | Qué pasaba | Corrección | Dónde |
|---|---|---|---|
| **Zip de Open Data Euskadi** | Cada zip anual trae `datos_horarios/` y `datos_diarios/` con ficheros del mismo nombre. Se guardaba solo el nombre del fichero, los diarios pisaban a los horarios y, desde un clon limpio, la limpieza fallaba (`ValueError: No objects to concatenate`). | Solo se extraen los ficheros de `datos_horarios/`. | `descargar_calidad_aire` |
| **Hora de la meteo** | Open-Meteo da la hora en GMT y se trataba como hora de Madrid. Cada medición de NO₂ se cruzaba con el tiempo de 1 h más tarde en invierno y 2 h más tarde en verano. | La meteo se pasa a hora de Madrid y el cruce se hace por la hora GMT. | `limpiar_meteorologia`, `integrar_datasets` |
| **Columna «NO» de Mazarredo** | La búsqueda por trozo de texto encontraba «no» dentro de «Benceno», así que en Mazarredo la columna `no` era en realidad el benceno. | Se compara el nombre exacto de la cabecera oficial. | `MAPEO_CONTAMINANTES`, `limpiar_calidad_aire` |
| **PM2,5 vacía** | La cabecera «PM2,5» nunca coincidía, así que `pm25` salía vacía en todas las estaciones. | Mismo cambio: ahora tiene datos en las 6 estaciones que la miden (Arraiz y Castrejana no la miden). | `MAPEO_CONTAMINANTES` |
| **Cambio de hora de octubre** | Se quitaban duplicados por hora local, y la 02:00 de ese día aparece dos veces. Se borraban 32 lecturas reales (4 por estación: una por cada octubre de 2022 a 2025). | Se quitan duplicados por hora GMT. Ahora no se borra ninguna fila. | `limpiar_calidad_aire` |
| **Fecha de fin variable** | El final del estudio lo marcaba, sin querer, la fecha hasta la que se descargaba la meteo. | `FECHA_FIN = 30/09/2026`, definida una sola vez al principio del notebook. | Notebook, celda 1 |
| **Efecto DiD sobrescrito** | El bucle de P4 reutilizaba el nombre `efecto_neto_did`, de modo que al final valía el del SO₂. | Variable propia en el bucle (`efecto_neto_c`). | Notebook, celda «20. P4» |
| **Calma post** | Era la media simple de la calma en fase 1 y fase 2. | Media de todas las horas posteriores a la ZBE con viento en calma (decisión del equipo). | Notebook, celda «16. Gráfica 6» |

### Cifras que cambian

| Cifra | Antes | Ahora | Causa |
|---|---|---|---|
| Filas limpias de aire | 333.376 | 336.480 (332.619 en el periodo) | Zip, cambio de hora y fecha de fin |
| Retención del JOIN | 99,82 % | 100 % | Meteo descargada para todo el periodo y cruce por hora GMT |
| DiD NO₂ (P1) | −1,63 | −1,63 | No cambia |
| Efecto neto en horario ZBE / fuera de horario (P2) | −2,93 / −0,86 | −2,93 / −0,85 | Fecha de fin |
| Calma dentro: antes → fase 1 → fase 2 | 28,10 → 25,47 → 23,56 | 29,32 → 26,61 → 24,82 | Hora de la meteo |
| Calma post | 24,52 (−12,8 %) | 25,56 (−12,84 %) | Hora de la meteo y nueva definición |
| Regresión con controles | −1,74 | −1,73 | Hora de la meteo |
| Correlación NO₂-viento / NO₂-temperatura (dentro) | −0,22 / −0,22 | −0,30 / −0,27 | Hora de la meteo |
| NO dentro (P4) | Mazarredo usaba el benceno | −34,46 % | Mapeo de columnas |
| PM2,5 dentro (P4) | Vacía | −7,93 % (efecto neto +0,14) | Mapeo de columnas |
| Gradient Boosting (provisional) | −2,87; R² 0,472; MAE 7,78 | −2,77; R² 0,514; MAE 7,53 | Hora de la meteo. La validación sigue sin ser temporal: no se cita hasta la fase 4 |

### Otros cambios
- `ingesta/carga_historica.py` lee ahora la salida del pipeline A (`data/clean/calidad_aire_limpio.csv` y `data/clean/meteorologia_limpia.csv`) y usa la hora GMT como instante. Antes cargaba el zip y la meteo del pipeline B.
- `trafico_accesos_bilbao.csv` se mueve de `datos/procesados/trafico/` a `data/clean/`.
- El servicio `sbd-notebook` monta `resultados/` para que `resultados.json` se guarde fuera del contenedor.

---

## Fase 2 · Notebook SBD simple

Las cifras salen de `resultados/resultados.json` (ejecución del notebook en la rama `fix/analisis-sbd-simple`). Las 149 cifras que ya existían en la fase 1 no cambian.

### EV-09
- **Comentario:** «Lo presentado no tiene ningún tipo de coherencia, se ha intentado un análisis demasiado complejo que ni vosotros entendéis. […] Tenéis que hacer un análisis que seáis capaces de entender vosotros.»
- **Qué se ha cambiado:**
  - El notebook se reorganiza en torno a cinco preguntas (P1-P5). Cada una tiene una consulta en pandas, una tabla, una gráfica y una frase «Qué significa».
  - Se quitan la regresión OLS con `summary()` y sus p-valores, la matriz de correlaciones, el perfil horario, la comparación de 8 contaminantes, los aforos de tráfico, el GeoJSON y 5 de las 10 gráficas.
  - Todos los textos con cifras se generan con f-strings. Las conclusiones y recomendaciones se escriben a partir de `resultados.json`.
- **Dónde:** `notebooks/zbe_bilbao.ipynb`, secciones 1-8.
- **Por qué:** un solo método (la resta de restas) responde a las cinco preguntas, y el equipo puede explicar cada cifra.

### SBD-14
- **Comentario:** «"p < 0,001", "desmontando titulares inflados"» (tono efectista; incertidumbre mal presentada).
- **Qué se ha cambiado:** se quitan los p-valores del OLS horario. El margen de error se calcula con un bootstrap por bloques semanales (2.000 repeticiones). Efecto neto del NO₂: −1,63 µg/m³, con un intervalo del 95 % de −2,38 a −0,94. Se explica en dos líneas por qué las horas consecutivas no son independientes.
- **Dónde:** notebook, apartado 6.2 (función `efecto_neto_con_intervalo`); `resultados.json` → `p1_did.ic95_*`.
- **Por qué:** con más de 300.000 horas tratadas como independientes, el margen salía demasiado estrecho (±0,24) y el «p < 0,001» daba una seguridad falsa.

### SBD-06
- **Comentario:** «¿por qué? ¿con qué contexto? ¿Máx.? ¿Alta? ¿Media?»
- **Qué se ha cambiado:** el criterio es cuánto cambia la respuesta la decisión de ampliar, mantener o ajustar la ZBE. Hay dos niveles definidos: alta (cambia la decisión por sí sola: P1, P2, P5) y media (comprueba una pregunta alta: P3, P4). Cada pregunta lleva una frase.
- **Dónde:** notebook, sección 2.
- **Por qué:** las etiquetas «Máxima, Alta, Media» no tenían criterio.

### SBD-02
- **Comentario:** nombres de las fuentes subrayados.
- **Qué se ha cambiado:** tabla con quién publica cada fuente, el formato, el periodo, la frecuencia, las variables usadas y para qué pregunta. La fuente oficial de cada festivo queda como `[PENDIENTE DE VERIFICAR]`.
- **Dónde:** notebook, sección 3.
- **Por qué:** era una lista de nombres sin datos de cada fuente.

### SBD-03
- **Comentario:** «se convirtieron a **NaN**» (círculo).
- **Qué se ha cambiado:** se explica qué es NaN, con un ejemplo, y por qué no se pone un 0 (bajaría la media) ni se borra la fila (se perderían el SO₂ y el viento de esa hora).
- **Dónde:** notebook, sección 3.
- **Por qué:** el término se usaba sin explicar.

### SBD-07 y SBD-08
- **Comentario:** «¿es un sesgo? ¿en qué sentido?» · «cuenca y flota» (subrayado).
- **Qué se ha cambiado:** se explica sin esos términos. Comparar solo antes y después mezcla el efecto de la ZBE con lo que habría bajado igualmente (el tiempo, coches más nuevos y limpios, cambios de movilidad). Las estaciones de control tienen «el mismo tiempo atmosférico y el mismo tipo de coches, pero no la ZBE».
- **Dónde:** notebook, sección 6, «Definiciones».
- **Por qué:** la jerga no se entendía. El informe se corrige en la fase 3.

### SBD-09
- **Comentario:** columna «Rol» → «??».
- **Qué se ha cambiado:** se definen tratamiento, control y fondo, con las estaciones de cada grupo y el motivo. Arraiz (fondo) no entra en el control porque está en un monte, lejos del tráfico, y su NO₂ es mucho más bajo (8,73 µg/m³ antes de la ZBE frente a 18,25 de media en el control).
- **Dónde:** notebook, sección 6, «Definiciones», y tabla por estación de P1.
- **Por qué:** los grupos no estaban explicados.

### SBD-10
- **Comentario:** «¿Qué es cada indicador?»
- **Qué se ha cambiado:** se definen Pre-ZBE (01/01/2022-14/06/2024), Post-ZBE (15/06/2024-30/09/2026), fase 1, fase 2, caída bruta y efecto neto. P1 muestra la resta de restas con nuestros números: (21,91 − 25,50) − (16,29 − 18,25) = −1,63. La tabla por estación se genera en el notebook y se guarda en `estaciones_no2`.
- **Dónde:** notebook, sección 6 y P1; `resultados.json` → `p1_did`, `estaciones_no2`.
- **Por qué:** las columnas del informe no estaban definidas y las cifras por estación no salían del código. El informe se rehace en la fase 3.

### SBD-12
- **Comentario:** −2,93 presentado como caída; placebo SO₂ «p > 0,40»; «corroborando la causalidad».
- **Qué se ha cambiado:**
  - P2 dice que −2,93 es un efecto neto, no una caída. En horario ZBE el NO₂ bajó 4,64 dentro y 1,71 fuera; −2,93 es la diferencia.
  - Se quita el «3,4 veces».
  - El SO₂ no tiene p-valor. Su efecto neto es +0,33 µg/m³, con un intervalo de −0,01 a +0,66, que incluye el cero. Castrejana no mide SO₂ y no entra en ese cálculo.
- **Dónde:** notebook, P2 y P4; `resultados.json` → `p2_horario`, `p4_so2`.
- **Por qué:** el p-valor del SO₂ no existía en el código y «caída» confundía dos cifras distintas.

### SBD-15
- **Comentario:** «Rendimientos decrecientes en Fase 2» contradice el notebook («ganancia progresiva continuada», −8,3 % adicional).
- **Qué se ha cambiado:** se calcula el efecto neto de cada fase contra el control. Fase 1 frente a antes: −1,29 µg/m³ (de −2,43 a −0,13). Fase 2 frente a fase 1: −0,52 µg/m³ (de −1,72 a +0,74). Conclusión única: la fase 2 no muestra una bajada adicional que se pueda distinguir de cero, y la bajada propia de dentro se produjo sobre todo con la fase 1. Se quitan las dos frases contradictorias y el −8,3 %, que era una caída bruta sin control.
- **Dónde:** notebook, P5 y sección 8; `resultados.json` → `p5_fases`.
- **Por qué:** había dos conclusiones opuestas y ninguna descontaba lo que bajó fuera.

### MIA-05
- **Comentario:** «objetivo final !!!» · «no perdáis el foco».
- **Qué se ha cambiado:** el contexto (5 líneas), la prioridad de las preguntas y las tres recomendaciones giran en torno a la decisión de ampliar, mantener o ajustar la ZBE. El documento MIA se corrige en la fase 4.
- **Dónde:** notebook, secciones 1, 2 y 8.
- **Por qué:** el análisis debe servir a esa decisión.

### MIA-07
- **Comentario:** «¿qué tendencia traía la ciudad?»
- **Qué se ha cambiado:** tabla de medias anuales por zona. De 2022 a 2023 el NO₂ medio pasó de 25,85 a 25,95 dentro (+0,10) y de 19,09 a 17,95 fuera (−1,14). Se dice que antes de la ZBE no iban del todo en paralelo y que, por eso, el efecto neto es una estimación aproximada.
- **Dónde:** notebook, P1; `resultados.json` → `medias_anuales_no2`.
- **Por qué:** la frase no tenía datos detrás.

### EV-08 (se completa)
- **Comentario:** (sin comentario; nivel «integración básica con poca justificación o comprobación»).
- **Qué se ha cambiado:** la sección de integración explica qué se añade a cada medición y por qué se cruza cada fuente por una clave distinta: el calendario por la fecha en hora de Madrid y la meteorología por la hora GMT. Se comprueban las filas antes y después (332.619 → 332.619), las repetidas (0) y las filas sin viento o sin fase (0). Hay una conclusión por fuente.
- **Dónde:** notebook, secciones 4.3 y 5.
- **Por qué:** faltaba justificar el JOIN.

### EV-07 (ajuste)
- **Comentario:** «Presentar con más claridad los resultados de las comprobaciones…»
- **Qué se ha cambiado:** la tabla crudo frente a limpio la genera ahora `ingesta/descargar_y_limpiar.py` (función `guardar_comprobacion_crudo_limpio`) en `data/clean/comprobacion_crudo_limpio.csv`. El notebook solo la lee. Se ha calculado una sola vez con los crudos locales y coincide con los ficheros limpios de la fase 1.
- **Dónde:** `ingesta/descargar_y_limpiar.py`; `data/clean/comprobacion_crudo_limpio.csv`; notebook, apartado 4.1.
- **Por qué:** los crudos no se versionan. Con la tabla en `data/clean/`, el notebook se ejecuta desde un clon sin volver a descargar ni limpiar (decisión 15 del equipo).

### Cifras que se dejan de calcular en el notebook

| Cifra | Antes | Motivo |
|---|---|---|
| Regresión con controles meteorológicos (OLS) | −1,73 | Respondía a lo mismo que P1 (−1,63) con un método más difícil de explicar. Además, su p-valor trataba cada hora como un dato independiente, así que daba una seguridad falsa. El margen de error lo da ahora el bootstrap semanal |
| Correlaciones NO₂-viento / NO₂-temperatura | −0,30 / −0,27 | No responde a ninguna pregunta |
| NO, NOx, CO, benceno, PM10, PM2,5 | Tabla de P4 | P4 pregunta solo por el SO₂. El CO y el benceno no los miden todas las estaciones |
| Aforos de San Mamés | −10,12 % (2023-2024) | No responde a ninguna de las cinco preguntas |
| Gradient Boosting | −2,77 | Se mantiene en el anexo como provisional y no se cita hasta la fase 4 |

---

## Fase 3 · Informe SBD impreso

El informe se rehace entero. `docs/generar_informe.py` lee `resultados/resultados.json` y escribe `docs/informe-cliente-sbd.md`, el `.docx` y el `.pdf` (estos dos, con Word). Ninguna cifra del informe está escrita a mano. Si una cifra cambia de signo y una frase deja de ser cierta, el script se para.

Formato: portada y 4 páginas de cuerpo en A4, en Arial 11 (títulos en Arial 12). El PDF generado tiene 5 páginas. Todo el texto es Arial: el 2 de NO2 y SO2 va como subíndice de Word y las viñetas son un carácter de Arial.

### SBD-01
- **Comentario:** «renovación vegetativa» → «??».
- **Qué se ha cambiado:** «la sustitución normal de coches viejos por otros más limpios, que ocurre con o sin ZBE». Se quita «dictaminar».
- **Dónde:** informe, sección 1.
- **Por qué:** era jerga que no se entendía.

### SBD-02, SBD-03, SBD-04 y SBD-05
- **Comentarios:** fuentes subrayadas · «NaN» (círculo) · «¿armonizaron, en qué sentido?» · «98,8 %: ¿qué significa? ¿de dónde sale?».
- **Qué se ha cambiado:** la sección 3 tiene:
  - una tabla de fuentes con quién la publica, el formato y la frecuencia, las variables y la pregunta;
  - qué es NaN y por qué no se pone 0 ni se borra la fila;
  - la conversión exacta del viento (km/h ÷ 3,6, media 8,85 → 2,46) y de la hora (GMT → Madrid);
  - la completitud definida y calculada: 96,66 % en total, de 91,98 % a 99,07 % por estación. El 98,8 % desaparece.
- **Dónde:** informe, sección 3.
- **Por qué:** cada término y cada cifra tenían que tener definición y origen.

### SBD-06
- **Comentario:** «¿por qué? ¿con qué contexto? ¿Máx.? ¿Alta? ¿Media?»
- **Qué se ha cambiado:** se usa el mismo criterio que en el notebook (cuánto cambia la respuesta la decisión), con dos niveles definidos y una frase por pregunta.
- **Dónde:** informe, sección 2.
- **Por qué:** los niveles no tenían criterio.

### SBD-07, SBD-08 y SBD-09
- **Comentarios:** «¿es un sesgo?» · «cuenca y flota» · columna «Rol» → «??».
- **Qué se ha cambiado:**
  - Se quitan «sesgo», «cuenca y flota» y «Rol».
  - Se definen los grupos dentro (tratamiento), fuera (control) y fondo, con sus estaciones y el motivo de cada uno. Arraiz no entra en el control.
  - Se explica por qué no basta con comparar antes y después.
- **Dónde:** informe, sección 4.
- **Por qué:** el lector no sabía qué significaba cada grupo.

### SBD-10 y SBD-11
- **Comentarios:** «¿Qué es cada indicador?» · Europa 20,10 → 17,55 en el impreso y 21,30 → 18,35 en el `.md`.
- **Qué se ha cambiado:**
  - Tabla de estaciones sin la columna «Papel», con la definición de cada columna debajo y los periodos con fechas exactas.
  - Todas las filas salen de `resultados.json` → `estaciones_no2`. Europa es 20,92 → 15,32 (−26,8 %) en el `.md`, el `.docx` y el `.pdf`.
  - Las estaciones de dentro ya no salen intercambiadas: Mazarredo es 22,44 → 19,07 y Mª Díaz de Haro, 28,67 → 25,03.
- **Dónde:** informe, sección 4.
- **Por qué:** las cifras por estación no salían del código y eran distintas en cada documento.

### SBD-12
- **Comentario:** −2,93 presentado como caída; «p > 0,40»; «corroborando la causalidad».
- **Qué se ha cambiado:** P2 dice que −2,93 es un efecto neto, no una caída. El SO₂ se da con su intervalo (de −0,01 a +0,66), sin p-valor. Se quitan «corroborando», «3,4 veces» y «causal».
- **Dónde:** informe, sección 5 (P2 y P4).
- **Por qué:** igual que en el notebook (fase 2).

### SBD-13
- **Comentario:** el panel oscuro de 4 cuadrantes es ilegible impreso.
- **Qué se ha cambiado:**
  - Se elimina `docs/img/dashboard_decision_v1.png`, como pide la decisión 12 del equipo.
  - El informe lleva 3 gráficas del notebook con fondo claro: evolución mensual (P1), horario (P2) y fases (P5).
  - Las gráficas se han reducido en el notebook para que el texto se lea impreso a 11-15 cm de ancho. Solo cambia el tamaño; `resultados.json` no cambia.
- **Dónde:** informe, sección 5; notebook, celdas de las gráficas.
- **Por qué:** el panel venía del pipeline B, era oscuro y tenía cifras fijas que ya no eran correctas («−7,1 %»).

### SBD-14
- **Comentario:** «p < 0,001», «desmontando titulares inflados».
- **Qué se ha cambiado:** se quitan el p-valor y el tono efectista. La incertidumbre se da como intervalo del 95 % y se explica en tres líneas.
- **Dónde:** informe, secciones 4 y 5.
- **Por qué:** el p-valor del OLS horario era engañoso.

### SBD-15
- **Comentario:** «Rendimientos decrecientes en Fase 2» contradice el notebook.
- **Qué se ha cambiado:** una sola conclusión, igual que en el notebook: la fase 2 no muestra una bajada adicional distinguible de cero (−0,52; de −1,72 a +0,74). La bajada propia de dentro llegó sobre todo con la fase 1 (−1,29).
- **Dónde:** informe, secciones 5 (P5) y 6.
- **Por qué:** el informe y el notebook decían cosas opuestas.

### SBD-16
- **Comentario:** el reparto de responsabilidades debe reflejar lo que hizo cada uno de verdad y el orden de tareas.
- **Qué se ha cambiado:** la sección 8 tiene el orden de las tareas (de la descarga al informe) y, para cada una, el responsable con su rol y su área (Product Owner · Relación con el cliente y desarrollo; Lead Data Engineer · Datos e infraestructura; Scrum Master · Análisis y modelado). Se usan áreas, no nombres de módulos del curso. El equipo dio los roles y cada tarea se asignó al rol que mejor encaja. Debajo se añade: «Todo el equipo conoce y puede explicar el trabajo completo; la asignación indica quién lideró cada tarea».
- **Dónde:** informe, sección 8.
- **Por qué:** el reparto anterior tenía roles inventados y no mostraba el orden de las tareas.

### EV-07 (informe)
- **Comentario:** «verificar que las cifras de calidad y cobertura del informe coinciden con las obtenidas al ejecutar el código».
- **Qué se ha cambiado:** las cifras de calidad del informe se leen de `resultados.json` → `calidad_datos`: 0,021 % de negativos (antes decía 0,04 %), completitud del 96,66 % (antes 98,8 %) y 332.619 filas (antes 332.776).
- **Dónde:** informe, sección 3.
- **Por qué:** el informe citaba cifras que no salían del código.

### Otros cambios del informe
- Se quitan las referencias al curso, al módulo y al reto, la checklist de la rúbrica y la tabla RACI con roles inventados.
- Se quitan cifras sin fuente verificada: «27 cámaras», «2 km²», «Abando», los aforos de San Mamés y las dos referencias bibliográficas.
- La sección de herramientas explica por qué InfluxDB y no SQL Server, y deja claro que Node-RED es automatización, no IA.
- El notebook dice en una frase que el análisis llega hasta el 30/09/2026 y que Grafana puede mostrar datos posteriores (decisión 11). El informe lo dice en la sección 3.

---

## Fase 4 · MIA: modelo y documento

Las cifras salen de `resultados/resultados.json`, bloque `modelo_ia` (ejecución del notebook en la rama `fix/mia`). El resto de bloques no cambia. `docs/generar_mia.py` lee ese fichero y escribe `docs/propuesta-modelo-ia.md`, `docs/MIA_Haizen_Lab.docx` y `.pdf`. Ninguna cifra del documento está escrita a mano. Si una cifra cambia y una frase deja de ser cierta, el script se para. `docs/generar_informe.py` solo cambia para que sus funciones de salida (Markdown, HTML y Word) acepten el contenido como parámetro; el informe SBD que genera no cambia.

### Notebook: anexo del modelo de IA

| Paso | Qué se hace | Resultado |
|---|---|---|
| Datos | Las 7 estaciones de dentro y de fuera; variables de tiempo atmosférico (temperatura, humedad, lluvia, viento), calendario (hora, día de la semana, mes, laborable, festivo) y estación | 118.804 horas-estación de entrenamiento y 27.613 de validación |
| Validación temporal | Entrenar 01/01/2022 – 31/12/2023 y validar 01/01/2024 – 14/06/2024, ordenado por fecha; un `assert` comprueba que la validación es posterior | — |
| Comparación | Base sin IA (NO₂ medio de cada estación a esa hora en ese mes), regresión lineal, Random Forest y Gradient Boosting | MAE en validación: 10,50 / 9,79 / 8,14 / 8,15 |
| Modelo elegido | Menor MAE en validación | Random Forest (22,5 % menos error que la base) |
| Efecto | (observado − predicho) dentro − fuera, por semanas, con bootstrap | −0,49 µg/m³ (de −0,86 a −0,12) |
| Placebo | ZBE ficticia el 15/06/2023, solo con datos anteriores a la ZBE | +0,33 (de −0,23 a +0,96): incluye el cero |
| Importancia | `permutation_importance` en la validación | Viento +2,48, hora +2,07, estación +1,87 µg/m³ de MAE |
| Límite horario | Horas-estación con NO₂ > 200 µg/m³ | 0 en todos los años; máximo 168 µg/m³ |

### EV-04
- **Comentario:** «El problema no es solo una regresión: el objetivo es estimar el efecto de una política pública. Predecir bien el NO₂ no demuestra que la ZBE haya causado la reducción. No se concreta qué estaciones externas se usan como referencia, cómo se seleccionan ni si son comparables.»
- **Qué se ha cambiado:**
  - El modelo ya no mira solo dentro: el efecto es la diferencia (observado − predicho) dentro menos la de fuera. Así se descuenta lo que el modelo no conoce y pasa en toda la comarca: el modelo también se pasa fuera (−1,73).
  - El documento explica por qué predecir no basta, nombra las 5 estaciones de control, el criterio de elección y en qué son comparables y en qué no (nivel distinto, tendencia previa +0,10 frente a −1,14, bajada de Europa).
- **Dónde:** notebook, anexo A.3; MIA, sección 1.
- **Por qué:** el modelo anterior atribuía a la ZBE también la bajada de toda la comarca.

### EV-05 y EV-06
- **Comentarios:** «Explicación superficial […]. No se desarrolla su funcionamiento ni el alcance de sus resultados.» · «Falta justificar en profundidad Gradient Boosting. La validación, la estimación de la incertidumbre y SHAP requieren explicación precisa. La comparación con DiD necesita desarrollar sus limitaciones.»
- **Qué se ha cambiado:**
  - Se explica cómo funciona cada modelo en una línea y cómo decide un árbol, con preguntas sobre nuestros datos.
  - La elección se justifica con la tabla de métricas: gana Random Forest por 0,01 µg/m³ frente a Gradient Boosting; se dice que casi empatan y que el criterio (menor MAE en validación) estaba fijado de antemano.
  - Validación temporal, intervalo bootstrap por semanas y placebo explicados en llano, con su resultado.
  - SHAP se elimina del documento y del chatbot; en su lugar, importancia por permutación, que sí está calculada.
  - Comparación con DiD: modelo −0,49 y DiD −1,63. Los intervalos no se solapan y se dice que el tamaño del efecto es incierto.
- **Dónde:** notebook, anexo A.1-A.5; MIA, secciones 4, 5 y 8; `chatbot/main.py` (dos frases).
- **Por qué:** el documento prometía técnicas que no estaban hechas y no explicaba las que sí.

### EV-01, EV-02 y EV-03
- **Comentarios:** aplicaciones sin sentido («¿cómo se resuelve "lanzar avisos"? ¿solo con modelos de predicción?») y sin casos reales · contrafactual sin explicar, familias como enumeración, «DiD no es IA. La automatización de tareas no es una técnica de IA» · «no se proponen elementos medibles».
- **Qué se ha cambiado:**
  - Cinco casos reales, con su fuente al final ([1]-[5]) y su relación con nuestro problema. Quedan como `[PENDIENTE DE VERIFICAR]` la página oficial de Google Project Green Light y la versión vigente del protocolo de Madrid, porque sus webs no se pudieron consultar.
  - Avisos: la cadena predicción (IA) → umbral (regla) → aviso (regla). Con nuestros datos no hubo ninguna hora por encima de 200 µg/m³, así que se dice que esta aplicación tiene menos relación con la decisión.
  - Familias en una tabla: qué son, un ejemplo ligado a los casos y si se usan aquí. La automatización (Node-RED) y DiD salen de las familias y se dice que no son IA.
  - Tabla de 5 indicadores medibles: trabajo manual, tiempo hasta el panel, error del modelo, horas > 200 µg/m³ y efecto. El trabajo manual queda `[A COMPLETAR POR EL EQUIPO]` porque no se ha medido.
- **Dónde:** MIA, secciones 2, 3 y 7.
- **Por qué:** cada aplicación tenía que conectar con la decisión del cliente y poder medirse.

### MIA-01, MIA-04, MIA-28 y MIA-29
- **Comentarios:** cabecera del curso tachada · «ocho puntos del enunciado» → «??» · «Checklist de verificación» → «?» · «Demasiado complejo, tenéis que entenderlo vosotros primero».
- **Qué se ha cambiado:** portada de cliente (cliente, equipo, periodo, fecha), sin curso, módulo, reto, enunciado ni checklist. Cada término técnico se define la primera vez. Se quitan «validez concluyente», «inversión térmica», «Abando», «2 km²» y «27 cámaras».
- **Dónde:** MIA, portada y todo el documento.
- **Por qué:** es un documento para el Ayuntamiento y el equipo tiene que poder defender cada frase.

### MIA-02, MIA-03 y MIA-05
- **Comentarios:** «Para saber si algo funciona o no» · «¿técnico o lenguaje coloquial?» · «objetivo final !!!», «no perdáis el foco».
- **Qué se ha cambiado:** el objetivo es una frase: saber si la ZBE funciona y decidir si ampliarla, mantenerla o ajustarla. Se define «dentro» (estaciones situadas en la ZBE) y se concreta «todo lo demás» (tiempo atmosférico y renovación de coches). El documento cierra con «Qué significa para la decisión».
- **Dónde:** MIA, secciones 1 y 8.
- **Por qué:** todo el documento debe girar en torno a la decisión.

### MIA-06
- **Comentario:** «¿La ZBE es sólo NO₂? No se explica».
- **Qué se ha cambiado:** se explica por qué el NO₂: sale sobre todo de los tubos de escape y tiene límites legales (40 µg/m³ de media anual y 200 en una hora). También por qué no los demás: el SO₂ se usa como comprobación (+0,33, no baja), las partículas tienen muchas otras fuentes, NO y NOx dirían lo mismo, y CO y benceno no los miden todas las estaciones (decisión 16).
- **Dónde:** MIA, sección 1.
- **Por qué:** no se justificaba la elección del contaminante.

### MIA-07, MIA-08, MIA-09 y MIA-12
- **Comentarios:** «¿qué tendencia traía la ciudad?» · contrafactual → «??» · entradas y salida → simplificar · «¿qué ruido? ¿por qué?».
- **Qué se ha cambiado:**
  - Tendencia: +0,10 dentro y −1,14 fuera de 2022 a 2023.
  - Contrafactual con un ejemplo: después de la ZBE, dentro se midieron 21,91 µg/m³ y el modelo calcula unos 24,1 sin ZBE.
  - Entradas y salida en una línea.
  - Ruido: la variación que el modelo no explica (63 % de la variación horaria: atascos, obras, eventos, fallos del sensor). Importa porque el efecto es pequeño frente al error de 8,14 µg/m³ por hora.
- **Dónde:** MIA, sección 1.
- **Por qué:** eran términos sin definir.

### MIA-10, MIA-11 y MIA-14
- **Comentarios:** «habrá que comparar la predicción con la realidad y tener un indicador real» · «Temporal» (círculo) · «¿dónde hay overfitting?».
- **Qué se ha cambiado:** el indicador real es el MAE en validación frente al modelo base (8,14 frente a 10,50). Se explica la validación temporal: no usar el futuro para predecir el pasado. Sobreajuste con cifras: Random Forest tiene 4,77 en entrenamiento y 8,14 en validación; se elige por el error en validación.
- **Dónde:** notebook, anexo A.1; MIA, secciones 1, 2, 4 y 8.
- **Por qué:** la validación antigua no era temporal y no había indicador.

### MIA-13, MIA-15 y MIA-16
- **Comentarios:** «cómo aplicáis a vuestro proyecto» · «leed los comentarios del excel» · DiD como técnica de IA → «IA?».
- **Qué se ha cambiado:** la tabla de principios tiene una columna «En nuestro caso» con cifras. Las familias se relacionan con los casos (ver EV-01 y EV-02). DiD sale de las técnicas de IA.
- **Dónde:** MIA, secciones 2 y 3.
- **Por qué:** eran enumeraciones sin relación con el proyecto.

### MIA-17, MIA-18, MIA-19 y MIA-20
- **Comentarios:** SARIMAX «poco flexibles» → «?? por qué» · LSTM → «por qué?» · «¿no hay otros modelos que encajen con los que comparar?» · «no lineal» subrayado.
- **Qué se ha cambiado:**
  - Tres modelos de IA y una base, con la misma tabla de métricas.
  - SARIMAX: el tiempo entra como una suma con peso fijo, como en la regresión lineal (MAE 9,79), y sus valores pasados de NO₂ ya llevan el efecto de la ZBE.
  - LSTM: muchos parámetros para dos años de datos, difícil de explicar, más cálculo y el mismo problema que SARIMAX. Se dice que las dos se descartan sin probarlas.
  - No linealidad con nuestros datos: NO₂ medio por tramo de viento (24,01 → 24,84 → 21,53 → 16,29 → 13,16 → 8,02). Entre 0-1 y 1-2 m/s sube 0,83; de 2-3 a 3-4 baja 5,24.
- **Dónde:** notebook, anexo A.1 y A.2; MIA, secciones 4 y 5.
- **Por qué:** faltaban argumentos concretos y modelos con los que comparar.

### MIA-21 y MIA-26
- **Comentarios:** «el efecto agregado por fase y franja» → «¿cómo?» · «Separa el efecto» (círculo).
- **Qué se ha cambiado:** cuatro pasos en llano y la resta con nuestros números: −2,21 − (−1,73) = −0,49. Se explica cómo se separa: el modelo descuenta el tiempo y la resta con fuera descuenta lo demás. El modelo no desglosa por fase ni por franja; eso lo hacen P2 y P5 del informe.
- **Dónde:** notebook, anexo A.3; MIA, secciones 5 y 8.
- **Por qué:** no se decía cómo se calculaba.

### MIA-22 y MIA-24
- **Comentarios:** «¿entendéis esto?» (tendencias paralelas…) · «Contraste con DiD» → «¿por qué?».
- **Qué se ha cambiado:** «Por qué DiD no es el modelo principal» en tres líneas: solo resta medias y no descuenta el tiempo hora a hora. Se usa para comparar porque es simple y no depende de ningún modelo. Se quitan «tendencias paralelas» y «corrección lineal».
- **Dónde:** MIA, sección 8.
- **Por qué:** el texto anterior no se podía defender oralmente.

### MIA-23 y MIA-27
- **Comentarios:** «Tres placebos» (círculo) · «Vale → ¿cómo lo medís?».
- **Qué se ha cambiado:**
  - Se define placebo con un ejemplo.
  - Solo se citan las comprobaciones hechas: la fecha falsa (+0,33; de −0,23 a +0,96) y el SO₂ (+0,33; de −0,01 a +0,66).
  - Se dice que el placebo se aleja de cero tanto como el efecto del modelo, así que ese efecto se da con cautela.
  - Se quitan el placebo de «estaciones exteriores», que no estaba hecho, y la «regla de integridad».
- **Dónde:** notebook, anexo A.4; MIA, sección 8 (tabla de riesgos con comprobación y resultado).
- **Por qué:** cada riesgo tiene que llevar su comprobación y su cifra.

### MIA-25
- **Comentario:** «¿qué lo son? ¿el modelo?».
- **Qué se ha cambiado:** el título dice «de la solución» y una frase aclara que se refiere al modelo más la comparación con las estaciones de fuera.
- **Dónde:** MIA, sección 8.
- **Por qué:** no estaba claro de qué eran las ventajas y los riesgos.

### Cifras que cambian

| Cifra | Antes | Ahora | Causa |
|---|---|---|---|
| Modelo | Gradient Boosting (provisional) | Random Forest | Menor MAE en validación temporal frente a 3 alternativas |
| Error del modelo | MAE 7,53; R² 0,514 (validación no temporal) | MAE 8,14; R² 0,37 (validación temporal) | La validación anterior veía horas de la misma semana |
| Efecto del modelo en el notebook | −2,77 µg/m³ (solo dentro, sin intervalo) | −0,49 (de −0,86 a −0,12), dentro − fuera | Se resta lo que pasó fuera |

El chatbot (`chatbot/main.py` y `knowledge_base.json`) aún cita el −2,87 del modelo antiguo. Solo se le quita SHAP en esta fase; sus cifras se actualizan en la fase 6 (punto 4).

### Ajustes tras la revisión del equipo (rama `fix/mia-ajustes`)
No cambia ninguna cifra de `resultados.json`. Solo cambia el texto de `docs/generar_mia.py` y se regeneran el `.md`, el `.docx` y el `.pdf`.

| ID | Qué se ha cambiado | Dónde | Por qué |
|---|---|---|---|
| EV-06, MIA-24 | Se explica en llano por qué el modelo da menos que DiD (−0,49 frente a −1,63): DiD resta medias y no descuenta el tiempo atmosférico, y el modelo sí. Se mantiene que los intervalos no se solapan y que el tamaño exacto es incierto. | MIA, sección 5 («Por qué el modelo da menos») y fila «Que el resultado dependa del método» de la tabla de riesgos (sección 8) | El documento daba las dos cifras, pero no explicaba la diferencia |
| EV-06, MIA-19 | Frase explícita: Random Forest empata en la práctica con Gradient Boosting (0,01 µg/m³ de diferencia) y se eligió por la regla fijada de antemano, el menor MAE en validación. | MIA, sección 5 | Para no presentar como clara una ventaja que no lo es |
| EV-01 | Fuente [5]: la página de la ciudad de Boston, que participa en Project Green Light. Recoge las cifras del programa: hasta un 30 % menos de paradas y hasta un 10 % menos de emisiones en los cruces. | MIA, sección 2 y «Fuentes» | Sustituye el `[PENDIENTE DE VERIFICAR]` |
| EV-01 | Fuente [6]: texto oficial del protocolo de NO₂ de Madrid (2015). Se ha leído y confirma tres cosas: los niveles de preaviso, aviso y alerta (200, 250 y 400 µg/m³ superados en varias estaciones de una zona durante horas seguidas); que los escenarios se aplican solo con previsión meteorológica desfavorable; y que esa previsión sale de las predicciones oficiales de AEMET. El documento aclara que en Madrid la previsión es meteorológica, no un modelo de IA del NO₂. | MIA, sección 2 (cadena de avisos) y «Fuentes» | Sustituye el `[PENDIENTE DE VERIFICAR]` |
| EV-03 | Indicador de horas de trabajo manual definido (qué se mide y cómo), con el valor «A medir en la puesta en marcha». No se da ninguna cifra porque no se ha medido. | MIA, sección 7 | Sustituye el `[A COMPLETAR POR EL EQUIPO]` |

| EV-03, SBD-02 | Ya no se afirma cada cuánto actualiza su web el Gobierno Vasco. Donde se hablaba de la frecuencia de la calidad del aire pone «datos horarios por estación, según los propios ficheros descargados». En el MIA sustituye al `[PENDIENTE DE VERIFICAR]`. En el informe SBD sustituye a «CSV anual; horaria», que se podía leer como una publicación anual. En el notebook sustituye a «Horaria». | MIA, sección 7 (indicador «Tiempo hasta tener el panel actualizado»); informe SBD, tabla de fuentes (sección 3); notebook, sección 3 (celda de texto, sin cambio de cifras) | Es lo único que se puede comprobar con los ficheros que tenemos |

Para que el informe SBD siga en 4 páginas de cuerpo con la frase nueva, se cambia el reparto de anchos de la tabla de fuentes y la figura 1 se imprime a 14 cm de ancho en vez de 15. No cambia ningún texto ni ninguna cifra del informe.

El chatbot se actualiza en la fase 6.

---

## Fase 6 · Limpieza y revisión final (puntos 3 a 6)

No se ha vuelto a ejecutar el notebook: `resultados/resultados.json` no cambia. Lo que cambia es que el README, la presentación y el chatbot dejan de llevar cifras antiguas y pasan a tomarlas de ese fichero.

### MIA-28
- **Comentario:** «Checklist de verificación» → «?».
- **Qué se ha cambiado:** no quedaba ninguna sección «Checklist de verificación» en los documentos; se quitaron en las fases 3 y 4. Se quitan las dos referencias a la rúbrica que quedaban: «(Rúbrica BDA)» en un título del organigrama y «requisito PIA» en un comentario de `docker-compose.yml`.
- **Dónde:** `docs/organigrama-datos.md` (sección «Evidencias visuales y capturas de pantalla»); `docker-compose.yml` (cabecera).
- **Por qué:** los documentos no deben hablar de la rúbrica ni del curso.

### EV-07 (README y presentación)
- **Comentario:** «verificar que las cifras de calidad y cobertura del informe coinciden con las obtenidas al ejecutar el código».
- **Qué se ha cambiado:**
  - README reescrito en versión breve: qué es, resultados, arquitectura, arranque paso a paso, estructura y autores. La tabla de resultados (P1-P5 y modelo de IA) tiene una frase «Qué significa» por pregunta y se ha rellenado desde `resultados.json` con un script, sin teclear cifras.
  - La carga del histórico en el bucket `aire` aparece como paso obligatorio del arranque, con el comando exacto (decisión 6 del equipo).
  - Se quitan del README el p-valor, la regresión −1,74, los aforos de San Mamés, el correo personal de la tabla de variables y la referencia al curso.
  - Presentación: se actualizan las cifras de las diapositivas 2, 3, 5, 6, 7 y 12 y las respuestas de reserva del asistente (ver tabla de abajo). Se quitan «2 km²» y «27 cámaras», que tampoco están en el informe ni en el MIA por no tener fuente verificada.
- **Dónde:** `README.md`; `presentacion/index.html`.
- **Por qué:** el README y la presentación tenían las cifras de antes de las fases 1-4.

### EV-06 (chatbot)
- **Comentario:** «Falta justificar en profundidad Gradient Boosting. La validación, la estimación de la incertidumbre y SHAP requieren explicación precisa. La comparación con DiD necesita desarrollar sus limitaciones.»
- **Qué se ha cambiado:**
  - El chatbot decía que el modelo elegido era Gradient Boosting, con −2,87 µg/m³ (−11,6 %), y que «ambos modelos convergen». Ahora dice lo mismo que el MIA: Random Forest, −0,49 µg/m³ (de −0,86 a −0,12), el placebo con ZBE ficticia y que el tamaño exacto depende del método.
  - `chatbot/main.py` ya no lleva ninguna cifra: lee `resultados/resultados.json` al arrancar y genera los textos con f-strings. Si el fichero no está, lo dice en vez de inventar cifras. `docker-compose.yml` monta `resultados/` en solo lectura en el contenedor.
  - Se elimina `chatbot/knowledge_base.json`: el código no lo usaba y solo tenía cifras antiguas (calma 28,10 → 24,35, ±0,24, benceno, aforos).
  - Se quita la «validación triple de placebos»: solo se citan la fecha falsa y el SO₂, que están hechos.
- **Dónde:** `chatbot/main.py` (bloques «Cifras del análisis y prompt de razonamiento» y «Fallback Local de Contingencia»); `chatbot/Dockerfile`; `chatbot/README.md`; `docker-compose.yml` (servicio `chatbot`).
- **Por qué:** el chatbot contradecía al MIA y al informe.

### EV-02 (presentación y chatbot)
- **Comentario:** «DiD no es IA. La automatización de tareas no es una técnica de IA.»
- **Qué se ha cambiado:** en la diapositiva 12 («La propuesta de IA»), diferencias en diferencias lleva la etiqueta «estadística, no IA» y el modelo elegido pasa a Random Forest. El chatbot y la respuesta de reserva de la presentación dicen que Node-RED es automatización, no IA.
- **Dónde:** `presentacion/index.html` (diapositiva 12 y `CONOCIMIENTO_FALLBACK`); `chatbot/main.py`.
- **Por qué:** la presentación seguía poniendo DiD y Gradient Boosting como dos modelos de IA.

### MIA-01 y MIA-04 (README y chatbot)
- **Comentarios:** cabecera del curso tachada · «ocho puntos del enunciado» → «??».
- **Qué se ha cambiado:** se quitan «Reto 0», «HERE WE GO» y «Centro de Formación Somorrostro» del README y del chatbot.
- **Dónde:** `README.md`; `chatbot/main.py`; `chatbot/README.md`.
- **Por qué:** son textos que ve el cliente.

### Cifras que cambian en el README, la presentación y el chatbot

| Cifra | Antes | Ahora (`resultados.json`) |
|---|---|---|
| NO₂ dentro después de la ZBE | 21,90 | 21,91 |
| Margen del efecto neto | ±0,24; IC −1,87 a −1,39 y «p < 0,001» | Intervalo del 95 %: de −2,38 a −0,94 |
| Efecto neto fuera de horario | −0,86 | −0,85 |
| Comprobación con el tiempo atmosférico | Regresión −1,74 | Efecto neto en calma −1,23 (de −2,05 a −0,42) |
| Calma dentro (chatbot) | 28,10 → 24,35 (−13,4 %) | Efecto neto en calma −1,23 |
| Modelo de IA | Gradient Boosting, −2,87 (−11,6 %) | Random Forest, −0,49 (de −0,86 a −0,12); MAE 8,14 frente a 10,50 sin IA |
| Horas por estación / filas | 41.700 / 332.776 | 41.615 / 332.619 |
| Caída bruta en la diapositiva 3 | −14,1 % dentro, −10,8 % fuera | −3,59 y −1,96 µg/m³ (el % de fuera no está en `resultados.json`) |
| Tráfico San Mamés | −10,1 % (2024) | Se quita: no entra en el análisis (decisión 16) |
| Cuarta prueba de la diapositiva 7 | Tráfico | Fase 2 frente a fase 1: −0,52 (de −1,72 a 0,74) |

### Estado de todas las correcciones

Están los 57 IDs de `CORRECCIONES.md`. 55 están resueltos; EV-11 y EV-12 siguen pendientes.

| ID | Estado | Fase |
|---|---|---|
| EV-01 | Resuelto | 4 |
| EV-02 | Resuelto | 4, 6 |
| EV-03 | Resuelto. El indicador de horas de trabajo manual está definido, pero sin cifra: «A medir en la puesta en marcha» | 4 |
| EV-04 | Resuelto. La causa de la bajada de Europa (−26,8 %) queda `[PENDIENTE DE VERIFICAR POR EL EQUIPO]` (decisión 5) | 4 |
| EV-05 | Resuelto | 4 |
| EV-06 | Resuelto | 4, 6 |
| EV-07 | Resuelto | 1, 2, 3, 6 |
| EV-08 | Resuelto | 1, 2 |
| EV-09 | Resuelto | 2 |
| EV-10 | Resuelto en la parte de crudo frente a limpio | 1 |
| **EV-11** | **Pendiente** (ver abajo) | 5, no hecha |
| **EV-12** | **Pendiente** (ver abajo) | 5, no hecha |
| SBD-01 | Resuelto | 3 |
| SBD-02 | Resuelto. La fuente oficial de los festivos queda `[PENDIENTE DE VERIFICAR]` | 2, 3, 4 |
| SBD-03 a SBD-10 | Resueltos | 1, 2, 3 |
| SBD-11 | Resuelto | 3 |
| SBD-12 a SBD-15 | Resueltos | 2, 3 |
| SBD-16 | Resuelto. El equipo ha confirmado que el reparto de la sección 8 del informe es el real (decisión 7) | 3, 6 |
| MIA-01 a MIA-27 | Resueltos | 2, 4 |
| MIA-28 | Resuelto | 4, 6 |
| MIA-29 | Resuelto | 4 |

### No resueltas y por qué
- **EV-11** («revisar», InfluxDB). Corresponde a la fase 5, que no se ha hecho. Sigue pendiente quitar el field string `fecha_original` de `aire_demo` (`nodered/flows.json` y organigrama) y comprobar que `docs/organigrama-datos.md` coincide 1:1 con lo que escriben `flows.json` y `carga_historica.py`. Lo único hecho es que el README ya pone la carga del bucket `aire` como paso obligatorio con su comando.
- **EV-12** («Falta comprobar alertas y permisos por organización, equipo y usuario»). También es de la fase 5. La alerta «> 40 µg/m³ límite EU» sigue evaluándose sobre valores horarios, aunque 40 es el límite de la media anual, y no existen `docs/alertas.md` ni `docs/permisos-grafana.md`. Por eso el README no describe las alertas.

### Ajustes antes del merge (revisión del equipo)

| ID | Qué se ha cambiado | Dónde | Por qué |
|---|---|---|---|
| MIA-29, EV-07 | Una frase del MIA mostraba el código en vez de las cifras: «entre {min(horas_200)} y {max(horas_200)}». Faltaba la `f` de un f-string. Ahora dice «entre 2022 y 2026». Se ha revisado el resto de `generar_mia.py` y `generar_informe.py` y no hay más textos con llaves sin evaluar. Se regeneran el `.md`, el `.docx` y el `.pdf` del MIA (sigue en 7 páginas); el texto del PDF del MIA y el del informe SBD no tienen ninguna llave. | `docs/generar_mia.py` (apartado 2, cadena de avisos); `docs/propuesta-modelo-ia.md`, `docs/MIA_Haizen_Lab.docx` y `.pdf` | El documento impreso enseñaba código al cliente |
| EV-07 | Se quita la diapositiva del vídeo `veredicto.mp4`, que tenía cifras antiguas. La presentación pasa de 14 a 13 diapositivas; Grafana pasa a la diapositiva 9. | `presentacion/index.html`; `presentacion/README.md` | El vídeo no salía de `resultados.json` |
| EV-07 | La gráfica de la diapositiva 6 era un dibujo con valores fijos. Se sustituye por la figura de P1 del notebook (`docs/img/p1_evolucion_mensual_no2.png`), copiada en `presentacion/assets/` porque el servidor de la presentación solo publica esa carpeta. Si se vuelve a ejecutar el notebook, hay que volver a copiarla. | `presentacion/index.html` (diapositiva 6); `presentacion/assets/p1_evolucion_mensual_no2.png` | Una sola fuente para la gráfica |
| — | Se quita el recuento de commits de la diapositiva «Cómo trabajamos». | `presentacion/index.html` | Era una cifra que cambia con cada commit |
| — | «5 contenedores» pasa a 7: `docker compose up -d --build` levanta 6 contenedores permanentes y `influxdb_setup`, que crea los buckets y los tokens y se cierra. | `presentacion/index.html` (diapositivas 1 y 8) | No coincidía con `docker-compose.yml` |
| SBD-16 | El equipo confirma que el reparto de tareas de la sección 8 del informe es el real. Pasa a resuelto. | Este fichero | Confirmación del equipo |

### Pendiente en la presentación
- La diapositiva 9 dice «NO₂ por encima de 25, 40 y 200 µg/m³»: se cambia en la fase 5, cuando se corrijan las alertas.
