# API Flask (master-only)

Pequeña API en Flask que se conecta únicamente al master PostgreSQL. Incluye endpoints para crear y listar `items`.

Variables de entorno (opcional):

- `DB_HOST` (default: `postgres-primary`)
- `DB_PORT` (default: `5432`)
- `DB_NAME` (default: `travelhub`)
- `DB_USER` (default: `postgres`)
- `DB_PASSWORD` (default: `postgres_pass`)

Ejecutar local (virtualenv):
```bash
python -m pip install -r requirements.txt
python app.py
```

Construir imagen Docker:
```bash
docker build -t travelhub-api .
```

Notas:
- Esta implementación mantiene una sola conexión al master; el ruteo read/write se gestionará externamente (proxy/balanceador) si se agrega en el futuro.
