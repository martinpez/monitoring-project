# 📊 API Monitoreo — Express + TypeScript + Prometheus + Grafana

Sistema de monitoreo completo con una API REST instrumentada, Prometheus para recolección de métricas y Grafana para visualización. Todo corre en Docker.

---

## 🏗️ Estructura del proyecto

```
monitoring-project/
├── docker-compose.yml
├── README.md
├── api/
│   ├── Dockerfile
│   ├── package.json
│   ├── tsconfig.json
│   └── src/
│       └── index.ts          ← API Express con métricas
├── prometheus/
│   ├── prometheus.yml        ← Configuración de scraping
│   └── alerts.yml            ← Reglas de alertas (bonus)
├── grafana/
│   └── provisioning/
│       ├── datasources/
│       │   └── prometheus.yml
│       └── dashboards/
│           ├── dashboard.yml
│           └── api-dashboard.json  ← Dashboard pre-cargado
└── scripts/
    ├── generate-traffic.py   ← Script Python (recomendado)
    └── generate-traffic.sh   ← Script Bash (alternativo)
```

---

## 🚀 Inicio rápido

### 1. Requisitos
- Docker y Docker Compose instalados
- Python 3.8+ con `requests` (para el script de tráfico)

### 2. Levantar los servicios

```bash
# Desde la raíz del proyecto
docker-compose up -d

# Verificar que los 3 servicios estén corriendo
docker-compose ps
```

### 3. Acceder a los servicios

| Servicio    | URL                         | Credenciales    |
|-------------|------------------------------|-----------------|
| API         | http://localhost:3000        | —               |
| Prometheus  | http://localhost:9090        | —               |
| Grafana     | http://localhost:3001        | admin / admin   |

### 4. Generar tráfico sintético

```bash
# Instalar dependencia (solo la primera vez)
pip install requests

# Modo normal (infinito, 2 req/seg)
python3 scripts/generate-traffic.py

# Con duración y tasa específicas
python3 scripts/generate-traffic.py --duracion 120 --rps 5

# Modo stress
python3 scripts/generate-traffic.py --modo stress

# Con bash (alternativo)
bash scripts/generate-traffic.sh
```

---

## 🔌 Endpoints de la API

| Método | Endpoint              | Descripción                                  |
|--------|----------------------|----------------------------------------------|
| GET    | `/`                  | Estado general de la API                     |
| GET    | `/api/productos`     | Lista de productos (rápido ~10ms)            |
| GET    | `/api/productos/:id` | Producto por ID (404 si no existe)           |
| GET    | `/api/reportes`      | Genera reporte (lento: 2–3.5 segundos)       |
| GET    | `/api/estadisticas`  | Métricas de negocio simuladas                |
| GET    | `/api/salud`         | Health check con info de memoria             |
| GET    | `/api/error-demo`    | Genera errores aleatorios (30% error 500)    |
| GET    | `/metrics`           | Métricas en formato Prometheus ✅            |

---

## 📈 Métricas expuestas

| Métrica                              | Tipo      | Descripción                          |
|--------------------------------------|-----------|--------------------------------------|
| `http_requests_total`                | Counter   | Total requests por endpoint/método   |
| `http_request_duration_seconds`      | Histogram | Latencia por endpoint                |
| `http_requests_active`               | Gauge     | Requests simultáneos en curso        |
| `http_errors_total`                  | Counter   | Errores 4xx/5xx por endpoint         |
| `inventory_temperature_celsius`      | Gauge     | Métrica de negocio personalizada     |
| `nodejs_heap_size_used_bytes`        | Gauge     | Memoria heap Node.js (automática)    |
| `process_cpu_seconds_total`          | Counter   | CPU total (automática)               |

---

## 🔍 Queries PromQL útiles

```promql
# Requests por segundo (último minuto)
rate(http_requests_total[1m])

# Requests por segundo por endpoint
sum by (endpoint) (rate(http_requests_total[1m]))

# Latencia promedio
rate(http_request_duration_seconds_sum[1m]) / rate(http_request_duration_seconds_count[1m])

# Percentil 95 de latencia
histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[1m])) by (le))

# Tasa de errores
sum(rate(http_errors_total[1m])) / sum(rate(http_requests_total[1m]))

# Total de requests en los últimos 5 minutos
sum(increase(http_requests_total[5m]))
```

---

## 📊 Dashboard de Grafana

El dashboard se carga automáticamente al iniciar Grafana. Incluye **8 paneles**:

1. **Throughput** — Requests por segundo por endpoint (time series)
2. **Latencia** — Promedio y P95 (time series)
3. **Tasa de errores** — % de respuestas 4xx/5xx (time series)
4. **Requests activos** — Gauge en tiempo real (stat)
5. **Temperatura del almacén** — Métrica personalizada (gauge)
6. **Memoria heap** — Usado vs total (time series)
7. **Total de requests** — Últimos 5 min (stat)
8. **Distribución por endpoint** — Pastel (piechart)

---

## 🔔 Alertas configuradas (Bonus)

| Alerta             | Condición                              | Severidad |
|--------------------|----------------------------------------|-----------|
| AltaTasaDeErrores  | Tasa de errores > 20% por 1 minuto     | warning   |
| AltaLatencia       | P95 > 3 segundos por 2 minutos         | warning   |
| APINoDisponible    | API no responde por 30 segundos        | critical  |

---

## 🛑 Detener los servicios

```bash
# Detener (conserva datos)
docker-compose down

# Detener y eliminar volúmenes (datos de Prometheus y Grafana)
docker-compose down -v
```

---

## 💡 Análisis de métricas

- **`/api/reportes`** siempre mostrará latencia alta (~2-3s); esto es intencional para demostrar el P95.
- **`/api/error-demo`** genera ~30-50% de errores, útil para ver la tasa de errores en acción.
- **`/api/productos/99`** siempre retorna 404, visible en el contador de errores por endpoint.
- El modo `--modo stress` del script es útil para ver cómo responden las métricas bajo carga.

---

## 👤 Entrega

**Nombre:** Martin Elias Perez  
**Código:** 202229901601
