#!/bin/sh
# grafana/provisioning/access-control/setup-access.sh
# =====================================================
# Configura el control de acceso de Grafana vía API REST.
#
# Roles según requisito:
#   Cúpula directiva (viewers):  ven todo, no editan
#   Análisis (6 personas):       ven dashboards asignados, home dashboard por equipo
#   IT (3 personas):             ven y editan todo (Editor + Admin)
#
# Ejecución: se invoca desde grafana/entrypoint.sh tras arrancar Grafana.
# Requiere que la API esté disponible en localhost:3000.
#
# Credenciales de admin: tomadas de las vars de entorno que ya tiene el contenedor.

set -eu

GRAFANA_URL="http://localhost:3000"
ADMIN_USER="${GF_SECURITY_ADMIN_USER:-admin}"
ADMIN_PASS="${GF_SECURITY_ADMIN_PASSWORD:-haizelab2024seguro}"
AUTH="$ADMIN_USER:$ADMIN_PASS"

# Esperar a que Grafana esté sano antes de llamar a la API
echo "[acceso] Esperando a que Grafana esté disponible..."
until wget -qO- "$GRAFANA_URL/api/health" 2>/dev/null | grep -q '"database":"ok"'; do
  sleep 2
done
echo "[acceso] Grafana disponible. Configurando control de acceso..."

# ──── Función auxiliar ────────────────────────────────────────────────────────
api_post() {
  local endpoint="$1"
  local data="$2"
  wget -qO- \
    --header="Content-Type: application/json" \
    --header="Authorization: Basic $(printf '%s' "$AUTH" | base64)" \
    --post-data="$data" \
    "$GRAFANA_URL$endpoint" 2>/dev/null || true
}

api_put() {
  local endpoint="$1"
  local data="$2"
  wget -qO- \
    --header="Content-Type: application/json" \
    --header="Authorization: Basic $(printf '%s' "$AUTH" | base64)" \
    --method=PUT \
    --body-data="$data" \
    "$GRAFANA_URL$endpoint" 2>/dev/null || true
}

api_get() {
  local endpoint="$1"
  wget -qO- \
    --header="Authorization: Basic $(printf '%s' "$AUTH" | base64)" \
    "$GRAFANA_URL$endpoint" 2>/dev/null || echo "{}"
}

# ──── 1. Crear Teams ──────────────────────────────────────────────────────────
echo "[acceso] Creando teams..."

# Team: Dirección (Viewers — ven todo, no editan)
TEAM_DIR=$(api_post "/api/teams" '{"name":"Direccion","email":"direccion@haizelab.eus"}')
ID_TEAM_DIR=$(echo "$TEAM_DIR" | grep -o '"teamId":[0-9]*' | grep -o '[0-9]*')
echo "[acceso] Team Dirección: id=$ID_TEAM_DIR"

# Team: Análisis (Viewers con home dashboard propio)
TEAM_ANL=$(api_post "/api/teams" '{"name":"Analisis","email":"analisis@haizelab.eus"}')
ID_TEAM_ANL=$(echo "$TEAM_ANL" | grep -o '"teamId":[0-9]*' | grep -o '[0-9]*')
echo "[acceso] Team Análisis: id=$ID_TEAM_ANL"

# Team: IT (Editors/Admins — ven y editan todo)
TEAM_IT=$(api_post "/api/teams" '{"name":"IT","email":"it@haizelab.eus"}')
ID_TEAM_IT=$(echo "$TEAM_IT" | grep -o '"teamId":[0-9]*' | grep -o '[0-9]*')
echo "[acceso] Team IT: id=$ID_TEAM_IT"

# ──── 2. Home dashboard por equipo ──────────────────────────────────────────
# Según rúbrica: al loguearse deben acceder directamente al panel que corresponda.
#   - Análisis: aterriza en el panel técnico "haizelab-analisis"
#   - Dirección: aterriza en el monitor general "haizelab-overview"
echo "[acceso] Configurando home dashboard del team Análisis..."
if [ -n "$ID_TEAM_ANL" ]; then
  DASH_INFO=$(api_get "/api/dashboards/uid/haizelab-analisis")
  DASH_ID=$(echo "$DASH_INFO" | grep -o '"id":[0-9]*' | head -1 | grep -o '[0-9]*')
  if [ -n "$DASH_ID" ]; then
    api_put "/api/teams/$ID_TEAM_ANL/preferences" \
      "{\"homeDashboardId\":$DASH_ID,\"theme\":\"dark\",\"timezone\":\"browser\"}"
    echo "[acceso] Home dashboard Análisis → id=$DASH_ID (haizelab-analisis)"
  else
    echo "[acceso] AVISO: Dashboard 'haizelab-analisis' no encontrado aún. Skipping."
  fi
fi

echo "[acceso] Configurando home dashboard del team Dirección..."
if [ -n "$ID_TEAM_DIR" ]; then
  DASH_DIR_INFO=$(api_get "/api/dashboards/uid/haizelab-overview")
  DASH_DIR_ID=$(echo "$DASH_DIR_INFO" | grep -o '"id":[0-9]*' | head -1 | grep -o '[0-9]*')
  if [ -n "$DASH_DIR_ID" ]; then
    api_put "/api/teams/$ID_TEAM_DIR/preferences" \
      "{\"homeDashboardId\":$DASH_DIR_ID,\"theme\":\"dark\",\"timezone\":\"browser\"}"
    echo "[acceso] Home dashboard Dirección → id=$DASH_DIR_ID (haizelab-overview)"
  fi
fi

# ──── 3. Crear usuarios de ejemplo y asignarlos a teams ──────────────────────
# En producción estos usuarios se crearían con LDAP/OAuth.
# Aquí se crean via API como demostración con rol acorde.

crear_usuario() {
  local nombre="$1"
  local email="$2"
  local login="$3"
  local role="$4"   # Viewer | Editor | Admin
  local pass="$5"
  api_post "/api/admin/users" \
    "{\"name\":\"$nombre\",\"email\":\"$email\",\"login\":\"$login\",\"password\":\"$pass\",\"OrgId\":1,\"role\":\"$role\"}" \
    > /dev/null
  echo "[acceso] Usuario '$login' ($role) creado."
}

# Dirección: 1 usuario ejemplo (Viewer)
crear_usuario "Directora ZBE"         "directora@haizelab.eus"     "directora"  "Viewer"  "haize2024dir"

# Análisis: 6 usuarios (Viewer con home dashboard)
crear_usuario "Analista 1"  "analista1@haizelab.eus"  "analista1"  "Viewer"  "haize2024a1"
crear_usuario "Analista 2"  "analista2@haizelab.eus"  "analista2"  "Viewer"  "haize2024a2"
crear_usuario "Analista 3"  "analista3@haizelab.eus"  "analista3"  "Viewer"  "haize2024a3"
crear_usuario "Analista 4"  "analista4@haizelab.eus"  "analista4"  "Viewer"  "haize2024a4"
crear_usuario "Analista 5"  "analista5@haizelab.eus"  "analista5"  "Viewer"  "haize2024a5"
crear_usuario "Analista 6"  "analista6@haizelab.eus"  "analista6"  "Viewer"  "haize2024a6"

# IT: 3 usuarios (Editor/Admin)
crear_usuario "IT Admin 1"  "it1@haizelab.eus"  "it_admin1"  "Admin"   "haize2024it1"
crear_usuario "IT Admin 2"  "it2@haizelab.eus"  "it_admin2"  "Editor"  "haize2024it2"
crear_usuario "IT Admin 3"  "it3@haizelab.eus"  "it_admin3"  "Editor"  "haize2024it3"

# ──── 4. Añadir usuarios a sus teams ─────────────────────────────────────────
añadir_a_team() {
  local team_id="$1"
  local login="$2"
  local user_info
  user_info=$(api_get "/api/users/lookup?loginOrEmail=$login")
  local user_id
  user_id=$(echo "$user_info" | grep -o '"id":[0-9]*' | head -1 | grep -o '[0-9]*')
  if [ -n "$user_id" ] && [ -n "$team_id" ]; then
    api_post "/api/teams/$team_id/members" "{\"userId\":$user_id}" > /dev/null
    echo "[acceso] $login añadido al team $team_id"
  fi
}

# Dirección
[ -n "$ID_TEAM_DIR" ] && añadir_a_team "$ID_TEAM_DIR" "directora"

# Análisis
for i in 1 2 3 4 5 6; do
  [ -n "$ID_TEAM_ANL" ] && añadir_a_team "$ID_TEAM_ANL" "analista$i"
done

# IT
[ -n "$ID_TEAM_IT" ] && añadir_a_team "$ID_TEAM_IT" "it_admin1"
[ -n "$ID_TEAM_IT" ] && añadir_a_team "$ID_TEAM_IT" "it_admin2"
[ -n "$ID_TEAM_IT" ] && añadir_a_team "$ID_TEAM_IT" "it_admin3"

# ──── 5. Deshabilitar registro y acceso anónimo (producción) ─────────────────
# Nota: GF_USERS_ALLOW_SIGN_UP ya está en false en docker-compose.yml.
# GF_AUTH_ANONYMOUS_ENABLED=true está en dev; en prod se desactiva.

echo "[acceso] Control de acceso configurado."
echo "[acceso] Resumen:"
echo "  - Team Dirección (Viewer):   1 usuario — ve todo, no edita"
echo "  - Team Análisis  (Viewer):   6 usuarios — home dashboard propio"
echo "  - Team IT        (Admin/Ed): 3 usuarios — acceso completo"
