import express, { Request, Response, NextFunction } from "express";
import client from "prom-client";

const app = express();
const PORT = process.env.PORT || 3000;

// ─── Prometheus: registro y métricas ─────────────────────────────────────────

const register = new client.Registry();
client.collectDefaultMetrics({ register });

// Contador total de requests
const httpRequestsTotal = new client.Counter({
  name: "http_requests_total",
  help: "Total de requests HTTP recibidos",
  labelNames: ["method", "endpoint", "status_code"],
  registers: [register],
});

// Histograma de latencia
const httpRequestDuration = new client.Histogram({
  name: "http_request_duration_seconds",
  help: "Duración de los requests HTTP en segundos",
  labelNames: ["method", "endpoint", "status_code"],
  buckets: [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5],
  registers: [register],
});

// Gauge de requests activos
const httpRequestsActive = new client.Gauge({
  name: "http_requests_active",
  help: "Requests HTTP activos en este momento",
  registers: [register],
});

// Contador de errores
const httpErrorsTotal = new client.Counter({
  name: "http_errors_total",
  help: "Total de respuestas con error (4xx / 5xx)",
  labelNames: ["endpoint", "status_code"],
  registers: [register],
});

// Gauge de "temperatura" del inventario (métrica de negocio inventada)
const inventoryTemperature = new client.Gauge({
  name: "inventory_temperature_celsius",
  help: "Temperatura simulada del almacén de inventario",
  registers: [register],
});

// ─── Middleware de instrumentación ──────────────────────────────────────────

app.use((req: Request, res: Response, next: NextFunction) => {
  const end = httpRequestDuration.startTimer();
  httpRequestsActive.inc();

  res.on("finish", () => {
    const labels = {
      method: req.method,
      endpoint: req.path,
      status_code: String(res.statusCode),
    };
    httpRequestsTotal.inc(labels);
    end(labels);
    httpRequestsActive.dec();

    if (res.statusCode >= 400) {
      httpErrorsTotal.inc({ endpoint: req.path, status_code: String(res.statusCode) });
    }
  });

  next();
});

app.use(express.json());

// ─── Endpoints ───────────────────────────────────────────────────────────────

// GET / — estado general
app.get("/", (_req: Request, res: Response) => {
  res.json({
    status: "ok",
    message: "API de monitoreo activa 🚀",
    version: "1.0.0",
    timestamp: new Date().toISOString(),
  });
});

// GET /api/productos — lista de productos (rápido)
app.get("/api/productos", (_req: Request, res: Response) => {
  const productos = [
    { id: 1, nombre: "Laptop Pro", precio: 1500, stock: 42 },
    { id: 2, nombre: "Mouse Inalámbrico", precio: 35, stock: 200 },
    { id: 3, nombre: "Teclado Mecánico", precio: 120, stock: 75 },
    { id: 4, nombre: "Monitor 27\"", precio: 450, stock: 18 },
    { id: 5, nombre: "Webcam HD", precio: 90, stock: 60 },
  ];

  // Actualizar temperatura simulada del inventario
  inventoryTemperature.set(20 + Math.random() * 10);

  res.json({ total: productos.length, productos });
});

// GET /api/productos/:id — producto por id
app.get("/api/productos/:id", (req: Request, res: Response) => {
  const id = parseInt(req.params.id);
  const productos: Record<number, object> = {
    1: { id: 1, nombre: "Laptop Pro", precio: 1500, stock: 42 },
    2: { id: 2, nombre: "Mouse Inalámbrico", precio: 35, stock: 200 },
    3: { id: 3, nombre: "Teclado Mecánico", precio: 120, stock: 75 },
  };

  if (!productos[id]) {
    return res.status(404).json({ error: "Producto no encontrado", id });
  }

  return res.json(productos[id]);
});

// GET /api/reportes — endpoint lento (simula procesamiento pesado)
app.get("/api/reportes", async (_req: Request, res: Response) => {
  const delay = 2000 + Math.random() * 1500; // 2–3.5 segundos
  await new Promise((resolve) => setTimeout(resolve, delay));

  res.json({
    reporte: "ventas_mensual",
    periodo: "2026-05",
    total_ventas: Math.floor(Math.random() * 50000) + 10000,
    tiempo_generacion_ms: Math.round(delay),
    generado_en: new Date().toISOString(),
  });
});

// GET /api/estadisticas — métricas de negocio
app.get("/api/estadisticas", (_req: Request, res: Response) => {
  res.json({
    usuarios_activos: Math.floor(Math.random() * 500) + 50,
    pedidos_hoy: Math.floor(Math.random() * 300) + 20,
    ingresos_hoy_usd: +(Math.random() * 15000 + 2000).toFixed(2),
    tasa_conversion: +(Math.random() * 5 + 1).toFixed(2),
    timestamp: new Date().toISOString(),
  });
});

// GET /api/salud — health check detallado
app.get("/api/salud", (_req: Request, res: Response) => {
  const uptime = process.uptime();
  const memoryUsage = process.memoryUsage();

  res.json({
    status: "healthy",
    uptime_segundos: Math.round(uptime),
    memoria: {
      heap_usado_mb: +(memoryUsage.heapUsed / 1024 / 1024).toFixed(2),
      heap_total_mb: +(memoryUsage.heapTotal / 1024 / 1024).toFixed(2),
      rss_mb: +(memoryUsage.rss / 1024 / 1024).toFixed(2),
    },
    node_version: process.version,
  });
});

// GET /api/error-demo — genera errores para demostrar métricas de errores
app.get("/api/error-demo", (_req: Request, res: Response) => {
  const rand = Math.random();
  if (rand < 0.3) {
    return res.status(500).json({ error: "Error interno simulado" });
  }
  if (rand < 0.5) {
    return res.status(503).json({ error: "Servicio no disponible (simulado)" });
  }
  return res.json({ resultado: "ok", valor: Math.random() });
});

// GET /metrics — expone métricas en formato Prometheus
app.get("/metrics", async (_req: Request, res: Response) => {
  res.set("Content-Type", register.contentType);
  res.end(await register.metrics());
});

// ─── Iniciar servidor ─────────────────────────────────────────────────────────

app.listen(PORT, () => {
  console.log(`✅  API corriendo en http://localhost:${PORT}`);
  console.log(`📊  Métricas en http://localhost:${PORT}/metrics`);
});

export default app;
