#!/bin/bash
# Script de tráfico sintético (bash/curl)
# Uso: ./generate-traffic.sh [duracion_segundos]

BASE_URL="http://localhost:3000"
DURACION=${1:-0}  # 0 = infinito
CONTADOR=0
ERRORES=0
INICIO=$(date +%s)

ENDPOINTS=(
  "/"
  "/api/productos"
  "/api/productos/1"
  "/api/productos/2"
  "/api/productos/99"
  "/api/estadisticas"
  "/api/salud"
  "/api/reportes"
  "/api/error-demo"
  "/api/productos"
  "/api/productos"
  "/api/estadisticas"
  "/api/estadisticas"
)

echo "============================================"
echo "  🚀  Tráfico sintético — bash/curl"
echo "============================================"
echo "  URL: $BASE_URL"
echo "  Duración: $([ $DURACION -eq 0 ] && echo '∞' || echo "${DURACION}s")"
echo "============================================"

# Verificar conexión
if ! curl -sf "$BASE_URL/api/salud" > /dev/null 2>&1; then
  echo "❌  No se puede conectar a $BASE_URL"
  echo "    Ejecuta: docker-compose up -d"
  exit 1
fi
echo "✅  API disponible"
echo ""

while true; do
  # Verificar duración
  if [ $DURACION -gt 0 ]; then
    AHORA=$(date +%s)
    ELAPSED=$((AHORA - INICIO))
    if [ $ELAPSED -ge $DURACION ]; then
      break
    fi
  fi

  # Elegir endpoint aleatorio
  IDX=$((RANDOM % ${#ENDPOINTS[@]}))
  ENDPOINT="${ENDPOINTS[$IDX]}"
  URL="$BASE_URL$ENDPOINT"

  # Hacer request y medir tiempo
  INICIO_REQ=$(date +%s%N)
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$URL")
  FIN_REQ=$(date +%s%N)
  DURACION_MS=$(( (FIN_REQ - INICIO_REQ) / 1000000 ))

  CONTADOR=$((CONTADOR + 1))
  HORA=$(date +%H:%M:%S)

  if [ "$STATUS" -ge 400 ] || [ "$STATUS" -eq 0 ]; then
    ERRORES=$((ERRORES + 1))
    echo "[$HORA] #$CONTADOR  ✗  HTTP $STATUS  $ENDPOINT  ${DURACION_MS}ms"
  else
    echo "[$HORA] #$CONTADOR  ✓  HTTP $STATUS  $ENDPOINT  ${DURACION_MS}ms"
  fi

  sleep 0.5
done

echo ""
echo "============================================"
echo "  📊  Resumen"
echo "============================================"
echo "  Total  : $CONTADOR"
echo "  Errores: $ERRORES"
if [ $CONTADOR -gt 0 ]; then
  echo "  Error % : $(( ERRORES * 100 / CONTADOR ))%"
fi
echo "============================================"
