#!/bin/sh
# grafana/provisioning/access-control/setup-access.sh
# =====================================================
# Configura el control de acceso de Grafana vía API REST.
#
# Roles según requisito:
#   Directora (Viewer):          ve todo, no edita
#   Analistas 1-6 (Viewer):      ven dashboards asignados, home dashboard haizelab-analisis
#   IT Admin 1 (Admin):          administrador completo de la organización
#   IT Admin 2-3 (Editor):       editores técnicos (creación y edición de paneles)
#
# Reescrito con curl e idempotente: crea o sincroniza usuarios, contraseñas, roles y equipos.

set -eu

GRAFANA_URL="http://localhost:3000"
ADMIN_USER="${GF_SECURITY_ADMIN_USER:-${INFLUXDB_ADMIN_USER:-admin}}"
ADMIN_PASS="${GF_SECURITY_ADMIN_PASSWORD:-${INFLUXDB_ADMIN_PASSWORD:-}}"
PASS_BASE="${GRAFANA_DEFAULT_PASSWORD:-}"

# Validación estricta de secretos en entorno (sin contraseñas por defecto en el script)
if [ -z "$ADMIN_PASS" ]; then
  echo "[acceso] ERROR: Contraseña de admin no definida en variables de entorno (GF_SECURITY_ADMIN_PASSWORD / INFLUXDB_ADMIN_PASSWORD)." >&2
  exit 1
fi

if [ -z "$PASS_BASE" ]; then
  echo "[acceso] ERROR: Contraseña base no definida en variables de entorno (GRAFANA_DEFAULT_PASSWORD)." >&2
  exit 1
fi

AUTH="$ADMIN_USER:$ADMIN_PASS"

# Esperar a que la API esté lista (con timeout)
echo "[acceso] Verificando disponibilidad de la API de Grafana..."
INTENTOS=0
until curl -s "$GRAFANA_URL/api/health" 2>/dev/null | grep -Eq '"database":[[:space:]]*"ok"'; do
  sleep 2
  INTENTOS=$((INTENTOS + 1))
  if [ "$INTENTOS" -ge 20 ]; then
    echo "[acceso] ERROR: Grafana no respondió a tiempo." >&2
    exit 1
  fi
done
echo "[acceso] Grafana API lista. Iniciando aprovisionamiento RBAC..."

# ──── Función HTTP con trazabilidad de código de respuesta ───────────────────
api_req() {
  local method="$1"
  local endpoint="$2"
  local data="${3:-}"
  local resp
  if [ -n "$data" ]; then
    resp=$(curl -s -w "\n%{http_code}" -X "$method" \
      -u "$AUTH" \
      -H "Content-Type: application/json" \
      -d "$data" \
      "$GRAFANA_URL$endpoint")
  else
    resp=$(curl -s -w "\n%{http_code}" -X "$method" \
      -u "$AUTH" \
      -H "Content-Type: application/json" \
      "$GRAFANA_URL$endpoint")
  fi
  RESP_CODE=$(echo "$resp" | tail -n1)
  RESP_BODY=$(echo "$resp" | sed '$d')
}

# ──── 1. Gestión Idempotente de Teams ─────────────────────────────────────────
echo "[acceso] Aprovisionando teams..."

TEAM_ID=""
obtener_o_crear_team() {
  local name="$1"
  local email="$2"
  TEAM_ID=""

  api_req GET "/api/teams/search?name=$name"
  TEAM_ID=$(echo "$RESP_BODY" | grep -o '"id":[0-9]*' | head -n1 | cut -d: -f2 || true)

  if [ -z "$TEAM_ID" ]; then
    api_req POST "/api/teams" "{\"name\":\"$name\",\"email\":\"$email\"}"
    echo "[acceso] [$RESP_CODE] POST /api/teams ($name)"
    TEAM_ID=$(echo "$RESP_BODY" | grep -o '"teamId":[0-9]*' | head -n1 | cut -d: -f2 || true)
    if [ -z "$TEAM_ID" ]; then
      api_req GET "/api/teams/search?name=$name"
      TEAM_ID=$(echo "$RESP_BODY" | grep -o '"id":[0-9]*' | head -n1 | cut -d: -f2 || true)
    fi
  else
    echo "[acceso] [$RESP_CODE] Team '$name' existente reutilizado (id=$TEAM_ID)."
  fi
}

obtener_o_crear_team "Direccion" "direccion@haizelab.eus"
ID_TEAM_DIR="$TEAM_ID"

obtener_o_crear_team "Analisis" "analisis@haizelab.eus"
ID_TEAM_ANL="$TEAM_ID"

obtener_o_crear_team "IT" "it@haizelab.eus"
ID_TEAM_IT="$TEAM_ID"

# ──── 2. Home Dashboard por Team (homeDashboardUID) ─────────────────────────
configurar_home_team() {
  local team_id="$1"
  local uid="$2"
  local team_name="$3"
  if [ -n "$team_id" ]; then
    api_req PUT "/api/teams/$team_id/preferences" "{\"homeDashboardUID\":\"$uid\",\"theme\":\"dark\",\"timezone\":\"browser\"}"
    echo "[acceso] [$RESP_CODE] PUT /api/teams/$team_id/preferences ($team_name -> $uid)"
  else
    echo "[acceso] AVISO: Team '$team_name' no tiene ID válido. Saltando preferencias."
  fi
}

echo "[acceso] Configurando home dashboards para teams..."
configurar_home_team "$ID_TEAM_ANL" "haizelab-analisis" "Analisis"
configurar_home_team "$ID_TEAM_DIR" "haizelab-overview" "Direccion"

# ──── 3. Gestión Idempotente de Usuarios y Asignación de Roles ───────────────
echo "[acceso] Aprovisionando usuarios, roles y sincronizando credenciales..."

USER_ID=""
gestionar_usuario() {
  local nombre="$1"
  local email="$2"
  local login="$3"
  local rol="$4"
  local pass="$5"
  USER_ID=""

  # 1. Verificar si existe
  api_req GET "/api/users/lookup?loginOrEmail=$login"
  if [ "$RESP_CODE" = "200" ]; then
    USER_ID=$(echo "$RESP_BODY" | grep -o '"id":[0-9]*' | head -n1 | cut -d: -f2 || true)
    echo "[acceso] [$RESP_CODE] Usuario '$login' existente detectado (id=$USER_ID)."
  else
    # 2. Crear si no existe
    api_req POST "/api/admin/users" "{\"name\":\"$nombre\",\"email\":\"$email\",\"login\":\"$login\",\"password\":\"$pass\",\"OrgId\":1}"
    echo "[acceso] [$RESP_CODE] POST /api/admin/users ($login)"
    USER_ID=$(echo "$RESP_BODY" | grep -o '"id":[0-9]*' | head -n1 | cut -d: -f2 || true)
    if [ -z "$USER_ID" ]; then
      api_req GET "/api/users/lookup?loginOrEmail=$login"
      USER_ID=$(echo "$RESP_BODY" | grep -o '"id":[0-9]*' | head -n1 | cut -d: -f2 || true)
    fi
  fi

  if [ -n "$USER_ID" ]; then
    # 3. Sincronizar contraseña
    api_req PUT "/api/admin/users/$USER_ID/password" "{\"password\":\"$pass\"}"
    echo "[acceso] [$RESP_CODE] PUT /api/admin/users/$USER_ID/password ($login)"

    # 4. Asignar rol real en la Organización 1 (Viewer, Editor o Admin)
    api_req PATCH "/api/orgs/1/users/$USER_ID" "{\"role\":\"$rol\"}"
    echo "[acceso] [$RESP_CODE] PATCH /api/orgs/1/users/$USER_ID ($login -> rol $rol)"
  else
    echo "[acceso] ERROR: No se pudo obtener ID para '$login'." >&2
  fi
}

# Función para asociar a equipo
asignar_a_team() {
  local team_id="$1"
  local user_id="$2"
  local login="$3"
  if [ -n "$team_id" ] && [ -n "$user_id" ]; then
    api_req POST "/api/teams/$team_id/members" "{\"userId\":$user_id}"
    if [ "$RESP_CODE" = "200" ]; then
      echo "[acceso] [$RESP_CODE] Usuario '$login' vinculado al team $team_id."
    elif [ "$RESP_CODE" = "400" ] || [ "$RESP_CODE" = "409" ]; then
      echo "[acceso] [$RESP_CODE] Usuario '$login' ya pertenecía al team $team_id (idempotente)."
    else
      echo "[acceso] [$RESP_CODE] POST /api/teams/$team_id/members ($login)"
    fi
  fi
}

# Dirección: 1 usuario (Viewer)
gestionar_usuario "Directora ZBE" "directora@haizelab.eus" "directora" "Viewer" "${PASS_BASE}dir"
[ -n "$ID_TEAM_DIR" ] && asignar_a_team "$ID_TEAM_DIR" "$USER_ID" "directora"

# Análisis: 6 analistas (Viewer con home dashboard específico)
for i in 1 2 3 4 5 6; do
  gestionar_usuario "Analista $i" "analista$i@haizelab.eus" "analista$i" "Viewer" "${PASS_BASE}a$i"
  [ -n "$ID_TEAM_ANL" ] && asignar_a_team "$ID_TEAM_ANL" "$USER_ID" "analista$i"
done

# IT: 3 administradores técnicos (it_admin1 Admin, it_admin2 y it_admin3 Editor)
gestionar_usuario "IT Admin 1" "it1@haizelab.eus" "it_admin1" "Admin"  "${PASS_BASE}it1"
[ -n "$ID_TEAM_IT" ] && asignar_a_team "$ID_TEAM_IT" "$USER_ID" "it_admin1"

gestionar_usuario "IT Admin 2" "it2@haizelab.eus" "it_admin2" "Editor" "${PASS_BASE}it2"
[ -n "$ID_TEAM_IT" ] && asignar_a_team "$ID_TEAM_IT" "$USER_ID" "it_admin2"

gestionar_usuario "IT Admin 3" "it3@haizelab.eus" "it_admin3" "Editor" "${PASS_BASE}it3"
[ -n "$ID_TEAM_IT" ] && asignar_a_team "$ID_TEAM_IT" "$USER_ID" "it_admin3"

echo "[acceso] ====================================================="
echo "[acceso] Control de acceso RBAC provisionado correctamente."
echo "[acceso] ====================================================="
