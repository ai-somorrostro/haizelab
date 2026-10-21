# Alertas de Grafana

Las reglas están en `grafana/provisioning/alerting/alerting.yaml` y Grafana las carga al arrancar, en la carpeta **HaizeLab Alertas**. Se ven en *Alerting → Alert rules*.

## Límites de referencia del NO₂

| Valor | Qué es | Cómo se usa aquí |
|---|---|---|
| 200 µg/m³ | Límite **horario** de la UE (Directiva 2008/50/CE) | Alerta: un solo valor horario por encima ya es una superación. |
| 40 µg/m³ | Límite de la **media anual** de la UE (Directiva 2008/50/CE) | No es una alerta. Una hora por encima de 40 no incumple nada; solo se puede comparar con la media de un año entero. |
| 25 µg/m³ | Nivel de la guía **diaria** (24 horas) de la OMS [1] | Aviso preventivo con la media de las últimas 24 horas. No es un límite legal, y la propia guía admite 3-4 días al año por encima (es un percentil 99). |

## Reglas

| Regla | Qué mide | Umbral | Ventana | `for` | Evaluación | Gravedad | Si no hay datos |
|---|---|---|---|---|---|---|---|
| NO₂ — Valor horario por encima del límite horario | El valor horario más alto de cada estación entre los escritos en el último minuto | > 200 µg/m³ | Último minuto | 0 s | Cada 1 min | `critical` | OK |
| NO₂ — Aviso preventivo: media de 24 horas | Media de los últimos 24 valores horarios de cada estación | > 25 µg/m³ | Últimas 24 horas de datos | 2 min | Cada 1 min | `warning` | NoData |
| Tráfico — Congestión alta | Ocupación media de todos los tramos | > 35 % | Últimos 30 min | 10 min | Cada 2 min | `warning` | NoData |

- **Ventana:** los datos que mira la regla en cada evaluación.
- **`for`:** cuánto tiempo seguido tiene que cumplirse la condición antes de avisar. El límite horario usa 0 s porque basta un valor; el aviso de 24 horas usa 2 min para no avisar por un solo valor suelto.
- **Por estación:** las dos reglas de NO₂ dan un resultado por estación (Mazarredo, Mª Díaz de Haro, Europa y Arraiz), y el aviso dice cuál es.
- **Sin datos en la regla de 200:** si no llega ningún valor en el último minuto no hay superación, así que el estado es OK. Que Node-RED deje de escribir se ve en el aviso de 24 horas, que pasa a NoData.

**Datos de la demo.** Las reglas de NO₂ leen el bucket `aire_demo`, donde Node-RED reproduce el histórico oficial: escribe un valor horario por estación cada 5 segundos. Por eso las reglas se definen por número de valores horarios y no por tiempo de reloj: «últimas 24 horas» son los últimos 24 valores de cada estación (2 minutos de reloj), y el último minuto de reloj son 12 horas del histórico. Con datos reales de una hora cada hora, la ventana de la regla de 200 sería la última hora y la de 24 horas, el último día.

**Umbral de tráfico.** El 35 % de ocupación es un criterio propio del equipo; no viene de ninguna norma.

**Regla quitada.** Había una regla «NO₂ — Superación límite EU (> 40 µg/m³)» que comparaba la media de la última hora con 40 µg/m³. Era incorrecta: 40 es el límite de la media anual. Se borra con `deleteRules` en el mismo fichero, también en instalaciones que ya la tenían.

## Dónde se ven las alertas y a quién llegan

- **En Grafana:** siempre, en *Alerting → Alert rules*, con su estado por estación (*Normal*, *Pending*, *Firing* o *No data*).
- **Por correo:** Grafana envía cada alerta al punto de contacto `haizelab-ops`, de tipo correo, si el SMTP está configurado en el `.env`.

| Elemento | Valor |
|---|---|
| Punto de contacto | `haizelab-ops`, de tipo correo |
| Dirección de destino | Variable `ALERT_EMAIL_TO` del `.env` (en `.env.example`: `alertas@example.com`) |
| Agrupación | Por nombre de alerta y gravedad. `critical`: primer envío a los 10 s y repetición cada 15 min. `warning`: primer envío a los 30 s y repetición cada hora. |

## Cómo se configura el correo

Las direcciones y la contraseña van **solo en el `.env`**, que no se sube al repositorio. `docker-compose.yml` las pasa al contenedor de Grafana, y `alerting.yaml` toma la dirección de destino de `ALERT_EMAIL_TO`.

1. Copiar a `.env` el bloque «Alertas por correo» de `.env.example` y rellenarlo:

   | Variable | Qué es | Ejemplo |
   |---|---|---|
   | `ALERT_EMAIL_TO` | Dirección que recibe las alertas (varias, separadas por `;`) | `alertas@example.com` |
   | `GF_SMTP_ENABLED` | `true` para enviar correos | `true` |
   | `GF_SMTP_HOST` | Servidor SMTP y puerto de la cuenta que envía | `smtp.gmail.com:587` |
   | `GF_SMTP_USER` | Usuario de esa cuenta | `avisos@example.com` |
   | `GF_SMTP_PASSWORD` | Contraseña de esa cuenta; con Gmail, una contraseña de aplicación de 16 caracteres | — |
   | `GF_SMTP_FROM_ADDRESS` | Dirección que aparece como remitente | `avisos@example.com` |
   | `GF_SMTP_FROM_NAME` | Nombre del remitente (opcional) | `HaizeLab Alerting` |

2. Aplicar los cambios a Grafana (vuelve a crear el contenedor con el `.env` nuevo):
   ```bash
   docker compose up -d grafana
   ```
3. Mandar un correo de prueba: en Grafana, como `admin` o `it_admin1`, *Alerting → Contact points → haizelab-ops → Test*. Por API, la misma prueba es `POST /api/alertmanager/grafana/config/api/v1/receivers/test` con la configuración del punto de contacto.

Si `GF_SMTP_ENABLED` es `false` o faltan datos, las alertas siguen evaluándose y se ven en Grafana, pero no se envía ningún correo.

**Prueba hecha el 21/10/2026:** con el SMTP del `.env` local, la prueba del punto de contacto por API devolvió estado `ok` (Grafana dio el correo por enviado). Que llegue al buzón se comprueba en la cuenta de destino.

## Cómo comprobarlo

1. Entrar en Grafana como `it_admin1` y abrir *Alerting → Alert rules*. Deben aparecer las 3 reglas en la carpeta **HaizeLab Alertas** y ninguna de 40 µg/m³.
2. Abrir cada regla y comprobar umbral, `for` y evaluación con la tabla de arriba.
3. Pulsar *Preview* en las reglas de NO₂: sale una fila por estación con su valor.
4. En *Alerting → Contact points*, `haizelab-ops` tiene la dirección de `ALERT_EMAIL_TO`; el botón *Test* manda un correo de prueba.
5. Por API, con el usuario administrador: `curl -u admin:<contraseña> http://localhost:3000/api/v1/provisioning/alert-rules`.

## Fuentes

- Directiva 2008/50/CE del Parlamento Europeo y del Consejo, relativa a la calidad del aire ambiente y a una atmósfera más limpia en Europa (límites de NO₂: 200 µg/m³ en una hora y 40 µg/m³ de media anual).
- [1] Organización Mundial de la Salud (2021). *WHO global air quality guidelines: particulate matter (PM2.5 and PM10), ozone, nitrogen dioxide, sulfur dioxide and carbon monoxide. Executive summary*. Ginebra: OMS. ISBN 978-92-4-003443-3. Tabla 0.1: NO₂, 25 µg/m³ en 24 horas (percentil 99, es decir, 3-4 días al año por encima) y 10 µg/m³ de media anual. Publicación completa: https://www.who.int/publications/i/item/9789240034228 (ISBN 978-92-4-003422-8).
