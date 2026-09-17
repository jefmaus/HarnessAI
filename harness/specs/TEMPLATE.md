# Guía y Plantilla Universal de Especificaciones (Specs)

Este documento define el protocolo interactivo que el agente debe seguir para co-crear cualquier especificación con el desarrollador, junto con la plantilla universal para el archivo `spec.md`. Es compatible con cualquier tipo de proyecto (monolitos, microservicios, monorepos, CLIs, librerías, frontends, APIs) y cualquier tipo de trabajo de ingeniería (features nuevas, corrección de bugs, tareas batch/cron, colas de mensajería, refactors y migraciones).

---

## PARTE 1: Protocolo de Co-Creación Interactivo (6 Pasos y 1 Checkpoint Obligatorio)

Antes de generar cualquier archivo, el agente asume el rol de arquitecto de software y ejecuta estos pasos conversacionales en orden estricto:

### Paso 1: Cálculo Autónomo del Siguiente ID (Sin preguntar al usuario)
El ID se calcula de forma **determinista e infalible** ejecutando el script del arnés:
```bash
python harness/scripts/new-spec.py <slug> [--title "Nombre descriptivo"]
```
1. El script inspecciona los prefijos numéricos en `harness/specs/backlog/`, `harness/specs/active/` y `harness/specs/done/`.
2. Toma el máximo, suma +1 y formatea a 3 dígitos (`001`, `015`, …).
3. **Rechaza en seco** slugs mal formados (deben ser `kebab-case`) e IDs numéricos duplicados entre carpetas; avisa de carpetas sin prefijo `NNN-` para que las renombres.
4. Materializa el esqueleto de la spec **solo tras el CHECKPOINT** (ver abajo) con el campo de evidencia `Aprobada:`.

### Paso 2: Asignación de Módulo / Servicio, Arquitectura y Estrategia de Tests
El agente consulta la topología registrada en `AGENTS.md` o `harness/config.json` y acuerda con el usuario:
1. **Módulo(s) Objetivo:** ¿A qué servicio(s) o componente(s) aplica la spec? (Ej: `core`, `api`, `frontend`, o combinación en monorepos).
2. **Arquitectura del Módulo:**
   * Si el módulo ya existe: el agente adopta la arquitectura declarada, priorizando simplicidad y rendimiento, aplicando principios de diseño (como SOLID, KISS o YAGNI) de forma pragmática según el contexto.
   * Si da origen a un nuevo microservicio: el agente propone su arquitectura (Clean, Hexagonal, Layered, etc.) y filosofía de diseño, validando con el usuario antes de materializar el archivo.
3. **Estrategia de Tests:**
   * **Dedicada:** Tests en una carpeta específica (ej: `<modulo>/tests/` o `tests/unit/`).
   * **Colocalizada:** Tests adyacentes al código fuente (ej: `*.spec.ts`, `*_test.go`).
   * **Ninguna / Omitida:** Solo si se declara formalmente para prototipos o maquetación sin suite automatizada.

### Paso 3: Diálogo de Alcance y Requisitos (Adaptativo según el Tipo de Tarea)
El agente **NO asume ni inventa** reglas ni alcance por su cuenta. Identifica el tipo de tarea y entrevista al desarrollador en el chat:

0. **Alineación Estratégica con la Visión 360° (Mandatoria):**
   Antes de entrar en detalles de pantallas o código, el agente consulta `AGENTS.md` (Sección 1) y valida con el desarrollador:
   * **Contribución al Valor:** ¿Cómo contribuye esta spec al **Propósito General** de la aplicación?
   * **Control de Alcance:** ¿La funcionalidad está dentro de los límites **In-Scope** o roza aspectos catalogados como **Out-of-Scope**? (Si amplía el alcance o introduce dependencias no contempladas, exige confirmación explícita del usuario).
   * **Lenguaje Ubicuo:** ¿Qué entidades troncales del dominio se ven involucradas o enriquecidas?

1. **Nombre y Slug propuesto:** Sugiere el formato `XXX-<nombre-corto>`.
2. **Tipo de Tarea:**
   * **Feature / Nueva Funcionalidad:** Pregunta qué flujos, pantallas, campos, opciones y reglas de negocio requiere.
   * **Bugfix / Corrección de Error:** Pregunta cuál es el síntoma observado, bajo qué condiciones se reproduce el fallo, qué comportamiento es el erróneo vs el esperado, y si hay excepciones o trazas conocidas.
   * **Tarea Programada / Proceso Batch (Cron / Worker):** Pregunta la periodicidad/trigger, el criterio de selección de los datos/lotes, las mutaciones o efectos secundarios esperados, y qué ocurre en reintentos o ejecuciones repetidas.
   * **Colas de Mensajería / Event-Driven:** Pregunta el canal/tópico/cola, formato del mensaje, estrategia de ACK, timeouts y manejo de mensajes fallidos (DLQ).
   * **Refactor / Optimización:** Pregunta qué cuello de botella o deuda técnica se busca resolver, qué interfaces públicas deben permanecer inalteradas (compatibilidad retroactiva) y qué métrica o SLA se espera mejorar.
   * **Migración de Base de Datos:** Pregunta el esquema actual, cambios requeridos en modelos/tablas y estrategia de retrocompatibilidad/rollback.

### Paso 3.5: Criterio de Diseño, Simplicidad y Rendimiento (Diseño Pragmático)
Antes de proponer contratos, el agente evalúa la solución bajo un enfoque de ingeniería pragmática:
* **Simplicidad (KISS / YAGNI):** Diseñar la solución más directa y comprensible posible. No introducir capas intermedias, interfaces o abstracciones para casos hipotéticos futuros.
* **Impacto en Rendimiento:** Asegurar que la estructura propuesta no agregue indirecciones innecesarias, llamadas costosas ni sobrecarga de memoria en rutas críticas.
* **SOLID como Guía Opcional (No Dogmática):** Si la modularidad del componente realmente lo amerita (y sin penalizar el rendimiento), evaluar principios pertinentes (ej. Responsabilidad Única para no sobrecargar módulos, o Inversión de Dependencias para facilitar testing). No forzar el desglose de los 5 principios si la tarea no lo requiere.

### Paso 4: Propuesta de Contratos Técnicos o Invariantes (En el Chat)
Con base en las respuestas, el agente redacta y presenta en el chat la propuesta técnica adecuada a la naturaleza del trabajo (¡NO inventar APIs ni códigos HTTP si no aplican!):
* **Criterio de Diseño:** La propuesta técnica debe respetar la arquitectura del módulo, priorizando código simple, legible y de alto rendimiento (KISS/YAGNI). Los principios de diseño (como SOLID) se aplican solo como sugerencias de buenas prácticas donde aporten valor real.
* **Para APIs / Servicios Web:** Métodos, endpoints, payloads de request, respuestas exitosas y códigos de error (ej. 200, 201, 400, 401, 409).
* **Para Interfaces UI / Frontend:** Vistas/componentes, inputs/props, eventos/outputs, estados visuales (`idle`, `submitting`, `success`, `error`).
* **Para Procesos Batch / Crons:** Trigger/expresión cron, query o filtro de selección de lote, mutaciones en base de datos/archivos, reporte/telemetría de ejecución e idempotencia.
* **Para Colas / Workers Asíncronos:** Nombre de cola/tópico, esquema JSON del payload, consumidor/handler, política de reintentos y Dead-Letter Queue.
* **Para Bugfixes:** **Contrato de Invariantes**: Caso de reproducción determinista (input que causa el fallo), comportamiento anómalo actual vs comportamiento correcto esperado, y test de regresión que debe pasar a verde.
* **Para Refactors / Optimizaciones:** Invariante externa (la API o firmas existentes no sufren cambios de ruptura) y métrica/condición de aceptación técnica.
* **Para Migraciones de Base de Datos:** DDL Up/Down, estrategia sin bloqueo de tablas (zero-downtime), script de rollback y validación de datos existentes.
* **Para CLIs / Scripts:** Comando, flags/argumentos, stdout, stderr y exit codes.
* **Para Librerías / Capa de Dominio:** Firmas de funciones/clases, tipos de parámetros, precondiciones y excepciones esperadas.

### Paso 5: Propuesta de Criterios de Aceptación (CA-*) (En el Chat)
El agente traduce las reglas a una lista numerada de criterios deterministas y comprobables:
* Formato: `CA-1`, `CA-2`, `CA-3`...
* Cada criterio debe ser comprobable mediante una prueba automatizada o verificación formal.
* **Cada `CA-*` debe citar el comando exacto que lo certifica** (ej. `verify.py auth`, `node --test src/validate.test.js`). Un CA sin comando de verificación es ambiguo y no es aceptable.
* En bugfixes, al menos un criterio (`CA-1`) debe certificar que el caso de reproducción deja de fallar (test de regresión).
* En batch/crons, al menos un criterio debe certificar la idempotencia o el procesamiento correcto del lote.
* **Regla estricta:** Usar viñetas informativas (`*`), NUNCA casillas de verificación (`[ ]`).

### ⛔ CHECKPOINT OBLIGATORIO: Aprobación Previa del Desarrollador
> **REGLA DE PARADA INFRANQUEABLE:**  
> Queda **TERMINANTEMENTE PROHIBIDO** crear o modificar archivos (`write_to_file`) en `harness/specs/backlog/` o `harness/specs/active/` antes de que el usuario haya revisado el borrador de contratos/invariantes y Criterios de Aceptación (`CA-*`) presentado en el chat y haya respondido con su **aprobación explícita** ("De acuerdo", "Aprobado", "Adelante" o similar). Si el usuario solicita ajustes, el agente debe corregir la propuesta en el chat y volver a solicitar confirmación.

### Paso 6: Materialización de la Spec y Pregunta de Activación
Solo tras recibir la aprobación expresa del usuario:
1. El agente materializa el archivo con el script del arnés (que calcula el ID y rechaza duplicados):
   ```bash
   python harness/scripts/new-spec.py <slug> --title "Nombre descriptivo"
   ```
   Luego completa el contenido (requisitos, contratos, CA-*) ya consensuado en el chat, y **rellena el campo `Aprobada:` con la fecha real del checkpoint** como evidencia auditable.
2. El agente pregunta al usuario: *"¿Deseas activar esta feature de inmediato para comenzar el ciclo TDD, o prefieres mantenerla en el backlog?"*.
   * Si decide activarla, se traslada de forma determinista (nunca a mano):
     ```bash
     python harness/scripts/activate-spec.py <ID-slug>
     ```
     El script garantiza que no haya otra feature activa, enlaza `tasks.md` con la cabecera `> Feature:` y el agente desglosa las micro-tareas atómicas (típicamente entre 3 y 12, sin límite rígido).

---

## PARTE 2: Plantilla Oficial de spec.md

Todo archivo creado dentro de `harness/specs/backlog/<ID>-<slug>/spec.md` debe respetar esta estructura base, seleccionando la(s) variante(s) técnica(s) aplicable(s):

```markdown
# [ID-Slug] - [Nombre Descriptivo de la Tarea]

## 0. Metadatos de la Spec
* **Tipo de Tarea:** `[feature | bugfix | refactor | performance | batch_job | event_worker | db_migration]`
* **Módulo Afectado:** `[nombre_modulo]` (ej. `core`, `api`, `frontend`, `global`)
* **Arquitectura de Referencia:** `[clean_architecture | hexagonal | layered | feature_sliced | etc.]`
* **Estrategia de Tests:** `[dedicated | co-located | none]` (acepta alias `dedicada | colocalizada | ninguna`)
* **Ruta Base de Código:** `[ruta relativa]` (ej. `src/` o `<modulo>/src/`)
* **Ubicación de Tests:** `[ruta o patrón]` (ej. `<modulo>/tests/` o `*.spec.ts colocalizado`)
* **Aprobada:** `[AAAA-MM-DD] por [usuario]` (evidencia del CHECKPOINT; obligatoria antes de activar)

## 1. Requisitos y Contexto
<!-- Explicación concisa y unívoca según el tipo de tarea -->
* **Objetivo de Negocio / Valor Aportado:** [Explicación concisa de cómo esta spec contribuye a la visión del producto y qué dolor resuelve al usuario o al sistema].
* [Regla o Comportamiento esperado 1].
* [Regla 2: Restricciones operativas, límites, expiraciones o formatos].
* [Regla 3: Comportamiento ante fallos, entradas anómalas o condiciones de carrera].

## 2. Contratos Técnicos e Invariantes

<!-- SELECCIONAR O COMBINAR LA(S) VARIANTE(S) APROPIADA(S) SEGÚN EL TIPO DE TRABAJO -->

### Variante A: APIs / Servicios de Red (REST / JSON / GraphQL / gRPC)
#### Entrada (Request)
- **Método / Endpoint:** `POST /api/v1/recurso`
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
- **Status:** `400 Bad Request` -> `{"error": "INVALID_INPUT", "detail": "Mensaje descriptivo"}`
- **Status:** `401 Unauthorized` -> `{"error": "UNAUTHORIZED"}`
- **Status:** `409 Conflict` -> `{"error": "ALREADY_EXISTS"}`

---

### Variante B: CLIs / Comandos de Terminal / Scripts
- **Comando de Invocación:** `app-cli process --input <archivo> [--dry-run]`
- **Parámetros / Flags:** `--input` (requerido, ruta a archivo), `--dry-run` (opcional, booleano)
- **Salida Estándar (stdout):** Resumen de ejecución tabular o JSON con total procesado.
- **Salida de Error (stderr):** Mensajes diagnósticos claros y sugerencia de uso ante fallo.
- **Códigos de Salida (Exit Codes):** `0` (éxito), `1` (archivo no encontrado), `2` (parámetros inválidos).

---

### Variante C: Librerías / Módulos de Dominio Interno
- **Firma / Interfaz:** `calculate_tax(amount: Decimal, region: str) -> TaxBreakdown`
- **Precondiciones:** `amount > 0`, `region` debe ser código ISO válido.
- **Postcondiciones:** Retorna instancia inmutable de `TaxBreakdown` con totales calculados.
- **Excepciones Tipadas:** Lanza `InvalidRegionError` si la región no existe en el catálogo.

---

### Variante D: Componentes UI / Frontend
- **Componente / Vista:** `DataFilterComponent`
- **Inputs / Props:** `categories: string[]`, `initialFilter?: string`
- **Outputs / Eventos:** `onFilterChange(selected: string)`
- **Estados Visuales:** `idle` | `loading` (indicador activo, control deshabilitado) | `empty` (mensaje de sin resultados) | `error` (alerta de fallo accesible)
- **Validaciones / Comportamiento:** Validación de entrada limpia y emisión reactiva del filtro seleccionado.

---

### Variante E: Tareas Programadas / Procesos Batch (Crons / Daemons)
- **Disparador / Frecuencia:** Expresión cron (ej. `0 2 * * *` - 2:00 AM diario) o comando CLI ejecutable.
- **Criterio de Selección (Scope del Lote):** Registros en almacén de datos con `status = 'stale'` y `updated_at < NOW() - 30d`.
- **Efectos Secundarios (Mutaciones):**
  - Actualiza el estado a `status = 'archived'`.
  - Emite registro de auditoría en la tabla o log de eventos.
- **Idempotencia:** Si el job se ejecuta dos veces consecutivas con el mismo lote, la segunda ejecución reporta 0 registros mutados sin generar duplicados.
- **Telemetría / Salida:** Log estructurado: `{"job": "archive_stale_records", "processed": 42, "failed": 0, "duration_ms": 180}`.

---

### Variante F: Eventos / Colas de Mensajería / Workers Asíncronos
- **Cola / Tópico:** `tasks.document_processing`
- **Esquema del Mensaje (Payload):**
```json
{
  "event_id": "uuid-v4",
  "event_type": "DOCUMENT_GENERATE",
  "timestamp": "2026-09-11T18:00:00Z",
  "payload": {
    "document_id": 1042,
    "format": "PDF",
    "requested_by": "service_core"
  }
}
```
- **Consumidor / Handler:** `DocumentProcessingWorker.handle(event)`
- **Estrategia de Confirmación (ACK):** ACK manual tras procesamiento exitoso; NACK con requeue en fallos transitorios.
- **Manejo de Errores y Reintentos:** Máximo 3 reintentos con backoff exponencial. Al 4to fallo se envía a Dead-Letter Queue (`tasks.document_processing.dlq`).

---

### Variante G: Bugfixes / Corrección de Defectos
- **Caso de Reproducción (El Fallo):**
  - *Pasos para reproducir:* Invocar `parse_record(data)` con una cadena que contenga caracteres de control o formato incompleto.
  - *Comportamiento erróneo actual:* Lanza una excepción no controlada `ValueError` provocando la interrupción del flujo sin liberar recursos.
- **Comportamiento Esperado / Invariante Restaurada:**
  - La función debe validar y descartar datos anómalos, retornando un resultado tipado de error controlado (`Result.failure`).
  - Cualquier recurso abierto o descriptor de archivo debe liberarse en un bloque `finally`.
- **Prueba de Regresión Obligatoria:** Test unitario `test_parse_record_handles_malformed_input()` que reproduzca el fallo inicial (rojo) y confirme la corrección sin efectos colaterales (verde).

---

### Variante H: Refactors Técnicos / Optimizaciones de Rendimiento
- **Motivación / Deuda Técnica:** Desacoplar la lógica de cálculo del controlador y eliminar consultas $N+1$ en consultas masivas.
- **Invariante Externa:** Cero cambios de ruptura en firmas públicas o interfaces expuestas. Todas las pruebas unitarias existentes deben seguir pasando en verde sin alteraciones.
- **Métrica / SLA de Rendimiento (si aplica):**
  - Reducción de consultas de $N+1$ a máximo 2 consultas.
  - Tiempo de ejecución para 1.000 registros inferior a 80ms verificado mediante benchmark.

---

### Variante I: Migraciones de Base de Datos / Cambios de Esquema
- **Motor / Herramienta:** PostgreSQL / SQLite / Alembic / Prisma / Flyway (según stack).
- **Operación DDL:** Adición de columna `status_code` a la tabla `entities` con índice no bloqueante.
- **Script UP (Migración):**
```sql
ALTER TABLE entities ADD COLUMN status_code VARCHAR(20) DEFAULT 'ACTIVE';
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_entities_status_code ON entities(status_code);
```
- **Script DOWN (Reversión / Rollback):**
```sql
DROP INDEX IF EXISTS idx_entities_status_code;
ALTER TABLE entities DROP COLUMN status_code;
```
- **Estrategia de Retrocompatibilidad (Zero-Downtime):** La columna es nullable o posee un valor default seguro para no romper instancias de la aplicación en ejecución previa.
- **Verificación de Integridad:** Consulta de verificación posterior para asegurar que ningún registro preexistente quedó en estado inconsistente.

---

## 2.5. Consideraciones de Diseño y Rendimiento (Opcional)
<!-- Rellenar únicamente si amerita justificar trade-offs de arquitectura, simplicidad o rendimiento; omitir o indicar 'N/A' en tareas directas -->
* **Simplicidad y Performance:** [Cómo se evita la sobreingeniería y se cuida el rendimiento / N/A - Diseño directo]
* **Principios de Diseño (si aplica):** [Buenas prácticas o heurísticas aplicadas (ej. modularidad, desacoplamiento o SOLID) solo si aportan valor real sin penalizar performance]

## 3. Criterios de Aceptación (Inmutables)
* **CA-1:** [Condición inicial / Entrada / Trigger] -> [Acción disparada] -> [Resultado esperado verificable]. *Verifica con:* `[comando exacto]`.
* **CA-2:** Enviar parámetros incompletos, tipos inválidos o datos corruptos rechaza la operación de forma determinista y segura. *Verifica con:* `[comando exacto]`.
* **CA-3:** Operaciones concurrentes o repetidas respetan la idempotencia y no generan duplicaciones ni estados inconsistentes. *Verifica con:* `[comando exacto]`.
* **CA-4:** [En bugfixes] El test de regresión que recrea el fallo pasa exitosamente en verde sin efectos secundarios. *Verifica con:* `[comando exacto]`.
* **CA-5:** [En migraciones/refactors] La suite de pruebas de regresión pasa al 100% y la verificación confirma compatibilidad retroactiva. *Verifica con:* `[comando exacto]`.

## 4. Seguridad y Resiliencia (solo si aplica)
<!-- Rellenar únicamente las líneas pertinentes al caso; escribir 'no aplica' en las demás. -->
* **Secretos:** [no aplica | cómo se evita la fuga de credenciales / dónde se inyectan]
* **Validación de entradas:** [no aplica |_sanitización o límites de entrada_]
* **Límites o rollback:** [no aplica | timeout, reintentos o plan de reversión]
```
