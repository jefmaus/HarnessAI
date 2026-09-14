#!/usr/bin/env python3
"""
Comando determinista de cierre y archivado de features.
Ejecuta la suite de verificacion, valida que todas las tareas en tasks.md esten completadas [x],
garantiza la unicidad de la feature activa y traslada la carpeta a specs/done/.

Reglas de integridad (v1.1):
- tasks.md debe llevar cabecera '> Feature: <ID>-<slug>' y coincidir con la carpeta activa.
- Feature activa + tasks.md en reposo = estado inconsistente => error (antes solo avisaba).
- Casillas reconocidas en viñetas '-', '*' y listas numeradas '1.' / '2)'.
- No se exige un minimo artificial de tareas: una sola '[x]' legitima cierra.
"""
import re
import shutil
import subprocess
import sys
from pathlib import Path

# Asegurar compatibilidad UTF-8 en consolas Windows (cp1252 / cp850)
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HARNESS_DIR = Path(__file__).resolve().parent.parent
ACTIVE_DIR = HARNESS_DIR / "specs" / "active"
DONE_DIR = HARNESS_DIR / "specs" / "done"
TASKS_FILE = HARNESS_DIR / "specs" / "tasks.md"
VERIFY_SCRIPT = HARNESS_DIR / "scripts" / "verify.py"

REST_MARKER = "Esperando asignacion"
REST_MARKER_ACCENTS = "Esperando asignación"
FEATURE_HEADER_RE = re.compile(r"^>\s*Feature:\s*(.+?)\s*$", re.MULTILINE)
CHECKBOX_RE = re.compile(r"^\s*(?:[-*]|\d+[.)])\s*\[([ xX-])\]")

REPO_TASKS_TEMPLATE = "# Tareas Activas\n\n> Esperando asignación de feature activa.\n"


def check_tasks(feature_name):
    """Valida el vinculo y el estado de tasks.md contra la feature activa."""
    if not TASKS_FILE.exists():
        print(f"❌ Error: El archivo '{TASKS_FILE}' no existe.")
        return False

    content = TASKS_FILE.read_text(encoding="utf-8-sig")
    lines = content.splitlines()

    if REST_MARKER in content or REST_MARKER_ACCENTS in content:
        print("❌ Error: Hay una feature activa pero 'tasks.md' esta en estado de reposo.")
        print("   Desglosa primero las micro-tareas atomicas de la spec antes de cerrar.")
        return False

    header_match = FEATURE_HEADER_RE.search(content)
    if not header_match:
        print("❌ Error: 'tasks.md' no contiene la cabecera de vinculo con la feature.")
        print("   Agrega una linea como:  > Feature: <ID>-<slug>")
        return False

    declared = header_match.group(1).strip()
    if declared != feature_name:
        print(f"❌ Error de vinculo: 'tasks.md' declara la feature '{declared}'")
        print(f"   pero la feature activa en 'specs/active/' es '{feature_name}'.")
        return False

    pending = []
    in_progress = []
    completed = []
    for line in lines:
        match = CHECKBOX_RE.match(line)
        if not match:
            continue
        state = match.group(1)
        if state == " ":
            pending.append(line.strip())
        elif state == "-":
            in_progress.append(line.strip())
        else:
            completed.append(line.strip())

    if not (pending or in_progress or completed):
        print("❌ Error: 'tasks.md' vinculado a la feature activa no contiene ninguna micro-tarea.")
        print("   Desglosa las tareas atomicas (formato '- [ ]' o numerado) antes de cerrar.")
        return False

    if in_progress:
        print("❌ Error: Hay tareas aun marcadas en progreso [-]:")
        for t in in_progress:
            print(f"   {t}")
        return False

    if pending:
        print("❌ Error: Hay tareas pendientes de completar [ ]:")
        for t in pending:
            print(f"   {t}")
        return False

    return True


def main():
    print("=" * 65)
    print("📦 [Finish-Feature] Iniciando proceso determinista de cierre...")
    print("=" * 65)

    # 1. Validar features activas en specs/active/
    if not ACTIVE_DIR.exists():
        print(f"❌ Error: El directorio '{ACTIVE_DIR}' no existe.")
        sys.exit(1)

    features = [d for d in ACTIVE_DIR.iterdir() if d.is_dir() and not d.name.startswith(".")]

    if not features:
        print("⚠️ No hay ninguna feature activa en 'harness/specs/active/'. Nada que archivar.")
        sys.exit(0)

    if len(features) > 1:
        names = ", ".join(f"'{d.name}'" for d in features)
        print(f"❌ Error de integridad: Se detectaron multiples features activas: {names}.")
        print("La regla constitucional 'Single-Task Focus' prohibe mas de una feature en active/ simultaneamente.")
        sys.exit(1)

    feature_dir = features[0]
    spec_file = feature_dir / "spec.md"
    if not spec_file.exists():
        print(f"❌ Error: La feature activa '{feature_dir.name}' no contiene un archivo 'spec.md'.")
        sys.exit(1)

    # 2. Validar vinculo y estado de tareas
    print("\n📋 Validando estado de micro-tareas en 'harness/specs/tasks.md'...")
    if not check_tasks(feature_dir.name):
        print("\n🚫 Cierre cancelado: Resuelve el estado de 'tasks.md' antes de archivar.")
        sys.exit(1)
    print("✅ Todas las micro-tareas estan completadas [x] y vinculadas a la feature activa.")

    # 3. Verificacion de calidad obligatoria
    print(f"\n🧪 Ejecutando suite de verificacion previa ({VERIFY_SCRIPT.name})...")
    res = subprocess.run([sys.executable, str(VERIFY_SCRIPT)])
    if res.returncode != 0:
        print("\n❌ Error: La suite de verificacion fallo. Corrige el codigo/tests antes de cerrar la feature.")
        sys.exit(1)

    # 4. Validar colision en specs/done/
    target_dir = DONE_DIR / feature_dir.name
    if target_dir.exists():
        print(f"❌ Error: Ya existe una carpeta archivada con el nombre '{target_dir.name}' en 'harness/specs/done/'.")
        print("Renombra la carpeta archivada anterior o resuelvelo manualmente para evitar sobreescrituras.")
        sys.exit(1)

    # 5. Mover carpeta de active a done
    DONE_DIR.mkdir(parents=True, exist_ok=True)
    shutil.move(str(feature_dir), str(target_dir))
    print(f"\n📁 Feature '{feature_dir.name}' archivada exitosamente en:")
    print(f"   {target_dir}/")

    # 6. Limpiar buffer de tareas
    TASKS_FILE.write_text(REPO_TASKS_TEMPLATE, encoding="utf-8")
    print("🧹 'harness/specs/tasks.md' restaurado a reposo para el siguiente ciclo.")

    print("\n" + "=" * 65)
    print(f"🎉 Feature '{feature_dir.name}' finalizada y archivada con exito.")
    print("=" * 65)
    print("👉 Recuerda commitear el archivado: git add -A && git commit -m \"chore(specs): archivar {name}\"".replace("{name}", feature_dir.name))
    sys.exit(0)


if __name__ == "__main__":
    main()
