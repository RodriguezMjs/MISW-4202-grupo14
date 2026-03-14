# Experimento 2

## Validación de integridad y autorización de JWT en el API Gateway

Este experimento valida que el **API Gateway verifica correctamente la
autenticidad y autorización de los tokens JWT antes de permitir que una
solicitud llegue a los microservicios**.

El objetivo es demostrar que:

-   solicitudes **con tokens válidos y roles autorizados** son
    procesadas por la API
-   solicitudes **sin token o con tokens inválidos** son rechazadas en
    el Gateway
-   las solicitudes rechazadas **no llegan al microservicio**

Este experimento valida la decisión arquitectónica de **centralizar la
seguridad en el API Gateway**.

------------------------------------------------------------------------

# Arquitectura del experimento

Cliente → API Gateway → Microservicio API

El API Gateway valida:

-   firma del JWT
-   expiración del token
-   estructura del token
-   rol autorizado

Solo si todas las validaciones son correctas la solicitud es enviada al
microservicio.

------------------------------------------------------------------------

# Servicios del sistema

  Servicio       Puerto   Función
  -------------- -------- -------------------------------------
  Auth Service   5002     Genera tokens JWT
  API Gateway    7001     Valida autenticación y autorización
  API Service    5001     Procesa solicitudes autorizadas

------------------------------------------------------------------------

# Endpoint protegido

GET /api/items

Este endpoint solo puede consumirse usando:

Authorization: Bearer `<JWT>`{=html}

------------------------------------------------------------------------

# Configuración JWT

Los tokens utilizan:

-   issuer: auth-service
-   audience: travelhub-clients
-   algorithm: HS256

El rol requerido para acceder al endpoint es:

admin

------------------------------------------------------------------------

# Escenarios evaluados

  Caso   Escenario                    Resultado esperado
  ------ ---------------------------- --------------------
  1      Solicitud sin token          401 Unauthorized
  2      Token válido con rol admin   200 OK
  3      Token expirado               401 Unauthorized
  4      Token con rol insuficiente   403 Forbidden
  5      Token malformado             401 Unauthorized
  6      Token adulterado             401 Unauthorized

------------------------------------------------------------------------

# Evidencias

Las evidencias del experimento se generan en tres niveles:

1.  **Respuesta HTTP**
2.  **Logs del API Gateway**
3.  **Logs del microservicio API**

Estas evidencias permiten verificar si el Gateway bloquea correctamente
las solicitudes antes de que lleguen al microservicio.

------------------------------------------------------------------------

# Evidencia 1: Solicitud sin token

Resultado esperado:

HTTP 401 Unauthorized

Error devuelto:

MISSING_OR_INVALID_AUTH_HEADER

Interpretación:

El Gateway detecta que la solicitud no incluye el header Authorization y
la rechaza inmediatamente.

Los logs del Gateway muestran el rechazo y la API no procesa la
solicitud.

------------------------------------------------------------------------

# Evidencia 2: Token válido con rol admin

Resultado esperado:

HTTP 200 OK

Respuesta:

\[{"id":1,"name":"item-1"},{"id":2,"name":"item-2"}\]

Interpretación:

El Gateway valida correctamente:

-   firma
-   expiración
-   issuer
-   audience
-   rol admin

Luego reenvía la solicitud al microservicio.

Los logs del Gateway muestran aceptación del token y los logs de la API
muestran procesamiento del endpoint.

------------------------------------------------------------------------

# Evidencia 3: Token expirado

Resultado esperado:

HTTP 401 Unauthorized

Error:

TOKEN_EXPIRED

Interpretación:

El Gateway valida el claim exp del JWT y detecta que el token ya no es
válido.

La solicitud es rechazada antes de llegar a la API.

------------------------------------------------------------------------

# Evidencia 4: Rol insuficiente

Resultado esperado:

HTTP 403 Forbidden

El token contiene el rol:

viewer

El endpoint requiere:

admin

Interpretación:

El Gateway valida el claim role y detecta que el usuario no tiene
permisos para acceder al recurso.

La solicitud es bloqueada.

------------------------------------------------------------------------

# Evidencia 5: Token malformado

Resultado esperado:

HTTP 401 Unauthorized

Error:

MALFORMED_TOKEN

Interpretación:

El Gateway detecta que el token no tiene una estructura JWT válida.

La solicitud es rechazada inmediatamente.

------------------------------------------------------------------------

# Evidencia 6: Token adulterado

Resultado esperado:

HTTP 401 Unauthorized

Error:

INVALID_SIGNATURE

Interpretación:

El Gateway valida la firma criptográfica del JWT.

Si el contenido fue alterado, la firma ya no coincide con la clave
secreta.

El Gateway detecta esta manipulación y bloquea la solicitud.

------------------------------------------------------------------------

# Resultados del experimento

  Caso                 Resultado esperado   Resultado obtenido   Llegó a API
  -------------------- -------------------- -------------------- -------------
  Sin token            401                  401                  No
  Token válido admin   200                  200                  Sí
  Token expirado       401                  401                  No
  Rol insuficiente     403                  403                  No
  Token malformado     401                  401                  No
  Token adulterado     401                  401                  No

------------------------------------------------------------------------

# Conclusión

El experimento confirma la hipótesis de diseño:

El API Gateway valida correctamente la integridad, autenticación y
autorización de los tokens JWT antes de enrutar solicitudes a los
microservicios.

Esto demuestra que la decisión arquitectónica de **centralizar la
seguridad en el Gateway** protege los microservicios contra solicitudes
no autorizadas.
