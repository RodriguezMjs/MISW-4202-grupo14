#!/usr/bin/env bash
set -e

# Borra todos los toxics
curl -s -X GET http://localhost:8474/proxies/api_proxy/toxics | jq -r 'keys[]' | while read -r t; do
  curl -s -X DELETE "http://localhost:8474/proxies/api_proxy/toxics/$t" | jq .
done

echo "Toxics eliminados"