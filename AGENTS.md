# Constitución del Agente y Reglas de Desarrollo

Este documento rige el comportamiento de cualquier agente de inteligencia artificial en este repositorio. Sus directivas son inmutables y de cumplimiento estricto.

---

## 0. Protocolo de Inicio de Sesión (On-Wakeup Routine)
Cada vez que el agente despierte o inicie una interacción en este repositorio:
1. **Verificar Estado del Arnés:** Consulta `harness/config.json`. Si `"configured": false`, no inventes stacks ni asumas rutas; solicita al usuario inicializar el arnés con: *"Configura el arnés siguiendo harness/SETUP_HARNESS.md"*.
2. **Verificar Barrera Física Activa:** Ejecuta `git config core.hooksPath`. Debe devolver `harness/.githooks` (esta configuración **no viaja con `git clone`**). Si está vacía o es otra, advierte al usuario y reactiva la barrera con `git config core.hooksPath harness/.githooks` antes de cualquier commit.
3. **Inspeccionar Foco Activo:** Comprueba si existe una carpeta en `harness/specs/active/`.
   * Si existe: Tu contexto de trabajo se limita estrictamente a `harness/specs/active/*/spec.md` y `harness/specs/tasks.md`. Lee ambos antes de proponer cambios o tocar código. Si hay **dos o más** carpetas, detente: es una violación de integridad y debes reportarla antes de continuar.
   * Si no existe: Pregunta al usuario si desea co-crear una nueva spec con `harness/specs/TEMPLATE.md` o activar una feature existente desde `harness/specs/backlog/`. Al co-crear, sigue obligatoriamente el diálogo interactivo y el CHECKPOINT de aprobación previa antes de escribir cualquier archivo.
4. **Restricción de Lectura (acotada):** Durante el **ciclo TDD** de una feature activa, queda prohibido inspeccionar archivos en `harness/specs/backlog/` o `harness/specs/done/` para evitar saturación de tokens y *context drift*. **Única excepción:** el flujo de co-creación/activación de specs (`TEMPLATE.md` y los scripts `new-spec.py` / `activate-spec.py`), donde inspeccionar esas carpetas es obligatorio para calcular IDs.

---

## 1. Topología del Proyecto y Stack Tecnológico
> [POR CONFIGURAR VÍA harness/SETUP_HARNESS.md]

* **Tipo de Repositorio:** [Single / Monorepo / Multi-Servicio]
* **Módulos Registrados:**

| Módulo / Servicio | Ruta Base | Runtime / Framework | Estrategia de Tests | Comando Verificación |
| :--- | :--- | :--- | :--- | :--- |
| *[Ej. auth-service]* | `services/auth` | Python 3.12 / FastAPI | Dedicada (`services/auth/tests/`) | `python harness/scripts/verify.py auth-service` |
| *[Ej. frontend]* | `frontend` | Angular 18 | Colocalizada (`*.spec.ts`) | `python harness/scripts/verify.py frontend` |

---

## 2. Máquina de Estados de Especificaciones (SDD)
* **`harness/specs/backlog/`:** Cola de espera. Solo se accede cuando el usuario ordene explícitamente co-crear o priorizar una especificación.
* **`harness/specs/active/`:** Foco de ejecución actual. **SOLO PUEDE EXISTIR EXACTAMENTE UNA CARPETA AQUÍ A LA VEZ**. Si hay dos, el sistema lo considerará una violación de integridad.
* **`harness/specs/done/`:** Histórico inmutable de funcionalidades concluidas y verificadas.
* **`harness/specs/tasks.md`:** Buffer de micro-tareas de la feature activa. **Debe llevar la cabecera `> Feature: <ID>-<slug>`** que lo vincula físicamente a la feature; `activate-spec.py` la escribe y `finish-feature.py` la exige.
* **Transiciones físicas (anti-alucinación):** crear specs con `python harness/scripts/new-spec.py <slug>`, activar con `python harness/scripts/activate-spec.py <ID-slug>` y cerrar con `python harness/scripts/finish-feature.py`. Está prohibido mover carpetas de specs a mano.
* **Sincronización Concurrente de IDs:** En entornos con múltiples desarrolladores, el hook `pre-push` ejecuta automáticamente `python harness/scripts/rebase-spec.py`. Si detecta colisión con `origin/main`, renumera la spec de forma determinista y crea el commit de ajuste antes de permitir el push. En pipelines de CI/CD (ej. Azure DevOps o GitHub Actions), el mismo script puede integrarse en la validación de Pull Requests para resolver colisiones automáticamente en la nube.
* **Co-Creación de Specs:** Proceso conversacional obligatorio gobernado por `harness/specs/TEMPLATE.md`. Jamás se debe generar el archivo físico `spec.md` en un solo turno asumiendo requisitos; requiere la aprobación explícita del usuario sobre los contratos técnicos o invariantes y criterios de aceptación en el chat.

---

## 3. Protocolo TDD Obligatorio y Adaptativo
1. **Lectura Previa:** Lee `harness/specs/active/*/spec.md` y verifica el Módulo Afectado y su Estrategia de Tests.
2. **Desglose de Tareas:** `tasks.md` ya debe estar vinculado a la feature activa (cabecera `> Feature:` escrita por `activate-spec.py`). Desglosa la spec en `harness/specs/tasks.md` en micro-tareas atómicas y manejables (típicamente entre 3 y 12 según la complejidad, sin límite rígido), donde cada tarea represente un ciclo TDD verificable.
3. **Selección:** Toma la siguiente tarea y márcala en progreso con `[-]`. Solo puede haber una tarea en `[-]` a la vez.
4. **Fase Roja (Según Estrategia del Módulo):**
   * **Estrategia Dedicada:** Escribe la prueba unitaria en el directorio de tests del módulo (ej. `services/auth/tests/`).
   * **Estrategia Colocalizada:** Escribe la prueba adyacente a la unidad de código (ej. `src/app/login/login.component.spec.ts` antes de `login.component.ts`).
   * **Estrategia Ninguna:** Si y solo si la spec declara explícitamente `Estrategia de Tests: Ninguna` (ej. maquetación visual), omite la prueba y documenta el motivo.
   * Ejecuta `python harness/scripts/verify.py <modulo>` y confirma que falle por la razón esperada.
5. **Fase Verde:** Escribe el código mínimo necesario en producción para que el test pase.
6. **Fase Refactor:** Limpia y optimiza manteniendo `python harness/scripts/verify.py <modulo>` en verde (`exit 0`).
7. **Completado:** Marca la micro-tarea con `[x]` en `harness/specs/tasks.md`.
8. **Commit:** Realiza un commit local describiendo la micro-tarea (Git disparará el pre-commit automáticamente).
9. **Cierre de Feature:** Cuando todas las micro-tareas de `tasks.md` estén marcadas con `[x]`, ejecuta:
   ```bash
   python harness/scripts/finish-feature.py
   ```
   El script exige el vínculo `> Feature:` y que `tasks.md` no esté en reposo. Tras archivar, **commitea el movimiento** (`git add -A && git commit -m "chore(specs): archivar <ID>-<slug>"`) para que el archivado quede en el historial.

---

## 4. Política de Memoria Técnica JIT (`harness/memory/`)
* **Qué se guarda:** Decisiones de arquitectura estructurales (ADRs), trampas sutiles de dependencias y soluciones a errores no triviales del entorno.
* **Qué NO se guarda:** Diffs de código, tareas rutinarias, bitácoras de conversación o explicaciones que Git ya preserva en el historial de commits.
* **Comandos:**
  * Consultar un registro por ID: `python harness/scripts/get-memory.py <ID>`
  * Registrar nuevo conocimiento: `python harness/scripts/save-memory.py "<modulo>" "<titulo>" "<contexto>" "<decision_o_solucion>"`

---

## 5. Deny-List (Acciones Prohibidas)
* Modificar archivos en `harness/.githooks/` sin orden expresa del usuario.
* Realizar commits o pushes con la bandera `--no-verify`.
* Escribir código de producción sin una prueba unitaria previa que lo justifique (salvo módulos con estrategia declarada formalmente como `none`).
* Intentar activar más de una feature simultáneamente en `harness/specs/active/`.
* Mover, renombrar o archivar carpetas de `specs/` a mano en lugar de usar `new-spec.py` / `activate-spec.py` / `finish-feature.py` (las transiciones de la máquina de estados son físicas y deterministas).
* Dejar comentarios `TODO` o bloques de código comentado en el código fuente.
* Crear o modificar archivos `spec.md` (en `backlog/` o `active/`) sin haber presentado previamente el borrador de reglas, contratos técnicos / invariantes y Criterios de Aceptación (`CA-*`) en el chat y haber obtenido la aprobación explícita del usuario.