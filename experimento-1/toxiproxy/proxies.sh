#!/usr/bin/env bash
set -e

curl -s -X POST http://localhost:8474/proxies \
  -H "Content-Type: application/json" \
  -d '{
    "name":"api_proxy",
    "listen":"0.0.0.0:8666",
    "upstream":"api:5000"
  }' | jq .

echo "OK: api_proxy creado (8666 -> api:5000)"