import json

flows = []

# Nodo de configuracion InfluxDB 2.0 (token via msg.token override)
CFG = 'influx_cfg_haizelab'
flows.append({
    'id': CFG, 'type': 'influxdb', 'name': 'InfluxDB-HaizeLab',
    'hostname': '127.0.0.1', 'port': '8086', 'database': '',
    'usetls': False, 'tls': '', 'influxdbVersion': '2.0',
    'url': 'http://influxdb:8086', 'rejectUnauthorized': True
})

# --- FLUJO METEO ---
T1 = 'tab_meteo'
flows.append({'id': T1, 'type': 'tab', 'label': 'meteo', 'disabled': False})
flows.append({'id': 'inj_meteo', 'type': 'inject', 'z': T1,
    'name': 'Cada 15 min', 'props': [{'p': 'payload'}],
    'repeat': '900', 'once': True, 'onceDelay': '3',
    'payload': '', 'payloadType': 'date', 'wires': [['fn_meteo_url']],
    'x': 160, 'y': 160})

FUNC_METEO_URL = """msg.url = 'https://api.open-meteo.com/v1/forecast?latitude=43.263&longitude=-2.935&current=temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m,wind_direction_10m&wind_speed_unit=kmh&timezone=Europe%2FMadrid';
return msg;"""
flows.append({'id': 'fn_meteo_url', 'type': 'function', 'z': T1,
    'name': 'URL Open-Meteo', 'func': FUNC_METEO_URL,
    'outputs': 1, 'noerr': 0, 'initialize': '', 'finalize': '',
    'wires': [['req_meteo']],
    'x': 360, 'y': 160})
flows.append({'id': 'req_meteo', 'type': 'http request', 'z': T1,
    'name': 'GET Open-Meteo', 'method': 'GET', 'ret': 'obj',
    'paytoqs': 'ignore', 'url': '', 'tls': '', 'persist': False,
    'wires': [['fn_meteo_parse']],
    'x': 580, 'y': 160})

FUNC_METEO_PARSE = """try {
    var p = msg.payload;
    if (!p || !p.current) { node.warn('[meteo] Sin current. Status:'+msg.statusCode); return null; }
    var c = p.current;
    if (c.temperature_2m === undefined || c.wind_speed_10m === undefined) {
        node.warn('[meteo] Campos faltantes: '+JSON.stringify(c)); return null;
    }
    msg.payload = [{
        measurement: 'clima',
        tags: {ubicacion:'bilbao', fuente:'open-meteo'},
        fields: {temp_c:parseFloat(c.temperature_2m), viento_kmh:parseFloat(c.wind_speed_10m),
                 viento_dir:parseFloat(c.wind_direction_10m), lluvia_mm:parseFloat(c.precipitation),
                 humedad:parseFloat(c.relative_humidity_2m)},
        timestamp: new Date()
    }];
    msg.token  = env.get('INFLUXDB_NODERED_WRITE_TOKEN');
    msg.bucket = 'meteo';
    msg.org    = env.get('INFLUXDB_ORG');
    node.status({fill:'green',shape:'dot',text:c.temperature_2m+'C '+c.wind_speed_10m+'km/h'});
    return msg;
} catch(e) { node.warn('[meteo] Error:'+e.message); node.status({fill:'red',shape:'ring',text:'error'}); return null; }"""
flows.append({'id': 'fn_meteo_parse', 'type': 'function', 'z': T1,
    'name': 'Parsear meteo', 'func': FUNC_METEO_PARSE,
    'outputs': 1, 'noerr': 0, 'initialize': '', 'finalize': '',
    'wires': [['out_meteo']],
    'x': 800, 'y': 160})
flows.append({'id': 'out_meteo', 'type': 'influxdb batch', 'z': T1,
    'influxdb': CFG, 'name': 'Escribir > meteo',
    'precision': 'ms', 'retentionPolicy': '', 'database': 'meteo',
    'precisionV18FluxV20': 'ms', 'retentionPolicyV18Flux': '',
    'org': 'haizenlab', 'bucket': 'meteo', 'wires': [],
    'x': 1020, 'y': 160})
flows.append({'id': 'catch_meteo', 'type': 'catch', 'z': T1,
    'name': 'Catch meteo', 'scope': ['out_meteo', 'req_meteo'],
    'uncaught': False, 'wires': [['dbg_meteo']],
    'x': 800, 'y': 280})
flows.append({'id': 'dbg_meteo', 'type': 'debug', 'z': T1,
    'name': 'Log error meteo', 'active': True, 'tosidebar': True, 'console': True,
    'complete': 'true', 'targetType': 'full', 'wires': [],
    'x': 1020, 'y': 280})

# --- FLUJO TRAFICO ---
T2 = 'tab_trafico'
flows.append({'id': T2, 'type': 'tab', 'label': 'trafico', 'disabled': False})
flows.append({'id': 'inj_trafico', 'type': 'inject', 'z': T2,
    'name': 'Cada 5 min', 'props': [{'p': 'payload'}],
    'repeat': '300', 'once': True, 'onceDelay': '5',
    'payload': '', 'payloadType': 'date', 'wires': [['req_trafico']],
    'x': 160, 'y': 160})
flows.append({'id': 'req_trafico', 'type': 'http request', 'z': T2,
    'name': 'GET Trafico GeoJSON', 'method': 'GET', 'ret': 'obj',
    'paytoqs': 'ignore',
    'url': 'https://www.bilbao.eus/aytoonline/srvDatasetTrafico?formato=geojson',
    'tls': '', 'persist': False, 'wires': [['fn_trafico_parse']],
    'x': 380, 'y': 160})

FUNC_TRAFICO = """try {
    var geo = msg.payload;
    if (!geo || !geo.features || geo.features.length === 0) {
        node.warn('[trafico] Respuesta sin features. Status:'+msg.statusCode);
        node.status({fill:'red',shape:'ring',text:'sin datos'}); return null;
    }
    var ahora = new Date();
    var puntos = [];
    geo.features.forEach(function(f) {
        var p = f.properties;
        if (!p || !p.CodigoSeccion) return;
        puntos.push({
            measurement: 'estado',
            tags: {codigo_seccion: String(p.CodigoSeccion)},
            fields: {intensidad: parseInt(p.Intensidad)||0,
                     ocupacion:  parseInt(p.Ocupacion)||0,
                     velocidad:  parseInt(p.Velocidad)||0},
            timestamp: ahora
        });
    });
    if (puntos.length === 0) { node.warn('[trafico] Sin puntos'); return null; }
    msg.payload = puntos;
    msg.token  = env.get('INFLUXDB_NODERED_WRITE_TOKEN');
    msg.bucket = 'trafico';
    msg.org    = env.get('INFLUXDB_ORG');
    node.status({fill:'green',shape:'dot',text:puntos.length+' tramos @ '+ahora.toLocaleTimeString()});
    return msg;
} catch(e) { node.warn('[trafico] Error:'+e.message); node.status({fill:'red',shape:'ring',text:'error'}); return null; }"""
flows.append({'id': 'fn_trafico_parse', 'type': 'function', 'z': T2,
    'name': 'Parsear tramos', 'func': FUNC_TRAFICO,
    'outputs': 1, 'noerr': 0, 'initialize': '', 'finalize': '',
    'wires': [['out_trafico']],
    'x': 620, 'y': 160})
flows.append({'id': 'out_trafico', 'type': 'influxdb batch', 'z': T2,
    'influxdb': CFG, 'name': 'Escribir > trafico',
    'precision': 'ms', 'retentionPolicy': '', 'database': 'trafico',
    'precisionV18FluxV20': 'ms', 'retentionPolicyV18Flux': '',
    'org': 'haizenlab', 'bucket': 'trafico', 'wires': [],
    'x': 880, 'y': 160})
flows.append({'id': 'catch_trafico', 'type': 'catch', 'z': T2,
    'name': 'Catch trafico', 'scope': ['out_trafico', 'req_trafico'],
    'uncaught': False, 'wires': [['dbg_trafico']],
    'x': 620, 'y': 280})
flows.append({'id': 'dbg_trafico', 'type': 'debug', 'z': T2,
    'name': 'Log error trafico', 'active': True, 'tosidebar': True, 'console': True,
    'complete': 'true', 'targetType': 'full', 'wires': [],
    'x': 880, 'y': 280})

# --- FLUJO AIRE_DEMO ---
T3 = 'tab_demo'
flows.append({'id': T3, 'type': 'tab', 'label': 'aire_demo', 'disabled': False})
flows.append({'id': 'inj_demo', 'type': 'inject', 'z': T3,
    'name': 'Cada 5 s', 'props': [{'p': 'payload'}],
    'repeat': '5', 'once': True, 'onceDelay': '10',
    'payload': '', 'payloadType': 'date', 'wires': [['fn_demo']],
    'x': 160, 'y': 160})

FUNC_DEMO = """var fs = global.get('fs') || require('fs');
if (!flow.get('demo_cargado')) {
    var csvPath = env.get('AIRE_DEMO_CSV') || '/data/no2_demo_reducido.csv';
    try { var contenido = fs.readFileSync(csvPath, 'utf8'); }
    catch(e) { node.error('[aire_demo] No se puede leer '+csvPath+': '+e.message); return null; }
    var lineas = contenido.trim().split('\\n');
    var cab = lineas[0].split(',').map(function(c) { return c.trim(); });
    var iTs = cab.indexOf('ts'), iEst = cab.indexOf('estacion'), iZon = cab.indexOf('zona'), iNo2 = cab.indexOf('no2');
    var porTs = {};
    for (var i = 1; i < lineas.length; i++) {
        var linea = lineas[i].trim();
        if (!linea) continue;
        var cols = linea.split(',').map(function(c) { return c.trim(); });
        var ts = cols[iTs] || '';
        if (!ts) continue;
        var n = parseFloat(cols[iNo2]);
        if (isNaN(n)) continue;
        if (!porTs[ts]) porTs[ts] = [];
        porTs[ts].push({estacion: cols[iEst] || '', zona: cols[iZon] || '', no2: n});
    }
    var ticks = Object.keys(porTs).sort();
    flow.set('demo_por_ts', porTs); flow.set('demo_ticks', ticks);
    flow.set('demo_idx', 0); flow.set('demo_cargado', true);
    node.log('[aire_demo] CSV cargado: '+ticks.length+' ticks');
}
var porTs = flow.get('demo_por_ts'), ticks = flow.get('demo_ticks');
if (!ticks || ticks.length === 0) {
    node.warn('[aire_demo] No hay ticks disponibles'); return null;
}
var idx = parseInt(flow.get('demo_idx')) || 0;
if (idx >= ticks.length) { idx = 0; node.warn('[aire_demo] Reiniciando historico'); }
var tsOrig = ticks[idx], filas = porTs[tsOrig];
flow.set('demo_idx', idx + 1);
if (!filas || filas.length === 0) {
    node.warn('[aire_demo] Sin filas para tick: '+tsOrig); return null;
}
var ahora = new Date();
var puntos = filas.map(function(f) {
    return {measurement: 'contaminantes', tags: {estacion: f.estacion, zona: f.zona},
            fields: {no2: f.no2, fecha_original: tsOrig}, timestamp: ahora};
});
msg.payload = puntos;
msg.token  = env.get('INFLUXDB_NODERED_WRITE_TOKEN');
msg.bucket = 'aire_demo';
msg.org    = env.get('INFLUXDB_ORG');
node.status({fill:'green', shape:'dot', text:(idx+1)+'/'+ticks.length+' | '+tsOrig.substring(0,16)});
return msg;"""
flows.append({'id': 'fn_demo', 'type': 'function', 'z': T3,
    'name': 'Siguiente hora NO2', 'func': FUNC_DEMO,
    'outputs': 1, 'noerr': 0, 'initialize': '', 'finalize': '',
    'wires': [['out_demo']],
    'x': 400, 'y': 160})
flows.append({'id': 'out_demo', 'type': 'influxdb batch', 'z': T3,
    'influxdb': CFG, 'name': 'Escribir > aire_demo',
    'precision': 'ms', 'retentionPolicy': '', 'database': 'aire_demo',
    'precisionV18FluxV20': 'ms', 'retentionPolicyV18Flux': '',
    'org': 'haizenlab', 'bucket': 'aire_demo', 'wires': [],
    'x': 680, 'y': 160})
flows.append({'id': 'catch_demo', 'type': 'catch', 'z': T3,
    'name': 'Catch aire_demo', 'scope': ['out_demo'],
    'uncaught': False, 'wires': [['dbg_demo']],
    'x': 400, 'y': 280})
flows.append({'id': 'dbg_demo', 'type': 'debug', 'z': T3,
    'name': 'Log error demo', 'active': True, 'tosidebar': True, 'console': True,
    'complete': 'true', 'targetType': 'full', 'wires': [],
    'x': 680, 'y': 280})

from pathlib import Path
ruta_flows = Path(__file__).resolve().parent / 'flows.json'
with open(ruta_flows, 'w', encoding='utf-8') as f:
    json.dump(flows, f, ensure_ascii=False, indent=2)
print('OK:', len(flows), 'nodos')