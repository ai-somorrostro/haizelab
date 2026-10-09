# HaizeLab: Monitorización y Análisis Multivariable de la ZBE de Bilbao

> **Evaluación econométrica del impacto de la Zona de Bajas Emisiones (ZBE) en la calidad del aire de Bilbao (2022-2026).**  
> Reto 0 ("HERE WE GO") — Centro de Formación Somorrostro | Especialización en Inteligencia Artificial y Big Data.  
> **Equipo HaizeLab:** Alfred Gabriel (PO / PIA), Iñigo Guzman (Lead Data Engineer / BDA), Kerman Irusta (SM / MIA).

---

## 🎯 Veredicto Ejecutivo del Reto 0

El análisis econométrico cuasiexperimental de **Diferencias en Diferencias (Diff-in-Diff)** sobre más de **41.700 horas de datos** (2022-2026), aislando la meteorología (viento, temperatura, lluvia) y la tendencia macro mediante 6 estaciones de control, concluye:

* **Efecto Causal Neto de la ZBE**: **-1,63 µg/m³ de NO₂** (**-6,4%**) estadísticamente significativo ($p < 0,001$).
* **Filtro de Calma Atmosférica**: La reducción neta asciende a **-2,84 µg/m³** en episodios sin dispersión por viento.
* **Aforos de Tráfico**: Caída inmediata del **-15,3%** en accesos principales (San Mamés) tras la implantación.
* **Test de Placebo ($SO_2$)**: Cambio de **+0,08 µg/m³** ($p = 0,72$), confirmando que la caída de $NO_2$ responde a la restricción vehicular y no a artefactos estadísticos.

---

## 🏗️ Arquitectura del Sistema

El ecosistema integra dos pilares sincronizados:

1. **Pipeline Analítico y Causal**: Ingesta reproducible (Open-Meteo, Open Data Euskadi, Bizkaia Aforos), tratamiento en Pandas y contrastes econométricos.
2. **Plataforma de Streaming y Monitorización**:
   - **InfluxDB 2.9**: Almacenamiento optimizado de series temporales (`aire`, `meteo`, `trafico`, `kpis`).
   - **Node-RED 5.0**: Orquestación y flujos continuos de ingesta.
   - **Grafana 11.2**: Cuadros de mando con RBAC, alertas oficiales (OMS/UE) y dashboards públicos.
   - **HaizeLab Assistant (FastAPI + RAG Local)**: Chatbot local con motor RAG, blindaje anti prompt-injection y soporte `file:///`.
   - **Cloudflare Tunnels**: Cifrado TLS de extremo a extremo sin exponer puertos en el router.

```
[Fuentes Abiertas: Euskadi / Bizkaia / Meteo] 
       │
       ▼
  [Node-RED 5.0] ──> [InfluxDB 2.9] <── [MCP Server (IA)]
                            │
              ┌─────────────┴─────────────┐
              ▼                           ▼
       [Grafana 11.2]             [Chatbot API (FastAPI)]
              │                           │
              └─────────────┬─────────────┘
                            ▼
                [Cloudflare Tunnels TLS]
                            ▼
          [Presentación Web / Cuadros de Mando]
```

---

## 🚀 Inicio Rápido (3 Pasos)

### 1. Variables de Entorno
Copia la plantilla de entorno y ajusta las credenciales si es necesario:
```bash
cp .env.example .env
```

### 2. Despliegue de Contenedores Docker
Levanta toda la infraestructura con un único comando:
```bash
docker compose up -d
```
Verifica el estado de los servicios:
```bash
docker compose ps
```

### 3. Abrir la Presentación y Cuadros de Mando
Puedes acceder a la presentación de tres formas:
* **Producción (Vercel)**: [haizelab-presentacion.vercel.app](https://haizelab-presentacion.vercel.app)
* **Local directo**: Abre `presentacion/index.html` con doble clic en tu navegador.
* **Servidor HTTP local**:
  ```bash
  python -m http.server 5500 --directory presentacion
  ```
  y navega a `http://localhost:5500`.

---

## 🌐 Túneles Seguros Cloudflare

Para conectar los dashboards de Grafana y el Chatbot local con la web en la nube sin problemas de CORS ni *Mixed Content*, ejecuta el script automatizado:

```powershell
.\scripts\iniciar_tuneles.ps1
```

Este script levanta los túneles para Grafana (`3000`), Influx Proxy (`8085`), Node-RED (`1880`) y Chatbot (`8000`), y actualiza automáticamente `presentacion/grafana.json`.

---

## 🔐 Matriz de Credenciales y Control de Acceso (RBAC)

| Servicio / Rol | Usuario | Contraseña / Token | Permisos |
|---|---|---|---|
| **Grafana (Viewer)** | `directora` | Configurada en `.env` | Visualización ejecutiva de dashboards |
| **Grafana (Editor)** | `analista1` ... `analista6` | Configurada en `.env` | Creación y edición de paneles y consultas |
| **Grafana (Admin)** | `it_admin1` ... `it_admin3` | Configurada en `.env` | Administración de usuarios, datasources y alertas |
| **InfluxDB** | `admin` | Configurada en `.env` | Gestión integral de buckets y tokens Flux |
| **Node-RED** | `admin` | Configurada en `.env` | Edición y despliegue de flujos de streaming |
| **MCP Server** | N/A | `mcp-read-only` | Lectura de series temporales para modelos LLM |

---

## 📁 Estructura del Repositorio

```
haizelab/
|-- chatbot/              # API FastAPI y motor RAG local (con test suite 18/18)
|-- data/                 # Datasets limpios (clean/) y brutos (raw/)
|-- docs/                 # Informes ejecutivos (Word/PDF), memorias técnicas y arquitecturas
|-- grafana/              # Dashboards JSON, políticas RBAC y provisioning de alertas
|-- influxdb/             # Scripts de inicialización y buckets de series temporales
|-- ingesta/              # Scripts de descarga, limpieza masiva y carga a InfluxDB
|-- mcp/                  # Servidor Model Context Protocol con dependencias optimizadas
|-- nodered/              # Flujos de orquestación en tiempo real (flows.json)
|-- presentacion/         # Aplicación web interactiva, diapositivas y configuración de túneles
`-- scripts/              # Pipeline analítico numerado (01 a 06) y script de túneles
```

---

## 📚 Documentación Técnica Detallada

Para consultar el desarrollo exhaustivo de cada módulo, revisa los documentos en `docs/`:

* **[Informe Ejecutivo del Cliente (SBD)](docs/informe-cliente-sbd.md)**: Memoria completa del análisis econométrico, datos y tablas oficiales.
* **[Propuesta de Modelos de IA (MIA)](docs/propuesta-modelo-ia.md)**: Diseño de modelos predictivos y arquitecturas de Machine Learning.
* **[Memoria Técnica de Infraestructura](docs/infraestructura-explicada.md)**: Configuración en detalle de InfluxDB, Node-RED, Grafana y seguridad.
* **[Organigrama de Datos](docs/organigrama-datos.md)**: Estructura de buckets, measurements, fields y tags.
