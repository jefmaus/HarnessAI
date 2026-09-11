# Proyecto con Arnés de Desarrollo Determinista (SDD + TDD)

Este repositorio está preparado para construir software de alta fidelidad asistido por agentes de inteligencia artificial (LLMs), implementando **Spec Driven Development (SDD)** y **TDD estricto**, garantizando que el agente nunca sufra de deriva de contexto (*context drift*) ni genere regresiones silenciosas.

Todo el mecanismo de control, especificaciones, memoria técnica y scripts de automatización se encuentra **completamente aislado en la carpeta `harness/`**, dejando la raíz del proyecto limpia para el código fuente de tu aplicación (monolito, microservicios o monorepo con frontend).

---

## 🚀 Inicio Rápido en 3 Pasos

### 1. Inicializar el Proyecto
Abre tu asistente de IA (Google Antigravity, Claude Code, Cursor, Windsurf, etc.) e indícale:
```text
Configura el arnés siguiendo harness/SETUP_HARNESS.md
```
El agente te formulará 5 preguntas rápidas para identificar la topología (si tienes 1 o varios microservicios/frontends), los comandos de verificación y activará los hooks de Git automáticamente.

### 2. Co-crear una Especificación
Cuando quieras planificar una funcionalidad, dile al agente:
```text
Vamos a co-crear una nueva feature siguiendo harness/specs/TEMPLATE.md
```
El agente calculará el siguiente ID autónomamente (`001`, `002`...), acordará contigo los contratos y generará la especificación en `harness/specs/backlog/`.

### 3. Desarrollar con Foco Único
1. Mueve la carpeta de `harness/specs/backlog/XXX-nombre/` a `harness/specs/active/XXX-nombre/`.
2. El agente volcará las micro-tareas en `harness/specs/tasks.md` y ejecutará el ciclo **Rojo-Verde-Refactor**.
3. Al terminar todas las tareas, ejecuta:
   ```bash
   python harness/scripts/finish-feature.py
   ```
   La feature se archivará automáticamente en `harness/specs/done/` y el buffer quedará listo para la siguiente entrega.

---

## 📚 Documentación Completa del Arnés
Para consultar la arquitectura detallada, los diagramas de flujo y las políticas de memoria técnica, consulta el manual en:
👉 **[harness/README.md](harness/README.md)**
