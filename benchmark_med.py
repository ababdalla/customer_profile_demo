
"""
benchmark.py
============
Script de medición ("benchmark honesto") para el proyecto Perfil de Cliente.

Ubicación:  raíz del proyecto, junto a generar_reporte.py / profile_service.py
Uso:        python benchmark.py --cliente 12345678 --inicio 2025-04-01 --fin 2026-04-01

Qué hace:
  1) Mide CADA consulta por separado  -> encuentra la "más lenta".
  2) Mide el perfil SECUENCIAL (suma de todas).
  3) Mide el perfil PARALELO (ThreadPoolExecutor) -> ~ la más lenta.
  4) Imprime un resumen comparativo con el speedup.

NOTA: correr este script FUERA de Streamlit para no contaminar la medición
(sin overhead de renderizado ni caché). Los tiempos salen en la terminal.
"""

import argparse
import time
from contextlib import contextmanager
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# --- Funciones reales del proyecto (no se modifica nada del código existente) ---
from generar_reporte import (
    obtener_cliente,
    obtener_cuentas,
    obtener_cuentas_firmantes,
    obtener_mensual,
    obtener_causas,
    obtener_agencias,
    obtener_transaccionalidad,
    obtener_ach,
)


# ---------------------------------------------------------------------------
# Utilidad de cronometraje
# ---------------------------------------------------------------------------
@contextmanager
def cronometro(nombre, registro=None):
    """Mide el tiempo de un bloque. Si se pasa `registro` (dict), guarda el valor."""
    t0 = time.perf_counter()
    try:
        yield
    finally:
        dt = time.perf_counter() - t0
        print(f"  [{nombre:<12}] {dt:7.2f} s")
        if registro is not None:
            registro[nombre] = dt


# ---------------------------------------------------------------------------
# 1) Medición de consultas individuales
# ---------------------------------------------------------------------------
def medir_individuales(cid, ai, af):
    print("\n=== 1) Consultas individuales (para hallar la más lenta) ===")
    tiempos = {}
    tareas = [
        ("cliente",   lambda: obtener_cliente(cid)),
        ("cuentas",   lambda: obtener_cuentas(cid)),
        ("firmantes", lambda: obtener_cuentas_firmantes(cid)),
        ("mensual",   lambda: obtener_mensual(cid, ai, af)),
        ("causas",    lambda: obtener_causas(cid, ai, af)),
        ("agencias",  lambda: obtener_agencias(cid, ai, af)),
        ("trans",     lambda: obtener_transaccionalidad(cid, ai, af)),
        ("ach",       lambda: obtener_ach(cid, ai, af)),
    ]
    for nombre, fn in tareas:
        with cronometro(nombre, tiempos):
            fn()

    if tiempos:
        mas_lenta = max(tiempos, key=tiempos.get)
        print(f"\n  -> Consulta MÁS LENTA: '{mas_lenta}' ({tiempos[mas_lenta]:.2f} s)")
        print(f"  -> Suma de individuales: {sum(tiempos.values()):.2f} s")
    return tiempos


# ---------------------------------------------------------------------------
# 2) Perfil SECUENCIAL (así funciona hoy)
# ---------------------------------------------------------------------------
def perfil_secuencial(cid, ai, af):
    obtener_cliente(cid)
    obtener_cuentas(cid)
    obtener_cuentas_firmantes(cid)
    obtener_mensual(cid, ai, af)
    obtener_causas(cid, ai, af)
    obtener_agencias(cid, ai, af)
    obtener_transaccionalidad(cid, ai, af)
    obtener_ach(cid, ai, af)


# ---------------------------------------------------------------------------
# 3) Perfil PARALELO (propuesta con hilos)
# ---------------------------------------------------------------------------
def perfil_paralelo(cid, ai, af, max_workers=8):
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futuros = [
            ex.submit(obtener_cliente, cid),
            ex.submit(obtener_cuentas, cid),
            ex.submit(obtener_cuentas_firmantes, cid),
            ex.submit(obtener_mensual, cid, ai, af),
            ex.submit(obtener_causas, cid, ai, af),
            ex.submit(obtener_agencias, cid, ai, af),
            ex.submit(obtener_transaccionalidad, cid, ai, af),
            ex.submit(obtener_ach, cid, ai, af),
        ]
        # .result() propaga cualquier excepción de los hilos
        for f in futuros:
            f.result()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Benchmark del Perfil de Cliente.")
    parser.add_argument("--cliente", required=True, help="Cliente ID de prueba (uno que tarde).")
    parser.add_argument("--inicio", default="2025-04-01", help="Fecha inicio YYYY-MM-DD.")
    parser.add_argument("--fin", default="2026-04-01", help="Fecha fin YYYY-MM-DD.")
    parser.add_argument("--workers", type=int, default=8, help="Hilos para la versión paralela.")
    parser.add_argument("--skip-individuales", action="store_true",
                        help="Omitir la medición consulta por consulta.")
    args = parser.parse_args()

    cid = args.cliente
    fi = datetime.strptime(args.inicio, "%Y-%m-%d")
    ff = datetime.strptime(args.fin, "%Y-%m-%d")
    ai = int(fi.strftime("%Y%m"))
    af = int(ff.strftime("%Y%m"))

    print("=" * 60)
    print(f" BENCHMARK Perfil de Cliente")
    print(f" Cliente: {cid} | Periodo: {ai} - {af} | Workers: {args.workers}")
    print("=" * 60)

    # 1) Individuales
    if not args.skip_individuales:
        medir_individuales(cid, ai, af)

    # 2) y 3) Comparativa completa
    print("\n=== 2) Perfil completo: SECUENCIAL vs PARALELO ===")
    resumen = {}
    with cronometro("SECUENCIAL", resumen):
        perfil_secuencial(cid, ai, af)
    with cronometro("PARALELO", resumen):
        perfil_paralelo(cid, ai, af, max_workers=args.workers)

    # 4) Resumen final
    print("\n" + "=" * 60)
    print(" RESUMEN")
    print("=" * 60)
    t_seq = resumen.get("SECUENCIAL")
    t_par = resumen.get("PARALELO")
    if t_seq and t_par:
        speedup = t_seq / t_par if t_par else float("inf")
        ahorro = t_seq - t_par
        print(f"  Secuencial : {t_seq:7.2f} s")
        print(f"  Paralelo   : {t_par:7.2f} s")
        print(f"  Ahorro     : {ahorro:7.2f} s")
        print(f"  Speedup    : {speedup:7.2f}x")
    print("=" * 60)


if __name__ == "__main__":
    main()
