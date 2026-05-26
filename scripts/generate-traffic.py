#!/usr/bin/env python3
"""
Script de tráfico sintético para la API de monitoreo.
Genera requests variados con diferentes patrones de carga.

Uso:
    python3 generate-traffic.py                  # modo normal (infinito)
    python3 generate-traffic.py --duracion 120   # 2 minutos
    python3 generate-traffic.py --rps 10         # 10 requests/seg
    python3 generate-traffic.py --modo stress    # carga alta
"""

import argparse
import random
import sys
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

try:
    import requests as req_lib
except ImportError:
    print("❌  Instala requests: pip install requests")
    sys.exit(1)

BASE_URL = "http://localhost:3000"

# Endpoints con su peso relativo (más peso = más frecuente)
ENDPOINTS = [
    ("/",                  15),
    ("/api/productos",     30),
    ("/api/productos/1",   10),
    ("/api/productos/2",   10),
    ("/api/productos/99",   5),   # Genera 404
    ("/api/estadisticas",  15),
    ("/api/salud",         10),
    ("/api/reportes",       5),   # Lento (2-3 seg)
    ("/api/error-demo",    10),   # Genera errores aleatorios
]

endpoints_list = [ep for ep, weight in ENDPOINTS for _ in range(weight)]

COLORES = {
    "ok":      "\033[92m",  # verde
    "lento":   "\033[93m",  # amarillo
    "error":   "\033[91m",  # rojo
    "reset":   "\033[0m",
    "header":  "\033[96m",  # cyan
    "bold":    "\033[1m",
}


def color(texto: str, tipo: str) -> str:
    return f"{COLORES.get(tipo, '')}{texto}{COLORES['reset']}"


def hacer_request(endpoint: str, session: req_lib.Session) -> dict:
    url = f"{BASE_URL}{endpoint}"
    inicio = time.time()
    try:
        resp = session.get(url, timeout=10)
        duracion = time.time() - inicio
        return {
            "endpoint": endpoint,
            "status": resp.status_code,
            "duracion_ms": round(duracion * 1000),
            "ok": resp.status_code < 400,
        }
    except req_lib.exceptions.ConnectionError:
        return {
            "endpoint": endpoint,
            "status": 0,
            "duracion_ms": 0,
            "ok": False,
            "error": "Conexión rechazada (¿está el docker-compose corriendo?)",
        }
    except Exception as e:
        return {
            "endpoint": endpoint,
            "status": 0,
            "duracion_ms": 0,
            "ok": False,
            "error": str(e),
        }


def imprimir_resultado(r: dict, contador: int) -> None:
    hora = datetime.now().strftime("%H:%M:%S")
    status = r["status"]

    if r.get("error"):
        print(color(f"[{hora}] #{contador:>5}  ERROR  {r['endpoint']:<25}  {r['error']}", "error"))
        return

    tipo = "ok"
    if status >= 500:
        tipo = "error"
    elif status >= 400:
        tipo = "lento"
    elif r["duracion_ms"] > 1000:
        tipo = "lento"

    icono = "✓" if tipo == "ok" else ("✗" if tipo == "error" else "⚠")
    linea = (
        f"[{hora}] #{contador:>5}  {icono}  "
        f"HTTP {status}  {r['endpoint']:<25}  {r['duracion_ms']:>5} ms"
    )
    print(color(linea, tipo))


def verificar_api() -> bool:
    """Verifica que la API esté disponible antes de empezar."""
    print(color("🔍  Verificando conexión con la API...", "header"))
    try:
        resp = req_lib.get(f"{BASE_URL}/api/salud", timeout=5)
        if resp.status_code == 200:
            print(color(f"✅  API disponible en {BASE_URL}", "ok"))
            return True
    except Exception:
        pass
    print(color(f"❌  No se puede conectar a {BASE_URL}", "error"))
    print("    Asegúrate de que docker-compose esté corriendo:")
    print("    docker-compose up -d")
    return False


def generar_trafico(
    duracion: float,
    rps: float,
    modo: str,
    workers: int,
) -> None:
    print(color(f"\n{'='*60}", "header"))
    print(color(f"  🚀  Generador de tráfico sintético", "bold"))
    print(color(f"{'='*60}", "header"))
    print(f"  URL base  : {BASE_URL}")
    print(f"  Modo      : {modo}")
    print(f"  RPS target: {rps}")
    print(f"  Duración  : {'∞ (Ctrl+C para detener)' if duracion == 0 else f'{duracion}s'}")
    print(f"  Workers   : {workers}")
    print(color(f"{'='*60}\n", "header"))

    intervalo = 1.0 / rps if rps > 0 else 0.1
    contador = 0
    inicio_total = time.time()
    errores = 0

    session = req_lib.Session()

    try:
        with ThreadPoolExecutor(max_workers=workers) as executor:
            while True:
                if duracion > 0 and (time.time() - inicio_total) >= duracion:
                    break

                endpoint = random.choice(endpoints_list)

                # En modo stress añadimos más llamadas a endpoints lentos
                if modo == "stress" and random.random() < 0.3:
                    endpoint = "/api/reportes"

                future = executor.submit(hacer_request, endpoint, session)
                contador += 1
                resultado = future.result()
                imprimir_resultado(resultado, contador)

                if not resultado["ok"]:
                    errores += 1
                    if resultado.get("error") and "Conexión" in resultado.get("error", ""):
                        print(color("\n⚠️  API no disponible. Esperando 5 segundos...", "lento"))
                        time.sleep(5)
                        continue

                time.sleep(intervalo)

    except KeyboardInterrupt:
        pass
    finally:
        tiempo_total = time.time() - inicio_total
        print(color(f"\n{'='*60}", "header"))
        print(color("  📊  Resumen final", "bold"))
        print(color(f"{'='*60}", "header"))
        print(f"  Total requests : {contador}")
        print(f"  Errores        : {errores}")
        print(f"  Tasa de error  : {errores/contador*100:.1f}%" if contador > 0 else "  —")
        print(f"  Tiempo total   : {tiempo_total:.1f}s")
        print(f"  RPS real       : {contador/tiempo_total:.2f}" if tiempo_total > 0 else "  —")
        print(color(f"{'='*60}\n", "header"))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Genera tráfico sintético hacia la API de monitoreo"
    )
    parser.add_argument(
        "--duracion", type=float, default=0,
        help="Duración en segundos (0 = infinito)",
    )
    parser.add_argument(
        "--rps", type=float, default=2.0,
        help="Requests por segundo (default: 2)",
    )
    parser.add_argument(
        "--modo", choices=["normal", "stress", "lento"], default="normal",
        help="Patrón de tráfico (default: normal)",
    )
    parser.add_argument(
        "--workers", type=int, default=3,
        help="Threads concurrentes (default: 3)",
    )
    args = parser.parse_args()

    if args.modo == "stress":
        args.rps = max(args.rps, 10.0)
        args.workers = max(args.workers, 8)

    if not verificar_api():
        sys.exit(1)

    generar_trafico(
        duracion=args.duracion,
        rps=args.rps,
        modo=args.modo,
        workers=args.workers,
    )


if __name__ == "__main__":
    main()
