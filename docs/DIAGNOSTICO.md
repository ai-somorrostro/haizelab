# Diagnóstico del repositorio (fase 0)

Fecha: 20/10/2026 · Rama: `fix/diagnostico` · Base: `develop` en `87085d8`.

Este documento no cambia código, datos ni documentos. Solo describe lo que hay y propone qué hacer.

**Cómo se ha comprobado.** Se ha copiado el repositorio a una carpeta temporal y se han descargado de nuevo los datos crudos de Open Data Euskadi y Open-Meteo. Después se ha ejecutado `ingesta/descargar_y_limpiar.py` y el notebook completo con `nbclient`. Todas las cifras de este documento salen de esa ejecución o de pequeños scripts de comprobación sobre sus ficheros. Ninguna está escrita a mano.

---

## Resumen en 8 puntos

1. **Las cifras del notebook guardado se reproducen.** Al ejecutarlo de nuevo salen las mismas: DiD −1,63, 25,50 → 21,90, calma 28,10 → 25,47, regresión −1,74, SO₂ +0,33, etc. Solo cambia el Gradient Boosting: −2,87 pasa a −2,85, y R² de 0,472 a 0,476.
2. **Desde un clon limpio, el pipeline A no funciona.** El zip oficial trae dos carpetas con ficheros del mismo nombre (`datos_horarios/` y `datos_diarios/`). El script guarda solo el nombre del fichero, así que los diarios pisan a los horarios y la limpieza termina con `ValueError: No objects to concatenate`.
3. **La diferencia entre A y B tiene tres causas, todas medidas** (apartado 1):
   - B mezcla los ficheros diarios con los horarios.
   - B y A agregan de forma distinta.
   - Usan una fuente de viento distinta.
4. **El split de validación del Gradient Boosting no es temporal.** La validación es un año de una sola estación, y el 99,4 % de sus horas también está en el entrenamiento (apartado 2).
5. **Pipeline A tiene tres errores más que cambian cifras:**
   - La meteorología está en hora GMT y se cruza como si fuera hora local.
   - En Mazarredo, la columna «NO» es en realidad el benceno.
   - PM2,5 sale vacía en todas las estaciones.
6. **Las cifras por estación de los informes no salen del código, y algunas son muy distintas.** Europa, que es control, baja un **−26,8 %**. Más que las dos estaciones de dentro (−15,0 % y −12,7 %).
7. **Fase 2.** El DiD de la fase 2 frente a la fase 1 es **−0,53 µg/m³**. Hay una ganancia adicional, pero menor que la de la fase 1. Ni «ganancia progresiva continuada» ni «rendimientos decrecientes» describen bien el dato sin matices.
8. **Grafana y la carga histórica usan los datos del pipeline B**, no los del A (apartado 6).

---

## 1. Diferencias entre el pipeline A y el pipeline B

| | **A**: `ingesta/` + `data/` + notebook | **B**: `scripts/01..06` + `datos/` + `salida/` |
|---|---|---|
| NO₂ en el fichero limpio | 333.376 filas estación-hora (notebook guardado) | 333.418 filas (`no2_horario_limpio.zip`) |
| Viento | Open-Meteo (modelo, media 2,46 m/s) | Estación de Monte Banderas (medido, media 4,21 m/s) |
| Hora | Aire en hora local, meteo en GMT (ver 1.2) | Todo en GMT |
| Cifras | 25,50 → 21,90 · DiD **−1,63** · calma 28,10 → 25,47 | 25,63 → 21,89 · DiD **−1,81** · calma 32,32 → 27,41 |

### 1.1 Causa principal de B: mezcla ficheros diarios con horarios
- `scripts/01_extraer_calidad_aire.py:182` lee **todos** los CSV de `datos/crudo/` (`glob("**/*")`), incluidos los de `datos_diarios/`.
- Un fichero diario solo tiene fecha, sin hora, así que cada media diaria se guarda como si fuera la medición de las 00:00. Después, `drop_duplicates(["estacion","ts"])` (línea 207) se queda con una de las dos, y a menudo es la diaria.
- **Comprobación:** de las 13.410 medianoches de B que se pueden comparar, el **99,74 %** coinciden exactamente con la media diaria oficial. En total hay 12.843 valores de NO₂ distintos entre A y B, y casi todos son de las 00:00.
- Esto también explica las **42 filas de más** de B (333.418 − 333.376):
  - 8 filas del 01/01/2022 00:00 (la media diaria del 1 de enero; esa hora no existe en el fichero horario);
  - 32 horas del cambio de hora de octubre que A borra (ver 1.5);
  - 2 días más en Arraiz, que tienen media diaria pero no tienen datos horarios.

### 1.2 Zona horaria
- **A mezcla horas.** El aire se convierte de GMT a hora de Madrid (`ingesta/descargar_y_limpiar.py:458-459`). En cambio, la meteo de Open-Meteo se pide sin el parámetro `timezone`, que por defecto devuelve GMT (`:218-230`), y se guarda directamente como `ts_local` (`:563`).
  - Prueba: `data/clean/meteorologia_limpia.csv` contiene `2022-03-27 02:00`, una hora que no existe en hora local, y siempre tiene 24 filas por día.
  - Consecuencia: cada medición de NO₂ se cruza con el tiempo de **1 h más tarde en invierno y 2 h más tarde en verano**.
- **B** usa GMT en todo. Es coherente entre aire y meteo, pero las fechas de corte de las fases y el horario de la ZBE quedan desplazados 1-2 h.

### 1.3 Hora 24:00
- A (`:446-455`) y B (`01_…py:104-136`) la convierten igual: 00:00 del día siguiente. **No es causa de diferencias por sí sola.** El problema de B es que a esa misma hora le llega también la media diaria (1.1).
- Con los datos actuales hay 14.020 filas con hora 24:00 (13.892 en el notebook guardado, porque entonces los datos llegaban hasta el 05/10/2026).

### 1.4 Redondeo y negativos
- **Redondeo: no es causa.** El NO₂ crudo viene en números enteros (el 100 % de los valores, tanto en A como en B). Que B lo guarde «en enteros» es simplemente cómo viene el dato.
- **Negativos: no es causa.** Ambos pipelines convierten NO₂ < 0 en NaN, y son 71 valores en total. Es el **0,02 %** de las filas brutas, no el «0,04 %» de los informes.

### 1.5 Número de filas en A
- 333.408 filas brutas (notebook guardado) → 333.376 tras quitar 32 filas → 332.776 tras el JOIN con la meteo.
- **Las 32 filas quitadas** son lecturas reales del cambio de hora de octubre (4 por estación). Al pasar a hora local sin zona horaria, la hora 02:00 aparece dos veces, y `drop_duplicates(subset=["ts_local"])` (`:515`) borra una de las dos.
- **Las 600 filas que se pierden en el JOIN** son 8 estaciones × 75 h. La meteo se pide solo hasta `2026-10-01` (`:222`), pero el aire llegaba hasta el 05/10/2026. Con los datos de hoy (aire hasta el 21/10/2026) se pierden 3.672 filas y la retención baja del 99,82 % al 98,91 %. El resultado final sigue siendo de 332.776 filas, porque la fecha de corte la marca la meteo.
- **Las «5 horas faltantes» por estación** de `data/clean/inventario_calidad.csv` no son horas sin dato. Son las 5 horas que no existen en hora local por el cambio de hora de marzo (2022-2026). En Arraiz las horas faltantes reales son 288; el inventario dice 293 y la celda 9 del notebook dice «288».

### 1.6 Cuánto pesa cada causa (medido paso a paso)

Se parte de B tal cual y se cambia una sola cosa en cada paso (mismo periodo de datos):

| Paso | Dentro (antes → después) | Fuera | DiD | Calma (antes → fase 1) |
|---|---|---|---|---|
| 0. B tal cual | 25,63 → 21,89 | 18,25 → 16,33 | −1,81 | 32,33 → 27,37 |
| 1. Sin medias diarias (datos de A en GMT) | 25,50 → 21,78 | 18,19 → 16,26 | −1,79 | 32,32 → 27,42 |
| 2. + agregación de A (todas las filas estación-hora juntas) | 25,49 → 21,91 | 18,25 → 16,30 | **−1,63** | 32,24 → 27,65 |
| 3. + hora local | 25,50 → 21,91 | 18,25 → 16,29 | −1,63 | 32,24 → 27,66 |
| 4. + viento de Open-Meteo (= A actual) | 25,50 → 21,90 | 18,25 → 16,29 | −1,63 | **28,10 → 25,45** |
| 5. A con Open-Meteo bien pasada a hora local | 25,50 → 21,90 | 18,25 → 16,29 | −1,63 | 29,34 → 26,62 |

Qué significa:
- **El nivel 25,63 frente a 25,50** se debe a las medias diarias mezcladas (paso 1).
- **El DiD −1,81 frente a −1,63** se debe sobre todo a la forma de agregar (paso 2):
  - B hace primero la media de las estaciones de cada zona en cada hora y luego la media de esas horas (`04_unificar_datos.py:62-64, 94-105`). Así, una hora en la que solo funciona una estación pesa lo mismo que una en la que funcionan todas.
  - A hace la media de todas las filas estación-hora juntas.
- **La calma 32,32 frente a 28,10** se debe a la fuente de viento (paso 4). Banderas es una estación en un monte y mide mucho más viento que el modelo de Open-Meteo a nivel de calle, así que «menos de 2 m/s» selecciona horas distintas.
- Si se corrige la hora de la meteo en A (paso 5), la calma pasa a 29,34 → 26,62. **Esta corrección cambia también la regresión (−1,74) y el Gradient Boosting.**
- (En el paso 4 la calma da 25,45 y no 25,47 porque aquí se usa el mismo periodo que B, hasta el 05/10/2026.)

### 1.7 Otros errores de A que cambian cifras
- **Mapeo de columnas** (`:470-486`). La búsqueda es por subcadena:
  - **«NO»** encuentra primero la columna «Benceno», porque «bence**no**» contiene «no». En Mazarredo, `no` = `benceno` en el 92,7 % de las filas. En las otras estaciones sí es el NO. Por tanto, la cifra «NO −39 %» de P4 está mal.
  - **«PM2,5»**: las variantes tienen espacios, pero el nombre de columna se compara sin espacios, así que nunca coincide. `pm25` sale vacía al 100 % en todas las estaciones.
- **Cobertura por contaminante:**
  - el benceno solo existe en Mazarredo;
  - el CO solo en Mazarredo, Díaz de Haro, Barakaldo y Erandio.

  Por eso el DiD del benceno es NaN, y el del CO compara grupos de estaciones distintos.

---

## 2. ¿Es temporal el split `iloc[:split_idx]` del Gradient Boosting?

**No.** Se ha comprobado con el dataframe real de la celda 26.

- `df_dentro` mantiene el orden en que se concatenaron las estaciones en `limpiar_calidad_aire()`: primero **todo Mazarredo** (2022→2026) y después **todo Mª Díaz de Haro**. Los `merge` posteriores conservan ese orden.
- `X_train` (anterior a la ZBE) tiene 41.787 filas y **no está ordenado por fecha** (`is_monotonic_increasing = False`). `split_idx` = 33.429.

| Bloque | Filas | Contenido real |
|---|---|---|
| Ajuste (`iloc[:33429]`) | 33.429 | Mazarredo **completo** (01/01/2022 → 14/06/2024) + Díaz de Haro (01/01/2022 → 16/06/2023) |
| Validación (`iloc[33429:]`) | 8.358 | **Solo Díaz de Haro**, 16/06/2023 → 14/06/2024 |

Consecuencias:
- **La validación no prueba el futuro.** El modelo ya ha visto esas mismas horas en Mazarredo durante el entrenamiento: el **99,4 %** de las horas de validación también están en el ajuste.
- **Las mismas horas tienen las mismas variables.** El modelo no recibe la estación como variable, así que una hora en Mazarredo y la misma hora en Díaz de Haro tienen exactamente los mismos valores de meteo y calendario. Por eso el MAE (7,78), el RMSE (10,58) y el R² (0,476) no miden la capacidad de predecir hacia adelante.
- **La validación no es la que dicen los documentos.** Es un año de una sola estación, no «los últimos 6 meses previos» que dicen el MIA y `propuesta-modelo-ia.md:126`.
- **Sí es correcto el modelo final.** Se entrena solo con datos anteriores al 15/06/2024. El error está solo en la validación.

---

## 3. Cifras de los documentos que no coinciden con el notebook

Referencia: la salida del notebook ejecutado de nuevo. Las cifras que coinciden no se listan. Por ejemplo: 25,50 / 21,90 / 18,25 / 16,29, −1,63, −6,4 %, −1,74, +0,33, −2,93 / −0,86 (como efectos netos), calma 28,10 / 25,47 / 23,56 y aforos de San Mamés.

«No sale» quiere decir que el notebook no imprime esa cifra. En esos casos, entre paréntesis va el valor real calculado en este diagnóstico con los datos del notebook.

### `README.md`
| Línea | Dice | Real |
|---|---|---|
| 33 | IC 95 % −1,87 a −1,39, p < 0,001 | Sale del OLS horario con HC1. Las horas consecutivas están correlacionadas, así que el intervalo sale demasiado estrecho. Hay que recalcularlo (fase 2) |
| 55 | GBM con «velocidad y ángulo de viento» | `features_ml` no incluye la dirección del viento |
| 55 | GBM −2,87 (−11,6 %) | −2,85 (−11,5 %) al ejecutar de nuevo; y la validación no es válida (apartado 2) |
| 290-291 | Aviso > 25 (OMS) y superación > 40 (límite anual UE) | 25 es la guía **diaria** de la OMS y 40 es una media **anual**, pero las alertas se evalúan sobre medias de 15 min / horarias |

### `docs/informe-cliente-sbd.md`
| Línea | Dice | Real |
|---|---|---|
| 20 | «27 cámaras» | Sin fuente en el repo. `[PENDIENTE DE VERIFICAR]` |
| 62 | negativos 0,04 % | 0,02 % (71 de 336.480) |
| 76 | nulos residuales < 1,2 % | El NO₂ tiene dato en el 96,74 % de las filas, es decir, un 3,26 % nulo. Díaz de Haro solo tiene el 91,99 % |
| 86, 93 | −14,08 % | −14,09 % |
| 88 | Arraiz post 8,16 (−6,53 %) | No sale (8,31; −4,80 %) |
| 89 | Mazarredo 26,71 → 22,86 (−14,41 %) | No sale (**22,44 → 19,07; −15,03 %**) |
| 90 | Díaz de Haro 24,28 → 20,95 (−13,71 %) | No sale (**28,67 → 25,03; −12,71 %**). Las dos estaciones de dentro están **intercambiadas** |
| 91 | Europa 21,30 → 18,35 (−13,85 %) | No sale (**20,92 → 15,32; −26,79 %**) |
| 102 | Datos hasta febrero de 2026 | Hasta el 01/10/2026 |
| 104 | Picos > 34 y máximo interior < 28 | No salen del notebook |
| 114 | Calma post global 24,35 (−13,4 %) | El notebook imprime 24,52 (−12,8 %), que es la media simple de fase 1 y fase 2. La media de todas las horas posteriores es 24,32 (−13,4 %). Hay que elegir una sola definición |
| 119 | «−5.075 veh/día laborable» | La IMD es una media de **todos** los días, no solo de los laborables |
| 127 | Menos horas por encima de la guía de la OMS | No se calcula |
| 128 | «Rendimientos decrecientes» | Contradice la celda 34 del notebook. Ver el apartado 4 (SBD-15) |

### `docs/Informe_Ejecutivo_ZBE_Bilbao_HaizeLab.docx` / `.pdf`
| Sección | Dice | Real |
|---|---|---|
| Portada y cabecera de cada página | Referencias al curso, módulo y reto | El PDF tiene portada + 4 páginas: cumple el límite. Sobran las referencias (regla de documentos de cliente) |
| §2 | negativos 0,04 % | 0,02 % |
| §2 | «completitud temporal superior al 98,8 %» | No sale de ningún cálculo (NO₂ con dato: 96,74 %; retención del JOIN: 99,82 %) |
| §4 tabla | −14,08 % | −14,09 % |
| §4 tabla | Mazarredo 26,71 / 22,86; Díaz de Haro 24,28 / 20,95 | 22,44 / 19,07 y 28,67 / 25,03 |
| §4 tabla | Europa 20,10 / 17,55 (−12,69 %) | 20,92 / 15,32 (−26,79 %). Además, el `.md` dice 21,30 / 18,35 |
| §4 tabla | Barakaldo / Erandio / Basauri 17,63 / 15,87 | 19,63 / 18,58 |
| §4 tabla | Castrejana 16,40 / 14,92 (−9,02 %) | 11,67 / 10,44 (−10,60 %) |
| §4 tabla | Arraiz 8,73 / 8,16 (−6,53 %) | 8,73 / 8,31 (−4,80 %) |
| §5.1 | «el NO₂ **cayó** −2,93 … 3,4 veces» | −2,93 y −0,86 son efectos **netos** (DiD), no caídas. Las caídas son −4,65 y −2,98, y su cociente es **1,6**. El 3,4 sale de dividir los dos efectos netos (−2,93 / −0,86) |
| §5.2 | SO₂ «p > 0,40» | No se calcula en ningún sitio |
| §6 | «p < 0,001» | Ver la línea 33 del README |
| §6 figura | Panel oscuro de `salida/dashboard_decision_zbe.png` (pipeline B) con el texto fijo «−7,1 % (−1,8 µg/m³)» (`scripts/06_visualizar_decision.py:188`) | DiD −1,63 (−6,4 %) |
| §7 | Calma −9,4 % / −16,2 % | Coincide con el notebook, pero cambiará al corregir la hora de la meteo (1.6) |

### `docs/MIA_Haizen_Lab.docx` / `.pdf` y `docs/propuesta-modelo-ia.md`
| Dónde | Dice | Real en el notebook |
|---|---|---|
| MIA §1, `.md:23` | «27 cámaras» | `[PENDIENTE DE VERIFICAR]` |
| `.md:113` | viento en km/h | m/s (Open-Meteo lo da en km/h y se divide entre 3,6; `descargar_y_limpiar.py:575-576`) |
| MIA §5, `.md:113` | Dirección del viento y marca de pandemia como variables | No están en `features_ml` |
| MIA §5 | «NO₂ esperado por estación» | El modelo no recibe la estación como variable |
| MIA §5 | Efecto «con su intervalo» | El GBM no calcula ningún intervalo |
| MIA §5, `.md:126` | Validación con los últimos 6 meses | Un año de una sola estación, con fuga (apartado 2) |
| MIA §5, `.md:127-131, 161, 176, 200` | Tres placebos (SO₂, estaciones fuera, fecha falsa) | Solo existe el de SO₂ |
| MIA §2/§5/§8, `.md:99, 111, 160` | SHAP | No está implementado |
| MIA §1 | «Abando» / notebook celda 37: «Abando e Indautxu» | Inconsistente. `[PENDIENTE DE VERIFICAR]` el perímetro oficial |

### `presentacion/index.html`
| Dice | Real |
|---|---|
| ±0,24 | Intervalo del OLS horario con HC1, demasiado estrecho (ver README:33) |
| «41.700» horas por estación | 41.708 en el notebook guardado; con los datos de hoy son 42.092 antes del JOIN |
| −2,93 / −0,86 | Correctos y bien descritos como «netos» |

El resto de las cifras coincide.

### `chatbot/knowledge_base.json`
| Clave / texto | Dice | Real |
|---|---|---|
| `no2_calma_post_ug`, `caida_calma_pct` | 24,35 / −13,4 | El notebook imprime 24,52 / −12,8 (ver la línea 114 del informe) |
| `margen_error_ic95` | 0,24 | Igual que en la presentación |
| `benceno_dentro_var_pct` | 13,0 | 13,24 (y solo hay benceno en Mazarredo) |
| `caida_bruta_dentro_ug` | −3,6 | −3,59 |
| `superficie_zbe_km2` | 2,1 | Los informes dicen 2. `[PENDIENTE DE VERIFICAR]` |
| `datos_sintesis` (líneas 36-98) | 25,63 / 21,89 / −14,57; 18,25 / 16,33 / −10,54; calma 32,32 / 27,41 / −15,21 y 26,78 / −17,17 | **Cifras del pipeline B** mezcladas con el −1,63 / −6,4 de A |

### Textos fijos del propio notebook que no cuadran con su salida
| Celda | Dice | Salida real |
|---|---|---|
| 0 | Efecto «entre −1,5 y −2,1 µg/m³ (−6 % a −8 %)» | El GBM da −2,85 (−11,5 %) |
| 9 | «Monte Arraiz: 288 horas faltantes» | El inventario dice 293 (y 5 de ellas son el artefacto del cambio de hora) |
| 21 | −15,4 % / −13,9 %; «en control, prácticamente idéntico» | −15,54 / −12,99; en control, −8,19 / −12,73 |
| 23 | Correlación viento −0,46, temperatura −0,31 | −0,22 y −0,22. Además, se guarda como `g7_…png` aunque es la «Gráfica 5» |
| 30 | «NO, NOx, NO₂, CO caen −14 % a −39 %» | CO −4,89 %; el NO de Mazarredo es en realidad benceno; el benceno **sube** +13,24 % |
| 31 | Interiores −14 / −15 %; Europa −13 %, Erandio −12 %, Basauri −11 % | Fase 1 frente a antes: Mazarredo −10,0 %, Díaz de Haro −7,6 %, **Europa −26,7 %**, Erandio −15,2 %, **Basauri +14,4 %**, Barakaldo +6,3 % |
| 34, 37 | «ganancia progresiva continuada», «3,4 veces», «~1,6 a 2,0» | Ver SBD-12 y SBD-15 |

---

## 4. Cada corrección: dónde está y qué se propone

Abreviaturas:
- **Inf.** = `docs/Informe_Ejecutivo_ZBE_Bilbao_HaizeLab.docx` y su espejo `docs/informe-cliente-sbd.md`.
- **MIA** = `docs/MIA_Haizen_Lab.docx` y su espejo `docs/propuesta-modelo-ia.md`.
- **NB** = `notebooks/zbe_bilbao.ipynb`.

### Hoja de evaluación
| ID | Dónde | Propuesta |
|---|---|---|
| EV-01 | MIA §2, tabla de aplicaciones | Dejar solo aplicaciones que encajen con el caso. Para los avisos, explicar la cadena completa predicción → umbral → aviso. Casos reales verificados o `[PENDIENTE DE VERIFICAR]` (fase 4). |
| EV-02 | MIA §3 (técnicas); se habla de contrafactual en §1 sin definirlo | Definir contrafactual con un ejemplo, sacar DiD y la automatización de la lista de técnicas de IA, y relacionar el §2 con el §3. |
| EV-03 | MIA §7, impacto | Indicadores medibles con su valor: horas de trabajo manual, tiempo hasta tener el panel actualizado, MAE en µg/m³, horas al año por encima de 200 µg/m³. |
| EV-04 | MIA §1, requisitos | Explicar que predecir el NO₂ no prueba la causa. Comparar dentro frente a fuera, nombrar las estaciones de control y explicar cómo se eligen. **Ojo con Europa (−26,8 %)**: ver el apartado 6. |
| EV-05 | MIA §3-§5 | Explicar en llano cómo funciona cada modelo y qué alcance tienen sus resultados. Quitar lo que no se pueda defender. |
| EV-06 | MIA §5, NB celda 26 | Validación temporal real, comparación con 3 modelos, bootstrap por semanas, placebo de fecha falsa y `permutation_importance` en lugar de SHAP (fase 4). |
| EV-07 | Inf. §2, NB celdas 7-9 | Sección «crudo frente a limpio» con filas, motivos y medias por estación. Completitud calculada. Arreglar el bug del zip (1.1, punto 2 del resumen). |
| EV-08 | NB celda 12 | Filas antes y después de cada JOIN, duplicados = 0 y por qué se cruza por hora local (después de corregir la hora de la meteo, 1.2). |
| EV-09 | Inf. y NB enteros | Reducir el notebook a P1-P5 con una gráfica y una frase «Qué significa» por pregunta. Todas las cifras en `resultados.json` (fase 2). |
| EV-10 | `ingesta/descargar_y_limpiar.py` | Corregir los errores de 1.2, 1.5 y 1.7 (meteo en GMT, borrado del cambio de hora, mapeo NO/benceno y PM2,5) y documentar cada diferencia entre crudo y limpio. |
| EV-11 | `nodered/flows.json:299` (`fecha_original` como field de texto); bucket `aire` | Quitar el field. La carga histórica debe leer los datos de A (apartado 6). |
| EV-12 | `grafana/provisioning/alerting/alerting.yaml:32-185` | Horaria > 200; aviso con media móvil de 24 h. Renombrar la regla de 40. Documentar alertas y permisos (fase 5). |

### Informe SBD
| ID | Dónde | Propuesta |
|---|---|---|
| SBD-01 | Inf. §1 «dictaminar… renovación vegetativa del parque» | «la sustitución normal de coches viejos por otros más limpios, que ocurre con o sin ZBE»; quitar «dictaminar». |
| SBD-02 | Inf. §2, lista de fuentes | Tabla por fuente: quién la publica, formato, periodo, frecuencia, variables y para qué pregunta se usa. |
| SBD-03 | Inf. §2 «se convirtieron a NaN» | NaN = celda vacía. Poner 0 bajaría la media falsamente; borrar la fila perdería el resto de contaminantes de esa hora. |
| SBD-04 | Inf. §2 «se armonizaron las unidades» | Decirlo exacto: viento de km/h a m/s (÷ 3,6) y hora GMT a hora de Madrid. **Corregir antes la meteo, que hoy sigue en GMT** (1.2). |
| SBD-05 | Inf. §2 «98,8 %» | Quitar. Poner la completitud calculada (horas con dato / horas esperadas) por estación; hoy el NO₂ tiene dato en el 96,74 % de las filas. |
| SBD-06 | Inf. §3, prioridades P1-P5 | Criterio: cuánto cambia cada respuesta la decisión de ampliar, mantener o ajustar. Una frase por nivel. |
| SBD-07 | Inf. §4 «eludir el sesgo» | «Comparar solo antes y después mezcla el efecto de la ZBE con lo que habría bajado igualmente». |
| SBD-08 | Inf. §4 «cuenca y flota» | «misma meteorología de la comarca y mismo tipo de coches». |
| SBD-09 | Inf. §4, columna «Rol» | Definir tratamiento, control y fondo, y por qué Arraiz (fondo) no entra en el control. |
| SBD-10 | Inf. §4, columnas de la tabla | Definir cada columna con fechas exactas. Quitar «Papel». **Regenerar todas las filas desde el código** (las de estación son erróneas, apartado 3). |
| SBD-11 | Europa 20,10 / 17,55 (docx) frente a 21,30 / 18,35 (md) | Ninguna de las dos es correcta (20,92 → 15,32). Leerlas de `resultados.json`. |
| SBD-12 | Inf. §5 «cayó −2,93 … 3,4 veces», «p > 0,40», «corroborando la causalidad» | −2,93 es un efecto neto, no una caída. Quitar el p del SO₂ o calcularlo. Quitar «corroborando». |
| SBD-13 | Inf. §6, panel oscuro (pipeline B, «−7,1 %») | Sustituirlo por 1-2 gráficas del notebook con fondo claro. |
| SBD-14 | Inf. §6 «p < 0,001», «desmontando titulares» | Intervalo bootstrap por semanas explicado en llano; tono neutro. |
| SBD-15 | Inf. §8 «rendimientos decrecientes» frente a NB celda 34 «ganancia progresiva continuada» | Con control: fase 1 frente a antes −1,29; fase 2 frente a fase 1 **−0,53** (adicional, pero menor). Una sola frase coherente con esto (cifra definitiva en la fase 2). |
| SBD-16 | Inf. §9, tabla de reparto | `[A COMPLETAR POR EL EQUIPO]`: no se puede deducir del repo. |

### MIA
| ID | Dónde | Propuesta |
|---|---|---|
| MIA-01 | Cabecera «Modelos de IA (5071)…», «RETO 0» | Quitarla. Dejar título, equipo, cliente y fecha. |
| MIA-02 | Subtítulo | «Un modelo para saber si la ZBE funciona». |
| MIA-03 | «separar… del centro… todo lo demás» | Definir «centro» = perímetro ZBE y enumerar qué es «todo lo demás» (tiempo, coches más limpios, tendencia). |
| MIA-04 | «ocho puntos del enunciado» | Quitar. |
| MIA-05 | Objetivo (resaltado) | Abrir con la decisión de ampliar, mantener o ajustar, y cerrar cada sección conectando con ella. |
| MIA-06 | §1 «El NO₂ también…» | Por qué NO₂ (tráfico diésel, límite legal) y qué pasa con NOx, PM10 y PM2,5 (esta última hoy vacía por un error, 1.7). |
| MIA-07 | §1 «tendencia que ya traía la ciudad» | Medias anuales: dentro 25,85 (2022) → 25,95 (2023); fuera 19,09 → 17,95. |
| MIA-08 | §1 «contrafactual» | «Lo que habría pasado sin ZBE; no se puede medir, hay que estimarlo». Con un ejemplo con nuestras cifras. |
| MIA-09 | Tabla, «Entradas y salida» | Una línea: entra meteo + calendario + estación; sale el NO₂ esperado. |
| MIA-10 | Tabla, «Interpretabilidad» | Indicador: MAE en validación temporal frente a un modelo base (media por hora y mes). |
| MIA-11 | Tabla, «Validación temporal» | Entrenar 2022-2023 y validar del 01/01/2024 al 14/06/2024, ordenado por fecha. Explicar por qué no aleatoria. Hoy no lo es (apartado 2). |
| MIA-12 | Tabla, «Ruido meteorológico» | Ruido = variación que el modelo no explica. Importa porque el efecto buscado (≈ 1,6 µg/m³) es pequeño frente al error (MAE ≈ 7,8). |
| MIA-13 | §2, principios y aplicaciones | Cada principio con una frase sobre nuestro caso. |
| MIA-14 | §2 «sobreajuste» | Tabla de error en entrenamiento frente a validación, con cifras (fase 4). |
| MIA-15 | §2, tabla de 5 familias | Aplicar EV-01/EV-02: la automatización no es IA; relacionar cada familia con una aplicación. |
| MIA-16 | §3, DiD como técnica de IA | Sacarlo de la lista de IA; dejarlo como método estadístico de comprobación. |
| MIA-17 | §3, SARIMAX «poco flexibles» | Argumento concreto: modela una sola serie; añadir varias estaciones y meteo con relaciones no lineales es difícil. |
| MIA-18 | §3, LSTM «muchos datos, cuesta explicarla» | Argumento concreto: ≈ 42.000 horas por estación y 2 estaciones de dentro; hay que entrenarla en CPU; es difícil de explicar a un concejal. |
| MIA-19 | §4, sin modelos para comparar | Regresión lineal, Random Forest y GBM con las mismas variables y métricas. |
| MIA-20 | §5 «no lineal» | Ejemplo con nuestros datos (dentro, antes de la ZBE): hasta 3 m/s de viento el NO₂ medio apenas cambia (26,6-28,8 µg/m³), y a partir de ahí baja rápido (9,6 µg/m³ con más de 8 m/s). No es una línea recta. Cifras definitivas en la fase 4. |
| MIA-21 | §5 «efecto agregado ¿cómo?» | Fórmula en llano: (observado − predicho) dentro − (observado − predicho) fuera, por semanas, con bootstrap. |
| MIA-22 | §5 «Por qué DiD no es el modelo principal» | Quitarlo o dejarlo en 3 líneas llanas. |
| MIA-23 | §5 «Tres placebos» | Solo los que estén hechos: SO₂ (hoy) y fecha falsa (fase 4), con su resultado. |
| MIA-24 | §5 «Contraste con DiD» | Explicar para qué sirve (dos métodos distintos, misma pregunta) o quitarlo. |
| MIA-25 | §8, título | «Ventajas, limitaciones y riesgos de la solución propuesta». |
| MIA-26 | §8 «Separa el efecto…» | Explicar cómo (comparación con el control + predicción meteo) o quitarlo. |
| MIA-27 | §8, riesgo de atribuir mal | Prueba concreta y su cifra: placebo de fecha falsa, SO₂ e intervalo. |
| MIA-28 | §8, «Checklist de verificación» | Eliminarla. |
| MIA-29 | Documento entero | Reescribirlo más corto. Cada término definido o quitado. |

---

## 5. ¿Se puede ejecutar el notebook con lo que hay en local?

**Hoy no.** En el ordenador no hay `data/raw/` ni `datos/crudo/` (los dos están en `.gitignore`). La celda 4 del notebook descarga los datos, pero:

1. **Bug del zip** (punto 2 del resumen). Los CSV diarios pisan a los horarios y la celda 7 falla con `ValueError: No objects to concatenate`. Esto pasa siempre que no exista `datos/crudo/`.
2. **Errores 503 de Open Data Euskadi.** Son pasajeros (fallaron 2024 y 2026 y funcionaron al reintentar). El script no reintenta.

**Comando de descarga** (PowerShell, desde la raíz del repo):

```powershell
pip install -r requirements.txt
python ingesta/descargar_y_limpiar.py
```

Para que funcione, antes hay que corregir una línea en `descargar_calidad_aire()` (`ingesta/descargar_y_limpiar.py:190-194`): copiar solo los miembros del zip cuya carpeta sea `datos_horarios`. Esto queda para la fase 1, porque esta fase no toca código.

Con esa corrección aplicada en una copia temporal, **el notebook se ejecuta de principio a fin sin errores (≈ 30 s)** y reproduce las cifras guardadas (Resumen, punto 1).

Avisos:
- Ejecutarlo **sobrescribe ficheros versionados**: `data/clean/meteorologia_limpia.csv`, `inventario_calidad.csv`, `calendario_zbe_limpio.csv` y las `docs/img/*.png`.
- Con los datos de hoy, **el inventario cambia** (42.092 horas por estación en lugar de 41.708), porque Open Data ya tiene datos hasta el 20/10/2026.
- Las cifras del análisis no cambian, porque la meteo corta el 01/10/2026. Pero si alguien cambia esa fecha, cambiarán todas.

---

## 6. Riesgos y decisiones para el equipo

1. **Rama `fix/pipeline-unico` ya existe en local** con un commit de hoy (`b0c9404`, «pipeline único, comprobación crudo vs limpio, completitud y resultados.json») hecho **antes** de este diagnóstico, y sin subir. La fase 1 pide crear esa rama. Hay que decidir si se descarta y se empieza de nuevo desde `develop`, o si se revisa y se aprovecha. Recomendación: revisarla, pero no reutilizarla sin aplicar lo de este diagnóstico.
2. **Fecha de corte fija del estudio.** Hoy el final lo marca, sin querer, `end_date="2026-10-01"` de la meteo. Propuesta: fijar `FECHA_FIN` (por ejemplo, el 30/09/2026) para que las cifras no cambien cada vez que Open Data publique datos nuevos.
3. **Corregir la hora de la meteo cambia cifras ya presentadas:**
   - la calma pasa de 28,10 → 25,47 a ≈ 29,34 → 26,62;
   - también cambian la regresión −1,74 y el GBM.

   Recomendación: corregirlo; es un error real y defendible. El DiD básico (−1,63) **no cambia**.
4. **Definición de «calma post global».** Hay dos: la media simple de fase 1 y fase 2 (24,52; −12,8 %) o la media de todas las horas posteriores (24,32; −13,4 %). Recomendación: la de todas las horas, que es más fácil de explicar.
5. **Estaciones de control muy desiguales.** Europa baja −26,8 % y Barakaldo sube +4,1 %. El −1,63 depende mucho de qué estaciones estén en el control. Antes de defenderlo hay que saber si Europa tuvo algún cambio propio (obras, traslado, cambio de sensor). `[PENDIENTE DE VERIFICAR]` en la ficha de la estación de Open Data Euskadi. Las fases 2 y 4 no piden un análisis por estación, así que el equipo debe decidir si se menciona como limitación.
6. **Grafana y la carga histórica usan datos del pipeline B.**
   - `ingesta/carga_historica.py:47-49, 150-155, 235` lee primero `datos/procesados/calidad_aire/no2_horario_limpio.zip` (B, con medias diarias a las 00:00) y la meteo de Banderas.
   - Al borrar `datos/` en la fase 1 hay que apuntarla a `data/clean/calidad_aire_limpio.csv`.
   - Ese fichero **no está versionado** (pesa más de 50 MB), así que el bucket `aire` solo tendrá datos si antes se ejecuta el pipeline A.
   - Hay que decidir si se versiona un zip de A o si la carga histórica se documenta como paso obligatorio.
7. **El NO de P4 y PM2,5.**
   - Al corregir el mapeo, cambian la fila «NO» de P4 y el texto «−14 % a −39 %».
   - PM2,5 empezará a tener datos.

   Hay que decidir si P4 usa solo NO₂, NOx y SO₂ (los que tienen todas las estaciones) para que el análisis sea simple.
8. **Gradient Boosting:** el −2,85 depende de una validación que no es válida. Hasta la fase 4 no debe citarse en ningún documento.
9. **Fuentes no verificadas** que aparecen en los documentos:
   - «27 cámaras», superficie de 2 o 2,1 km², «Abando» o «Abando e Indautxu»: `[PENDIENTE DE VERIFICAR]`;
   - ~10 % del parque sin etiqueta (NB celda 32): `[PENDIENTE DE VERIFICAR]`;
   - las dos referencias bibliográficas del informe (Grange y Carslaw, 2019; Angrist y Pischke, 2009): `[PENDIENTE DE VERIFICAR]`.
10. **Reparto de responsabilidades (SBD-16):** lo tiene que escribir el equipo.
11. **«Leed los comentarios del Excel» (MIA-15):** en `correcciones/` solo está el PDF de la hoja de evaluación. Si hay comentarios en el Excel original que no están en `CORRECCIONES.md`, hace falta ese fichero.
