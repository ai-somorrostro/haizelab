# ¿Funciona la ZBE de Bilbao? Propuesta de modelo de IA
### Para decidir si ampliar, mantener o ajustar la Zona de Bajas Emisiones

**Cliente:** Ayuntamiento de Bilbao  
**Equipo:** HaizeLab: Alfred Gabriel, Iñigo Guzmán y Kerman Latorre  
**Periodo analizado:** 01/01/2022 – 30/09/2026  
**Fecha:** Octubre de 2026  

Versión para imprimir: [MIA_Haizen_Lab.docx](MIA_Haizen_Lab.docx) · [MIA_Haizen_Lab.pdf](MIA_Haizen_Lab.pdf). Este fichero lo genera `docs/generar_mia.py` a partir de `resultados/resultados.json`.

## 1. Problema y requisitos

**Objetivo:** saber si la Zona de Bajas Emisiones (ZBE) funciona y, con esa respuesta, decidir si ampliarla, mantenerla o ajustarla. Todo el documento sirve a esa decisión.

La ZBE restringe la entrada de vehículos de lunes a viernes laborables, de 7:00 a 20:00: desde el 15/06/2024 (fase 1) a los vehículos sin etiqueta ambiental y desde el 16/06/2025 (fase 2) también a los de etiqueta B de no residentes. **Dentro** son las estaciones de medida situadas en la ZBE (Mazarredo y Mª Díaz de Haro).

**Por qué el NO<sub>2</sub>.** El NO<sub>2</sub> (dióxido de nitrógeno) sale sobre todo de los tubos de escape, en especial de los motores diésel, así que es el contaminante que más debería notar una medida que saca coches del centro. Además tiene límites legales: 40 µg/m³ de media anual y 200 µg/m³ en una hora (Directiva 2008/50/CE). Los demás contaminantes no sirven igual de bien:

- **SO<sub>2</sub>:** apenas sale de los coches. Se usa como comprobación: si bajara dentro igual que el NO<sub>2</sub>, la causa no sería el tráfico. No baja: efecto de +0,33 µg/m³ (de −0,01 a +0,66).
- **PM10 y PM2,5 (partículas):** además del tráfico vienen de calefacciones, obras y polvo que llega de lejos; un cambio no se podría atribuir a la ZBE.
- **NO y NOx:** son de la misma familia que el NO<sub>2</sub> y dirían lo mismo; el NO<sub>2</sub> es el que tiene límite legal.
- **CO y benceno:** no los miden todas las estaciones, así que no se puede comparar dentro con fuera.

**El problema no es solo predecir el NO<sub>2</sub>.** El objetivo es medir el efecto de una política. Un modelo que predice bien el NO<sub>2</sub> no demuestra que la ZBE haya causado una bajada: el NO<sub>2</sub> también baja por el tiempo atmosférico o porque los coches viejos se sustituyen por otros más limpios, con o sin ZBE. Por eso hacen falta dos piezas: un modelo que descuente el tiempo y una comparación con estaciones de fuera que descuente lo demás.

**Contrafactual:** lo que habría pasado si no se hubiera puesto la ZBE. No se puede medir, hay que estimarlo. Ejemplo: después de la ZBE, dentro se midió de media 21,91 µg/m³. El modelo calcula que, con el mismo tiempo y calendario pero sin ZBE, habría habido unos 24,1. Esa cifra es el contrafactual.

**Ruido:** la parte de la variación del NO<sub>2</sub> que el modelo no explica: un atasco, unas obras, un evento o un fallo del sensor. En nuestro caso es el 63 % de la variación de una hora a otra. Importa porque el efecto que se busca es pequeño (décimas o pocas unidades de µg/m³) frente a un error de 8,14 µg/m³ en cada hora; por eso el efecto se calcula con miles de horas y con un margen de error.

| Requisito | En este proyecto |
|---|---|
| Qué entra y qué sale | Entra el tiempo atmosférico, el calendario y la estación de cada hora; sale el NO<sub>2</sub> esperado sin ZBE. |
| Tipo de problema | Regresión (predecir un número, el NO<sub>2</sub> en µg/m³) dentro de una evaluación de una política: el efecto se obtiene comparando dentro con fuera. |
| Indicador de calidad | Error medio (MAE) en un periodo que el modelo no ha visto, comparado con un modelo simple sin IA: 8,14 frente a 10,50 µg/m³ (apartado 4). |
| Validación | Temporal: se entrena con el pasado y se valida con el futuro, nunca al revés. Si se mezclaran horas al azar, el modelo vería horas de la misma semana que tiene que predecir y su error parecería menor. |
| Interpretación | El resultado se da en µg/m³ con un margen de error y con qué variables usa más el modelo. |

**Estaciones de control (fuera).** Europa, Erandio, Castrejana, Basauri y Barakaldo. Se eligen las estaciones de la red del Gobierno Vasco que están en el área de Bilbao, fuera de la ZBE y con NO<sub>2</sub> en todo el periodo (completitud de al menos 93,13 %). Arraiz no entra: está en un monte, lejos del tráfico (8,73 µg/m³ antes de la ZBE). Son comparables porque tienen el mismo tiempo atmosférico y el mismo tipo de coches que el centro, pero no la ZBE. No tienen el mismo nivel de NO<sub>2</sub> (18,25 frente a 25,50 µg/m³ antes), pero el método compara cambios, no niveles. Límite: antes de la ZBE no iban del todo en paralelo (de 2022 a 2023, +0,10 dentro y −1,14 fuera).

## 2. Principios de la IA y casos reales

Un sistema de IA de aprendizaje supervisado aprende una relación a partir de ejemplos con la respuesta conocida y la aplica a casos nuevos. Así se aplican sus principios en este proyecto:

| Principio | Qué significa | En nuestro caso |
|---|---|---|
| Aprender de datos | El modelo saca la relación de ejemplos, no de reglas escritas. | Aprende de 118.804 horas-estación de 2022 y 2023. |
| Datos de calidad | Si los datos están mal, el modelo aprende mal. | Se comprueba el dato limpio contra el original; hay dato de NO<sub>2</sub> en el 96,66 % de las horas. |
| Generalizar sin sobreajuste | Debe acertar en casos nuevos, no memorizar los de entrenamiento. | Random Forest: error de 4,77 en entrenamiento y 8,14 en validación (apartado 8). |
| Validar con datos no vistos | El error se mide en un periodo que el modelo no ha usado. | Validación del 01/01/2024 al 14/06/2024, posterior al entrenamiento. |
| Explicabilidad | Hay que poder decir en qué se basa el resultado. | Importancia de variables: la que más usa es el viento (apartado 5). |
| Incertidumbre | Toda estimación lleva un margen de error. | Cada efecto se da con un intervalo del 95 %. |

**Casos reales de IA en calidad del aire y movilidad urbana.** Las fuentes completas están al final.

| Caso | Qué hace la IA | Relación con este proyecto |
|---|---|---|
| Normalización meteorológica (Reino Unido) [1] | Un Random Forest aprende el contaminante a partir del tiempo y el calendario para ver cambios por medidas de tráfico. | Es la misma idea que nuestro modelo. |
| ZBE de Londres (ULEZ) [2] | Random Forest para quitar el efecto del tiempo y ciudades de control. La ULEZ de 2019 bajó el NO<sub>2</sub> un 19,6 % en las estaciones de tráfico del centro a los tres meses; la ampliación de 2023 no mostró cambio detectable. | Misma pregunta que la nuestra, incluida la de si una fase nueva añade algo. |
| Madrid Central [3] | Regresión polinómica y redes neuronales sobre el NO<sub>2</sub> para evaluar la zona de bajas emisiones. | ZBE española y mismo contaminante. |
| Previsión europea de calidad del aire (CAMS) [4] | Random Forest y Gradient Boosting corrigen la previsión del NO<sub>2</sub>, el ozono y las partículas en cada estación. | Primer paso de un sistema de avisos (ver abajo). |
| Semáforos (Google, Project Green Light) [5] | Modela el tráfico con IA y datos de Google Maps y recomienda tiempos de semáforo. Boston, ciudad participante, cita los primeros resultados del programa: hasta un 30 % menos de paradas y hasta un 10 % menos de emisiones en los cruces. | Movilidad urbana; no se usa en este proyecto porque no gestionamos semáforos. |

**Avisos de contaminación: la cadena completa.** Un aviso no lo da solo un modelo de predicción. Son tres pasos: (1) **predicción:** un modelo de IA, como el del caso [4], predice el NO<sub>2</sub> de las próximas horas en cada estación; (2) **umbral:** una regla fija compara la predicción con un límite (por ejemplo, 200 µg/m³ en una hora); (3) **aviso:** si se supera, se informa a la población y, si un protocolo lo prevé, se aplican medidas. El protocolo de Madrid para el NO<sub>2</sub> [6] sigue este esquema: fija niveles de preaviso, aviso y alerta (200, 250 y 400 µg/m³ superados en varias estaciones de una zona durante horas seguidas) y solo aplica sus escenarios de medidas cuando la previsión meteorológica de AEMET es desfavorable. Allí la previsión es meteorológica; un modelo de IA como el del caso [4] permitiría prever directamente el NO<sub>2</sub>. Solo el primer paso puede ser IA; el segundo y el tercero son reglas. En Bilbao no hubo ninguna hora por encima de 200 µg/m³ entre 2022 y 2026 (máximo horario: 168 µg/m³), así que este aviso no se habría activado nunca. Tiene menos relación con la decisión sobre la ZBE que la evaluación del efecto, que es lo que se propone.

## 3. Familias de IA

| Familia | Qué es | Ejemplo | ¿Se usa aquí? |
|---|---|---|---|
| Aprendizaje supervisado | Aprende de ejemplos con la respuesta conocida. | Casos [1] a [5]. | Sí. Es el núcleo: Random Forest predice el NO<sub>2</sub> sin ZBE. |
| Razonamiento impreciso | Trabaja con categorías sin límites exactos («calidad del aire regular») o con probabilidades. | Clasificar el aire en «buena», «regular» o «mala» con grados intermedios. | No. El margen de error se calcula con un método estadístico (apartado 5). |
| Sistemas basados en reglas | Reglas «si… entonces…» escritas por expertos; no aprenden. | Pasos 2 y 3 de los avisos: «si la predicción supera el umbral, avisar». | Solo en las alertas de Grafana, que son reglas fijas. |
| Visión artificial | Interpreta imágenes o vídeo. | Cámaras que leen matrículas para controlar el acceso a una ZBE. | No. Nuestros datos son tablas de números, no imágenes. |

- **La automatización no es IA.** Node-RED descarga los datos y los guarda en InfluxDB siguiendo pasos fijos; no aprende ni decide.
- **Diferencias en diferencias (DiD) no es IA.** Es un método estadístico: la caída de dentro menos la caída de fuera. Se usa como comprobación del resultado del modelo (apartado 8).

## 4. Comparación de alternativas

Mismas variables para todos: tiempo atmosférico (temperatura, humedad, lluvia, viento), calendario (hora, día de la semana, mes, laborable, festivo) y estación. Entrenamiento: 01/01/2022 – 31/12/2023. Validación: 01/01/2024 – 14/06/2024, antes de la ZBE. **MAE:** cuántos µg/m³ se equivoca el modelo en una hora, de media. **RMSE:** parecido, pero castiga más los errores grandes. **R²:** parte de la variación del NO<sub>2</sub> que explica (1 = toda, 0 = nada).

| Modelo | MAE entren. | MAE valid. | RMSE valid. | R² valid. |
|---|---|---|---|---|
| Base: media por hora y mes (sin IA) | 9,09 | 10,50 | 13,49 | 0,05 |
| Regresión lineal | 9,56 | 9,79 | 12,23 | 0,22 |
| Random Forest | 4,77 | 8,14 | 11,00 | 0,37 |
| Gradient Boosting | 6,55 | 8,15 | 10,85 | 0,38 |

- **Base (sin IA):** NO<sub>2</sub> medio de cada estación a esa hora en ese mes. Si un modelo de IA no lo mejora, no aporta nada.
- **Regresión lineal:** suma cada variable multiplicada por un peso; solo dibuja rectas.
- **Random Forest:** muchos árboles de decisión, cada uno entrenado con una muestra distinta; predice la media de todos.
- **Gradient Boosting:** árboles en cadena; cada uno corrige el error de los anteriores.

**Descartados sin probar:**

- **SARIMAX:** predice una serie a partir de sus propios valores pasados, y el tiempo atmosférico entra como una suma con un peso fijo, igual que en la regresión lineal, que ya se equivoca más (9,79 µg/m³). Además, después de la ZBE los valores pasados de NO<sub>2</sub> ya llevan el efecto de la ZBE, así que el contrafactual saldría contaminado.
- **Red LSTM:** red neuronal para secuencias, con miles de parámetros. Con dos años de entrenamiento solo ve dos veces cada estación del año; Random Forest ya mejora la base un 22,5 %. Es más difícil de explicar (no se puede ver qué hace con cada variable), necesita más cálculo y tendría el mismo problema que SARIMAX si usara el NO<sub>2</sub> de horas anteriores.

## 5. Modelo elegido y resultado

**Random Forest**, porque tiene el menor error en validación (8,14 µg/m³), un 22,5 % menos que la base. En la práctica empata con Gradient Boosting: la diferencia es de 0,01 µg/m³. Se eligió Random Forest por la regla fijada de antemano: el menor MAE en validación. Cada árbol hace preguntas como «¿viento de menos de 2 m/s?», «¿entre las 7 y las 9?», «¿laborable?», y al final da el NO<sub>2</sub> medio de las horas de entrenamiento que cumplen lo mismo.

**Por qué hace falta un modelo no lineal.** Una relación es lineal si cada m/s de viento de más baja el NO<sub>2</sub> siempre lo mismo. En nuestros datos no es así:

| Viento (m/s) | 0-1 | 1-2 | 2-3 | 3-4 | 4-6 | 6 o más |
|---|---|---|---|---|---|---|
| NO<sub>2</sub> medio (µg/m³) | 24,01 | 24,84 | 21,53 | 16,29 | 13,16 | 8,02 |

Entre 0-1 y 1-2 m/s el NO<sub>2</sub> sube 0,83 µg/m³ y al pasar de 2-3 a 3-4 m/s baja 5,24. Una regresión lineal usa una recta y no reproduce esa curva; los árboles parten el viento en tramos.

**Qué variables usa más.** Importancia por permutación: se desordena una variable en la validación y se mira cuánto sube el MAE. Las tres primeras son viento (+2,48), hora (+2,07), estación (+1,87) µg/m³.

**Cómo se calcula el efecto:**

- Se entrena el modelo con todas las horas de antes de la ZBE, de dentro y de fuera.
- Para cada hora después de la ZBE, predice el NO<sub>2</sub> de cada estación con el tiempo y el calendario de esa hora.
- Diferencia = NO<sub>2</sub> observado − NO<sub>2</sub> predicho, y efecto = diferencia media dentro − diferencia media fuera. Se resta la de fuera porque el modelo no conoce la renovación de coches ni otros cambios de toda la comarca, que aparecen también fuera.
- Intervalo del 95 %: se agrupan las horas por semanas y se repite el cálculo sorteando semanas (bootstrap). Si el intervalo incluye el cero, el resultado es **no concluyente**.

**Resultado:** diferencia dentro −2,21, fuera −1,73; efecto = −2,21 − (−1,73) = **−0,49 µg/m³** (de −0,86 a −0,12; −1,9 % del nivel de antes). *Qué significa:* descontado el tiempo atmosférico y lo que pasó fuera, el NO<sub>2</sub> bajó dentro algo más que fuera. El efecto es pequeño: menor que el que da la comparación de medias del informe de análisis (DiD, −1,63). **Por qué el modelo da menos:** DiD resta medias y no descuenta el tiempo atmosférico; el modelo predice cada hora con el tiempo que hizo de verdad y sí lo descuenta. La parte de la bajada que DiD atribuye a la ZBE y el modelo no es la que el modelo explica con el tiempo atmosférico. Se puede medir aunque el error por hora sea de 8,14 porque es la media de 134.753 horas-estación, y los errores hacia arriba y hacia abajo se compensan.

## 6. Cómo funciona la solución

| 1. Datos | 2. Modelo | 3. Resultado | 4. Decisión y acción |
|---|---|---|---|
| NO<sub>2</sub> horario (Gobierno Vasco), tiempo atmosférico (Open-Meteo) y calendario, limpios y unidos por hora. | Random Forest entrenado antes de la ZBE; predice el NO<sub>2</sub> sin ZBE en cada estación. | Efecto = (observado − predicho) dentro − fuera, con intervalo y placebo. | Ampliar, mantener o ajustar la ZBE. Panel de Grafana para seguirlo. |

Cada flecha es un paso automático: los datos los descarga y limpia un script, el notebook calcula y guarda las cifras en resultados.json, y este documento y el informe se generan desde ese fichero.

## 7. Impacto: indicadores medibles

| Indicador | Cómo se mide | Valor |
|---|---|---|
| Horas de trabajo manual para actualizar el análisis | Horas de una persona para actualizar el análisis con datos nuevos: a mano (descargar, limpiar y calcular) frente a con el notebook (un comando). Se cronometran las dos formas. | A medir en la puesta en marcha. |
| Tiempo hasta tener el panel actualizado | Frecuencia de ingesta de Node-RED en InfluxDB. | Tiempo atmosférico cada 15 min y tráfico cada 5 min. Calidad del aire oficial: datos horarios por estación, según los propios ficheros descargados. |
| Error del modelo | MAE en validación cada vez que se reentrena. | 8,14 µg/m³ (base sin IA: 10,50). Debe seguir por debajo de la base. |
| Horas al año por encima de 200 µg/m³ | Contar horas-estación con NO<sub>2</sub> > 200. | 0 en todos los años de 2022 a 2026; máximo horario 168 µg/m³. |
| Efecto de la ZBE | Repetir el apartado 5 con cada año de datos nuevos. | −0,49 µg/m³ (de −0,86 a −0,12). |

## 8. Ventajas, limitaciones y riesgos de la solución

Se refieren a la solución propuesta: el modelo más la comparación con las estaciones de fuera.

**Ventajas**

- Descuenta el tiempo atmosférico hora a hora; el viento es la variable que más pesa (+2,48 µg/m³ de error si se desordena).
- Descuenta lo que pasa en toda la comarca: el modelo también se pasa fuera (−1,73), y eso se resta.
- Se puede comprobar: validación temporal y placebo con su resultado.
- Se repite con un comando sobre los mismos datos que el informe de análisis; no trata datos personales.

**Limitaciones**

- El modelo explica el 37 % de la variación hora a hora; el resto es ruido.
- Solo hay 2 estaciones dentro de la ZBE.
- Las estaciones miden la concentración en el aire, no lo que emiten los coches.
- El tamaño del efecto depende del método (ver riesgos).

**Riesgos, cómo se miden y resultado**

| Riesgo | Comprobación | Resultado |
|---|---|---|
| Atribuir a la ZBE un cambio que no es suyo | Placebo: repetir el cálculo con una ZBE ficticia el 15/06/2023, con datos de antes de la real. Debería dar cero. | +0,33 (de −0,23 a +0,96): incluye el cero, pero se aleja de cero tanto como el efecto real (−0,49). El efecto se da como pequeño y con cautela. |
| Que baje todo el aire, no solo el del tráfico | SO<sub>2</sub>, que no viene del tráfico. | +0,33 (de −0,01 a +0,66): no baja. |
| Sobreajuste | MAE en entrenamiento frente a validación. | Random Forest: 4,77 frente a 8,14. Memoriza parte del entrenamiento; por eso se elige por el error en validación, que sigue siendo el menor. |
| Que el control no sea comparable | Tendencia antes de la ZBE y bajada por estación. | 2022→2023: +0,10 dentro, −1,14 fuera. Europa baja un 26,8 %, más que las de dentro; causa [PENDIENTE DE VERIFICAR POR EL EQUIPO]. |
| Que el resultado dependa del método | Comparar con la resta de medias (DiD) del informe de análisis. | Modelo −0,49; DiD −1,63 (de −2,38 a −0,94). Los dos bajan, pero sus intervalos no se solapan: el tamaño exacto es incierto. La diferencia viene de que el modelo descuenta el tiempo atmosférico y DiD no. |

**Por qué DiD no es el modelo principal.** DiD solo resta medias: no descuenta el tiempo hora a hora. Si después de la ZBE hubiera hecho más viento en el centro que fuera, lo contaría como efecto de la ZBE. Se mantiene como comprobación porque es simple y no depende de ningún modelo: si los dos métodos dan una bajada, la dirección del resultado no depende del método elegido.

**Qué significa para la decisión**

- **Mantener la ZBE:** los dos métodos dan una bajada dentro mayor que fuera (−0,49 y −1,63 µg/m³).
- **No ampliar todavía:** el efecto es pequeño y la fase 2 no añade una bajada distinguible de cero (−0,52; de −1,72 a +0,74).
- **Ajustar la medición:** más puntos de medida dentro de la ZBE reducirían el margen de error. Repetir el cálculo cada año.

## Fuentes

- [1] Grange, S. K. y Carslaw, D. C. (2019). Using meteorological normalisation to detect interventions in air quality time series. *Science of the Total Environment*, 653, 578-588.
- [2] Tong, C., Dai, Y., Cole, M., Elliott, R. J. R., Bartington, S. E., Liu, B. y Shi, Z. (2025). Further improvement in London's air quality demands more than the Ultra Low Emission Zone policy. *npj Clean Air*, 1, 29. doi:10.1038/s44407-025-00030-9.
- [3] Toutouh, J., Lebrusán, I. y Nesmachnow, S. (2020). Computational Intelligence for Evaluating the Air Quality in the Center of Madrid, Spain. En *Optimization and Learning (OLA 2020)*, Communications in Computer and Information Science, vol. 1173. Springer.
- [4] Bertrand, J.-M., Meleux, F., Ung, A., Descombes, G. y Colette, A. (2023). Technical note: Improving the European air quality forecast of the Copernicus Atmosphere Monitoring Service using machine learning techniques. *Atmospheric Chemistry and Physics*, 23, 5317-5333.
- [5] Ciudad de Boston. Project Green Light: Saving You Time On The Road. https://www.boston.gov/node/16372851
- [6] Ayuntamiento de Madrid (2015). Protocolo de medidas a adoptar durante episodios de alta contaminación por dióxido de nitrógeno en la ciudad de Madrid. https://www.madrid.es/UnidadWeb/UGNormativas/Normativa/2015/ficheros/AnexoProtocoloContaminacion.pdf
- Directiva 2008/50/CE del Parlamento Europeo y del Consejo, relativa a la calidad del aire ambiente y a una atmósfera más limpia en Europa.
