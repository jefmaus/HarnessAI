#!/usr/bin/env python3
"""
Runner determinista universal de verificacion (Windows / Linux / macOS).
Ejecuta linter, compilacion/tipado y pruebas unitarias segun harness/config.json.
Soporta ejecucion global o enfocada en un modulo/microservicio especifico.

Reglas de integridad de configuracion (v1.1):
- config.json se lee con utf-8-sig (tolera BOM de editores Windows).
- 'path' de cada modulo debe ser relativa y resolverse DENTRO de la raiz del repo.
- 'test_strategy' acepta el vocabulario canonico en ingles (none|dedicated|co-located)
  y alias en espanol (ninguna|dedicada|colocalizada); valor desconocido es error.
- Si la estrategia ejecuta pruebas (dedicated|co-located), 'commands.test' es OBLIGATORIO.
- Cada comando tiene un timeout para que el hook pre-commit no pueda colgarse.
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
DEFAULT_TIMEOUT = 900

STRATEGY_ALIASES = {
    "none": "none",
    "ninguna": "none",
    "omitida": "none",
    "dedicated": "dedicated",
    "dedicada": "dedicated",
    "co-located": "co-located",
    "colocated": "co-located",
    "colocalizada": "co-located",
}

TESTING_STRATEGIES = ("dedicated", "co-located")


def die(msg, code=1):
    print(msg)
    sys.exit(code)


def within_root(candidate, root):
    try:
        Path(candidate).relative_to(root)
        return True
    except ValueError:
        return False


def load_config():
    if not CONFIG_FILE.exists():
        die("❌ Error critico: 'harness/config.json' no existe.")
    try:
        raw = CONFIG_FILE.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError as e:
        die(f"❌ Error critico: 'harness/config.json' no esta codificado en UTF-8: {e}")
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        die(f"❌ Error al leer 'harness/config.json': {e}")


def resolve_module_dir(mod_name, rel_path):
    """Valida que la ruta del modulo sea relativa, exista y este dentro de la raiz."""
    if rel_path is None or str(rel_path).strip() == "":
        rel_path = "."
    rel_path = str(rel_path)
    p = Path(rel_path)
    if p.is_absolute():
        die(
            f"❌ [CONFIG ERROR] El modulo '{mod_name}' tiene 'path' absoluta ({rel_path}).\n"
            "   Debe ser relativa a la raiz del repositorio (ej. 'services/auth' o '.')."
        )
    root = ROOT_DIR.resolve()
    working_dir = (root / p).resolve()
    if working_dir != root and not within_root(working_dir, root):
        die(
            f"❌ [CONFIG ERROR] El modulo '{mod_name}' apunta fuera del repositorio: {working_dir}\n"
            "   Se prohiben rutas con '..' que escapen de la raiz."
        )
    if not working_dir.is_dir():
        die(f"❌ [CONFIG ERROR] La ruta del modulo '{mod_name}' no existe: {working_dir}")
    return working_dir


def normalize_strategy(mod_name, raw_strategy):
    strategy_raw = str(raw_strategy or "dedicated").strip().lower()
    strategy = STRATEGY_ALIASES.get(strategy_raw)
    if strategy is None:
        die(
            f"❌ [CONFIG ERROR] Estrategia de tests desconocida en modulo '{mod_name}': '{raw_strategy}'.\n"
            "   Valores validos: none|ninguna | dedicated|dedicada | co-located|colocalizada."
        )
    return strategy


def validate_commands(mod_name, commands, strategy):
    if not isinstance(commands, dict):
        die(f"❌ [CONFIG ERROR] El campo 'commands' del modulo '{mod_name}' debe ser un objeto.")
    lint = commands.get("lint")
    build = commands.get("build")
    test = commands.get("test")
    for label, value in (("lint", lint), ("build", build), ("test", test)):
        if value is not None and not isinstance(value, str):
            die(f"❌ [CONFIG ERROR] 'commands.{label}' del modulo '{mod_name}' debe ser string o null.")
    if strategy in TESTING_STRATEGIES and not (test and test.strip()):
        die(
            f"❌ [CONFIG ERROR] El modulo '{mod_name}' declara estrategia '{strategy}' (ejecuta pruebas)\n"
            "   pero 'commands.test' esta vacio. Registra el comando real de pruebas o\n"
            "   cambia la estrategia a 'none' solo si el modulo no tiene logica ejecutable."
        )
    return lint, build, test


def run_step(name, command, working_dir, timeout):
    """Ejecuta un comando en un subproceso y valida su codigo de salida."""
    print(f"  -> [{name}] Ejecutando: {command}")
    try:
        res = subprocess.run(command, shell=True, cwd=str(working_dir), timeout=timeout)
    except subprocess.TimeoutExpired:
        print(f"\n❌ [VERIFY ERROR] El paso '{name}' supero el timeout de {timeout}s. Revisa suites en modo watch.")
        return False
    except OSError as e:
        print(f"\n❌ [VERIFY ERROR] No se pudo ejecutar el paso '{name}': {e}")
        return False
    if res.returncode != 0:
        print(f"\n❌ [VERIFY ERROR] Fallo el paso '{name}' con codigo {res.returncode}.")
        return False
    return True


def verify_module(mod, timeout):
    """Ejecuta los pasos de verificacion de un modulo ya validado."""
    mod_name = mod["name"]
    working_dir = mod["working_dir"]
    lint_cmd, build_cmd, test_cmd = mod["lint"], mod["build"], mod["test"]
    strategy = mod["strategy"]

    print(f"\n🔍 === [VERIFY MODULO: {mod_name}] ({working_dir}) ===")

    if lint_cmd:
        if not run_step("Linter / Formato", lint_cmd, working_dir, timeout):
            return False

    if build_cmd:
        if not run_step("Compilacion / Tipado", build_cmd, working_dir, timeout):
            return False

    if strategy == "none":
        print("  ℹ️ [Tests] Estrategia declarada como 'none'. Se omiten pruebas automaticas para este modulo.")
    elif test_cmd:
        if not run_step("Pruebas Unitarias", test_cmd, working_dir, timeout):
            return False

    if not any((lint_cmd, build_cmd, test_cmd)):
        print(f"  ⚠️ [Alerta] El modulo '{mod_name}' no tiene ningun comando de verificacion configurado.")

    return True


def prepare_modules(config, target_name):
    modules = config.get("modules", [])
    if not isinstance(modules, list) or not modules:
        die("⚠️ No hay modulos registrados en 'harness/config.json'.")

    prepared = []
    for i, mod in enumerate(modules):
        if not isinstance(mod, dict):
            die(f"❌ [CONFIG ERROR] El modulo #{i + 1} en config.json no es un objeto valido.")
        mod_name = mod.get("name")
        if not isinstance(mod_name, str) or not mod_name.strip():
            die(f"❌ [CONFIG ERROR] El modulo #{i + 1} carece de un 'name' no vacio.")
        mod_name = mod_name.strip()
        strategy = normalize_strategy(mod_name, mod.get("test_strategy"))
        working_dir = resolve_module_dir(mod_name, mod.get("path"))
        lint, build, test = validate_commands(mod_name, mod.get("commands", {}), strategy)
        prepared.append({
            "name": mod_name,
            "strategy": strategy,
            "working_dir": working_dir,
            "lint": lint,
            "build": build,
            "test": test,
        })

    if target_name:
        filtered = [m for m in prepared if m["name"].lower() == target_name.lower()]
        if not filtered:
            valid_names = ", ".join(m["name"] for m in prepared)
            print(f"❌ Error: Modulo '{target_name}' no encontrado.")
            print(f"Modulos validos: {valid_names}")
            sys.exit(1)
        return filtered
    return prepared


def main():
    parser = argparse.ArgumentParser(description="Runner de Calidad y Verificacion del Arnes.")
    parser.add_argument("module", nargs="?", help="Nombre del modulo especifico a verificar (opcional)")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT,
                        help=f"Segundos maximos por comando (por defecto {DEFAULT_TIMEOUT})")
    args = parser.parse_args()

    config = load_config()

    if not config.get("configured", False):
        # Si el arnés no está configurado, permitir commits si SOLO se modifican archivos del propio arnés/docs
        try:
            diff_res = subprocess.run(["git", "diff", "--cached", "--name-only"], capture_output=True, text=True, cwd=str(ROOT_DIR))
            staged_files = [f.strip() for f in diff_res.stdout.splitlines() if f.strip()]
            harness_files = all(
                f.startswith("harness/") or f in ("AGENTS.md", "README.md", ".gitignore", ".gitattributes")
                for f in staged_files
            )
            if staged_files and harness_files:
                print("ℹ️  [VERIFY] Arnés no configurado, pero solo se detectaron cambios en archivos del arnés/docs.")
                print("    Permitiendo commit de infraestructura del arnés.")
                sys.exit(0)
        except Exception:
            pass

        print("=" * 65)
        print("⚠️  [VERIFY] EL ARNES AUN NO HA SIDO CONFIGURADO")
        print("=" * 65)
        print("Para configurar el stack tecnologico y los comandos de verificacion,")
        print("pidele al agente:")
        print("👉 'Configura el arnes siguiendo harness/SETUP_HARNESS.md'")
        print("=" * 65)
        sys.exit(1)

    modules_to_verify = prepare_modules(config, args.module)

    for mod in modules_to_verify:
        success = verify_module(mod, args.timeout)
        if not success:
            print(f"\n🚫 Pipeline interrumpido. Corrige los errores en '{mod['name']}' antes de continuar.")
            sys.exit(1)

    print("\n" + "=" * 65)
    print("✅ === [VERIFY] Todos los chequeos pasaron exitosamente. Pipeline en VERDE. ===")
    print("=" * 65)
    sys.exit(0)


if __name__ == "__main__":
    main()
