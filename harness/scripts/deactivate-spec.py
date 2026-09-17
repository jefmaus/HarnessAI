#!/usr/bin/env python3
"""
Desactiva una spec de specs/active/ devolviendola a specs/backlog/.

Reglas de integridad:
- Solo se puede desactivar la feature unica que esta en specs/active/.
- Si tasks.md esta en reposo y no hay feature activa: nada que hacer.
- Si hay una feature activa, se traslada de vuelta a backlog/ y se restaura
  tasks.md a su estado de reposo.

USO:
    python harness/scripts/deactivate-spec.py
"""
import re
import shutil
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HARNESS_DIR = Path(__file__).resolve().parent.parent
ACTIVE_DIR = HARNESS_DIR / "specs" / "active"
BACKLOG_DIR = HARNESS_DIR / "specs" / "backlog"
DONE_DIR = HARNESS_DIR / "specs" / "done"
TASKS_FILE = HARNESS_DIR / "specs" / "tasks.md"

REST_MARKER = "Esperando asignación de feature activa"
REPO_TASKS_TEMPLATE = "# Tareas Activas\n\n> Esperando asignación de feature activa.\n"


def main():
    print("=" * 65)
    print("⏪ [Deactivate-Spec] Devolviendo feature de active/ a backlog/...")
    print("=" * 65)

    if not ACTIVE_DIR.exists():
        print(f"❌ Error: El directorio '{ACTIVE_DIR}' no existe.")
        sys.exit(1)

    features = [d for d in ACTIVE_DIR.iterdir() if d.is_dir() and not d.name.startswith(".")]

    if not features:
        print("⚠️ No hay ninguna feature activa en 'harness/specs/active/'. Nada que desactivar.")
        sys.exit(0)

    if len(features) > 1:
        names = ", ".join(f"'{d.name}'" for d in features)
        print(f"❌ Error de integridad: Multiples features activas detectadas: {names}.")
        print("La regla 'Single-Task Focus' prohibe mas de una feature activa simultaneamente.")
        sys.exit(1)

    feature_dir = features[0]
    spec_file = feature_dir / "spec.md"
    if not spec_file.exists():
        print(f"❌ Error: La feature activa '{feature_dir.name}' no contiene 'spec.md'.")
        sys.exit(1)

    # Validar que no exista ya en backlog (colision)
    target_in_backlog = BACKLOG_DIR / feature_dir.name
    if target_in_backlog.exists():
        print(f"❌ Error: Ya existe una spec con nombre '{feature_dir.name}' en 'harness/specs/backlog/'.")
        print("Resuelve la colision antes de desactivar.")
        sys.exit(1)

    BACKLOG_DIR.mkdir(parents=True, exist_ok=True)
    shutil.move(str(feature_dir), str(target_in_backlog))
    print(f"\n📁 Feature '{feature_dir.name}' devuelta a:")
    print(f"   {target_in_backlog}/")

    # Restaurar buffer de tareas a reposo
    if TASKS_FILE.exists():
        TASKS_FILE.write_text(REPO_TASKS_TEMPLATE, encoding="utf-8")
        print("🧹 'harness/specs/tasks.md' restaurado a reposo.")

    print("\n" + "=" * 65)
    print(f"✅ Feature '{feature_dir.name}' desactivada exitosamente.")
    print("=" * 65)
    print("✅ Cierre del buffer de tareas. El backlog esta listo para nueva priorizacion.")
    sys.exit(0)


if __name__ == "__main__":
    main()
