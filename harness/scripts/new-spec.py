#!/usr/bin/env python3
"""
Creador determinista de carpetas de spec (barrera anti-alucinacion del Paso 6 de TEMPLATE.md).

Calcula el siguiente ID escaneando los prefijos numericos de backlog/, active/ y done/,
rechaza IDs duplicados y nombres mal formados, y materializa el esqueleto de spec.md
con la cabecera de metadatos y el campo de evidencia de aprobacion.

USO:
    python harness/scripts/new-spec.py <slug> [--title "Nombre descriptivo"]

RECORDATORIO CONSTITUCIONAL: este script solo debe ejecutarse DESPUES de que el usuario
haya aprobado en el chat los contratos/invariantes y los CA-* (CHECKPOINT de TEMPLATE.md).
"""
import argparse
import re
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
SCAN_DIRS = [SPECS_DIR / "backlog", SPECS_DIR / "active", SPECS_DIR / "done"]

ID_PREFIX_RE = re.compile(r"^(\d{3})-(.+)$")
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

SKELETON = """#{heading}

## 0. Metadatos de la Spec
* **Tipo de Tarea:** `[feature | bugfix | refactor | performance | batch_job | event_worker | db_migration]`
* **Modulo Afectado:** `[nombre_modulo]`
* **Estrategia de Tests:** `[dedicated | co-located | none]`
* **Ruta Base de Codigo:** `[ruta relativa]`
* **Ubicacion de Tests:** `[ruta o patron, segun estrategia]`
* **Aprobada:** `[fecha] por [usuario]` (completar con la fecha del checkpoint aprobado en el chat)

## 1. Requisitos y Contexto
* [Regla o comportamiento esperado 1]
* [Regla 2: restricciones, limites, formatos]
* [Regla 3: comportamiento ante fallos o condiciones anomalias]

## 2. Contratos Tecnicos e Invariantes
[Redactar la variante aplicable segun harness/specs/TEMPLATE.md (A-I):
APIs, CLIs, librerias, UI, batch/crons, colas/eventos, bugfix, refactor o migracion.]

## 3. Criterios de Aceptacion (Inmutables)
* **CA-1:** [Condicion inicial] -> [Accion] -> [Resultado verificable] (indicar el comando que lo certifica)
* **CA-2:** [Entradas invalidas se rechazan de forma determinista] (indicar el comando que lo certifica)

## 4. Seguridad y Resiliencia (solo si aplica)
* Secretos: [no aplica / descripcion]
* Validacion de entradas: [no aplica / descripcion]
* Limites o rollback: [no aplica / descripcion]
"""


def fail(msg):
    print(f"❌ [NEW-SPEC] {msg}")
    sys.exit(1)


def scan_existing():
    """Devuelve (max_num, seen_ids, malformed) tras inspeccionar las tres carpetas."""
    max_num = 0
    seen = {}
    malformed = []
    for folder in SCAN_DIRS:
        if not folder.is_dir():
            continue
        for entry in folder.iterdir():
            if not entry.is_dir() or entry.name.startswith("."):
                continue
            match = ID_PREFIX_RE.match(entry.name)
            if not match:
                malformed.append(f"{folder.name}/{entry.name}")
                continue
            num = int(match.group(1))
            max_num = max(max_num, num)
            seen.setdefault(num, []).append(f"{folder.name}/{entry.name}")
    return max_num, seen, malformed


def main():
    parser = argparse.ArgumentParser(description="Crea la carpeta de spec con el siguiente ID determinista.")
    parser.add_argument("slug", help="Nombre corto en kebab-case (ej. login-jwt)")
    parser.add_argument("--title", default="", help="Nombre descriptivo para el encabezado de la spec")
    args = parser.parse_args()

    slug = args.slug.strip().lower()
    if not SLUG_RE.match(slug):
        fail(f"El slug '{args.slug}' no es valido. Usa kebab-case: minusculas, digitos y guiones (ej. 'login-jwt').")

    max_num, seen, malformed = scan_existing()
    duplicates = {k: v for k, v in seen.items() if len(v) > 1}
    if duplicates:
        lines = "\n".join(f"   - {k:03d}: {', '.join(names)}" for k, names in sorted(duplicates.items()))
        fail("Se detectaron IDs NUMERICOS DUPLICADOS entre carpetas de specs. Resuelvelos antes de crear la spec:\n" + lines)
    if malformed:
        print("⚠️ [NEW-SPEC] Ignorando carpetas sin prefijo numerico NNN- (revisa sus nombres):")
        for name in malformed:
            print(f"   - {name}")

    next_id = max_num + 1
    if next_id > 999:
        fail("Se supero el rango de IDs de 3 digitos (999). Amplia el patron del arnes deliberadamente.")

    folder_name = f"{next_id:03d}-{slug}"
    target_dir = SPECS_DIR / "backlog" / folder_name
    if target_dir.exists():
        fail(f"Ya existe '{target_dir.relative_to(HARNESS_DIR.parent)}'. No se sobreescribiran specs.")

    target_dir.mkdir(parents=True)
    heading = f"# {folder_name} - {args.title.strip()}" if args.title.strip() else f"# {folder_name} - [Nombre Descriptivo]"
    spec_path = target_dir / "spec.md"
    spec_path.write_text(SKELETON.replace("#{heading}", heading, 1), encoding="utf-8")

    print(f"✅ [NEW-SPEC] Spec creada (borrador materializado): {spec_path.relative_to(HARNESS_DIR.parent)}")
    print("   Completa el contenido segun TEMPLATE.md y verifica el campo 'Aprobada' con la fecha del checkpoint.")
    print("   Para iniciar el ciclo TDD: python harness/scripts/activate-spec.py " + folder_name)
    sys.exit(0)


if __name__ == "__main__":
    main()
