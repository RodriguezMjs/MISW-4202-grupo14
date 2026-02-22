"""
experimento_replicacion.py
--------------------------
Script que automatiza y valida los 4 escenarios del experimento de
replicacion PostgreSQL + cache Valkey.

Requisitos:
    pip install requests docker

Uso:
    python experimento_replicacion.py
"""

import time
import requests
import docker

BASE_URL = "http://localhost:5000"
PRIMARY_CONTAINER = "postgres-primary"
REPLICA_CONTAINER = "postgres-replica"

docker_client = docker.from_env()

# -- Helpers -------------------------------------------------------------------

def separador(titulo):
    print(f"\n{'='*55}")
    print(f"  {titulo}")
    print(f"{'='*55}")

def resultado(ok, mensaje):
    estado = "OK  " if ok else "FAIL"
    print(f"  [{estado}] {mensaje}")

def get_hotels():
    r = requests.get(f"{BASE_URL}/hotels", timeout=10)
    return r.json(), r.status_code

def clear_cache():
    requests.post(f"{BASE_URL}/cache/clear", timeout=5)

def stop_container(name):
    docker_client.containers.get(name).stop()
    print(f"  [STOP] Contenedor '{name}' detenido")

def start_container(name):
    docker_client.containers.get(name).start()
    print(f"  [START] Contenedor '{name}' iniciado")

def esperar(segundos, motivo):
    print(f"  [WAIT] Esperando {segundos}s ({motivo})...")
    time.sleep(segundos)

# -- Escenarios ----------------------------------------------------------------

def escenario_1_cache_miss():
    separador("ESCENARIO 1 -- Cache Miss (primera request)")
    clear_cache()
    data, status = get_hotels()
    source = data.get("source")
    ms = data.get("response_ms")
    ok = source == "database"
    resultado(ok, f"source='{source}' | {ms}ms | esperado: 'database'")
    return ms

def escenario_2_cache_hit():
    separador("ESCENARIO 2 -- Cache Hit (segunda request)")
    data, status = get_hotels()
    source = data.get("source")
    ms = data.get("response_ms")
    ttl = data.get("ttl_remaining_seconds")
    ok = source == "cache"
    resultado(ok, f"source='{source}' | {ms}ms | TTL restante: {ttl}s | esperado: 'cache'")
    return ms

def escenario_3_cache_fallback():
    separador("ESCENARIO 3 -- Cache Fallback (Replica caida, cache vivo)")
    stop_container(REPLICA_CONTAINER)
    esperar(3, "replica terminando")
    data, status = get_hotels()
    source = data.get("source")
    ms = data.get("response_ms")
    ok = source == "cache"
    resultado(ok, f"source='{source}' | {ms}ms | esperado: 'cache' (sirviendo aunque BD caida)")
    start_container(REPLICA_CONTAINER)
    esperar(5, "replica levantando")
    return ms

def escenario_4_falla_total():
    separador("ESCENARIO 4 -- Falla Total (Replica caida + sin cache)")
    stop_container(REPLICA_CONTAINER)
    esperar(3, "replica terminando")
    clear_cache()
    try:
        data, status = get_hotels()
        source = data.get("source")
        ok = source == "none" and status == 503
        resultado(ok, f"source='{source}' | HTTP {status} | esperado: 'none' con 503")
    except Exception as e:
        resultado(False, f"Error inesperado: {e}")
    finally:
        start_container(REPLICA_CONTAINER)
        esperar(5, "replica levantando")

# -- Resumen -------------------------------------------------------------------

def resumen(ms_database, ms_cache, ms_fallback):
    separador("RESUMEN DEL EXPERIMENTO")
    print(f"  {'Escenario':<40} {'Tiempo'}")
    print(f"  {'-'*50}")
    print(f"  {'Cache miss  (BD directa)':<40} {ms_database}ms")
    print(f"  {'Cache hit   (Valkey)':<40} {ms_cache}ms")
    print(f"  {'Cache fallback (BD caida)':<40} {ms_fallback}ms")

    if ms_database and ms_cache:
        mejora = round(ms_database / ms_cache, 1)
        print(f"\n  Cache es {mejora}x mas rapido que BD directa")

    print(f"\n  HIPOTESIS:")
    print(f"  El sistema mantiene disponibilidad ante fallas de dependencias")
    print(f"  mediante cache fallback y errores controlados (no cascada).")

    cumple = ms_cache < ms_database and ms_fallback < ms_database
    if cumple:
        print(f"\n  [OK  ] HIPOTESIS CUMPLIDA")
    else:
        print(f"\n  [FAIL] HIPOTESIS NO CUMPLIDA -- revisar configuracion")

# -- Main ----------------------------------------------------------------------

if __name__ == "__main__":
    print("\nEXPERIMENTO: Replicacion PostgreSQL + Cache Valkey")
    print("TravelHub -- Validacion de resiliencia ante fallas\n")

    ms_db       = escenario_1_cache_miss()
    ms_cache    = escenario_2_cache_hit()
    ms_fallback = escenario_3_cache_fallback()
    escenario_4_falla_total()

    resumen(ms_db, ms_cache, ms_fallback)
