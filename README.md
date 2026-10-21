# HaizeLab

Evaluación del efecto de la Zona de Bajas Emisiones (ZBE) de Bilbao sobre el NO₂, para que el Ayuntamiento decida si **amplía, mantiene o ajusta la ZBE**. Compara dos estaciones de dentro de la ZBE con cinco de fuera, con datos horarios del 01/01/2022 al 30/09/2026.

## Resultado principal

Cifras en µg/m³, tomadas de `resultados/resultados.json`. **Efecto neto** = lo que bajó el NO₂ dentro menos lo que bajó fuera (diferencias en diferencias, un método estadístico); entre paréntesis, el intervalo del 95 %.

- **P1. Efecto neto: −1,63** (de −2,38 a −0,94); en horario de la ZBE, −2,93. Dentro bajó más que fuera y no se explica por el azar.
- **P5. Fase 2 frente a fase 1: −0,52** (de −1,72 a 0,74). La bajada llegó sobre todo con la fase 1; la fase 2 no añade una bajada distinguible de cero.
- **Comprobación con SO₂: 0,33** (de −0,01 a 0,66). El SO₂ no viene del tráfico y no baja más dentro que fuera: el método no inventa efectos donde la ZBE no actúa.
- **Modelo de IA (Random Forest): −0,49** (de −0,86 a −0,12), con un error medio de 8,14 por hora. Confirma la dirección; el tamaño exacto depende del método.

Desarrollo completo: [informe para el cliente](docs/informe-cliente-sbd.md) y [propuesta de modelo de IA (MIA)](docs/propuesta-modelo-ia.md).

## Arquitectura

![Arquitectura de HaizeLab](docs/img/arquitectura_haizelab.png)

| Servicio | Puerto | Función |
|---|---:|---|
| `influxdb` | 8086 | Base de datos de series temporales |
| `nodered` | 1880 | Automatización: recoge datos y los escribe en InfluxDB |
| `grafana` | 3000 | Paneles, alertas y permisos |
| `influx-mcp` | 5001 | Servidor MCP de solo lectura |
| `chatbot` | 8000 | Responde con las cifras de `resultados.json` |
| `presentacion` | 8080 | Presentación web |

## Arranque

```bash
git clone https://github.com/ai-somorrostro/haizelab.git
cd haizelab
cp .env.example .env              # cambiar los valores cambia_...
docker compose up -d --build
docker compose run --rm --build carga-historica   # llena el bucket aire
docker compose run --rm --build sbd-notebook      # opcional: repite el análisis
```

| Servicio | Dirección |
|---|---|
| Grafana | http://localhost:3000 |
| Node-RED | http://localhost:1880 |
| InfluxDB | http://localhost:8086 |
| Presentación | http://localhost:8080 |
| Chatbot | http://localhost:8000/docs |

Usuarios y permisos de Grafana: [docs/permisos-grafana.md](docs/permisos-grafana.md).

## Estructura

- `ingesta/`: descarga, limpieza y carga del histórico en InfluxDB.
- `data/`: datos limpios que lee el notebook.
- `notebooks/`: análisis P1-P5 y anexo del modelo de IA.
- `resultados/`: `resultados.json`, única fuente de las cifras.
- `docs/`: informe, MIA, alertas, permisos y registro de mejoras.
- `influxdb/`, `nodered/`, `grafana/`: configuración de cada servicio.
- `mcp/`, `chatbot/`, `presentacion/`: código de cada servicio, con su propio README ([mcp](mcp/README.md), [chatbot](chatbot/README.md), [presentación](presentacion/README.md)).
- `scripts_check/`: `verificar_cifras.py` comprueba las cifras de los documentos.

## Autores

Alfred Gabriel (Product Owner), Iñigo Guzmán (Lead Data Engineer) y Kerman Latorre (Scrum Master).
