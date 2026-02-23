# Experimento 1 - Load Test

## Requisitos
- JMeter instalado (modo no-GUI)

## Ejecutar Baseline (sin fallas)
- Endpoint: http://localhost/api/items

## Ejecutar (ejemplo)
jmeter -n -t experiment1.jmx -l results/baseline.jtl -e -o results/baseline-report

## Ejecutar con falla (latency 2s)
1) Activar toxic en toxiproxy (ver /toxiproxy)
2) Correr JMeter y guardar report