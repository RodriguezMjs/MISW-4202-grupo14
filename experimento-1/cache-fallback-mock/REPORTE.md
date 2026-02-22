# Experimento: Replicacion PostgreSQL + Cache Valkey
## TravelHub — Validacion de resiliencia ante fallas

---

## Hipotesis

> El sistema mantiene disponibilidad ante fallas de dependencias mediante
> cache fallback y errores controlados, sin propagacion en cascada.

---

## Arquitectura del experimento

```
[Cliente / Script]
       |
       v
[cache-fallback-mock :5000]
       |
       +---> [Valkey :6379]         (cache compartido)
       |
       +---> [postgres-replica :5433]  (lecturas)
                    |
             replica streaming
                    |
             [postgres-primary :5432]  (escrituras)
```

Todos los contenedores corren en la red Docker `travelhub-net`.

---

## Componentes

| Contenedor           | Imagen          | Puerto | Rol                              |
|----------------------|-----------------|--------|----------------------------------|
| postgres-primary     | postgres:14     | 5432   | BD principal, recibe escrituras  |
| postgres-replica     | postgres:14     | 5433   | Solo lectura, replica en tiempo real |
| valkey               | valkey/valkey:8 | 6379   | Cache compartido                 |
| cache-fallback-mock  | python:3.11     | 5000   | Mock que demuestra cache-aside   |

---

## Tacticas de arquitectura validadas

- **Replicacion activa**: datos replicados en tiempo real desde Primary a Replica via WAL streaming.
- **Cache-aside**: el servicio busca en Valkey antes de ir a la BD; guarda el resultado si no habia cache.
- **Cache fallback**: si la BD cae, el cache sirve la ultima respuesta conocida.
- **Fail-fast controlado**: si no hay ni BD ni cache, el sistema responde HTTP 503 con mensaje claro en lugar de colgarse.

---

## Como ejecutar

### Requisitos

- Docker y Docker Compose instalados
- Python 3.11+

### 1. Levantar la infraestructura

Desde la carpeta `experimento-1/`:

```bash
docker compose up -d
```

Verificar que todos los contenedores esten corriendo:

```bash
docker compose ps
```

### 2. Ejecutar el experimento automatizado

```bash
cd cache-fallback-mock
python -m venv venv
source venv/bin/activate
pip install requests docker
python experimento_replicacion.py
```

### 3. Detener sin perder datos

```bash
docker compose stop
```

### 4. Reset completo

```bash
docker compose down -v
```

---

## Resultados obtenidos

| Escenario                               | Source | Ejecucion inicial | Ejecucion en video | Resultado  |
|-----------------------------------------|--------|-------------------|--------------------|------------|
| Cache miss — primera request            | database | 16.64ms         | 28.05ms            | OK         |
| Cache hit — segunda request             | cache    | 1.51ms          | 1.01ms             | OK         |
| Cache fallback — replica caida          | cache    | 1.40ms          | 1.30ms             | OK         |
| Falla total — replica caida + sin cache | none     | —               | —                  | OK (503)   |

Los tiempos de cache miss varian segun la carga del sistema (16ms - 28ms) debido a la cantidad
de contenedores corriendo simultaneamente. Los tiempos de cache hit se mantienen estables
por debajo de 2ms independientemente de la carga.

**Ejecucion inicial: el cache es 11x mas rapido que la BD directa.**
**Ejecucion en video: el cache es 27.8x mas rapido que la BD directa.**

---

## Analisis

### Escenario 1 — Cache Miss
Primera request sin cache previo. El servicio consulta PostgreSQL Replica
y almacena el resultado en Valkey con TTL de 30 segundos. Tiempo: 16.64ms.

### Escenario 2 — Cache Hit
Segunda request dentro del TTL. El servicio responde directamente desde
Valkey sin tocar la BD. Tiempo: 1.51ms — reduccion del 91% respecto a BD directa.

### Escenario 3 — Cache Fallback
Con la Replica detenida y cache vivo, el servicio responde desde Valkey
sin errores. El cliente no percibe la caida de la BD. Tiempo: 1.40ms.
Demuestra que la tactica de cache fallback funciona correctamente.

### Escenario 4 — Falla Total
Con la Replica detenida y cache limpiado manualmente (simula TTL expirado),
el servicio responde HTTP 503 con mensaje de error controlado. No hay
colgamiento ni propagacion en cascada — falla rapido y de forma explicita.

---

## Conclusion

La hipotesis se cumple. Los resultados demuestran que:

1. La replicacion PostgreSQL mantiene disponibilidad de lecturas ante falla del Primary.
2. El cache Valkey reduce la latencia en un 91% en condiciones normales.
3. Ante falla de BD con cache vivo, el sistema continua respondiendo sin degradacion perceptible.
4. Ante falla total (BD + cache), el sistema falla de forma controlada con HTTP 503, sin cascada.
