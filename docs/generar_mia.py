"""
Genera la propuesta de modelo de IA para el Ayuntamiento a partir de resultados/resultados.json:
  - docs/propuesta-modelo-ia.md
  - docs/MIA_Haizen_Lab.docx y .pdf (con Microsoft Word, solo en Windows)

Todas las cifras salen de resultados.json (y la frecuencia de ingesta, de nodered/flows.json); ninguna se escribe a mano.
Uso (desde la raíz del repo):  python docs/generar_mia.py
Para generar solo el Markdown (sin Word):  python docs/generar_mia.py --solo-md
"""
import json
import sys

from generar_informe import DIR_DOCS, DIR_RAIZ, R, a_html, a_markdown, a_word, es, fecha

NOMBRE = "MIA_Haizen_Lab"

# ---------------------------------------------------------------------------
# Cifras que se usan en el texto
per, cal = R["periodo_estudio"], R["calidad_datos"]
p1, p4, p5 = R["p1_did"], R["p4_so2"], R["p5_fases"]
est, anual = R["estaciones_no2"], R["medias_anuales_no2"]
m = R["modelo_ia"]
met, ef, pl = m["metricas"], m["efecto"], m["placebo_15_06_2023"]
BASE = "Base: media por hora y mes (sin IA)"
IA = ["Regresión lineal", "Random Forest", "Gradient Boosting"]
el = m["modelo_elegido"]
otro = min((n for n in IA if n != el), key=lambda n: met[n]["mae_val"])
f2 = p5["fase2_vs_fase1"]

NOMBRE_VAR = {"temp_c": "temperatura", "humedad_pct": "humedad", "precipitacion_mm": "lluvia", "viento_ms": "viento",
              "hora": "hora", "dia_semana": "día de la semana", "mes": "mes", "es_laborable": "laborable",
              "es_festivo": "festivo", "estacion": "estación"}
imp = m["importancia_permutacion_mae"]
top = list(imp)[:3]
tramos = m["no2_por_tramo_viento"]
t = list(tramos)
cambios = {(a, b): tramos[b] - tramos[a] for a, b in zip(t[:-1], t[1:])}
mayor_bajada = min(cambios, key=cambios.get)
horas_200 = m["horas_no2_mayor_200_por_año"]
ruido_pct = (1 - met[el]["r2_val"]) * 100
predicho_dentro = p1["dentro_post"] - ef["diferencia_dentro"]
sin_zbe_segun_fuera = p1["dentro_pre"] + p1["caida_bruta_fuera"]
dentro = [e for e in est if est[e]["zona"] == "dentro"]
fuera = [e for e in est if est[e]["zona"] == "fuera"]
fondo = [e for e in est if est[e]["zona"] == "fondo"]
control_min = min(fuera, key=lambda e: est[e]["var_post_vs_previo_pct"])
cambio_previo_dentro = anual["dentro"]["2023"] - anual["dentro"]["2022"]
cambio_previo_fuera = anual["fuera"]["2023"] - anual["fuera"]["2022"]
completitud = cal["completitud_no2_por_estacion_pct"]

# Frecuencia de ingesta de Node-RED (segundos), leída de su configuración
flujos = json.loads((DIR_RAIZ / "nodered" / "flows.json").read_text(encoding="utf-8"))
repeticion = {n.get("name"): int(n["repeat"]) for n in flujos if n.get("type") == "inject" and n.get("repeat")}
min_meteo, min_trafico = repeticion["Cada 15 min"] // 60, repeticion["Cada 5 min"] // 60

# Las frases dependen de estas condiciones. Si los datos cambian y dejan de cumplirse,
# el script se para en vez de escribir algo que ya no es cierto.
assert el == "Random Forest", "El modelo elegido ya no es Random Forest; revisar el texto"
assert met[otro]["mae_val"] - met[el]["mae_val"] < 0.1, "Ya no hay casi empate entre modelos; revisar el texto"
assert met[el]["mae_val"] < met["Regresión lineal"]["mae_val"] < met[BASE]["mae_val"]
assert ef["ic95_sup"] < 0 and p1["ic95_sup"] < 0, "Algún efecto ya no es una bajada distinta de cero; revisar el texto"
assert not m["intervalo_solapa_con_did"], "Los intervalos ya se solapan; revisar el texto"
assert pl["incluye_cero"] and pl["del_mismo_orden_que_el_efecto"], "Placebo: revisar el texto"
assert p4["ic95_inf"] <= 0 <= p4["ic95_sup"] and f2["ic95_inf"] <= 0 <= f2["ic95_sup"]
assert cambios[(t[0], t[1])] > 0, "El NO2 ya no sube del primer al segundo tramo de viento; revisar el texto"
assert top[0] == "viento_ms" and sum(horas_200.values()) == 0

# ---------------------------------------------------------------------------
portada = {
    "titulo": "¿Funciona la ZBE de Bilbao? Propuesta de modelo de IA",
    "subtitulo": "Para decidir si ampliar, mantener o ajustar la Zona de Bajas Emisiones",
    "filas": [
        ("Cliente", "Ayuntamiento de Bilbao"),
        ("Equipo", "HaizeLab: Alfred Gabriel, Iñigo Guzmán y Kerman Latorre"),
        ("Periodo analizado", f"{fecha(per['fecha_inicio'])} – {fecha(per['fecha_fin'])}"),
        ("Fecha", "Octubre de 2026"),
    ],
}

B = []
h = lambda x: B.append(("h", x))
p = lambda x: B.append(("p", x))
ul = lambda *items: B.append(("ul", list(items)))
tabla = lambda cab, filas, anchos: B.append(("tabla", cab, filas, anchos))

# 1 ---------------------------------------------------------------------------
h("1. Problema y requisitos")
p("**Objetivo:** saber si la Zona de Bajas Emisiones (ZBE) funciona y, con esa respuesta, decidir si ampliarla, "
  "mantenerla o ajustarla. Todo el documento sirve a esa decisión.")
p(f"La ZBE restringe la entrada de vehículos de lunes a viernes laborables, de 7:00 a 20:00: desde el {fecha(per['fecha_fase1'])} "
  f"(fase 1) a los vehículos sin etiqueta ambiental y desde el {fecha(per['fecha_fase2'])} (fase 2) también a los de etiqueta B de "
  f"no residentes. **Dentro** son las estaciones de medida situadas en la ZBE ({' y '.join(dentro)}).")
p("**Por qué el NO₂.** El NO₂ (dióxido de nitrógeno) sale sobre todo de los tubos de escape, en especial de los motores diésel, "
  "así que es el contaminante que más debería notar una medida que saca coches del centro. Además tiene límites legales: "
  "40 µg/m³ de media anual y 200 µg/m³ en una hora (Directiva 2008/50/CE). Los demás contaminantes no sirven igual de bien:")
ul(f"**SO₂:** apenas sale de los coches. Se usa como comprobación: si bajara dentro igual que el NO₂, la causa no sería el tráfico. "
   f"No baja: efecto de {es(p4['efecto_neto'], signo=True)} µg/m³ (de {es(p4['ic95_inf'])} a {es(p4['ic95_sup'], signo=True)}).",
   "**PM10 y PM2,5 (partículas):** además del tráfico vienen de calefacciones, obras y polvo que llega de lejos; un cambio no se "
   "podría atribuir a la ZBE.",
   "**NO y NOx:** son de la misma familia que el NO₂ y dirían lo mismo; el NO₂ es el que tiene límite legal.",
   "**CO y benceno:** no los miden todas las estaciones, así que no se puede comparar dentro con fuera.")
p("**El problema no es solo predecir el NO₂.** El objetivo es medir el efecto de una política. Un modelo que predice bien el NO₂ "
  "no demuestra que la ZBE haya causado una bajada: el NO₂ también baja por el tiempo atmosférico o porque los coches viejos se "
  "sustituyen por otros más limpios, con o sin ZBE. Por eso hacen falta dos piezas: un modelo que descuente el tiempo y una "
  "comparación con estaciones de fuera que descuente lo demás.")
p(f"**Contrafactual:** lo que habría pasado si no se hubiera puesto la ZBE. No se puede medir, hay que estimarlo. Ejemplo: "
  f"después de la ZBE, dentro se midió de media {es(p1['dentro_post'])} µg/m³. El modelo calcula que, con el mismo tiempo y "
  f"calendario pero sin ZBE, habría habido unos {es(predicho_dentro, 1)}. Esa cifra es el contrafactual.")
p(f"**Ruido:** la parte de la variación del NO₂ que el modelo no explica: un atasco, unas obras, un evento o un fallo del sensor. "
  f"En nuestro caso es el {es(ruido_pct, 0)} % de la variación de una hora a otra. Importa porque el efecto que se busca es pequeño "
  f"(décimas o pocas unidades de µg/m³) frente a un error de {es(met[el]['mae_val'])} µg/m³ en cada hora; por eso el efecto se "
  "calcula con miles de horas y con un margen de error.")
tabla(["Requisito", "En este proyecto"], [
    ["Qué entra y qué sale", "Entra el tiempo atmosférico, el calendario y la estación de cada hora; sale el NO₂ esperado sin ZBE."],
    ["Tipo de problema", "Regresión (predecir un número, el NO₂ en µg/m³) dentro de una evaluación de una política: el efecto se "
                         "obtiene comparando dentro con fuera."],
    ["Indicador de calidad", f"Error medio (MAE) en un periodo que el modelo no ha visto, comparado con un modelo simple sin IA: "
                             f"{es(met[el]['mae_val'])} frente a {es(met[BASE]['mae_val'])} µg/m³ (apartado 4)."],
    ["Validación", "Temporal: se entrena con el pasado y se valida con el futuro, nunca al revés. Si se mezclaran horas al azar, "
                   "el modelo vería horas de la misma semana que tiene que predecir y su error parecería menor."],
    ["Interpretación", "El resultado se da en µg/m³ con un margen de error y con qué variables usa más el modelo."],
], [4, 14])
p("**Estaciones de control (fuera).** " + ", ".join(fuera[:-1]) + f" y {fuera[-1]}. Se eligen las estaciones de la red del "
  "Gobierno Vasco que están en el área de Bilbao, fuera de la ZBE y con NO₂ en todo el periodo "
  f"(completitud de al menos {es(min(completitud[e] for e in fuera))} %). {fondo[0]} no entra: está en un monte, lejos del tráfico "
  f"({es(est[fondo[0]]['previo'])} µg/m³ antes de la ZBE). Son comparables porque tienen el mismo tiempo atmosférico y el mismo "
  "tipo de coches que el centro, pero no la ZBE. No tienen el mismo nivel de NO₂ "
  f"({es(p1['fuera_pre'])} frente a {es(p1['dentro_pre'])} µg/m³ antes), pero el método compara cambios, no niveles. "
  f"Límite: antes de la ZBE no iban del todo en paralelo (de 2022 a 2023, {es(cambio_previo_dentro, signo=True)} dentro y "
  f"{es(cambio_previo_fuera, signo=True)} fuera).")

# 2 ---------------------------------------------------------------------------
h("2. Principios de la IA y casos reales")
p("Un sistema de IA de aprendizaje supervisado aprende una relación a partir de ejemplos con la respuesta conocida y la aplica "
  "a casos nuevos. Así se aplican sus principios en este proyecto:")
tabla(["Principio", "Qué significa", "En nuestro caso"], [
    ["Aprender de datos", "El modelo saca la relación de ejemplos, no de reglas escritas.",
     f"Aprende de {es(m['filas_entrenamiento'], 0)} horas-estación de {m['entrenamiento'][0][:4]} y {m['entrenamiento'][1][:4]}."],
    ["Datos de calidad", "Si los datos están mal, el modelo aprende mal.",
     f"Se comprueba el dato limpio contra el original; hay dato de NO₂ en el {es(cal['completitud_no2_total_pct'])} % de las horas."],
    ["Generalizar sin sobreajuste", "Debe acertar en casos nuevos, no memorizar los de entrenamiento.",
     f"{el}: error de {es(met[el]['mae_ent'])} en entrenamiento y {es(met[el]['mae_val'])} en validación (apartado 8)."],
    ["Validar con datos no vistos", "El error se mide en un periodo que el modelo no ha usado.",
     f"Validación del {fecha(m['validacion'][0])} al {fecha(m['validacion'][1])}, posterior al entrenamiento."],
    ["Explicabilidad", "Hay que poder decir en qué se basa el resultado.",
     f"Importancia de variables: la que más usa es el {NOMBRE_VAR[top[0]]} (apartado 5)."],
    ["Incertidumbre", "Toda estimación lleva un margen de error.", "Cada efecto se da con un intervalo del 95 %."],
], [4, 6, 8])
p("**Casos reales de IA en calidad del aire y movilidad urbana.** Las fuentes completas están al final.")
tabla(["Caso", "Qué hace la IA", "Relación con este proyecto"], [
    ["Normalización meteorológica (Reino Unido) [1]",
     "Un Random Forest aprende el contaminante a partir del tiempo y el calendario para ver cambios por medidas de tráfico.",
     "Es la misma idea que nuestro modelo."],
    ["ZBE de Londres (ULEZ) [2]",
     "Random Forest para quitar el efecto del tiempo y ciudades de control. La ULEZ de 2019 bajó el NO₂ un 19,6 % en las "
     "estaciones de tráfico del centro a los tres meses; la ampliación de 2023 no mostró cambio detectable.",
     "Misma pregunta que la nuestra, incluida la de si una fase nueva añade algo."],
    ["Madrid Central [3]", "Regresión polinómica y redes neuronales sobre el NO₂ para evaluar la zona de bajas emisiones.",
     "ZBE española y mismo contaminante."],
    ["Previsión europea de calidad del aire (CAMS) [4]",
     "Random Forest y Gradient Boosting corrigen la previsión del NO₂, el ozono y las partículas en cada estación.",
     "Primer paso de un sistema de avisos (ver abajo)."],
    ["Semáforos (Google, Project Green Light) [5]",
     "Modela el tráfico con IA y datos de Google Maps y recomienda tiempos de semáforo. Boston, ciudad participante, "
     "cita los primeros resultados del programa: hasta un 30 % menos de paradas y hasta un 10 % menos de emisiones en los cruces.",
     "Movilidad urbana; no se usa en este proyecto porque no gestionamos semáforos."],
], [4, 8, 6])
p("**Avisos de contaminación: la cadena completa.** Un aviso no lo da solo un modelo de predicción. Son tres pasos: "
  "(1) **predicción:** un modelo de IA, como el del caso [4], predice el NO₂ de las próximas horas en cada estación; "
  "(2) **umbral:** una regla fija compara la predicción con un límite (por ejemplo, 200 µg/m³ en una hora); "
  "(3) **aviso:** si se supera, se informa a la población y, si un protocolo lo prevé, se aplican medidas. El protocolo de "
  "Madrid para el NO₂ [6] sigue este esquema: fija niveles de preaviso, aviso y alerta (200, 250 y 400 µg/m³ superados en "
  "varias estaciones de una zona durante horas seguidas) y solo aplica sus escenarios de medidas cuando la previsión "
  "meteorológica de AEMET es desfavorable. Allí la previsión es meteorológica; un modelo de IA como el del caso [4] permitiría "
  "prever directamente el NO₂. Solo el primer paso puede ser IA; el segundo y el tercero son reglas. En Bilbao no hubo ninguna hora por encima de 200 µg/m³ entre {min(horas_200)} y {max(horas_200)} (máximo horario: "
  f"{es(m['no2_max_horario'], 0)} µg/m³), así que este aviso no se habría activado nunca. Tiene menos relación con la decisión "
  "sobre la ZBE que la evaluación del efecto, que es lo que se propone.")

# 3 ---------------------------------------------------------------------------
h("3. Familias de IA")
tabla(["Familia", "Qué es", "Ejemplo", "¿Se usa aquí?"], [
    ["Aprendizaje supervisado", "Aprende de ejemplos con la respuesta conocida.", "Casos [1] a [5].",
     f"Sí. Es el núcleo: {el} predice el NO₂ sin ZBE."],
    ["Razonamiento impreciso", "Trabaja con categorías sin límites exactos («calidad del aire regular») o con probabilidades.",
     "Clasificar el aire en «buena», «regular» o «mala» con grados intermedios.",
     "No. El margen de error se calcula con un método estadístico (apartado 5)."],
    ["Sistemas basados en reglas", "Reglas «si… entonces…» escritas por expertos; no aprenden.",
     "Pasos 2 y 3 de los avisos: «si la predicción supera el umbral, avisar».",
     "Solo en las alertas de Grafana, que son reglas fijas."],
    ["Visión artificial", "Interpreta imágenes o vídeo.",
     "Cámaras que leen matrículas para controlar el acceso a una ZBE.",
     "No. Nuestros datos son tablas de números, no imágenes."],
], [4, 5, 5, 4])
ul("**La automatización no es IA.** Node-RED descarga los datos y los guarda en InfluxDB siguiendo pasos fijos; no aprende ni decide.",
   "**Diferencias en diferencias (DiD) no es IA.** Es un método estadístico: la caída de dentro menos la caída de fuera. Se usa "
   "como comprobación del resultado del modelo (apartado 8).")

# 4 ---------------------------------------------------------------------------
h("4. Comparación de alternativas")
p(f"Mismas variables para todos: tiempo atmosférico ({', '.join(NOMBRE_VAR[v] for v in m['variables']['Meteorología'])}), "
  f"calendario ({', '.join(NOMBRE_VAR[v] for v in m['variables']['Calendario'])}) y estación. Entrenamiento: "
  f"{fecha(m['entrenamiento'][0])} – {fecha(m['entrenamiento'][1])}. Validación: {fecha(m['validacion'][0])} – "
  f"{fecha(m['validacion'][1])}, antes de la ZBE. **MAE:** cuántos µg/m³ se equivoca el modelo en una hora, de media. "
  "**RMSE:** parecido, pero castiga más los errores grandes. **R²:** parte de la variación del NO₂ que explica (1 = toda, 0 = nada).")
tabla(["Modelo", "MAE entren.", "MAE valid.", "RMSE valid.", "R² valid."],
      [[n, es(met[n]["mae_ent"]), es(met[n]["mae_val"]), es(met[n]["rmse_val"]), es(met[n]["r2_val"])] for n in [BASE] + IA],
      [7, 3, 3, 3, 3])
ul("**Base (sin IA):** NO₂ medio de cada estación a esa hora en ese mes. Si un modelo de IA no lo mejora, no aporta nada.",
   "**Regresión lineal:** suma cada variable multiplicada por un peso; solo dibuja rectas.",
   "**Random Forest:** muchos árboles de decisión, cada uno entrenado con una muestra distinta; predice la media de todos.",
   "**Gradient Boosting:** árboles en cadena; cada uno corrige el error de los anteriores.")
p("**Descartados sin probar:**")
ul("**SARIMAX:** predice una serie a partir de sus propios valores pasados, y el tiempo atmosférico entra como una suma con un "
   f"peso fijo, igual que en la regresión lineal, que ya se equivoca más ({es(met['Regresión lineal']['mae_val'])} µg/m³). Además, "
   "después de la ZBE los valores pasados de NO₂ ya llevan el efecto de la ZBE, así que el contrafactual saldría contaminado.",
   "**Red LSTM:** red neuronal para secuencias, con miles de parámetros. Con dos años de entrenamiento solo ve dos veces cada estación "
   f"del año; {el} ya mejora la base un {es(m['mejora_mae_frente_base_pct'], 1)} %. Es más difícil de explicar (no se puede ver qué "
   "hace con cada variable), necesita más cálculo y tendría el mismo problema que SARIMAX si usara el NO₂ de horas anteriores.")

# 5 ---------------------------------------------------------------------------
h("5. Modelo elegido y resultado")
p(f"**{el}**, porque tiene el menor error en validación ({es(met[el]['mae_val'])} µg/m³), un {es(m['mejora_mae_frente_base_pct'], 1)} % "
  f"menos que la base. En la práctica empata con {otro}: la diferencia es de {es(met[otro]['mae_val'] - met[el]['mae_val'])} µg/m³. "
  f"Se eligió {el} por la regla fijada de antemano: el menor MAE en validación. Cada árbol hace preguntas como «¿viento de menos de 2 m/s?», "
  "«¿entre las 7 y las 9?», «¿laborable?», y al final da el NO₂ medio de las horas de entrenamiento que cumplen lo mismo.")
p("**Por qué hace falta un modelo no lineal.** Una relación es lineal si cada m/s de viento de más baja el NO₂ siempre lo mismo. "
  "En nuestros datos no es así:")
tabla(["Viento (m/s)"] + t, [["NO₂ medio (µg/m³)"] + [es(v) for v in tramos.values()]], [4] + [2] * len(t))
p(f"Entre {t[0]} y {t[1]} m/s el NO₂ sube {es(cambios[(t[0], t[1])])} µg/m³ y al pasar de {mayor_bajada[0]} a {mayor_bajada[1]} m/s baja "
  f"{es(abs(cambios[mayor_bajada]))}. Una regresión lineal usa una recta y no reproduce esa curva; los árboles parten el viento en tramos.")
p(f"**Qué variables usa más.** Importancia por permutación: se desordena una variable en la validación y se mira cuánto sube el "
  f"MAE. Las tres primeras son {', '.join(f'{NOMBRE_VAR[v]} (+{es(imp[v])})' for v in top)} µg/m³.")
p("**Cómo se calcula el efecto:**")
ul("Se entrena el modelo con todas las horas de antes de la ZBE, de dentro y de fuera.",
   "Para cada hora después de la ZBE, predice el NO₂ de cada estación con el tiempo y el calendario de esa hora.",
   "Diferencia = NO₂ observado − NO₂ predicho, y efecto = diferencia media dentro − diferencia media fuera. Se resta la de fuera "
   "porque el modelo no conoce la renovación de coches ni otros cambios de toda la comarca, que aparecen también fuera.",
   "Intervalo del 95 %: se agrupan las horas por semanas y se repite el cálculo sorteando semanas (bootstrap). Si el intervalo "
   "incluye el cero, el resultado es **no concluyente**.")
p(f"**Resultado:** diferencia dentro {es(ef['diferencia_dentro'])}, fuera {es(ef['diferencia_fuera'])}; efecto = "
  f"{es(ef['diferencia_dentro'])} − ({es(ef['diferencia_fuera'])}) = **{es(ef['efecto_neto'])} µg/m³** (de {es(ef['ic95_inf'])} a "
  f"{es(ef['ic95_sup'])}; {es(ef['efecto_neto'] / p1['dentro_pre'] * 100, 1)} % del nivel de antes). *Qué significa:* descontado el "
  "tiempo atmosférico y lo que pasó fuera, el NO₂ bajó dentro algo más que fuera. El efecto es pequeño: menor que el que da la "
  f"comparación de medias del informe de análisis (DiD, {es(p1['efecto_neto_did'])}). **Por qué el modelo da menos:** DiD resta "
  "medias y no descuenta el tiempo atmosférico; el modelo predice cada hora con el tiempo que hizo de verdad y sí lo descuenta. "
  "La parte de la bajada que DiD atribuye a la ZBE y el modelo no es la que el modelo explica con el tiempo atmosférico. Se puede medir aunque el error por hora sea de "
  f"{es(met[el]['mae_val'])} porque es la media de {es(ef['horas_despues'], 0)} horas-estación, y los errores hacia arriba y "
  "hacia abajo se compensan.")

# 6 ---------------------------------------------------------------------------
h("6. Cómo funciona la solución")
tabla(["1. Datos", "2. Modelo", "3. Resultado", "4. Decisión y acción"], [[
    "NO₂ horario (Gobierno Vasco), tiempo atmosférico (Open-Meteo) y calendario, limpios y unidos por hora.",
    f"{el} entrenado antes de la ZBE; predice el NO₂ sin ZBE en cada estación.",
    "Efecto = (observado − predicho) dentro − fuera, con intervalo y placebo.",
    "Ampliar, mantener o ajustar la ZBE. Panel de Grafana para seguirlo.",
]], [4, 4, 4, 4])
p("Cada flecha es un paso automático: los datos los descarga y limpia un script, el notebook calcula y guarda las cifras en "
  "resultados.json, y este documento y el informe se generan desde ese fichero.")

# 7 ---------------------------------------------------------------------------
h("7. Impacto: indicadores medibles")
tabla(["Indicador", "Cómo se mide", "Valor"], [
    ["Horas de trabajo manual para actualizar el análisis",
     "Horas de una persona para actualizar el análisis con datos nuevos: a mano (descargar, limpiar y calcular) frente a con "
     "el notebook (un comando). Se cronometran las dos formas.",
     "A medir en la puesta en marcha."],
    ["Tiempo hasta tener el panel actualizado", "Frecuencia de ingesta de Node-RED en InfluxDB.",
     f"Tiempo atmosférico cada {min_meteo} min y tráfico cada {min_trafico} min. Calidad del aire oficial: según publique el "
     "Gobierno Vasco [PENDIENTE DE VERIFICAR]."],
    ["Error del modelo", "MAE en validación cada vez que se reentrena.",
     f"{es(met[el]['mae_val'])} µg/m³ (base sin IA: {es(met[BASE]['mae_val'])}). Debe seguir por debajo de la base."],
    ["Horas al año por encima de 200 µg/m³", "Contar horas-estación con NO₂ > 200.",
     f"0 en todos los años de {min(horas_200)} a {max(horas_200)}; máximo horario {es(m['no2_max_horario'], 0)} µg/m³."],
    ["Efecto de la ZBE", "Repetir el apartado 5 con cada año de datos nuevos.",
     f"{es(ef['efecto_neto'])} µg/m³ (de {es(ef['ic95_inf'])} a {es(ef['ic95_sup'])})."],
], [5, 6, 7])

# 8 ---------------------------------------------------------------------------
h("8. Ventajas, limitaciones y riesgos de la solución")
p("Se refieren a la solución propuesta: el modelo más la comparación con las estaciones de fuera.")
p("**Ventajas**")
ul(f"Descuenta el tiempo atmosférico hora a hora; el viento es la variable que más pesa (+{es(imp['viento_ms'])} µg/m³ de error si se desordena).",
   f"Descuenta lo que pasa en toda la comarca: el modelo también se pasa fuera ({es(ef['diferencia_fuera'])}), y eso se resta.",
   "Se puede comprobar: validación temporal y placebo con su resultado.",
   "Se repite con un comando sobre los mismos datos que el informe de análisis; no trata datos personales.")
p("**Limitaciones**")
ul(f"El modelo explica el {es(met[el]['r2_val'] * 100, 0)} % de la variación hora a hora; el resto es ruido.",
   f"Solo hay {len(dentro)} estaciones dentro de la ZBE.",
   "Las estaciones miden la concentración en el aire, no lo que emiten los coches.",
   "El tamaño del efecto depende del método (ver riesgos).")
p("**Riesgos, cómo se miden y resultado**")
tabla(["Riesgo", "Comprobación", "Resultado"], [
    ["Atribuir a la ZBE un cambio que no es suyo",
     "Placebo: repetir el cálculo con una ZBE ficticia el 15/06/2023, con datos de antes de la real. Debería dar cero.",
     f"{es(pl['efecto_neto'], signo=True)} (de {es(pl['ic95_inf'])} a {es(pl['ic95_sup'], signo=True)}): incluye el cero, pero se "
     f"aleja de cero tanto como el efecto real ({es(ef['efecto_neto'])}). El efecto se da como pequeño y con cautela."],
    ["Que baje todo el aire, no solo el del tráfico", "SO₂, que no viene del tráfico.",
     f"{es(p4['efecto_neto'], signo=True)} (de {es(p4['ic95_inf'])} a {es(p4['ic95_sup'], signo=True)}): no baja."],
    ["Sobreajuste", "MAE en entrenamiento frente a validación.",
     f"{el}: {es(met[el]['mae_ent'])} frente a {es(met[el]['mae_val'])}. Memoriza parte del entrenamiento; por eso se elige "
     "por el error en validación, que sigue siendo el menor."],
    ["Que el control no sea comparable", "Tendencia antes de la ZBE y bajada por estación.",
     f"2022→2023: {es(cambio_previo_dentro, signo=True)} dentro, {es(cambio_previo_fuera, signo=True)} fuera. {control_min} baja un "
     f"{es(abs(est[control_min]['var_post_vs_previo_pct']), 1)} %, más que las de dentro; causa [PENDIENTE DE VERIFICAR POR EL EQUIPO]."],
    ["Que el resultado dependa del método", "Comparar con la resta de medias (DiD) del informe de análisis.",
     f"Modelo {es(ef['efecto_neto'])}; DiD {es(p1['efecto_neto_did'])} (de {es(p1['ic95_inf'])} a {es(p1['ic95_sup'])}). Los dos "
     "bajan, pero sus intervalos no se solapan: el tamaño exacto es incierto. La diferencia viene de que el modelo descuenta "
     "el tiempo atmosférico y DiD no."],
], [4, 6, 8])
p("**Por qué DiD no es el modelo principal.** DiD solo resta medias: no descuenta el tiempo hora a hora. Si después de la ZBE "
  "hubiera hecho más viento en el centro que fuera, lo contaría como efecto de la ZBE. Se mantiene como comprobación porque es "
  "simple y no depende de ningún modelo: si los dos métodos dan una bajada, la dirección del resultado no depende del método elegido.")
p("**Qué significa para la decisión**")
ul(f"**Mantener la ZBE:** los dos métodos dan una bajada dentro mayor que fuera ({es(ef['efecto_neto'])} y {es(p1['efecto_neto_did'])} µg/m³).",
   f"**No ampliar todavía:** el efecto es pequeño y la fase 2 no añade una bajada distinguible de cero ({es(f2['efecto_neto'])}; de "
   f"{es(f2['ic95_inf'])} a {es(f2['ic95_sup'], signo=True)}).",
   "**Ajustar la medición:** más puntos de medida dentro de la ZBE reducirían el margen de error. Repetir el cálculo cada año.")

h("Fuentes")
ul("[1] Grange, S. K. y Carslaw, D. C. (2019). Using meteorological normalisation to detect interventions in air quality time "
   "series. *Science of the Total Environment*, 653, 578-588.",
   "[2] Tong, C., Dai, Y., Cole, M., Elliott, R. J. R., Bartington, S. E., Liu, B. y Shi, Z. (2025). Further improvement in "
   "London's air quality demands more than the Ultra Low Emission Zone policy. *npj Clean Air*, 1, 29. "
   "doi:10.1038/s44407-025-00030-9.",
   "[3] Toutouh, J., Lebrusán, I. y Nesmachnow, S. (2020). Computational Intelligence for Evaluating the Air Quality in the "
   "Center of Madrid, Spain. En *Optimization and Learning (OLA 2020)*, Communications in Computer and Information Science, "
   "vol. 1173. Springer.",
   "[4] Bertrand, J.-M., Meleux, F., Ung, A., Descombes, G. y Colette, A. (2023). Technical note: Improving the European air "
   "quality forecast of the Copernicus Atmosphere Monitoring Service using machine learning techniques. *Atmospheric Chemistry "
   "and Physics*, 23, 5317-5333.",
   "[5] Ciudad de Boston. Project Green Light: Saving You Time On The Road. https://www.boston.gov/node/16372851",
   "[6] Ayuntamiento de Madrid (2015). Protocolo de medidas a adoptar durante episodios de alta contaminación por dióxido de "
   "nitrógeno en la ciudad de Madrid. "
   "https://www.madrid.es/UnidadWeb/UGNormativas/Normativa/2015/ficheros/AnexoProtocoloContaminacion.pdf",
   "Directiva 2008/50/CE del Parlamento Europeo y del Consejo, relativa a la calidad del aire ambiente y a una atmósfera más "
   "limpia en Europa.")


if __name__ == "__main__":
    (DIR_DOCS / "propuesta-modelo-ia.md").write_text(
        a_markdown(B, portada, NOMBRE, "docs/generar_mia.py"), encoding="utf-8")
    print("[OK] docs/propuesta-modelo-ia.md")
    if "--solo-md" not in sys.argv:
        docx, pdf = a_word(a_html(B, portada), NOMBRE)
        print(f"[OK] docs/{docx.name} y docs/{pdf.name}")
