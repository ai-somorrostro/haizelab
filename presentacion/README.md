# Presentación Haizen Lab · Reto 0

Versión web de la presentación: un `index.html` y la carpeta `assets/`, sin dependencias.

## Controles
- `→` / `Espacio` / `AvPág`: siguiente diapositiva. `←` / `RePág`: la anterior.
- `Inicio` / `Fin`: primera y última diapositiva.
- `F`: pantalla completa.
- `G`: en la diapositiva 10, Grafana a pantalla completa. `Esc` para salir.
- `#n` en la URL abre la diapositiva n (por ejemplo `/#10`).

## Grafana en directo (diapositiva 10)
- Por defecto carga `http://localhost:3000/d/<uid>?orgId=1&kiosk&refresh=5s`.
- Otra URL de Grafana: `?grafana=http://IP:3000`.
- Botones: Monitor (`haizelab-overview`), Análisis (`haizelab-analisis`), ↻ recargar, ⤢ pantalla completa.
- Si Grafana no responde en 2,5 s, se muestra la captura de respaldo.
