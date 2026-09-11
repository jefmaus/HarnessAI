# Guía y Plantilla Universal de Especificaciones (Specs)

Este documento define el protocolo interactivo que el agente debe seguir para co-crear una nueva funcionalidad con el desarrollador, junto con la plantilla obligatoria para el archivo `spec.md`. Es compatible con arquitecturas monolíticas, microservicios, monorepos, CLIs, librerías y aplicaciones frontend.

---

## PARTE 1: Protocolo de Co-Creación (5 Pasos Obligatorios)

Antes de generar el archivo, el agente asume el rol de arquitecto de software y ejecuta estos pasos en orden:

### Paso 1: Cálculo Autónomo del Siguiente ID (Sin preguntar al usuario)
El agente calcula el número de forma autónoma:
1. Inspecciona los nombres de carpetas en `harness/specs/backlog/`, `harness/specs/active/` y `harness/specs/done/`.
2. Identifica el número de prefijo más alto existente (ej. si existe `014-login-lock`, el mayor es 14).
3. Suma +1 y formatea el nuevo ID a 3 dígitos con ceros a la izquierda (ej. `015`). Si no hay carpetas previas, inicia en `001`.

### Paso 2: Asignación de Módulo / Servicio y Estrategia de Tests
El agente consulta la topología registrada en `AGENTS.md` o `harness/config.json` y acuerda:
1. **Módulo Objetivo:** ¿A qué servicio o componente aplica la feature? (Ej: `backend/auth`, `backend/billing`, `frontend`, o `global`).
2. **Estrategia de Tests:**
   * **Dedicada:** Tests en una carpeta específica (ej: `services/auth/tests/` o `src/test/java`).
   * **Colocalizada:** Tests adyacentes al código fuente (ej: Angular `*.spec.ts`, React `*.test.tsx`, Go `*_test.go`).
   * **Ninguna / Omitida:** Declarada explícitamente para módulos visuales o prototipos sin suite automatizada.

### Paso 3: Nombre de la Feature, Slug y Reglas de Negocio
El agente pregunta al usuario:
1. **Nombre y Slug:** "¿Cómo se llamará la feature? (Propongo el slug `XXX-<nombre-corto>`, ¿te parece bien o prefieres otro?)".
2. **Propósito:** ¿Cuál es el objetivo exacto de la funcionalidad?
3. **Reglas duras:** ¿Qué restricciones de negocio aplican? (Límites, validaciones, expiración, estados válidos).
4. **Precondiciones:** ¿Qué estado previo requiere el sistema antes de ejecutar la acción?

### Paso 4: Definición de Contratos Técnicos (Agnóstico de Plataforma)
Dependiendo del tipo de funcionalidad, acuerdan la interfaz técnica:
* **Para APIs / Servicios (HTTP, REST, gRPC):** Métodos, rutas, headers, payloads JSON de entrada, respuestas exitosas y errores con códigos de estado.
* **Para CLIs / Scripts:** Comandos, argumentos posicionales, flags, formato de stdout/stderr y códigos de retorno (`0`, `1`, etc.).
* **Para Librerías / Módulos de Dominio:** Interfaces, firmas de clases/funciones, tipos de datos y excepciones lanzadas.
* **Para Frontend / UI:** Componentes, estados visuales (carga, éxito, error), eventos de usuario y llamadas a servicios.

### Paso 5: Redactar Criterios de Aceptación y Crear el Archivo
1. Traducir las reglas y casos borde a criterios deterministas: `CA-1`, `CA-2`, etc.
2. Cada criterio debe ser comprobable (mediante una prueba unitaria o verificación definida).
3. **Regla estricta:** Usar viñetas informativas (`*`), NUNCA casillas de verificación (`[ ]`). Las casillas de progreso pertenecen exclusivamente a `harness/specs/tasks.md`.
4. Crear el archivo final en: `harness/specs/backlog/<ID>-<slug>/spec.md`.

---

## PARTE 2: Plantilla Oficial de spec.md

Todo archivo creado dentro de `harness/specs/backlog/<ID>-<slug>/spec.md` debe respetar esta estructura:

```markdown
# Feature: [ID-Slug] - [Nombre Descriptivo de la Feature]

## 0. Metadatos de la Feature
* **Módulo Afectado:** `[nombre_modulo]` (ej. `services/auth`, `frontend`, `raiz`)
* **Estrategia de Tests:** `[dedicada | colocalizada | ninguna]`
* **Ruta Base de Código:** `[ruta relativa]` (ej. `services/auth/src/`)
* **Ubicación de Tests:** `[ruta o patrón]` (ej. `services/auth/tests/` o `*.spec.ts colocalizado`)

## 1. Requisitos de Negocio
* [Regla 1: Descripción clara e inequívoca del comportamiento esperado].
* [Regla 2: Restricciones operativas, tipos permitidos o tiempos de expiración].
* [Regla 3: Comportamiento ante entradas o estados inválidos].

## 2. Contratos y Esquemas

<!-- SELECCIONAR LA VARIANTE APROPIADA SEGÚN EL TIPO DE PROYECTO -->

### Variante A: APIs / Servicios (REST / JSON)
#### Entrada (Request)
- **Método / Endpoint:** `POST /api/v1/ejemplo`
- **Headers:** `Content-Type: application/json`
- **Payload:**
```json
{
  "campo_requerido": "string",
  "limite": 5
}
```
#### Salida Exitosa (Response)
- **Status:** `200 OK`
```json
{
  "status": "SUCCESS",
  "data": { "id": "uuid", "resultado": "ok" }
}
```
#### Salidas de Error
- **Status:** `400 Bad Request` -> `{"error": "INVALID_INPUT", "detail": "Mensaje"}`
- **Status:** `401 Unauthorized` -> `{"error": "UNAUTHORIZED"}`

---

### Variante B: CLIs / Comandos de Terminal
- **Comando:** `app-cli process --input <archivo> [--dry-run]`
- **Salida estándar (stdout):** `Resumen de procesamiento en formato tabular o JSON`
- **Salida de error (stderr):** `Mensaje de error y sugerencia de uso`
- **Códigos de salida:** `0` (éxito), `1` (archivo no encontrado), `2` (parámetros inválidos)

---

### Variante C: Librerías / Módulos de Dominio (Código interno)
- **Firma / Interfaz:** `calculate_tax(amount: Decimal, region: str) -> TaxBreakdown`
- **Precondiciones:** `amount > 0`, `region` debe ser un código ISO-3166 válido.
- **Excepciones:** Lanza `InvalidRegionError` si la región no está registrada.

---

### Variante D: Componentes Frontend / UI
- **Componente:** `LoginFormComponent`
- **Inputs:** `redirectUrl: string`
- **Outputs:** `onLoginSuccess(token: string)`
- **Estados:** `idle` | `submitting` (spinner activo, botón deshabilitado) | `error` (banner rojo con mensaje accesible)

## 3. Criterios de Aceptación (Inmutables)
* **CA-1:** [Condición inicial] -> [Acción disparada] -> [Resultado esperado verificable].
* **CA-2:** Enviar parámetros incompletos o tipos inválidos rechaza la operación con el error esperado.
* **CA-3:** Operaciones que superen el límite establecido son bloqueadas deterministamente.
```
