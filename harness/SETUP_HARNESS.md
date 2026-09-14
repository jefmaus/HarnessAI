# Protocolo de Configuración del Arnés (Setup Interactivo)

Este documento es el asistente que el agente de IA debe seguir cuando el desarrollador indique:
> *"Configura el arnés siguiendo harness/SETUP_HARNESS.md"*

Tu objetivo como agente arquitecto es recopilar las respuestas técnicas del usuario, configurar deterministamente `harness/config.json`, actualizar la constitución central `AGENTS.md` y activar las barreras físicas de Git.

---

## Paso 1: Inspección Silenciosa y Cuestionario Técnico

### A. Inspección Previa
Antes de hacer preguntas, inspecciona la raíz y subcarpetas para detectar si ya existen archivos de configuración (`package.json`, `pom.xml`, `go.mod`, `pyproject.toml`, `Cargo.toml`, etc.). Si encuentras pistas claras, úsalas para sugerir respuestas pre-llenadas.

### B. Cuestionario de 5 Preguntas al Usuario
Formula las siguientes preguntas de forma concisa y espera las respuestas antes de modificar ningún archivo:

1. **Topología del Repositorio:**
   ¿El proyecto contendrá un único servicio/aplicación o será un monorepo / multi-módulo (ej: 2 microservicios, backend + frontend Angular, etc.)?

2. **Módulos y Rutas:**
   Para cada componente o módulo:
   * Nombre del módulo y carpeta raíz (ej. `services/auth`, `services/billing`, `frontend`, o `.` si es raíz).
   * Lenguaje, runtime y framework principal (ej. Python 3.12 / FastAPI, Java 21 / Spring Boot 3.3, TypeScript / Angular 18).

3. **Estrategia y Ubicación de Pruebas:**
   Para cada módulo, define su estrategia:
   * **Dedicada:** Carpeta específica para tests (ej. `services/auth/tests/`, `src/test/java`).
   * **Colocalizada:** Pruebas adyacentes al código fuente (ej. `*.spec.ts` en Angular, `*_test.go` en Go).
   * **Ninguna / Omitida:** Declara si un módulo (ej. landing page estática o prototipo UI) no contará con suite automatizada por el momento.

4. **Comandos de Verificación por Módulo:**
   ¿Cuáles son los comandos exactos de terminal para:
   * Linter / Formateador (ej. `ruff check .`, `npm run lint`, `mvn spotless:check` o `none` si no aplica).
   * Compilación / Chequeo de tipos (ej. `tsc --noEmit`, `dotnet build` o `none`).
   * Pruebas unitarias con cobertura (ej. `pytest --cov`, `npm test -- --watch=false`, `go test ./...` o `none`).

   **Regla de vocabulario de estrategias:** usa el valor canónico en inglés en `config.json` — `dedicated`, `co-located`, `none` — (el runner también tolera los alias en español `dedicada`, `colocalizada`, `ninguna`). Si un módulo declara `dedicated` o `co-located`, su comando de `test` es **obligatorio**; no puede quedar en `null`.

5. **Persistencia y Almacenamiento:**
   ¿Qué base de datos o almacenamiento se utilizará y mediante qué librería o driver? (ej. PostgreSQL con Prisma, MongoDB con Motor, SQLite con SQLAlchemy, Redis, o memoria volátil).

---

## Paso 2: Ejecución Determinista de Cambios

Una vez que el usuario proporcione las respuestas:

### 1. Actualizar `harness/config.json`
Escribe el archivo con `configured: true` y el catálogo de módulos configurados. Ejemplo de esquema:
```json
{
  "configured": true,
  "repository_type": "monorepo",
  "project_name": "Nombre del Proyecto",
  "modules": [
    {
      "name": "auth-service",
      "path": "services/auth",
      "runtime": "Python 3.12 / FastAPI",
      "test_strategy": "dedicated",
      "test_path": "services/auth/tests",
      "commands": {
        "lint": "ruff check .",
        "build": null,
        "test": "pytest --cov=src"
      }
    },
    {
      "name": "frontend",
      "path": "frontend",
      "runtime": "Angular 18",
      "test_strategy": "co-located",
      "test_path": "*.spec.ts",
      "commands": {
        "lint": "npm run lint",
        "build": "npm run build",
        "test": "npm test -- --watch=false --browsers=ChromeHeadless"
      }
    }
  ]
}
```

### 2. Actualizar la Constitución Central (`AGENTS.md`)
Rellena la Sección 1 de `AGENTS.md` con la tabla de topología, lenguajes, estrategias de test y comandos de verificación acordados, manteniendo todas las reglas constitucionales intactas.

### 2.5 Prueba en Seco Obligatoria de Cada Comando (Dry-Run)

Antes de dar por buena la configuración, el agente **DEBE ejecutar cada comando registrado** (lint, build y test de cada módulo) **una vez** y comprobar que termina en `exit 0` y que realmente invoca el runner de pruebas del stack declarado. Un `test` que siempre pasa (por ejemplo, un comando mal escrito que no descubre ningún test) **invalida la estrategia `dedicated`/`co-located`**.

* Si un comando falla: reporta la salida cruda al usuario y corrígelo en conjunto (no registres comandos rotos).
* Si un módulo aún no tiene código ni tests: declara su estrategia en `none` de forma explícita o pospone el registro. Nunca inventes un comando de test.

### 3. Activar los Frenos Físicos de Git
Ejecuta en la terminal del sistema:
```bash
git config core.hooksPath harness/.githooks
```
*(Nota: En sistemas Unix/Linux/macOS, otorga permisos a los hooks si es necesario: `chmod +x harness/.githooks/*`).*

### 4. Prueba de Sanidad del Pipeline
Ejecuta (usa `py -3` en lugar de `python` si tu sistema solo expone el lanzador de Windows):
```bash
python harness/scripts/verify.py
python harness/scripts/secret-scan.py
python harness/scripts/rebase-spec.py
git config core.hooksPath
```
* `verify.py` debe reportar los módulos registrados en verde.
* `secret-scan.py` debe salir en `0` con el staging limpio (confirma que la barrera de credenciales está operativa).
* `rebase-spec.py` debe salir en `0` confirmando sincronización con la rama remota base.
* `git config core.hooksPath` debe devolver exactamente `harness/.githooks`; si está vacío, los hooks **no** están activos (recuerda que esta config no viaja con `git clone`).

Si todo concluye correctamente, confirma al usuario que el arnés está 100% operativo y listo para co-crear la primera especificación con `harness/specs/TEMPLATE.md`.
