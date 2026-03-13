# Auth Service - Experimento 2

Servicio simple de autenticación para emitir JWT válidos e inválidos para el experimento de seguridad.

## Endpoints

- GET /health
- GET /auth/config
- POST /auth/login
- POST /auth/token
- POST /auth/token-expired
- POST /auth/token-role-insufficient
- POST /auth/token-malformed
- POST /auth/token-tampered

## Variables de entorno

- JWT_SECRET
- JWT_ALGORITHM
- JWT_ISSUER
- JWT_AUDIENCE
- JWT_EXP_MINUTES

## Puerto

5002

## Generación de tokens de prueba

### Token válido
```bash
curl -X POST http://localhost:5002/auth/token \
  -H "Content-Type: application/json" \
  -d '{
    "username":"team14",
    "role":"admin",
    "permissions":["items:read","items:write"],
    "expires_in_minutes":15
  }'
  ```

### Token expirado
```bash
curl -X POST http://localhost:5002/auth/token-expired \
  -H "Content-Type: application/json" \
  -d '{
    "username":"team14",
    "role":"admin",
    "permissions":["items:read","items:write"]
  }'
```

### Token con rol insuficiente
```bash
  curl -X POST http://localhost:5002/auth/token-role-insufficient \
  -H "Content-Type: application/json" \
  -d '{
    "username":"team14"
  }'
```

### Token malformado
```bash
curl -X POST http://localhost:5002/auth/token-malformed
```

### Token adulterado
```bash
curl -X POST http://localhost:5002/auth/token-tampered \
  -H "Content-Type: application/json" \
  -d '{
    "username":"team14",
    "role":"admin",
    "permissions":["items:read","items:write"]
  }'
```

### Solicitud sin token
```bash
curl -i http://localhost:7001/api/items 
```

### Solicitud con token válido

- Primero generar el token:

```bash
curl -X POST http://localhost:5002/auth/token \
  -H "Content-Type: application/json" \
  -d '{
    "username":"team14",
    "role":"admin",
    "permissions":["items:read","items:write"]
  }'
```
- Luego invocar el gateway usando el access_token obtenido:

```bash
  curl -i http://localhost:7001/api/items \
  -H "Authorization: Bearer TOKEN_AQUI"
```

### Solicitud con token expirado
Resultado esperado: 401 Unauthorized
```bash
  curl -i http://localhost:7001/api/items \
  -H "Authorization: Bearer TOKEN_EXPIRADO_AQUI"
```

### Solicitud con rol insuficiente
Resultado esperado: 403 Forbidden
```bash
  curl -i http://localhost:7001/api/items \
  -H "Authorization: Bearer TOKEN_VIEWER_AQUI"
```

### Solicitud con rol insuficiente
Resultado esperado: 401 Unauthorized
```bash
  curl -i http://localhost:7001/api/items \
  -H "Authorization: Bearer TOKEN_ADULTERADO_AQUI"
```

### Solicitud con token malformado
Resultado esperado: 401 Unauthorized
```bash
  curl -i http://localhost:7001/api/items \
  -H "Authorization: Bearer abc.def"
```

### Validación de no procesamiento en microservicio
docker compose logs gateway --tail=100
docker compose logs api --tail=100


Resultados esperados

| Caso | Tipo de solicitud | Resultado esperado |
|------|-------------------|-------------------|
| 1 | Sin token | 401 |
| 2 | Token válido (`admin`) | 200 |
| 3 | Token expirado | 401 |
| 4 | Token con rol insuficiente (`viewer`) | 403 |
| 5 | Token adulterado | 401 |
| 6 | Token malformado | 401 |

### Medida del experimento
- Solicitudes inválidas enviadas: **5**
- Solicitudes inválidas rechazadas por el gateway: **5**
- Solicitudes inválidas procesadas por el microservicio: **0**

### Criterio de aceptación
El experimento se considera exitoso si:
- El **100%** de las solicitudes con tokens inválidos son rechazadas por el API Gateway.
- Ninguna solicitud inválida llega a ser procesada por el microservicio.
- Las respuestas de rechazo corresponden a códigos HTTP **401** o **403**, según el tipo de error.
