#!/usr/bin/env python3
"""
Runner determinista universal de verificación (Windows / Linux / macOS).
Ejecuta linter, compilación/tipado y pruebas unitarias según la configuración en harness/config.json.
Soporta ejecución global o enfocada en un módulo/microservicio específico.
"""
import argparse
import json
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
ROOT_DIR = HARNESS_DIR.parent
CONFIG_FILE = HARNESS_DIR / "config.json"

def run_step(name, command, working_dir):
    """Ejecuta un comando en un subproceso y valida su código de salida."""
    print(f"  -> [{name}] Ejecutando: {command}")
    res = subprocess.run(command, shell=True, cwd=str(working_dir))
    if res.returncode != 0:
        print(f"\n❌ [VERIFY ERROR] Falló el paso '{name}' con código {res.returncode}.")
        return False
    return True

def verify_module(mod):
    """Ejecuta los pasos de verificación de un módulo."""
    mod_name = mod.get("name", "unnamed")
    mod_path_rel = mod.get("path", "")
    working_dir = (ROOT_DIR / mod_path_rel).resolve() if mod_path_rel else ROOT_DIR

    print(f"\n🔍 === [VERIFY MÓDULO: {mod_name}] ({working_dir}) ===")

    commands = mod.get("commands", {})
    lint_cmd = commands.get("lint")
    build_cmd = commands.get("build")
    test_cmd = commands.get("test")

    executed_any = False

    if lint_cmd:
        executed_any = True
        if not run_step("Linter / Formato", lint_cmd, working_dir):
            return False

    if build_cmd:
        executed_any = True
        if not run_step("Compilación / Tipado", build_cmd, working_dir):
            return False

    strategy = mod.get("test_strategy", "dedicated")
    if strategy == "none":
        print("  ℹ️ [Tests] Estrategia declarada como 'none'. Se omiten pruebas automáticas para este módulo.")
    elif test_cmd:
        executed_any = True
        if not run_step("Pruebas Unitarias", test_cmd, working_dir):
            return False
    else:
        print("  ⚠️ [Aviso] No hay comando de test configurado para este módulo.")

    if not executed_any and strategy != "none":
        print(f"  ⚠️ [Alerta] El módulo '{mod_name}' no tiene comandos de linter, compilación ni tests.")

    return True

def main():
    parser = argparse.ArgumentParser(description="Runner de Calidad y Verificación del Arnés.")
    parser.add_argument("module", nargs="?", help="Nombre del módulo específico a verificar (opcional)")
    args = parser.parse_args()

    if not CONFIG_FILE.exists():
        print("❌ Error crítico: 'harness/config.json' no existe.")
        sys.exit(1)

    try:
        config = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"❌ Error al leer 'harness/config.json': {e}")
        sys.exit(1)

    if not config.get("configured", False):
        print("=" * 65)
        print("⚠️  [VERIFY] EL ARNÉS AÚN NO HA SIDO CONFIGURADO")
        print("=" * 65)
        print("Para configurar el stack tecnológico y los comandos de verificación,")
        print("pídele al agente:")
        print("👉 'Configura el arnés siguiendo harness/SETUP_HARNESS.md'")
        print("=" * 65)
        sys.exit(1)

    modules = config.get("modules", [])
    if not modules:
        print("⚠️ No hay módulos registrados en 'harness/config.json'.")
        sys.exit(1)

    target_module = args.module
    if target_module:
        filtered = [m for m in modules if m.get("name", "").lower() == target_module.lower()]
        if not filtered:
            valid_names = ", ".join(m.get("name", "") for m in modules)
            print(f"❌ Error: Módulo '{target_module}' no encontrado.")
            print(f"Módulos válidos: {valid_names}")
            sys.exit(1)
        modules_to_verify = filtered
    else:
        modules_to_verify = modules

    for mod in modules_to_verify:
        success = verify_module(mod)
        if not success:
            print(f"\n🚫 Pipeline interrumpido. Corrige los errores en '{mod.get('name')}' antes de continuar.")
            sys.exit(1)

    print("\n" + "=" * 65)
    print("✅ === [VERIFY] Todos los chequeos pasaron exitosamente. Pipeline en VERDE. ===")
    print("=" * 65)
    sys.exit(0)

if __name__ == "__main__":
    main()
