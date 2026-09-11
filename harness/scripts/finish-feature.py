#!/usr/bin/env python3
"""
Comando determinista de cierre y archivado de features.
Ejecuta la suite de verificación, valida que todas las tareas en tasks.md estén completadas [x],
garantiza la unicidad de la feature activa y traslada la carpeta a specs/done/.
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

def check_tasks_completed():
    """Valida que no existan tareas pendientes [ ] ni en progreso [-] en tasks.md."""
    if not TASKS_FILE.exists():
        print(f"❌ Error: El archivo '{TASKS_FILE}' no existe.")
        return False

    content = TASKS_FILE.read_text(encoding="utf-8")
    lines = content.splitlines()

    pending = []
    in_progress = []
    completed = []

    for line in lines:
        stripped = line.strip()
        if re.search(r"^\s*[-*]\s*\[ \]", stripped):
            pending.append(stripped)
        elif re.search(r"^\s*[-*]\s*\[-\]", stripped):
            in_progress.append(stripped)
        elif re.search(r"^\s*[-*]\s*\[x\]", stripped, re.IGNORECASE):
            completed.append(stripped)

    if in_progress:
        print("❌ Error: Hay tareas aún marcadas en progreso [-]:")
        for t in in_progress:
            print(f"   {t}")
        return False

    if pending:
        print("❌ Error: Hay tareas pendientes de completar [ ]:")
        for t in pending:
            print(f"   {t}")
        return False

    if not completed:
        print("⚠️ Advertencia: No se encontraron tareas completadas [x] en tasks.md.")

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
        print(f"❌ Error de integridad: Se detectaron múltiples features activas: {names}.")
        print("La regla constitucional 'Single-Task Focus' prohíbe más de una feature en active/ simultáneamente.")
        sys.exit(1)

    feature_dir = features[0]
    spec_file = feature_dir / "spec.md"
    if not spec_file.exists():
        print(f"❌ Error: La feature activa '{feature_dir.name}' no contiene un archivo 'spec.md'.")
        sys.exit(1)

    # 2. Validar que las tareas en tasks.md estén todas en [x]
    print("\n📋 Validando estado de micro-tareas en 'harness/specs/tasks.md'...")
    if not check_tasks_completed():
        print("\n🚫 Cierre cancelado: Completa todas las micro-tareas antes de archivar.")
        sys.exit(1)
    print("✅ Todas las micro-tareas están completadas [x].")

    # 3. Verificación de calidad obligatoria
    print(f"\n🧪 Ejecutando suite de verificación previa ({VERIFY_SCRIPT.name})...")
    res = subprocess.run([sys.executable, str(VERIFY_SCRIPT)])
    if res.returncode != 0:
        print("\n❌ Error: La suite de verificación falló. Corrige el código/tests antes de cerrar la feature.")
        sys.exit(1)

    # 4. Validar colisión en specs/done/
    target_dir = DONE_DIR / feature_dir.name
    if target_dir.exists():
        print(f"❌ Error: Ya existe una carpeta archivada con el nombre '{target_dir.name}' en 'harness/specs/done/'.")
        print("Por favor, renombra la carpeta de destino o resuélvelo manualmente para evitar sobreescrituras accidentales.")
        sys.exit(1)

    # 5. Mover carpeta de active a done
    DONE_DIR.mkdir(parents=True, exist_ok=True)
    shutil.move(str(feature_dir), str(target_dir))
    print(f"\n📁 Feature '{feature_dir.name}' archivada exitosamente en:")
    print(f"   {target_dir}/")

    # 6. Limpiar buffer de tareas
    clean_tasks_content = "# Tareas Activas\n\n> Esperando asignación de feature activa.\n"
    TASKS_FILE.write_text(clean_tasks_content, encoding="utf-8")
    print("🧹 'harness/specs/tasks.md' restaurado a reposo para el siguiente ciclo.")

    print("\n" + "=" * 65)
    print(f"🎉 Feature '{feature_dir.name}' finalizada y archivada con éxito.")
    print("=" * 65)
    sys.exit(0)

if __name__ == "__main__":
    main()
