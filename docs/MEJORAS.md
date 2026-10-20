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
