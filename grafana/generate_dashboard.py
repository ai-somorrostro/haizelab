import json
from pathlib import Path

dashboard = {
    "annotations": {"list": []},
    "editable": True,
    "fiscalYearStartMonth": 0,
    "graphTooltip": 1,
    "id": None,
    "links": [],
    "liveNow": True,
    "panels": [
        # ──────────────────────────────────────────────────────────────────────
        # FILA 1: CALIDAD DEL AIRE (ZBE BILBAO)
        # ──────────────────────────────────────────────────────────────────────
        {
            "collapsed": False,
            "gridPos": {"h": 1, "w": 24, "x": 0, "y": 0},
            "id": 100,
            "title": "💨 Calidad del Aire — NO₂ y Zona de Bajas Emisiones (ZBE Bilbao)",
            "type": "row"
        },
        {
            "id": 1,
            "title": "Concentración Actual de NO₂ por Estación",
            "description": "Umbrales según directivas de calidad del aire: Verde (< 25 µg/m³), Amarillo (25-40 µg/m³ límite OMS/UE), Rojo (> 40 µg/m³ superación).",
            "type": "gauge",
            "gridPos": {"h": 8, "w": 8, "x": 0, "y": 1},
            "datasource": {"type": "influxdb", "uid": "InfluxDB-HaizeLab"},
            "targets": [
                {
                    "datasource": {"type": "influxdb", "uid": "InfluxDB-HaizeLab"},
                    "query": 'from(bucket: "aire_demo")\n  |> range(start: -15m)\n  |> filter(fn: (r) => r["_measurement"] == "contaminantes")\n  |> filter(fn: (r) => r["_field"] == "no2")\n  |> last()',
                    "refId": "A"
                }
            ],
            "options": {
                "reduceOptions": {
                    "values": False,
                    "calcs": ["lastNotNull"],
                    "fields": ""
                },
                "showThresholdLabels": False,
                "showThresholdMarkers": True
            },
            "fieldConfig": {
                "defaults": {
                    "displayName": "${__field.labels.estacion}",
                    "unit": "µg/m³",
                    "min": 0,
                    "max": 100,
                    "thresholds": {
                        "mode": "absolute",
                        "steps": [
                            {"color": "green", "value": None},
                            {"color": "#EAB839", "value": 25},
                            {"color": "red", "value": 40}
                        ]
                    }
                },
                "overrides": []
            }
        },
        {
            "id": 2,
            "title": "Evolución Temporal de NO₂ (Dentro vs Fuera de la ZBE)",
            "description": "Comparativa en tiempo real de estaciones dentro de la ZBE (Mazarredo y Mª Díaz de Haro), fuera (Europa) y fondo natural (Arraiz).",
            "type": "timeseries",
            "gridPos": {"h": 8, "w": 16, "x": 8, "y": 1},
            "datasource": {"type": "influxdb", "uid": "InfluxDB-HaizeLab"},
            "targets": [
                {
                    "datasource": {"type": "influxdb", "uid": "InfluxDB-HaizeLab"},
                    "query": 'from(bucket: "aire_demo")\n  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)\n  |> filter(fn: (r) => r["_measurement"] == "contaminantes")\n  |> filter(fn: (r) => r["_field"] == "no2")\n  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)\n  |> yield(name: "mean")',
                    "refId": "A"
                }
            ],
            "options": {
                "legend": {
                    "calcs": ["mean", "lastNotNull"],
                    "displayMode": "table",
                    "placement": "bottom",
                    "showLegend": True
                },
                "tooltip": {
                    "mode": "multi",
                    "sort": "desc"
                }
            },
            "fieldConfig": {
                "defaults": {
                    "displayName": "${__field.labels.estacion} (${__field.labels.zona})",
                    "custom": {
                        "drawStyle": "line",
                        "lineInterpolation": "smooth",
                        "lineWidth": 2,
                        "pointSize": 5,
                        "showPoints": "auto",
                        "spanNulls": True
                    },
                    "unit": "µg/m³",
                    "thresholds": {
                        "mode": "absolute",
                        "steps": [
                            {"color": "green", "value": None},
                            {"color": "#EAB839", "value": 25},
                            {"color": "red", "value": 40}
                        ]
                    }
                },
                "overrides": [
                    {
                        "matcher": {"id": "byRegexp", "options": ".*dentro.*"},
                        "properties": [
                            {"id": "color", "value": {"fixedColor": "#F2495C", "mode": "fixed"}}
                        ]
                    },
                    {
                        "matcher": {"id": "byRegexp", "options": ".*fuera.*"},
                        "properties": [
                            {"id": "color", "value": {"fixedColor": "#FF9830", "mode": "fixed"}}
                        ]
                    },
                    {
                        "matcher": {"id": "byRegexp", "options": ".*fondo.*"},
                        "properties": [
                            {"id": "color", "value": {"fixedColor": "#73BF69", "mode": "fixed"}}
                        ]
                    }
                ]
            }
        },

        # ──────────────────────────────────────────────────────────────────────
        # FILA 2: METEOROLOGIA (OPEN-METEO BILBAO)
        # ──────────────────────────────────────────────────────────────────────
        {
            "collapsed": False,
            "gridPos": {"h": 1, "w": 24, "x": 0, "y": 9},
            "id": 200,
            "title": "🌦️ Meteorología en Tiempo Real (Bilbao — Open-Meteo)",
            "type": "row"
        },
        {
            "id": 3,
            "title": "Temperatura y Humedad Relativa",
            "type": "timeseries",
            "gridPos": {"h": 7, "w": 12, "x": 0, "y": 10},
            "datasource": {"type": "influxdb", "uid": "InfluxDB-HaizeLab"},
            "targets": [
                {
                    "datasource": {"type": "influxdb", "uid": "InfluxDB-HaizeLab"},
                    "query": 'from(bucket: "meteo")\n  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)\n  |> filter(fn: (r) => r["_measurement"] == "clima")\n  |> filter(fn: (r) => r["_field"] == "temp_c" or r["_field"] == "humedad")\n  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)',
                    "refId": "A"
                }
            ],
            "options": {
                "legend": {"displayMode": "list", "placement": "bottom"}
            },
            "fieldConfig": {
                "defaults": {
                    "custom": {
                        "drawStyle": "line",
                        "lineInterpolation": "smooth",
                        "lineWidth": 2,
                        "spanNulls": True
                    }
                },
                "overrides": [
                    {
                        "matcher": {"id": "byName", "options": "temp_c"},
                        "properties": [
                            {"id": "displayName", "value": "Temperatura (°C)"},
                            {"id": "unit", "value": "celsius"},
                            {"id": "color", "value": {"fixedColor": "#FF9830", "mode": "fixed"}}
                        ]
                    },
                    {
                        "matcher": {"id": "byName", "options": "humedad"},
                        "properties": [
                            {"id": "displayName", "value": "Humedad Relativa (%)"},
                            {"id": "unit", "value": "percent"},
                            {"id": "color", "value": {"fixedColor": "#5794F2", "mode": "fixed"}},
                            {"id": "custom.axisPlacement", "value": "right"}
                        ]
                    }
                ]
            }
        },
        {
            "id": 4,
            "title": "Velocidad del Viento y Precipitación",
            "type": "timeseries",
            "gridPos": {"h": 7, "w": 12, "x": 12, "y": 10},
            "datasource": {"type": "influxdb", "uid": "InfluxDB-HaizeLab"},
            "targets": [
                {
                    "datasource": {"type": "influxdb", "uid": "InfluxDB-HaizeLab"},
                    "query": 'from(bucket: "meteo")\n  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)\n  |> filter(fn: (r) => r["_measurement"] == "clima")\n  |> filter(fn: (r) => r["_field"] == "viento_kmh" or r["_field"] == "lluvia_mm")\n  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)',
                    "refId": "A"
                }
            ],
            "options": {
                "legend": {"displayMode": "list", "placement": "bottom"}
            },
            "fieldConfig": {
                "defaults": {
                    "custom": {"drawStyle": "line", "lineInterpolation": "smooth", "lineWidth": 2, "spanNulls": True}
                },
                "overrides": [
                    {
                        "matcher": {"id": "byName", "options": "viento_kmh"},
                        "properties": [
                            {"id": "displayName", "value": "Velocidad Viento (km/h)"},
                            {"id": "unit", "value": "velocitykmh"},
                            {"id": "color", "value": {"fixedColor": "#73BF69", "mode": "fixed"}}
                        ]
                    },
                    {
                        "matcher": {"id": "byName", "options": "lluvia_mm"},
                        "properties": [
                            {"id": "displayName", "value": "Precipitación Lluvia (mm)"},
                            {"id": "unit", "value": "lengthmm"},
                            {"id": "custom.drawStyle", "value": "bars"},
                            {"id": "custom.axisPlacement", "value": "right"},
                            {"id": "color", "value": {"fixedColor": "#5794F2", "mode": "fixed"}}
                        ]
                    }
                ]
            }
        },

        # ──────────────────────────────────────────────────────────────────────
        # FILA 3: TRAFICO (BILBAO OPEN DATA) - DISEÑO LIMPIO Y SIN SPAGHETTI
        # ──────────────────────────────────────────────────────────────────────
        {
            "collapsed": False,
            "gridPos": {"h": 1, "w": 24, "x": 0, "y": 17},
            "id": 300,
            "title": "🚗 Estado del Tráfico Urbano (Bilbao Open Data — 81 Tramos)",
            "type": "row"
        },
        {
            "id": 5,
            "title": "Intensidad Global de Tráfico",
            "description": "Volumen medio actual de vehículos por hora en los accesos y vías de Bilbao.",
            "type": "stat",
            "gridPos": {"h": 7, "w": 6, "x": 0, "y": 18},
            "datasource": {"type": "influxdb", "uid": "InfluxDB-HaizeLab"},
            "targets": [
                {
                    "datasource": {"type": "influxdb", "uid": "InfluxDB-HaizeLab"},
                    "query": 'from(bucket: "trafico")\n  |> range(start: -30m)\n  |> filter(fn: (r) => r["_measurement"] == "estado")\n  |> filter(fn: (r) => r["_field"] == "intensidad")\n  |> group()\n  |> mean()',
                    "refId": "A"
                }
            ],
            "options": {
                "colorMode": "value",
                "graphMode": "area",
                "justifyMode": "auto",
                "reduceOptions": {"calcs": ["mean"], "fields": "", "values": False}
            },
            "fieldConfig": {
                "defaults": {
                    "displayName": "Media Ciudad",
                    "unit": "veh/h",
                    "thresholds": {
                        "mode": "absolute",
                        "steps": [
                            {"color": "green", "value": None},
                            {"color": "#EAB839", "value": 500},
                            {"color": "red", "value": 1000}
                        ]
                    }
                }
            }
        },
        {
            "id": 6,
            "title": "Evolución del Tráfico: Ocupación (%) vs Velocidad (km/h)",
            "description": "Medias globales agregadas de toda la red de Bilbao. Muestra la correlación directa: a mayor ocupación, menor velocidad de circulación.",
            "type": "timeseries",
            "gridPos": {"h": 7, "w": 12, "x": 6, "y": 18},
            "datasource": {"type": "influxdb", "uid": "InfluxDB-HaizeLab"},
            "targets": [
                {
                    "datasource": {"type": "influxdb", "uid": "InfluxDB-HaizeLab"},
                    "query": 'from(bucket: "trafico")\n  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)\n  |> filter(fn: (r) => r["_measurement"] == "estado")\n  |> filter(fn: (r) => r["_field"] == "ocupacion" or r["_field"] == "velocidad")\n  |> group(columns: ["_field"])\n  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)',
                    "refId": "A"
                }
            ],
            "options": {
                "legend": {
                    "calcs": ["mean", "lastNotNull"],
                    "displayMode": "table",
                    "placement": "bottom",
                    "showLegend": True
                },
                "tooltip": {"mode": "multi", "sort": "desc"}
            },
            "fieldConfig": {
                "defaults": {
                    "custom": {
                        "drawStyle": "line",
                        "lineInterpolation": "smooth",
                        "lineWidth": 3,
                        "pointSize": 5,
                        "showPoints": "auto",
                        "spanNulls": True
                    }
                },
                "overrides": [
                    {
                        "matcher": {"id": "byName", "options": "ocupacion"},
                        "properties": [
                            {"id": "displayName", "value": "Ocupación Media Vías (%)"},
                            {"id": "unit", "value": "percent"},
                            {"id": "color", "value": {"fixedColor": "#F2495C", "mode": "fixed"}},
                            {"id": "custom.axisPlacement", "value": "left"}
                        ]
                    },
                    {
                        "matcher": {"id": "byName", "options": "velocidad"},
                        "properties": [
                            {"id": "displayName", "value": "Velocidad Media (km/h)"},
                            {"id": "unit", "value": "velocitykmh"},
                            {"id": "color", "value": {"fixedColor": "#5794F2", "mode": "fixed"}},
                            {"id": "custom.axisPlacement", "value": "right"}
                        ]
                    }
                ]
            }
        },
        {
            "id": 7,
            "title": "Top 5 Tramos con Mayor Retención",
            "description": "Tramos de Bilbao con mayor nivel de ocupación actual (en % sobre su capacidad).",
            "type": "bargauge",
            "gridPos": {"h": 7, "w": 6, "x": 18, "y": 18},
            "datasource": {"type": "influxdb", "uid": "InfluxDB-HaizeLab"},
            "targets": [
                {
                    "datasource": {"type": "influxdb", "uid": "InfluxDB-HaizeLab"},
                    "query": 'from(bucket: "trafico")\n  |> range(start: -30m)\n  |> filter(fn: (r) => r["_measurement"] == "estado")\n  |> filter(fn: (r) => r["_field"] == "ocupacion")\n  |> last()\n  |> group()\n  |> sort(columns: ["_value"], desc: true)\n  |> limit(n: 5)',
                    "refId": "A"
                }
            ],
            "options": {
                "displayMode": "gradient",
                "orientation": "horizontal",
                "reduceOptions": {
                    "calcs": ["lastNotNull"],
                    "fields": "",
                    "values": False
                },
                "showUnfilled": True
            },
            "fieldConfig": {
                "defaults": {
                    "displayName": "Tramo ${__field.labels.codigo_seccion}",
                    "min": 0,
                    "max": 100,
                    "unit": "percent",
                    "thresholds": {
                        "mode": "absolute",
                        "steps": [
                            {"color": "green", "value": None},
                            {"color": "#EAB839", "value": 20},
                            {"color": "red", "value": 35}
                        ]
                    }
                }
            }
        }
    ],
    "refresh": "5s",
    "schemaVersion": 39,
    "tags": ["haizelab", "zbe", "bilbao", "no2", "meteo", "trafico"],
    "time": {"from": "now-30m", "to": "now"},
    "timepicker": {"refresh_intervals": ["5s", "10s", "30s", "1m", "5m"]},
    "timezone": "browser",
    "title": "HaizeLab — Monitor ZBE Bilbao en Tiempo Real",
    "uid": "haizelab-overview",
    "version": 2
}

dest_dir = Path("grafana/dashboards")
dest_dir.mkdir(parents=True, exist_ok=True)
dest_file = dest_dir / "haizelab-overview.json"
with open(dest_file, "w", encoding="utf-8") as f:
    json.dump(dashboard, f, indent=2, ensure_ascii=False)
print("Dashboard actualizado con exito en:", dest_file)
