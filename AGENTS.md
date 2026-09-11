# Constitución del Agente y Reglas de Desarrollo

Este documento rige el comportamiento de cualquier agente de inteligencia artificial en este repositorio. Sus directivas son inmutables y de cumplimiento estricto.

---

## 0. Protocolo de Inicio de Sesión (On-Wakeup Routine)
Cada vez que el agente despierte o inicie una interacción en este repositorio:
1. **Verificar Estado del Arnés:** Consulta `harness/config.json`. Si `"configured": false`, no inventes stacks ni asumas rutas; solicita al usuario inicializar el arnés con: *"Configura el arnés siguiendo harness/SETUP_HARNESS.md"*.
2. **Inspeccionar Foco Activo:** Comprueba si existe una carpeta en `harness/specs/active/`.
   * Si existe: Tu contexto de trabajo se limita estrictamente a `harness/specs/active/*/spec.md` y `harness/specs/tasks.md`. Lee ambos antes de proponer cambios o tocar código.
   * Si no existe: Pregunta al usuario si desea co-crear una nueva spec con `harness/specs/TEMPLATE.md` o activar una feature existente desde `harness/specs/backlog/`.
3. **Restricción de Lectura:** Queda terminantemente prohibido inspeccionar archivos en `harness/specs/backlog/` o `harness/specs/done/` durante el desarrollo diario para evitar saturación de tokens y *context drift*.

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
* **`harness/specs/tasks.md`:** Buffer de micro-tareas de la feature activa.

---

## 3. Protocolo TDD Obligatorio y Adaptativo
1. **Lectura Previa:** Lee `harness/specs/active/*/spec.md` y verifica el Módulo Afectado y su Estrategia de Tests.
2. **Desglose de Tareas:** Desglosa la spec en `harness/specs/tasks.md` en bloques manejables de **5 a 8 micro-tareas**.
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
* Realizar commits con la bandera `--no-verify`.
* Escribir código de producción sin una prueba unitaria previa que lo justifique (salvo módulos con estrategia declarada formalmente como `none`).
* Intentar activar más de una feature simultáneamente en `harness/specs/active/`.
* Dejar comentarios `TODO` o bloques de código comentado en el código fuente.