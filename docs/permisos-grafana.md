# Permisos de Grafana

Los usuarios, los equipos y los permisos los crea `grafana/provisioning/access-control/setup-access.sh` cada vez que arranca Grafana. La contraseña de cada usuario es `GRAFANA_DEFAULT_PASSWORD` (del `.env`) seguida del sufijo de la tabla.

## Qué ve y qué edita cada usuario

| Usuario | Sufijo | Equipo | Rol en la organización | Dashboards que ve | Puede editar | Dashboard de inicio |
|---|---|---|---|---|---|---|
| `directora`, `ceo`, `coo`, `cfo` | `dir`, `ceo`, `coo`, `cfo` | Dirección | Viewer | Monitor ZBE (`haizelab-overview`) y Análisis ZBE (`haizelab-analisis`) | No | Monitor ZBE |
| `analista1` … `analista6` | `a1` … `a6` | Análisis | Viewer | Solo Análisis ZBE | No | Análisis ZBE |
| `it_admin1` | `it1` | IT | Admin | Los dos | Sí, y también fuentes de datos, usuarios y alertas | Monitor ZBE |
| `it_admin2`, `it_admin3` | `it2`, `it3` | IT | Editor | Los dos | Sí (dashboards y alertas) | Monitor ZBE |

`admin` es el administrador de Grafana (contraseña `GF_SECURITY_ADMIN_PASSWORD` o, si no está, `INFLUXDB_ADMIN_PASSWORD`). Grafana lo añade a los tres equipos al crearlos, así que su dashboard de inicio es el de Análisis.

## Cómo se consigue

| Pieza | Qué hace |
|---|---|
| Carpetas | Cada dashboard está en su carpeta: Monitor ZBE en **Dirección** y Análisis ZBE en **Análisis** (`grafana/provisioning/dashboards/dashboards.yaml`). |
| Permisos de carpeta | **Dirección:** ver para el equipo Dirección y editar para el equipo IT. **Análisis:** ver para Dirección y Análisis, y editar para IT. Al fijar estos permisos se quitan los que Grafana da por defecto a todos los Viewer y Editor, por eso un analista no ve la carpeta Dirección. |
| Rol en la organización | Viewer no puede crear ni editar dashboards. Editor y Admin sí. |
| Dashboard de inicio | Preferencia del equipo: Dirección → `haizelab-overview`, Análisis → `haizelab-analisis`. IT usa el inicio por defecto de Grafana, que es el Monitor ZBE. |

## Cómo comprobarlo usuario por usuario

Para cada usuario de la tabla:

1. Entrar en http://localhost:3000 con su usuario (no con el correo) y su contraseña.
2. **Inicio:** la primera pantalla debe ser el dashboard de inicio de la tabla.
3. **Lo que ve:** en *Dashboards* deben aparecer solo los dashboards de la columna «Dashboards que ve». Un analista solo ve la carpeta Análisis.
4. **Si puede editar:** abrir un dashboard. Si no puede editar, no aparece el botón *Edit* y no puede guardar. Si puede, aparece *Edit*.
5. **Crear:** solo IT ve *New → New dashboard*.

También se puede comprobar por API, sin entrar en la web. Por ejemplo, para un analista con `GRAFANA_DEFAULT_PASSWORD=admin`:

```bash
curl -s -u analista1:admina1 "http://127.0.0.1:3000/api/search?type=dash-db"        # solo haizelab-analisis
curl -s -u analista1:admina1 http://127.0.0.1:3000/api/dashboards/uid/haizelab-analisis   # "canSave": false
curl -s -u analista1:admina1 http://127.0.0.1:3000/api/dashboards/home                  # redirige a haizelab-analisis
```

## Resultado de la comprobación (21/10/2026)

Comprobado por API para los 14 usuarios y `admin`, después de `docker compose down -v` y `docker compose up -d --build`:

| Usuarios | Ve | Edita | Inicio | Crea dashboards |
|---|---|---|---|---|
| `directora`, `ceo`, `coo`, `cfo` | Monitor ZBE y Análisis ZBE | Ninguno | Monitor ZBE | No |
| `analista1` … `analista6` | Análisis ZBE | Ninguno | Análisis ZBE | No |
| `it_admin1`, `it_admin2`, `it_admin3` | Monitor ZBE y Análisis ZBE | Los dos | Monitor ZBE | Sí |

Coincide con lo que se pide: Dirección ve todo y no edita; Análisis solo ve su dashboard y entra directo en él; IT ve y edita todo.
