#!/usr/bin/env bash
set -e

curl -s -X POST http://localhost:8474/proxies/api_proxy/toxics \
  -H "Content-Type: application/json" \
  -d '{
    "name":"latency_2s",
    "type":"latency",
    "stream":"downstream",
    "attributes":{"latency":2000,"jitter":100}
  }' | jq .

echo "Toxic aplicado: latency_2s"