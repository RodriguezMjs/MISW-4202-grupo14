#!/usr/bin/env bash
set -euo pipefail

echo "Esperando que el Primary esté listo..."
until pg_isready -h postgres-primary -p 5432 -U postgres; do
  sleep 2
done

echo "Primary listo. Iniciando replicación..."

rm -rf /var/lib/postgresql/data/*

pg_basebackup \
  -h postgres-primary \
  -p 5432 \
  -U replicator \
  -D /var/lib/postgresql/data \
  -Fp \
  -Xs \
  -P \
  -R

chown -R postgres:postgres /var/lib/postgresql/data
chmod 700 /var/lib/postgresql/data

echo "Arrancando PostgreSQL como replica..."
exec gosu postgres postgres
