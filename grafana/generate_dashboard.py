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
        # --- FILA 1: CALIDAD DEL AIRE ---
        {
            "collapsed": False,
            "gridPos": {"h": 1, "w": 24, "x": 0, "y": 0},
            "id": 100,
            "title": "💨 Calidad del Aire — NO₂ y Zona de Bajas Emisiones (ZBE Bilbao)",
            "type": "row"
        },
        {
            "id": 1,
            "title": "NO₂ en Tiempo Real por Estación (µg/m³)",
            "type": "gauge",
            "gridPos": {"h": 7, "w": 8, "x": 0, "y": 1},
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
            "title": "Evolución Temporal de NO₂ (Comparativa Dentro vs Fuera de la ZBE)",
            "type": "timeseries",
            "gridPos": {"h": 7, "w": 16, "x": 8, "y": 1},
            "datasource": {"type": "influxdb", "uid": "InfluxDB-HaizeLab"},
            "targets": [
                {
                    "datasource": {"type": "influxdb", "uid": "InfluxDB-HaizeLab"},
                    "query": 'from(bucket: "aire_demo")\n  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)\n  |> filter(fn: (r) => r["_measurement"] == "contaminantes")\n  |> filter(fn: (r) => r["_field"] == "no2")\n  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)\n  |> yield(name: "mean")',
                    "refId": "A"
                }
            ],
            "fieldConfig": {
                "defaults": {
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
                }
            }
        },

        # --- FILA 2: METEOROLOGIA ---
        {
            "collapsed": False,
            "gridPos": {"h": 1, "w": 24, "x": 0, "y": 8},
            "id": 200,
            "title": "🌦️ Meteorología en Tiempo Real (Open-Meteo Bilbao)",
            "type": "row"
        },
        {
            "id": 3,
            "title": "Temperatura y Humedad Relativa",
            "type": "timeseries",
            "gridPos": {"h": 7, "w": 12, "x": 0, "y": 9},
            "datasource": {"type": "influxdb", "uid": "InfluxDB-HaizeLab"},
            "targets": [
                {
                    "datasource": {"type": "influxdb", "uid": "InfluxDB-HaizeLab"},
                    "query": 'from(bucket: "meteo")\n  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)\n  |> filter(fn: (r) => r["_measurement"] == "clima")\n  |> filter(fn: (r) => r["_field"] == "temp_c" or r["_field"] == "humedad")\n  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)',
                    "refId": "A"
                }
            ],
            "fieldConfig": {
                "defaults": {
                    "custom": {
                        "drawStyle": "line",
                        "lineInterpolation": "smooth",
                        "lineWidth": 2
                    }
                },
                "overrides": [
                    {
                        "matcher": {"id": "byName", "options": "temp_c"},
                        "properties": [
                            {"id": "unit", "value": "celsius"},
                            {"id": "color", "value": {"fixedColor": "orange", "mode": "fixed"}}
                        ]
                    },
                    {
                        "matcher": {"id": "byName", "options": "humedad"},
                        "properties": [
                            {"id": "unit", "value": "percent"},
                            {"id": "color", "value": {"fixedColor": "blue", "mode": "fixed"}},
                            {"id": "custom.axisPlacement", "value": "right"}
                        ]
                    }
                ]
            }
        },
        {
            "id": 4,
            "title": "Velocidad del Viento (km/h) y Precipitación (mm)",
            "type": "timeseries",
            "gridPos": {"h": 7, "w": 12, "x": 12, "y": 9},
            "datasource": {"type": "influxdb", "uid": "InfluxDB-HaizeLab"},
            "targets": [
                {
                    "datasource": {"type": "influxdb", "uid": "InfluxDB-HaizeLab"},
                    "query": 'from(bucket: "meteo")\n  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)\n  |> filter(fn: (r) => r["_measurement"] == "clima")\n  |> filter(fn: (r) => r["_field"] == "viento_kmh" or r["_field"] == "lluvia_mm")\n  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)',
                    "refId": "A"
                }
            ],
            "fieldConfig": {
                "defaults": {
                    "custom": {"drawStyle": "line", "lineInterpolation": "smooth", "lineWidth": 2}
                },
                "overrides": [
                    {
                        "matcher": {"id": "byName", "options": "viento_kmh"},
                        "properties": [
                            {"id": "unit", "value": "velocitykmh"},
                            {"id": "color", "value": {"fixedColor": "#73BF69", "mode": "fixed"}}
                        ]
                    },
                    {
                        "matcher": {"id": "byName", "options": "lluvia_mm"},
                        "properties": [
                            {"id": "unit", "value": "lengthmm"},
                            {"id": "custom.drawStyle", "value": "bars"},
                            {"id": "custom.axisPlacement", "value": "right"},
                            {"id": "color", "value": {"fixedColor": "#5794F2", "mode": "fixed"}}
                        ]
                    }
                ]
            }
        },

        # --- FILA 3: TRAFICO ---
        {
            "collapsed": False,
            "gridPos": {"h": 1, "w": 24, "x": 0, "y": 16},
            "id": 300,
            "title": "🚗 Estado del Tráfico Urbano (Bilbao Open Data)",
            "type": "row"
        },
        {
            "id": 5,
            "title": "Intensidad Media de Tráfico (veh/h)",
            "type": "stat",
            "gridPos": {"h": 6, "w": 8, "x": 0, "y": 17},
            "datasource": {"type": "influxdb", "uid": "InfluxDB-HaizeLab"},
            "targets": [
                {
                    "datasource": {"type": "influxdb", "uid": "InfluxDB-HaizeLab"},
                    "query": 'from(bucket: "trafico")\n  |> range(start: -30m)\n  |> filter(fn: (r) => r["_measurement"] == "estado")\n  |> filter(fn: (r) => r["_field"] == "intensidad")\n  |> mean()',
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
                    "unit": "veh/h",
                    "thresholds": {
                        "mode": "absolute",
                        "steps": [
                            {"color": "green", "value": None},
                            {"color": "orange", "value": 500},
                            {"color": "red", "value": 1200}
                        ]
                    }
                }
            }
        },
        {
            "id": 6,
            "title": "Ocupación de Vías (%) y Velocidad Media (km/h)",
            "type": "timeseries",
            "gridPos": {"h": 6, "w": 16, "x": 8, "y": 17},
            "datasource": {"type": "influxdb", "uid": "InfluxDB-HaizeLab"},
            "targets": [
                {
                    "datasource": {"type": "influxdb", "uid": "InfluxDB-HaizeLab"},
                    "query": 'from(bucket: "trafico")\n  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)\n  |> filter(fn: (r) => r["_measurement"] == "estado")\n  |> filter(fn: (r) => r["_field"] == "ocupacion" or r["_field"] == "velocidad")\n  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)',
                    "refId": "A"
                }
            ],
            "fieldConfig": {
                "defaults": {
                    "custom": {"drawStyle": "line", "lineInterpolation": "smooth", "lineWidth": 2}
                },
                "overrides": [
                    {
                        "matcher": {"id": "byName", "options": "ocupacion"},
                        "properties": [
                            {"id": "unit", "value": "percent"},
                            {"id": "color", "value": {"fixedColor": "#F2495C", "mode": "fixed"}}
                        ]
                    },
                    {
                        "matcher": {"id": "byName", "options": "velocidad"},
                        "properties": [
                            {"id": "unit", "value": "velocitykmh"},
                            {"id": "color", "value": {"fixedColor": "#5794F2", "mode": "fixed"}},
                            {"id": "custom.axisPlacement", "value": "right"}
                        ]
                    }
                ]
            }
        }
    ],
    "refresh": "5s",
    "schemaVersion": 39,
    "tags": ["haizelab", "zbe", "bilbao", "no2", "meteo", "trafico"],
    "time": {"from": "now-1h", "to": "now"},
    "timepicker": {"refresh_intervals": ["5s", "10s", "30s", "1m", "5m"]},
    "timezone": "browser",
    "title": "HaizeLab — Monitor ZBE Bilbao en Tiempo Real",
    "uid": "haizelab-overview",
    "version": 1
}

dest_dir = Path("grafana/dashboards")
dest_dir.mkdir(parents=True, exist_ok=True)
dest_file = dest_dir / "haizelab-overview.json"
with open(dest_file, "w", encoding="utf-8") as f:
    json.dump(dashboard, f, indent=2, ensure_ascii=False)
print("Dashboard generado:", dest_file)
