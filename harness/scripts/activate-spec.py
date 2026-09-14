#!/usr/bin/env python3
"""
Activador determinista de specs (barrera anti-alucinacion de la maquina de estados).

Traslada 'harness/specs/backlog/<NNN-slug>/' a 'harness/specs/active/<NNN-slug>/'
garantizando fisicamente la regla 'Single-Task Focus' (exactamente una feature activa)
y escribiendo la cabecera de vinculo '> Feature:' en 'harness/specs/tasks.md'.

USO:
    python harness/scripts/activate-spec.py <NNN-slug>
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
SPECS_DIR = HARNESS_DIR / "specs"
BACKLOG_DIR = SPECS_DIR / "backlog"
ACTIVE_DIR = SPECS_DIR / "active"
TASKS_FILE = SPECS_DIR / "tasks.md"

NAME_RE = re.compile(r"^\d{3}-[a-z0-9]+(?:-[a-z0-9]+)*$")
FEATURE_HEADER_RE = re.compile(r"^>\s*Feature:\s*(.+?)\s*$", re.MULTILINE)


def fail(msg):
    print(f"❌ [ACTIVATE-SPEC] {msg}")
    sys.exit(1)


def main():
    if len(sys.argv) != 2:
        available = []
        if BACKLOG_DIR.is_dir():
            available = [d.name for d in BACKLOG_DIR.iterdir() if d.is_dir() and not d.name.startswith(".")]
        print("Uso: python harness/scripts/activate-spec.py <NNN-slug>")
        print("Specs disponibles en backlog: " + (", ".join(available) if available else "(ninguna)"))
        sys.exit(1)

    name = sys.argv[1].strip()
    if not NAME_RE.match(name):
        fail(f"'{name}' no cumple el patron <NNN-slug> (ej. '001-login-jwt').")

    source = BACKLOG_DIR / name
    if not source.is_dir():
        fail(f"No existe 'harness/specs/backlog/{name}/'. Activa solo specs que esten en el backlog.")
    if not (source / "spec.md").is_file():
        fail(f"'{name}' no contiene 'spec.md'. Completa la spec antes de activarla.")

    if not ACTIVE_DIR.is_dir():
        ACTIVE_DIR.mkdir(parents=True)
    current = [d for d in ACTIVE_DIR.iterdir() if d.is_dir() and not d.name.startswith(".")]
    if current:
        fail(
            f"Ya existe una feature activa: '{current[0].name}'.\n"
            "   La regla 'Single-Task Focus' exige cerrarla primero con:\n"
            "   python harness/scripts/finish-feature.py\n"
            "   (o devolverla a backlog manualmente si fue un error)."
        )
    if (SPECS_DIR / "done" / name).exists():
        fail(f"'{name}' ya fue archivada en done/. No se reactiva historico inmutable; crea una spec nueva.")

    if TASKS_FILE.exists():
        content = TASKS_FILE.read_text(encoding="utf-8-sig")
        match = FEATURE_HEADER_RE.search(content)
        if match and match.group(1).strip() != name:
            fail(
                f"'tasks.md' tiene tareas de otra feature ({match.group(1).strip()}).\n"
                "   Cierra esa feature con finish-feature.py o restaura tasks.md a reposo primero."
            )

    shutil.move(str(source), str(ACTIVE_DIR / name))
    TASKS_FILE.write_text(
        "# Tareas Activas\n\n"
        f"> Feature: {name}\n\n"
        "> Desglosa aqui las micro-tareas atomicas de la spec\n"
        "> (usa '- [ ]' o '1. [ ]'; marca '[-]' en progreso y '[x]' al completar).\n",
        encoding="utf-8",
    )

    print(f"✅ [ACTIVATE-SPEC] Feature '{name}' activada: harness/specs/active/{name}/")
    print("   'tasks.md' vinculado a la feature. Siguiente paso (TDD):")
    print("   1. Desglosa micro-tareas en harness/specs/tasks.md")
    print("   2. Toma la primera y marcala [-]")
    print("   3. python harness/scripts/verify.py <modulo>  (Fase Roja)")
    sys.exit(0)


if __name__ == "__main__":
    main()
